from peewee import *

from datetime import datetime

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
            trips = Trip.select().where(Trip.user_id == user_id and Trip.status == True).order_by(Trip.date, Trip.time)

    database.close()
    return trips


def update_status(trip, status):
    database.connect(reuse_if_open=True)

    with database.atomic():
        query = Trip.update({Trip.status: status, Trip.updated_at: datetime.now()}).where(Trip.id == trip)
        result = query.execute()

    database.close()
    return result
