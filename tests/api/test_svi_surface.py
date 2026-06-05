from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi.testclient import TestClient

from neon.api.main import app

client = TestClient(app)

_EXPIRY = "2027-01-15"
_SPOT = 200.0


def _mock_ticker(expiries: list[str] | None = None, n_strikes: int = 6):
    strikes = [150.0 + 10.0 * i for i in range(n_strikes)]
    calls = pd.DataFrame({
        "strike": strikes,
        "impliedVolatility": [0.30 + 0.01 * i for i in range(n_strikes)],
    })
    chain = MagicMock()
    chain.calls = calls
    tk = MagicMock()
    tk.options = expiries if expiries is not None else [_EXPIRY]
    tk.option_chain.return_value = chain
    return tk


def _patch(ticker=None, spot=_SPOT):
    tk = ticker or _mock_ticker()
    return (
        patch("neon.api.routers.svi_surface.yf.Ticker", return_value=tk),
        patch("neon.api.routers.svi_surface._adapter.spot", return_value=spot),
    )


class TestGetSviSurface:
    def test_returns_200(self):
        p1, p2 = _patch()
        with p1, p2:
            resp = client.get("/stock/AAPL/svi-surface")
        assert resp.status_code == 200

    def test_response_shape(self):
        p1, p2 = _patch()
        with p1, p2:
            data = client.get("/stock/AAPL/svi-surface").json()
        assert set(data) == {"strikes", "expiries", "vols"}

    def test_vols_grid_dimensions(self):
        p1, p2 = _patch()
        with p1, p2:
            data = client.get("/stock/AAPL/svi-surface").json()
        n_strikes = len(data["strikes"])
        n_expiries = len(data["expiries"])
        assert len(data["vols"]) == n_strikes
        assert all(len(row) == n_expiries for row in data["vols"])

    def test_vols_are_positive(self):
        p1, p2 = _patch()
        with p1, p2:
            data = client.get("/stock/AAPL/svi-surface").json()
        assert all(v > 0 for row in data["vols"] for v in row)

    def test_multiple_expiries(self):
        expiries = ["2027-01-15", "2027-06-18"]
        tk = _mock_ticker(expiries=expiries)
        p1, p2 = _patch(ticker=tk)
        with p1, p2:
            data = client.get("/stock/AAPL/svi-surface").json()
        assert len(data["expiries"]) == 2

    def test_returns_404_when_no_options(self):
        tk = MagicMock()
        tk.options = []
        p1, p2 = _patch(ticker=tk)
        with p1, p2:
            resp = client.get("/stock/AAPL/svi-surface")
        assert resp.status_code == 404

    def test_returns_404_when_all_chains_too_thin(self):
        tk = _mock_ticker(n_strikes=2)  # < 3 valid strikes, calibration skipped
        p1, p2 = _patch(ticker=tk)
        with p1, p2:
            resp = client.get("/stock/AAPL/svi-surface")
        assert resp.status_code == 404
