from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi.testclient import TestClient

from neon.api.main import app

client = TestClient(app)

_CALLS = pd.DataFrame({
    "strike": [200.0, 210.0],
    "impliedVolatility": [0.45, 0.42],
    "bid": [5.0, 3.0],
    "ask": [5.5, 3.5],
    "volume": [100, 200],
})
_PUTS = pd.DataFrame({
    "strike": [190.0, 200.0],
    "impliedVolatility": [0.48, 0.46],
    "bid": [4.0, 6.0],
    "ask": [4.5, 6.5],
    "volume": [150, 250],
})


def _mock_chain():
    chain = MagicMock()
    chain.calls = _CALLS
    chain.puts = _PUTS
    return chain


class TestGetOptions:
    def test_returns_200(self):
        with patch("neon.api.routers.options.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.option_chain.return_value = _mock_chain()
            resp = client.get("/stock/TSLA/options/2026-06-20")
        assert resp.status_code == 200

    def test_response_has_calls_and_puts(self):
        with patch("neon.api.routers.options.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.option_chain.return_value = _mock_chain()
            data = client.get("/stock/TSLA/options/2026-06-20").json()
        assert "calls" in data and "puts" in data

    def test_calls_have_correct_option_type(self):
        with patch("neon.api.routers.options.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.option_chain.return_value = _mock_chain()
            data = client.get("/stock/TSLA/options/2026-06-20").json()
        assert all(r["option_type"] == "call" for r in data["calls"])
        assert all(r["option_type"] == "put" for r in data["puts"])

    def test_returns_404_on_error(self):
        with patch(
            "neon.api.routers.options.yf.Ticker",
            side_effect=Exception("bad ticker"),
        ):
            resp = client.get("/stock/TSLA/options/2026-06-20")
        assert resp.status_code == 404
