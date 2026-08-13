"""
NinjaAPI instance and project-level endpoints.
"""

from ninja import NinjaAPI

api = NinjaAPI(title="evo-scheduler-service API", version="1.0.0")


@api.get("/health")
def health(request):
    return {"status": "ok"}
