import json
import requests
import pprint
import os
from dotenv import load_dotenv

load_dotenv()

class Betfair:

    def __init__(self):
        self.my_username = os.getenv('my_username')
        self.my_password = os.getenv('my_password')
        self.my_app_key = os.getenv('my_app_key')
        self.cert_location = os.getenv('cert_location')
        self.cert_key = os.getenv('cert_key')

        self.ssoid = self.get_ssoid()

        self.bet_url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

    def execute_request(self, request, params={}):
        request['params'] = params
        response = requests.post(self.bet_url, data=json.dumps(request), headers=self.get_app_headers())
        return response.json()

    def get_ssoid(self):
        payload = 'username=' + self.my_username + '&password=' + self.my_password
        headers = {'X-Application': self.my_app_key, 'Content-Type': 'application/x-www-form-urlencoded'}
        resp = requests.post('https://identitysso-cert.betfair.com/api/certlogin',
                             data=payload,cert=(self.cert_location, self.cert_key),headers=headers)
        json_resp = resp.json()
        SSOID = json_resp['sessionToken']
        return SSOID

    def get_app_headers(self):
        app_headers = {'X-Application': self.my_app_key, 'X-Authentication': self.ssoid, 'content-type': 'application/json'}
        return app_headers

    def get_base_req(self, method_name):
        base_req = {'jsonrpc':2.0,
                    'method': "SportsAPING/v1.0/{}".format(method_name),
                    'id': 1
                    }
        return base_req

    def get_betting_type_string(self, **betting_types):
        betting_type_string = '{'
        betting_type_list = []
        for key, value in betting_types.items():
            if isinstance(value, list):
                value = '[' + ', '.join(['"{}"'.format(val) for val in value]) + ']'
            betting_type_list.append(str(key) + ':' + str(value))
        betting_type_string = betting_type_string + ', '.join(betting_type_list) + '}'
        return betting_type_string

    def get_cancel_instructions(self, bet_id, size_reduction):
        cancel_instructions = {
                'betId': bet_id,
                'sizeReduction': size_reduction
            }
        return cancel_instructions

    def get_market_book(self, market_id, is_market_data_delayed, **kwargs):
        market_book = {}
        market_book['marketId'] = market_id
        market_book['isMarketDataDelayed'] = is_market_data_delayed
        for key, value in kwargs.items():
            market_book[key] = value
        return market_book

    def get_market_filter(self, **market_filters):
        market_filter_dict = {}
        for key, value in market_filters.items():
            market_filter_dict[key] = value
        return market_filter_dict


    def cancel_orders(self, string_market_id, cancel_instructions, customer_ref = None):
        """

        :param string_market_id: String
        :param cancel_instructions: <CancelInstruction>
        :param customer_ref: String
        :return:
        """
        cancel_req = self.get_base_req(method_name='cancelOrders')
        params = {'marketId': string_market_id,
                  'instructions': cancel_instructions
                  }
        if isinstance(customer_ref, str):
            params['customerRef'] = customer_ref
        cancel_req['params'] = params
        cancel_execution_report = requests.post(self.bet_url, data=json.dumps(cancel_req), headers=self.get_app_headers())
        return cancel_execution_report

    def list_cleared_orders(self, bet_status, **kwargs):
        list_cleared_req = self.get_base_req(method_name='listClearedOrders')
        list_cleared_req['id'] = '1'
        params = {}
        assert bet_status in ['SETTLED', 'VOIDED', 'LAPSED', 'CANCELLED']
        params['betStatus'] = bet_status
        for key, value in kwargs:
            params[key] = value
        ordered_summary_report = self.execute_request(list_cleared_req, params)
        return ordered_summary_report

    def list_competitions(self, market_filter={}, locale=None):
        list_competitions_req = self.get_base_req(method_name='listCompetitions')
        params = {'filter': market_filter}
        if isinstance(locale, str):
            params['locale'] = locale
        return self.execute_request(list_competitions_req, params)

    def list_countries(self, market_filter={}, locale=None):
        list_countries_req = self.get_base_req(method_name='listCountries')
        params = {'filter': market_filter}
        if isinstance(locale, str):
            params['locale'] = locale
        return self.execute_request(list_countries_req, params)

    def list_current_orders(self, **kwargs):
        list_current_orders_req = self.get_base_req(method_name='listCurrentOrders')
        params = {}
        for key, value in kwargs.items():
            params[key] = value
        return self.execute_request(list_current_orders_req, params)

    def list_events(self, market_filter={}, locale=None):
        list_events_req = self.get_base_req(method_name='listEvents')
        params = {'filter': market_filter}
        if isinstance(locale, str):
            params['locale'] = locale
        return self.execute_request(list_events_req, params)

    def list_event_types(self, market_filter={}, locale=None):
        list_event_types_req = self.get_base_req(method_name='listEventTypes')
        params = {'filter': market_filter}
        if isinstance(locale, str):
            params['locale'] = locale
        return self.execute_request(list_event_types_req, params)

    def list_market_book(self, market_ids, **kwargs):
        list_market_book_req = self.get_base_req(method_name='listMarketBook')
        params = {'marketIds': market_ids}
        for key, value in kwargs.items():
            params[key] = value
        return self.execute_request(list_market_book_req, params)

    def list_market_catalogue(self, market_filter={}, market_projection=None, sort=None,
                              max_results=1000, locale=None):
        list_market_catalogue_req = self.get_base_req(method_name='listMarketCatalogue')
        if market_projection is None:
            market_projection = ['COMPETITION', 'EVENT', 'EVENT_TYPE', 'MARKET_START_TIME',
                                 'MARKET_START_DESCRIPTION', 'RUNNER_DESCRIPTION', 'RUNNER_METADATA']
        params = {'filter': market_filter, 'marketProjection': market_projection, 'maxResults': max_results}
        if isinstance(locale, str):
            params['locale'] = locale
        if isinstance(sort, str):
            assert sort in ['MINIMUM_TRADED', 'MAXIMUM_TRADED', 'MINUMUM_AVAILABLE', 'MAXIMUM_AVAILABLE',
                            'FIRST_TO_START', 'LAST_TO_START']
            params['sort'] = sort
        return self.execute_request(list_market_catalogue_req, params)

    def list_market_profit_and_loss(self, market_ids, **kwargs):
        list_market_profit_and_loss_req = self.get_base_req(method_name='listMarketProfitAndLoss')
        params = {'marketIds': market_ids}
        for key, value in kwargs.items():
            params[key] = value
        return self.execute_request(list_market_profit_and_loss_req, params)

    def list_market_types(self, market_filter={}, locale=None):
        list_market_types_req = self.get_base_req(method_name='listMarketTypes')
        params = {'filter': market_filter}
        if isinstance(locale, str):
            params['locale'] = locale
        return self.execute_request(list_market_types_req, params)

    def list_runner_book(self, market_id, selection_id, **kwargs):
        list_runner_book_req = self.get_base_req(method_name='listRunnerBook')
        params = {'marketId': market_id, 'selectionId': selection_id}
        for key, value in kwargs.items():
            params[key] = value
        return self.execute_request(list_runner_book_req, params)

    def list_time_ranges(self, market_filter={}, granularity='MINUTES'):
        assert granularity in ['DAYS', 'HOURS', 'MINUTES']
        list_time_ranges_req = self.get_base_req(method_name='listTimeRanges')
        params = {'filter': market_filter, 'granularity': granularity}
        return self.execute_request(list_time_ranges_req, params)

    def list_venues(self, market_filter={}, locale=None):
        list_venues_req = self.get_base_req(method_name='listVenues')
        params = {'filter': market_filter}
        if isinstance(locale, str):
            params['locale'] = locale
        return self.execute_request(list_venues_req, params)

    def place_orders(self, market_id, instructions, customer_ref=None, market_version=None,
                     customer_strategy_ref=None, async_flag=None):
        place_orders_req = self.get_base_req(method_name='placeOrders')
        params = {'marketId': market_id, 'instructions': instructions}
        if customer_ref is not None:
            params['customerRef'] = customer_ref
        if market_version is not None:
            params['marketVersion'] = market_version
        if customer_strategy_ref is not None:
            params['customerStrategyRef'] = customer_strategy_ref
        if async_flag is not None:
            params['async'] = async_flag
        return self.execute_request(place_orders_req, params)

    def update_orders(self, market_id, instructions, customer_ref=None):
        update_orders_req = self.get_base_req(method_name='updateOrders')
        params = {'marketId': market_id, 'instructions': instructions}
        if customer_ref is not None:
            params['customerRef'] = customer_ref
        return self.execute_request(update_orders_req, params)

    def replace_orders(self, market_id, instructions, customer_ref=None, market_version=None, async_flag=None):
        replace_orders_req = self.get_base_req(method_name='replaceOrders')
        params = {'marketId': market_id, 'instructions': instructions}
        if customer_ref is not None:
            params['customerRef'] = customer_ref
        if market_version is not None:
            params['marketVersion'] = market_version
        if async_flag is not None:
            params['async'] = async_flag
        return self.execute_request(replace_orders_req, params)

if __name__ == '__main__':
    b = Betfair()
   # pprint.pprint(b.list_event_types())
   # pprint.pprint(b.list_event_types_json())

    #pprint.pprint(betfair_sports)
    #pprint.pprint(b.list_market_types())
    #pprint.pprint(b.list_market_catalogue())
    #betting_types = b.get_betting_type_string(eventTypeIds = ['1', '2'], inPlayOnly = 'true')
    #cancel_instructions = b.get_cancel_instructions('1', 2.0)
    #pprint.pprint(cancel_instructions)
    #cancel_order = b.cancel_orders('2', cancel_instructions)
    #pprint.pprint(cancel_order)
    pprint.pprint(b.list_cleared_orders('SETTLED'))
    #football_market = b.get_market_filter(eventTypeIds=['1'], inPlayOnly=True)
    #pprint.pprint(football_market)
    #x = b.list_competitions(football_market)
    #pprint.pprint(x)