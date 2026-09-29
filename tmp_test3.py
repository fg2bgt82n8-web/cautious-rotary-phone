"""
大底指标测试3：构造持续创新低的下跌场景
"""
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '/workspace/outputs')
from dadi_indicator import calculate_dadi, get_dadi_status

np.random.seed(42)
n = 600

# 前300日高位震荡，后300日持续下跌创新低
close = np.zeros(n)
close[:300] = 30 + np.random.randn(300) * 0.3  # 高位震荡
# 后300日持续下跌
for i in range(300, n):
    close[i] = close[i-1] - 0.15 + np.random.randn() * 0.05

high = close + np.abs(np.random.randn(n) * 0.15)
low = close - np.abs(np.random.randn(n) * 0.15)
low = np.maximum(low, 0.5)
open_ = close + np.random.randn(n) * 0.1
vol = np.random.randint(5000000, 50000000, n).astype(float)
vol[300:] *= 2  # 下跌放量

dates = pd.bdate_range('2024-01-01', periods=n)
df = pd.DataFrame({
    'high': high, 'low': low, 'close': close, 'open': open_, 'vol': vol
}, index=dates)

result = calculate_dadi(df)

print("=== 持续下跌创新低场景测试 ===")
print(f"最后10日数据:")
for idx, row in result.tail(10).iterrows():
    level = "强底!!!" if row['strong_signal'] else ("大底!" if row['dadi_signal'] else "")
    print(f"  {idx.date()} close={row['close']:.2f} low={row['low']:.2f} aa3={row['aa3']:.2f} varA={row['varA']:.2f} {level}")

signals = result[result['dadi_signal'] == True]
strong = result[result['strong_signal'] == True]
print(f"\n大底信号触发次数(aa3>10): {len(signals)}")
print(f"强信号触发次数(aa3>100): {len(strong)}")

if len(signals) > 0:
    print(f"\n最近10次大底信号:")
    for idx, row in signals.tail(10).iterrows():
        level = "强底!!!" if row['strong_signal'] else "大底"
        print(f"  {idx.date()} close={row['close']:.2f} aa3={row['aa3']:.1f} {level} 净买={row['aa6']:.2f}")

# 检查varC/varD是否非零
print(f"\n最后5日varC/varD/aa3_raw检查:")
for idx, row in result.tail(5).iterrows():
    varE = row.get('varE', 'N/A')
    print(f"  {idx.date()} varA={row['varA']:.2f} close*1.35={row['close']*1.35:.2f} cond={row['close']*1.35 <= row['varA']}")

status = get_dadi_status(result.tail(10), df.iloc[-1]['close'])
print(f"\n最新状态: {status}")
