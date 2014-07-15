import logging

from community_share import store, mail_actions
from community_share.models import conversation
from community_share.models.share import EventReminder

logger = logging.getLogger(__name__)

ONEDAY_EVENT_REMINDER_TEMPLATE = '''You have an share coming up with {{otheruser.name}}
'''

def send_reminders():
    # Send reminders before events happen.
    events = EventReminder.get_oneday_reminder_events()
    if events:
        logger.info('Sending reminders for {} events'.format(len(events)))
        event_reminders = [EventReminder(event_id=event.id, typ='oneday_before')
                           for event in events]
        for reminder in event_reminders:
            store.session.add(reminder)
        store.session.commit()
        for event in events:
            mail_actions.send_event_reminder_message(event)

    # Send review reminder one day after they finish.
    events = EventReminder.get_review_reminder_events()
    if events:
        logger.info('Sending review reminders for {} events'.format(len(events)))
        event_reminders = [EventReminder(event_id=event.id, typ='review')
                           for event in events]
        for reminder in event_reminders:
            store.session.add(reminder)
            store.session.commit()
            for event in events:
                users = [event.share.educator, event.share.community_partner]
                for user in users:
                    # FIXME: Would be nice to have a check in case they
                    # already reviewed it.
                    mail_actions.send_review_reminder_message(user, event)
