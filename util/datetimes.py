import datetime
import time
from datetime import timedelta


def to_now():
    return datetime.datetime.now()


def to_current_timestamp():
    return int(time.time()) * 1000


def to_date_relative(d, delta):
    return d + timedelta(days=delta)


def to_string(d, f):
    return d.strftime(f)


def to_days_diff(d1, d2):
    return (d1 - d2).days


def to_date(s, f):
    return datetime.datetime.strptime(s, f)


def to_days_diff_f(d1, d2, f):
    return to_days_diff(to_date(d1, f), to_date(d2, f))


def to_last_month_end(f):
    d = datetime.date(day=1,
                      month=datetime.datetime.now().month,
                      year=datetime.datetime.now().year) - timedelta(days=1)
    return to_string(d,f)


