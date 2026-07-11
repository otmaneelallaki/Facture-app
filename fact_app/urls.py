from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),

    path('invoices/', views.HomeView.as_view(), name='home'),
    path('add-customer', views.AddCustomerView.as_view(), name='add-customer'),
    path('add-invoice', views.AddInvoiceView.as_view(), name='add-invoice'),
    path('view-invoice/<int:pk>', views.InvoiceVisualizationView.as_view(), name='view-invoice'),
    path('invoice-pdf/<int:pk>', views.get_invoice_pdf, name="invoice-pdf"),

    path('presupuestos/', views.PresupuestoHomeView.as_view(), name='presupuesto-home'),
    path('add-presupuesto', views.AddPresupuestoView.as_view(), name='add-presupuesto'),
    path('view-presupuesto/<int:pk>', views.PresupuestoVisualizationView.as_view(), name='view-presupuesto'),
    path('presupuesto-pdf/<int:pk>', views.get_presupuesto_pdf, name="presupuesto-pdf"),

    path('estadisticas/', views.StatisticsView.as_view(), name='statistics'),
]