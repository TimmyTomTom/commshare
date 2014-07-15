'''
Updates the questions.

'''
import os
import logging

from community_share.models.secret import Secret
from community_share import setup, config, store

from questions import get_questions

logger = logging.getLogger(__name__)

def main():
    logger.info('Loading settings from environment')    
    config.load_from_environment()
    creator = setup.get_creator()
    setup.update_questions(get_questions(creator))
    store.session.commit()

if __name__ == '__main__':
    main()
