import logging

from community_share import setup, config, store
from community_share.models.user import UserReview
from community_share.setup_data import get_questions

logger = logging.getLogger(__name__)

def main():
    logger.info('Loading settings from environment')    
    config.load_from_environment()
    logger.info('Getting the creating admin')
    creator = setup.get_creator()
    logger.info('Updating the questions')
    setup.update_questions(get_questions(creator))
    store.session.commit()

if __name__ == '__main__':
    main()
