from flask import jsonify

from community_share.models.survey import Question, Answer
from community_share.routes import base_routes

def register_survey_routes(app):

    conversation_blueprint = base_routes.make_blueprint(Question, 'question')
    app.register_blueprint(conversation_blueprint)

    answer_blueprint = base_routes.make_blueprint(Answer, 'answer')
    app.register_blueprint(answer_blueprint)
