from unittest.mock import MagicMock

import aiohttp_csrf
import pytest
from aiohttp.test_utils import make_mocked_request


class FakeStorage(aiohttp_csrf.storage.BaseStorage):

    async def _get(self, request):
        return request.get('my_field')

    async def _save_token(self, request, response, token):
        request['my_field'] = token


async def test_1():
    storage = FakeStorage()

    storage._generate_token = MagicMock(return_value='1')
    storage._get = MagicMock(return_value='1')
    storage._save = MagicMock()

    assert storage._generate_token.call_count == 0

    request = make_mocked_request('/', 'GET')

    await storage.generate_new_token(request)

    assert storage._generate_token.call_count == 1

    await storage.generate_new_token(request)
    await storage.generate_new_token(request)

    assert storage._generate_token.call_count == 1


async def test_2():
    storage = FakeStorage()

    storage._generate_token = MagicMock(return_value='1')

    request = make_mocked_request('/', 'GET')

    assert storage._generate_token.call_count == 0

    await storage.save_token(request, None)

    assert storage._generate_token.call_count == 1

    request2 = make_mocked_request('/', 'GET')

    request2['my_field'] = 1

    await storage.save_token(request2, None)


async def test_3():
    class Some:
        pass

    token_generator = Some()

    with pytest.raises(TypeError):
        FakeStorage(token_generator=token_generator)
