import logging
from datetime import datetime

from sqlalchemy import Table, ForeignKey, DateTime, Column
from sqlalchemy import Integer, String, Boolean, Float
from sqlalchemy.orm import relationship

from community_share import Base, store
from community_share.models.base import Serializable

logger = logging.getLogger(__name__)

search_label_table = Table('search_label', Base.metadata,
    Column('search_id', Integer, ForeignKey('search.id')),
    Column('label_id', Integer, ForeignKey('label.id'))
)

class Search(Base, Serializable):
    __tablename__ = 'search'
    
    MANDATORY_FIELDS = [
        'searcher_user_id', 'searcher_role', 'searching_for_role', 'labels', 'zipcode']
    WRITEABLE_FIELDS = [
        'searcher_user_id', 'searcher_role', 'searching_for_role', 'labels',
        'active', 'latitude', 'longitude', 'address', 'distance', 'zipcode']
    STANDARD_READABLE_FIELDS = [
        'id', 'searcher_user_id', 'searcher_role', 'searching_for_role',
        'labels', 'longitude', 'latitude', 'address', 'zipcode', 'distance',
        'searcher_user',]
    ADMIN_READABLE_FIELDS = [
        'id', 'searcher_user_id', 'searcher_role', 'searching_for_role', 'labels',
        'created', 'active', 'longitude', 'latitude', 'address', 'zipcode', 'distance',
        'searcher_user',]

    PERMISSIONS = {
        'all_can_read_many': False,
        'standard_can_read_many': True,
        'admin_can_delete': True
    }

    COMMUNITY_PARTNER_ROLE = 'partner'
    EDUCATOR_ROLE = 'educator'

    id = Column(Integer, primary_key=True)
    searcher_user_id = Column(Integer, ForeignKey('user.id'))
    searcher_role = Column(String(20), nullable=False)
    searching_for_role = Column(String(20), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    active = Column(Boolean, nullable=False, default=True)
    address = Column(String(200))
    zipcode = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    distance = Column(Float, nullable=True)

    labels = relationship('Label', secondary=search_label_table)

    @classmethod
    def has_add_rights(cls, data, user):
        has_rights = False
        if user is not None:
            if int(data.get('searcher_user_id', -1)) == user.id:
                has_rights = True
        return has_rights

    def has_standard_rights(self, requester):
        has_rights = False
        if requester is not None:
            has_rights = True
        return has_rights

    def has_admin_rights(self, user):
        has_rights = False
        if user.is_administrator:
            has_rights = True
        elif user.id == self.searcher_user_id:
            has_rights = True
        return has_rights

    def serialize_labels(self, requester):
        return [l.name for l in self.labels]
    def serialize_searcher_user(self, requester):
        return self.searcher_user.serialize(requester)

    custom_serializers = {
        'labels': serialize_labels,
        'searcher_user': serialize_searcher_user,
    }

    def deserialize_labels(self, labelnames):
        if labelnames is None:
            labelnames = []
        logger.debug('labelnames is {0}'.format(labelnames))
        self.labels = Label.name_list_to_object_list(labelnames)

    custom_deserializers = {
        'labels': deserialize_labels,
        }
        

class Label(Base, Serializable):
    __tablename__ = 'label'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    active = Column(Boolean, default=True)
    description = Column(String)

    @classmethod
    def name_list_to_object_list(cls, names):
        labels = store.session.query(Label).filter(Label.name.in_(names)).all()
        missing_labelnames = set(names)
        for label in labels:
            missing_labelnames.remove(label.name)
        for labelname in missing_labelnames:
            new_label = Label(name=labelname)
            labels.append(new_label)
        return labels
