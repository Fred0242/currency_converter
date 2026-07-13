import json
import logging
import os
import uuid
from datetime import datetime, timezone

import azure.functions as func
import requests
from azure.data.tables import TableServiceClient

app = func.FunctionApp()

TABLE_NAME = "ConversionHistory"
XAF_PER_EUR = 655.957

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
CURRENCIES_BY_CODE = {c['code']: c for c in SUPPORTED_CURRENCIES}


def get_exchange_rate(from_currency: str, to_currency: str):
    url = f'https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}'
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()['rates'][to_currency]


def convert_with_xaf(from_currency, to_currency, amount):
    if from_currency == 'XAF' and to_currency == 'XAF':
        return amount, 1
    if from_currency == 'XAF':
        amount_in_eur = amount / XAF_PER_EUR
        if to_currency == 'EUR':
            return round(amount_in_eur, 2), round(1 / XAF_PER_EUR, 6)
        rate = get_exchange_rate('EUR', to_currency)
        return round(amount_in_eur * rate, 2), round(rate / XAF_PER_EUR, 6)
    if to_currency == 'XAF':
        if from_currency == 'EUR':
            return round(amount * XAF_PER_EUR, 2), XAF_PER_EUR
        rate = get_exchange_rate(from_currency, 'EUR')
        return round(amount * rate * XAF_PER_EUR, 2), round(rate * XAF_PER_EUR, 6)
    rate = get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2), rate


def get_table_client():
    connection_string = os.environ["AzureWebJobsStorage"]
    service = TableServiceClient.from_connection_string(connection_string)
    return service.create_table_if_not_exists(TABLE_NAME)


@app.function_name(name="convert")
@app.route(route="convert", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def convert(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger — écrit une conversion dans Azure Table Storage."""
    try:
        body = req.get_json()
        username = (body.get('username') or 'anonymous').strip() or 'anonymous'
        from_currency = body['from_currency']
        to_currency = body['to_currency']
        amount = float(body.get('amount', 1))
    except (ValueError, KeyError, TypeError):
        return func.HttpResponse(
            json.dumps({'error': "Requête invalide."}),
            status_code=400, mimetype="application/json",
        )

    if from_currency not in CURRENCIES_BY_CODE or to_currency not in CURRENCIES_BY_CODE:
        return func.HttpResponse(
            json.dumps({'error': "Devise inconnue."}),
            status_code=400, mimetype="application/json",
        )

    try:
        converted, rate = convert_with_xaf(from_currency, to_currency, amount)
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API Frankfurter: {e}")
        return func.HttpResponse(
            json.dumps({'error': "Impossible de récupérer les taux de change. Réessaie plus tard."}),
            status_code=502, mimetype="application/json",
        )

    created_at = datetime.now(timezone.utc)
    row_key = f"{9999999999 - int(created_at.timestamp()):010d}-{uuid.uuid4()}"

    table = get_table_client()
    table.create_entity({
        'PartitionKey': username,
        'RowKey': row_key,
        'from_currency': from_currency,
        'to_currency': to_currency,
        'amount': amount,
        'converted': converted,
        'rate': rate,
        'created_at': created_at.isoformat(),
    })

    return func.HttpResponse(
        json.dumps({
            'from': CURRENCIES_BY_CODE[from_currency],
            'to': CURRENCIES_BY_CODE[to_currency],
            'amount': amount,
            'converted': converted,
            'rate': rate,
        }),
        status_code=200, mimetype="application/json",
    )


@app.function_name(name="history")
@app.route(route="history/{username}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def history(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP trigger — lit l'historique des conversions depuis Azure Table Storage."""
    username = req.route_params.get('username')

    table = get_table_client()
    entities = table.query_entities(
        query_filter="PartitionKey eq @username",
        parameters={"username": username},
        select=["from_currency", "to_currency", "amount", "converted", "created_at"],
    )

    items = []
    for entity in entities:
        items.append({
            'from_currency': entity['from_currency'],
            'to_currency': entity['to_currency'],
            'amount': entity['amount'],
            'converted': entity['converted'],
            'created_at': entity['created_at'],
        })
        if len(items) >= 10:
            break

    return func.HttpResponse(
        json.dumps({'history': items}),
        status_code=200, mimetype="application/json",
    )
