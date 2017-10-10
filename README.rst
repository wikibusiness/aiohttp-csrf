aiohttp_csrf
============

The library provides csrf (xsrf) protection for `aiohttp.web`__.

.. _aiohttp_web: https://aiohttp.readthedocs.io/en/latest/web.html

__ aiohttp_web_

.. image:: https://img.shields.io/travis/wikibusiness/aiohttp-csrf.svg
    :target: https://travis-ci.org/wikibusiness/aiohttp-csrf

Usage
-----

The library allows us to implement csrf (xsrf) protection for requests

Basic usage example:

.. code-block:: python

    import aiohttp_csrf
    from aiohttp import web

    FORM_FIELD_NAME = '_csrf_token'
    COOKIE_NAME = 'csrf_token'


    async def handler_get_form_with_token(request):
        token = await aiohttp_csrf.generate_token(request)

        body = '''
            <html>
                <head><title>Form with csrf protection</title></head>
                <body>
                    <form method="POST" action="/post_with_check">
                        <input type="hidden" name="{field}" value="{value}" />
                        <input type="text" name="name" />
                        <input type="submit" value="Say hello">
                    </form>
                </body>
            </html>
        '''

        body = body.format(
            field=FORM_FIELD_NAME,
            value=token,
        )

        return web.Response(body=body.encode('utf-8'), content_type='text/html')


    async def handler_get_form_without_token(request):
        body = '''
            <html>
                <head><title>Form without csrf protection</title></head>
                <body>
                    <form method="POST" action="/post_without_check">
                        <input type="text" name="name" />
                        <input type="submit" value="Say hello">
                    </form>
                </body>
            </html>
        '''

        return web.Response(body=body.encode('utf-8'), content_type='text/html')


    async def handler_post_check(request):
        post = await request.post()

        body = 'Hello, {name}'.format(name=post['name'])

        return web.Response(body=body.encode('utf-8'), content_type='text/html')


    @aiohttp_csrf.not_check
    async def handler_post_not_check(request):
        post = await request.post()

        body = 'Hello, {name}'.format(name=post['name'])

        return web.Response(body=body.encode('utf-8'), content_type='text/html')


    def make_app():
        csrf_storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

        csrf_policy = aiohttp_csrf.policy.FormPolicy(FORM_FIELD_NAME)

        csrf_middleware = aiohttp_csrf.CsrfMiddleware(
            policy=csrf_policy,
            storage=csrf_storage,
            global_mode=True,
        )

        middlewares = [csrf_middleware.middleware_factory]

        app = web.Application(middlewares=middlewares)

        app.router.add_route(
            'GET',
            '/form_with_check',
            handler_get_form_with_token,
        )
        app.router.add_route(
            'GET',
            '/form_without_check',
            handler_get_form_without_token,
        )

        app.router.add_route(
            'POST',
            '/post_with_check',
            handler_post_check,
        )
        app.router.add_route(
            'POST',
            '/post_without_check',
            handler_post_not_check,
        )

        return app


    web.run_app(make_app())


First of all, you have to create ``aiohttp_csrf.CsrfMiddleware`` and register it in ``aiohttp.web.Application``.

When you create instance of ``aiohttp_csrf.CsrfMiddleware`` you have to specify several required and several optional parameters

Required parameters:

- **policy**. This object defines how we will check csrf token. Object must implement ``aiohttp_csrf.policy.AbstractPolicy`` interface.
- **storage**. This is object, that define how and where we will store token. Object must implement ``aiohttp_csrf.storages.AbstractStorage`` interface.

Optional parameters:

- **global_mode**. This is a boolean value. From this value depends on whether we will check the token for all requests (for HTTP methods "POST", "PUT", "DELETE"), or only for those which are marked with ``aiohttp_csrf.check`` decorator. Default: ``True``
- **methods**. This is a tuple with methods, that we will be checking. Default: ``('POST', 'PUT', 'DELETE')``
- **error_renderer**. This is an exception, that will be raised, when token check will be fail.
