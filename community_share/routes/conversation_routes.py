from community_share.models.conversation import Conversation, Message
from community_share.routes import base_routes

def register_conversation_routes(app):

    conversation_blueprint = base_routes.make_blueprint(Conversation, 'conversation')
    app.register_blueprint(conversation_blueprint)

    message_blueprint = base_routes.make_blueprint(Message, 'message')
    app.register_blueprint(message_blueprint)

