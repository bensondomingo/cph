from .secrets import TOKEN
import logging
import requests
import urllib
import json

logger = logging.getLogger(__name__)


# Hardcoded keys to reduce processing load from extracting it on the
# response.
TRANSACTION_FIELDS_LEN = 22
TRANSACTION_FIELDS = ['entry_type', 'transaction_id', 'created_at', 'amount',
                      'running_balance', 'payment_outlet', 'recipient',
                      'currency', 'fee', 'transfer_id', 'order_id',
                      'payment_request_id', 'invoice_id',
                      'external_transaction_id', 'payment_request_fee',
                      'payer', 'message', 'exchange_amount',
                      'exchange_currency', 'exchange_rate', 'status',
                      'order_fee']

headers = {
    'Authorization': 'Bearer {}'.format(TOKEN),
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


def fetch(method, url, data=None):
    resp = None
    logger.info('Sending %s request to %s', method, url)
    if method == 'GET':
        try:
            resp = requests.get(url, headers=headers)
        except Exception as e:
            logging.exception(
                'An error occured during %s request to %s', method, url)
            raise e
    elif method == 'POST':
        try:
            resp = requests.post(url, data=data, headers=headers)
        except Exception as e:
            logging.exception(
                'An error occured during %s request to %s with data %s',
                method, url, data)
            raise e
    return resp


def fetch_orders(type, id=None, *args, **kwargs):
    endpoint = f'https://api.coins.asia/v1/{type}'
    if id:
        endpoint += f'/{id}/'
    else:
        params = kwargs
        params.setdefault('limit', 10)
        params.setdefault('offset', 0)
        endpoint = endpoint + '?' + urllib.parse.urlencode(params)
    resp = fetch('GET', endpoint)

    try:
        assert(resp.status_code == 200)
    except AssertionError as e:
        logger.exception(
            ('An error occured while sending GET request to %s. Expecting '
             'status code of 200 but %d is received'),
            endpoint, resp.status_code)
        raise e

    return resp.json()


def fetch_crypto_payment(order_id):
    endpoint = ('https://coins.ph/api/v3/crypto-payments'
                f'?reference__order_id={order_id}')
    resp = fetch('GET', endpoint)
    try:
        assert(resp.status_code == 200)
    except AssertionError as e:
        logger.exception(
            ('An error occured while sending GET request to %s. Expecting '
             'status code of 200 but %d is received'),
            endpoint, resp.status_code)
        raise e
    return resp.json()


def get_crypto_payments(id=None, *args, **kwargs):
    endpoint = 'https://coins.ph/api/v3/crypto-payments'
    if id:
        endpoint += f'/{id}/'
    else:
        args = dict(page=kwargs.get('page', 1),
                    per_page=kwargs.get('per_page', 100))
        endpoint = endpoint + '/?' + urllib.parse.urlencode(args)
    headers = {
        'Authorization': 'Bearer {}'.format(TOKEN),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.get(url=endpoint, headers=headers)
    try:
        assert(response.status_code == 200)
    except AssertionError:
        # TODO: implement error handling
        pass

    json_response = response.json()
    if not kwargs.get('all', False):
        return json_response

    next_page = json_response['meta'].get('next_page')
    if next_page is not None:
        r = get_crypto_payments(page=next_page, all=kwargs.get('all'))
        r.pop('meta')
        json_response['crypto-payments'] += r.get('crypto-payments')

    return json_response


def get_transactions(month, year, currency_symbol='PBTC', filters=None):
    url = 'https://coins.ph/api/v3/balance-statements/?'
    args = {'month': month, 'year': year}
    if currency_symbol:
        args.update({'currency': currency_symbol})
    endpoint = url + urllib.parse.urlencode(args)
    headers = {
        'Authorization': 'Bearer {}'.format(TOKEN),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.get(url=endpoint, headers=headers)
    try:
        assert(response.status_code == 200)
    except AssertionError:
        # TODO: implement error handling
        pass

    raw_data_list = response.text.split('\r\n')
    for data in raw_data_list[1:]:
        if not data:
            continue
        d = dict(zip(TRANSACTION_FIELDS, eval(data)))
        if not filters:
            yield d
            continue

        _filter = {k: v for k, v in filters.items()
                   if v == d.get(k, None)}
        if len(_filter) != len(filters):
            continue
        yield d


def get_account():
    url = 'https://coins.ph/api/v3/crypto-accounts'
    headers = {
        'Authorization': 'Bearer {}'.format(TOKEN),
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': 'application/json'
    }
    response = requests.get(url=url, headers=headers)
    try:
        assert(response.status_code == 200)
    except AssertionError:
        # TODO: implement error handling
        pass
    assert(response.status_code == 200)
    return json.loads(response.text)


class ThrottleError(BaseException):
    pass
