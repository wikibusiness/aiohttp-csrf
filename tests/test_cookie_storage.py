import uuid
from unittest import mock

import aiohttp_csrf
import pytest
from aiohttp import web

COOKIE_NAME = 'csrf_token'
FORM_FIELD_NAME = '_csrf_token'
AIOHTTP_SESSION_COOKIE_NAME = 'AIOHTTP_SESSION'


@pytest.fixture(params=[True, False])
def global_mode(request):
    return request.param


def create_app(loop, global_mode_option, handler):
    csrf_storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    csrf_policy = aiohttp_csrf.policy.FormPolicy(FORM_FIELD_NAME)

    csrf_middleware = aiohttp_csrf.CsrfMiddleware(
        policy=csrf_policy,
        storage=csrf_storage,
        global_mode=global_mode_option,
    )

    middlewares = [csrf_middleware.middleware_factory]
    app = web.Application(middlewares=middlewares, loop=loop)

    app.router.add_route('GET', '/', handler)

    return app


async def test_storage_manual_generate_key(test_client, global_mode):

    async def handler(request):
        await aiohttp_csrf.generate_token(request)

        return web.Response(body=b'OK')

    client = await test_client(
        create_app,
        global_mode_option=global_mode,
        handler=handler,
    )

    token = str(uuid.uuid4())

    with mock.patch(
        'aiohttp_csrf.storage.BaseStorage._generate_token',
        return_value=token,
    ):
        response = await client.get('/')

    cookie = response.cookies.get(COOKIE_NAME).value

    assert token == cookie


async def test_storage_auto_generate_key(test_client, global_mode):

    async def handler(request):
        return web.Response(body=b'OK')

    client = await test_client(
        create_app,
        global_mode_option=global_mode,
        handler=handler,
    )

    token = str(uuid.uuid4())

    with mock.patch(
        'aiohttp_csrf.storage.BaseStorage._generate_token',
        return_value=token,
    ):
        response = await client.get('/')

    cookie = response.cookies.get(COOKIE_NAME).value

    assert token == cookie


async def test_storage_manual_several_generate_key(test_client, global_mode):

    async def handler(request):
        await aiohttp_csrf.generate_token(request)
        await aiohttp_csrf.generate_token(request)
        await aiohttp_csrf.generate_token(request)

        return web.Response(body=b'OK')

    client = await test_client(
        create_app,
        global_mode_option=global_mode,
        handler=handler,
    )

    token = str(uuid.uuid4())

    with mock.patch(
        'aiohttp_csrf.storage.BaseStorage._generate_token',
        return_value=token,
    ) as mocked_generate_key:
        await client.get('/')

        assert mocked_generate_key.call_count == 1


async def test_storage_with_wrong_key_generator():
    class FakeKeyGenerator:
        pass

    fake_key_generator = FakeKeyGenerator()

    with pytest.raises(TypeError):
        aiohttp_csrf.storage.CookieStorage(
            COOKIE_NAME,
            token_generator=fake_key_generator,
        )
