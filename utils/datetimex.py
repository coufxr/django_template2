import calendar
import datetime

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, rrule


def ts2datetime(ts: int) -> datetime.datetime:
    """
    return %Y-%m-%d %H:%M:%S
    """
    tm = float(ts / 1000)
    tm = datetime.datetime.fromtimestamp(tm)
    return tm


def datetime2ts(date: datetime.datetime) -> int:
    """
    return timestamp int(13)
    """
    return int(date.timestamp() * 1000)


def timestamp2str(ts: int, fmt="%Y%m%d") -> str:
    return ts2datetime(ts).strftime(fmt)


def str2timestamp(string: str) -> int:
    return int(parse(str(string)).timestamp() * 1000)


def str2datetime(string: str) -> datetime.datetime:
    return parse(str(string))


def datetime2str(date: datetime.datetime, fmt="%Y%m%d") -> str:
    return date.strftime(fmt)


# 月,周,日的开始/结束


def day_begin(date: datetime.datetime) -> datetime.datetime:
    """
    return %Y-%m-%d 00:00:00
    """
    return datetime.datetime.combine(date, datetime.datetime.min.time())


def day_end(date: datetime.datetime) -> datetime.datetime:
    """
    return %Y-%m-%d 23:59:59
    """
    return datetime.datetime.combine(date, datetime.datetime.max.time())


def week_begin(date: datetime.datetime) -> datetime.datetime:
    """
    return 周一 %Y-%m-%d 00:00:00
    """
    date = move_day(date, -date.weekday())
    return day_begin(date)


def week_end(date: datetime.datetime) -> datetime.datetime:
    """
    return 周末 %Y-%m-%d 23:59:59
    """
    date = move_day(date, 6 - date.weekday())
    return day_end(date)


def month_begin(date: datetime.datetime) -> datetime.datetime:
    """
    return %Y-%m-1 00:00:00
    """
    date = date.replace(day=1)
    return day_begin(date)


def month_end(date: datetime.datetime) -> datetime.datetime:
    """
    return %Y-%m-(最后一天) 23:59:59
    """
    date = date.replace(day=calendar.monthrange(date.year, date.month)[1])
    return day_end(date)


def is_month_last_day(date: datetime.datetime) -> bool:
    """
    是否是这个月的最后一天
    """
    return date.day == calendar.monthrange(date.year, date.month)[1]


def move_day(date: datetime.datetime, day: int) -> datetime.datetime:
    """
    Before & After
    day: 正数:以后;负数:以前
    """
    return date + relativedelta(days=day)


def seconds_remaining() -> int:
    """
    :return: 截止到当前当日剩余秒数
    """
    today = datetime.datetime.today()
    end_date = day_end(today)
    return (end_date - today).seconds


def split_date_range(
    start_dt: datetime.datetime, end_dt: datetime.datetime, fmt: str = "%Y%W"
) -> list[datetime.datetime]:
    """
    Args:
        start_dt: datetime.datetime
        end_dt:datetime.datetime
        fmt: str;  datetime.format param
    """
    date_list = rrule(dtstart=start_dt, until=end_dt, freq=DAILY)
    result = set(map(lambda x: x.strftime(fmt), date_list))
    result = sorted(list(result))
    return result


def ms_to_hours(milliseconds: int) -> tuple[int, int, int]:
    """毫秒转时分秒"""
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return hours, minutes, seconds


def quarter_start_end(dt: datetime) -> tuple[datetime.datetime, datetime.datetime]:
    """获取一个季度的开始和结束"""
    start_time = datetime.datetime(year=dt.year, month=(dt.month - 1) * 3 + 1, day=1)
    end_time = start_time + relativedelta(months=3)
    return start_time, end_time
