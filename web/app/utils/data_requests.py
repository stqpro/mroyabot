import logging
import requests

logger = logging.getLogger(__name__)
base_url = 'http://znami.ru'


def get_direction_name(city_1, city_2):
    return f"{city_1} – {city_2}"


def get_directions():
    response = requests.get(base_url + '/cities.get')

    if response.status_code != 200:
        logger.error('Unable to get cities data.')
        return None

    cities_data = response.json()

    if cities_data['status'] != 'ok':
        logger.error('Error while getting cities info.')
        return None

    directions = []

    for c in cities_data['cities']:
        [directions.append(x) for x in list(map(lambda p: [c['name'], p], c['cities']))]

    sorted_directions = []

    for d in directions:
        tmp = [d[1], d[0]]

        if d not in sorted_directions:
            sorted_directions.append(d)

        if (tmp in directions) and (tmp not in sorted_directions):
            sorted_directions.append(tmp)

    return list(map(lambda p: get_direction_name(p[0], p[1]), sorted_directions))


def get_trips(date: str, city_1: str, city_2: str, time=None):
    response = requests.get(base_url + '/trips.get', params={'date': date, 'city_1': city_1, 'city_2': city_2})

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
    response = requests.post(base_url + '/api/confirm.send', json={'phone': phone})

    if response.status_code != 200:
        logger.error('Unable to send SMS.')
        return None

    confirm_data = response.json()

    if confirm_data['status'] != 'ok':
        logger.error('Error while sending SMS.')
        return None

    return confirm_data['confirm_id']


def check_code(confirm_id, code):
    response = requests.post(base_url + '/api/confirm.check', json={'confirm_id': confirm_id, 'code': code})

    if response.status_code != 200:
        logger.error('Unable to check code.')
        return None

    return response.json()


def create_booking(token, departure, destination, date, time, places, trip_id, station):
    user_info = get_user(token)

    if user_info is None:
        return None

    if user_info['fio'] is None:
        return {'status': 'false', 'error': 'Для бронирования рейсов необходимо указать фамилию в личном кабинете. '
                                            '(/account).'}

    response = requests.post(base_url + '/api/ticket.create',
                             json={'personal_token': token, 'city_1': departure, 'city_2': destination, 'date': date,
                                   'time': time, 'places': places, 'trip_id': trip_id, 'station_id': station,
                                   'fio': user_info['fio']})

    if response.status_code != 200:
        logger.error('Unable to create booking.')
        return None

    return response.json()


def create_reserve(token, trip, places):
    user_info = get_user(token)

    if user_info is None:
        return None

    if user_info['fio'] is None:
        return {'status': 'false', 'error': 'Для резервирования рейсов необходимо указать фамилию в личном кабинете. '
                                            '(/account).'}

    response = requests.post(base_url + '/api/reserve.create',
                             json={'personal_token': token, 'trip_id': trip, 'places': places, 'fio': user_info['fio']})

    if response.status_code != 200:
        logger.error('Unable to create reserve.')
        return None

    return response.json()


def get_user(token):
    response = requests.get(base_url + '/api/user.check', params={'personal_token': token})

    if response.status_code != 200:
        logger.error('Unable to get user info.')
        return None

    user_data = response.json()

    if user_data['status'] != 'ok':
        logger.error('Error while getting user info.')
        return None

    return user_data['user']


def get_tickets(token, mode):
    response = requests.get(base_url + '/api/tickets.get', params={'personal_token': token})

    if response.status_code != 200:
        logger.error('Unable to get users tickets.')
        return None

    tickets_data = response.json()

    if tickets_data['status'] != 'ok':
        logger.error('Error while getting users tickets')
        return None

    if mode == 'booking':
        return [t for t in tickets_data['tickets'] if t['status'] in [1, 2] and t['closed'] == 0]

    if mode == 'reserve':
        return [t for t in tickets_data['tickets'] if t['status'] == 5 and t['closed'] == 0]

    if mode == 'archive':
        return [t for t in tickets_data['tickets'] if t['closed'] == 1]


def cancel_trip(mode: str, ticket_id: int, token):
    if mode == 'booking':
        url = base_url + '/api/ticket.cancel'
    else:
        url = base_url + '/api/reserve.cancel'

    response = requests.post(url, params={'personal_token': token, 'ticket_id': ticket_id})

    if response.status_code != 200:
        logger.error('Unable to cancel ticket.')
        return None

    return response.json()


def get_stations(departure, destination):
    response = requests.get(base_url + '/trips.get', params={'city_1': departure, 'city_2': destination})

    if response.status_code != 200:
        logger.error('Unable to get stations list.')
        return None

    stations_data = response.json()

    if stations_data['status'] != 'ok':
        logger.error('Error while getting stations list.')
        return None

    return stations_data['stations_1']


def update_last_name(last_name, token):
    response = requests.post(base_url + '/api/user.update', params={'fio': last_name, 'personal_token': token})

    if response.status_code != 200:
        logger.error('Unable to update users last name.')
        return None

    return response.json()
