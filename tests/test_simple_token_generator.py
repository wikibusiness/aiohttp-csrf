import uuid
from unittest import mock

import aiohttp_csrf


def test_key_generation():
    token_generator = aiohttp_csrf.token_generator.SimpleTokenGenerator()

    u = uuid.uuid4()

    with mock.patch('uuid.uuid4', return_value=u):
        token = token_generator.generate()

        assert u.hex == token
