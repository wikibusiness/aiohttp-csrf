import abc

from .token_generator import AbstractTokenGenerator, SimpleTokenGenerator

try:
    from aiohttp_session import get_session
except ImportError:  # pragma: no cover
    pass


REQUEST_NEW_TOKEN_KEY = 'aiohttp_csrf_new_token'


class AbstractStorage(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def generate_new_token(self, request):
        pass  # pragma: no cover

    @abc.abstractmethod
    async def get(self, request):
        pass  # pragma: no cover

    @abc.abstractmethod
    async def save_token(self, request, response):
        pass  # pragma: no cover


class BaseStorage(AbstractStorage, metaclass=abc.ABCMeta):

    def __init__(self, token_generator=None):
        if token_generator is None:
            token_generator = SimpleTokenGenerator()
        elif not isinstance(token_generator, AbstractTokenGenerator):
            raise TypeError(
                'Token generator must be instance of AbstractTokenGenerator',
            )

        self.token_generator = token_generator

    def _generate_token(self):
        return self.token_generator.generate()

    async def generate_new_token(self, request):
        if REQUEST_NEW_TOKEN_KEY in request:
            return request[REQUEST_NEW_TOKEN_KEY]

        token = self._generate_token()

        request[REQUEST_NEW_TOKEN_KEY] = token

        return token

    @abc.abstractmethod
    async def _get(self, request):
        pass  # pragma: no cover

    async def get(self, request):
        token = await self._get(request)

        await self.generate_new_token(request)

        return token

    @abc.abstractmethod
    async def _save_token(self, request, response, token):
        pass  # pragma: no cover

    async def save_token(self, request, response):
        old_token = await self._get(request)

        if REQUEST_NEW_TOKEN_KEY in request:
            token = request[REQUEST_NEW_TOKEN_KEY]
        elif old_token is None:
            token = await self.generate_new_token(request)
        else:
            token = None

        if token is not None:
            await self._save_token(request, response, token)


class CookieStorage(BaseStorage):

    def __init__(self, cookie_name, cookie_kwargs=None, *args, **kwargs):
        self.cookie_name = cookie_name
        self.cookie_kwargs = cookie_kwargs or {}

        super().__init__(*args, **kwargs)

    async def _get(self, request):
        return request.cookies.get(self.cookie_name, None)

    async def _save_token(self, request, response, token):
        response.set_cookie(
            self.cookie_name,
            token,
            **self.cookie_kwargs,
        )


class SessionStorage(BaseStorage):
    def __init__(self, session_name, *args, **kwargs):
        self.session_name = session_name

        super().__init__(*args, **kwargs)

    async def _get(self, request):
        session = await get_session(request)

        return session.get(self.session_name, None)

    async def _save_token(self, request, response, token):
        session = await get_session(request)

        session[self.session_name] = token
