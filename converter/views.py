import json
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .services import get_exchange_rate, SUPPORTED_CURRENCIES
from .models import ConversionHistory

XAF_PER_EUR = 655.957

def convert_with_xaf(from_currency, to_currency, amount):
    if from_currency == 'XAF' and to_currency == 'XAF':
        return amount, 1
    if from_currency == 'XAF':
        amount_in_eur = amount / XAF_PER_EUR
        if to_currency == 'EUR':
            return round(amount_in_eur, 2), round(1 / XAF_PER_EUR, 6)
        rate = get_exchange_rate('EUR', to_currency)
        if rate:
            return round(amount_in_eur * rate, 2), round(rate / XAF_PER_EUR, 6)
        return None, None
    if to_currency == 'XAF':
        if from_currency == 'EUR':
            return round(amount * XAF_PER_EUR, 2), XAF_PER_EUR
        rate = get_exchange_rate(from_currency, 'EUR')
        if rate:
            return round(amount * rate * XAF_PER_EUR, 2), round(rate * XAF_PER_EUR, 6)
        return None, None
    rate = get_exchange_rate(from_currency, to_currency)
    if rate:
        return round(amount * rate, 2), rate
    return None, None


def converter_home(request):
    """Page principale — publique, historique uniquement si connecté."""
    result = None
    error  = None
    currencies_by_code = {c['code']: c for c in SUPPORTED_CURRENCIES}

    if request.method == 'POST':
        from_currency = request.POST.get('from_currency')
        to_currency   = request.POST.get('to_currency')
        amount        = float(request.POST.get('amount', 1))

        converted, rate = convert_with_xaf(from_currency, to_currency, amount)

        if converted is not None:
            # Sauvegarde uniquement si l'utilisateur est connecté
            if request.user.is_authenticated:
                ConversionHistory.objects.create(
                    user=request.user,
                    from_currency=from_currency,
                    to_currency=to_currency,
                    amount=amount,
                    converted=converted,
                    rate=rate,
                )
            result = {
                'from': currencies_by_code[from_currency],
                'to':   currencies_by_code[to_currency],
                'amount': amount,
                'converted': converted,
                'rate': rate,
            }
        else:
            error = "Impossible de récupérer les taux de change. Réessaie plus tard."

    # Historique uniquement si connecté
    history = []
    if request.user.is_authenticated:
        history = ConversionHistory.objects.filter(user=request.user)[:10]

    context = {
        'currencies': SUPPORTED_CURRENCIES,
        'result': result,
        'error': error,
        'history': history,
        'azure_function_base_url': settings.AZURE_FUNCTION_BASE_URL,
    }
    return render(request, 'converter/home.html', context)


@require_http_methods(["POST"])
def convert_api(request):
    """API HTTP — écrit une conversion (calcul + sauvegarde de l'historique)."""
    currencies_by_code = {c['code']: c for c in SUPPORTED_CURRENCIES}
    try:
        data = json.loads(request.body)
        from_currency = data.get('from_currency')
        to_currency = data.get('to_currency')
        amount = float(data.get('amount', 1))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': "Requête invalide."}, status=400)

    if from_currency not in currencies_by_code or to_currency not in currencies_by_code:
        return JsonResponse({'error': "Devise inconnue."}, status=400)

    converted, rate = convert_with_xaf(from_currency, to_currency, amount)
    if converted is None:
        return JsonResponse({'error': "Impossible de récupérer les taux de change. Réessaie plus tard."}, status=502)

    if request.user.is_authenticated:
        ConversionHistory.objects.create(
            user=request.user,
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            converted=converted,
            rate=rate,
        )

    return JsonResponse({
        'from': currencies_by_code[from_currency],
        'to': currencies_by_code[to_currency],
        'amount': amount,
        'converted': converted,
        'rate': rate,
    })


@require_http_methods(["GET"])
@login_required
def history_api(request):
    """API HTTP — lit l'historique des conversions de l'utilisateur connecté."""
    history = ConversionHistory.objects.filter(user=request.user)[:10]
    return JsonResponse({
        'history': [
            {
                'from_currency': item.from_currency,
                'to_currency': item.to_currency,
                'amount': str(item.amount),
                'converted': str(item.converted),
                'created_at': item.created_at.strftime('%d/%m/%Y %H:%M'),
            }
            for item in history
        ]
    })