aiohttp_csrf
=============

The library provides csrf (xsrf) protection for [aiohttp.web](https://docs.aiohttp.org/en/latest/web.html).

**Breaking Change:** New in 0.1.0 is Blake3 hashes are used by default. This means you must pass `secret_phrase` to
`aiohttp_csrf.storage.SessionStorage`

**note:** The package [aiohttp-csrf-fixed](https://pypi.org/project/aiohttp-csrf-fixed) is aiohttp_csrf 0.0.2 +
[this commit](https://github.com/oplik0/aiohttp-csrf/commit/b1bd9207f43a2abf30e32e72ecdb10983a251823). The maintainer
didn't submit a PR so I just saw it by chance. I haven't had  time to closely examine it but I think it's just removing
the HTTP security error that happens if no CSRF is provided. Why do that? An HTTP error is good because it tells the
client what happened and lets you handle it by middleware.

__0.1.1:__ Converted `@aiohttp_csrf.csrf_exempt` decorator to a co-routine to make it compatible with latest aiohttp.

![image](https://img.shields.io/travis/wikibusiness/aiohttp-csrf.svg%0A%20:target:%20https://travis-ci.org/wikibusiness/aiohttp-csrf)

Basic usage
-----------

The library allows you to implement csrf (xsrf) protection for requests

Basic usage example:

```python
import aiohttp_csrf
from aiohttp import web

FORM_FIELD_NAME = '_csrf_token'
COOKIE_NAME = 'csrf_token'


def make_app():
    csrf_policy = aiohttp_csrf.policy.FormPolicy(FORM_FIELD_NAME)

    csrf_storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

    app = web.Application()

    aiohttp_csrf.setup(app, policy=csrf_policy, storage=csrf_storage)

    app.middlewares.append(aiohttp_csrf.csrf_middleware)

    async def handler_get_form_with_token(request):
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

    async def handler_post_check(request):
        post = await request.post()

        body = 'Hello, {name}'.format(name=post['name'])

        return web.Response(
            body=body.encode('utf-8'),
            content_type='text/html',
        )

    app.router.add_route(
        'GET',
        '/',
        handler_get_form_with_token,
    )

    app.router.add_route(
        'POST',
        '/',
        handler_post_check,
    )

    return app


web.run_app(make_app())
```

### Initialize

First of all, you need to initialize `aiohttp_csrf` in your application:

```python
app = web.Application()

csrf_policy = aiohttp_csrf.policy.FormPolicy(FORM_FIELD_NAME)

csrf_storage = aiohttp_csrf.storage.CookieStorage(COOKIE_NAME)

aiohttp_csrf.setup(app, policy=csrf_policy, storage=csrf_storage)
```

### Middleware and decorators

After initialize you can use `@aiohttp_csrf.csrf_protect` for handlers, that you want to protect. Or you can
initialize `aiohttp_csrf.csrf_middleware` and do not disturb about using
decorator ([full middleware example here](demo/middleware.py)):

```python
# ...
app.middlewares.append(aiohttp_csrf.csrf_middleware)
# ...
```

In this case all your handlers will be protected.

**Note:** we strongly recommend to use `aiohttp_csrf.csrf_middleware` and `@aiohttp_csrf.csrf_exempt` instead of
manually managing with `@aiohttp_csrf.csrf_protect`. But if you prefer to use `@aiohttp_csrf.csrf_protect`, don't forget
to use `@aiohttp_csrf.csrf_protect` for both methods: GET and
POST ([manual protection example](demo/manual_protection.py))

If you want to use middleware, but need handlers without protection, you can use `@aiohttp_csrf.csrf_exempt`. Mark you
handler with this decorator and this handler will not check the token:

```python
@aiohttp_csrf.csrf_exempt
async def handler_post_not_check(request):
    ...
```

### Generate token

For generate token you need to call `aiohttp_csrf.generate_token` in your handler:

```python
@aiohttp_csrf.csrf_protect
async def handler_get(request):
    token = await aiohttp_csrf.generate_token(request)
    ...
```

Advanced usage
--------------

### Policies

You can use different policies for check tokens. Library provides 3 types of policy:

- **FormPolicy**. This policy will search token in the body of your POST request (Usually use for forms) or as a GET
  variable of the same name. You need to specify name of field that will be checked.
- **HeaderPolicy**. This policy will search token in headers of your POST request (Usually use for AJAX requests). You
  need to specify name of header that will be checked.
- **FormAndHeaderPolicy**. This policy combines behavior of **FormPolicy** and **HeaderPolicy**.

You can implement your custom policies if needed. But make sure that your custom policy
implements `aiohttp_csrf.policy.AbstractPolicy` interface.

### Storages

You can use different types of storages for storing token. Library provides 2 types of storage:

- **CookieStorage**. Your token will be stored in cookie variable. You need to specify cookie name.
- **SessionStorage**. Your token will be stored in session. You need to specify session variable name.

**Important:** If you want to use session storage, you need setup aiohttp\_session in your
application ([session storage example](demo/session_storage.py#L22))

You can implement your custom storages if needed. But make sure that your custom storage
implements `aiohttp_csrf.storage.AbstractStorage` interface.

### Token generators

You can use different token generator in your application. By default storages
using `aiohttp_csrf.token_generator.SimpleTokenGenerator`

But if you need more secure token generator - you can use `aiohttp_csrf.token_generator.HashedTokenGenerator`

And you can implement your custom token generators if needed. But make sure that your custom token generator
implements `aiohttp_csrf.token_generator.AbstractTokenGenerator` interface.

### Invalid token behavior

By default, if token is invalid, `aiohttp_csrf` will raise `aiohttp.web.HTTPForbidden` exception.

You have ability to specify your custom error handler. It can be:

- **callable instance. Input parameter - aiohttp request.**

```python
def custom_error_handler(request):
    # do something
    return aiohttp.web.Response(status=403)

# or

async def custom_async_error_handler(request):
    # await do something
    return aiohttp.web.Response(status=403)
```

It will be called instead of protected handler.

- **sub class of Exception**. In this case this Exception will be raised.

```python
class CustomException(Exception):
    pass
```

You can specify custom error handler globally, when initialize `aiohttp_csrf` in your application:

```python
...
class CustomException(Exception):
    pass

...
aiohttp_csrf.setup(app, policy=csrf_policy, storage=csrf_storage, error_renderer=CustomException)
...
```

In this case custom error handler will be applied to all protected handlers.

Or you can specify custom error handler locally, for specific handler:

```python
...
class CustomException(Exception):
    pass

...
@aiohttp_csrf.csrf_protect(error_renderer=CustomException)
def handler_with_custom_csrf_error(request):
    ...
```

In this case custom error handler will be applied to this handler only. For all other handlers will be applied global
error handler.
