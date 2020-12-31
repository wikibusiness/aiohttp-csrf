import asyncio

import aiohttp_csrf
import pytest
from aiohttp import web

COOKIE_NAME = 'csrf_token'
HEADER_NAME = 'X-CSRF-TOKEN'


@pytest.yield_fixture
def create_app(init_app):
    def go(loop, error_renderer):
        @aiohttp_csrf.csrf_protect
        async def handler_get(request):
            await aiohttp_csrf.generate_token(request)

            return web.Response(body=b'OK')

        @aiohttp_csrf.csrf_protect(error_renderer=error_renderer)
        async def handler_post(request):
            return web.Response(body=b'OK')

        handlers = [
            ('GET', '/', handler_get),
            ('POST', '/', handler_post)
        ]

        storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)
        policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)

        app = init_app(
            policy=policy,
            storage=storage,
            handlers=handlers,
            loop=loop,
        )

        return app

    yield go


async def test_custom_exception_error_renderer(test_client, create_app):
    client = await test_client(
        create_app,
        error_renderer=web.HTTPBadRequest,
    )

    await client.get('/')

    resp = await client.post('/')

    assert resp.status == web.HTTPBadRequest.status_code


@pytest.fixture(params=[False, True])
def make_error_renderer(request):
    is_coroutine = request.param

    def make_renderer(error_body):
        def error_renderer(request):
            return web.Response(body=error_body)

        if not is_coroutine:
            return error_renderer

        return asyncio.coroutine(error_renderer)

    return make_renderer


async def test_custom_coroutine_callable_error_renderer(test_client, create_app, make_error_renderer):  # noqa
    error_body = b'CSRF error'

    error_renderer = make_error_renderer(error_body)

    client = await test_client(
        create_app,
        error_renderer=error_renderer,
    )

    await client.get('/')

    resp = await client.post('/')

    assert resp.status == 200

    assert await resp.read() == error_body


async def test_bad_error_renderer(test_client, create_app):
    error_renderer = 'trololo'

    with pytest.raises(TypeError):
        await test_client(
            create_app,
            error_renderer=error_renderer,
        )
