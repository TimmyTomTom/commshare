import logging
import os

from flask import Flask, send_from_directory, render_template

from community_share import config, store
from community_share.routes.user_routes import register_user_routes
from community_share.routes.search_routes import register_search_routes
from community_share.routes.conversation_routes import register_conversation_routes
from community_share.routes.share_routes import register_share_routes
from community_share.routes.survey_routes import register_survey_routes
from community_share.routes.email_routes import register_email_routes
from community_share.routes.statistics_routes import register_statistics_routes

logger = logging.getLogger(__name__)

def make_app():
    logger.debug('COMMIT_HASH is {0}'.format(config.COMMIT_HASH))
    app = Flask(__name__, template_folder='../static/')
    app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_CONNECTION

    register_user_routes(app)
    register_search_routes(app)
    register_conversation_routes(app)
    register_share_routes(app)
    register_survey_routes(app)
    register_email_routes(app)
    register_statistics_routes(app)

    @app.teardown_appcontext
    def close_db_connection(exception):
        store.session.remove()

    @app.route('/static/js/<path:filename>')
    def js_static(filename):
        return send_from_directory(app.root_path + '/../static/js/', filename)

    @app.route('/static/fonts/<path:filename>')
    def fonts_static(filename):
        return send_from_directory(app.root_path + '/../static/fonts/', filename)

    @app.route('/static/css/<path:filename>')
    def css_static(filename):
        return send_from_directory(app.root_path + '/../static/css/', filename)

    @app.route('/static/templates/<path:filename>')
    def templates_static(filename):
        return send_from_directory(app.root_path + '/../static/templates/', filename)

    @app.route('/')
    def index():
        logger.debug('rendering index')
        return render_template('index.html', COMMIT_HASH=config.COMMIT_HASH,
                               config=config
        )
        
    return app

if __name__ == '__main__':
    logger.info('Loading settings from environment')
    config.load_from_environment()
    logger.info('Making application')
    app = make_app()
    app.debug = True
    logger.info('Running application - debug={0}'.format(app.debug))
    app.run()
