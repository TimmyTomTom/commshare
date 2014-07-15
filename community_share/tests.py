import re
import os
import unittest
from unittest import mock
import logging
import json
import datetime

from flask import jsonify

from community_share import setup, app, mail, config, time_format, store
from community_share.models.share import EventReminder, Event
from community_share.models.user import User
from community_share.models.conversation import Conversation
from community_share.models.statistics import Statistic
from community_share import reminder, worker
from community_share.crypt import CryptHelper

logger = logging.getLogger(__name__)

sample_userA = {
    'institution_associations': [],
    'name': 'Charles',
    'bio': 'I am Charles.',
    'zipcode' :'12345',
    'email': "charlies@notarealemail.com",
    'password': 'booooooo'
}

sample_userB = {
    'institution_associations': [],
    'name': 'Rob',
    'bio': 'I am Rob.',
    'zipcode' :'12345',
    'email': "rob@notarealemail.com",
    'password': 'oiuh298n[;w',
}

sample_userC = {
    'institution_associations': [],
    'name': 'Charlie',
    'bio': 'AAAAAAAAAAAAAhhhhhhhhhhh!!!!',
    'zipcode' :'12345',
    'email': "charlie@notarealemail.com",
    'password': 'oiuh298n[;wbosijdfkow',
}

def chop_link(link):
    start = config.BASEURL
    assert(link.startswith(start))
    chopped_link = link[len(start):]
    chopped_link = chopped_link.split('#')[0]
    return chopped_link

def compare_data(userA, userB, exclusions=set([])):
    for key, value in userA.items():
        if key not in exclusions:
            assert(userA[key] == userB[key])

def make_headers(api_key=None, email=None, password=None):
    headers = [('Content-Type', 'application/json')]
    if api_key:
        authorization_header = 'Basic:api:{0}'.format(api_key)
    elif email and password:
        authorization_header = 'Basic:{0}:{1}'.format(email, password)
    else:
        authorization_header = None
    if authorization_header:
        headers.append(('Authorization', authorization_header))
    return headers

class CommunityShareTestCase(unittest.TestCase):
    
    SQLLITE_FILE = '/tmp/test.db'

    def setUp(self):
        data = {
            'DB_CONNECTION': 'sqlite:///{}'.format(self.SQLLITE_FILE),
            'MAILER_TYPE': 'QUEUE',
            'MAILGUN_API_KEY': 'whatever',
            'MAILGUN_DOMAIN': 'whatever',
            'LOGGING_LEVEL': 'DEBUG',
            'DONOTREPLY_EMAIL_ADDRESS': 'whatever@communityshare.us',
            'SUPPORT_EMAIL_ADDRESS': 'whatever@communityshare.us',
            'BUG_EMAIL_ADDRESS': 'whatever@communityshare.us',
            'ABUSE_EMAIL_ADDRESS': 'whatever@communityshare.us',
            'NOTIFY_EMAIL_ADDRESS': 'whatever@communityshare.us',
            'ADMIN_EMAIL_ADDRESSES': 'whatever@communityshare.us',
            'BASEURL': 'localhost:5000/',
            'S3_BUCKETNAME': os.environ['COMMUNITYSHARE_S3_BUCKETNAME'],
            'S3_KEY': os.environ['COMMUNITYSHARE_S3_KEY'],
            'S3_USERNAME': os.environ['COMMUNITYSHARE_S3_USERNAME'],
            'UPLOAD_LOCATION': os.environ['COMMUNITYSHARE_UPLOAD_LOCATION'],
            'COMMIT_HASH': 'dummy123',
            'ENCRYPTION_KEY': CryptHelper.generate_key(),
        }
        config.load_from_dict(data)
        setup.init_db()
        # Clear mail queue
        mailer = mail.get_mailer()
        while len(mailer.queue):
            mailer.pop()
        self.app = app.make_app().test_client()

    def sign_up(self, user_data):
        data = {
            'password': user_data['password'],
            'user': user_data,
            }
        serialized = json.dumps(data)
        headers = [('Content-Type', 'application/json')]
        rv = self.app.post('/api/usersignup', data=serialized, headers=headers)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))
        user_id = data['data']['id']
        api_key = data['apiKey']
        authorization_header = 'Basic:api:{0}'.format(api_key)
        headers = [('Authorization', authorization_header)]
        # Create an authentication header
        # And try to retrieve user
        rv = self.app.get('/api/user/{0}'.format(user_id), headers=headers)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))
        # User details should match
        compare_data(user_data, data['data'], exclusions=['password'])
        mailer = mail.get_mailer()
        # We should have one email in queue (email confimation from signup)
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        links = email.find_links()
        assert(len(links)==1)
        email_key = re.search('key=(.*)', links[0]).groups()[0]
        return user_id, api_key, email_key

    def confirm_email(self, key):
        # Confirm email for new user
        headers = [('Content-Type', 'application/json')]
        data = json.dumps({'key': key})
        rv = self.app.post('/api/confirmemail', data=data,
                           headers=headers)
        assert(rv.status_code == 200)
        

    def save_search(self, user_id, headers,
                    searcher_role, searching_for_role, labels):
        data = {
            'searcher_user_id': user_id,
            'searcher_role': searcher_role,
            'searching_for_role': searching_for_role,
            'labels': labels,
            'zipcode': 12345
        }
        serialized = json.dumps(data)
        rv = self.app.post('/api/search', data=serialized, headers=headers)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))
        search_id = data['data']['id']
        return search_id

    def send_message(self, conversation_id, sender_user_id, content, api_key):
        message_data = {
            'conversation_id': conversation_id,
            'sender_user_id': sender_user_id,
            'content': content,
        }
        serialized = json.dumps(message_data)
        headers = make_headers(api_key)
        rv = self.app.post(
            '/api/message', headers=headers, data=serialized)
        assert(rv.status_code == 200)
        return rv

    def create_searches(self, user_ids, user_headers):
        # userA creates a search of educator for partner
        searchA_id = self.save_search(
            user_ids['userA'], user_headers['userA'], 'educator', 'partner',
            ['robot dogs', 'walks on the beach'])
        assert(searchA_id >= 0)
        # userB creates a search of partner to educator
        searchB_id = self.save_search(
            user_ids['userB'], user_headers['userB'], 'partner', 'educator',
            ['robot dogs', 'walks on the beach'])
        assert(searchB_id >= 0)
        return (searchA_id, searchB_id)

    def create_users(self, user_datas):
        user_ids = {}
        user_headers = {}
        for key, user_data in user_datas.items():
            user_id, api_key, email_key = self.sign_up(user_data)
            self.confirm_email(email_key)
            user_ids[key] = user_id
            user_headers[key] = make_headers(api_key)
        return (user_ids, user_headers)

    def make_conversation(self, headers, search_id, title, userA_id, userB_id):
        conversation_data = {
            'search_id': search_id,
            'title': title,
            'userA_id': userA_id,
            'userB_id': userB_id,
        }
        serialized = json.dumps(conversation_data)
        rv = self.app.post(
            '/api/conversation', headers=headers, data=serialized)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))['data']
        return data

    FAKE_TIME_SHIFT = 0

    class FakeDateTime():
        def utcnow():
            logger.debug('Getting fake utcnow')
            fake_time =  datetime.datetime.utcnow() - datetime.timedelta(
                hours=CommunityShareTestCase.FAKE_TIME_SHIFT)
            logger.debug('shift is {} fake now is {}'.format(
                CommunityShareTestCase.FAKE_TIME_SHIFT, fake_time))
            return fake_time

    @mock.patch('community_share.models.share.datetime', FakeDateTime)
    def make_share(
            self, headers, conversation_id,
            educator_user_id, community_partner_user_id,
            starting_in_hours=24,
            location='Somewhere', duration=1,
            title='Trip to moon',
            description='Is the moon made of Cheese?',
            force_past_events=False):
        if force_past_events:
            CommunityShareTestCase.FAKE_TIME_SHIFT = 1000
        else:
            CommunityShareTestCase.FAKE_TIME_SHIFT = 0
        now = datetime.datetime.utcnow()
        starting = now + datetime.timedelta(hours=starting_in_hours)
        ending = now + datetime.timedelta(hours=starting_in_hours + duration)
        share_data = {
            'title': title,
            'description': description,
            'conversation_id': conversation_id,
            'educator_user_id': educator_user_id,
            'community_partner_user_id': community_partner_user_id,
            'events': [
                {'location': location,
                 'datetime_start': time_format.to_iso8601(starting),
                 'datetime_stop': time_format.to_iso8601(ending),},
            ]
        }
        serialized = json.dumps(share_data)
        rv = self.app.post(
            '/api/share', headers=headers, data=serialized)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))['data']
        return data

    def test_statistics(self):
        user_datas = {
            'userA': sample_userA,
            'userB': sample_userB,
        }
        user_ids, user_headers = self.create_users(user_datas)
        # userA is not an administrator so we should get forbidden.
        rv = self.app.get(
            '/api/statistics', headers=user_headers['userA'])
        assert(rv.status_code == 403)
        # Make userA an administrator
        userA = store.session.query(User).filter(
            User.id==user_ids['userA']).first()
        userA.is_administrator = True
        store.session.add(userA)
        store.session.commit()
        # Now we should get stats
        rv = self.app.get(
            '/api/statistics', headers=user_headers['userA'])
        assert(rv.status_code == 200)
        stats = json.loads(rv.data.decode('utf8'))['data']
        yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
        yesterday_string = time_format.to_iso8601(yesterday)
        assert(stats[yesterday_string]['n_new_users'] == 0)
        # Now create change the creation date of a user so it was yesterday.
        userA.date_created = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        store.session.add(userA)
        store.session.commit()
        # Add force recalculation of statistics
        Statistic.update_statistics(yesterday, force=True)
        # We should get stats and see one new user yesterday.
        rv = self.app.get(
            '/api/statistics', headers=user_headers['userA'])
        assert(rv.status_code == 200)
        stats = json.loads(rv.data.decode('utf8'))['data']
        assert(stats[yesterday_string]['n_new_users'] == 1)
        assert(stats[yesterday_string]['n_users_started_conversation'] == 0)
        assert(stats[yesterday_string]['n_users_did_event'] == 0)
        # Now lets make a conversation and event
        searchA_id, searchB_id = self.create_searches(user_ids, user_headers)
        conversation_data = self.make_conversation(
            user_headers['userA'], search_id=searchA_id, title='Trip to moon.',
            userA_id=user_ids['userA'], userB_id=user_ids['userB'])
        conversation_id = conversation_data['id']
        share_data = self.make_share(
            user_headers['userA'], conversation_id,
            educator_user_id=user_ids['userA'],
            community_partner_user_id=user_ids['userB'],
            starting_in_hours=-20, force_past_events=True)
        share_id = share_data['id']
        eventA_id = share_data['events'][0]['id']
        # Pretend conversation was created yesterday.
        conversation = store.session.query(Conversation).filter(
            Conversation.id==conversation_id).first()
        conversation.date_created -= datetime.timedelta(hours=24)
        store.session.add(conversation)
        store.session.commit()
        # Stats should be appropriately changed.
        Statistic.update_statistics(yesterday, force=True)
        rv = self.app.get(
            '/api/statistics', headers=user_headers['userA'])
        assert(rv.status_code == 200)
        stats = json.loads(rv.data.decode('utf8'))['data']
        assert(stats[yesterday_string]['n_new_users'] == 1)
        assert(stats[yesterday_string]['n_users_started_conversation'] == 1)
        assert(stats[yesterday_string]['n_users_did_event'] == 2)
        # Make sure check_statistics doesn't break
        Statistic.check_statistics()
        rv = self.app.get(
            '/api/statistics', headers=user_headers['userA'])
        assert(rv.status_code == 200)
        stats = json.loads(rv.data.decode('utf8'))['data']
        assert(len(stats.keys()) == 30)

    def test_account_deletion(self):
        user_datas = {
            'userA': sample_userA,
            'userB': sample_userB,
        }
        user_ids, user_headers = self.create_users(user_datas)
        searchA_id, searchB_id = self.create_searches(user_ids, user_headers)
        conversation_data = self.make_conversation(
            user_headers['userA'], search_id=searchA_id, title='Trip to moon.',
            userA_id=user_ids['userA'], userB_id=user_ids['userB'])
        conversation_id = conversation_data['id']
        share_data = self.make_share(
            user_headers['userA'], conversation_id,
            educator_user_id=user_ids['userA'],
            community_partner_user_id=user_ids['userB'],
            starting_in_hours=0.5)
        mailer = mail.get_mailer()
        while mailer.queue:
            mailer.pop()
        # userB is deleting their account
        rv = self.app.delete(
            '/api/user/{0}'.format(user_ids['userB']), headers=user_headers['userB'])
        assert(rv.status_code == 200)
        # Emails should have been sent to userB (confirming deletion)
        # and UserA since they had an event scheduled.
        assert(len(mailer.queue) == 2)
        # userB should not longer be able to do things.
        data = {
            'searcher_user_id': user_ids['userB'],
            'searcher_role': 'educator',
            'searching_for_role': 'partner',
            'labels': 'Whatever',
            'zipcode': 12345
        }
        serialized = json.dumps(data)
        rv = self.app.post('/api/search', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 401)
        # And we shouldn't be able to login anymore
        headers = make_headers(email=sample_userB['email'], password=sample_userB['password'])
        rv = self.app.get('/api/requestapikey/', headers=headers)
        assert(rv.status_code == 401)

    def test_user_review(self):
        user_datas = {
            'userA': sample_userA,
            'userB': sample_userB,
            'userC': sample_userC,
        }
        user_ids, user_headers = self.create_users(user_datas)
        searchA_id, searchB_id = self.create_searches(user_ids, user_headers)
        conversation_data = self.make_conversation(
            user_headers['userA'], search_id=searchA_id, title='Trip to moon.',
            userA_id=user_ids['userA'], userB_id=user_ids['userB'])
        conversation_id = conversation_data['id']
        share_data = self.make_share(
            user_headers['userA'], conversation_id,
            educator_user_id=user_ids['userA'],
            community_partner_user_id=user_ids['userB'],
            starting_in_hours=0.5, force_past_events=False)
        # We shouldn't be able to save a review for the current event
        # because it is in the future
        share_id = share_data['id']
        eventA_id = share_data['events'][0]['id']
        review_data = {
            'event_id': eventA_id,
            'user_id': user_ids['userA'],
            'rating': 3,
        }
        serialized = json.dumps(review_data)
        rv = self.app.post('/api/user_review', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 403)
        # Two reminder emails should have been sent.
        # This check is mostly here since we need to flush the emails out
        # to test review reminder emails later.
        mailer = mail.get_mailer()
        while mailer.queue:
            mailer.pop()
        worker.work_loop(target_time_between_calls=datetime.timedelta(seconds=1),
                         max_loops=2)
        assert(len(mailer.queue) == 2)
        while mailer.queue:
            mailer.pop()
        # Let's make another conversation and share this time but put event in past.
        conversation_data = self.make_conversation(
            user_headers['userA'], search_id=searchA_id, title='Trip to moon.',
            userA_id=user_ids['userA'], userB_id=user_ids['userB'])
        conversation_id = conversation_data['id']
        share_data = self.make_share(
            user_headers['userA'], conversation_id,
            educator_user_id=user_ids['userA'],
            community_partner_user_id=user_ids['userB'],
            starting_in_hours=-26, force_past_events=True)
        eventA_id = share_data['events'][0]['id']
        # We should receive an email telling us to review it.
        events = EventReminder.get_review_reminder_events()
        assert(len(events) == 1)
        while mailer.queue:
            mailer.pop()
        worker.work_loop(target_time_between_calls=datetime.timedelta(seconds=1),
                         max_loops=2)
        events = EventReminder.get_review_reminder_events()
        assert(len(events) == 0)
        # Two reminder emails should have been sent.
        assert(len(mailer.queue) == 2)
        # Now try to make a review for the wrong user
        review_data = {
            'event_id': eventA_id,
            'user_id': user_ids['userC'],
            'rating': 3,
            'review': 'Was really super'
        }
        serialized = json.dumps(review_data)
        rv = self.app.post('/api/user_review', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 403)
        # Now try to make a review for oneself
        review_data = {
            'event_id': eventA_id,
            'user_id': user_ids['userB'],
            'rating': 3,
            'review': 'Was really super'
        }
        serialized = json.dumps(review_data)
        rv = self.app.post('/api/user_review', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 403)
        # Now try to make a review with invalid rating
        review_data = {
            'event_id': eventA_id,
            'user_id': user_ids['userA'],
            'rating': 6,
            'review': 'Was really super'
        }
        serialized = json.dumps(review_data)
        rv = self.app.post('/api/user_review', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 400)
        # Now try to make a review with invalid rating again
        review_data = {
            'event_id': eventA_id,
            'user_id': user_ids['userA'],
            'rating': -1,
            'review': 'Was really super'
        }
        serialized = json.dumps(review_data)
        rv = self.app.post('/api/user_review', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 400)
        # Make a valid review
        review_data = {
            'event_id': eventA_id,
            'user_id': user_ids['userA'],
            'rating': 3,
            'review': 'Was really super'
        }
        serialized = json.dumps(review_data)
        rv = self.app.post('/api/user_review', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 200)
        # We can't make a second review based off the same event
        review_data = {
            'event_id': eventA_id,
            'user_id': user_ids['userA'],
            'rating': 3,
            'review': 'Was really super'
        }
        serialized = json.dumps(review_data)
        rv = self.app.post('/api/user_review', data=serialized, headers=user_headers['userB'])
        assert(rv.status_code == 403)
        
        
    def test_reminders(self):
        user_datas = {
            'userA': sample_userA,
            'userB': sample_userB,
        }
        user_ids, user_headers = self.create_users(user_datas)
        searchA_id, searchB_id = self.create_searches(user_ids, user_headers)
        conversation_data = self.make_conversation(
            user_headers['userA'], search_id=searchA_id, title='Trip to moon.',
            userA_id=user_ids['userA'], userB_id=user_ids['userB'])
        conversation_id = conversation_data['id']
        share_data = self.make_share(
            user_headers['userA'], conversation_id,
            educator_user_id=user_ids['userA'],
            community_partner_user_id=user_ids['userB'],
            starting_in_hours=0.5)
        mailer = mail.get_mailer()
        while mailer.queue:
            mailer.pop()
        events = EventReminder.get_oneday_reminder_events()
        assert(len(events) == 1)
        worker.work_loop(target_time_between_calls=datetime.timedelta(seconds=1),
                         max_loops=2)
        events = EventReminder.get_oneday_reminder_events()
        assert(len(events) == 0)
        # Two reminder emails should have been sent.
        assert(len(mailer.queue) == 2)
        email1 = mailer.pop()
        email2 = mailer.pop()
        expected_email_addresses = set([sample_userA['email'], sample_userB['email']])
        rcvd_email_addresses = set([email1.to_address, email2.to_address])
        assert(expected_email_addresses == rcvd_email_addresses)

    def test_share(self):
        # Signup users and confirm emails
        user_datas = {
            'userA': sample_userA,
            'userB': sample_userB,
            'userC': sample_userC,
        }
        user_ids, user_headers = self.create_users(user_datas)
        user_headers['noone'] = make_headers()
        searchA_id, searchB_id = self.create_searches(user_ids, user_headers)
        conversation_data = self.make_conversation(
            user_headers['userA'], search_id=searchA_id, title='Trip to moon.',
            userA_id=user_ids['userA'], userB_id=user_ids['userB'])
        conversation_id = conversation_data['id']
        # userA creates a share
        share_data = self.make_share(
            user_headers['userA'], conversation_id,
            educator_user_id=user_ids['userA'],
            community_partner_user_id=user_ids['userB'])
        share_id = share_data['id']
        assert(len(share_data['events']) == 1)
        # This should send an email to userB that a share has been created.
        mailer = mail.get_mailer()
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.to_address == sample_userB['email'])
        # Check link is valid
        links = email.find_links()
        assert(len(links) == 1)
        chopped_link = chop_link(links[0])
        rv = self.app.get(chopped_link)
        assert(rv.status_code==200)
        # We should not be able to get this share if unauthenticated
        rv = self.app.get(
            '/api/share/{0}'.format(share_id), headers=user_headers['noone'])
        assert(rv.status_code == 401)
        # Logged on users can access share info
        # FIXME: Need to check if this should be more private.
        rv = self.app.get(
            '/api/share/{0}'.format(share_id), headers=user_headers['userC'])
        assert(rv.status_code == 200)
        # User B should be able to access it.
        rv = self.app.get(
            '/api/share/{0}'.format(share_id), headers=user_headers['userB'])
        assert(rv.status_code == 200)
        share_data = json.loads(rv.data.decode('utf8'))['data']
        assert(share_data['id'] == share_id)
        assert(share_data['educator_approved'] == True)
        assert(share_data['community_partner_approved'] == False)
        # Now let's edit the share.
        share_data = {
            'description': 'Is the moon made of Cheese?  There is only one way to find out!',
        }
        serialized = json.dumps(share_data)
        # Unauthenticated person should not be able to edit it.
        rv = self.app.put(
            '/api/share/{0}'.format(share_id), headers=user_headers['noone'], data=serialized)
        assert(rv.status_code == 401)
        # User C should not be able to edit it.
        rv = self.app.put(
            '/api/share/{0}'.format(share_id), headers=user_headers['userC'], data=serialized)
        assert(rv.status_code == 403)
        # User B should be able to edit it.
        rv = self.app.put(
            '/api/share/{0}'.format(share_id), headers=user_headers['userB'], data=serialized)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))['data']
        # There should still be one event there.
        assert(len(data['events']) == 1)
        event_id = data['events'][0]['id']
        # This should send an email to userA that a share has been edited.
        mailer = mail.get_mailer()
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.to_address == sample_userA['email'])
        # User B edits it and adds an additional event
        existing_event = data['events'][0]
        now = datetime.datetime.utcnow()
        starting = now + datetime.timedelta(hours=3)
        ending = now + datetime.timedelta(hours=4)
        data['events'].append(
            {'location': 'Somewhere Else',
             'datetime_start': time_format.to_iso8601(starting),
             'datetime_stop': time_format.to_iso8601(ending),}
        )
        serialized = json.dumps(data)
        rv = self.app.put(
            '/api/share/{0}'.format(share_id), headers=user_headers['userB'], data=serialized)
        data = json.loads(rv.data.decode('utf8'))['data']
        ids = set([e['id'] for e in data['events']])
        assert(event_id in ids)
        assert(len(ids) == 2)
        assert(rv.status_code == 200)
        # This should send an email to userA that a share has been edited.
        mailer = mail.get_mailer()
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.to_address == sample_userA['email'])
        # And who has given approval is switched.
        assert(data['educator_approved'] == False)
        assert(data['community_partner_approved'] == True)
        # User A can do a put with no changes to approve.
        serialized = json.dumps(data)
        rv = self.app.put(
            '/api/share/{0}'.format(share_id), headers=user_headers['userA'], data=serialized)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))['data']
        assert(data['educator_approved'] == True)
        assert(data['community_partner_approved'] == True)
        # This should send an email to userB that changes have been approved.
        mailer = mail.get_mailer()
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.to_address == sample_userB['email'])
        # Now userB deletes the events
        share_data = {
            'events': []
        }
        serialized = json.dumps(share_data)
        rv = self.app.put(
            '/api/share/{0}'.format(share_id), headers=user_headers['userB'], data=serialized)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))['data']
        assert(len(data['events']) == 0)
        # User A should have received an email
        mailer = mail.get_mailer()
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.to_address == sample_userA['email'])        
        # UserA cancels the share
        rv = self.app.delete(
            'api/share/{0}'.format(share_id), headers=user_headers['userA'])
        assert(rv.status_code == 200)
        # User B should have received an email.
        mailer = mail.get_mailer()
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.to_address == sample_userB['email'])        

    def test_password_reset(self):
        # Signup userA
        userA_id, userA_api_key, userA_email_key = self.sign_up(sample_userA)
        self.confirm_email(userA_email_key)
        rv = self.app.get('/api/requestresetpassword/{0}'.format(
            sample_userA['email']))
        assert(rv.status_code == 200)
        mailer = mail.get_mailer()
        # Check that we can authenticate with email and password
        headers = make_headers(email=sample_userA['email'], password=sample_userA['password'])
        rv = self.app.get('/api/requestapikey/', headers=headers)
        assert(rv.status_code == 200)
        # We should have one email in queue (email from password reset request)
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        links = email.find_links()
        assert(len(links)==1)
        email_key = re.search('key=(.*)', links[0]).groups()[0]
        logger.debug('email key is {0}'.format(email_key))
        # Now try to reset password
        new_password = 'mynewpassword'
        headers = make_headers()
        rv = self.app.post(
            '/api/resetpassword',
            data=json.dumps({'key': email_key, 'password': new_password}),
            headers=headers)
        assert(rv.status_code==200)
        # Check that we can't authenticate with email and old password
        headers = make_headers(email=sample_userA['email'], password=sample_userA['password'])
        rv = self.app.get('/api/requestapikey/', headers=headers)
        assert(rv.status_code == 401)
        # Check that we can authenticate with email and new password
        headers = make_headers(email=sample_userA['email'], password=new_password)
        rv = self.app.get('/api/requestapikey/', headers=headers)
        assert(rv.status_code == 200)

    def test_two(self):
        # Now sign up 2 new users but don't confirm their email addresses
        userA_id, userA_api_key, userA_email_key = self.sign_up(sample_userA)
        userB_id, userB_api_key, userB_email_key = self.sign_up(sample_userB)
        # Create Searches
        userA_headers = make_headers(api_key=userA_api_key)
        userB_headers = make_headers(api_key=userB_api_key)
        user_headers = {
            'userA': userA_headers,
            'userB': userB_headers,
        }
        user_ids = {
            'userA': userA_id,
            'userB': userB_id
        }
        searchA_id, searchB_id = self.create_searches(user_ids, user_headers)
        # Get all the results for userA's search
        rv = self.app.get('/api/search/{0}/results'.format(searchA_id),
                          headers=user_headers['userA'])
        data = json.loads(rv.data.decode('utf8'))
        searches = data['data']
        assert(len(searches) == 0)
        # Now userB will confirm their email.
        self.confirm_email(userB_email_key)
        # So that they should appear in userA's search.
        rv = self.app.get('/api/search/{0}/results'.format(searchA_id),
                          headers=user_headers['userA'])
        data = json.loads(rv.data.decode('utf8'))
        searches = data['data']
        assert(len(searches) == 1)
        # But userA shouldn't be able to start a conversation until they have
        # confirmed their email
        conversation_data = {
            'search_id': searchA_id,
            'title': 'Trip to moon',
            'userA_id': userA_id,
            'userB_id': userB_id,
        }
        serialized = json.dumps(conversation_data)
        rv = self.app.post(
            '/api/conversation', headers=user_headers['userA'], data=serialized)
        assert(rv.status_code == 400)
        # Now userA will confirm their email.
        self.confirm_email(userA_email_key)
        # And try to save the conversation again.
        rv = self.app.post(
            '/api/conversation', headers=user_headers['userA'], data=serialized)
        assert(rv.status_code == 200)

    def test_one(self):
        # Make sure we get an OK when requesting index.
        rv = self.app.get('/')
        assert(rv.status_code == 200)
        # Now try to get user from API
        # Expect forbidden (401)
        rv = self.app.get('/api/user/1')
        assert(rv.status_code == 401)
        # Now sign up UserA
        userA_id, userA_api_key, userA_email_key = self.sign_up(sample_userA)
        # Get userA and check that email is not confirmed
        userA_headers = make_headers(userA_api_key)
        rv = self.app.get('/api/user/1', headers=userA_headers)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))['data']
        assert(data['email_confirmed'] == False)
        # Confirm email
        self.confirm_email(userA_email_key)
        # Get userA and check that email is confirmed
        rv = self.app.get('/api/user/1', headers=userA_headers)
        assert(rv.status_code == 200)
        data = json.loads(rv.data.decode('utf8'))['data']
        assert(data['email_confirmed'] == True)
        # Sign up UserB
        userB_id, userB_api_key, userB_email_key = self.sign_up(sample_userB)
        self.confirm_email(userB_email_key)
        # Create Searches
        userB_headers = make_headers(api_key=userB_api_key)
        user_headers = {
            'userA': userA_headers,
            'userB': userB_headers,
        }
        user_ids = {
            'userA': userA_id,
            'userB': userB_id
        }        
        searchA_id, searchB_id = self.create_searches(user_ids, user_headers)
        # Get all the results for userA's search
        rv = self.app.get('/api/search/{0}/results'.format(searchA_id),
                          headers=user_headers['userA'])
        data = json.loads(rv.data.decode('utf8'))
        searches = data['data']
        assert(len(searches) == 1)
        assert(searches[0]['searcher_user_id'] == userB_id)
        # Now userA starts a conversation with userB
        conversation_title = 'Trip to moon.'
        conversation_data = self.make_conversation(
            user_headers['userA'], search_id=searchA_id, title=conversation_title,
            userA_id=user_ids['userA'], userB_id=user_ids['userB'])
        conversation_id = conversation_data['id']
        # And send the first message
        message_content = 'Are you interested in going to the moon?'
        rv = self.send_message(
            conversation_id=conversation_id,
            sender_user_id=userA_id,
            content=message_content,
            api_key=userA_api_key)
        data = json.loads(rv.data.decode('utf8'))
        message_id = data['data']['id']
        mailer = mail.get_mailer()
        # We should have one email in queue (email about new message)
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.subject == conversation_title)
        assert(email.content.startswith(message_content))
        assert(email.to_address == sample_userB['email'])
        new_reply_content = 'Sure, sounds great!'
        reply_email = email.make_reply(new_reply_content)
        assert(reply_email.subject == conversation_title)
        assert(reply_email.content.startswith(new_reply_content))
        assert(reply_email.from_address == email.to_address)
        assert(reply_email.to_address == email.from_address)
        # That email should contain a link to the conversation
        # We're not running the javascript so we can't test it properly.
        links = email.find_links()
        assert(len(links) == 1)
        chopped_link = chop_link(links[0])
        rv = self.app.get(chopped_link)
        assert(rv.status_code==200)
        # Send the reply email to our email API in the form of a Mailgun
        # request.
        rv = self.app.post(
            '/api/email', data=reply_email.make_mailgun_data())
        assert(rv.status_code==200)
        # It should have been forwarded to the other user.
        assert(len(mailer.queue) == 1)
        email = mailer.pop()
        assert(email.subject == conversation_title)
        assert(email.content.startswith(new_reply_content))
        assert(email.to_address == sample_userA['email'])
        # And we should now have two messages in the conversation
        # We'll hit the conversation API to confirm this.
        rv = self.app.get(
            '/api/conversation/{0}'.format(conversation_id),
            headers=user_headers['userA'])
        rcvd_conversation_data = json.loads(rv.data.decode('utf8'))['data']
        assert(rcvd_conversation_data['id'] == conversation_id)
        assert(rcvd_conversation_data['title'] == conversation_title)
        messages_data = rcvd_conversation_data['messages']
        assert(len(messages_data) == 2)
        assert(messages_data[0]['content'] == message_content)
        assert(messages_data[0]['sender_user_id'] == userA_id)
        assert(messages_data[1]['content'] == new_reply_content)
        assert(messages_data[1]['sender_user_id'] == userB_id)

        # To do:
        # Make sure that conversation link works in email
        
    def tearDown(self):
        #os.rmdir(self.SQLLITE_FILE)
        pass

if __name__ == '__main__':
    unittest.main()
    
        
