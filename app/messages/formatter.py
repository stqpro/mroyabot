import datetime
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
              f"<b>Время:</b> {trips[0]['time']}\n" \

    if len(trips) > 1 and trips[0]['car'] is None:
        message += f"\n<b>Рейсов:</b> {len(trips)}\n" \
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


def parse_favourite(trip):
    message = f"<b>Маршрут:</b> {trip.departure} – {trip.destination}\n\n" \
              f"<b>Дата:</b> {datetime.datetime.strptime(trip.date, '%Y-%m-%d').strftime('%d/%m/%Y')}\n" \
              f"<b>Время:</b> {trip.time}\n<b>Количество мест:</b> {trip.places}\n\n" \
              f"<b>Добавлен:</b> {trip.created_at.strftime('%d/%m/%Y %H:%M')}"

    return message
