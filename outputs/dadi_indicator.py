"""
大底指标模块 (dadi_indicator.py)
基于通达信自定义公式转换，作为"顶底山峰"补充信号
当 aa3 > 100 时给予强提示（极端超跌+主力吸筹）
"""

import numpy as np
import pandas as pd


def ema(series, period):
    """EMA指数移动平均，与通达信EMA一致"""
    return series.ewm(span=period, adjust=False).mean()


def sma(series, n, m=1):
    """通达信SMA函数: SMA(X,N,M) = (M*X + (N-M)*Y') / N，跳过NaN"""
    result = pd.Series(index=series.index, dtype=float)
    prev = None
    for i in range(len(series)):
        val = series.iloc[i]
        if pd.isna(val):
            result.iloc[i] = np.nan
            continue
        if prev is None or pd.isna(prev):
            prev = val
            result.iloc[i] = val
        else:
            prev = (m * val + (n - m) * prev) / n
            result.iloc[i] = prev
    return result


def hhv(series, n):
    """HHV: N周期最高值"""
    return series.rolling(window=n, min_periods=1).max()


def llv(series, n):
    """LLV: N周期最低值"""
    return series.rolling(window=n, min_periods=1).min()


def ref(series, n):
    """REF: N周期前的值"""
    return series.shift(n)


def calculate_dadi(df):
    """
    计算大底信号

    参数:
        df: DataFrame, 至少包含列: high, low, close, open, vol
            index为日期

    返回:
        DataFrame, 新增列:
        - aa3: 主力吸筹能量值
        - dadi_signal: 大底信号 (bool, aa3>10)
        - strong_signal: 强信号 (bool, aa3>100)
        - bb_breakout: aa3突破60日最高 (bool)
        - cc: 60日最高aa3
        - aa6: 净买占比
        - main_buy: 主买量
        - main_sell: 主卖量
    """
    H = df['high']
    L = df['low']
    C = df['close']
    O = df['open']
    V = df['vol']

    # === 第一层: 多周期价格通道 ===
    var1 = ema(hhv(H, 500), 21)
    var2 = ema(hhv(H, 250), 21)
    var3 = ema(hhv(H, 90), 21)
    var4 = ema(llv(L, 500), 21)
    var5 = ema(llv(L, 250), 21)
    var6 = ema(llv(L, 90), 21)

    # === 第二层: 加权合成基准价 ===
    var7 = ema((var4 * 0.96 + var5 * 0.96 + var6 * 0.96 +
                var1 * 0.558 + var2 * 0.558 + var3 * 0.558) / 6, 21)
    var8 = ema((var4 * 1.25 + var5 * 1.23 + var6 * 1.2 +
                var1 * 0.55 + var2 * 0.55 + var3 * 0.65) / 6, 21)
    var9 = ema((var4 * 1.3 + var5 * 1.3 + var6 * 1.3 +
                var1 * 0.68 + var2 * 0.68 + var3 * 0.68) / 6, 21)
    varA = ema((var7 * 3 + var8 * 2 + var9) / 6 * 1.738, 21)

    # === 第三层: 底部吸筹能量 ===
    varB = ref(L, 1)  # 昨日最低价

    # SMA(ABS(LOW-VarB),3,1) / SMA(MAX(LOW-VarB,0),3,1) * 100
    abs_diff = (L - varB).abs()
    max_diff = (L - varB).clip(lower=0)
    varC = sma(abs_diff, 3, 1) / sma(max_diff, 3, 1).replace(0, np.nan) * 100
    varC = varC.fillna(0)

    # EMA(IF(CLOSE*1.35<=VarA, VarC*10, VarC/10), 3)
    cond_d = C * 1.35 <= varA
    varD_raw = pd.Series(np.where(cond_d, varC * 10, varC / 10), index=df.index)
    varD = ema(varD_raw, 3)

    varE = llv(L, 30)      # 30日最低
    varF = hhv(varD, 30)    # 30日最高varD
    var10 = 1  # MA(CLOSE,58)存在则为1

    # aa3: EMA(IF(LOW<=VarE, (VarD+VarF*2)/2, 0), 3) / 618 * var10
    cond_e = L <= varE
    aa3_raw = pd.Series(np.where(cond_e, (varD + varF * 2) / 2, 0), index=df.index)
    aa3 = ema(aa3_raw, 3) / 618 * var10

    # bb: aa3突破60日最高
    aa3_hhv60 = hhv(aa3, 60)
    bb = aa3 > ref(aa3_hhv60, 1)

    # cc: 60日最高aa3
    cc = aa3_hhv60

    # 大底信号: FILTER(aa3 > 10, 1) — 当日aa3>10即触发
    dadi_signal = aa3 > 10

    # 强信号: aa3 > 100
    strong_signal = aa3 > 100

    # === 第四层: 买卖力量 ===
    VA1 = V / ((H - L) * 2 - (C - O).abs().replace(0, 0.0001))

    # 主买
    cond_buy1 = C > O
    cond_buy2 = C < O
    main_buy = pd.Series(np.where(
        cond_buy1, VA1 * (H - L),
        np.where(cond_buy2, VA1 * ((H - O) + (C - L)), V / 2)
    ), index=df.index)

    # 主卖
    main_sell = pd.Series(np.where(
        cond_buy1, -VA1 * ((H - C) + (O - L)),
        np.where(cond_buy2, -VA1 * (H - L), -V / 2)
    ), index=df.index)

    # 净买占比
    aa6 = (main_buy - (-main_sell)) / main_buy.replace(0, np.nan)

    # 写入结果
    result = df.copy()
    result['varA'] = varA          # 基准价
    result['aa3'] = aa3            # 吸筹能量值
    result['cc'] = cc              # 60日最高aa3
    result['bb_breakout'] = bb     # 突破60日最高
    result['dadi_signal'] = dadi_signal  # 大底信号(aa3>10)
    result['strong_signal'] = strong_signal  # 强信号(aa3>100)
    result['main_buy'] = main_buy  # 主买量
    result['main_sell'] = main_sell  # 主卖量
    result['aa6'] = aa6            # 净买占比

    return result


def get_dadi_status(df_tail, current_close):
    """
    从最近数据获取大底状态摘要（用于选股卡片展示）

    参数:
        df_tail: calculate_dadi返回的DataFrame尾部数据（最近5-10日）
        current_close: 当前/最新收盘价

    返回:
        dict: {
            'aa3': 最新aa3值,
            'signal': '无信号' / '大底' / '强底(aa3>100)',
            'breakout': 是否突破60日高,
            'net_buy_ratio': 净买占比,
            'description': 文字描述,
        }
    """
    if df_tail is None or len(df_tail) == 0:
        return {
            'aa3': 0,
            'signal': '数据缺失',
            'breakout': False,
            'net_buy_ratio': 0,
            'description': '大底指标数据缺失',
        }

    last = df_tail.iloc[-1]
    aa3_val = last['aa3']
    is_signal = last['dadi_signal']
    is_strong = last['strong_signal']
    is_breakout = last['bb_breakout']
    aa6_val = last['aa6'] if not np.isnan(last['aa6']) else 0

    if is_strong:
        signal = '强底(aa3>100)'
        desc = f'aa3={aa3_val:.1f}，极端超跌+主力吸筹，强底部信号'
    elif is_signal:
        signal = '大底'
        desc = f'aa3={aa3_val:.1f}，超跌吸筹信号'
    elif is_breakout:
        signal = '能量突破'
        desc = f'aa3={aa3_val:.1f}，吸筹能量突破60日高点，关注底部形成'
    else:
        signal = '无信号'
        desc = f'aa3={aa3_val:.1f}，暂无底部信号'

    if not np.isnan(aa6_val):
        if aa6_val > 0.3:
            desc += f'，净买占比{aa6_val*100:.0f}%，主力净买入'
        elif aa6_val < -0.3:
            desc += f'，净买占比{aa6_val*100:.0f}%，主力净卖出'

    return {
        'aa3': round(aa3_val, 1) if not np.isnan(aa3_val) else 0,
        'signal': signal,
        'breakout': bool(is_breakout) if not np.isnan(is_breakout) else False,
        'net_buy_ratio': round(aa6_val, 2) if not np.isnan(aa6_val) else 0,
        'description': desc,
    }


def scan_dadi_for_picks(stock_codes, fetch_func):
    """
    批量扫描推荐股票池的大底信号

    参数:
        stock_codes: list of str, 股票代码列表
        fetch_func: callable, 接收股票代码，返回含high/low/close/open/vol的DataFrame

    返回:
        dict: {股票代码: get_dadi_status结果}
    """
    results = {}
    for code in stock_codes:
        try:
            df = fetch_func(code)
            if df is None or len(df) < 100:
                results[code] = {
                    'aa3': 0,
                    'signal': '数据不足',
                    'breakout': False,
                    'net_buy_ratio': 0,
                    'description': f'{code}历史数据不足(需≥500日)，无法计算大底指标',
                }
                continue
            result_df = calculate_dadi(df)
            status = get_dadi_status(result_df.tail(10), df.iloc[-1]['close'])
            results[code] = status
        except Exception as e:
            results[code] = {
                'aa3': 0,
                'signal': '计算错误',
                'breakout': False,
                'net_buy_ratio': 0,
                'description': f'{code}大底指标计算异常: {e}',
            }
    return results


# === 测试入口 ===
if __name__ == '__main__':
    # 生成模拟数据测试
    np.random.seed(42)
    n = 600
    dates = pd.bdate_range('2024-01-01', periods=n)
    close = 10 + np.cumsum(np.random.randn(n) * 0.15)
    high = close + np.abs(np.random.randn(n) * 0.1)
    low = close - np.abs(np.random.randn(n) * 0.1)
    open_ = close + np.random.randn(n) * 0.05
    vol = np.random.randint(5000000, 50000000, n).astype(float)

    df = pd.DataFrame({
        'high': high, 'low': low, 'close': close, 'open': open_, 'vol': vol
    }, index=dates)

    result = calculate_dadi(df)
    status = get_dadi_status(result.tail(10), df.iloc[-1]['close'])

    print("=== 大底指标测试 ===")
    print(f"最新aa3值: {status['aa3']}")
    print(f"信号状态: {status['signal']}")
    print(f"能量突破: {status['breakout']}")
    print(f"净买占比: {status['net_buy_ratio']}")
    print(f"描述: {status['description']}")
    print()

    # 检查是否有触发信号
    signals = result[result['dadi_signal'] == True]
    strong_signals = result[result['strong_signal'] == True]
    print(f"大底信号触发次数(aa3>10): {len(signals)}")
    print(f"强信号触发次数(aa3>100): {len(strong_signals)}")
    if len(signals) > 0:
        print(f"\n最近5次大底信号:")
        for idx, row in signals.tail(5).iterrows():
            level = "强底" if row['strong_signal'] else "大底"
            print(f"  {idx.date()} aa3={row['aa3']:.1f} {level} close={row['close']:.2f}")
