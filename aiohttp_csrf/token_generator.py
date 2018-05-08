import abc
import hashlib
import uuid


class AbstractTokenGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate(self):
        pass  # pragma: no cover


class SimpleTokenGenerator(AbstractTokenGenerator):
    def generate(self):
        return uuid.uuid4().hex


class HashedTokenGenerator(AbstractTokenGenerator):
    encoding = 'utf-8'

    def __init__(self, secret_phrase):
        self.secret_phrase = secret_phrase

    def generate(self):
        token = uuid.uuid4().hex

        token += self.secret_phrase

        hasher = hashlib.sha256(token.encode(self.encoding))

        return hasher.hexdigest()
