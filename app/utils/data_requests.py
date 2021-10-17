import logging
import requests

logger = logging.getLogger(__name__)


def get_direction_name(city_1, city_2):
    return f"{city_1} – {city_2}"


def get_directions():
    response = requests.get('https://znami.by/cities.get')

    if response.status_code != 200:
        logger.error('Unable to get cities data.')
        return None

    cities_data = response.json()

    if cities_data['status'] != 'ok':
        logger.error('Error while getting cities info.')
        return None

    directions = []

    for c in cities_data['cities']:
        [directions.append(x) for x in list(map(lambda p: get_direction_name(c['name'], p), c['cities']))]

    return directions


def get_trips(date: str, city_1: str, city_2: str, time=None):
    response = requests.get('https://znami.by/trips.get', params={'date': date, 'city_1': city_1, 'city_2': city_2})

    if response.status_code != 200:
        logger.error('Unable to get cities data.')
        return None

    trips_data = response.json()

    if trips_data['status'] != 'ok':
        logger.error('Error while getting cities info.')
        return None

    if time is None:
        return trips_data['trips']

    return list(filter(lambda x: x['time'] == time, trips_data['trips']))


def send_code(phone):
    response = requests.post('https://znami.by/api/confirm.send', json={'phone': phone})

    if response.status_code != 200:
        logger.error('Unable to send SMS.')
        return None

    confirm_data = response.json()

    if confirm_data['status'] != 'ok':
        logger.error('Error while sending SMS.')
        return None

    return confirm_data['confirm_id']


def check_code(confirm_id, code):
    response = requests.post('https://znami.by/api/confirm.check', json={'confirm_id': confirm_id, 'code': code})

    if response.status_code != 200:
        logger.error('Unable to check code.')
        return None

    return response.json()


def create_reserve(token, trip, places):
    response = requests.post('https://znami.by/api/reserve.create',
                             json={'personal_token': token, 'trip_id': trip, 'places': places})

    if response.status_code != 200:
        logger.error('Unable to create reserve.')
        return None

    return response.json()
