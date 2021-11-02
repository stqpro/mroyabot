from peewee import *

from datetime import datetime

from app.messages.formatter import parse_notification
from app.utils.data_requests import get_trips

database = SqliteDatabase('bot.db')


class BaseModel(Model):
    class Meta:
        database = database


class Trip(BaseModel):
    user_id = CharField(max_length=12)
    departure = CharField(max_length=16)
    destination = CharField(max_length=16)
    date = DateField('%Y-%m-%d')
    time = TimeField('%H:%M')
    places = IntegerField()
    status = BooleanField()
    created_at = DateTimeField()
    updated_at = DateTimeField()


def create_trip(user_id, departure, destination, date, time, places):
    database.connect(reuse_if_open=True)

    with database.atomic():
        trip = Trip.create(
            user_id=user_id,
            departure=departure,
            destination=destination,
            date=date,
            time=time,
            places=places,
            status=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    database.close()
    return trip


def get_user_trips(user_id, active=False):
    database.connect(reuse_if_open=True)

    with database.atomic():
        if not active:
            trips = Trip.select().where(Trip.user_id == user_id).order_by(Trip.date, Trip.time)
        else:
            trips = Trip.select().where((Trip.user_id == user_id) & (Trip.status == True)) \
                .order_by(Trip.date, Trip.time)

    database.close()
    return trips


def update_trip(trip, status, places=None):
    database.connect(reuse_if_open=True)

    with database.atomic():
        if not places:
            query = Trip.update({Trip.status: status, Trip.updated_at: datetime.now()}).where(Trip.id == trip)
        else:
            query = Trip.update({Trip.status: status, Trip.places: places, Trip.updated_at: datetime.now()})\
                .where(Trip.id == trip)
        result = query.execute()

    database.close()
    return result


def get_active_dates():
    database.connect(reuse_if_open=True)

    with database.atomic():
        trips = Trip.select(Trip.date, Trip.departure, Trip.destination).distinct().where(Trip.status == True)

    database.close()
    return trips


def check_active_records(date: str, departure: str, destination: str, time: str, places: int):
    database.connect(reuse_if_open=True)

    with database.atomic():
        trips = Trip.select(Trip.id, Trip.user_id, Trip.places).where(
            (Trip.date == date) & (Trip.time == time) & (Trip.status == True) & (Trip.departure == departure) &
            (Trip.places <= places) & (Trip.destination == destination))

    database.close()

    return trips


def check_trips():
    messages = []

    database.connect(reuse_if_open=True)

    with database.atomic():
        dates = Trip.select(Trip.date, Trip.departure, Trip.destination).distinct().where(Trip.status == True)

    for item in dates:
        trips = get_trips(item.date, item.departure, item.destination)

        if trips is None:
            continue

        for trip in trips:
            concurrences = Trip.select(Trip.id, Trip.user_id, Trip.places).where(
                (Trip.date == trip['date']) & (Trip.time == trip['time']) & (Trip.status == True) & (
                        Trip.departure == item.departure) &
                (Trip.places <= trip['free_places']) & (Trip.destination == item.destination))

            for c in concurrences:
                messages.append((c.user_id, *parse_notification(item.departure, item.destination, trip['date'],
                                                                trip['time'], c.places, trip['id'])))

            query = Trip.update({Trip.status: False, Trip.updated_at: datetime.now()}) \
                .where(Trip.id << [c.id for c in concurrences])
            query.execute()

    database.close()

    return messages


def clear_trips():
    database.connect(reuse_if_open=True)

    with database.atomic():
        times = Trip.select(Trip.date, Trip.time).distinct()

        for t in times:
            trip_time = datetime.strptime(f"{t.date} {t.time}", '%Y-%m-%d %H:%M')

            if trip_time < datetime.now():
                query = Trip.delete().where((Trip.date == t.date) & (Trip.time == t.time))
                query.execute()

    database.close()


def get_stats():
    database.connect(reuse_if_open=True)

    with database.atomic():
        unique_users = Trip.select(Trip.user_id).distinct().count()
        active_followings = Trip.select().where(Trip.status == True).count()

    database.close()

    return unique_users, active_followings
