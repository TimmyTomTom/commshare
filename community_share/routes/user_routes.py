import logging
import os

import tinys3
from flask import request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from community_share.models.user import User, UserReview
from community_share.models.institution import Institution
from community_share.authorization import get_requesting_user
from community_share import mail_actions
from community_share.routes import base_routes
from community_share import config, store

logger = logging.getLogger(__name__)

def register_user_routes(app):

    user_blueprint = base_routes.make_blueprint(User, 'user')
    app.register_blueprint(user_blueprint)

    user_review_blueprint = base_routes.make_blueprint(UserReview, 'user_review')
    app.register_blueprint(user_review_blueprint)

    institution_blueprint = base_routes.make_blueprint(Institution, 'institution')
    app.register_blueprint(institution_blueprint)

    @app.route('/api/usersignup', methods=['POST'])
    def usersignup():
        data = request.json
        user = data.get('user', None)
        email = user.get('email', '')
        password = data.get('password', None)
        # Check that the email isn't in use.
        existing_user = store.session.query(User).filter(
            User.email==email, User.active==True).first()
        if existing_user is not None:
            response = base_routes.make_bad_request_response(
                'That email address is already associated with an account.')
        elif password is None:
            response = base_routes.make_bad_request_response(
                'A password was not specified.');
        else:
            user = User.admin_deserialize_add(user)
            error_messages = user.set_password(password)
            if error_messages:
                error_message = ', '.join(error_messages)
                response = base_routes.make_bad_request_response(error_message)
            else:
                store.session.add(user)
                store.session.commit()
                error_message = mail_actions.request_signup_email_confirmation(user)
                secret = user.make_api_key()
                serialized = user.serialize(user)
                response_data = {
                    'data': serialized,
                    'apiKey': secret.key,
                    'warningMessage': 'Failed to send email confirmation: {0}'.format(error_message)
                }
                response = jsonify(response_data)
        return response

    @app.route('/api/userbyemail/<string:email>', methods=['GET'])
    def userbyemail(email):
        requester = get_requesting_user()
        if requester is None:
            response = base_routes.make_not_authorized_response()
        elif requester.email != email:
            response = base_routes.make_forbidden_response()
        else:
            users = store.session.query(User).filter(
                User.email==email, User.active==True).all()
            if len(users) > 1:
                logger.error('More than one active user with the same email - {}'.format(email))
                user = users[0]
            elif len(users) == 0:
                user = None
            else:
                user = users[0]
            if user is None:
                response = base_routes.make_not_found_response()
            else:
                response = base_routes.make_single_response(requester, user)
        return response

    @app.route('/api/requestresetpassword/<string:email>', methods=['GET'])
    def request_reset_password(email):
        user = store.session.query(User).filter_by(email=email).first()
        if user is None:
            response = base_routes.make_not_found_response()
        else:
            error_message = mail_actions.request_password_reset(user)
            if error_message:
                response = base_routes.make_server_error_response(error_message)
            else:
                response = base_routes.make_OK_response()
        return response

    @app.route('/api/requestapikey/', methods=['GET'])
    def request_api_key():
        requester = get_requesting_user()
        if requester is None:
            response = base_routes.make_not_authorized_response()
        else:
            secret = requester.make_api_key()
            response_data = {
                'apiKey': secret.key
            }
            response = jsonify(response_data)
        return response

    @app.route('/api/resetpassword', methods=['POST'])
    def reset_password():
        data = request.json
        key = data.get('key', '')
        password = data.get('password', '')
        if key == '':
            response = base_routes.make_bad_request_response(
                'Did not receive a key with password reset request.')
        elif password == '':
            response = base_routes.make_bad_request_response(
                'Received password to reset to was blank.')
        else:
            user, error_messages = mail_actions.process_password_reset(key, password)
            if error_messages:
                error_message = ', '.join(error_messages)
                response = base_routes.make_bad_request_response(error_message)
            elif user is None:
                response = base_routes.make_bad_request_response()
            else:
                response = base_routes.make_single_response(user, user)
        return response

    @app.route('/api/requestconfirmemail', methods=['GET'])
    def request_confirm_email():
        requester = get_requesting_user()
        if requester is None:
            response = base_routes.make_not_authorized_response()
        else:
            error_message = mail_actions.request_signup_email_confirmation(requester)
            if error_message:
                response = base_routes.make_server_error_response(error_message)
            else:
                response = base_routes.make_OK_response()
        return response

    @app.route('/api/confirmemail', methods=['POST'])
    def confirm_email():
        data = request.json
        key = data.get('key', '')
        if key == '':
            response = base_routes.make_bad_request_response(
                'Did not receive a key with email confirmation.')
        else:
            user, error_messages = mail_actions.process_confirm_email(key)
            if error_messages:
                error_message = ', '.join(error_messages)
                response = base_routes.make_bad_request_response(error_message)
            elif user is None:
                response = base_routes.make_bad_request_response()
            else:
                secret = user.make_api_key()
                serialized = user.serialize(user)
                response_data = {
                    'data': serialized,
                    'apiKey': secret.key,
                }
                response = jsonify(response_data)
        return response
        
        

    ALLOWED_EXTENSIONS = set(['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif'])

    def process_filename(filename, user_id):
        base, extension = os.path.splitext(filename)
        if extension in ALLOWED_EXTENSIONS:
            # Maximum filename length = 100
            # Use 50 to be safe
            base = base[:50]
            processed = 'user_{0}_{1}{2}'.format(user_id, base, extension)
        else:
            processed = None
        return processed

    @app.route('/api/user/<int:user_id>/picture', methods=['PUT', 'POST', 'PATCH'])
    def post_picture(user_id):
        requester = get_requesting_user()
        if (user_id == requester.id):
            user = requester
            f = request.files['file']
            if f:
                filename = process_filename(f.filename, user_id)
                if filename is None:
                    response = base_routes.make_bad_request_response()
                else:
                    conn = tinys3.Connection(
                        config.S3_USERNAME, config.S3_KEY, tls=True)
                    # Upload it.  Set cache expiry time to 1 hr.
                    conn.upload(filename, f, config.S3_BUCKETNAME,
                                expires=3600)
                    user.picture_filename = filename
                    store.session.add(user)
                    store.session.commit()
                    response = base_routes.make_OK_response()
            else:
                response = base_routes.make_bad_request_response()
        else:
            response = base.routes.make_forbidden_response()
        return response
