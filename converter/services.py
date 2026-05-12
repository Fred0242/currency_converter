import requests

SUPPORTED_CURRENCIES = [
    {'code': 'EUR', 'country': 'eu', 'name': 'Euro'},
    {'code': 'USD', 'country': 'us', 'name': 'Dollar américain'},
    {'code': 'GBP', 'country': 'gb', 'name': 'Livre sterling'},
    {'code': 'JPY', 'country': 'jp', 'name': 'Yen japonais'},
    {'code': 'CHF', 'country': 'ch', 'name': 'Franc suisse'},
    {'code': 'CAD', 'country': 'ca', 'name': 'Dollar canadien'},
    {'code': 'AUD', 'country': 'au', 'name': 'Dollar australien'},
    {'code': 'XAF', 'country': 'cg', 'name': 'Franc CFA'},
]

XAF_PER_EUR = 655.957

def get_exchange_rate(from_currency: str, to_currency: str) -> float | None:
    try:
        url = f'https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data['rates'][to_currency]
    except requests.exceptions.RequestException as e:
        print(f"Erreur API: {e}")
        return None