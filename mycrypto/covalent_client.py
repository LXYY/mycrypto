import requests
import retry
from json.decoder import JSONDecodeError

class CovalentClient:
    def __init__(self):
        self._api_key = 'ckey_1cef18588f1a4ebfb33c769314c'
        self._url_tmpl = 'https://api.covalenthq.com/v1/{chain_id}/events/topics/{topic_hash}/'
        self._max_block_height = 100000
        self._default_page_size = 100
        self._max_attempts = 3

    @retry.retry(JSONDecodeError, tries=3, delay=1)
    def _retrieve_paginated_log_events_by_topic(self, topic, address, from_block, to_block, page_number):
        url = self._url_tmpl.format(chain_id=250, topic_hash=topic)
        params = {
            'sender-address': address,
            'starting-block': from_block,
            'ending-block': to_block,
            'quote-currency': 'USD',
            'format': 'JSON',
            'key': self._api_key,
            'page-number': page_number,
            'page-size': self._default_page_size,
        }
        response = requests.get(url, params=params)
        return response.json()['data']['items']

    def retrieve_log_events_by_topic(self, topic, address, from_block, to_block):
        current_from_block = from_block
        while current_from_block <= to_block:
            current_to_block = min(to_block, current_from_block + self._max_block_height)
            page_number = 0
            while True:
                event_log_items = self._retrieve_paginated_log_events_by_topic(topic, address, current_from_block,
                                                                               current_to_block, page_number)
                if not event_log_items:
                    break

                for event_log in event_log_items:
                    yield event_log
                page_number += 1

            current_from_block = current_to_block + 1
