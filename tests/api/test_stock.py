from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from neon.api.main import app

client = TestClient(app)

_HISTORY_DF = pd.DataFrame({
    "date": pd.to_datetime(["2026-05-01", "2026-05-02"]),
    "open": [170.0, 172.0],
    "high": [175.0, 176.0],
    "low": [169.0, 171.0],
    "close": [173.0, 174.0],
    "volume": [1_000_000, 1_100_000],
})


class TestGetHistory:
    def test_returns_200_with_valid_ticker(self):
        with patch(
            "neon.api.routers.stock._adapter.fetch", return_value=_HISTORY_DF
        ):
            resp = client.get("/stock/TSLA/history")
        assert resp.status_code == 200

    def test_response_has_expected_fields(self):
        with patch(
            "neon.api.routers.stock._adapter.fetch", return_value=_HISTORY_DF
        ):
            data = client.get("/stock/TSLA/history").json()
        assert set(data) == {"dates", "opens", "highs", "lows", "closes", "volumes"}

    def test_dates_are_formatted_strings(self):
        with patch(
            "neon.api.routers.stock._adapter.fetch", return_value=_HISTORY_DF
        ):
            data = client.get("/stock/TSLA/history").json()
        assert data["dates"] == ["2026-05-01", "2026-05-02"]

    def test_returns_404_on_fetch_error(self):
        from neon.lib.data.base import DataFetchError
        with patch(
            "neon.api.routers.stock._adapter.fetch",
            side_effect=DataFetchError("not found"),
        ):
            resp = client.get("/stock/TSLA/history")
        assert resp.status_code == 404
