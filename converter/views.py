from django.shortcuts import render
from .services import get_exchange_rate, SUPPORTED_CURRENCIES
from .models import ConversionHistory

XAF_PER_EUR = 655.957

def convert_with_xaf(from_currency, to_currency, amount):
    """Gère les conversions impliquant le XAF via l'EUR comme pivot."""
    if from_currency == 'XAF' and to_currency == 'XAF':
        return amount, 1

    if from_currency == 'XAF':
        amount_in_eur = amount / XAF_PER_EUR
        if to_currency == 'EUR':
            return round(amount_in_eur, 2), round(1 / XAF_PER_EUR, 6)
        rate = get_exchange_rate('EUR', to_currency)
        if rate:
            final_rate = round(rate / XAF_PER_EUR, 6)
            return round(amount_in_eur * rate, 2), final_rate
        return None, None

    if to_currency == 'XAF':
        if from_currency == 'EUR':
            return round(amount * XAF_PER_EUR, 2), XAF_PER_EUR
        rate = get_exchange_rate(from_currency, 'EUR')
        if rate:
            final_rate = round(rate * XAF_PER_EUR, 6)
            return round(amount * rate * XAF_PER_EUR, 2), final_rate
        return None, None

    rate = get_exchange_rate(from_currency, to_currency)
    if rate:
        return round(amount * rate, 2), rate
    return None, None


def converter_home(request):
    """Page principale du convertisseur de devises."""
    result = None
    error = None
    currencies_by_code = {c['code']: c for c in SUPPORTED_CURRENCIES}

    if request.method == 'POST':
        from_currency = request.POST.get('from_currency')
        to_currency   = request.POST.get('to_currency')
        amount        = float(request.POST.get('amount', 1))

        converted, rate = convert_with_xaf(from_currency, to_currency, amount)

        if converted is not None:
            # Sauvegarde en base de données
            ConversionHistory.objects.create(
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
                converted=converted,
                rate=rate,
            )

            result = {
                'from': currencies_by_code[from_currency],
                'to': currencies_by_code[to_currency],
                'amount': amount,
                'converted': converted,
                'rate': rate,
            }
        else:
            error = "Impossible de récupérer les taux de change. Réessaie plus tard."

    # Récupère les 10 dernières conversions
    history = ConversionHistory.objects.all()[:10]

    context = {
        'currencies': SUPPORTED_CURRENCIES,
        'result': result,
        'error': error,
        'history': history,
    }
    return render(request, 'converter/home.html', context)