from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi.testclient import TestClient

from neon.api.main import app

client = TestClient(app)


def _mock_ticker():
    calls = pd.DataFrame({
        "strike": [200.0, 210.0],
        "impliedVolatility": [0.45, 0.42],
    })
    chain = MagicMock()
    chain.calls = calls
    chain.puts = pd.DataFrame({"strike": [], "impliedVolatility": []})
    tk = MagicMock()
    tk.options = ["2026-06-20", "2026-09-19"]
    tk.option_chain.return_value = chain
    return tk


class TestGetSurface:
    def test_returns_200(self):
        with patch("neon.api.routers.surface.yf.Ticker", return_value=_mock_ticker()):
            resp = client.get("/stock/TSLA/surface")
        assert resp.status_code == 200

    def test_response_has_strikes_expiries_vols(self):
        with patch("neon.api.routers.surface.yf.Ticker", return_value=_mock_ticker()):
            data = client.get("/stock/TSLA/surface").json()
        assert set(data) == {"strikes", "expiries", "vols"}

    def test_vols_shape_matches_strikes_and_expiries(self):
        with patch("neon.api.routers.surface.yf.Ticker", return_value=_mock_ticker()):
            data = client.get("/stock/TSLA/surface").json()
        assert len(data["vols"]) == len(data["strikes"])
        assert all(len(row) == len(data["expiries"]) for row in data["vols"])

    def test_returns_404_when_no_options(self):
        tk = MagicMock()
        tk.options = []
        with patch("neon.api.routers.surface.yf.Ticker", return_value=tk):
            resp = client.get("/stock/TSLA/surface")
        assert resp.status_code == 404
