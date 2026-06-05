# SPEC: neon — Derivatives Analytics Suite (Phase 2)

## 1. Objective

**neon** is a personal quantitative finance library for options pricing, risk (Greeks), and volatility analytics. The target user is a single quant developer using it for research, backtesting, and hedging analysis.

**Phase 2 delivers four capabilities:**

| # | Capability | Status today |
|---|---|---|
| 1 | Fix `EuropeanOption` wiring bug | `xfail` LSP test |
| 2 | `AnalyticalGreeks` vanna & volga | returns `0.0` from base |
| 3 | `AmericanOption` — CRR binomial tree | `NotImplementedError` |
| 4 | `VolatilitySurface` — bilinear interpolation | empty placeholder dir |

**Success looks like:** Given a portfolio of European and American options, compute prices and a full set of Greeks (δ, γ, ν, θ, ρ, vanna, volga), and look up interpolated implied vol for any (strike, expiry) pair.

---

## 2. Tech Stack

| Tool | Version |
|---|---|
| Python | ≥ 3.13 |
| numpy | (transitive via scipy) |
| scipy | ≥ 1.17.1 — `scipy.stats.norm`, `scipy.interpolate.RegularGridInterpolator` |
| pydantic | ≥ 2.12.5 — `OptionInputs` validation |
| pytest | ≥ 8.0 |
| ruff | ≥ 0.4 |
| uv | package manager |

No new dependencies are permitted.

---

## 3. Commands

```bash
uv sync --group dev          # install all dependencies incl. dev
uv run pytest                # run all tests
uv run pytest tests/path/to/test_foo.py::TestClass::test_bar  # single test
uv run ruff check .          # lint
uv run ruff format .         # format
uv run neon                  # CLI entry point
```

---

## 4. Project Structure

```
src/neon/lib/
├── core/                   # enums, constants (no changes)
├── datetime/               # DayCount, time_to_maturity (no changes)
├── greeks/
│   ├── greeks.py           # base class (no changes)
│   ├── analytical_greeks.py  ← ADD vanna(), volga()
│   └── numerical_greeks.py   (no changes)
├── instruments/
│   ├── instrument.py       # ABC (no changes)
│   ├── options/
│   │   ├── base.py         ← FIX serialize_option_inputs format bug
│   │   ├── european.py     (no changes after fix)
│   │   ├── american.py     ← IMPLEMENT CRR binomial tree
│   │   ├── option_inputs.py  (no changes)
│   │   └── option_type.py  (no changes)
│   └── surface/
│       ├── __init__.py     ← CREATE
│       └── vol_surface.py  ← CREATE VolatilitySurface

tests/lib/
├── greeks/
│   ├── test_european_option_analytical_greeks.py  ← ADD vanna/volga tests
│   └── test_european_option_numerical_greeks.py   (TestLSP xfail → passing)
├── instruments/
│   └── options/
│       ├── test_base_option.py   ← ADD fix regression test
│       └── test_american_option.py  ← CREATE
└── surface/
    └── test_vol_surface.py  ← CREATE
```

---

## 5. Code Style

Match existing patterns exactly. Key conventions:

```python
# Greeks: attributes are injected externally, not passed to __init__
ag = AnalyticalGreeks()
ag.underlying_price = 100.0
ag.strike_price = 100.0
ag.volatility = 0.2
ag.risk_free_rate = 0.05
ag.time_to_maturity = 1.0
ag.option_type = OptionType.Call   # int ±1

# All Greek methods return float
def vanna(self) -> float:
    return float(norm.pdf(self.d1) / (self.underlying_price * self._a_) * (1 - self.d1 / self._a_))

# Option subclasses delegate to injected Greeks
class AmericanOption(BaseOption):
    def __init__(self, inputs: OptionInputs, greeks: Greeks = Greeks()):
        super().__init__(inputs, greeks)

    def price(self) -> float:
        return self.greeks.price()
```

- `OptionType` and `PositionDirection` are `IntEnum` ±1 — multiply directly into formulas.
- `DATE_FORMAT = "%Y%m%d"` — all dates are compact strings (e.g. `"20260408"`).
- No comments on self-explanatory code; comment only non-obvious domain invariants.
- `float()` wrap on all numpy scalar returns (matches `AnalyticalGreeks` pattern).

---

## 6. Feature Specs

### 6.1 Fix `EuropeanOption` wiring bug

**Bug:** `base.py:11` — `serialize_option_inputs` uses `str(option_inputs.strike_price):0f` which raises `ValueError` at runtime.

**Fix:** Replace with `f"{option_inputs.strike_price:.0f}"`.

**Acceptance:** `TestLSP.test_european_option_works_with_numerical_greeks` changes from `xfail` to a passing test. Remove the `@pytest.mark.xfail` decorator.

---

### 6.2 `AnalyticalGreeks` vanna & volga

**Closed-form formulas** (standard Black-Scholes):

```
vanna  = ∂²P/∂S∂σ = -norm.pdf(d1) * d2 / σ
volga  = ∂²P/∂σ²  =  underlying_price * norm.pdf(d1) * sqrt(T) * d1 * d2 / σ
```

**Acceptance:**
- Both return `float`.
- For ATM call (S=K=100, σ=0.2, r=0.05, T=1): vanna ≈ −0.37, volga ≈ 18.5 (within `abs=0.01` of those known values).
- `NumericalGreeks` vanna/volga agree with analytical within `abs=0.01`.

---

### 6.3 `AmericanOption` — CRR binomial tree

**Design:**
- `AmericanOption` follows the same constructor pattern as `EuropeanOption`: accepts `OptionInputs` and an injected `Greeks`.
- A private `_crr_price()` method on the class implements the tree directly — it does **not** live in `greeks/`.
- `price()` calls `_crr_price()`.
- Greek methods delegate to `self.greeks` (same pattern as `EuropeanOption`).

**CRR parameters** (derived from `OptionInputs`):
- Steps `n`: use `TimeSteps.Daily.value` (252) as default, or accept as constructor param.
- `dt = T / n`, `u = exp(σ√dt)`, `d = 1/u`, `p = (exp(r·dt) − d) / (u − d)`.
- Terminal payoffs: `max(φ·(S·uʲ·d^(n−j) − K), 0)` for j = 0…n, φ = OptionType (±1).
- Backward induction with early exercise: `max(continuation, intrinsic)`.

**Acceptance:**
- Deep ITM American call price ≥ equivalent European call price.
- ATM American put price > ATM European put price (early exercise premium).
- Price is always ≥ 0.
- `price()` returns `float`.
- `EuropeanOption` and `AmericanOption` are substitutable wherever `BaseOption` is expected (LSP).

---

### 6.4 `VolatilitySurface`

**Location:** `src/neon/lib/instruments/surface/vol_surface.py`

**Interface:**

```python
class VolatilitySurface:
    def __init__(
        self,
        strikes: list[float],          # sorted ascending
        expiries: list[str],           # DATE_FORMAT strings, sorted ascending
        vols: list[list[float]],       # shape [len(strikes)][len(expiries)]
    ) -> None: ...

    def get_vol(self, strike: float, expiry: str) -> float:
        """Bilinear interpolation; clamps to boundary for out-of-range inputs."""
        ...
```

**Implementation notes:**
- Convert `expiry` strings to days-to-expiry (float) internally for interpolation.
- Use `scipy.interpolate.RegularGridInterpolator(method="linear", bounds_error=False, fill_value=None)` — `fill_value=None` clamps to nearest boundary rather than returning NaN.
- `vols` is indexed `[strike_idx][expiry_idx]` to match `RegularGridInterpolator` convention.

**Acceptance:**
- Exact lookup on a grid point returns the stored vol (within `abs=1e-10`).
- Interpolated value between two strikes is strictly between the two boundary vols.
- Out-of-range strike/expiry clamps to the nearest boundary (no NaN, no exception).
- `get_vol` returns `float`.

---

## 7. Testing Strategy

- **Framework:** pytest.
- **Test location:** mirrors `src/neon/lib/` under `tests/lib/`.
- **Tolerance:** `abs=0.01` for numerical vs. analytical Greeks agreement; `abs=1e-10` for exact lookups.
- **Pattern:** test classes per concern (`TestPrice`, `TestDelta`, etc.) with `@pytest.mark.parametrize` for call/put/ITM/ATM/OTM variants.
- **No mocks** — all tests use real implementations; `AnalyticalGreeks` serves as the reference pricer for `NumericalGreeks` tests.
- **Coverage:** every public method on each new/modified class must have at least one test.

---

## 8. Boundaries

| Category | Rule |
|---|---|
| **Always** | Maintain `instruments → greeks → datetime → core` dependency flow |
| **Always** | Return `float` (not `np.float64`) from all Greek and pricing methods |
| **Always** | Follow attribute-injection pattern for Greeks market data |
| **Always** | Run `uv run pytest` and `uv run ruff check .` before considering a task done |
| **Ask first** | Adding any new dependency to `pyproject.toml` |
| **Ask first** | Changing `OptionInputs` fields (breaks all callers) |
| **Ask first** | Modifying `Greeks` base class signatures |
| **Never** | Modify `greeks.py`, `numerical_greeks.py`, or any file not listed in §4 |
| **Never** | Hard-code a pricing model inside a `Greeks` subclass |
| **Never** | Add upward imports (e.g. `greeks` importing from `instruments`) |
| **Never** | Leave a `NotImplementedError` stub in a method that has a spec |

---

## 9. Open Questions

None — all design decisions resolved above.

---

## 10. Implementation Order

Tasks must be executed in this order (each unblocks the next):

1. **Fix `base.py` format bug** — unblocks LSP tests and clean `EuropeanOption` usage.
2. **`AnalyticalGreeks` vanna/volga** — small, self-contained; establishes reference values for `NumericalGreeks` tests.
3. **`AmericanOption` CRR tree** — depends on `BaseOption` being clean (step 1).
4. **`VolatilitySurface`** — fully independent; can be done in parallel with steps 2–3.

---

# SPEC: Data Adapters — Phase 3

## 1. Objective

Add a `data` module to `neon` that fetches market and macro data from public providers and maps it to existing domain types. The adapters serve two use cases: interactive exploration in notebooks and programmatic use in pricing/risk workflows.

Target user: the same quant developer using the rest of the library, primarily in Jupyter notebooks.

---

## 2. Providers in scope

| Provider | Data | Auth |
|---|---|---|
| Yahoo Finance | Equities OHLCV, options chains | None (`yfinance`) |
| FRED | Interest rates, macro series, yield curve | API key (`fredapi`) |
| US Treasury | Daily par yield curve | None (public XML feed) |
| Alpha Vantage | Equities, FX, crypto, technicals | API key |

---

## 3. Commands

```bash
uv add yfinance fredapi                    # add provider dependencies
uv sync --group dev                        # install all deps incl. dev
uv run pytest tests/data/                  # run adapter tests
uv run pytest -m integration               # run live network tests (skipped by default)
```

API keys are read from environment variables:
```bash
export FRED_API_KEY="..."
export ALPHA_VANTAGE_API_KEY="..."
```

---

## 4. Project structure

```
src/neon/lib/data/
    __init__.py
    base.py              # DataAdapter ABC + DataFetchError
    cache.py             # file-based cache (~/.neon/cache/), configurable TTL
    yahoo.py             # YahooFinanceAdapter
    fred.py              # FREDAdapter
    treasury.py          # USTreasuryAdapter
    alpha_vantage.py     # AlphaVantageAdapter

tests/data/
    conftest.py          # canned provider response fixtures
    test_yahoo.py
    test_fred.py
    test_treasury.py
    test_alpha_vantage.py
```

---

## 5. Core design

### `DataAdapter` ABC (`base.py`)

```python
class DataAdapter(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> pd.DataFrame:
        """Return raw provider data as a DataFrame."""

    @abstractmethod
    def to_domain(self, df: pd.DataFrame):
        """Map a raw DataFrame to a domain object."""
```

Each adapter exposes both surfaces. Callers use `fetch()` for raw data or `to_domain(fetch(...))` for domain objects.

`DataFetchError` wraps all provider-level network and parse failures.

### Cache (`cache.py`)

- Cache directory: `~/.neon/cache/<provider>/<key>.parquet`
- Default TTL: 1 day for market data, 7 days for macro/curve data
- Cache key: deterministic hash of the request parameters
- Bypass: `adapter.fetch(..., cache=False)`

### Domain mappings

| Adapter method | Domain type |
|---|---|
| `YahooFinanceAdapter.spot(ticker)` | `float` |
| `YahooFinanceAdapter.history(ticker)` | `pd.DataFrame` |
| `YahooFinanceAdapter.option_chain(ticker, expiry)` | `list[OptionInputs]` |
| `FREDAdapter.series(series_id)` | `pd.DataFrame` |
| `FREDAdapter.yield_curve(date)` | `DiscountCurve` |
| `USTreasuryAdapter.yield_curve(date)` | `DiscountCurve` |
| `AlphaVantageAdapter.daily(symbol)` | `pd.DataFrame` |
| `AlphaVantageAdapter.fx_rate(from_, to)` | `float` |

---

## 6. Code style

- Match existing conventions: dataclasses and Pydantic models for value types, no mutable global state.
- API keys injected via constructor or environment variable — never hardcoded.
- Raise `ValueError` for missing API keys at construction time.
- Raise `DataFetchError` (wrapping the original exception) for all network and parse failures.
- No retries or backoff in scope — keep adapters thin.

---

## 7. Testing strategy

- Unit tests mock all HTTP calls — no live network in CI.
- Fixtures in `conftest.py` provide canned provider responses saved from real calls.
- One integration test per adapter marked `@pytest.mark.integration` — skipped by default.
- Test `to_domain()` output against domain type contracts (e.g. `DiscountCurve.df()` returns a valid discount factor ≤ 1).

---

## 8. Boundaries

| Category | Rule |
|---|---|
| **Always** | Read API keys from environment variables |
| **Always** | Return raw `pd.DataFrame` from `fetch()` before any domain mapping |
| **Always** | Write a unit test for every `to_domain()` mapping |
| **Ask first** | Adding a provider not in this spec |
| **Ask first** | Changing cache directory or TTL defaults |
| **Ask first** | Adding retry/backoff logic |
| **Never** | Hardcode API keys or credentials anywhere in source |
| **Never** | Make live network calls in unit tests |
| **Never** | Mutate cached data in place |
| **Never** | Add dependencies beyond `yfinance`, `fredapi`, and stdlib `urllib`/`xml` |

---

## 9. Implementation order

1. **`base.py`** — `DataAdapter` ABC and `DataFetchError`; unblocks all adapters.
2. **`cache.py`** — file-based cache; shared by all adapters.
3. **`USTreasuryAdapter`** — no auth, simplest to test; validates the cache and `DiscountCurve` mapping end-to-end.
4. **`FREDAdapter`** — macro rates and yield curve; requires `FRED_API_KEY`.
5. **`YahooFinanceAdapter`** — spot, history, option chain → `OptionInputs`.
6. **`AlphaVantageAdapter`** — daily OHLCV and FX; requires `ALPHA_VANTAGE_API_KEY`.

---

# SPEC: Dashboard — Phase 4

## 1. Objective

A browser-based analytics dashboard for **neon** — built with Vite + React + TypeScript — that lets a quant developer interactively explore options pricing, Greeks, vol surfaces, and fixed-income analytics for any ticker. The dashboard is a single-page app that calls the existing FastAPI backend (already scaffolded) and three new backend endpoints added in this phase.

**Target user:** the same single quant developer, running both servers locally.

**Success looks like:** enter a ticker and an expiry date; see a price chart, options chain, Greeks table, interactive 3D vol surface, and a portfolio Greeks panel — all populated from live market data.

---

## 2. Commands

```bash
# Frontend
cd dashboard
npm install              # install dependencies
npm run dev              # dev server on :5173 (proxies /stock → :8000)
npm run build            # production build
npm run typecheck        # tsc --noEmit

# Backend (from project root)
uv run uvicorn neon.api.main:app --reload   # API on :8000

# Tests
cd dashboard && npm test                    # Vitest unit tests
uv run pytest tests/api/                   # FastAPI endpoint tests
```

---

## 3. Tech stack

| Layer | Tool |
|---|---|
| Build | Vite 6, TypeScript, `@vitejs/plugin-react` |
| UI | React 19, Tailwind CSS v4 (`@tailwindcss/vite`) |
| Data fetching | TanStack Query v5 (`@tanstack/react-query`) |
| HTTP | Axios |
| Charts | Recharts (line/bar), Plotly.js (`react-plotly.js`) for 3D surface |
| Backend | FastAPI (existing), three new routers |
| Tests (FE) | Vitest + React Testing Library |
| Tests (BE) | pytest + FastAPI `TestClient` |

No additional Python dependencies. `react-plotly.js` + `plotly.js` added to `dashboard/package.json`.

---

## 4. Project structure

```
dashboard/src/
├── api.ts                          # typed axios calls (extend existing)
├── App.tsx                         # top-level layout + ticker/expiry form
├── main.tsx                        # QueryClientProvider entry
├── index.css                       # @import "tailwindcss"
└── components/
    ├── PriceChart.tsx              # Recharts line chart (existing)
    ├── OptionsChain.tsx            # calls/puts table (existing)
    ├── GreeksTable.tsx             # delta/gamma/vega/theta table (existing)
    ├── VolSurface.tsx              # NEW — Plotly.js 3D surface
    ├── PortfolioGreeks.tsx         # NEW — JSON input + aggregated Greeks
    └── BondAnalytics.tsx          # NEW — bond price, DV01, duration

src/neon/api/routers/
├── stock.py                        # existing
├── options.py                      # existing
├── greeks.py                       # existing
├── surface.py                      # existing (raw IV grid)
├── svi_surface.py                  # NEW — calibrated SVI surface
├── portfolio.py                    # NEW — portfolio Greeks via RiskEngine
└── bonds.py                        # NEW — bond pricing and analytics

tests/api/
├── test_svi_surface.py             # NEW
├── test_portfolio.py               # NEW
└── test_bonds.py                   # NEW
```

---

## 5. Feature specs

### 5.1 Vol surface panel — `VolSurface.tsx` + `/stock/{ticker}/svi-surface`

**Backend — `GET /stock/{ticker}/svi-surface`**

Calibrates `SVISurface` for the ticker (up to 8 nearest expiries from `yf.Ticker.options`) and returns a structured grid:

```json
{
  "strikes": [float, ...],
  "expiries": ["YYYY-MM-DD", ...],
  "vols": [[float, ...], ...]   // shape [n_strikes][n_expiries]
}
```

Response model reuses `SurfaceResponse` from `surface.py`. Uses `SVISurface.calibrate()` from `lib/instruments/surface/svi.py`; falls back to raw IV grid (existing `surface.py` logic) if calibration fails for an expiry.

**Frontend — `VolSurface.tsx`**

- Plotly.js `surface` trace: x = expiries (strings), y = strikes (floats), z = vols grid.
- Color scale: Viridis.
- Layout: dark background matching Tailwind `slate-950`, no axis gridlines.
- Loading / error states consistent with other panels.

**Acceptance:**
- Grid point lookup returns stored vol within `abs=1e-6`.
- Chart renders without NaN or zero-vol gaps (filter or clamp before passing to Plotly).
- Endpoint returns 404 with a message if no options data is available for the ticker.

---

### 5.2 Portfolio Greeks panel — `PortfolioGreeks.tsx` + `POST /portfolio/greeks`

**Backend — `POST /portfolio/greeks`**

Request body:

```json
{
  "positions": [
    {
      "ticker": "AAPL",
      "expiry": "2026-01-16",
      "strike": 200.0,
      "option_type": "call",
      "quantity": 10
    }
  ]
}
```

- Fetches spot price via `YahooFinanceAdapter.spot(ticker)`.
- Constructs `OptionInputs` for each position (IV from `YahooFinanceAdapter.option_chain`; falls back to `volatility=0.2` if not found).
- Wraps each in `EuropeanOption(inputs, AnalyticalGreeks())` and a `Position(instrument, quantity)`.
- Builds a `Portfolio` and calls `RiskEngine(portfolio).greeks()`.
- Returns aggregated Greeks: `delta`, `gamma`, `vega`, `theta` as floats.

Response model:

```json
{
  "delta": float,
  "gamma": float,
  "vega": float,
  "theta": float
}
```

**Frontend — `PortfolioGreeks.tsx`**

- `<textarea>` pre-filled with example JSON.
- "Calculate" button → POST → renders a summary row of the four aggregated Greeks.
- Inline validation: shows a parse error if the JSON is malformed before hitting the backend.
- Loading and error states.

**Acceptance:**
- Empty positions list returns all Greeks as `0.0`.
- Single ATM call with quantity 1 returns delta ≈ 0.5, gamma > 0, vega > 0, theta < 0.
- Quantity is signed: negative quantity flips the sign of all Greeks.

---

### 5.3 Bond analytics panel — `BondAnalytics.tsx` + `POST /bonds/price`

**Backend — `POST /bonds/price`**

Request body:

```json
{
  "face_value": 1000.0,
  "coupon_rate": 0.05,
  "coupon_freq": 2,
  "issue_date": "20240101",
  "maturity_date": "20340101",
  "ytm": 0.045
}
```

- Constructs a `Bond` from `lib/fixed_income/bond.py`.
- Computes dirty price, clean price, accrued interest, modified duration, Macaulay duration, DV01, convexity via `BondAnalytics`.
- Returns all as floats.

Response model:

```json
{
  "dirty_price": float,
  "clean_price": float,
  "accrued_interest": float,
  "modified_duration": float,
  "macaulay_duration": float,
  "dv01": float,
  "convexity": float
}
```

**Frontend — `BondAnalytics.tsx`**

- Form with labelled numeric inputs for each field (pre-filled with sensible defaults).
- "Price" button → POST → renders a summary card of all seven outputs.
- Client-side validation: `coupon_rate` and `ytm` must be in `[0, 1]`; `maturity_date` must be after `issue_date`.

**Acceptance:**
- 5% coupon at 4.5% YTM prices above par (dirty price > 1000).
- DV01 is negative (price falls when yield rises).
- All outputs are finite floats; no `NaN` or `Infinity`.

---

### 5.4 `optioncharts.io`-style charts

Implement the following chart types, modelled on the visual language of optioncharts.io:

| Chart | Data source | Component |
|---|---|---|
| IV smile (per expiry) | `/stock/{ticker}/options/{expiry}` | `IVSmile.tsx` — Recharts line, x = strike, y = IV% |
| Delta vs strike | `/stock/{ticker}/greeks/{expiry}` | `DeltaSmile.tsx` — Recharts line, x = strike, y = delta; calls and puts on same axis |
| Gamma vs strike | same Greeks endpoint | `GammaSmile.tsx` |
| Theta vs strike | same Greeks endpoint | `ThetaSmile.tsx` |

All four share the same Recharts `<LineChart>` skeleton — extract a `<SmileChart title xLabel yLabel data>` base component to avoid repetition.

**Acceptance:**
- IV smile is U-shaped (smile/skew visible) for a liquid ticker with a near-term expiry.
- Delta curve runs from ~0 (deep OTM put) to ~1 (deep ITM call).
- All charts render error state if the endpoint returns no rows.

---

## 6. Layout

Single-page layout with a sticky top bar containing the ticker input, expiry input, and Load button. Panels below in a two-column grid on wide screens, single column on narrow:

```
┌──────────────────────────────────────────────┐
│  neon dashboard   [ticker] [expiry]  [Load]  │  ← sticky header
├────────────────────┬─────────────────────────┤
│  Price Chart       │  Vol Surface (3D)        │
├────────────────────┼─────────────────────────┤
│  Options Chain     │  IV Smile                │
├────────────────────┼─────────────────────────┤
│  Greeks Table      │  Delta / Gamma / Theta   │
├────────────────────┴─────────────────────────┤
│  Portfolio Greeks (full width)               │
├──────────────────────────────────────────────┤
│  Bond Analytics (full width)                 │
└──────────────────────────────────────────────┘
```

---

## 7. Code style

### Frontend

- One component per file; no component exports more than one public symbol.
- All API response shapes typed in `api.ts`; no `any`.
- TanStack Query for all async data — no raw `useEffect` + `useState` for fetching.
- Tailwind utility classes only; no custom CSS files beyond `index.css`.
- `type` imports enforced (`verbatimModuleSyntax`).

### Backend

- New routers follow the existing pattern: `APIRouter(prefix=..., tags=[...])`, Pydantic request/response models, raise `HTTPException` for all error cases.
- No business logic in routers — delegate to domain objects.
- Module-level adapter singletons (`_adapter = YahooFinanceAdapter()`).

---

## 8. Testing strategy

### Frontend

- Vitest + React Testing Library.
- Each component has one test file: render with mock data, assert key elements visible.
- Mock `@tanstack/react-query` at the module level to return canned data — no real HTTP in tests.
- `PortfolioGreeks.tsx`: test JSON parse error path and the happy-path render.

### Backend

- `pytest` + FastAPI `TestClient`.
- Mock `YahooFinanceAdapter` and `yfinance` in all tests — no live network.
- One test class per endpoint: `TestSVISurface`, `TestPortfolioGreeks`, `TestBondPrice`.
- Cover: 200 happy path, 404 not found, 422 validation error.

---

## 9. Boundaries

| Category | Rule |
|---|---|
| **Always** | New routers follow `APIRouter(prefix=..., tags=[...])` convention |
| **Always** | All fetch calls go through `api.ts` — no inline `axios` in components |
| **Always** | Run `npm run typecheck` and `uv run ruff check .` before marking done |
| **Always** | Filter zero/NaN vols before passing to Plotly surface |
| **Ask first** | Adding any npm package beyond what's in this spec |
| **Ask first** | Adding any new Python dependency |
| **Ask first** | Changing the `/portfolio/greeks` request schema |
| **Never** | Business logic in React components — keep components as thin views |
| **Never** | Raw `useEffect` + `setState` for data fetching |
| **Never** | Import from `neon.lib` across router boundaries (routers call domain objects, not each other) |

---

## 10. Implementation order

1. **`svi_surface.py` router + tests** — independent of frontend work; validates SVI calibration end-to-end.
2. **`portfolio.py` router + tests** — depends on `RiskEngine` (already built).
3. **`bonds.py` router + tests** — depends on `Bond` and `BondAnalytics` (already built).
4. **`VolSurface.tsx`** — add `react-plotly.js`, implement 3D chart, wire to `/svi-surface`.
5. **`SmileChart` base + `IVSmile`, `DeltaSmile`, `GammaSmile`, `ThetaSmile`** — reuse existing endpoints.
6. **`PortfolioGreeks.tsx`** — wire to `/portfolio/greeks`.
7. **`BondAnalytics.tsx`** — wire to `/bonds/price`.
8. **Layout refactor** — two-column grid, sticky header, responsive breakpoints.

---

# SPEC: Cloud Deployment — Phase 5

## 1. Objective

Deploy **neon** to Azure so the app is publicly accessible and scales automatically with traffic. The FastAPI backend runs on Azure Container Apps (serverless containers, HTTP autoscaling, minimum 1 replica). The React SPA is served via Azure Static Web Apps (CDN-backed, GitHub-integrated). CI/CD is handled by Azure DevOps pipelines.

**Target user:** the same single quant developer, accessing the app from a browser anywhere.

**Success looks like:** push to `main` → pipeline builds and pushes the container → Container App updates → Static Web App redeploys the SPA — all without manual steps. The API scales from 1 to N replicas under load and back to 1 when quiet.

---

## 2. Azure resource map

| Resource | Purpose | Tier |
|---|---|---|
| Azure Container Registry (ACR) | Stores the FastAPI Docker image | Basic |
| Azure Container Apps Environment | Shared networking / log analytics for all container apps | Consumption |
| Azure Container App — `neon-api` | Runs the FastAPI backend; HTTP ingress on port 8000 | Consumption (min 1, max 10 replicas) |
| Azure Static Web Apps — `neon-dashboard` | Serves the Vite SPA from CDN | Free |
| Azure Key Vault | Stores `FRED_API_KEY`, `ALPHA_VANTAGE_API_KEY`, and any future secrets | Standard |
| Log Analytics Workspace | Container Apps logs and metrics | Pay-as-you-go |

All resources live in a single resource group (`rg-neon`), single region (`eastus2` default — override via pipeline variable).

---

## 3. Commands

```bash
# Provision infrastructure (one-time, run locally with az CLI)
az login
az group create --name rg-neon --location eastus2
az acr create --resource-group rg-neon --name neoncr --sku Basic
az containerapp env create --name neon-env --resource-group rg-neon --location eastus2

# Build and push image locally (dev/debug)
docker build -t neoncr.azurecr.io/neon-api:latest .
az acr login --name neoncr
docker push neoncr.azurecr.io/neon-api:latest

# Deploy container app (first time)
az containerapp create \
  --name neon-api \
  --resource-group rg-neon \
  --environment neon-env \
  --image neoncr.azurecr.io/neon-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 20

# Update after image push (done by pipeline)
az containerapp update --name neon-api --resource-group rg-neon \
  --image neoncr.azurecr.io/neon-api:<tag>
```

---

## 4. Project structure additions

```
/                               (project root)
├── Dockerfile                  ← NEW — FastAPI container image
├── .dockerignore               ← NEW
├── infra/
│   ├── main.bicep              ← NEW — Bicep template for all Azure resources
│   └── parameters.json         ← NEW — environment-specific parameter values
└── .azure-pipelines/
    ├── backend.yml             ← NEW — build, push image, update Container App
    └── frontend.yml            ← NEW — build SPA, deploy to Static Web Apps
```

The `dashboard/` frontend build is already handled by Azure Static Web Apps' built-in GitHub/ADO integration; `frontend.yml` only needs to set the build output path (`dashboard/dist`).

---

## 5. Feature specs

### 5.1 Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev
COPY src/ src/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "neon.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- Multi-stage build is not required (no compiled assets).
- `uv sync --no-dev` installs only runtime dependencies — dev tools (`pytest`, `ruff`) are excluded.
- `.dockerignore` excludes `dashboard/`, `tests/`, `*.md`, `__pycache__/`, `.venv/`.

**Acceptance:**
- `docker build` completes without error.
- `docker run -p 8000:8000` serves `GET /health` → `{"status": "ok"}`.
- Image size < 500 MB.

---

### 5.2 `/health` endpoint

Add `GET /health` to `src/neon/api/main.py`:

```python
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

Required by Azure Container Apps liveness and readiness probes.

**Acceptance:**
- Returns `200 {"status": "ok"}` with no auth.
- Added to `tests/api/test_health.py`.

---

### 5.3 Bicep infrastructure (`infra/main.bicep`)

Declares all resources in §2 as code. Parameterised:

| Parameter | Default | Description |
|---|---|---|
| `location` | `eastus2` | Azure region |
| `acrName` | `neoncr` | Container registry name (must be globally unique) |
| `minReplicas` | `1` | Container App min replicas |
| `maxReplicas` | `10` | Container App max replicas |
| `concurrencyThreshold` | `20` | HTTP requests/replica before scale-out |

**Acceptance:**
- `az deployment group validate --template-file infra/main.bicep` passes with no errors.
- A fresh `az deployment group create` from the template produces all resources in §2.

---

### 5.4 Azure DevOps pipeline — backend (`.azure-pipelines/backend.yml`)

Trigger: push to `main` with changes under `src/`, `Dockerfile`, or `pyproject.toml`.

Stages:
1. **Test** — `uv run pytest tests/` and `uv run ruff check .`; fail fast on error.
2. **Build & Push** — `docker build` → tag with `$(Build.BuildId)` and `latest` → `docker push` to ACR.
3. **Deploy** — `az containerapp update --image neoncr.azurecr.io/neon-api:$(Build.BuildId)`.

Pipeline variables (stored in Azure DevOps variable group `neon-secrets`, not in YAML):
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID` (service principal)
- `ACR_NAME`
- `FRED_API_KEY`
- `ALPHA_VANTAGE_API_KEY`

Secrets are injected as environment variables into the Container App via `az containerapp update --set-env-vars`.

**Acceptance:**
- Pipeline runs green on push to `main`.
- Container App URL returns `200` on `GET /health` after deploy.
- Secrets never appear in pipeline logs (use `isSecret: true` in variable group).

---

### 5.5 Azure DevOps pipeline — frontend (`.azure-pipelines/frontend.yml`)

Trigger: push to `main` with changes under `dashboard/`.

Stages:
1. **Build** — `cd dashboard && npm ci && npm run build` → artifact at `dashboard/dist/`.
2. **Deploy** — Azure Static Web Apps deploy task (`AzureStaticWebApp@0`) pointing at `dashboard/dist/`.

Pipeline variable: `AZURE_STATIC_WEB_APPS_API_TOKEN` (from SWA deployment token, stored in variable group).

**Acceptance:**
- SPA loads at the Static Web Apps URL after deploy.
- API calls from the SPA reach the Container App (CORS configured in FastAPI — `ALLOWED_ORIGINS` env var, defaulting to `*` for development).

---

### 5.6 CORS configuration

Add `CORSMiddleware` to `src/neon/api/main.py`:

```python
import os
from fastapi.middleware.cors import CORSMiddleware

origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])
```

In production, `ALLOWED_ORIGINS` is set to the Static Web Apps URL via `az containerapp update --set-env-vars`.

---

## 6. Scaling policy

| Metric | Value |
|---|---|
| Scale trigger | Concurrent HTTP requests per replica |
| Scale-out threshold | 20 requests/replica |
| Min replicas | 1 (always warm — no cold starts) |
| Max replicas | 10 |
| Scale-in cooldown | Azure Container Apps default (5 min) |

The 1-replica minimum keeps the API responsive for the moderate/unpredictable traffic pattern without cold-start latency.

---

## 7. Testing strategy

- `tests/api/test_health.py` — unit test for the `/health` endpoint.
- Bicep validation runs in the backend pipeline as a pre-deploy check (`az deployment group validate`).
- No new integration tests beyond what exists — the pipeline's post-deploy `GET /health` smoke check is sufficient.

---

## 8. Boundaries

| Category | Rule |
|---|---|
| **Always** | Secrets in Azure Key Vault / ADO variable groups — never in source |
| **Always** | Tag images with `$(Build.BuildId)` in addition to `latest` |
| **Always** | Run tests before building the image |
| **Always** | `ALLOWED_ORIGINS` must be set to the SWA URL in production |
| **Ask first** | Adding a database or persistent storage (stateless app assumed) |
| **Ask first** | Changing the Azure region |
| **Ask first** | Moving to a Dedicated Container Apps plan (cost implications) |
| **Never** | Hardcode secrets or subscription IDs in Bicep or pipeline YAML |
| **Never** | Push the `latest` tag without also pushing a build-ID tag |
| **Never** | Skip the test stage to speed up a deploy |

---

## 9. Implementation order

1. **`GET /health` endpoint + test** — required by Container Apps probes; trivial, unblocks everything.
2. **`Dockerfile` + `.dockerignore`** — verify `docker build` and `docker run` locally before pushing to ACR.
3. **Bicep template** — provision all Azure resources; validate with `az deployment group validate`.
4. **CORS middleware** — needed before the SPA can call the API from a different origin.
5. **Backend ADO pipeline** — wire up test → build → push → deploy; validate with a push to `main`.
6. **Frontend ADO pipeline** — wire up build → SWA deploy; validate end-to-end in the browser.
