import requests

SUPPORTED_CURRENCIES = [
    {'code': 'EUR', 'flag': '🇪🇺', 'name': 'Euro'},
    {'code': 'USD', 'flag': '🇺🇸', 'name': 'Dollar américain'},
    {'code': 'GBP', 'flag': '🇬🇧', 'name': 'Livre sterling'},
    {'code': 'JPY', 'flag': '🇯🇵', 'name': 'Yen japonais'},
    {'code': 'CHF', 'flag': '🇨🇭', 'name': 'Franc suisse'},
    {'code': 'CAD', 'flag': '🇨🇦', 'name': 'Dollar canadien'},
    {'code': 'AUD', 'flag': '🇦🇺', 'name': 'Dollar australien'},
    {'code': 'XAF', 'flag': '🇨🇬', 'name': 'Franc CFA (Afrique Centrale)'},
]

def get_exchange_rate(from_currency: str, to_currency: str) -> float | None:
    """
    Récupère le taux de change entre deux devises.
    Retourne le taux ou None en cas d'erreur.
    """
    try:
        url = f'https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data['rates'][to_currency]
    except requests.exceptions.RequestException as e:
        print(f"Erreur API: {e}")
        return None