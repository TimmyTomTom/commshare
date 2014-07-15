# http://stackoverflow.com/questions/969285/how-do-i-translate-a-iso-8601-datetime-string-into-a-python-datetime-object

import datetime
import pytz

utc = pytz.utc
ARIZONA = pytz.timezone('US/Arizona')

PRETTY_FORMAT = "%A %d %B %Y %I:%M %p"
FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"

def to_iso8601(when):
    _when = when.strftime(FORMAT)
    return _when + 'Z'

def to_pretty(when):
    '''
    Received a datetime assumed to be UTC.
    Formats it as a pretty AZ datetime.
    '''
    when = when.replace(tzinfo=utc)
    when = when.astimezone(ARIZONA)
    _when = when.strftime(PRETTY_FORMAT) + ' (Arizona time)'
    return _when

def from_iso8601(when=None, tz=ARIZONA):
    if when.endswith('Z'):
        when = when[:-1] + '+0000'
    _when = datetime.datetime.strptime(when, FORMAT)
    if not _when.tzinfo:
        _when = tz.localize(_when)
    return _when
