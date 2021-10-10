import datetime

weekdays = [
    'понедельник',
    'вторник',
    'среда',
    'четверг',
    'пятница',
    'суббота',
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


def parse_date_string(date_string: str):  # TODO: add more parsing items
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

    return None
