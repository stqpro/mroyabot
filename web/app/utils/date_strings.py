import datetime
import re

weekdays = [
    'понедельник',
    'вторник',
    'среда',
    'четверг',
    'пятница',
    'суббота',
    'воскресенье'
]

adapted_weekdays = [
    'понедельник',
    'вторник',
    'среду',
    'четверг',
    'пятницу',
    'субботу',
    'воскресенье'
]

months = [
    'января',
    'февраля',
    'марта',
    'апреля',
    'мая',
    'июня',
    'июля',
    'августа',
    'сентября',
    'октября',
    'ноября',
    'декабря'
]


def generate_date_strings(offset=2, length=15):
    dates = []
    current_date = datetime.datetime.today() + datetime.timedelta(days=offset)

    for i in range(length):
        dates.append(f"{weekdays[current_date.weekday()]}, {current_date.day} {months[current_date.month - 1]}")
        current_date += datetime.timedelta(days=1)

    return dates


def parse_date_string(date_string: str):
    if date_string.lower() == 'сегодня':
        return datetime.datetime.today().strftime('%Y-%m-%d')

    if date_string.lower() == 'завтра':
        return (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    if date_string.lower() == 'послезавтра':
        return (datetime.datetime.today() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')

    dates = generate_date_strings(offset=0, length=30)

    for idx, date in enumerate(dates):
        if date_string.lower() == date:
            return (datetime.datetime.today() + datetime.timedelta(days=idx)).strftime('%Y-%m-%d')

    formats_with_year = ['%d/%m/%y', '%d/%m/%Y', '%d.%m.%y', '%d.%m.%Y', '%d-%m-%y', '%d-%m-%Y']

    for fmt in formats_with_year:
        try:
            parsed_date = datetime.datetime.strptime(date_string, fmt)
            if -2 < (parsed_date - datetime.datetime.today()).days < 30:  # today .. 30 days
                return parsed_date.strftime('%Y-%m-%d')

        except ValueError:
            pass

    formats_without_year = ['%d/%m', '%d.%m', '%d-%m']

    for fmt in formats_without_year:
        try:
            parsed_date = datetime.datetime.strptime(date_string, fmt).replace(year=datetime.datetime.today().year)
            if -2 < (parsed_date - datetime.datetime.today()).days < 30:  # today .. 30 days
                return parsed_date.strftime('%Y-%m-%d')
            else:
                parsed_date = datetime.datetime.strptime(date_string, fmt)\
                    .replace(year=datetime.datetime.today().year + 1)
                if -2 < (parsed_date - datetime.datetime.today()).days < 30:  # today .. 30 days
                    return parsed_date.strftime('%Y-%m-%d')

        except ValueError:
            pass

    return None


def generate_readable_date(date: str) -> str:
    parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    return f"{adapted_weekdays[parsed_date.weekday()]}, {parsed_date.day} {months[parsed_date.month - 1]}"
