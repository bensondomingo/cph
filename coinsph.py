import requests
import urllib
import json
from pprint import pprint

from secrets import TOKEN


def get_transactions(month, year, currency_symbol='PBTC'):
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
    # Hardcoded keys to reduce processing load in extracting it from the
    # response text.
    keys = ('Entry Type', 'Transaction ID', 'Created At', 'Amount',
            'Running Balance', 'Payment Outlet', 'Recipient', 'Currency',
            'Fee', 'Transfer ID', 'Order ID', 'Payment Request ID',
            'Invoice ID', 'External Transaction ID', 'Payment Request Fee',
            'Payer', 'Message', 'Exchange Amount', 'Exchange Currency',
            'Exchange Rate', 'Status', 'Order Fee')
    raw_data_list = response.text.split('\r\n')
    for data in raw_data_list[1:]:
        if not data:
            continue
        yield dict(zip(keys, eval(data)))


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
