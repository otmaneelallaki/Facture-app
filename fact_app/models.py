from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    """
    Name: Customer model definition
    """
    SEX_TYPES = (
        ('M', _('Male')),
        ('F', _('Feminine')),
    )
    name = models.CharField(max_length=132)

    email = models.EmailField()

    phone = models.CharField(max_length=132)

    address = models.CharField(max_length=64)

    sex = models.CharField(max_length=1, choices=SEX_TYPES)

    age = models.CharField(max_length=20)

    city = models.CharField(max_length=32)

    created_date = models.DateTimeField(auto_now_add=True)

    save_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta: 
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.name     



class Invoice(models.Model):
    """
    Name: Invoice model definition
    Description: 
    author: otmane.allaki1@gmail.com
    """

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    save_by = models.ForeignKey(User, on_delete=models.PROTECT)

    invoice_date_time = models.DateTimeField(auto_now_add=True)

    total = models.DecimalField(max_digits=10000, decimal_places=2)

    last_updated_date = models.DateTimeField(null=True, blank=True)

    paid  = models.BooleanField(default=False) 

    comments = models.TextField(null=True, max_length=1000, blank=True)

    tax = models.DecimalField(max_digits=100, decimal_places=2)

    
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
           return f"{self.customer.name}_{self.invoice_date_time}"

    @property
    def get_total(self):
        articles = self.article_set.all()   
        total = sum(article.get_total for article in articles)
        return total    
    
    def get_total_taxed(self):
        articles = self.article_set.all()   
        total =  sum(article.get_total for article in articles) + sum(article.get_total for article in articles) * self.tax/100
        return total 


class Article(models.Model):
    """
    Name: Article model definiton
    Descripiton: 
    Author: otmane.allaki1@gmail.com
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)

    name = models.CharField(max_length=32)

    quantity = models.IntegerField()

    unit_price = models.DecimalField(max_digits=1000, decimal_places=2)

    total = models.DecimalField(max_digits=1000, decimal_places=2)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    @property
    def get_total(self):
        total = self.quantity * self.unit_price  
        return total 
