from django.shortcuts import render
from django.views import View
from .models import * 
from django.contrib import messages

from django.db import transaction

from .utils import pagination, get_invoice, get_presupuesto, get_statistics

from xhtml2pdf import pisa
import datetime
import os
from django.conf import settings
from django.template.loader import get_template
from django.http import HttpResponse


from django.utils.translation import gettext as _

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .decorators import *


from django.utils.translation import gettext as _









# Create your views here.

class LandingView(LoginRequiredSuperuserMixim, View):
    """ Landing page: entry point offering Facturas or Presupuestos """

    template_name = 'landing.html'

    def get(self, request, *args, **kwargs):

        context = {
            'invoices_count': Invoice.objects.count(),
            'presupuestos_count': Presupuesto.objects.count(),
        }

        return render(request, self.template_name, context)


class HomeView(LoginRequiredSuperuserMixim, View):
    """ Main view """

    templates_name = 'index.html'

    invoices = Invoice.objects.select_related('customer', 'save_by').all().order_by('-invoice_date_time')

    context = {
        'invoices': invoices
    }

    def get(self, request, *args, **kwags):  
        items = pagination(request, self.invoices)

        self.context['invoices'] = items

        return render(request, self.templates_name, self.context)
    
    
    def post(self, request, *args, **kwagrs):
        # modify an invoice

        if request.POST.get('id_modified'):

            paid = request.POST.get('modified')

            try: 

                obj = Invoice.objects.get(id=request.POST.get('id_modified'))

                if paid == 'True':

                    obj.paid = True

                else:

                    obj.paid = False 

                obj.save() 

                messages.success(request,  _("Cambio realizado con éxito.")) 

            except Exception as e:   

                messages.error(request, f"Sorry, the following error has occured {e}.")      

        # deleting an invoice    

        if request.POST.get('id_supprimer'):

            try:

                obj = Invoice.objects.get(pk=request.POST.get('id_supprimer'))

                obj.delete()

                messages.success(request, _("La eliminación fue exitosa."))   

            except Exception as e:

                messages.error(request, f"Sorry, the following error has occured {e}.")
        
        items = pagination(request, self.invoices)

        self.context['invoices'] = items

        return render(request, self.templates_name, self.context)

class AddCustomerView(LoginRequiredSuperuserMixim, View):
     """ add new customer """    
     template_name = 'add_customer.html'

     def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

     def post(self, request, *args, **kwargs):

        data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'sex': "Homme",#request.POST.get('sex'),
            'age': "#",# request.POST.get('age'),
            'city': request.POST.get('city'),
            'save_by': request.user

        }
        try:
            created = Customer.objects.create(**data)

            if created:

                messages.success(request, _("Cliente registrado con éxito."))

            else:

                messages.error(request, "Lo sentimos, inténtalo de nuevo, los datos enviados están corruptos.")

        except Exception as e:    

            messages.error(request, f"Sorry our system is detecting the following issues {e}.")

        return render(request, self.template_name) 
     
class AddInvoiceView(LoginRequiredSuperuserMixim, View):
    """ add a new invoice view """

    template_name = 'add_invoice.html'

    customers = Customer.objects.select_related('save_by').all()

    context = {
        'customers': customers
    }

    def get(self, request, *args, **kwargs):
        return  render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):

        try:

            customer = request.POST.get('customer')

            if not customer:
                raise ValueError(_("Debes seleccionar un cliente."))

            articles = request.POST.getlist('article')

            qties = request.POST.getlist('qty')

            units = request.POST.getlist('unit')

            total_a = request.POST.getlist('total-a')

            total = 0 #request.POST.get('total')

            comment = request.POST.get('comment')

            tax = request.POST.get('tax')

            with transaction.atomic():

                invoice_object = {
                    'customer_id': customer,
                    'save_by': request.user,
                    'total': total,
                    'comments': comment,
                    'tax' : tax,
                }

                invoice = Invoice.objects.create(**invoice_object)

                items = []

                for index, article in enumerate(articles):

                    data = Article(
                        invoice_id = invoice.id,
                        name = article,
                        quantity=qties[index],
                        unit_price = units[index],
                        total = total_a[index],
                    )

                    items.append(data)

                Article.objects.bulk_create(items)

            messages.success(request, _("Data saved successfully."))

        except Exception as e:
            messages.error(request, f"Sorry the following error has occured {e}.")

        return  render(request, self.template_name, self.context)
    

class InvoiceVisualizationView(LoginRequiredSuperuserMixim, View):
    """ This view helps to visualize the invoice """

    template_name = 'invoice.html'

    def get(self, request, *args, **kwargs):

        pk = kwargs.get('pk')

        context = get_invoice(pk)

        return render(request, self.template_name, context)


#@superuser_required
def get_invoice_pdf(request, *args, **kwargs):
    """ generate pdf file from html file """

    pk = kwargs.get('pk')

    context = get_invoice(pk)

    context['date'] = datetime.datetime.today()

    # get html file
    template = get_template('invoice-pdf.html')

    # render html with context variables

    html = template.render(context)

    # options of pdf format 

    options = {
        'page-size': 'Letter',
        'encoding': 'UTF-8',
        "enable-local-file-access": ""
    }

    # generate pdf 
    ##config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')

    #pdf = pdfkit.from_string(html, False, options)

    #response = HttpResponse(pdf, content_type='application/pdf')

    #response['Content-isposition'] = "attachement"

    #return response
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    name = "Facture Nº {}.pdf".format(pk)
    disposition = 'inline' if request.GET.get('inline') else 'attachment'
    response['Content-Disposition'] = '%s; filename= "%s"' % (disposition, name)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


class PresupuestoHomeView(LoginRequiredSuperuserMixim, View):
    """ Main view for Presupuestos (price quotes) """

    template_name = 'presupuesto_index.html'

    def get(self, request, *args, **kwargs):

        presupuesto_qs = Presupuesto.objects.select_related('customer', 'save_by').all().order_by('-presupuesto_date_time')

        items = pagination(request, presupuesto_qs)

        return render(request, self.template_name, {'presupuestos': items})

    def post(self, request, *args, **kwargs):

        # modify a presupuesto status

        if request.POST.get('id_modified'):

            status = request.POST.get('status')

            try:

                obj = Presupuesto.objects.get(id=request.POST.get('id_modified'))

                obj.status = status

                obj.save()

                messages.success(request, _("Cambio realizado con éxito."))

            except Exception as e:

                messages.error(request, f"Sorry, the following error has occured {e}.")

        # deleting a presupuesto

        if request.POST.get('id_supprimer'):

            try:

                obj = Presupuesto.objects.get(pk=request.POST.get('id_supprimer'))

                obj.delete()

                messages.success(request, _("La eliminación fue exitosa."))

            except Exception as e:

                messages.error(request, f"Sorry, the following error has occured {e}.")

        presupuesto_qs = Presupuesto.objects.select_related('customer', 'save_by').all().order_by('-presupuesto_date_time')

        items = pagination(request, presupuesto_qs)

        return render(request, self.template_name, {'presupuestos': items})


class AddPresupuestoView(LoginRequiredSuperuserMixim, View):
    """ add a new presupuesto view """

    template_name = 'add_presupuesto.html'

    def get(self, request, *args, **kwargs):

        customers = Customer.objects.select_related('save_by').all()

        return render(request, self.template_name, {'customers': customers})

    def post(self, request, *args, **kwargs):

        try:

            customer = request.POST.get('customer')

            if not customer:
                raise ValueError(_("Debes seleccionar un cliente."))

            articles = request.POST.getlist('article')

            qties = request.POST.getlist('qty')

            units = request.POST.getlist('unit')

            total_a = request.POST.getlist('total-a')

            comment = request.POST.get('comment')

            tax = request.POST.get('tax')

            valid_until = request.POST.get('valid_until') or None

            with transaction.atomic():

                presupuesto_object = {
                    'customer_id': customer,
                    'save_by': request.user,
                    'comments': comment,
                    'tax': tax,
                    'valid_until': valid_until,
                }

                presupuesto = Presupuesto.objects.create(**presupuesto_object)

                items = []

                for index, article in enumerate(articles):

                    data = PresupuestoArticle(
                        presupuesto_id=presupuesto.id,
                        name=article,
                        quantity=qties[index],
                        unit_price=units[index],
                        total=total_a[index],
                    )

                    items.append(data)

                PresupuestoArticle.objects.bulk_create(items)

            messages.success(request, _("Data saved successfully."))

        except Exception as e:
            messages.error(request, f"Sorry the following error has occured {e}.")

        customers = Customer.objects.select_related('save_by').all()

        return render(request, self.template_name, {'customers': customers})


class PresupuestoVisualizationView(LoginRequiredSuperuserMixim, View):
    """ This view helps to visualize the presupuesto """

    template_name = 'presupuesto.html'

    def get(self, request, *args, **kwargs):

        pk = kwargs.get('pk')

        context = get_presupuesto(pk)

        return render(request, self.template_name, context)


def get_presupuesto_pdf(request, *args, **kwargs):
    """ generate pdf file from html file for a presupuesto

    Both the "Download" and "Print" actions on the detail page point at this
    same endpoint so the printed and downloaded documents are always
    byte-identical. ?inline=1 opens it in the browser's PDF viewer (for
    printing) instead of forcing a download.
    """

    pk = kwargs.get('pk')

    context = get_presupuesto(pk)

    context['date'] = datetime.datetime.today()

    context['logo_path'] = os.path.join(settings.BASE_DIR, 'static', 'images', 'Logo.png')

    template = get_template('presupuesto-pdf.html')

    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    name = "Presupuesto Nº {}.pdf".format(pk)
    disposition = 'inline' if request.GET.get('inline') else 'attachment'
    response['Content-Disposition'] = '%s; filename= "%s"' % (disposition, name)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


class StatisticsView(LoginRequiredSuperuserMixim, View):
    """ Statistics dashboard: revenue, presupuesto status breakdown, top customers """

    template_name = 'statistics.html'

    def get(self, request, *args, **kwargs):

        context = get_statistics()

        return render(request, self.template_name, context)