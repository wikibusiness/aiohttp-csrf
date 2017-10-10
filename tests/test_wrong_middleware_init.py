import aiohttp
import aiohttp_csrf
import pytest


async def test_get_token_not_init_middleware():
    req = aiohttp.test_utils.make_mocked_request('GET', '/')

    with pytest.raises(RuntimeError):
        await aiohttp_csrf.get_token(req)


async def test_generate_token_not_init_middleware():
    req = aiohttp.test_utils.make_mocked_request('GET', '/')

    with pytest.raises(RuntimeError):
        await aiohttp_csrf.generate_token(req)


async def test_middleware_with_wrong_storage():
    class FakeStorage:
        pass

    fake_csrf_storage = FakeStorage()

    csrf_policy = aiohttp_csrf.policy.HeaderPolicy('X-CSRF-TOKEN')

    with pytest.raises(TypeError):
        aiohttp_csrf.CsrfMiddleware(
            policy=csrf_policy,
            storage=fake_csrf_storage,
        )


async def test_middleware_with_wrong_policy():
    class FakePolicy:
        pass

    csrf_storage = aiohttp_csrf.storage.CookieStorage('csrf_token')

    fake_csrf_policy = FakePolicy()

    with pytest.raises(TypeError):
        aiohttp_csrf.CsrfMiddleware(
            policy=fake_csrf_policy,
            storage=csrf_storage,
        )
