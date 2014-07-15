from community_share.models.share import Share, Event
from community_share.routes import base_routes

def register_share_routes(app):

    share_blueprint = base_routes.make_blueprint(Share, 'share')
    event_blueprint = base_routes.make_blueprint(Event, 'event')
    app.register_blueprint(share_blueprint)
    app.register_blueprint(event_blueprint)

