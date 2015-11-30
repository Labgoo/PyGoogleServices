from datetime import timedelta, datetime


__author__ = 'ekampf'

def get_table_id(table_id, d):
    return "{table_id}{day}".format(table_id=table_id, day=d.strftime("%Y%m%d"))


def get_daily_table_names(name_pattern, days_ahead):
    today = datetime.utcnow()
    return [get_table_id(name_pattern, today + timedelta(days=d)) for d in xrange(days_ahead)]
