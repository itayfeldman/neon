from unittest.mock import patch

from fastapi.testclient import TestClient

from neon.api.main import app

client = TestClient(app)

_ATM_CALL = {
    "ticker": "AAPL",
    "expiry": "2027-01-15",
    "strike": 200.0,
    "option_type": "call",
    "quantity": 1,
}

_ATM_PUT = {
    "ticker": "AAPL",
    "expiry": "2027-01-15",
    "strike": 200.0,
    "option_type": "put",
    "quantity": 1,
}


def _patch_adapter(spot=200.0):
    return (
        patch("neon.api.routers.portfolio._adapter.spot", return_value=spot),
        patch("neon.api.routers.portfolio._adapter.option_chain", return_value=[]),
    )


class TestPortfolioGreeks:
    def test_empty_positions_returns_zeros(self):
        resp = client.post("/portfolio/greeks", json={"positions": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0}

    def test_returns_200_with_valid_call(self):
        p1, p2 = _patch_adapter()
        with p1, p2:
            resp = client.post("/portfolio/greeks", json={"positions": [_ATM_CALL]})
        assert resp.status_code == 200

    def _post(self, positions):
        return client.post(
            "/portfolio/greeks", json={"positions": positions}
        ).json()

    def test_response_has_expected_fields(self):
        p1, p2 = _patch_adapter()
        with p1, p2:
            data = self._post([_ATM_CALL])
        assert set(data) == {"delta", "gamma", "vega", "theta"}

    def test_atm_call_delta_near_half(self):
        p1, p2 = _patch_adapter()
        with p1, p2:
            data = self._post([_ATM_CALL])
        assert 0.4 < data["delta"] < 0.7

    def test_atm_call_gamma_and_vega_positive(self):
        p1, p2 = _patch_adapter()
        with p1, p2:
            data = self._post([_ATM_CALL])
        assert data["gamma"] > 0
        assert data["vega"] > 0

    def test_atm_call_theta_negative(self):
        p1, p2 = _patch_adapter()
        with p1, p2:
            data = self._post([_ATM_CALL])
        assert data["theta"] < 0

    def test_negative_quantity_flips_greeks(self):
        short_call = {**_ATM_CALL, "quantity": -1}
        p1, p2 = _patch_adapter()
        with p1, p2:
            data = self._post([short_call])
        assert data["delta"] < 0
        assert data["gamma"] < 0

    def test_invalid_option_type_returns_422(self):
        bad = {**_ATM_CALL, "option_type": "forward"}
        p1, p2 = _patch_adapter()
        with p1, p2:
            resp = client.post("/portfolio/greeks", json={"positions": [bad]})
        assert resp.status_code == 422
