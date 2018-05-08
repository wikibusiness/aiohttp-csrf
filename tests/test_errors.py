import aiohttp_csrf
import pytest
from aiohttp import web

COOKIE_NAME = 'csrf_token'
HEADER_NAME = 'X-CSRF-TOKEN'


class FakeClass:
    pass


async def test_bad_policy(test_client, init_app):
    policy = FakeClass()
    storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    with pytest.raises(TypeError):
        await test_client(
            init_app,
            policy=policy,
            storage=storage,
            handlers=[],
        )


async def test_bad_storage(test_client, init_app):
    policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
    storage = FakeClass()

    with pytest.raises(TypeError):
        await test_client(
            init_app,
            policy=policy,
            storage=storage,
            handlers=[],
        )


async def test_bad_error_renderer(test_client, init_app):
    policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
    storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    with pytest.raises(TypeError):
        await test_client(
            init_app,
            policy=policy,
            storage=storage,
            error_renderer=1,
            handlers=[],
        )


async def test_app_without_setup(test_client):
    def create_app(loop):
        app = web.Application()

        @aiohttp_csrf.csrf_protect
        async def handler(request):
            await aiohttp_csrf.generate_token(request)

            return web.Response()

        app.router.add_route(
            'GET',
            '/',
            handler,
        )

        return app

    client = await test_client(
        create_app,
    )

    resp = await client.get('/')

    assert resp.status == 500
