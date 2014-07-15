import logging
import os
import datetime

from flask import jsonify

from community_share.authorization import get_requesting_user
from community_share import config, store, time_format
from community_share.models.statistics import Statistic
from community_share.routes import base_routes

def get_new_user_statistics():
    '''
    number of new users each day
    number of events each day
    number of event reviews each day
    number of messages sent each day
    number of users active each day
    number of users active in last month
    '''
    now = datetime.datetime.utcnow()
    one_year_ago = now - datetime.timedelta(years=1)
    last_year_new_users = store.session.query(User).filter(
        User.date_created > one_year_ago).all()
    
    new_user_stats = {
        'last year': {
            'new number': len(last_year_new_users)
        },
    }
    

logger = logging.getLogger(__name__)

def register_statistics_routes(app):

    @app.route('/api/statistics', methods=['GET'])
    def statistics():
        requester = get_requesting_user()
        if requester is None:
            response = base_routes.make_not_authorized_response()
        elif not requester.is_administrator:
            response = base_routes.make_forbidden_response()
        else:
            yesterday = Statistic.date_yesterday()
            response_data = {'data': {}}
            for days_ago in range(30):
                date = yesterday - datetime.timedelta(days=days_ago)
                stats = Statistic.get_statistics(date)
                response_data['data'][time_format.to_iso8601(date)] = stats
            response = jsonify(response_data)
        return response
