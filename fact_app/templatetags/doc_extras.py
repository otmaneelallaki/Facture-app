from django import template

register = template.Library()


def _spanish_number(value, decimals=2):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    formatted = f"{value:,.{decimals}f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


@register.filter
def eur(value):
    """ Format a number as Spanish-style currency: 1.234,56 € """
    return f"{_spanish_number(value)} €"


@register.filter
def pct(value):
    """ Format a number as Spanish-style percentage: 21,00 % """
    return f"{_spanish_number(value)} %"
