import aiohttp_csrf
import pytest
from aiohttp import web
from aiohttp_session import setup as setup_session
from aiohttp_session import SimpleCookieStorage

COOKIE_NAME = SESSION_NAME = 'csrf_token'

HEADER_NAME = 'X-CSRF-TOKEN'


@pytest.fixture(params=[True, False])
def global_mode(request):
    return request.param


def create_app(loop, global_mode_option):

    csrf_storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    csrf_policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)

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
        await aiohttp_csrf.generate_token(request)

        return web.Response(body=b'OK')

    async def handler_post_global_check(request):
        return web.Response(body=b'OK')

    @aiohttp_csrf.check
    async def handler_post_required_check(request):
        return web.Response(body=b'OK')

    @aiohttp_csrf.not_check
    async def handler_post_required_not_check(request):
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

    return app


async def test_global_check_success(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    if global_mode:
        token = resp.cookies[COOKIE_NAME].value

        headers = {HEADER_NAME: token}
    else:
        headers = {}

    resp = await client.post('/global_check', headers=headers)

    assert resp.status == 200


async def test_global_check_failure(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    resp = await client.post('/global_check')

    if global_mode:
        assert resp.status == 403
    else:
        assert resp.status == 200


async def test_global_check_with_wrong_token(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    await client.get('/')

    resp = await client.post('/global_check', headers=headers)

    if global_mode:
        assert resp.status == 403
    else:
        assert resp.status == 200


async def test_required_check_success(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    resp = await client.post('/required_check', headers=headers)

    assert resp.status == 200


async def test_required_check_failure(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    resp = await client.post('/required_check')

    assert resp.status == 403


async def test_required_check_with_wrong_token(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    await client.get('/')

    resp = await client.post('/required_check', headers=headers)

    assert resp.status == 403


async def test_required_not_check_success(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    resp = await client.post('/required_not_check')

    assert resp.status == 200


async def test_required_not_check_with_wrong_key(test_client, global_mode):
    client = await test_client(
        create_app,
        global_mode_option=global_mode,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    await client.get('/')

    resp = await client.post('/required_not_check', headers=headers)

    assert resp.status == 200
