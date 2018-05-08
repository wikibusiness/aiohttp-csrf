import aiohttp_csrf
from aiohttp import web

COOKIE_NAME = 'csrf_token'
HEADER_NAME = 'X-CSRF-TOKEN'


async def test_decorator_method_view(test_client, init_app):
    @aiohttp_csrf.csrf_protect
    async def handler_get(request):
        await aiohttp_csrf.generate_token(request)

        return web.Response(body=b'OK')

    @aiohttp_csrf.csrf_protect
    async def handler_post(request):
        return web.Response(body=b'OK')

    handlers = [
        ('GET', '/', handler_get),
        ('POST', '/', handler_post)
    ]

    policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
    storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    client = await test_client(
        init_app,
        policy=policy,
        storage=storage,
        handlers=handlers,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    resp = await client.post('/', headers=headers)

    assert resp.status == 200

    resp = await client.post('/', headers=headers)

    assert resp.status == 403


async def test_decorator_class_view(test_client):
    class TestView(web.View):
        @aiohttp_csrf.csrf_protect
        async def get(self):
            await aiohttp_csrf.generate_token(self.request)

            return web.Response(body=b'OK')

        @aiohttp_csrf.csrf_protect
        async def post(self):
            return web.Response(body=b'OK')

    def create_app(loop):
        policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
        storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

        app = web.Application()

        aiohttp_csrf.setup(app, policy=policy, storage=storage)

        if hasattr(app.router, 'add_view'):
            # For aiohttp >= 3.0.0
            app.router.add_view('/', TestView)
        else:
            app.router.add_route('*', '/', TestView)

        return app

    client = await test_client(
        create_app,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    resp = await client.post('/', headers=headers)

    assert resp.status == 200

    resp = await client.post('/', headers=headers)

    assert resp.status == 403


async def test_handle_http_exceptions(test_client, init_app):
    @aiohttp_csrf.csrf_protect
    async def handler_get(request):
        await aiohttp_csrf.generate_token(request)

        return web.Response(body=b'OK')

    @aiohttp_csrf.csrf_protect
    async def handler_post(request):
        raise web.HTTPBadRequest

    handlers = [
        ('GET', '/', handler_get),
        ('POST', '/', handler_post)
    ]

    policy = aiohttp_csrf.policy.HeaderPolicy(HEADER_NAME)
    storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    client = await test_client(
        init_app,
        policy=policy,
        storage=storage,
        handlers=handlers,
    )

    resp = await client.get('/')

    assert resp.status == 200

    token = resp.cookies[COOKIE_NAME].value

    headers = {HEADER_NAME: token}

    resp = await client.post('/', headers=headers)

    assert resp.status == 400
