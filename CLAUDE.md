# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync --group dev       # install all dependencies incl. dev
uv run neon               # run the CLI entry point
uv run pytest             # run all tests
uv run pytest tests/test_foo.py::test_bar  # run a single test
uv run ruff check .       # lint
uv run ruff format .      # format
```

## Architecture

This is a **quantitative finance / derivatives** project. The domain is options pricing and risk (Greeks).

**src layout** — all source lives under `src/neon/lib/`. The package is installed in editable mode by `uv sync`, so imports are always `from neon.lib.X import Y`.

### Module layers

| Layer | Path | Purpose |
|---|---|---|
| `core` | `lib/core/` | Enums and numeric constants |
| `datetime` | `lib/datetime/` | Day count conventions and time-to-maturity calculations |
| `greeks` | `lib/greeks/` | Base Greeks class; `AnalyticalGreeks` and `NumericalGreeks` subclasses |
| `pricing` | `lib/pricing/` | `simulate_gbm`, `price_mc` — reusable Monte Carlo simulation |
| `instruments` | `lib/instruments/` | `Instrument` ABC, `Cash`, and options hierarchy |
| `portfolio` | `lib/portfolio/` | `Portfolio` and `Position` |
| `risk` | `lib/risk/` | `RiskEngine` — portfolio-level Greeks aggregation |
| `fixed_income` | `lib/fixed_income/` | Bond pricing, discount curve, analytics |

Dependency flow is strictly downward: `risk` → `portfolio` → `instruments` → `pricing` → `core`; `instruments` → `greeks` → `datetime` → `core`; `fixed_income` → `datetime` → `core`.

### Key modules

- `lib/core/constants.py` — numeric constants: `N_SIM`, `ERR`, `VOL`, `VOL_MIN`, `TARGET_GAMMA`, `TARGET_VEGA`, `DATE_FORMAT`.
- `lib/core/` — individual enum files: `currency.py` (`Currency` StrEnum), `month_code.py` (`MonthCode` IntEnum, F–Z), `position_direction.py` (`PositionDirection`), `time_steps.py` (`TimeSteps`).
- `lib/datetime/day_count.py` — `DayCount` StrEnum: `ACT360`, `ACT365`, `THIRTY360`, `ACTACT_ISDA`.
- `lib/instruments/options/option_inputs.py` — `OptionInputs` Pydantic model: the canonical input struct for all option types; holds underlying price, strike, vol, rate, dates, `OptionType`, `DayCount`, etc.
- `lib/instruments/options/base.py` — `BaseOption` abstract class; computes `time_to_maturity` from `OptionInputs` on construction.
- `lib/datetime/ttm.py` — `time_to_maturity()` dispatcher; three implementations for ACT/360, ACT/365, and 30/360 conventions.
- `securities_master/` — YAML reference data for equities and indexes (e.g. TSLA, SPX); bonds and options subdirs are empty placeholders.

### Domain conventions

- `OptionType` and `PositionDirection` are `IntEnum` with signed values (Call/Long = +1, Put/Short = −1) so they multiply directly into pricing and PnL formulas.
- `MonthCode` maps standard futures month letter codes to integers (F=1 … Z=12).
- `TimeSteps` values represent **periods per year** (Daily=252 trading days).
- `DATE_FORMAT = "%Y%m%d"` — dates are compact strings (e.g. `"20260408"`).

### Status

- `AnalyticalGreeks` — full Black-Scholes pricing and all 7 Greeks (delta, gamma, vega, theta, rho, vanna, volga).
- `AmericanOption` — CRR binomial tree with early exercise.
- `VolatilitySurface` — bilinear interpolation via `scipy.interpolate.RegularGridInterpolator`.
- `Position` — frozen dataclass; signed `quantity` encodes direction (positive = long, negative = short).
- `RiskEngine` — aggregates portfolio Greeks as `Σ position.quantity × instrument.greeks.<greek>()`.
- `EuropeanOption` — delegates pricing and Greeks to injected `Greeks` object; auto-wires `OptionInputs` on construction.
- `AsianOption` — Monte Carlo arithmetic average price via `lib/pricing/monte_carlo.py`.
- `BermudaOption` — CRR binomial tree with early exercise only at specified `exercise_dates`.
- `lib/pricing/monte_carlo.py` — `simulate_gbm` (GBM path simulation) and `price_mc` (discounted mean payoff).
- `lib/fixed_income/coupon_schedule.py` — `CouponSchedule`: backward generation of payment dates from maturity by coupon frequency.
- `lib/fixed_income/bond.py` — `Bond`: dirty/clean price from YTM (fractional-period discounting), YTM from clean price (`brentq`), accrued interest, price from discount curve.
- `lib/fixed_income/discount_curve.py` — `DiscountCurve`: log-linear interpolation; `df()`, `zero_rate()`, `forward_rate()`.
- `lib/fixed_income/bond_analytics.py` — `BondAnalytics`: DV01, modified duration, Macaulay duration, convexity (all ±1bp bump-and-reprice).
- `lib/fixed_income/zero_coupon_bond.py` — `ZeroCouponBond`: subclass of `Bond` with `coupon_rate=0`, `coupon_freq=1`.
- `lib/fixed_income/frn.py` — `FloatingRateNote`: subclass of `Bond`; `coupon_rate = reference_rate + spread`.
- `cash_flow/`, `term_structure/`, `api/` are unimplemented placeholders.
