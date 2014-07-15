import logging, datetime, time

from community_share import reminder
from community_share.models.statistics import Statistic

logger = logging.getLogger(__name__)

def do_work():
    logger.info('Running do_work')
    reminder.send_reminders()
    Statistic.check_statistics()
    
default_target_time = datetime.timedelta(seconds=600)

def work_loop(target_time_between_calls=default_target_time, max_loops=None):
    last_call_time = None
    n_loops = 0
    while True:
        last_call_time = datetime.datetime.utcnow() 
        do_work()
        duration = datetime.datetime.utcnow() - last_call_time
        remaining = (target_time_between_calls - duration).total_seconds()
        if remaining > 0:
            time.sleep(remaining)
        n_loops += 1
        if (max_loops is not None) and (n_loops >= max_loops):
            break
