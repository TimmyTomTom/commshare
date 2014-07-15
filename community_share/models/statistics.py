import datetime
import time

import logging

from sqlalchemy import Column, Integer, String, Date, Float, or_

from community_share import Base, store
from community_share.models.user import User, UserReview
from community_share.models.conversation import Conversation
from community_share.models.share import Share, Event

logger = logging.getLogger(__name__)

class Statistic(Base):
    __tablename__ = 'statistic'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    value = Column(Float, nullable=False)

    @staticmethod
    def date_now():
        now = datetime.datetime.utcnow()
        today = now.date()
        return today

    @staticmethod
    def date_yesterday():
        now = datetime.datetime.utcnow()
        today = now.date()
        yesterday = today - datetime.timedelta(days=1)
        return yesterday


    @classmethod
    def get_statistics(cls, date):
        stats = store.session.query(cls).filter(cls.date==date).all()
        if len(stats) == 0:
            cls.update_statistics(date)
            stats = store.session.query(cls).filter(cls.date==date).all()
        combined = {}
        for stat in stats:
            combined[stat.name] = stat.value
        return combined

    @classmethod
    def check_statistics(cls):
        yesterday = cls.date_yesterday()
        for days_ago in range(30):
            date = yesterday - datetime.timedelta(days=days_ago)
            n_stats = store.session.query(cls).filter(cls.date==date).count()
            if n_stats == 0:
                cls.update_statistics(date)

    @classmethod
    def update_statistics(cls, date, force=False):
        # Get existing statistics for that date.
        stats = store.session.query(cls).filter(cls.date==date).all()
        old_stats = {}
        for stat in stats:
            old_stats[stat.name] = stat
        new_stats = cls.calculate_statistics(date)
        for key, value in new_stats.items():
            if value is not None:
                if key not in old_stats:
                    stat = Statistic(name=key, value=value, date=date)
                    store.session.add(stat)
                elif force:
                    old_stats[key].value = value
                    store.session.add(old_stats[key])
        store.session.commit()

    active_statistics = [
        'n_new_users', 
        'n_total_users',
        'n_users_active_in_last_month',
        'n_users_started_conversation',
        'n_users_did_event',
        'n_users_reviewed_event',
        'n_events_done',
        'n_total_events_done',
        'n_upcoming_events',
    ]

    @classmethod
    def calculate_statistics(cls, date):
        statistics = {}
        for stat_name in cls.active_statistics:
            func_name = 'calculate_{}'.format(stat_name)
            stat_func = getattr(cls, func_name, None)
            if stat_func is None:
                logger.error('Failed to find statistic function for {}'.format(
                    stat_name))
            else:
                statistics[stat_name] = stat_func(date)
        return statistics

    @staticmethod
    def calculate_n_new_users(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        # Users created in time period
        n_new_users = store.session.query(User).filter(
            User.date_created > start_of_period,
            User.date_created < end_of_period).count()
        return n_new_users

    @staticmethod
    def calculate_n_total_users(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        # Total number of users.
        n_total_users = store.session.query(User).filter(
            User.date_created < end_of_period,
            or_(User.date_inactivated == None, User.date_inactivated > end_of_period)
        ).count()
        return n_total_users

    @staticmethod
    def calculate_n_users_active_in_last_month(date):
        # Total users active in the last 30 days.
        # We can only do this if we're processing the results for yesterday.
        now = datetime.datetime.utcnow()
        today = now.date()
        n_active_users_in_last_month = None
        if date + datetime.timedelta(days=1) == today:
            one_month_ago = today - datetime.timedelta(days=30)
            n_active_users_in_last_month = store.session.query(User).filter(
                User.last_active > one_month_ago,
                User.active == True
            ).count()
        return n_active_users_in_last_month;

    @staticmethod
    def calculate_n_users_started_conversation(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        # Number of users who have started a conversation
        query = store.session.query(User)
        query = query.join(Conversation, Conversation.userA_id==User.id)
        query = query.filter(Conversation.date_created > start_of_period,
                             Conversation.date_created < end_of_period)
        n_users_started_conversation = query.count()
        return n_users_started_conversation

    @staticmethod
    def calculate_n_users_did_event(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        # Number of users who did an event
        query = store.session.query(User)
        query = query.join(
            Share, or_(Share.educator_user_id==User.id,
                       Share.community_partner_user_id==User.id))
        query = query.join(Event)
        query = query.filter(Event.datetime_stop > start_of_period,
                             Event.datetime_stop < end_of_period)
        n_users_did_event = query.count()        
        return n_users_did_event

    @staticmethod
    def calculate_n_users_reviewed_event(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        # Number of users who reviewed an event
        query = store.session.query(User)
        query = query.join(
            UserReview, UserReview.creator_user_id==User.id)
        query = query.filter(UserReview.date_created > start_of_period,
                             UserReview.date_created < end_of_period)
        n_users_reviewed_event = query.count()
        return n_users_reviewed_event

    @staticmethod
    def calculate_n_events_done(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        query = store.session.query(Event)
        query = query.filter(Event.datetime_stop > start_of_period,
                             Event.datetime_stop < end_of_period,
                             Event.active == True)
        n_events_done = query.count()
        return n_events_done

    @staticmethod
    def calculate_n_total_events_done(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        query = store.session.query(Event)
        query = query.filter(Event.datetime_stop < end_of_period,
                             Event.active == True)
        n_total_events_done = query.count()
        return n_total_events_done
        
    @staticmethod
    def calculate_n_upcoming_events(date):
        start_of_period = datetime.datetime.combine(date, datetime.time())
        end_of_period = start_of_period + datetime.timedelta(days=1)
        query = store.session.query(Event)
        query = query.filter(
            Event.date_created < end_of_period,
            Event.datetime_stop > end_of_period,
            Event.active == True)
        n_upcoming_events = query.count()
        return n_upcoming_events
        
