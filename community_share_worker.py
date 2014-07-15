import logging

from community_share import worker, config

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('Loading settings from environment')
    config.load_from_environment()
    worker.work_loop()
