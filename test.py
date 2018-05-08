import asyncio

from aiohttp import web

async def hello(request):
    return web.Response(text="Hello, world")


def dec(handler):
    def wrapped(*args, **kwargs):
        request = args[-1]
        import ipdb;ipdb.set_trace()
        return handler(*args, **kwargs)

    return wrapped


class MyView(web.View):
    @dec
    async def get(self):
        return web.Response(text="Get Hello, world")

    async def post(self):
        return web.Response(text="Post Hello, world")


@web.middleware
async def middleware(request, handler):
    return await handler(request)


app = web.Application(middlewares=[middleware])
app.router.add_route('*', '/', MyView)

web.run_app(app)
