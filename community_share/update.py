from community_share.models.search import Label, Search
from community_share.models.user import User, UserReview
from community_share.models.institution import Institution, InstitutionAssociation
from community_share.models.conversation import Conversation, Message
from community_share.models.secret import Secret
from community_share.models.share import Share, Event
from community_share import store, config, Base, setup, setup_data
from community_share.models.statistics import Statistic

if __name__ == '__main__':
    #Event.__table__.drop(engine)
    #Share.__table__.drop(engine)
    config.load_from_environment()
    Base.metadata.create_all(store.engine)
    creator = setup.get_creator()
    questions = setup_data.get_questions(creator)
    setup.update_questions(questions)
    store.session.commit()
