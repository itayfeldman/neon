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

# SPEC: TSLA Dashboard — Phase 4

## 1. Objective

A small-team web dashboard for TSLA options analytics. The frontend is a React single-page app deployed to Vercel; the backend is a FastAPI service deployed to Railway. The backend wraps the existing `neon` library (data adapters, Greeks, vol surface) and exposes JSON endpoints. The frontend renders interactive charts and tables.

Target users: a small quant team accessing the dashboard via browser, no local setup required.

---

## 2. Tech stack

| Layer | Tool | Notes |
|---|---|---|
| Backend | FastAPI | Python, thin API over `neon` lib |
| Frontend | React + TypeScript | Vite for build tooling |
| Charts | Recharts or Plotly.js | Plotly preferred for finance charts |
| Deployment | Vercel (frontend) + Railway (backend) | Both have free tiers |
| Data | `YahooFinanceAdapter` | Live TSLA data, file-cached |

---

## 3. Commands

```bash
# Backend
uv add fastapi uvicorn
uv run uvicorn neon.api.main:app --reload   # dev server at localhost:8000

# Frontend (requires Node.js ≥ 20)
npm create vite@latest dashboard -- --template react-ts
cd dashboard && npm install && npm run dev  # dev server at localhost:5173

# Deploy
railway up                                  # deploy backend
vercel --prod                               # deploy frontend
```

Environment variables:
```bash
# Backend (.env / Railway)
ALLOWED_ORIGINS=https://your-app.vercel.app

# Frontend (.env / Vercel)
VITE_API_URL=https://your-api.railway.app
```

---

## 4. Project structure

```
src/neon/api/
    __init__.py
    main.py          # FastAPI app, CORS, router registration
    routers/
        stock.py     # GET /stock/{ticker}/history
        options.py   # GET /stock/{ticker}/options/{expiry}
        greeks.py    # GET /stock/{ticker}/greeks/{expiry}
        surface.py   # GET /stock/{ticker}/surface

dashboard/           # Vite + React project (separate dir, deployed to Vercel)
    src/
        api/
            client.ts        # typed fetch wrappers for each endpoint
        components/
            PriceChart.tsx   # OHLCV candlestick (Plotly)
            OptionsTable.tsx # calls/puts chain with IV, delta, gamma
            GreeksHeatmap.tsx # delta/gamma/vega across strikes × expiries
            VolSurface.tsx   # 3D implied vol surface (Plotly)
        App.tsx
    vite.config.ts
    vercel.json
```

---

## 5. API endpoints

| Method | Path | Returns |
|---|---|---|
| `GET` | `/stock/{ticker}/history` | `{dates, opens, highs, lows, closes, volumes}` |
| `GET` | `/stock/{ticker}/options/{expiry}` | `{calls: [...], puts: [...]}` each row: strike, iv, bid, ask, volume |
| `GET` | `/stock/{ticker}/greeks/{expiry}` | `[{strike, delta, gamma, vega, theta}]` per strike |
| `GET` | `/stock/{ticker}/surface` | `{strikes, expiries, vols}` for vol surface |

All endpoints accept `?ticker=TSLA` as the default. Errors return `{"detail": "..."}` with appropriate HTTP status.

---

## 6. Dashboard panels

1. **Price chart** — OHLCV candlestick for the past year. Ticker selector (default TSLA).
2. **Options chain** — expiry date picker; table of calls and puts with strike, IV, bid, ask, volume, delta, gamma.
3. **Greeks heatmap** — delta, gamma, or vega (selector) as a heatmap across strike × expiry.
4. **Vol surface** — 3D surface plot of implied vol across all strikes and expiries.

---

## 7. Code style

**Backend**
- Thin routers — no business logic in routers; delegate to `neon.lib.data` and `neon.lib.greeks`.
- Pydantic response models for every endpoint.
- CORS restricted to `ALLOWED_ORIGINS` env var (comma-separated).

**Frontend**
- TypeScript strict mode.
- One component per panel; `App.tsx` composes them.
- `api/client.ts` is the only place that knows the API URL — never hardcode URLs in components.
- No CSS frameworks in scope — plain CSS modules are fine.

---

## 8. Testing strategy

**Backend**
- Unit tests for each router using `httpx.AsyncClient` with `TestClient`.
- Mock `YahooFinanceAdapter` — no live network in tests.
- One test per endpoint: happy path + error (ticker not found).

**Frontend**
- No frontend tests in scope for the initial build.

---

## 9. Boundaries

| Category | Rule |
|---|---|
| **Always** | Keep `VITE_API_URL` in env — never hardcode the Railway URL in source |
| **Always** | Restrict CORS to the Vercel domain via `ALLOWED_ORIGINS` |
| **Always** | Return Pydantic models from every FastAPI endpoint |
| **Ask first** | Adding a new ticker beyond TSLA |
| **Ask first** | Adding authentication |
| **Never** | Put business logic (Greeks computation, vol calibration) in routers |
| **Never** | Make live network calls in backend unit tests |
| **Never** | Commit `.env` files |

---

## 10. Implementation order

1. **FastAPI backend** — `main.py`, CORS, `/stock/{ticker}/history` endpoint + test.
2. **Options endpoint** — `/options/{expiry}` using `YahooFinanceAdapter.option_chain()`.
3. **Greeks endpoint** — compute `AnalyticalGreeks` per strike from options chain.
4. **Surface endpoint** — build `VolatilitySurface` from IV grid.
5. **React scaffold** — Vite project, `api/client.ts`, `PriceChart.tsx`.
6. **Options chain table** — `OptionsTable.tsx` wired to `/options/{expiry}`.
7. **Greeks heatmap** — `GreeksHeatmap.tsx` wired to `/greeks/{expiry}`.
8. **Vol surface** — `VolSurface.tsx` wired to `/surface`.
9. **Deploy** — Railway + Vercel, env vars, CORS.
