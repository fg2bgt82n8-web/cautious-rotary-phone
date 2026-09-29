"""
大底指标测试2：构造一个真实下跌场景验证信号触发
"""
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '/workspace/outputs')
from dadi_indicator import calculate_dadi, get_dadi_status

np.random.seed(42)
n = 600

# 构造先涨后大跌的场景
close = np.zeros(n)
close[:300] = 20 + np.cumsum(np.random.randn(300) * 0.1)  # 前300日缓慢上涨
close[300:] = 30 - np.cumsum(np.random.randn(300) * 0.25)  # 后300日急跌
close = np.maximum(close, 1)  # 不允许负数

high = close + np.abs(np.random.randn(n) * 0.15)
low = close - np.abs(np.random.randn(n) * 0.15)
low = np.maximum(low, 0.5)
open_ = close + np.random.randn(n) * 0.1
vol = np.random.randint(5000000, 50000000, n).astype(float)
# 大跌时放量
vol[300:] *= 2

dates = pd.bdate_range('2024-01-01', periods=n)
df = pd.DataFrame({
    'high': high, 'low': low, 'close': close, 'open': open_, 'vol': vol
}, index=dates)

result = calculate_dadi(df)

print("=== 下跌场景大底指标测试 ===")
print(f"最后10日aa3序列:")
for idx, row in result.tail(10).iterrows():
    level = "强底" if row['strong_signal'] else ("大底" if row['dadi_signal'] else "")
    print(f"  {idx.date()} close={row['close']:.2f} aa3={row['aa3']:.1f} {level}")

# 查找所有大底信号
signals = result[result['dadi_signal'] == True]
strong = result[result['strong_signal'] == True]
print(f"\n大底信号触发次数(aa3>10): {len(signals)}")
print(f"强信号触发次数(aa3>100): {len(strong)}")

if len(signals) > 0:
    print(f"\n最近10次大底信号:")
    for idx, row in signals.tail(10).iterrows():
        level = "强底!!!" if row['strong_signal'] else "大底"
        print(f"  {idx.date()} close={row['close']:.2f} aa3={row['aa3']:.1f} {level} 净买={row['aa6']:.2f}")

status = get_dadi_status(result.tail(10), df.iloc[-1]['close'])
print(f"\n最新状态: {status}")
