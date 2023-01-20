import datetime

from spinningjenny.jobs.shared.models import eclipse_dates


def test__get_dates_from_schedule():
    first = "DATES\n 01 'JAN' 2000 /\n\n\n/"
    second = "DATES\n\n\n\t2  JAN  2000    12:03:06.1232 /\n/"
    comment = "-- DATES\n\n 25 JAN 2001 /\n/"
    third = 'DATES\n\n 28   "JLY" 2015     /\n\n\t/'
    fourth = "DATES\n1 JAN 2020 /\n/"
    fifth = "DATES\n 1 FEB 2020/\n/"
    for item, (date, value) in zip(
        eclipse_dates(f"{first}\n\n{second}\n{comment}\n{third}\n\n{fourth}\n{fifth}"),
        (
            (datetime.date(2000, 1, 1), first),
            (datetime.date(2000, 1, 2), second),
            (datetime.date(2015, 7, 28), third),
            (datetime.date(2020, 1, 1), fourth),
            (datetime.date(2020, 2, 1), fifth),
        ),
    ):
        assert item.date == date
        assert not item.for_insertion
        assert item.value == value
