import logging
from datetime import datetime, timedelta
import pytz

from sqlalchemy import Table, ForeignKey, DateTime, Column
from sqlalchemy import Integer, String, Boolean, Float
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql.expression import func
from sqlalchemy import or_, and_

from community_share import time_format, mail_actions
from community_share import store, Base, config
from community_share.models.base import Serializable, ValidationException

logger = logging.getLogger(__name__)

class Share(Base, Serializable):
    __tablename__ = 'share'
    
    MANDATORY_FIELDS = [
        'educator_user_id', 'community_partner_user_id', 'conversation_id',
        'description']
    WRITEABLE_FIELDS = [
        'educator_approved', 'community_partner_approved', 'title', 'description', 'events']
    STANDARD_READABLE_FIELDS = [
        'id', 'educator_user_id', 'community_partner_user_id', 'title' ,
        'description', 'conversation_id', 'active', 'events', 'educator',
        'community_partner'
    ]
    ADMIN_READABLE_FIELDS = [
        'id', 'educator_user_id', 'community_partner_user_id', 'title' ,'description',
        'educator_approved', 'community_partner_approved', 'date_created',
        'conversation_id', 'active', 'events', 'educator', 'community_partner'
    ]

    PERMISSIONS = {
        'all_can_read_many': False,
        'standard_can_read_many': True,
        'admin_can_delete': True
    }

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversation.id'), nullable=False)
    educator_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    community_partner_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    educator_approved = Column(Boolean, default=False, nullable=False)
    community_partner_approved = Column(Boolean, default=False, nullable=False)
    title = Column(String(100), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    description = Column(String, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)

    events = relationship('Event', primaryjoin='and_(Event.share_id == Share.id, Event.active == True)')
    educator = relationship('User', primaryjoin='Share.educator_user_id == User.id')
    community_partner = relationship('User', primaryjoin='Share.community_partner_user_id == User.id')
    conversation = relationship('Conversation')

    @classmethod
    def has_add_rights(cls, data, user):
        has_rights = False
        if user is not None:
            if int(data.get('educator_user_id', -1)) == user.id:
                has_rights = True
            elif int(data.get('community_partner_user_id', -1)) == user.id:
                has_rights = True
        return has_rights

    def has_standard_rights(self, requester):
        has_rights = False
        if requester is not None:
            has_rights = True
        return has_rights

    def has_admin_rights(self, user):
        has_rights = False
        if user.is_administrator:
            has_rights = True
        elif user.id == self.educator_user_id:
            has_rights = True
        elif user.id == self.community_partner_user_id:
            has_rights = True
        return has_rights

    def serialize_events(self, requester):
        serialized = [e.serialize(requester, exclude=['share'])
                      for e in self.events if e.active]
        return serialized

    def deserialize_events(self, data_list):
        logger.debug('deserialize_events')
        if data_list is None:
            data_list = []
        for e in data_list:
            e['share_id'] = self.id
        # Don't set it to self.events because sqlalchemy's automatic
        # updating doesn't work for us.
        self.new_events = [
            Event.admin_deserialize(e) for e in data_list]

    custom_deserializers = {
        'events': deserialize_events,
    }

    def serialize_educator(self, requester):
        return self.educator.serialize(requester)
    def serialize_community_partner(self, requester):
        return self.community_partner.serialize(requester)

    custom_serializers = {
        'educator': serialize_educator,
        'community_partner': serialize_community_partner,
        'events': serialize_events,
    }

    def on_delete(self, requester):
        for e in self.events:
            e.delete(requester)
        mail_actions.send_share_message(self, requester, is_delete=True)
        
    def on_add(self, requester):
        logger.debug('in share on_add')
        mail_actions.send_notify_share_creation(self, requester)        
        self.on_edit(requester, unchanged=False, is_add=True)
    
    def on_edit(self, requester, unchanged=False, is_add=False):
        if not hasattr(self, 'new_events'):
            self.new_events = self.events
        old_event_ids = set([e.id for e in self.events])
        new_event_ids = set([e.id for e in self.new_events])
        to_delete_event_ids = old_event_ids - new_event_ids
        to_add_event_ids = new_event_ids - old_event_ids
        if len(to_add_event_ids) > 0:
            unchanged = False
        # Set unused events to inactive
        for e in self.events:
            if e.id in to_delete_event_ids:
                e.delete(requester)
                unchanged = False
        #store.session.commit()
        # Set self.events to the new events but put the deleted ones in as well
        # otherwise sqlalchemy will try to set share_id to None which we don't
        # want.
        combined_events = self.new_events
        for e in self.events:
            if e.id not in new_event_ids:
                combined_events.append(e)
        self.events = combined_events        
        if not unchanged:
            self.educator_approved = False
            self.community_partner_approved = False
            mail_actions.send_share_message(self, requester, new_share=is_add)
        if requester.id == self.educator_user_id:
            if (not self.educator_approved) and unchanged:
                mail_actions.send_share_message(
                    self, requester, is_confirmation=True)
            self.educator_approved = True
        if requester.id == self.community_partner_user_id:
            if (not self.community_partner) and unchanged:
                mail_actions.send_share_message(
                    self, requester, is_confirmation=True)
            self.community_partner_approved = True
        store.session.add(self)

    @classmethod
    def args_to_query(cls, args, requester):
        # user_id matches to educator_id or community_partner_id
        user_id = args.get('user_id', None)
        query = cls._args_to_query(args, requester)
        if user_id is not None:
            try:
                user_id = int(user_id)
                query = query.filter(
                    or_(Share.educator_user_id==user_id,
                        Share.community_partner_user_id==user_id))
            except ValueError:
                pass
        return query

    def get_url(self):
        url = '{0}/#/share/{1}'.format(config.BASEURL, self.id)
        return url


class Event(Base, Serializable):
    __tablename__ = 'event'

    MANDATORY_FIELDS = [
        'share_id', 'datetime_start', 'datetime_stop', 'location',]
    WRITEABLE_ONCE_FIELDS = ['about_event_id']
    WRITEABLE_FIELDS = [
        'datetime_start', 'datetime_stop', 'title', 'description', 'location',]
    STANDARD_READABLE_FIELDS = [
        'id', 'share_id', 'datetime_start', 'datetime_stop', 'title',
        'description', 'location', 'active', 'share']
    ADMIN_READABLE_FIELDS = [
        'id', 'share_id', 'datetime_start', 'datetime_stop', 'title',
        'description', 'location', 'active', 'share', 'answers']

    PERMISSIONS = {
        'all_can_read_many': False,
        'standard_can_read_many': True,
        'admin_can_delete': True
    }

    id = Column(Integer, primary_key=True)
    share_id = Column(Integer, ForeignKey('share.id'), nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    active = Column(Boolean, default=True, nullable=False)
    datetime_start = Column(DateTime, nullable=False)
    datetime_stop = Column(DateTime, nullable=False)
    title = Column(String(100), nullable=True)
    description = Column(String, nullable=True)
    location = Column(String(100), nullable=False)

    answers = relationship('Answer')
    
    @validates('datetime_start', 'datetime_stop')
    def validate_datetime_start(self, key, datetime_start):
        # Hackish method to check if it's a datetime
        if not hasattr(datetime_start, 'utcnow'):
            converted = time_format.from_iso8601(datetime_start)
            converted = converted.replace(tzinfo=None)
        else:
            converted = datetime_start
        if converted < datetime.utcnow():
            raise ValidationException('Event cannot be in the past.')
        return converted

    # FIXME: Not checking if duration is negative.

    share = relationship('Share')
    reminders = relationship('EventReminder')

    @property
    def formatted_datetime_start(self):
        return time_format.to_pretty(self.datetime_start)

    @property
    def formatted_datetime_stop(self):
        return time_format.to_pretty(self.datetime_stop)

    @classmethod
    def has_add_rights(cls, data, user):
        has_rights = False
        share_id = int(data.get('share_id', -1))
        if share_id >= 0:
            query = store.session.query(Share).filter(Share.id==share_id)
            share = query.first()
            if share is not None:
                if user.id == share.educator_user_id:
                    has_rights = True
                elif user.id == share.community_partner_user_id:
                    has_rights = True
        return has_rights

    def on_add(self, requester):
        self.on_edit(requester, unchanged=False)

    def on_edit(self, requester, unchanged=False):
        logger.debug('event: on_edit')
        if not unchanged:
            share = self.share
            if share is None:
                share = store.session.query(Share).filter_by(id=self.share_id).first()
            share.educator_approved = False
            share.community_partner_approved = False
        if requester.id == share.educator_user_id:
            share.educator_approved = True
        if requester.id == share.community_partner_user_id:
            share.community_partner_approved = True
        logger.debug('ed {0} cp {1}'.format(
            share.educator_approved, share.community_partner_approved))
        store.session.add(share)

    def has_standard_rights(self, requester):
        has_rights = False
        if requester is not None:
            has_rights = True
        return has_rights

    def has_admin_rights(self, user):
        has_rights = False
        if user.is_administrator:
            has_rights = True
        else:
            share = store.session.query(Share).filter(Share.id==self.share_id).first()
            if share is not None:
                if user.id == share.educator_user_id:
                    has_rights = True
                elif user.id == share.community_partner_user_id:
                    has_rights = True
        return has_rights

    def serialize_share(self, requester):
        return self.share.serialize(requester, exclude=['events'])
    def serialize_datetime_start(self, requester):
        return time_format.to_iso8601(self.datetime_start)
    def serialize_datetime_stop(self, requester):
        return time_format.to_iso8601(self.datetime_stop)
    def serialize_answers(self, requester):
        return [a.serialize(requester) for a in self.answers]

    custom_serializers = {
        'share': serialize_share,
        'datetime_start': serialize_datetime_start,
        'datetime_stop': serialize_datetime_stop,
        'answers': serialize_answers,
    }

    @classmethod
    def args_to_query(cls, args, requester):
        # user_id matches to educator_id or community_partner_id of Share
        user_id = args.get('user_id', None)
        query = cls._args_to_query(args, requester)
        if user_id is not None:
            try:
                user_id = int(user_id)
                query = query.join(Share)
                query = query.filter(
                    or_(Share.educator_user_id==user_id,
                        Share.community_partner_user_id==user_id))
            except ValueError(e):
                logger.warning('Error trying to get user_id: {0}'.format(e))
        
        return query

    def get_url(self):
        url = '{0}/#/event/{1}'.format(config.BASEURL, self.id)
        return url


class EventReminder(Base):
    __tablename__ = 'eventreminder'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('event.id'), nullable=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    typ = Column(String(20), nullable=False)
    
    @classmethod
    def get_oneday_reminder_events(cls):
        typ = 'oneday_before'
        # Get all events starting in the next day.
        now = datetime.utcnow()
        one_day_in_future = now + timedelta(hours=24)
        query = store.session.query(Event)
        query = query.filter(Event.datetime_start < one_day_in_future)
        query = query.filter(Event.datetime_start > now)
        events = query.all()
        unreminded_events = []
        for event in events:
            oneday_before_reminders = [r for r in event.reminders if r.typ == typ]
            if not oneday_before_reminders:
                unreminded_events.append(event)
        return unreminded_events

    @classmethod
    def get_review_reminder_events(cls):
        typ = 'review'
        # Get all events that finished more than a day ago.
        now = datetime.utcnow()
        one_day_in_past = now - timedelta(hours=24)
        two_days_in_past = now - timedelta(hours=48)
        query = store.session.query(Event)
        query = query.filter(Event.datetime_stop < one_day_in_past)
        query = query.filter(Event.datetime_stop > two_days_in_past)
        events = query.all()
        unreminded_events = []
        for event in events:
            review_reminders = [r for r in event.reminders if r.typ == typ]
            if not review_reminders:
                unreminded_events.append(event)
        return unreminded_events
        
