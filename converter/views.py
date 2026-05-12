from django.shortcuts import render
from .services import get_exchange_rate, SUPPORTED_CURRENCIES

# Taux fixe officiel XAF/EUR (parité fixe depuis 1999)
XAF_PER_EUR = 655.957

def convert_with_xaf(from_currency: str, to_currency: str, amount: float) -> float | None:
    """Gère les conversions impliquant le XAF via l'EUR comme pivot."""

    if from_currency == 'XAF' and to_currency == 'XAF':
        return amount

    if from_currency == 'XAF':
        # XAF → EUR → devise cible
        amount_in_eur = amount / XAF_PER_EUR
        if to_currency == 'EUR':
            return round(amount_in_eur, 2)
        rate = get_exchange_rate('EUR', to_currency)
        return round(amount_in_eur * rate, 2) if rate else None

    if to_currency == 'XAF':
        # devise source → EUR → XAF
        if from_currency == 'EUR':
            return round(amount * XAF_PER_EUR, 2)
        rate = get_exchange_rate(from_currency, 'EUR')
        return round(amount * rate * XAF_PER_EUR, 2) if rate else None

    # Conversion normale sans XAF
    rate = get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2) if rate else None


def converter_home(request):
    """Page principale du convertisseur de devises."""
    result = None
    error = None

    # Dictionnaire pour accéder facilement aux infos par code
    currencies_by_code = {c['code']: c for c in SUPPORTED_CURRENCIES}

    if request.method == 'POST':
        from_currency = request.POST.get('from_currency')
        to_currency = request.POST.get('to_currency')
        amount = float(request.POST.get('amount', 1))

        converted = convert_with_xaf(from_currency, to_currency, amount)

        if converted is not None:
            result = {
                'from': currencies_by_code[from_currency],
                'to': currencies_by_code[to_currency],
                'amount': amount,
                'converted': converted,
            }
        else:
            error = "Impossible de récupérer les taux de change. Réessaie plus tard."

    context = {
        'currencies': SUPPORTED_CURRENCIES,
        'result': result,
        'error': error,
    }
    return render(request, 'converter/home.html', context)