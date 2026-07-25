# QIS Backtesting System — Task List

## Checkpoint A: Core QIS primitives

### A1 — `config.py` + `test_config.py`
**Files:** `src/neon/lib/qis/config.py`, `tests/lib/qis/test_config.py`

Central config object. Loads YAML, exposes params, dynamically imports the strategy class.

**Acceptance:**
- `StrategyConfig.load("configs/momentum.yaml")` returns a frozen dataclass with `module`, `class_name`, `params`
- `config.get("lookback_months", 12)` returns the value from YAML or the default
- `config.build_strategy()` uses `importlib.import_module` + `getattr` to instantiate the class
- `build_strategy()` raises `ImportError` with a clear message for a bad `module` value
- `build_strategy()` raises `AttributeError` with a clear message for a bad `class` value
- YAML keys `module` and `class` are consumed; all remaining keys land in `params`

**Verify:** `uv run pytest tests/lib/qis/test_config.py`

---

### A2 — `signal.py` + `test_signal.py`
**Files:** `src/neon/lib/qis/signal.py`, `tests/lib/qis/test_signal.py`

Pure value object, no neon deps.

**Acceptance:**
- `Signal` is frozen, hashable, slots=True
- `SignalDirection.Long == 1`, `SignalDirection.Short == -1`, `SignalDirection.Flat == 0`
- `Signal.metadata` defaults to empty dict
- Two `Signal` instances with identical fields are equal

**Verify:** `uv run pytest tests/lib/qis/test_signal.py`

---

### A3 — `book.py` + `test_book.py`
**Files:** `src/neon/lib/qis/book.py`, `tests/lib/qis/test_book.py`

Wraps `Portfolio` + `Position`; owns cash accounting.

**Acceptance:**
- `StrategyBook(name="test", cash=100_000).mark_to_market() == 100_000` (no positions)
- `open_position(instrument, qty, price)` debits `cash` by `qty * price * multiplier`
- `close_position(ticker, price)` credits `cash`; open+close round-trip leaves `cash` unchanged
- `update_position` removes the old frozen `Position` and adds a new one; cash-settles the diff
- `position_quantity(ticker)` returns `0.0` for unknown ticker
- `book.portfolio` is a valid `Portfolio` passable to `RiskEngine`

**Verify:** `uv run pytest tests/lib/qis/test_book.py`

---

### A4 — `strategy.py`
**File:** `src/neon/lib/qis/strategy.py`

ABC only. No test file — verified implicitly by strategy implementations.

**Acceptance:**
- Constructor stores `StrategyConfig` as `self._config`
- `on_expiry` default returns `[]`
- A concrete subclass implementing `name`, `initialize`, `on_date` can be instantiated

---

### A5 — `backtest.py` + `test_backtest.py`
**Files:** `src/neon/lib/qis/backtest.py`, `tests/lib/qis/test_backtest.py`

Event-driven date loop; drives strategy over a date range.

**Acceptance:**
- `NoOpStrategy` (returns `[]` from `on_date`) runs 10 business days without error
- `_business_days("20260601", "20260605")` yields exactly 5 date strings (Mon–Fri)
- `len(analytics.snapshots)` equals business day count in configured range
- `DaySnapshot.nav == initial_capital` throughout a no-op run
- `trading_cost_bps` is deducted from cash proportionally to executed notional
- `_compute_greeks` returns `(None, None, None)` for a portfolio with no options

**Verify:** `uv run pytest tests/lib/qis/test_backtest.py`

---

### A6 — `analytics.py` + `test_analytics.py`
**Files:** `src/neon/lib/qis/analytics.py`, `tests/lib/qis/test_analytics.py`

All performance metrics from `list[DaySnapshot]`.

**Acceptance:**
- `nav_series()` has DatetimeIndex with length == `len(snapshots)`
- `daily_returns()[t] == (nav[t] - nav[t-1]) / nav[t-1]`
- `max_drawdown() == 0.0` for monotonically increasing NAV
- `max_drawdown() == pytest.approx(0.5, abs=0.001)` for NAV that doubles then halves
- `sharpe_ratio()` annualizes by `sqrt(TimeSteps.Daily.value)` = `sqrt(252)`
- `sortino_ratio()` uses only negative-return days in the denominator
- `hit_rate()` in `[0.0, 1.0]`
- `summary()` has exactly: `total_pnl`, `total_return_pct`, `annualized_return_pct`, `sharpe_ratio`, `max_drawdown`, `calmar_ratio`, `sortino_ratio`, `hit_rate`; all values are `float`
- `delta_series()` returns `NaN` for snapshots where `net_delta is None`

**Verify:** `uv run pytest tests/lib/qis/test_analytics.py`

---

### A7 — `__init__.py`
**File:** `src/neon/lib/qis/__init__.py`

Exports: `Strategy`, `BacktestRunner`, `BacktestConfig`, `Signal`, `SignalDirection`, `StrategyBook`, `PerformanceAnalytics`, `StrategyConfig`

**Acceptance:** `from neon.lib.qis import BacktestRunner, StrategyConfig` works

---

### A-checkpoint verification
```bash
uv run pytest tests/lib/qis/ -v
uv run pytest                   # no regressions
uv run ruff check .
```

---

## Checkpoint B: Equity Momentum

### B1 — `strategies/momentum.py` + `configs/momentum.yaml` + `test_momentum.py`
**Files:** `src/neon/lib/qis/strategies/momentum.py`, `src/neon/lib/qis/configs/momentum.yaml`, `tests/lib/qis/strategies/test_momentum.py`

Cross-sectional 12-1 month momentum. All parameters come from `StrategyConfig`.

**Config shape:**
```yaml
module: neon.lib.qis.strategies.momentum
class: MomentumStrategy
universe: [SPY, QQQ, IWM, EFA, TLT, GLD, XLF, XLE]
lookback_months: 12
skip_months: 1
rebalance_frequency: monthly
n_longs: 3
n_shorts: 3
```

**Acceptance:**
- `StrategyConfig.load("configs/momentum.yaml").build_strategy()` returns a `MomentumStrategy`
- On first rebalance, signals are only `Long` or `Short`
- 252-day synthetic run: `sharpe_ratio()` is a finite float; `hit_rate()` in `[0, 1]`
- Fewer tickers than `n_longs + n_shorts` does not crash
- Config param `n_longs` overrides default behavior

**Verify:** `uv run pytest tests/lib/qis/strategies/test_momentum.py`

---

### B-checkpoint verification
```bash
uv run pytest tests/lib/qis/ -v
uv run ruff check .
```

---

## Checkpoint C: Fixed Income Carry/Roll

### C1 — `strategies/carry_roll.py` + `configs/carry_roll.yaml` + `test_carry_roll.py`
**Files:** `src/neon/lib/qis/strategies/carry_roll.py`, `src/neon/lib/qis/configs/carry_roll.yaml`, `tests/lib/qis/strategies/test_carry_roll.py`

Yield curve carry + roll-down. Bonds placed as `Position(bond, qty)` duck-typed.

**Config shape:**
```yaml
module: neon.lib.qis.strategies.carry_roll
class: CarryRollStrategy
tenors: [2, 5, 10, 30]
roll_weight: 0.5
rebalance_frequency: weekly
```

**Acceptance:**
- `StrategyConfig.load("configs/carry_roll.yaml").build_strategy()` returns a `CarryRollStrategy`
- `RiskEngine(book.portfolio).bond_risk(date, ytms_dict)` does not raise
- Positive carry PnL over 60 synthetic days with upward-sloping yield curve
- `roll_weight` from config changes the combined score

**Verify:** `uv run pytest tests/lib/qis/strategies/test_carry_roll.py`

---

### C-checkpoint verification
```bash
uv run pytest tests/lib/qis/ -v
uv run ruff check .
```

---

## Checkpoint D: Options Delta Hedge

### D1 — `strategies/delta_hedge.py` + `configs/delta_hedge.yaml` + `test_delta_hedge.py`
**Files:** `src/neon/lib/qis/strategies/delta_hedge.py`, `src/neon/lib/qis/configs/delta_hedge.yaml`, `tests/lib/qis/strategies/test_delta_hedge.py`

ATM straddle + daily delta re-hedge.

**Config shape:**
```yaml
module: neon.lib.qis.strategies.delta_hedge
class: DeltaHedgeStrategy
ticker: SPY
delta_threshold: 0.05
expiry_days_min: 30
expiry_days_max: 60
```

**Acceptance:**
- `StrategyConfig.load("configs/delta_hedge.yaml").build_strategy()` returns a `DeltaHedgeStrategy`
- After signal execution: `abs(net_delta) < delta_threshold * mark_to_market()`
- `DaySnapshot.net_delta` is finite float for options positions
- `delta_series()` has no NaN for an options-only run
- `delta_threshold` from config controls rebalance trigger

**Verify:** `uv run pytest tests/lib/qis/strategies/test_delta_hedge.py`

---

### D-checkpoint verification
```bash
uv run pytest tests/lib/qis/ -v
uv run ruff check .
```

---

## Checkpoint E: Volatility Arb

### E1 — `strategies/vol_arb.py` + `configs/vol_arb.yaml` + `test_vol_arb.py`
**Files:** `src/neon/lib/qis/strategies/vol_arb.py`, `src/neon/lib/qis/configs/vol_arb.yaml`, `tests/lib/qis/strategies/test_vol_arb.py`

Realized vs implied vol spread signal.

**Config shape:**
```yaml
module: neon.lib.qis.strategies.vol_arb
class: VolArbStrategy
ticker: SPY
realized_vol_window: 21
signal_threshold: 0.10
```

**Acceptance:**
- `StrategyConfig.load("configs/vol_arb.yaml").build_strategy()` returns a `VolArbStrategy`
- `realized > implied * (1 + threshold)` → signal is `Long`
- `implied > realized * (1 + threshold)` → signal is `Short`
- `vega_series()` positive on long-straddle days, negative on short-straddle days
- `realized_vol_window` and `signal_threshold` from config control behavior

**Verify:** `uv run pytest tests/lib/qis/strategies/test_vol_arb.py`

---

### Final verification (all checkpoints)
```bash
uv run pytest tests/lib/qis/ -v
uv run pytest                     # full suite regression
uv run ruff check .
uv run ruff format .
```

End-to-end smoke:
```python
from neon.lib.qis import StrategyConfig, BacktestRunner, BacktestConfig
cfg = StrategyConfig.load("src/neon/lib/qis/configs/momentum.yaml")
strategy = cfg.build_strategy()
runner = BacktestRunner(strategy, BacktestConfig("20230101","20231231",100_000), market_data)
summary = runner.run().summary()
assert isinstance(summary["sharpe_ratio"], float)
```
