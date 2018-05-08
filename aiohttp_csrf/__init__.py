import asyncio
import inspect

from functools import wraps

from aiohttp import web

from .policy import AbstractPolicy
from .storage import AbstractStorage


__version__ = '0.0.1'

APP_POLICY_KEY = 'aiohttp_csrf_policy'
APP_STORAGE_KEY = 'aiohttp_csrf_storage'
APP_ERROR_RENDERER_KEY = 'aiohttp_csrf_error_renderer'

MIDDLEWARE_SKIP_PROPERTY = 'csrf_middleware_skip'

UNPROTECTED_HTTP_METHODS = ('GET', 'HEAD', 'OPTIONS', 'TRACE')


def setup(app, *, policy, storage, error_renderer=web.HTTPForbidden):
    if not isinstance(policy, AbstractPolicy):
        raise TypeError('Policy must be instance of AbstractPolicy')

    if not isinstance(storage, AbstractStorage):
        raise TypeError('Storage must be instance of AbstractStorage')

    if not isinstance(error_renderer, Exception) and not callable(error_renderer):  # noqa
        raise TypeError(
            'Default error renderer must be instance of Exception or callable.'
        )

    app[APP_POLICY_KEY] = policy
    app[APP_STORAGE_KEY] = storage
    app[APP_ERROR_RENDERER_KEY] = error_renderer


def _get_policy(request):
    try:
        return request.app[APP_POLICY_KEY]
    except KeyError:
        raise RuntimeError(
            'Policy not found. Install aiohttp_csrf in your '
            'aiohttp.web.Application using aiohttp_csrf.setup()'
        )


def _get_storage(request):
    try:
        return request.app[APP_STORAGE_KEY]
    except KeyError:
        raise RuntimeError(
            'Storage not found. Install aiohttp_csrf in your '
            'aiohttp.web.Application using aiohttp_csrf.setup()'
        )


async def _render_error(request, error_renderer=None):
    if error_renderer is None:
        try:
            error_renderer = request.app[APP_ERROR_RENDERER_KEY]
        except KeyError:
            raise RuntimeError(
                'Default error renderer not found. Install aiohttp_csrf in '
                'your aiohttp.web.Application using aiohttp_csrf.setup()'
            )

    if inspect.isclass(error_renderer) and issubclass(error_renderer, Exception):  # noqa
        raise error_renderer
    elif callable(error_renderer):
        if asyncio.iscoroutinefunction(error_renderer):
            return await error_renderer(request)
        else:
            return error_renderer(request)
    else:
        raise NotImplementedError


async def get_token(request):
    storage = _get_storage(request)

    return await storage.get(request)


async def generate_token(request):
    storage = _get_storage(request)

    return await storage.generate_new_token(request)


async def save_token(request, response):
    storage = _get_storage(request)

    await storage.save_token(request, response)


def csrf_exempt(handler):
    @wraps(handler)
    def wrapped_handler(*args, **kwargs):
        return handler(*args, **kwargs)

    setattr(wrapped_handler, MIDDLEWARE_SKIP_PROPERTY, True)

    return wrapped_handler


async def _check(request):
    if not isinstance(request, web.Request):
        raise RuntimeError('Can\'t get request from handler params')

    original_token = await get_token(request)

    policy = _get_policy(request)

    return await policy.check(request, original_token)


def csrf_protect(handler=None, error_renderer=None):
    if (
        error_renderer is not None
        and not isinstance(error_renderer, Exception)
        and not callable(error_renderer)
    ):
        raise TypeError(
            'Renderer must be instance of Exception or callable.'
        )

    def wrapper(handler):
        @wraps(handler)
        async def wrapped(*args, **kwargs):
            request = args[-1]

            if isinstance(request, web.View):
                request = request.request

            if (
                request.method not in UNPROTECTED_HTTP_METHODS
                and not await _check(request)
            ):
                return await _render_error(request, error_renderer)

            raise_response = False

            try:
                response = await handler(*args, **kwargs)
            except web.HTTPException as exc:
                response = exc
                raise_response = True

            if isinstance(response, web.Response):
                await save_token(request, response)

            if raise_response:
                raise response

            return response

        setattr(wrapped, MIDDLEWARE_SKIP_PROPERTY, True)

        return wrapped

    if handler is None:
        return wrapper

    return wrapper(handler)


@web.middleware
async def csrf_middleware(request, handler):
    if not getattr(handler, MIDDLEWARE_SKIP_PROPERTY, False):
        handler = csrf_protect(handler=handler)

    return await handler(request)
