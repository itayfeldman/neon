import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import pandas as pd

from neon.lib.core.constants import DATE_FORMAT
from neon.lib.data import cache
from neon.lib.data.base import DataAdapter, DataFetchError
from neon.lib.fixed_income.discount_curve import DiscountCurve

_PROVIDER = "treasury"
_TTL = 7 * 24 * 3600  # 7 days
_FEED_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month={month}"
)
# Par yield tenors published by the Treasury, in years
_TENORS = {
    "BC_1MONTH": 1 / 12,
    "BC_2MONTH": 2 / 12,
    "BC_3MONTH": 3 / 12,
    "BC_6MONTH": 6 / 12,
    "BC_1YEAR": 1.0,
    "BC_2YEAR": 2.0,
    "BC_3YEAR": 3.0,
    "BC_5YEAR": 5.0,
    "BC_7YEAR": 7.0,
    "BC_10YEAR": 10.0,
    "BC_20YEAR": 20.0,
    "BC_30YEAR": 30.0,
}


class USTreasuryAdapter(DataAdapter):
    def fetch(self, date: str, *, use_cache: bool = True) -> pd.DataFrame:
        """
        Fetch the daily par yield curve for the month containing `date`.
        Returns a DataFrame with columns: date, tenor_years, par_yield.
        """
        dt = datetime.strptime(date, DATE_FORMAT)
        month = dt.strftime("%Y%m")
        params = {"month": month}

        if use_cache:
            cached = cache.load(_PROVIDER, params, _TTL)
            if cached is not None:
                return cached

        try:
            url = _FEED_URL.format(month=month)
            with urllib.request.urlopen(url, timeout=10) as resp:
                xml_bytes = resp.read()
        except Exception as exc:
            raise DataFetchError(f"Treasury fetch failed for {month}: {exc}") from exc

        df = _parse_xml(xml_bytes)

        if use_cache:
            cache.save(_PROVIDER, params, df)

        return df

    def to_domain(self, df: pd.DataFrame, date: str) -> DiscountCurve:
        """
        Build a DiscountCurve from the par yield row closest to `date`.
        Par yields approximate zero rates (acceptable for bootstrapping seed).
        """
        dt = datetime.strptime(date, DATE_FORMAT)
        row = df.iloc[(df["date"] - dt).abs().argsort()[:1]].iloc[0]
        value_date = row["date"].strftime(DATE_FORMAT)
        value_dt = datetime.strptime(value_date, DATE_FORMAT)

        dates = []
        zero_rates = []
        for tenor_col in _TENORS:
            if tenor_col not in row or pd.isna(row[tenor_col]):
                continue
            tenor_years = _TENORS[tenor_col]
            maturity_dt = value_dt + timedelta(days=int(tenor_years * 365))
            dates.append(maturity_dt.strftime(DATE_FORMAT))
            zero_rates.append(row[tenor_col] / 100.0)

        return DiscountCurve(value_date=value_date, dates=dates, zero_rates=zero_rates)


def _parse_xml(xml_bytes: bytes) -> pd.DataFrame:
    ns = {
        "ns": "http://www.w3.org/2005/Atom",
        "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
        "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
    }
    root = ET.fromstring(xml_bytes)
    rows = []
    for entry in root.findall("ns:entry", ns):
        content = entry.find("ns:content", ns)
        if content is None:
            continue
        props = content.find("m:properties", ns)
        if props is None:
            continue
        date_el = props.find("d:NEW_DATE", ns)
        if date_el is None or not date_el.text:
            continue
        date = datetime.fromisoformat(date_el.text[:10])
        row = {"date": date}
        for key in _TENORS:
            el = props.find(f"d:{key}", ns)
            if el is not None and el.text:
                row[key] = float(el.text)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
