"""
大底指标调试：逐行追踪计算过程
"""
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '/workspace/outputs')
from dadi_indicator import ema, hhv, llv, sma, ref

np.random.seed(42)
n = 600

# 更真实的下跌+底部场景
close = np.zeros(n)
close[0] = 30
for i in range(1, n):
    if i < 300:
        drift = -0.03
    elif i < 450:
        drift = -0.08  # 加速下跌
    else:
        drift = 0.02    # 底部企稳
    close[i] = max(close[i-1] + drift + np.random.randn() * 0.35, 1.5)

high = close + np.abs(np.random.randn(n) * 0.25)
low = close - np.abs(np.random.randn(n) * 0.25)
low = np.maximum(low, 1.0)
open_ = close + np.random.randn(n) * 0.15
vol = np.random.randint(5000000, 50000000, n).astype(float)

dates = pd.bdate_range('2024-01-01', periods=n)
df = pd.DataFrame({
    'high': high, 'low': low, 'close': close, 'open': open_, 'vol': vol
}, index=dates)

H, L, C, O, V = df['high'], df['low'], df['close'], df['open'], df['vol']

var1 = ema(hhv(H, 500), 21)
var2 = ema(hhv(H, 250), 21)
var3 = ema(hhv(H, 90), 21)
var4 = ema(llv(L, 500), 21)
var5 = ema(llv(L, 250), 21)
var6 = ema(llv(L, 90), 21)

var7 = ema((var4 * 0.96 + var5 * 0.96 + var6 * 0.96 + var1 * 0.558 + var2 * 0.558 + var3 * 0.558) / 6, 21)
var8 = ema((var4 * 1.25 + var5 * 1.23 + var6 * 1.2 + var1 * 0.55 + var2 * 0.55 + var3 * 0.65) / 6, 21)
var9 = ema((var4 * 1.3 + var5 * 1.3 + var6 * 1.3 + var1 * 0.68 + var2 * 0.68 + var3 * 0.68) / 6, 21)
varA = ema((var7 * 3 + var8 * 2 + var9) / 6 * 1.738, 21)

varB = ref(L, 1)
abs_diff = (L - varB).abs()
max_diff = (L - varB).clip(lower=0)
varC_num = sma(abs_diff, 3, 1)
varC_den = sma(max_diff, 3, 1)

# 关键：当分母为0时，用TDX的方式处理（结果为0）
varC = (varC_num / varC_den.replace(0, np.nan) * 100).fillna(0)

cond_d = C * 1.35 <= varA
varD_raw = pd.Series(np.where(cond_d, varC * 10, varC / 10), index=df.index)
varD = ema(varD_raw, 3)

varE = llv(L, 30)
varF = hhv(varD, 30)

cond_e = L <= varE
aa3_raw = pd.Series(np.where(cond_e, (varD + varF * 2) / 2, 0), index=df.index)
aa3 = ema(aa3_raw, 3) / 618

print("=== 最后20日逐行追踪 ===")
for idx in result_idx[-20:] if 'result_idx' in dir() else df.index[-20:]:
    i = df.index.get_loc(idx)
    print(f"{idx.date()} C={C[idx]:.2f} L={L[idx]:.2f} varA={varA[idx]:.2f} "
          f"C*1.35={C[idx]*1.35:.2f} cond_d={cond_d[idx]} "
          f"varC_num={varC_num[idx]:.4f} varC_den={varC_den[idx]:.4f} "
          f"varC={varC[idx]:.2f} varD={varD[idx]:.4f} "
          f"varE={varE[idx]:.2f} cond_e={cond_e[idx]} "
          f"aa3_raw={aa3_raw[idx]:.4f} aa3={aa3[idx]:.2f}")

signals = aa3[aa3 > 10]
print(f"\naa3>10的次数: {len(signals)}")
strong = aa3[aa3 > 100]
print(f"aa3>100的次数: {len(strong)}")
if len(signals) > 0:
    print("信号日:")
    for idx in signals.index[-10:]:
        print(f"  {idx.date()} aa3={aa3[idx]:.1f} close={C[idx]:.2f}")
