from datetime import datetime
import logging
import json

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from community_share import Base
from community_share.models.base import Serializable


logger = logging.getLogger(__name__)

class Question(Base, Serializable):
    __tablename__ = 'question'

    MANDATORY_FIELDS = ['text', 'question_type', 'public']
    WRITEABLE_FIELDS = ['public', 'order', 'only_suggested_answers', 'suggested_answers', 'long_answer']
    STANDARD_READABLE_FIELDS = [
        'id', 'text', 'question_type', 'public', 'only_suggested_answers', 'order',
        'suggested_answers', 'long_answer']
    ADMIN_READABLE_FIELDS = [
        'id', 'text', 'creator', 'date_created', 'question_type', 'public',
        'only_suggested_answers', 'order', 'suggested_answers', 'long_answer']
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    long_answer = Column(Boolean, nullable=False, default=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    question_type = Column(String(50), nullable=False)
    public = Column(Boolean, nullable=False)
    only_suggested_answers = Column(Boolean, nullable=False, default=False)
    requires_share_id = Column(Boolean, nullable=False, default=False)
    requires_event_id = Column(Boolean, nullable=False, default=False)
    requires_user_id = Column(Boolean, nullable=False, default=False)
    order = Column(Integer)

    creator = relationship('User')
    suggested_answers = relationship('SuggestedAnswer')

    PERMISSIONS = {
        'all_can_read_many': True,
        'standard_can_read_many': True
    }

    def __init__(self, *args, **kwargs):
        self.long_answer = False
        self.active = True
        self.only_suggested_answers = False
        self.requires_share_id = False
        self.requires_event_id = False
        self.requires_user_id = False
        Base.__init__(self, *args, **kwargs)

    def has_standard_rights(self, requester):
        return True
    
    def serialize_suggested_answers(self, requester=None):
        serialized = [sa.text for sa in self.suggested_answers if sa.active]
        return serialized

    def make_hash(self):
        hash_data = [self.text, self.question_type, self.only_suggested_answers,
                     self.long_answer, self.serialize_suggested_answers()]
        return json.dumps(hash_data)
        
    @classmethod
    def args_to_query(cls, args, requester=None):
        query = cls._args_to_query(args, requester)
        query = query.order_by(cls.order)
        return query

    def serialize_creator(self, requester):
        return self.creator.serialize(requester)

    custom_serializers = {
        'suggested_answers': serialize_suggested_answers,
        'creator': serialize_creator,
    }


class SuggestedAnswer(Base, Serializable):
    __tablename__ = 'suggested_answer'

    def __init__(self, *args, **kwargs):
        self.active = True
        Base.__init__(self, *args, **kwargs)

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    text = Column(String)
    active = Column(Boolean, nullable=False, default=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)

    creator = relationship('User')
    question = relationship('Question')


class Answer(Base, Serializable):
    __tablename__ = 'answer'

    MANDATORY_FIELDS = ['question_id', 'responder_id', 'text']
    WRITEABLE_ONCE_FIELDS = ['about_event_id', 'about_user_id', 'about_share_id']
    WRITEABLE_FIELDS = ['text']
    STANDARD_READABLE_FIELDS = [
        'id', 'question_id', 'responder_id', 'text', 'date_created',
        'about_user_id', 'about_share_id', 'about_event_id']
    ADMIN_READABLE_FIELDS = [
        'id', 'question_id', 'responder_id', 'text', 'date_created',
        'about_user_id', 'about_share_id', 'about_event_id']

    PERMISSIONS = {
        'all_can_read_many': True,
        'standard_can_read_many': True
    }

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    responder_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    text = Column(String)
    active = Column(Boolean, default=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    about_user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    about_share_id = Column(Integer, ForeignKey('share.id'), nullable=True)
    about_event_id = Column(Integer, ForeignKey('event.id'), nullable=True)

    question = relationship('Question')

    @classmethod
    def has_add_rights(cls, data, requester):
        data['responder_id'] = int(data.get('responder_id', requester.id))
        if (requester is not None and requester.is_administrator):
            has_rights = True
        elif data['responder_id'] == requester.id:
            has_rights = True
        else:
            has_rights = False
        return has_rights
            
    def has_standard_rights(self, requester):
        has_rights = False
        if requester is not None:
            if requester.is_administrator:
                has_rights = True
            elif self.question.public:
                has_rights = True
            elif self.responder_id == requester.id:
                has_rights = True
        return has_rights

    def has_admin_rights(self, requester):
        has_rights = False
        if requester is not None:
            if requester.is_administrator:
                has_rights = True
            elif self.responder_id == requester.id:
                has_rights = True
        return has_rights
