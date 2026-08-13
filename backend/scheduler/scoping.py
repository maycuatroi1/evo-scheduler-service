from scheduler.middleware import get_current_tenant


def tenant_scope_kwargs(model_cls):
    field = "tenant_id" if hasattr(model_cls, "tenant_id") else "tenant"
    return {field: get_current_tenant()}


def scoped_queryset(model_cls):
    tenant_id = get_current_tenant()
    if tenant_id is None:
        return model_cls.objects.none()
    return model_cls.objects.filter(tenant_id=tenant_id)
