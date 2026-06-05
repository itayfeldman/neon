from fastapi.testclient import TestClient

from neon.api.main import app

client = TestClient(app)

_VALID = {
    "face_value": 1000.0,
    "coupon_rate": 0.05,
    "coupon_freq": 2,
    "issue_date": "20200101",
    "maturity_date": "20300101",
    "ytm": 0.045,
}


class TestPriceBond:
    def test_returns_200(self):
        assert client.post("/bonds/price", json=_VALID).status_code == 200

    def test_response_has_expected_fields(self):
        data = client.post("/bonds/price", json=_VALID).json()
        assert set(data) == {
            "dirty_price", "clean_price", "accrued_interest",
            "modified_duration", "macaulay_duration", "dv01", "convexity",
        }

    def test_premium_bond_prices_above_par(self):
        # coupon > ytm → price above face
        data = client.post("/bonds/price", json=_VALID).json()
        assert data["dirty_price"] > _VALID["face_value"]

    def test_discount_bond_prices_below_par(self):
        payload = {**_VALID, "ytm": 0.08}
        data = client.post("/bonds/price", json=payload).json()
        assert data["dirty_price"] < _VALID["face_value"]

    def test_dv01_is_nonzero(self):
        data = client.post("/bonds/price", json=_VALID).json()
        assert data["dv01"] != 0.0

    def test_all_outputs_are_finite(self):
        data = client.post("/bonds/price", json=_VALID).json()
        import math
        assert all(math.isfinite(v) for v in data.values())

    def test_invalid_coupon_rate_returns_422(self):
        payload = {**_VALID, "coupon_rate": 1.5}
        assert client.post("/bonds/price", json=payload).status_code == 422

    def test_invalid_ytm_returns_422(self):
        payload = {**_VALID, "ytm": -0.01}
        assert client.post("/bonds/price", json=payload).status_code == 422
