from enum import Enum


class Action(Enum):
    FOLLOW_START = '0'
    FOLLOW_PLACES = '1'
    RESERVE_START = '2'
    RESERVE_PLACES = '3'
    BOOKING_START = '4'
    BOOKING_PLACES = '5'
    CANCEL = '6'
    FOLLOW_DATE = '7'
