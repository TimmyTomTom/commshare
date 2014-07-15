import re
import logging
import hmac, hashlib

import requests

from community_share import config

logger = logging.getLogger(__name__)

dummy_template = '''
----------------------------
SENDING AN EMAIL
----------------------------
from: {email.from_address}
to: {email.to_address}
subject: {email.subject}
content: {email.content}
'''

def verify_email(api_key, token, timestamp, signature):
    return signature == hmac.new(
        key=bytearray(api_key, 'utf8'),
        msg=bytearray('{}{}'.format(timestamp, token), 'utf8'),
        digestmod=hashlib.sha256).hexdigest()


class Email(object):

    def __init__(self, from_address, to_address, subject, content, new_content):
        self.from_address = from_address
        self.to_address = to_address
        self.subject = subject
        self.new_content = new_content
        self.content = content

    def make_reply(self, new_content):
        new_from_address = self.to_address
        new_to_address = self.from_address
        new_lines = [new_content, '']
        lines = self.content.splitlines()
        new_lines += ['>' + line for line in lines]
        combined_content = '\n'.join(new_lines)
        new_email = Email(new_from_address, new_to_address, self.subject,
                          combined_content, new_content)
        return new_email
        
    def make_mailgun_data(self):
        data = {
            'recipient': self.to_address,
            'stripped-text': self.new_content,
            'body-plain': self.content,
            'sender': self.from_address,
            'subject': self.subject,
        }
        return data

    @classmethod
    def from_mailgun_data(cls, data, verify=True):
        recipient = data.get('recipient', None)
        body_plain = data.get('body-plain', None)
        stripped_text = data.get('stripped-text', None)
        sender = data.get('sender', None)
        subject = data.get('subject', None)
        headers = data.get('message-headers', [])
        signature = data.get('signature', None)
        token = data.get('token', None)
        timestamp = data.get('timestamp', None)
        if verify:
            verified = verify_email(config.MAILGUN_API_KEY, token, timestamp, signature)
        else:
            verified = True
        if verified:
            email = Email(sender, recipient, subject, body_plain, stripped_text)
        else:
            email = None
        return email

    def find_links(self):
        links = []
        pattern = '\s+({}.*)\s*'.format(config.BASEURL)
        match = re.search(pattern, self.content)
        if match:
            links = match.groups()
        return links

class QueueMailer(object):
    def __init__(self):
        self.queue = []
    def send(self, email):
        self.queue.append(email)
    def pop(self):
        return self.queue.pop(0)

class DummyMailer(object):
    def send(email):
        text = dummy_template.format(email=email)
        logger.info(text)

class MailgunMailer(object):
    def send(email):
        error_message = ''
        if not ('notarealemail' in email.to_address):
            payload = {
                'from': email.from_address,
                'to': email.to_address,
                'subject': email.subject,
                'text': email.content
            }
            logger.info('Sending mail request to mailgun - {}'.format(payload))
            r = requests.post(
                'https://api.mailgun.net/v2/{0}/messages'.format(
                    config.MAILGUN_DOMAIN),
                auth=('api', config.MAILGUN_API_KEY),
                data=payload)
            if not r.ok:
                logger.error('Mailgun API failed with message: {0}'.format(
                    r.json()['message']))
                error_message = 'Server failed to connect to email service.'
            text = dummy_template.format(email=email)
            logger.debug(text)
        else:
            text = dummy_template.format(email=email)
            logger.info(text)
        return error_message

mailer_type_to_mail = {
    'DUMMY': DummyMailer,
    'MAILGUN': MailgunMailer,
    'QUEUE': QueueMailer(),
}

def get_mailer():
    mailer = mailer_type_to_mail[config.MAILER_TYPE]
    return mailer
