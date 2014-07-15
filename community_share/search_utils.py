from sqlalchemy.sql.expression import func

from community_share.models.search import Search, Label
from community_share.models.user import User
from community_share import store

def get_searches_ordered_by_label_matches(
        labels, searcher_role, searching_for_role, max_number=10):
    labelnames = [label.name.lower() for label in labels]
    query = store.session.query(Search, func.count(Label.id).label('matches'))
    query = query.join(Search.labels)
    query = query.filter(func.lower(Label.name).in_(labelnames))
    query = query.filter(Search.active==True)
    query = query.filter(Search.searcher_role==searcher_role)
    query = query.filter(Search.searching_for_role==searching_for_role)
    query = query.join(Search.searcher_user)
    query = query.filter(User.email_confirmed==True)
    query = query.group_by(Search.id)
    query = query.order_by('matches DESC')
    searches_and_count = query.limit(max_number)
    searches = [sc[0] for sc in searches_and_count]
    return searches

def find_matching_searches(search):
    searches = get_searches_ordered_by_label_matches(
        search.labels, searcher_role=search.searching_for_role,
        searching_for_role=search.searcher_role)
    return searches
    


