import json

import pandas as pd
import pytest

TREASURY_XML = b"""<?xml version="1.0" encoding="utf-8" standalone="yes" ?>
<feed xml:base="https://home.treasury.gov"
  xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
  xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
  xmlns="http://www.w3.org/2005/Atom">
<entry>
<content type="application/xml">
<m:properties>
<d:NEW_DATE m:type="Edm.DateTime">2026-05-01T00:00:00</d:NEW_DATE>
<d:BC_1MONTH m:type="Edm.Double">3.71</d:BC_1MONTH>
<d:BC_2MONTH m:type="Edm.Double">3.70</d:BC_2MONTH>
<d:BC_3MONTH m:type="Edm.Double">3.68</d:BC_3MONTH>
<d:BC_6MONTH m:type="Edm.Double">3.71</d:BC_6MONTH>
<d:BC_1YEAR m:type="Edm.Double">3.73</d:BC_1YEAR>
<d:BC_2YEAR m:type="Edm.Double">3.88</d:BC_2YEAR>
<d:BC_3YEAR m:type="Edm.Double">3.91</d:BC_3YEAR>
<d:BC_5YEAR m:type="Edm.Double">4.02</d:BC_5YEAR>
<d:BC_7YEAR m:type="Edm.Double">4.20</d:BC_7YEAR>
<d:BC_10YEAR m:type="Edm.Double">4.39</d:BC_10YEAR>
<d:BC_20YEAR m:type="Edm.Double">4.96</d:BC_20YEAR>
<d:BC_30YEAR m:type="Edm.Double">4.97</d:BC_30YEAR>
</m:properties>
</content>
</entry>
</feed>"""

FRED_SERIES_JSON = b"""{
  "observations": [
    {"date": "2026-05-01", "value": "3.71"},
    {"date": "2026-05-02", "value": "3.72"},
    {"date": "2026-05-05", "value": "3.70"}
  ]
}"""

ALPHA_VANTAGE_DAILY_JSON = b"""{
  "Time Series (Daily)": {
    "2026-05-05": {
      "1. open": "180.0", "2. high": "182.0", "3. low": "179.0",
      "4. close": "181.5", "5. volume": "1000000"
    },
    "2026-05-06": {
      "1. open": "181.5", "2. high": "183.0", "3. low": "180.5",
      "4. close": "182.0", "5. volume": "1100000"
    }
  }
}"""

ALPHA_VANTAGE_FX_JSON = b"""{
  "Realtime Currency Exchange Rate": {
    "1. From_Currency Code": "USD",
    "3. To_Currency Code": "EUR",
    "5. Exchange Rate": "0.9250"
  }
}"""


@pytest.fixture
def treasury_df():
    from neon.lib.data.treasury import _parse_xml
    return _parse_xml(TREASURY_XML)


@pytest.fixture
def fred_series_df():
    data = json.loads(FRED_SERIES_JSON)
    df = pd.DataFrame(data["observations"])[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"])
    return df


@pytest.fixture
def alpha_vantage_df():
    ts = json.loads(ALPHA_VANTAGE_DAILY_JSON)["Time Series (Daily)"]
    rows = [
        {
            "date": pd.Timestamp(date),
            "open": float(v["1. open"]),
            "high": float(v["2. high"]),
            "low": float(v["3. low"]),
            "close": float(v["4. close"]),
            "volume": int(v["5. volume"]),
        }
        for date, v in ts.items()
    ]
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
