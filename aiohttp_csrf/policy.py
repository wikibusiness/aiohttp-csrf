import abc
from secrets import compare_digest


class AbstractPolicy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def check(self, request, original_value):
        pass  # pragma: no cover


class FormPolicy(AbstractPolicy):

    def __init__(self, field_name):
        self.field_name = field_name

    async def check(self, request, original_value):
        get = request.match_info.get(self.field_name, None)
        post_req = await request.post() if get is None else None
        post = post_req.get(self.field_name) if post_req is not None else None
        post = post if post is not None else ''
        token = get if get is not None else post

        return compare_digest(token, original_value)


class HeaderPolicy(AbstractPolicy):

    def __init__(self, header_name):
        self.header_name = header_name

    async def check(self, request, original_value):
        token = request.headers.get(self.header_name)

        return compare_digest(token, original_value)


class FormAndHeaderPolicy(HeaderPolicy, FormPolicy):

    def __init__(self, header_name, field_name):
        self.header_name = header_name
        self.field_name = field_name

    async def check(self, request, original_value):
        header_check = await HeaderPolicy.check(
            self,
            request,
            original_value,
        )

        if header_check:
            return True

        form_check = await FormPolicy.check(self, request, original_value)

        if form_check:
            return True

        return False
