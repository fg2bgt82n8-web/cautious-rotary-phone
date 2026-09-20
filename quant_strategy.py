"""
手搓量化策略 —— 双均线趋势跟踪策略 (Dual Moving Average Crossover)

实现说明:
  - 不依赖 backtrader / vnpy 等第三方回测框架, 全部逻辑手写
  - 策略: 短期均线(MA_short) 上穿 长期均线(MA_long) 买入; 下穿卖出
  - 回测: 按日撮合, 次日开盘价成交, 考虑手续费与滑点
  - 评估: 年化收益 / 夏普 / 最大回撤 / 胜率 / 盈亏比 / Calmar
  - 输出: 控制台绩效报告 + 净值曲线图 (PNG)

数据来源: 贵州茅台(600519) 日K, 前复权, 600 个交易日
"""

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # 无界面环境
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ======================== 策略参数 ========================
INIT_CAPITAL = 1_000_000.0      # 初始资金 100 万
MA_SHORT = 20                   # 短期均线周期
MA_LONG = 60                    # 长期均线周期
COMMISSION_RATE = 0.0003        # 单边手续费 万分之三 (0.03%)
SLIPPAGE_RATE = 0.001           # 滑点 千分之一 (0.1%)
STAMP_TAX_RATE = 0.0005         # 卖出印花税 万分之五 (仅卖出)
DATA_PATH = "/workspace/600519_daily.csv"


# ======================== 1. 数据加载 ========================
def load_data(path: str, ma_short: int = MA_SHORT, ma_long: int = MA_LONG) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    # 计算均线 (参数化, 便于网格搜索)
    df["ma_short"] = df["close"].rolling(ma_short).mean()
    df["ma_long"] = df["close"].rolling(ma_long).mean()
    return df


# ======================== 2. 信号生成 ========================
def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    信号规则:
      signal = 1  表示金叉后持仓状态
      signal = 0  表示空仓
    用均线的相对位置决定当日收盘后的目标仓位, 次日开盘执行.
    """
    df = df.copy()
    # 短均线 > 长均线 -> 持仓 (1), 否则空仓 (0)
    df["position_target"] = (df["ma_short"] > df["ma_long"]).astype(int)
    # 信号变化点: 0->1 买入, 1->0 卖出
    df["signal"] = df["position_target"].diff().fillna(0).astype(int)
    return df


# ======================== 3. 回测引擎 ========================
def backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    逐日撮合回测.
    - 当日产生信号 signal, 次日开盘成交 (避免未来函数)
    - 全仓买卖 (满仓 / 空仓), 手续费 + 滑点 + 印花税(卖出)
    - 记录每日持仓市值、现金、总资产、收益率
    """
    n = len(df)
    cash = np.zeros(n)
    shares = np.zeros(n)
    total = np.zeros(n)

    cash[0] = INIT_CAPITAL
    shares[0] = 0.0
    total[0] = INIT_CAPITAL

    # 逐根K线推进
    for i in range(1, n):
        # 继承上一日的状态
        cash[i] = cash[i - 1]
        shares[i] = shares[i - 1]

        # 当日信号 (前一日收盘后产生的目标仓位变化)
        sig = df["signal"].iloc[i - 1]
        price = df["open"].iloc[i]  # 次日开盘成交

        if sig == 1:  # 买入: 全仓
            # 可买金额 = 现金 * (1 - 滑点) , 扣除手续费后能买的股数
            buy_amount = cash[i] / (1 + COMMISSION_RATE + SLIPPAGE_RATE)
            shares_buy = int(buy_amount / (price * (1 + SLIPPAGE_RATE)) / 100) * 100
            if shares_buy > 0:
                cost = shares_buy * price * (1 + SLIPPAGE_RATE)
                commission = cost * COMMISSION_RATE
                cash[i] -= (cost + commission)
                shares[i] += shares_buy

        elif sig == -1:  # 卖出: 清仓
            if shares[i] > 0:
                sell_value = shares[i] * price * (1 - SLIPPAGE_RATE)
                commission = sell_value * COMMISSION_RATE
                stamp_tax = sell_value * STAMP_TAX_RATE
                cash[i] += sell_value - commission - stamp_tax
                shares[i] = 0.0

        # 当日总资产 = 现金 + 持仓市值 (按收盘价计)
        total[i] = cash[i] + shares[i] * df["close"].iloc[i]

    df["cash"] = cash
    df["shares"] = shares
    df["total_asset"] = total
    df["strategy_return"] = df["total_asset"].pct_change().fillna(0.0)
    df["benchmark_return"] = df["close"].pct_change().fillna(0.0)
    df["strategy_nav"] = df["total_asset"] / INIT_CAPITAL
    df["benchmark_nav"] = df["close"] / df["close"].iloc[0]
    return df


# ======================== 4. 绩效评估 ========================
def calc_metrics(df: pd.DataFrame) -> dict:
    strat = df["strategy_return"].values
    bench = df["benchmark_return"].values
    days = len(df)

    total_ret = df["strategy_nav"].iloc[-1] - 1
    bench_total_ret = df["benchmark_nav"].iloc[-1] - 1

    # 年化 (按 252 交易日)
    ann_ret = (1 + total_ret) ** (252 / days) - 1
    bench_ann_ret = (1 + bench_total_ret) ** (252 / days) - 1

    # 年化波动率
    ann_vol = np.std(strat, ddof=1) * np.sqrt(252)

    # 夏普比率 (无风险利率取 3%)
    rf = 0.03
    sharpe = (ann_ret - rf) / ann_vol if ann_vol > 0 else 0.0

    # 最大回撤
    nav = df["strategy_nav"].values
    running_max = np.maximum.accumulate(nav)
    drawdown = (nav - running_max) / running_max
    max_dd = drawdown.min()
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0.0

    # 交易统计: 找出每笔完整交易 (买入到卖出)
    trades = []
    in_pos = False
    entry_price = 0.0
    for i in range(len(df)):
        sig = df["signal"].iloc[i]
        if sig == 1 and not in_pos:
            entry_price = df["open"].iloc[i + 1] if i + 1 < len(df) else df["close"].iloc[i]
            in_pos = True
        elif sig == -1 and in_pos:
            exit_price = df["open"].iloc[i + 1] if i + 1 < len(df) else df["close"].iloc[i]
            ret = exit_price / entry_price - 1
            trades.append(ret)
            in_pos = False

    win_trades = [t for t in trades if t > 0]
    lose_trades = [t for t in trades if t <= 0]
    win_rate = len(win_trades) / len(trades) if trades else 0.0
    avg_win = np.mean(win_trades) if win_trades else 0.0
    avg_lose = abs(np.mean(lose_trades)) if lose_trades else 0.0
    profit_loss_ratio = avg_win / avg_lose if avg_lose > 0 else float("inf")

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
        "胜率": f"{win_rate*100:.1f}%",
        "平均盈利": f"{avg_win*100:.2f}%",
        "平均亏损": f"{avg_lose*100:.2f}%",
        "盈亏比": f"{profit_loss_ratio:.2f}",
    }


# ======================== 5. 可视化 ========================
def plot_result(df: pd.DataFrame, ma_short: int = MA_SHORT, ma_long: int = MA_LONG,
                out_path: str = "/workspace/backtest_result.png"):
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), gridspec_kw={"height_ratios": [3, 1, 1]})

    # ---- 子图1: 价格 + 均线 + 买卖点 ----
    ax = axes[0]
    ax.plot(df["date"], df["close"], label="Close", color="#333", linewidth=1.2)
    # 防御式: 均线列存在才绘制
    if "ma_short" in df.columns:
        ax.plot(df["date"], df["ma_short"], label=f"MA{ma_short}", color="#1f77b4", linewidth=1)
    if "ma_long" in df.columns:
        ax.plot(df["date"], df["ma_long"], label=f"MA{ma_long}", color="#ff7f0e", linewidth=1)

    # 买卖点 (信号日次日开盘成交, 标注在信号日)
    if "signal" in df.columns:
        buy = df[df["signal"] == 1]
        sell = df[df["signal"] == -1]
        ax.scatter(buy["date"], buy["close"], marker="^", color="red", s=80, zorder=5, label="Buy")
        ax.scatter(sell["date"], sell["close"], marker="v", color="green", s=80, zorder=5, label="Sell")
    ax.set_title(f"600519 Kweichow Moutai - Dual MA({ma_short}/{ma_long}) Backtest", fontsize=14, fontweight="bold")
    ax.set_ylabel("Price (CNY)")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)

    # ---- 子图2: 净值曲线 (策略 vs 基准) ----
    ax = axes[1]
    if "strategy_nav" in df.columns:
        ax.plot(df["date"], df["strategy_nav"], label="Strategy", color="#d62728", linewidth=1.5)
    if "benchmark_nav" in df.columns:
        ax.plot(df["date"], df["benchmark_nav"], label="Benchmark(Buy&Hold)", color="#7f7f7f", linewidth=1.2, linestyle="--")
    ax.set_ylabel("Net Value")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)

    # ---- 子图3: 回撤 ----
    ax = axes[2]
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


# ======================== 6. 单次回测 (供网格搜索调用) ========================
def run_single_backtest(ma_short: int, ma_long: int) -> tuple[dict, pd.DataFrame]:
    """对指定均线周期运行完整回测, 返回 (指标字典, 回测DataFrame)"""
    df = load_data(DATA_PATH, ma_short=ma_short, ma_long=ma_long)
    df = generate_signals(df)
    df = backtest(df)
    metrics = calc_metrics(df)
    return metrics, df


# ======================== 7. 参数网格搜索 ========================
def grid_search(short_range: list[int], long_range: list[int]) -> pd.DataFrame:
    """
    遍历所有 (短周期, 长周期) 组合, 返回按夏普比率排序的结果表.
    要求: 短周期 < 长周期.
    """
    results = []
    for s in short_range:
        for l in long_range:
            if s >= l:
                continue
            metrics, _ = run_single_backtest(s, l)
            # 提取数值型指标用于排序
            results.append({
                "ma_short": s,
                "ma_long": l,
                "总收益%": float(metrics["策略总收益"].replace("%", "")),
                "年化%": float(metrics["策略年化"].replace("%", "")),
                "夏普": float(metrics["夏普比率"]),
                "最大回撤%": float(metrics["最大回撤"].replace("%", "")),
                "交易次数": int(metrics["交易次数"]),
                "胜率%": float(metrics["胜率"].replace("%", "")),
            })
    res_df = pd.DataFrame(results).sort_values("夏普", ascending=False).reset_index(drop=True)
    return res_df


# ======================== 主流程 ========================
def main():
    print("=" * 60)
    print("  双均线趋势跟踪策略 回测报告")
    print(f"  手续费={COMMISSION_RATE*100:.2f}%  滑点={SLIPPAGE_RATE*100:.2f}%  印花税={STAMP_TAX_RATE*100:.2f}%(卖)")
    print("=" * 60)

    # ---------- 阶段一: 参数网格搜索 ----------
    print("\n>>> 阶段一: 参数网格搜索 (按夏普比率排序 Top 10)")
    short_candidates = [5, 10, 15, 20, 30]
    long_candidates = [40, 60, 90, 120, 150]
    gs = grid_search(short_candidates, long_candidates)
    print(gs.head(10).to_string(index=False))

    # 取夏普最高的参数组合
    best = gs.iloc[0]
    best_s, best_l = int(best["ma_short"]), int(best["ma_long"])
    print(f"\n最优参数: MA_SHORT={best_s}, MA_LONG={best_l} (夏普={best['夏普']:.2f})")

    # ---------- 阶段二: 用最优参数回测 ----------
    print(f"\n>>> 阶段二: 最优参数 (MA{best_s}/MA{best_l}) 回测结果")
    metrics, df = run_single_backtest(best_s, best_l)

    print()
    for k, v in metrics.items():
        print(f"  {k:>12s}: {v}")
    print("=" * 60)

    img = plot_result(df, ma_short=best_s, ma_long=best_l)
    print(f"\n图表已保存: {img}")


if __name__ == "__main__":
    main()
