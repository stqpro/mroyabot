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


def generate_date_keyboard():
    dates = []
    current_date = datetime.datetime.today()

    for i in range(15):
        dates.append(f"{weekdays[current_date.weekday()]}, {current_date.day} {months[current_date.month - 1]}")
        current_date += datetime.timedelta(days=1)

    return dates
