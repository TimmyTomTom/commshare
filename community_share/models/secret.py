from datetime import datetime, timedelta
import string, random, json

from sqlalchemy import Column, String, DateTime, Boolean

from community_share import store, Base

class Secret(Base):
    __tablename__ = 'secret'
    KEY_LENGTH = 200
    
    key = Column(String(KEY_LENGTH), primary_key=True)
    info = Column(String)
    expiration = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)

    @classmethod
    def make_key(cls, key_length=KEY_LENGTH):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        key = ''.join(random.choice(chars) for _ in range(cls.KEY_LENGTH))
        return key

    @classmethod
    def make(cls, info, hours_duration):
        info_as_json = json.dumps(info)
        key = cls.make_key()
        expiration = datetime.now() + timedelta(hours=hours_duration)
        secret = Secret(key=key, info=info_as_json, expiration=expiration)
        return secret

    def get_info(self):
        info = None
        try:
            info = json.loads(self.info)
        except ValueError:
            logger.error("Invalid JSON data in secret.info")
        return info

    @classmethod
    def create_secret(cls, info, hours_duration):
        secret = Secret.make(info, hours_duration)
        store.session.add(secret)
        store.session.commit()
        return secret

    @classmethod
    def lookup_secret(cls, key):
        current_time = datetime.utcnow()
        secret = store.session.query(Secret).filter_by(key=key, used=False).filter(
            Secret.expiration>current_time).first()
        return secret
