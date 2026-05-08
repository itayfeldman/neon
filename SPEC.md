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
