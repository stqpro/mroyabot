import logging

from typing import Union, Dict, List

logger = logging.getLogger(__name__)


def reformat_date(date: str) -> str:
    numbers = date.split("-", maxsplit=2)
    return f"{numbers[2]}/{numbers[1]}/{numbers[0]}"


def parse_car_info(car: Union[Dict, None]) -> str:
    if car is None:
        return "<b>Автомобиль:</b> не назначен"

    try:
        return f"<b>Автомобиль:</b> {car['color'].lower()} {car['mark'].capitalize()} {car['model'].capitalize()}\n" \
               f"<b>Номер автомобиля:</b> {car['number']}"
    except KeyError:
        logger.error('Unable to get car info.')
        return "<b>Автомобиль:</b> неизвестен"


def parse_driver_info(driver: Union[Dict, None]) -> str:
    if driver is None:
        return "<b>Водитель:</b> не назначен"

    try:
        return f"\n<b>Водитель:</b> {driver['name']}\n<b>Телефон водителя: </b>+{driver['phone']}"
    except KeyError:
        logger.error('Unable to get driver info.')
        return "<b>Водитель:</b> неизвестен"


def parse_trips_info(trips: List[Dict], direction: str) -> List[Dict]:
    message = f"<b>Маршрут:</b> {direction}\n\n" \
              f"<b>Дата:</b> {reformat_date(trips[0]['date'])}\n" \
              f"<b>Время:</b> {trips[0]['time']}\n\n" \

    if len(trips) > 1 and trips[0]['car'] is None:
        message += f"<b>Рейсов:</b> {len(trips)}\n" \
                   f"<b>Свободных мест:</b> {sum([int(t['free_places']) for t in trips])} " \
                   f"<em>({' + '.join(str(t['free_places']) for t in trips)})</em>\n\n"

        result = {'message': message,
                  'places': max(t['free_places'] for t in trips),
                  'id': max(trips, key=lambda x: x['free_places'])['id']}

        return [result]

    result = []

    for t in trips:
        result.append({'message': f"{message}<b>Свободных мест:</b> {t['free_places']}\n\n"
                                  f"{parse_car_info(t['car'])}\n{parse_driver_info(t['driver'])}",
                       'places': t['free_places'],
                       'id': t['id']})

    return result

# {
#     'id': 29484,
#     'time': '07:00',
#     'date': '2021-10-11',
#     'car': {
#         'id': 18,
#         'mark': 'Mercedes',
#         'model': 'Sprinter',
#         'color': 'Серый',
#         'number': '4TAX5880',
#         'places': 15,
#         'wifi': 1,
#         'tv': 1,
#         'power': 0,
#         'chair': 1,
#         'condition': 0,
#         'created_at': '2019-02-11 08:26:49',
#         'updated_at': '2020-07-21 14:16:10'
#     },
#     'driver': {
#         'id': 19,
#         'name': 'Сергей Соломевич',
#         'phone': '375292863005',
#         'password': '3005',
#         'document_number': 'нету',
#         'driving_experience': 1,
#         'lat': None,
#         'lng': None,
#         'created_at': '2019-02-11 08:41:05',
#         'updated_at': '2019-06-07 09:42:10'
#     },
#     'duration': 180,
#     'free_places': 0,
#     'price': 13,
#     'kids_price': 6.5
# }
