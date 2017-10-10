import hashlib
import uuid
from unittest import mock

import aiohttp_csrf


def test_key_generation():
    secret_phrase = 'This is secret phrase for tests'

    token_generator = aiohttp_csrf.token_generator.HashedTokenGenerator(
        secret_phrase=secret_phrase,
    )

    u = uuid.uuid4()

    unhashed_token = u.hex + secret_phrase

    hasher = hashlib.sha256(unhashed_token.encode(token_generator.encoding))

    with mock.patch('uuid.uuid4', return_value=u):
        token = token_generator.generate()

        assert hasher.hexdigest() == token
