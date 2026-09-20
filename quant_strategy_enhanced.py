"""
增强版量化策略 —— 双均线 + ADX趋势过滤 + ATR止损

相比基础版的增强:
  1. ADX 趋势过滤: ADX < 20 视为震荡市, 不开仓 (过滤假突破)
  2. ATR 动态止损: 买入后跌破 (入场价 - 2*ATR) 强制止损
  3. 死叉卖出保留, 作为止盈/趋势反转退出

不依赖第三方回测框架, 全部手写.
"""

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ======================== 策略参数 ========================
INIT_CAPITAL = 1_000_000.0
MA_SHORT = 20
MA_LONG = 40
ADX_PERIOD = 14
ADX_THRESHOLD = 20          # ADX >= 20 才允许开仓
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0         # 止损 = 入场价 - ATR_STOP_MULT * ATR
COMMISSION_RATE = 0.0003
SLIPPAGE_RATE = 0.001
STAMP_TAX_RATE = 0.0005
DATA_PATH = "/workspace/600519_daily.csv"


# ======================== 1. 数据加载 + 指标计算 ========================
def calc_adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.DataFrame:
    """计算 ADX 趋势强度指标"""
    high, low, close = df["high"], df["low"], df["close"]
    # 真实波幅 TR
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    # 方向运动 DM
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    plus_di = 100 * plus_dm.rolling(period).mean() / atr
    minus_di = 100 * minus_dm.rolling(period).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.rolling(period).mean()

    df["atr"] = atr
    df["plus_di"] = plus_di
    df["minus_di"] = minus_di
    df["adx"] = adx
    return df


def load_data(path: str, ma_short: int = MA_SHORT, ma_long: int = MA_LONG) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ma_short"] = df["close"].rolling(ma_short).mean()
    df["ma_long"] = df["close"].rolling(ma_long).mean()
    df = calc_adx(df)  # 新增: ADX + ATR
    return df


# ======================== 2. 信号生成 (双均线 + ADX过滤) ========================
def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    增强信号规则:
      买入条件: MA短 上穿 MA长  AND  ADX >= ADX_THRESHOLD (趋势明确)
      卖出条件: MA短 下穿 MA长 (趋势反转止盈)
    注: ATR止损在回测引擎里实时判断, 不在此信号列体现
    """
    df = df.copy()
    # 基础趋势持仓状态 (仅看均线)
    ma_above = (df["ma_short"] > df["ma_long"]).astype(int)
    # ADX 是否达标
    adx_ok = (df["adx"] >= ADX_THRESHOLD).astype(int)

    # 目标仓位: 均线多头 + ADX达标 -> 持仓, 否则空仓
    df["position_target"] = (ma_above & adx_ok).astype(int)

    # 信号变化点
    df["signal"] = df["position_target"].diff().fillna(0).astype(int)

    # 记录买入信号当天的 ATR, 供止损使用
    df["entry_atr"] = np.where(df["signal"] == 1, df["atr"], np.nan)
    return df


# ======================== 3. 回测引擎 (含 ATR 止损) ========================
def backtest(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    cash = np.zeros(n)
    shares = np.zeros(n)
    total = np.zeros(n)
    stop_price = np.zeros(n)       # 止损价
    stop_triggered = np.zeros(n)   # 当日是否触发止损
    entry_price_rec = np.zeros(n)  # 记录入场价

    cash[0] = INIT_CAPITAL
    shares[0] = 0.0
    total[0] = INIT_CAPITAL

    for i in range(1, n):
        cash[i] = cash[i - 1]
        shares[i] = shares[i - 1]
        stop_price[i] = stop_price[i - 1]
        entry_price_rec[i] = entry_price_rec[i - 1]

        price_open = df["open"].iloc[i]
        price_close = df["close"].iloc[i]
        sig = df["signal"].iloc[i - 1]

        # ---- 先检查止损 (持仓中, 当日开盘或盘中跌破止损价) ----
        if shares[i] > 0 and stop_price[i] > 0:
            # 用开盘价判断: 若开盘已跌破止损, 则开盘止损
            if price_open <= stop_price[i]:
                sell_value = shares[i] * price_open * (1 - SLIPPAGE_RATE)
                commission = sell_value * COMMISSION_RATE
                stamp_tax = sell_value * STAMP_TAX_RATE
                cash[i] += sell_value - commission - stamp_tax
                shares[i] = 0.0
                stop_price[i] = 0
                stop_triggered[i] = 1
                entry_price_rec[i] = 0

        # ---- 执行策略信号 (若止损未触发) ----
        if shares[i] == 0 and sig == 1:
            buy_amount = cash[i] / (1 + COMMISSION_RATE + SLIPPAGE_RATE)
            shares_buy = int(buy_amount / (price_open * (1 + SLIPPAGE_RATE)) / 100) * 100
            if shares_buy > 0:
                cost = shares_buy * price_open * (1 + SLIPPAGE_RATE)
                commission = cost * COMMISSION_RATE
                cash[i] -= (cost + commission)
                shares[i] += shares_buy
                entry_price_rec[i] = price_open
                # 止损价 = 入场价 - 2 * ATR (用买入信号日的ATR)
                atr_at_entry = df["atr"].iloc[i - 1]
                stop_price[i] = price_open - ATR_STOP_MULT * atr_at_entry

        elif shares[i] > 0 and sig == -1:
            # 死叉卖出
            sell_value = shares[i] * price_open * (1 - SLIPPAGE_RATE)
            commission = sell_value * COMMISSION_RATE
            stamp_tax = sell_value * STAMP_TAX_RATE
            cash[i] += sell_value - commission - stamp_tax
            shares[i] = 0.0
            stop_price[i] = 0
            entry_price_rec[i] = 0

        total[i] = cash[i] + shares[i] * price_close

    df["cash"] = cash
    df["shares"] = shares
    df["total_asset"] = total
    df["stop_price"] = stop_price
    df["stop_triggered"] = stop_triggered
    df["entry_price"] = entry_price_rec
    df["strategy_return"] = df["total_asset"].pct_change().fillna(0.0)
    df["benchmark_return"] = df["close"].pct_change().fillna(0.0)
    df["strategy_nav"] = df["total_asset"] / INIT_CAPITAL
    df["benchmark_nav"] = df["close"] / df["close"].iloc[0]
    return df


# ======================== 4. 绩效评估 ========================
def calc_metrics(df: pd.DataFrame) -> dict:
    strat = df["strategy_return"].values
    days = len(df)
    total_ret = df["strategy_nav"].iloc[-1] - 1
    bench_total_ret = df["benchmark_nav"].iloc[-1] - 1
    ann_ret = (1 + total_ret) ** (252 / days) - 1
    bench_ann_ret = (1 + bench_total_ret) ** (252 / days) - 1
    ann_vol = np.std(strat, ddof=1) * np.sqrt(252)
    rf = 0.03
    sharpe = (ann_ret - rf) / ann_vol if ann_vol > 0 else 0.0
    nav = df["strategy_nav"].values
    running_max = np.maximum.accumulate(nav)
    drawdown = (nav - running_max) / running_max
    max_dd = drawdown.min()
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0.0

    # 交易统计
    trades = []
    in_pos = False
    entry_price = 0.0
    for i in range(len(df)):
        sig = df["signal"].iloc[i]
        if sig == 1 and not in_pos:
            entry_price = df["open"].iloc[i + 1] if i + 1 < len(df) else df["close"].iloc[i]
            in_pos = True
        elif (sig == -1 or df["stop_triggered"].iloc[i] == 1) and in_pos:
            exit_idx = i + 1 if i + 1 < len(df) else i
            exit_price = df["open"].iloc[exit_idx] if df["signal"].iloc[i] == -1 else df["open"].iloc[i]
            # 止损用当日开盘价
            if df["stop_triggered"].iloc[i] == 1:
                exit_price = df["open"].iloc[i]
            ret = exit_price / entry_price - 1
            trades.append(ret)
            in_pos = False

    win_trades = [t for t in trades if t > 0]
    lose_trades = [t for t in trades if t <= 0]
    win_rate = len(win_trades) / len(trades) if trades else 0.0
    avg_win = np.mean(win_trades) if win_trades else 0.0
    avg_lose = abs(np.mean(lose_trades)) if lose_trades else 0.0
    profit_loss_ratio = avg_win / avg_lose if avg_lose > 0 else float("inf")

    # 统计止损触发次数
    stop_count = int(df["stop_triggered"].sum())

    return {
        "回测区间": f"{df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}",
        "交易日数": days,
        "初始资金": f"{INIT_CAPITAL:,.0f}",
        "期末资产": f"{df['total_asset'].iloc[-1]:,.2f}",
        "策略总收益": f"{total_ret*100:.2f}%",
        "基准总收益": f"{bench_total_ret*100:.2f}%",
        "策略年化": f"{ann_ret*100:.2f}%",
        "基准年化": f"{bench_ann_ret*100:.2f}%",
        "年化波动": f"{ann_vol*100:.2f}%",
        "夏普比率": f"{sharpe:.2f}",
        "最大回撤": f"{max_dd*100:.2f}%",
        "Calmar": f"{calmar:.2f}",
        "交易次数": len(trades),
        "止损次数": stop_count,
        "胜率": f"{win_rate*100:.1f}%",
        "平均盈利": f"{avg_win*100:.2f}%",
        "平均亏损": f"{avg_lose*100:.2f}%",
        "盈亏比": f"{profit_loss_ratio:.2f}",
    }


# ======================== 5. 可视化 ========================
def plot_result(df: pd.DataFrame, ma_short=MA_SHORT, ma_long=MA_LONG,
                out_path: str = "/workspace/backtest_enhanced.png"):
    fig, axes = plt.subplots(4, 1, figsize=(14, 15),
                             gridspec_kw={"height_ratios": [3, 1, 1, 1]})

    # 子图1: 价格 + 均线 + 买卖点 + 止损线
    ax = axes[0]
    ax.plot(df["date"], df["close"], label="Close", color="#333", linewidth=1.2)
    if "ma_short" in df.columns:
        ax.plot(df["date"], df["ma_short"], label=f"MA{ma_short}", color="#1f77b4", linewidth=1)
    if "ma_long" in df.columns:
        ax.plot(df["date"], df["ma_long"], label=f"MA{ma_long}", color="#ff7f0e", linewidth=1)
    if "signal" in df.columns:
        buy = df[df["signal"] == 1]
        sell = df[df["signal"] == -1]
        ax.scatter(buy["date"], buy["close"], marker="^", color="red", s=80, zorder=5, label="Buy")
        ax.scatter(sell["date"], sell["close"], marker="v", color="green", s=80, zorder=5, label="Sell")
    # 止损点
    stops = df[df["stop_triggered"] == 1]
    if len(stops) > 0:
        ax.scatter(stops["date"], stops["open"], marker="x", color="purple", s=100, zorder=6, label="Stop Loss")
    ax.set_title(f"Enhanced Strategy: Dual MA({ma_short}/{ma_long}) + ADX filter + ATR stop", fontsize=13, fontweight="bold")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)

    # 子图2: ADX
    ax = axes[1]
    if "adx" in df.columns:
        ax.plot(df["date"], df["adx"], color="#9467bd", linewidth=1, label="ADX")
        ax.axhline(ADX_THRESHOLD, color="red", linestyle="--", linewidth=0.8, label=f"ADX={ADX_THRESHOLD}")
    ax.set_ylabel("ADX")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)

    # 子图3: 净值
    ax = axes[2]
    if "strategy_nav" in df.columns:
        ax.plot(df["date"], df["strategy_nav"], label="Strategy", color="#d62728", linewidth=1.5)
    if "benchmark_nav" in df.columns:
        ax.plot(df["date"], df["benchmark_nav"], label="Benchmark", color="#7f7f7f", linewidth=1.2, linestyle="--")
    ax.set_ylabel("Net Value")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)

    # 子图4: 回撤
    ax = axes[3]
    if "strategy_nav" in df.columns:
        nav = df["strategy_nav"].values
        running_max = np.maximum.accumulate(nav)
        drawdown = (nav - running_max) / running_max
        ax.fill_between(df["date"], drawdown, 0, color="#d62728", alpha=0.4)
        ax.plot(df["date"], drawdown, color="#d62728", linewidth=0.8)
    ax.set_ylabel("Drawdown")
    ax.set_xlabel("Date")
    ax.grid(alpha=0.3)

    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)

    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()
    return out_path


# ======================== 主流程 ========================
def main():
    print("=" * 60)
    print("  增强版策略: 双均线 + ADX过滤 + ATR止损")
    print(f"  MA={MA_SHORT}/{MA_LONG}  ADX阈值={ADX_THRESHOLD}  ATR止损={ATR_STOP_MULT}倍")
    print("=" * 60)

    df = load_data(DATA_PATH)
    df = generate_signals(df)
    df = backtest(df)
    metrics = calc_metrics(df)

    print()
    for k, v in metrics.items():
        print(f"  {k:>12s}: {v}")
    print("=" * 60)

    img = plot_result(df)
    print(f"\n图表已保存: {img}")


if __name__ == "__main__":
    main()
