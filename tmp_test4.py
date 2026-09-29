"""
大底指标测试4：构造真实超跌场景，low有波动且持续创新低
"""
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '/workspace/outputs')
from dadi_indicator import calculate_dadi, get_dadi_status

np.random.seed(42)
n = 600

# 构造真实下跌场景: 从30元跌到5元
close = np.zeros(n)
close[0] = 30
for i in range(1, n):
    # 前200日缓跌，后400日加速跌
    drift = -0.05 if i < 200 else -0.12
    close[i] = max(close[i-1] + drift + np.random.randn() * 0.3, 2.0)

high = close + np.abs(np.random.randn(n) * 0.2)
low = close - np.abs(np.random.randn(n) * 0.2)
low = np.maximum(low, 1.0)
open_ = close + np.random.randn(n) * 0.15
vol = np.random.randint(5000000, 50000000, n).astype(float)

dates = pd.bdate_range('2024-01-01', periods=n)
df = pd.DataFrame({
    'high': high, 'low': low, 'close': close, 'open': open_, 'vol': vol
}, index=dates)

result = calculate_dadi(df)

print("=== 真实超跌场景测试 ===")
print(f"最后15日数据:")
for idx, row in result.tail(15).iterrows():
    level = "强底!!!" if row['strong_signal'] else ("大底!" if row['dadi_signal'] else "")
    print(f"  {idx.date()} close={row['close']:.2f} low={row['low']:.2f} aa3={row['aa3']:.2f} {level}")

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
