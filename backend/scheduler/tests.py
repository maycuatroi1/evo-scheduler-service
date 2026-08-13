import datetime as dt

import jwt
from django.test import TestCase, override_settings
from ninja.testing import TestClient

from scheduler.models import Teacher, Tenant


SIGNING_KEY = "dev-insecure-signing-key-change-me"


def mint_token(tenant_id, deployment_id="dep-1", issuer="", audience=""):
    payload = {
        "user_id": "u-1",
        "email": "ops@example.com",
        "tenant_id": tenant_id,
        "deployment_id": deployment_id,
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        "iat": dt.datetime.now(dt.timezone.utc),
        "sub": "u-1",
    }
    if issuer:
        payload["iss"] = issuer
    if audience:
        payload["aud"] = audience
    kwargs = {"algorithm": "HS256"}
    return jwt.encode(payload, SIGNING_KEY, **kwargs)


class HealthEndpointTests(TestCase):
    def test_health_no_auth(self):
        client = TestClient(__import__("config.api", fromlist=["api"]).api)
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})


class JWTAuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant_a = Tenant.objects.create(name="Tenant A", code="TA")
        cls.tenant_b = Tenant.objects.create(name="Tenant B", code="TB")
        cls.teacher_a = Teacher.objects.create(
            tenant=cls.tenant_a, code="T-A1", name="Alice"
        )
        cls.teacher_b = Teacher.objects.create(
            tenant=cls.tenant_b, code="T-B1", name="Bob"
        )

    def setUp(self):
        from config.api import api

        self.client = TestClient(api)

    def _bearer(self, tenant_id):
        return {"Authorization": f"Bearer {mint_token(tenant_id)}"}

    def test_me_with_valid_token_tenant_a_returns_200(self):
        resp = self.client.get("/me", headers=self._bearer(self.tenant_a.id))
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["tenant_id"], self.tenant_a.id)
        self.assertEqual(body["tenant_code"], "TA")
        self.assertEqual(body["tenant_name"], "Tenant A")
        self.assertEqual(body["deployment_id"], "dep-1")

    def test_me_with_unknown_tenant_returns_403(self):
        unknown_id = self.tenant_b.id + 9_999
        resp = self.client.get("/me", headers=self._bearer(unknown_id))
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_me_without_token_returns_401(self):
        resp = self.client.get("/me")
        self.assertEqual(resp.status_code, 401, resp.content)

    def test_me_with_bad_signature_returns_401(self):
        payload = {
            "tenant_id": self.tenant_a.id,
            "deployment_id": "dep-1",
            "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        }
        bad = jwt.encode(payload, "wrong-key", algorithm="HS256")
        resp = self.client.get("/me", headers={"Authorization": f"Bearer {bad}"})
        self.assertEqual(resp.status_code, 401, resp.content)

    def test_teachers_scoped_to_tenant_a_excludes_tenant_b(self):
        resp = self.client.get("/teachers", headers=self._bearer(self.tenant_a.id))
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        codes = [row["code"] for row in body]
        self.assertIn("T-A1", codes)
        self.assertNotIn("T-B1", codes)

    def test_teachers_scoped_to_tenant_b_excludes_tenant_a(self):
        resp = self.client.get("/teachers", headers=self._bearer(self.tenant_b.id))
        self.assertEqual(resp.status_code, 200, resp.content)
        codes = [row["code"] for row in resp.json()]
        self.assertIn("T-B1", codes)
        self.assertNotIn("T-A1", codes)

    def test_token_without_tenant_claim_returns_401(self):
        payload = {
            "deployment_id": "dep-1",
            "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        }
        tok = jwt.encode(payload, SIGNING_KEY, algorithm="HS256")
        resp = self.client.get("/me", headers={"Authorization": f"Bearer {tok}"})
        self.assertEqual(resp.status_code, 401, resp.content)


@override_settings(JWT_ISSUER="auth.evo.local", JWT_AUDIENCE="scheduler.evo.local")
class JWTIssuerAudienceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant_a = Tenant.objects.create(name="Tenant A", code="TA")

    def setUp(self):
        from config.api import api

        self.client = TestClient(api)

    def test_me_rejects_token_with_wrong_issuer(self):
        payload = {
            "tenant_id": self.tenant_a.id,
            "deployment_id": "dep-1",
            "iss": "someone-else",
            "aud": "scheduler.evo.local",
            "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        }
        tok = jwt.encode(payload, SIGNING_KEY, algorithm="HS256")
        resp = self.client.get("/me", headers={"Authorization": f"Bearer {tok}"})
        self.assertEqual(resp.status_code, 401, resp.content)

    def test_me_accepts_token_with_correct_iss_aud(self):
        payload = {
            "tenant_id": self.tenant_a.id,
            "deployment_id": "dep-1",
            "iss": "auth.evo.local",
            "aud": "scheduler.evo.local",
            "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        }
        tok = jwt.encode(payload, SIGNING_KEY, algorithm="HS256")
        resp = self.client.get("/me", headers={"Authorization": f"Bearer {tok}"})
        self.assertEqual(resp.status_code, 200, resp.content)
