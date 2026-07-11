
from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)
from django.utils import timezone
from collections import OrderedDict

from .models import *

MONTH_LABELS_ES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

def pagination(request, invoices):
    # default_page 
        default_page = 1 

        page = request.GET.get('page', default_page)

        # paginate items

        items_per_page = 5

        paginator = Paginator(invoices, items_per_page)

        try:

            items_page = paginator.page(page)

        except PageNotAnInteger:

            items_page = paginator.page(default_page)

        except EmptyPage:

            items_page = paginator.page(paginator.num_pages) 

        return items_page    



def get_invoice(pk):
    """ get invoice fonction """

    obj = Invoice.objects.get(pk=pk)

    articles = obj.article_set.all()

    context = {
        'obj': obj,
        'articles': articles
    }

    return context


def get_presupuesto(pk):
    """ get presupuesto fonction """

    obj = Presupuesto.objects.get(pk=pk)

    articles = obj.presupuestoarticle_set.all()

    context = {
        'obj': obj,
        'articles': articles
    }

    return context


def _last_n_months(n):
    """ returns the last n (year, month) tuples ending with the current month """

    today = timezone.localdate()

    buckets = []

    for i in range(n - 1, -1, -1):

        year, month = today.year, today.month - i

        while month <= 0:
            month += 12
            year -= 1

        buckets.append((year, month))

    return buckets


def get_statistics():
    """ aggregate the numbers shown on the statistics dashboard """

    invoices = Invoice.objects.select_related('customer').prefetch_related('article_set').all()

    presupuestos = Presupuesto.objects.select_related('customer').prefetch_related('presupuestoarticle_set').all()

    paid_invoices = [i for i in invoices if i.paid]

    pending_invoices = [i for i in invoices if not i.paid]

    total_collected = sum(i.get_total_taxed() for i in paid_invoices)

    total_pending = sum(i.get_total_taxed() for i in pending_invoices)

    # monthly breakdown (last 6 months), split collected vs pending

    months = _last_n_months(6)

    monthly = OrderedDict()

    for year, month in months:
        monthly[(year, month)] = {'label': MONTH_LABELS_ES[month - 1], 'collected': 0, 'pending': 0}

    for invoice in invoices:

        key = (invoice.invoice_date_time.year, invoice.invoice_date_time.month)

        if key not in monthly:
            continue

        amount = float(invoice.get_total_taxed())

        if invoice.paid:
            monthly[key]['collected'] += amount
        else:
            monthly[key]['pending'] += amount

    monthly_data = list(monthly.values())

    max_month_total = max((m['collected'] + m['pending'] for m in monthly_data), default=0) or 1

    for m in monthly_data:
        m['total'] = m['collected'] + m['pending']
        m['collected_pct'] = round(m['collected'] / max_month_total * 100, 1)
        m['pending_pct'] = round(m['pending'] / max_month_total * 100, 1)

    # presupuestos by status

    status_labels = dict(Presupuesto.STATUS_CHOICES)

    status_counts = OrderedDict((code, 0) for code in status_labels)

    for presupuesto in presupuestos:
        status_counts[presupuesto.status] = status_counts.get(presupuesto.status, 0) + 1

    total_presupuestos = presupuestos.count()

    status_data = []

    for code, label in status_labels.items():
        count = status_counts[code]
        pct = round(count / total_presupuestos * 100, 1) if total_presupuestos else 0
        status_data.append({'code': code, 'label': label, 'count': count, 'pct': pct})

    # top customers by collected revenue

    customer_totals = {}

    for invoice in paid_invoices:
        customer_totals.setdefault(invoice.customer, 0)
        customer_totals[invoice.customer] += float(invoice.get_total_taxed())

    top_customers = sorted(customer_totals.items(), key=lambda item: item[1], reverse=True)[:5]

    return {
        'total_invoices': invoices.count(),
        'total_presupuestos': total_presupuestos,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'paid_invoices_count': len(paid_invoices),
        'pending_invoices_count': len(pending_invoices),
        'monthly_data': monthly_data,
        'status_data': status_data,
        'top_customers': top_customers,
    }