import os
import logging

from community_share.models.secret import Secret
from community_share import setup, config, store

logger = logging.getLogger(__name__)


def main():
    logger.info('Loading settings from environment')    
    config.load_from_environment()
    logger.info('Starting setup script produced on 2014 June 14th.')
    setup.init_db()
    first_admin = None
    logger.info('Making labels.')
    setup.make_labels()
    admin_emails = os.environ.get('COMMUNITYSHARE_ADMIN_EMAILS', '').split(',')
    admin_emails = [x.strip() for x in admin_emails]
    logger.info('admin_emails is {0}'.format(admin_emails))
    logger.info('Making Admin Users')
    for email in admin_emails:
        if email:
            user = setup.make_admin_user(email, email, Secret.make_key(20))
            if user is not None and first_admin is None:
                first_admin = user
    logger.info('Making questions')
    setup.make_questions(first_admin)
    store.session.commit()

if __name__ == '__main__':
    main()
