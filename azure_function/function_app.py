import json
import logging
import os
import uuid
from datetime import datetime, timezone

import azure.functions as func
import requests

app = func.FunctionApp()

DATABASE_NAME = "CurrencyConverterDB"
CONTAINER_NAME = "ConversionHistory"
QUEUE_NAME = "conversion-queue"
COSMOS_CONNECTION = "CosmosDbConnectionSetting"
STORAGE_CONNECTION = "AzureWebJobsStorage"

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


@app.function_name(name="convert")
@app.route(route="convert", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.queue_output(arg_name="msg", queue_name=QUEUE_NAME, connection=STORAGE_CONNECTION)
def convert(req: func.HttpRequest, msg: func.Out[str]) -> func.HttpResponse:
    """HTTP trigger — calcule la conversion et dépose un message sur la queue
    (écriture différée, persistée plus tard par la fonction persist_conversion)."""
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

    created_at = datetime.now(timezone.utc).isoformat()

    msg.set(json.dumps({
        'username': username,
        'from_currency': from_currency,
        'to_currency': to_currency,
        'amount': amount,
        'converted': converted,
        'rate': rate,
        'created_at': created_at,
    }))

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


@app.function_name(name="persist_conversion")
@app.queue_trigger(arg_name="msg", queue_name=QUEUE_NAME, connection=STORAGE_CONNECTION)
@app.cosmos_db_output(
    arg_name="document",
    database_name=DATABASE_NAME,
    container_name=CONTAINER_NAME,
    connection=COSMOS_CONNECTION,
    create_if_not_exists=True,
    partition_key="/username",
)
def persist_conversion(msg: func.QueueMessage, document: func.Out[func.Document]) -> None:
    """Queue trigger — consomme un message et persiste la conversion sur Cosmos DB."""
    data = json.loads(msg.get_body().decode('utf-8'))
    data['id'] = str(uuid.uuid4())
    document.set(func.Document.from_dict(data))
    logging.info(f"Conversion persistée sur Cosmos DB pour {data['username']}")


@app.function_name(name="history")
@app.route(route="history/{username}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.cosmos_db_input(
    arg_name="items",
    database_name=DATABASE_NAME,
    container_name=CONTAINER_NAME,
    connection=COSMOS_CONNECTION,
    sql_query="SELECT TOP 10 * FROM c WHERE c.username = {username} ORDER BY c.created_at DESC",
)
def history(req: func.HttpRequest, items: func.DocumentList) -> func.HttpResponse:
    """HTTP trigger — lit l'historique des conversions depuis Cosmos DB (binding d'entrée)."""
    history_items = [
        {
            'from_currency': item['from_currency'],
            'to_currency': item['to_currency'],
            'amount': item['amount'],
            'converted': item['converted'],
            'created_at': item['created_at'],
        }
        for item in items
    ]

    return func.HttpResponse(
        json.dumps({'history': history_items}),
        status_code=200, mimetype="application/json",
    )
