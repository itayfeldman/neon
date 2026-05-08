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
| `instruments` | `lib/instruments/` | `Instrument` ABC, `Cash`, and options hierarchy |
| `portfolio` | `lib/portfolio/` | `Portfolio` and `Position` |

Dependency flow is strictly downward: `instruments` → `greeks` → `datetime` → `core`.

### Key modules

- `lib/core/constants.py` — numeric constants: `N_SIM`, `ERR`, `VOL`, `VOL_MIN`, `TARGET_GAMMA`, `TARGET_VEGA`, `DATE_FORMAT`.
- `lib/core/` — individual enum files: `currency.py` (`Currency` StrEnum), `month_code.py` (`MonthCode` IntEnum, F–Z), `position_direction.py` (`PositionDirection`), `time_steps.py` (`TimeSteps`).
- `lib/datetime/day_count.py` — `DayCount` StrEnum (e.g. `ACT/360`, `ACT/365`, `30/360`).
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

Most option pricing methods (`EuropeanOption`, `AmericanOption`, `AsianOption`, `BermudaOption`) and both Greeks subclasses raise `NotImplementedError`. The modules `cash_flow/`, `surface/`, `term_structure/`, and `api/` are empty placeholders for future work.
