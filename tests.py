import json
import unittest

from rest_framework import status

from cph.coinsph import fetch_outlet_data
from cph import coinsph

from cphapp.test_assets import defines, json_file_path

PHONE_NUMBERS = {
    'globe': defines.PHONE_NUMBER_GLOBE,
    'smart': defines.PHONE_NUMBER_SMART,
    'sun': defines.PHONE_NUMBER_SUN,
    'invalid_phone_number': defines.PHONE_NUMBER_INVALID
}


class TestCase(unittest.TestCase):

    def test_fetch_outlet_data(self):
        for k, v in PHONE_NUMBERS.items():
            if k == 'invalid_phone_number':
                with self.assertRaises(coinsph.InvalidPhoneNumber):
                    coinsph.fetch_outlet_data(v)
            else:
                r = fetch_outlet_data(v)
                self.assertEqual(r.keys().__len__(), 2)
                self.assertIn(k, r.get('payout-outlets')[0].get('id'))

    def test_fetch_orders(self):
        with open(json_file_path.GET_REQUEST_RESP_JSON, 'r') as f:
            resp = json.load(f)
            data = resp.get('orders')[0]

        eti = data.get('external_transaction_id')
        resp = coinsph.fetch_orders('sellorder', external_transaction_id=eti)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
