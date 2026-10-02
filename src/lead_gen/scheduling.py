import secrets

from datetime import date, time, datetime, timezone, timedelta

from dataclasses import dataclass


def time_to_seconds(t: time) -> int:
    return t.hour * 60 * 60 + t.minute * 60 + t.second


def seconds_to_time(s: int) -> time:
    hour = s // 60 // 60
    minute = s // 60 % 60
    second = s % 60

    return time(hour, minute, second, 0, timezone.utc)


@dataclass
class Rules:
    "The days and times at which emails can be sent."

    time_from: time
    "The earliest time of the day an email can be sent at."
    time_to: time
    "The latest time of the day an email can be sent at."
    days: list[int]
    "Weekdays from 0 (Monday) to 6 (Sunday)."
    daily_max: int
    "The max amount of emails to send per day."

    def get_soonest_allowed_datetime(self, dt: datetime) -> datetime:
        while True:
            if dt.weekday() not in self.days or dt.time() > self.time_to:
                dt += timedelta(days=1)
                dt = min(dt, datetime.combine(dt.date(), self.time_from, timezone.utc))
                continue

            if dt.time() < self.time_from:
                dt = datetime.combine(dt.date(), self.time_from, timezone.utc)

            return dt


class Calendar[T]:
    "An email sending calendar, consisting of multiple scheduled Events."

    rules: Rules
    "The rules this calendar will follow."
    starting: datetime
    "The first date and time events can be scheduled."

    usage: dict[date, list["Event[T]"]]
    "Events organized per date."
    index: dict[str, date]
    "A map of each event's ID to the date they were scheduled for."

    def __init__(self, rules: Rules, starting: datetime = None) -> None:
        self.rules = rules
        self.usage = {}
        self.index = {}

        if starting is None:
            self.starting = datetime.now(timezone.utc)
        else:
            self.starting = starting

    def schedule(
        self,
        data: T,
        *,
        after_id: str | None = None,
        after_time: timedelta | None = None,
    ) -> "Event[T]":
        starting = self.starting

        if after_id is not None:
            if after_id not in self.index:
                raise ValueError(f"`{after_id}` is not in this calendar.")

            starting = datetime.combine(self.index[after_id], self.rules.time_from, timezone.utc)

            if after_time is not None:
                starting += after_time

        schedule = self.rules.get_soonest_allowed_datetime(starting)
        while True:
            schedule_date = schedule.date()
            schedule_events = self.usage.setdefault(schedule_date, [])

            if len(schedule_events) < self.rules.daily_max:
                schedule_time_seconds = secrets.choice(
                    range(
                        time_to_seconds(self.rules.time_from),
                        time_to_seconds(self.rules.time_to),
                    )
                )
                schedule_time = seconds_to_time(schedule_time_seconds)

                schedule = datetime.combine(schedule_date, schedule_time, timezone.utc)
                event = Event(schedule, data)

                self.usage[schedule_date].append(event)
                self.index[event.id] = schedule_date

                return event

            else:
                schedule += timedelta(days=1)
                schedule = self.rules.get_soonest_allowed_datetime(schedule)

    def insert(self, data: T, dt: datetime) -> "Event[T]":
        event = Event(dt, data)

        self.usage.setdefault(dt.date(), []).append(event)
        self.index[event.id] = dt.date()

        return event


class Event[T]:
    "An event in a calendar (an email scheduled to be sent)."

    id: str
    dt: datetime

    data: T

    def __init__(self, dt: datetime, data: T) -> None:
        id = secrets.token_hex(32)

        self.id = id
        self.dt = dt
        self.data = data
