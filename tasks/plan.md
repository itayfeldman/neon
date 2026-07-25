# QIS Backtesting System — Phase 6 Plan

## What we're building

A new `src/neon/lib/qis/` module that runs systematic quantitative investment strategies over historical data. The system is event-driven (date-by-date), config-driven (YAML names the strategy module to load), and produces full performance analytics (PnL, Sharpe, drawdown, Greeks exposure).

## What already exists (reused unchanged)

| Module | Role in QIS |
|---|---|
| `portfolio/Portfolio`, `portfolio/Position` | Book holds positions via these |
| `risk/RiskEngine` | Greeks aggregation at each simulation step |
| `instruments/EuropeanOption`, `greeks/AnalyticalGreeks` | Options strategies |
| `fixed_income/Bond`, `BondAnalytics`, `DiscountCurve` | Fixed income strategy |
| `instruments/Cash` | Cash holdings |
| `data/YahooFinanceAdapter`, `USTreasuryAdapter`, `FREDAdapter` | Market data |
| `core/TimeSteps.Daily` (252) | Sharpe annualization |
| `core/DATE_FORMAT` ("%Y%m%d") | All QIS date strings |

**Key finding:** `Bond` is already duck-typed directly into `Position.instrument` in existing tests — no `BondInstrument` wrapper is needed.

## Layer cake (extended)

```
qis → risk → portfolio → instruments → greeks → core
qis → fixed_income → datetime → core
qis → data (adapters + Parquet cache)
```

No new Python dependencies. `pd.bdate_range` (pandas) drives the date loop. `importlib` (stdlib) handles dynamic strategy loading.

---

## Module layout

```
src/neon/lib/qis/
├── __init__.py            exports: Strategy, BacktestRunner, BacktestConfig,
│                                   Signal, SignalDirection, StrategyBook,
│                                   PerformanceAnalytics, StrategyConfig
├── config.py              StrategyConfig — loads YAML, exposes params, dynamic import
├── signal.py              Signal (frozen dataclass), SignalDirection (IntEnum +1/0/-1)
├── book.py                StrategyBook — cash + Portfolio aggregate
├── strategy.py            Strategy ABC (initialize, on_date, on_expiry hook)
├── backtest.py            BacktestRunner, BacktestConfig, DaySnapshot
├── analytics.py           PerformanceAnalytics (all metrics)
├── configs/               YAML config files — one per strategy
│   ├── momentum.yaml
│   ├── carry_roll.yaml
│   ├── delta_hedge.yaml
│   └── vol_arb.yaml
└── strategies/            Strategy implementations — one .py per strategy
    ├── __init__.py
    ├── momentum.py
    ├── carry_roll.py
    ├── delta_hedge.py
    └── vol_arb.py

tests/lib/qis/
├── __init__.py
├── test_config.py
├── test_signal.py
├── test_book.py
├── test_backtest.py
├── test_analytics.py
└── strategies/
    ├── __init__.py
    ├── test_momentum.py
    ├── test_carry_roll.py
    ├── test_delta_hedge.py
    └── test_vol_arb.py
```

---

## Config-driven strategy loading

Each YAML config identifies the strategy module and class, plus all tunable parameters. The runner uses `importlib` to dynamically load the class — no registry needed.

### Example: `configs/momentum.yaml`
```yaml
module: neon.lib.qis.strategies.momentum
class: MomentumStrategy
universe: [SPY, QQQ, IWM, EFA, TLT, GLD, XLF, XLE]
lookback_months: 12
skip_months: 1
rebalance_frequency: monthly   # daily | weekly | monthly
n_longs: 3
n_shorts: 3
```

### Example: `configs/delta_hedge.yaml`
```yaml
module: neon.lib.qis.strategies.delta_hedge
class: DeltaHedgeStrategy
ticker: SPY
delta_threshold: 0.05
expiry_days_min: 30
expiry_days_max: 60
```

### `config.py`
```python
@dataclass(frozen=True)
class StrategyConfig:
    module: str           # dotted import path
    class_name: str       # class inside that module
    params: dict[str, Any]  # all remaining YAML keys

    @classmethod
    def load(cls, path: str) -> "StrategyConfig": ...
    # reads YAML, pops 'module' and 'class', puts rest in params

    def build_strategy(self) -> "Strategy":
        # importlib.import_module(self.module)
        # getattr(module, self.class_name)(self)
        ...
```

Strategy constructors accept `StrategyConfig` as their only argument and read parameters from `config.params`.

### Usage pattern
```python
cfg = StrategyConfig.load("src/neon/lib/qis/configs/momentum.yaml")
strategy = cfg.build_strategy()       # dynamically loads MomentumStrategy(cfg)
runner = BacktestRunner(strategy, backtest_cfg, market_data)
analytics = runner.run()
```

---

## Key design decisions

**Config names the module.** YAML `module` + `class` fields drive dynamic import via `importlib`. Adding a new strategy requires only: a new `.py` in `strategies/` and a new `.yaml` in `configs/`. No registry to update.

**`StrategyConfig` is passed to the strategy constructor.** Strategies read all tunable params from `config.params["lookback_months"]` etc. This keeps constructors uniform and makes parameter sweeps trivial (swap one config).

**`target_notional` not `quantity` on Signal.** Strategies think in dollars. The runner converts to quantity using current mark price. Decouples signal logic from lot sizes.

**`market_data` pre-loaded once.** Full DataFrames passed to `initialize` and `on_date`. Strategies slice by `df[df["date"] <= date]` to avoid look-ahead bias.

**`on_expiry` hook.** Separate from `on_date` so options roll logic isn't scattered in every strategy's date check. Default returns `[]`.

**`StrategyBook` wraps, not subclasses, `Portfolio`.** Portfolio is a mutable dataclass with no cash concept. Because `Position` is `frozen=True`, resizing means remove + add new.

**`PerformanceAnalytics` takes `list[DaySnapshot]`.** Analytics are computable from the persisted record without re-running.

---

## Interfaces (signatures only)

### config.py
```python
@dataclass(frozen=True)
class StrategyConfig:
    module: str
    class_name: str
    params: dict[str, Any]

    @classmethod
    def load(cls, path: str) -> "StrategyConfig": ...
    def build_strategy(self) -> "Strategy": ...
    def get(self, key: str, default: Any = None) -> Any: ...
```

### signal.py
```python
class SignalDirection(IntEnum):  Long=1, Flat=0, Short=-1

@dataclass(frozen=True, slots=True)
class Signal:
    date: str; ticker: str; direction: SignalDirection
    target_notional: float; confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
```

### book.py
```python
@dataclass
class StrategyBook:
    name: str; cash: float
    portfolio: Portfolio = field(default_factory=...)
    def open_position(self, instrument, quantity, price) -> None
    def close_position(self, ticker, price) -> None
    def update_position(self, ticker, new_quantity, price) -> None
    def mark_to_market(self) -> float        # portfolio.value() + cash
    def position_quantity(self, ticker) -> float
    def tickers(self) -> list[str]
```

### strategy.py
```python
class Strategy(ABC):
    def __init__(self, config: StrategyConfig) -> None: ...  # stores config

    @property @abstractmethod def name(self) -> str
    @abstractmethod def initialize(self, book, market_data) -> None
    @abstractmethod def on_date(self, date, book, market_data) -> list[Signal]
    def on_expiry(self, date, book, market_data) -> list[Signal]: return []
```

### backtest.py
```python
@dataclass class BacktestConfig:
    start_date: str; end_date: str; initial_capital: float
    trading_cost_bps: float = 0.0

@dataclass class DaySnapshot:
    date: str; nav: float; cash: float
    daily_pnl: float; cumulative_pnl: float; signals: list[Signal]
    net_delta: float|None; net_vega: float|None; net_gamma: float|None

class BacktestRunner:
    def __init__(self, strategy, config, market_data): ...
    def run(self) -> PerformanceAnalytics: ...
    def _business_days(self) -> Iterator[str]: ...   # pd.bdate_range
    def _execute_signals(self, signals, book, date) -> float: ...
    def _compute_greeks(self, book) -> tuple[float|None, float|None, float|None]: ...
```

### analytics.py
```python
@dataclass class PerformanceAnalytics:
    snapshots: list[DaySnapshot]
    def cumulative_pnl(self) -> pd.Series
    def daily_returns(self) -> pd.Series
    def nav_series(self) -> pd.Series
    def sharpe_ratio(self, risk_free_rate=0.0, time_steps=TimeSteps.Daily) -> float
    def max_drawdown(self) -> float
    def max_drawdown_period(self) -> tuple[str, str]
    def calmar_ratio(self) -> float
    def sortino_ratio(self, risk_free_rate=0.0) -> float
    def hit_rate(self) -> float
    def delta_series(self) -> pd.Series
    def vega_series(self) -> pd.Series
    def gamma_series(self) -> pd.Series
    def summary(self) -> dict[str, float]
```

---

## Strategy YAML configs

### `configs/momentum.yaml`
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

### `configs/carry_roll.yaml`
```yaml
module: neon.lib.qis.strategies.carry_roll
class: CarryRollStrategy
tenors: [2, 5, 10, 30]
roll_weight: 0.5
rebalance_frequency: weekly
```

### `configs/delta_hedge.yaml`
```yaml
module: neon.lib.qis.strategies.delta_hedge
class: DeltaHedgeStrategy
ticker: SPY
delta_threshold: 0.05
expiry_days_min: 30
expiry_days_max: 60
```

### `configs/vol_arb.yaml`
```yaml
module: neon.lib.qis.strategies.vol_arb
class: VolArbStrategy
ticker: SPY
realized_vol_window: 21
signal_threshold: 0.10
```

---

## Implementation order & checkpoints

### Checkpoint A — Core primitives
1. `config.py` + `test_config.py` — YAML load, dynamic import, `build_strategy()`
2. `signal.py` + `test_signal.py`
3. `book.py` + `test_book.py`
4. `strategy.py` — ABC, receives `StrategyConfig`
5. `backtest.py` + `test_backtest.py` — NoOp strategy, date loop
6. `analytics.py` + `test_analytics.py`
7. `__init__.py`

After A: `StrategyConfig.load("configs/x.yaml").build_strategy()` works end-to-end.

### Checkpoint B — Equity Momentum
8. `strategies/momentum.py` + `configs/momentum.yaml` + `test_momentum.py`

### Checkpoint C — Fixed Income Carry/Roll
9. `strategies/carry_roll.py` + `configs/carry_roll.yaml` + `test_carry_roll.py`

### Checkpoint D — Options Delta Hedge
10. `strategies/delta_hedge.py` + `configs/delta_hedge.yaml` + `test_delta_hedge.py`

### Checkpoint E — Vol Arb
11. `strategies/vol_arb.py` + `configs/vol_arb.yaml` + `test_vol_arb.py`

---

## Verification

```bash
uv run pytest tests/lib/qis/ -v   # all QIS tests
uv run pytest                      # full suite, no regressions
uv run ruff check .
uv run ruff format .
```

End-to-end smoke:
```python
cfg = StrategyConfig.load("src/neon/lib/qis/configs/momentum.yaml")
strategy = cfg.build_strategy()
runner = BacktestRunner(strategy, BacktestConfig("20230101","20231231",100_000), market_data)
assert isinstance(runner.run().summary()["sharpe_ratio"], float)
```
