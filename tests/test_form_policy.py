import re

import aiohttp_csrf
import pytest
from aiohttp import web
from aiohttp_session import setup as setup_session
from aiohttp_session import SimpleCookieStorage

COOKIE_NAME = SESSION_NAME = 'csrf_token'

FORM_FIELD_NAME = '_csrf_token'


FORM_FIELD_REGEX = re.compile(
    r'<input.*name="' + FORM_FIELD_NAME + '".*value="(?P<value>[^"]+)".*>',
)


def create_cookie_storage():
    storage_obj = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    return storage_obj


def create_session_storage():
    storage_obj = aiohttp_csrf.storage.SessionStorage(SESSION_NAME)

    return storage_obj


@pytest.fixture(
    params=[
        create_cookie_storage,
        create_session_storage,
    ]
)
def storage(request):
    storage_factory = request.param

    return storage_factory()


@pytest.fixture(params=[True, False])
def global_mode(request):
    return request.param


def create_app(loop, csrf_storage, global_mode_option):

    csrf_policy = aiohttp_csrf.policy.FormPolicy(FORM_FIELD_NAME)

    csrf_middleware = aiohttp_csrf.CsrfMiddleware(
        policy=csrf_policy,
        storage=csrf_storage,
        global_mode=global_mode_option,
    )

    app = web.Application(loop=loop)

    session_storage = SimpleCookieStorage()

    setup_session(app, session_storage)

    app.middlewares.append(csrf_middleware.middleware_factory)

    async def handler_get(request):
        token = await aiohttp_csrf.generate_token(request)

        body = '''
            <html>
                <head></head>
                <body>
                    <form>
                        <input type="hidden" name="{field}" value="{value}" />
                    </form>
                </body>
            </html>
        '''

        body = body.format(
            field=FORM_FIELD_NAME,
            value=token,
        )
        return web.Response(body=body.encode('utf-8'))

    async def handler_post_global_check(request):
        return web.Response(body=b'OK')

    @aiohttp_csrf.check
    async def handler_post_required_check(request):
        return web.Response(body=b'OK')

    @aiohttp_csrf.not_check
    async def handler_post_required_not_check(request):
        return web.Response(body=b'OK')

    @aiohttp_csrf.not_check
    async def handler_post_manual_check(request):
        post = await request.post()

        original_token = await aiohttp_csrf.get_token(request)

        if post.get(FORM_FIELD_NAME) != original_token:
            raise web.HTTPForbidden

        return web.Response(body=b'OK')

    app.router.add_route('GET', '/', handler_get)
    app.router.add_route(
        'POST',
        '/global_check',
        handler_post_global_check,
    )
    app.router.add_route(
        'POST',
        '/required_check',
        handler_post_required_check,
    )
    app.router.add_route(
        'POST',
        '/required_not_check',
        handler_post_required_not_check,
    )

    app.router.add_route(
        'POST',
        '/manual_check',
        handler_post_manual_check,
    )

    return app


async def test_global_check_success(test_client, storage, global_mode):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    if global_mode:
        body = await resp.text()

        search_result = FORM_FIELD_REGEX.search(body)

        value = search_result.group('value')

        data = {FORM_FIELD_NAME: value}
    else:
        data = {}

    resp = await client.post('/global_check', data=data)

    assert resp.status == 200


async def test_global_check_failure(test_client, storage, global_mode):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    resp = await client.post('/global_check')

    if global_mode:
        assert resp.status == 403
    else:
        assert resp.status == 200


async def test_global_check_with_wrong_token(
    test_client,
    storage,
    global_mode,
):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    value = search_result.group('value')

    data = {FORM_FIELD_NAME: value}

    await client.get('/')

    resp = await client.post('/global_check', data=data)

    if global_mode:
        assert resp.status == 403
    else:
        assert resp.status == 200


async def test_required_check_success(test_client, storage, global_mode):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    value = search_result.group('value')

    data = {FORM_FIELD_NAME: value}

    resp = await client.post('/required_check', data=data)

    assert resp.status == 200


async def test_required_check_failure(test_client, storage, global_mode):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    resp = await client.post('/required_check')

    assert resp.status == 403


async def test_required_check_with_wrong_token(
    test_client,
    storage,
    global_mode,
):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    value = search_result.group('value')

    data = {FORM_FIELD_NAME: value}

    await client.get('/')

    resp = await client.post('/required_check', data=data)

    assert resp.status == 403


async def test_required_not_check_success(test_client, storage, global_mode):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    resp = await client.post('/required_not_check')

    assert resp.status == 200


async def test_required_not_check_with_wrong_key(
    test_client,
    storage,
    global_mode,
):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    value = search_result.group('value')

    data = {FORM_FIELD_NAME: value}

    await client.get('/')

    resp = await client.post('/required_not_check', data=data)

    assert resp.status == 200


async def test_manual_check_success(test_client, storage, global_mode):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    value = search_result.group('value')

    data = {FORM_FIELD_NAME: value}

    resp = await client.post('/manual_check', data=data)

    assert resp.status == 200


async def test_manual_check_failure(test_client, storage, global_mode):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    resp = await client.post('/manual_check')

    assert resp.status == 403


async def test_manual_check_with_wrong_token(
    test_client,
    storage,
    global_mode,
):
    client = await test_client(
        create_app,
        csrf_storage=storage,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    body = await resp.text()

    search_result = FORM_FIELD_REGEX.search(body)

    value = search_result.group('value')

    data = {FORM_FIELD_NAME: value}

    await client.get('/')

    resp = await client.post('/manual_check', data=data)

    assert resp.status == 403
