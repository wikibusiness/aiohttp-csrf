import uuid
from unittest import mock

import aiohttp_csrf
import pytest
from aiohttp import web

from .conftest import COOKIE_NAME, HEADER_NAME


@pytest.yield_fixture
def create_app(init_app):
    def go(loop, policy):
        async def handler_get(request):
            await aiohttp_csrf.generate_token(request)

            return web.Response(body=b'OK')

        async def handler_post(request):
            return web.Response(body=b'OK')

        handlers = [
            ('GET', '/', handler_get),
            ('POST', '/', handler_post)
        ]

        storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

        app = init_app(
            policy=policy,
            storage=storage,
            handlers=handlers,
            loop=loop,
        )

        app.middlewares.append(aiohttp_csrf.csrf_middleware)

        return app

    yield go


async def test_header_policy_success(test_client, create_app, csrf_header_policy):  # noqa
    client = await test_client(
        create_app,
        policy=csrf_header_policy,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    resp = await client.post('/', headers=headers)

    assert resp.status == 200


async def test_header_policy_bad_token(test_client, create_app, csrf_header_policy):  # noqa
    real_token = uuid.uuid4().hex

    bad_token = real_token

    while bad_token == real_token:
        bad_token = uuid.uuid4().hex

    with mock.patch(
        'aiohttp_csrf.token_generator.SimpleTokenGenerator.generate',
        return_value=real_token,
    ):

        client = await test_client(
            create_app,
            policy=csrf_header_policy,
        )

        resp = await client.get('/')

        assert resp.status == 200

        headers = {HEADER_NAME: bad_token}

        resp = await client.post('/', headers=headers)

        assert resp.status == 403


async def test_header_policy_reuse_token(test_client, create_app, csrf_header_policy):  # noqa
    client = await test_client(
        create_app,
        policy=csrf_header_policy,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    resp = await client.post('/', headers=headers)

    assert resp.status == 200

    resp = await client.post('/', headers=headers)

    assert resp.status == 403
