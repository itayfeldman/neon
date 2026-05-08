# SPEC: NumericalGreeks

## 1. Objective

Implement `NumericalGreeks` — a finite-difference-based Greeks calculator that approximates option sensitivities by bumping inputs to any user-supplied pricing function.

**Target users:** Quant developers who need model-agnostic Greeks, numerical validation of analytical formulas, or Greeks for pricing models without closed-form derivatives (Monte Carlo, binomial trees, PDE solvers).

## 2. SOLID Design

### Single Responsibility (SRP)

`NumericalGreeks` has one job: approximate partial derivatives of a pricing function via central finite differences. It does not price options itself — it delegates pricing to an injected callable.

### Open/Closed (OCP)

Adding a new pricing model (Monte Carlo, binomial tree, etc.) requires zero changes to `NumericalGreeks`. Pass a new callable — done.

### Liskov Substitution (LSP)

`NumericalGreeks` extends `Greeks` and is a drop-in substitute wherever `Greeks` or `AnalyticalGreeks` is used. Same method signatures, same return types. `EuropeanOption(inputs, NumericalGreeks(fn))` works identically to `EuropeanOption(inputs, AnalyticalGreeks())`.

### Interface Segregation (ISP)

The pricing function contract is minimal: a single `Callable` that accepts six keyword arguments and returns a `float`. No base class or mixin required from the pricer.

### Dependency Inversion (DIP)

`NumericalGreeks` depends on an abstraction (a callable pricing function), not a concrete class. It never imports or references `AnalyticalGreeks`.

## 3. Interface

### Constructor

```python
class NumericalGreeks(Greeks):
    def __init__(
        self,
        pricing_fn: Callable[..., float],
        spot_bump: float = 0.01,
        vol_bump: float = 0.01,
        rate_bump: float = 0.0001,
        time_bump: float = 1 / 365,
    ): ...
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pricing_fn` | `Callable[..., float]` | required | Accepts keyword args `underlying_price`, `strike_price`, `volatility`, `risk_free_rate`, `time_to_maturity`, `option_type` and returns a price. |
| `spot_bump` | `float` | `0.01` | Relative bump for spot (1% of `underlying_price`). Used by `delta`, `gamma`, `vanna`. |
| `vol_bump` | `float` | `0.01` | Absolute bump for volatility (1 vol point). Used by `vega`, `volga`, `vanna`. |
| `rate_bump` | `float` | `0.0001` | Absolute bump for risk-free rate (1 basis point). Used by `rho`. |
| `time_bump` | `float` | `1/365` | Absolute bump for time to maturity (1 calendar day). Used by `theta`. |

### Market data attributes (set externally, same pattern as `AnalyticalGreeks`)

- `underlying_price: float`
- `strike_price: float`
- `volatility: float`
- `risk_free_rate: float`
- `time_to_maturity: float`
- `option_type: int` (OptionType enum, Call=+1, Put=−1)

### Methods

All methods return `float`, matching the `Greeks` base class.

| Method | Greek | Finite Difference | Formula |
|---|---|---|---|
| `price()` | — | None (delegates) | `pricing_fn(current params)` |
| `delta()` | ∂P/∂S | Central 1st | `[P(S+h) − P(S−h)] / 2h` where `h = spot_bump × S` |
| `gamma()` | ∂²P/∂S² | Central 2nd | `[P(S+h) − 2P(S) + P(S−h)] / h²` |
| `vega()` | ∂P/∂σ | Central 1st | `[P(σ+h) − P(σ−h)] / 2h` where `h = vol_bump` |
| `theta()` | −∂P/∂T | Central 1st (negated) | `−[P(T+h) − P(T−h)] / 2h` where `h = time_bump` |
| `rho()` | ∂P/∂r | Central 1st | `[P(r+h) − P(r−h)] / 2h` where `h = rate_bump` |
| `vanna()` | ∂²P/∂S∂σ | Central cross | `[P(S+h₁,σ+h₂) − P(S+h₁,σ−h₂) − P(S−h₁,σ+h₂) + P(S−h₁,σ−h₂)] / 4h₁h₂` |
| `volga()` | ∂²P/∂σ² | Central 2nd | `[P(σ+h) − 2P(σ) + P(σ−h)] / h²` |

**Theta sign convention:** The analytical `theta()` returns `∂P/∂t` (rate of change as calendar time advances), which is negative for standard options (time decay). Since we bump `T` (time to maturity), and `∂P/∂t = −∂P/∂T`, the finite difference is negated.

## 4. Internal Design

A private `_reprice(**overrides)` method builds the full parameter dict from current attributes, applies overrides, and calls `pricing_fn`:

```python
def _reprice(self, **overrides) -> float:
    params = {
        "underlying_price": self.underlying_price,
        "strike_price": self.strike_price,
        "volatility": self.volatility,
        "risk_free_rate": self.risk_free_rate,
        "time_to_maturity": self.time_to_maturity,
        "option_type": self.option_type,
    }
    params.update(overrides)
    return self.pricing_fn(**params)
```

Each Greek method calls `_reprice` with the appropriate bumped parameter(s). This keeps each method concise (3–5 lines) and avoids duplicating the parameter-assembly logic.

## 5. Files

| Action | Path | Description |
|---|---|---|
| Modify | `src/neon/lib/greeks/numerical_greeks.py` | Replace stub with full implementation |
| Modify | `tests/lib/greeks/test_european_option_numerical_greeks.py` | Comprehensive test suite |

No changes to `greeks.py`, `analytical_greeks.py`, `__init__.py`, or any other existing file.

## 6. Testing Strategy

### Approach: validate numerical Greeks against analytical Greeks

Use Black-Scholes (`AnalyticalGreeks.price`) as the pricing function for `NumericalGreeks`. The numerical results must agree with the closed-form analytical values within tolerance.

### Test cases

| Category | Tests |
|---|---|
| **price** | Delegates to `pricing_fn`; matches analytical for call and put |
| **delta** | ATM call ≈ 0.5–0.6; matches analytical within tolerance; call delta ∈ [0, 1]; put delta ∈ [−1, 0] |
| **gamma** | Matches analytical; always positive; peaks near ATM |
| **vega** | Matches analytical; always positive; peaks near ATM |
| **theta** | Matches analytical; sign is negative for long options |
| **rho** | Matches analytical; positive for calls, negative for puts |
| **vanna** | Matches analytical cross-partial |
| **volga** | Matches analytical second-order vol sensitivity |
| **Configurations** | ITM, ATM, OTM for both calls and puts |
| **LSP** | `EuropeanOption` works with `NumericalGreeks` the same as with `AnalyticalGreeks` |

### Tolerance

Numerical agreement with analytical values: `abs=0.01` (1 cent / 1% of Greek value) is acceptable given finite-difference approximation error.

## 7. Boundaries

| Category | Rule |
|---|---|
| **Always** | Maintain `instruments → greeks → datetime → core` dependency flow |
| **Always** | Follow existing patterns (attribute injection for market data, `Greeks` base class) |
| **Always** | Return `float` from all Greek methods |
| **Never** | Modify `Greeks`, `AnalyticalGreeks`, or any existing file beyond the two listed above |
| **Never** | Add external dependencies beyond what's in `pyproject.toml` |
| **Never** | Hard-code a specific pricing model inside `NumericalGreeks` |
