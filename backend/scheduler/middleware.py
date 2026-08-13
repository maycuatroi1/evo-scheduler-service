import threading

_current = threading.local()


def set_current_tenant(tenant_id):
    _current.tenant_id = tenant_id


def get_current_tenant():
    return getattr(_current, "tenant_id", None)


def clear_current_tenant():
    if hasattr(_current, "tenant_id"):
        del _current.tenant_id


class TenantScopeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        clear_current_tenant()
        response = self.get_response(request)
        clear_current_tenant()
        return response
