import logging
import requests
import urllib
import json

from eload.api_keys import CPH_TOKEN as TOKEN

logger = logging.getLogger(__name__)


class InvalidPhoneNumberError(Exception):
    def __init__(self, phone_number, errors, *args, **kwargs):
        self.phone_number = phone_number
        super().__init__('phone_number', phone_number, errors, *args, **kwargs)


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
    'Content-Type': 'application/json;charset=UTF-8',
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
            resp = requests.post(url, data=json.dumps(data), headers=headers)
        except Exception as e:
            logging.exception(
                'An error occured during %s request to %s with data %s',
                method, url, data)
            raise e
    return resp


def fetch_orders(order_type, id=None, *args, **kwargs):
    endpoint = f'https://api.coins.asia/v1/{order_type}'
    if id is not None:
        endpoint += f'/{id}/'
        if kwargs:
            endpoint += f'?{urllib.parse.urlencode(kwargs)}'
    elif id is None and kwargs:
        endpoint += f'?{urllib.parse.urlencode(kwargs)}'
    else:
        params = kwargs
        params.setdefault('limit', 10)
        params.setdefault('offset', 0)
        endpoint = endpoint + '?' + urllib.parse.urlencode(params)
    return fetch('GET', endpoint)


def _fetch_orders(typ, id=None, *args, **kwargs):
    endpoint = f'https://api.coins.asia/v1/{typ}'
    if id is not None:
        endpoint += f'/{id}/'
        if kwargs:
            endpoint += f'?{urllib.parse.urlencode(kwargs)}'
    elif id is None and kwargs:
        endpoint += f'?{urllib.parse.urlencode(kwargs)}'
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


def request_new_order(data):
    endpoint = 'https://coins.ph/api/v2/sellorder'
    return fetch('POST', endpoint, data=data)

    # if resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
    #     errors = resp.json().get('errors')
    #     raise RequestNewOrderError(data, errors)

    # try:
    #     assert(resp.status_code == 201)
    # except AssertionError as e:
    #     logger.exception(
    #         ('An error occured while sending POST request to %s. Expecting '
    #          'status code of 201 but %d is received'),
    #         endpoint, resp.status_code)
    #     raise e

    # return resp.json()


def fetch_crypto_payment(order_id):
    endpoint = ('https://coins.ph/api/v3/crypto-payments'
                f'?reference__order_id={order_id}')
    return fetch('GET', endpoint)


def fetch_outlet_details(outlet_id):
    endpoint = f'https://api.coins.asia/v1/payout-outlets/{outlet_id}'
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


def fetch_outlet_data(phone_number):
    """ Phone number must include country code. i.e +639XXXXXXXXX """
    encoded_arg = urllib.parse.quote(phone_number)
    endpoint = f'https://api.coins.asia/v4/payout-outlets/?language=en&per_page=100&recipient_info={encoded_arg}&recipient_type=msisdn'  # noqa: E501
    try:
        resp = fetch('GET', endpoint)
    except Exception as e:
        # Handle edge case exceptions here
        raise e

    return resp


def fetch_mobile_load_payout_outlets():
    endpoint = 'https://api.coins.asia/v4/payout-outlets/?language=en&per_page=1000&outlet_category=mobile-load&region=PH&provider_region=PH&recipient_type=msisdn'  # noqa: E501
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
