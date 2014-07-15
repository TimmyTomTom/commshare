from sqlalchemy.schema import CreateTable

from community_share import store, config, setup
from community_share.models.user import UserReview


config.load_from_environment()
table_sql = CreateTable(UserReview.__table__).compile(store.engine)
print(table_sql)
