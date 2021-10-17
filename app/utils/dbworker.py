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
    with database.atomic():
        trip = Trip.create(
            user_id=user_id,
            departure=departure,
            destination=destination,
            date=date,
            time=time,
            places=places,
            status=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return trip
