from unittest.mock import patch

from fastapi.testclient import TestClient

from neon.api.main import app
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.instruments.options.option_type import OptionType

client = TestClient(app)

_INPUTS = [
    OptionInputs(
        underlying_ticker="TSLA",
        underlying_price=200.0,
        strike_price=200.0,
        volatility=0.45,
        risk_free_rate=0.05,
        current_date="20260604",
        expiry_date="20261204",
        option_type=OptionType.Call,
    ),
    OptionInputs(
        underlying_ticker="TSLA",
        underlying_price=200.0,
        strike_price=190.0,
        volatility=0.48,
        risk_free_rate=0.05,
        current_date="20260604",
        expiry_date="20261204",
        option_type=OptionType.Put,
    ),
]


class TestGetGreeks:
    def test_returns_200(self):
        with patch(
            "neon.api.routers.greeks._adapter.option_chain", return_value=_INPUTS
        ):
            resp = client.get("/stock/TSLA/greeks/2026-12-04")
        assert resp.status_code == 200

    def test_response_has_rows(self):
        with patch(
            "neon.api.routers.greeks._adapter.option_chain", return_value=_INPUTS
        ):
            data = client.get("/stock/TSLA/greeks/2026-12-04").json()
        assert "rows" in data
        assert len(data["rows"]) == 2

    def test_rows_have_greek_fields(self):
        with patch(
            "neon.api.routers.greeks._adapter.option_chain", return_value=_INPUTS
        ):
            data = client.get("/stock/TSLA/greeks/2026-12-04").json()
        row = data["rows"][0]
        assert set(row) == {"strike", "option_type", "delta", "gamma", "vega", "theta"}

    def test_returns_404_on_error(self):
        with patch(
            "neon.api.routers.greeks._adapter.option_chain",
            side_effect=Exception("bad ticker"),
        ):
            resp = client.get("/stock/TSLA/greeks/2026-12-04")
        assert resp.status_code == 404
