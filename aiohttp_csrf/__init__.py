from functools import wraps

from aiohttp import web


from .policy import AbstractPolicy
from .storage import AbstractStorage


__version__ = '0.0.1'

REQUEST_STORAGE_KEY = 'aiohttp_csrf_storage'
DECORATOR_FIELD_NAME = 'aiohttp_csrf_check'


async def get_token(request):
    storage = request.get(REQUEST_STORAGE_KEY)

    if storage is None:
        raise RuntimeError(
            "Install aiohttp_csrf middleware in your aiohttp.web.Application",
        )

    return await storage.get(request)


async def generate_token(request):
    storage = request.get(REQUEST_STORAGE_KEY)

    if storage is None:
        raise RuntimeError(
            "Install aiohttp_csrf middleware in your aiohttp.web.Application",
        )

    return await storage.generate_new_token(request)


def check(handler):
    handler.__dict__[DECORATOR_FIELD_NAME] = True

    @wraps(handler)
    async def wrapped(*args, **kwargs):
        return await handler(*args, **kwargs)

    return wrapped


def not_check(handler):
    handler.__dict__[DECORATOR_FIELD_NAME] = False

    @wraps(handler)
    async def wrapped(*args, **kwargs):
        return await handler(*args, **kwargs)

    return wrapped


class CsrfMiddleware:
    def __init__(
        self,
        policy,
        storage,
        global_mode=False,
        methods=('POST', 'PUT', 'DELETE'),
        error_renderer=web.HTTPForbidden,
    ):
        if not isinstance(policy, AbstractPolicy):
            raise TypeError('Policy must be instance of AbstractPolicy')

        self.policy = policy

        if not isinstance(storage, AbstractStorage):
            raise TypeError('Storage must be instance of AbstractStorage')

        self.storage = storage

        self.methods = methods
        self.global_mode = global_mode

        self.error_renderer = error_renderer

    async def middleware_factory(self, app, handler):
        async def middleware_handler(request):
            request[REQUEST_STORAGE_KEY] = self.storage

            is_need_check = handler.__dict__.get(
                DECORATOR_FIELD_NAME,
                self.global_mode,
            )

            if is_need_check and request.method in self.methods:
                original_token = await self.storage.get(request)

                is_valid = await self.policy.check(
                    request,
                    original_token,
                )

                if not is_valid:
                    raise self.error_renderer

            raise_response = False

            try:
                response = await handler(request)
            except web.HTTPException as exc:
                response = exc
                raise_response = True

            if isinstance(response, web.Response):
                await self.storage.save_token(request, response)

            if raise_response:
                raise response

            return response

        return middleware_handler
