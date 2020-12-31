import aiohttp_csrf
from aiohttp import web

FORM_FIELD_NAME = '_csrf_token'
COOKIE_NAME = 'csrf_token'


def make_app():
    csrf_policy = aiohttp_csrf.policy.FormPolicy(FORM_FIELD_NAME)

    csrf_storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    app = web.Application()

    aiohttp_csrf.setup(app, policy=csrf_policy, storage=csrf_storage)

    # IMPORTANT! You need use @csrf_protect for both methods: GET and POST
    @aiohttp_csrf.csrf_protect
    async def handler_get(request):
        token = await aiohttp_csrf.generate_token(request)

        body = '''
            <html>
                <head><title>Form with csrf protection</title></head>
                <body>
                    <form method="POST" action="/">
                        <input type="hidden" name="{field_name}" value="{token}" />
                        <input type="text" name="name" />
                        <input type="submit" value="Say hello">
                    </form>
                </body>
            </html>
        '''  # noqa

        body = body.format(field_name=FORM_FIELD_NAME, token=token)

        return web.Response(
            body=body.encode('utf-8'),
            content_type='text/html',
        )

    @aiohttp_csrf.csrf_protect
    async def handler_post(request):
        post = await request.post()

        body = 'Hello, {name}'.format(name=post['name'])

        return web.Response(
            body=body.encode('utf-8'),
            content_type='text/html',
        )

    app.router.add_route(
        'GET',
        '/',
        handler_get,
    )

    app.router.add_route(
        'POST',
        '/',
        handler_post,
    )

    return app


web.run_app(make_app())
