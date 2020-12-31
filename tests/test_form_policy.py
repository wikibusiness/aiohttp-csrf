import re
import uuid
from unittest import mock

import aiohttp_csrf
import pytest
from aiohttp import web
from aiohttp_session import setup as setup_session
from aiohttp_session import SimpleCookieStorage

from .conftest import FORM_FIELD_NAME

FORM_FIELD_REGEX = re.compile(
    r'<input.*name="' + FORM_FIELD_NAME + '".*value="(?P<token>[^"]+)".*>',
)


@pytest.yield_fixture
def create_app(init_app):
    def go(loop, policy, storage):
        async def handler_get(request):
            token = await aiohttp_csrf.generate_token(request)

            body = '''
                <html>
                    <head></head>
                    <body>
                        <form>
                            <input type="hidden" name="{field_name}" value="{token}" />
                        </form>
                    </body>
                </html>
            '''  # noqa

            body = body.format(field_name=FORM_FIELD_NAME, token=token)

            return web.Response(body=body.encode('utf-8'))

        async def handler_post(request):
            return web.Response(body=b'OK')

        handlers = [
            ('GET', '/', handler_get),
            ('POST', '/', handler_post)
        ]

        app = init_app(
            policy=policy,
            storage=storage,
            handlers=handlers,
            loop=loop,
        )

        if isinstance(storage, aiohttp_csrf.storage.SessionStorage):
            session_storage = SimpleCookieStorage()
            setup_session(app, session_storage)

        app.middlewares.append(aiohttp_csrf.csrf_middleware)

        return app

    yield go


async def test_form_policy_success(
    test_client,
    create_app,
    csrf_form_policy,
    csrf_storage,
):
    client = await test_client(
        create_app,
        policy=csrf_form_policy,
        storage=csrf_storage,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    token = search_result.group('token')

    data = {FORM_FIELD_NAME: token}

    resp = await client.post('/', data=data)

    assert resp.status == 200


async def test_form_policy_bad_token(
    test_client,
    create_app,
    csrf_form_policy,
    csrf_storage,
):
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
            policy=csrf_form_policy,
            storage=csrf_storage,
        )

        resp = await client.get('/')

        assert resp.status == 200

        data = {FORM_FIELD_NAME: bad_token}

        resp = await client.post('/', data=data)

        assert resp.status == 403


async def test_form_policy_reuse_token(
    test_client,
    create_app,
    csrf_form_policy,
    csrf_storage,
):
    client = await test_client(
        create_app,
        policy=csrf_form_policy,
        storage=csrf_storage,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    token = search_result.group('token')

    data = {FORM_FIELD_NAME: token}

    resp = await client.post('/', data=data)

    assert resp.status == 200

    resp = await client.post('/', data=data)

    assert resp.status == 403
