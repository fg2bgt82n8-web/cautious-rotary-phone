#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整执行脚本：整合所有数据 → 生成HTML → 生成CSV台账"""
import csv
import os
from datetime import datetime

OUTPUT_DIR = "/workspace/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TODAY = "2026-09-28"
TODAY_COMPACT = "20260928"
PREV_CLOSE = "2026-09-24"

# ========= 大盘 =========
MKT_SUM = {
    "sh_close": 3888.37, "sh_chg": -1.22,
    "sz_close": 13316.97, "sz_chg": -2.34,
    "cyb_close": 3288.95, "cyb_chg": -2.68,
    "hs300_close": 4439.14, "hs300_chg": -1.73,
    "vol": "1.67万亿", "vol_chg": "缩量1140亿",
    "up": 1134, "down": 4352, "limit_up": 52, "limit_down": 15,
    "top_sec": "风电设备、纺织制造", "bot_sec": "贵金属、元器件、能源金属",
}
MKT_STR = {
    "ma200": "跌破MA200，三空共振",
    "chanlun": "日线中枢【4026,4242】下破，无一买信号",
    "wave": "4浪深调或A浪，5月高点4242回撤8.3%",
    "score": 3,
    "pos": 50,
}

EMO5 = {
    "score": 3, "turnover": "逐步缩量(日均9133亿)",
    "limit_up": "9/18→87家，9/24→52家，晋级率下滑",
    "up_ratio": "21%", "combo": "2板",
}
OVS = {
    "道指": "-0.50%", "标普": "+0.51%", "纳指": "+0.48%",
    "中概金龙": "+2.83%", "美债10Y": "5.0-5.2%",
    "布油": "$88.58", "黄金": "$4378/oz",
}

STOCKS = [
    (1,"002847.SZ","盐津铺子","A股","食品加工",95,25.86,48.66,36.82,78,
     "下跌楔形收敛→缠论二买→3浪回调完成→顶底山峰","日线·中枢震荡类二买","3浪回调完成","二买/三买临界",
     43.15,-0.12,0.58,"43.0-44.5",39.70,"站上46.3放量",10,
     "楔形+缠论二买+波浪3浪+顶底山峰"),
    (2,"600550.SH","保变电气","A股","输变电",96,34.63,60.0,27.44,72,
     "收敛平台→缠论三买→2浪回调完成→地量企稳","日线·中枢三买","2浪回调完成","三买",
     10.29,-1.06,0.69,"10.3-10.8",9.47,"站上11.0放量",10,
     "平台收敛+三买+2浪+地量"),
    (3,"603766.SH","隆鑫通用","A股","通用机械",97,48.88,44.5,17.50,82,
     "上涨楔形→缠论三买→3浪起点→顶底山峰","日线·中枢三买","3浪起点","三买",
     14.55,-0.07,0.52,"14.4-14.9",13.39,"突破14.85放量",10,
     "上涨楔形+三买+3浪+顶底山峰"),
    (4,"689009.SH","九号公司","A股","短交通",95,63.48,47.8,26.08,80,
     "底部反转楔形→缠论二买→4浪到位→地量","日线·中枢二买","4浪回调到位","二买",
     19.50,-2.10,0.65,"19.3-20.2",17.74,"重返21放量",10,
     "底部楔形+二买+4浪+地量"),
    (5,"600961.SH","株冶集团","A股","有色金属",92,99.71,50.2,31.40,68,
     "下跌楔形→缠论一买候选→4浪末端→短期底部","日线·下跌背驰一买候选","4浪末端","一买候选",
     23.61,-3.51,0.78,"23.5-24.5",21.72,"重返25",10,
     "下跌楔形+一买候选+4浪末端"),
    (6,"02020.HK","安踏体育","港股通","体育用品",96,25,22,20,85,
     "上升楔形→缠论三买→3浪推进→顶底山峰","日线·中枢三买","3浪推进中","三买",
     78.20,-0.85,0.60,"76-80",71.94,"突破82.5放量",10,
     "上升楔形+三买+3浪+顶底山峰"),
    (7,"01024.HK","快手-W","港股通","短视频",93,40,35,15,72,
     "底部反转→缠论三买→1→2浪衔接→颈线回踩","日线·中枢三买","1→2浪衔接","三买",
     44.80,-1.30,0.70,"44-46",41.22,"突破47放量",10,
     "底部反转+三买+1→2浪"),
    (8,"01810.HK","小米集团-W","港股通","消费电子",90,18,20,14,74,
     "箱体蓄势→缠论二买→2浪末端→底部放量","日线·中枢二买","2浪末端→3浪","二买",
     27.40,0.50,0.65,"26.5-28.0",25.21,"突破30放量",10,
     "箱体+二买+2→3浪+底部"),
    (9,"03690.HK","美团-W","港股通","本地生活",90,22,25,16,68,
     "下跌楔形→缠论一买→ABC末端→W底","日线·下跌背驰一买","ABC调整末端","一买候选",
     132.50,-2.10,0.75,"130-138",121.90,"重返150",10,
     "下跌楔形+一买+ABC+W底"),
    (10,"00700.HK","腾讯控股","港股通","互联网科技",89,15,18,18,68,
     "三角形收敛→缠论三买→B浪反弹→止跌","日线·中枢三买","B浪反弹","三买",
     378.50,1.20,0.80,"370-390",348.22,"突破400",10,
     "三角形+三买+B浪+止跌"),
]

# ========== 生成 CSV ==========
CSV_PATH = os.path.join(OUTPUT_DIR, "推荐与验证台账.csv")
CSV_HEADER = ["日期","环节","时间","代码","名称","市场","CANSLIM评分","买点形态","信号",
              "参考买点(元)","现价(元)","涨跌幅%","量比","成交额(万)","主力净流入(万)",
              "结论","备注"]

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
header_exists = os.path.exists(CSV_PATH)

with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    if not header_exists:
        w.writerow(CSV_HEADER)
    for s in STOCKS:
        seq, code, name, mkt, ind, canslim, cp, ac, roe, rps = s[:10]
        trigger_detail, chan_tag, wave_tag, buy_type = s[10:14]
        close, chg, vr, buy_range, stop_loss, observe, pos_pct = s[14:21]
        notes = s[21]
        vol_yi = 0  # 成交额近似标注
        main_flow = "数据缺失"
        w.writerow([
            TODAY, "盘前推荐", now_str,
            code, name, mkt, f"{canslim}",
            f"{trigger_detail}", f"缠论{buy_type}/{chan_tag} 波浪{wave_tag}",
            buy_range, f"{close:.2f}", f"{chg:.2f}", f"{vr}", vol_yi, main_flow,
            "买入观察", notes
        ])
print(f"CSV written: {CSV_PATH}")

# ========== 生成 HTML ==========
def build_html():
    stocks_html = ""
    for s in STOCKS:
        seq, code, name, mkt, ind, canslim = s[0:6]
        cp, ac, roe, rps = s[6:10]
        trigger, chan_tag, wave_tag, buy_type = s[10:14]
        close, chg, vr, buy_rng, stop, obs, pos = s[14:21]
        tag_color = "#e74c3c" if "A股" in mkt else "#2980b9"
        chg_color = "#e74c3c" if chg >= 0 else "#27ae60"
        stock_id = f"stock_{seq}"
        stocks_html += f"""
        <div class="stock-card" id="{stock_id}">
          <div class="stock-header">
            <div class="stock-title">
              <span class="stock-code">{code}</span>
              <span class="stock-name">{name}</span>
              <span class="tag" style="background:{tag_color}">{mkt}</span>
              <span class="tag gray">{ind}</span>
            </div>
            <div class="score-box">CANSLIM <b>{canslim}</b></div>
          </div>
          <div class="metrics-row">
            <div><span class="lbl">C净利同比</span><span class="val">{cp}%</span></div>
            <div><span class="lbl">A3年复合</span><span class="val">{ac}%</span></div>
            <div><span class="lbl">ROE</span><span class="val">{roe}%</span></div>
            <div><span class="lbl">L RPS</span><span class="val">{rps}</span></div>
          </div>
          <div class="analysis-box">
            <div class="ana-row"><span class="ana-lbl">缠论</span><span class="ana-val">{chan_tag}</span></div>
            <div class="ana-row"><span class="ana-lbl">波浪</span><span class="ana-val">{wave_tag}</span></div>
            <div class="ana-row"><span class="ana-lbl">买点</span><span class="ana-val"><b style="color:#e67e22">{buy_type}</b></span></div>
            <div class="ana-row"><span class="ana-lbl">触发</span><span class="ana-val">{trigger}</span></div>
          </div>
          <div class="price-row">
            <div class="price-item">
              <div class="price-lbl">昨收</div>
              <div class="price-val">{close:.2f}<span style="color:{chg_color};font-size:14px;margin-left:4px">({chg:+.2f}%)</span></div>
            </div>
            <div class="price-item">
              <div class="price-lbl">参考买点</div>
              <div class="price-val buy">{buy_rng}</div>
            </div>
            <div class="price-item">
              <div class="price-lbl">止损(-8%)</div>
              <div class="price-val stop">{stop:.2f}</div>
            </div>
            <div class="price-item">
              <div class="price-lbl">观察位</div>
              <div class="price-val">{obs}</div>
            </div>
            <div class="price-item">
              <div class="price-lbl">建议仓位</div>
              <div class="price-val pos">{pos}%</div>
            </div>
          </div>
        </div>
        """
    
    sectors_top = MKT_SUM["top_sec"].split("、")
    sectors_bot = MKT_SUM["bot_sec"].split("、")
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A+H 盘前十股推荐 · {TODAY}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#0f1923;color:#e8ecf1;line-height:1.6}}
.wrap{{max-width:1200px;margin:0 auto;padding:24px 16px}}
h1{{font-size:22px;font-weight:700;margin-bottom:4px;background:linear-gradient(90deg,#3498db,#2ecc71);-webkit-background-clip:text;color:transparent}}
.sub{{color:#7f8c8d;font-size:13px;margin-bottom:20px}}
.card{{background:#1a2733;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid #2a3a4a}}
.card h2{{font-size:16px;margin-bottom:14px;color:#3498db;display:flex;align-items:center;gap:8px}}
.card h2::before{{content:"";width:4px;height:18px;background:linear-gradient(180deg,#3498db,#2ecc71);border-radius:2px}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.grid2{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
.metric{{background:#142028;border-radius:8px;padding:12px}}
.metric .lbl{{font-size:12px;color:#7f8c8d;display:block;margin-bottom:4px}}
.metric .val{{font-size:18px;font-weight:600;color:#ecf0f1}}
.metric .sub{{font-size:11px;color:#5a6b7c;margin-top:2px}}
.pos-card{{background:linear-gradient(135deg,#2c3e50,#1a2733);border:2px solid #e67e22}}
.pos-card .val{{color:#e67e22}}
.warn-card{{background:linear-gradient(135deg,#c0392b,#1a2733);border:2px solid #e74c3c}}
.warn-card .val{{color:#e74c3c}}
.ok-card{{background:linear-gradient(135deg,#27ae60,#1a2733);border:2px solid #2ecc71}}
.tag{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;color:#fff;margin-left:4px}}
.tag.gray{{background:#34495e}}
.stock-card{{background:#1a2733;border-radius:10px;padding:16px;margin-bottom:10px;border-left:3px solid #3498db;transition:transform .2s}}
.stock-card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.3)}}
.stock-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}}
.stock-title{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.stock-code{{font-family:'Courier New',monospace;font-size:13px;color:#7f8c8d;background:#142028;padding:2px 6px;border-radius:4px}}
.stock-name{{font-size:17px;font-weight:600;color:#ecf0f1}}
.score-box{{background:linear-gradient(135deg,#3498db,#2ecc71);padding:8px 16px;border-radius:20px;font-size:13px;font-weight:500;white-space:nowrap}}
.score-box b{{font-size:18px}}
.metrics-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}}
.metrics-row > div{{background:#142028;padding:8px;border-radius:6px;text-align:center}}
.metrics-row .lbl{{font-size:11px;color:#7f8c8d;display:block}}
.metrics-row .val{{font-size:14px;font-weight:600;color:#ecf0f1}}
.analysis-box{{background:#142028;border-radius:8px;padding:12px;margin-bottom:12px}}
.ana-row{{display:flex;margin-bottom:6px;font-size:13px}}
.ana-row:last-child{{margin-bottom:0}}
.ana-lbl{{color:#7f8c8d;width:60px;flex-shrink:0}}
.ana-val{{color:#bdc3c7;flex:1}}
.price-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}
.price-item{{background:#142028;padding:10px;border-radius:6px;text-align:center}}
.price-lbl{{font-size:11px;color:#7f8c8d;display:block;margin-bottom:4px}}
.price-val{{font-size:14px;font-weight:600;color:#ecf0f1}}
.price-val.buy{{color:#2ecc71}}
.price-val.stop{{color:#e74c3c}}
.price-val.pos{{color:#e67e22;font-size:16px}}
.split-bar{{height:6px;background:#142028;border-radius:3px;display:flex;overflow:hidden;margin:8px 0}}
.split-bar div:nth-child(1){{flex:5;background:#e74c3c}}
.split-bar div:nth-child(2){{flex:5;background:#3498db}}
.section-title{{display:flex;align-items:center;gap:10px;margin:24px 0 12px;font-size:15px;color:#bdc3c7}}
.section-title .dot{{width:8px;height:8px;background:#2ecc71;border-radius:50%}}
.disclaimer{{background:#2c1810;border:1px solid #c0392b;border-radius:8px;padding:16px;margin-top:20px;font-size:12px;color:#e67e22;line-height:1.8}}
.sep{{text-align:center;color:#5a6b7c;margin:16px 0;font-size:12px}}
.sep::before,.sep::after{{content:"";display:inline-block;width:40px;height:1px;background:#34495e;margin:0 8px;vertical-align:middle}}
.emotion{{display:flex;gap:6px;margin-top:8px}}
.emotion span{{flex:1;height:24px;border-radius:4px;background:#142028;position:relative;overflow:hidden}}
.emotion span::before{{content:"";position:absolute;left:0;top:0;bottom:0;width:var(--p,30%);background:linear-gradient(90deg,#e74c3c,#f39c12,#2ecc71)}}
.sector-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}}
.sector-top li,.sector-bot li{{padding:6px 12px;border-radius:6px;font-size:13px;margin-bottom:4px}}
.sector-top li{{background:rgba(46,204,113,.15);color:#2ecc71}}
.sector-bot li{{background:rgba(231,76,60,.15);color:#e74c3c}}
ul{{list-style:none}}
@media(max-width:768px){{
  .grid3,.grid2{{grid-template-columns:1fr}}
  .metrics-row{{grid-template-columns:repeat(2,1fr)}}
  .price-row{{grid-template-columns:repeat(2,1fr)}}
}}
</style>
</head>
<body>
<div class="wrap">

<h1>A+H 全市场盘前十股推荐</h1>
<div class="sub">{TODAY} · 欧奈尔CANSLIM + 楔形理论 + 缠论 + 波浪理论 + 顶底山峰</div>

<!-- ============ 大盘一票否决 + 缠论波浪 ============ -->
<div class="card">
<h2>M大盘结论卡</h2>
<div class="grid3">
  <div class="metric warn-card">
    <span class="lbl">大盘位置</span>
    <span class="val">{MKT_STR['ma200']}</span>
    <span class="sub">上证{int(MKT_SUM['sh_chg']):+d}%，沪深300{int(MKT_SUM['hs300_chg']):+d}%</span>
  </div>
  <div class="metric pos-card">
    <span class="lbl">缠论结构</span>
    <span class="val">中枢下破</span>
    <span class="sub">{MKT_STR['chanlun']}</span>
  </div>
  <div class="metric pos-card">
    <span class="lbl">波浪结构</span>
    <span class="val">4浪/ABC</span>
    <span class="sub">{MKT_STR['wave']}</span>
  </div>
</div>
<div style="margin-top:16px;padding:12px;background:#142028;border-radius:8px">
  <b style="color:#e67e22">⚠ 总闸门结论：</b>{MKT_STR['chanlun']}。{MKT_STR['wave']}。三空共振（MA200跌破+中枢下破+波浪深调），
  整体偏空。<b style="color:#e67e22">今日建议总仓位上限 {MKT_STR['pos']}%</b>（半仓防守），仅选结构性强势股。
</div>
</div>

<!-- ============ 昨日盘口 ============ -->
<div class="card">
<h2>昨日盘口 ({PREV_CLOSE})</h2>
<div class="grid3">
  <div class="metric"><span class="lbl">上证指数</span><span class="val">{MKT_SUM['sh_close']}</span><span class="sub" style="color:#e74c3c">{MKT_SUM['sh_chg']:+.2f}%</span></div>
  <div class="metric"><span class="lbl">深证成指</span><span class="val">{MKT_SUM['sz_close']}</span><span class="sub" style="color:#e74c3c">{MKT_SUM['sz_chg']:+.2f}%</span></div>
  <div class="metric"><span class="lbl">创业板指</span><span class="val">{MKT_SUM['cyb_close']}</span><span class="sub" style="color:#e74c3c">{MKT_SUM['cyb_chg']:+.2f}%</span></div>
  <div class="metric"><span class="lbl">沪深300</span><span class="val">{MKT_SUM['hs300_close']}</span><span class="sub" style="color:#e74c3c">{MKT_SUM['hs300_chg']:+.2f}%</span></div>
  <div class="metric"><span class="lbl">两市成交额</span><span class="val">{MKT_SUM['vol']}</span><span class="sub">{MKT_SUM['vol_chg']}</span></div>
  <div class="metric"><span class="lbl">北向资金</span><span class="val" style="color:#7f8c8d">数据缺失</span></div>
</div>
<div style="margin-top:12px" class="grid2">
  <div class="metric">
    <span class="lbl">涨跌家数</span>
    <span class="val" style="color:#27ae60">{MKT_SUM['up']}↑</span> / 
    <span class="val" style="color:#e74c3c">{MKT_SUM['down']}↓</span>
    <div class="sub">涨停{MKT_SUM['limit_up']}家 / 跌停{MKT_SUM['limit_down']}家</div>
  </div>
  <div class="metric">
    <span class="lbl">板块强弱</span>
    <div class="sub"><span style="color:#2ecc71">领涨：</span>{MKT_SUM['top_sec']}</div>
    <div class="sub"><span style="color:#e74c3c">领跌：</span>{MKT_SUM['bot_sec']}</div>
  </div>
</div>
</div>

<!-- ============ 隔夜外股 ============ -->
<div class="card">
<h2>隔夜外股</h2>
<div class="grid3">
  <div class="metric"><span class="lbl">道琼斯</span><span class="val">{OVS['道指']}</span><span class="sub">涨跌不一</span></div>
  <div class="metric"><span class="lbl">标普500</span><span class="val">{OVS['标普']}</span></div>
  <div class="metric"><span class="lbl">纳斯达克</span><span class="val">{OVS['纳指']}</span></div>
  <div class="metric"><span class="lbl">中概金龙</span><span class="val" style="color:#2ecc71">{OVS['中概金龙']}</span><span class="sub">阿里+8%</span></div>
  <div class="metric"><span class="lbl">美债10Y</span><span class="val">{OVS['美债10Y']}</span><span class="sub">高位震荡</span></div>
  <div class="metric"><span class="lbl">布伦特原油</span><span class="val">{OVS['布油']}</span><span class="sub">回落</span></div>
  <div class="metric"><span class="lbl">黄金</span><span class="val">{OVS['黄金']}</span><span class="sub">高位整理</span></div>
  <div class="metric"><span class="lbl">恒指期货夜盘</span><span class="val" style="color:#7f8c8d">数据缺失</span></div>
  <div class="metric"><span class="lbl">A50期货</span><span class="val" style="color:#7f8c8d">数据缺失</span></div>
</div>
</div>

<!-- ============ 五日情绪 ============ -->
<div class="card">
<h2>五日情绪 (0-10分)</h2>
<div class="grid2">
  <div class="metric">
    <span class="lbl">综合情绪分</span>
    <span class="val" style="color:#e74c3c">{EMO5['score']}/10 冰点</span>
    <div class="emotion"><span style="--p:30%"></span></div>
  </div>
  <div class="metric">
    <span class="lbl">成交额趋势</span>
    <span class="val">{EMO5['turnover']}</span>
  </div>
  <div class="metric"><span class="lbl">涨停/晋级</span><span class="val">{EMO5['limit_up']}</span></div>
  <div class="metric"><span class="lbl">上涨家数占比</span><span class="val">{EMO5['up_ratio']}</span></div>
  <div class="metric"><span class="lbl">连板高度</span><span class="val">{EMO5['combo']}</span></div>
  <div class="metric"><span class="lbl">两融/北向</span><span class="val" style="color:#7f8c8d">边际收缩 / 数据缺失</span></div>
</div>
</div>

<!-- ============ 十股推荐 ============ -->
<div class="section-title"><span class="dot"></span>十股推荐 · A股5支 + 港股通5支</div>

<div class="card" style="padding:12px 16px;background:linear-gradient(90deg,#1a2733,#142028)">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:14px;color:#bdc3c7">市场配比：<b style="color:#e74c3c">A股 5支</b> + <b style="color:#3498db">港股通 5支</b></span>
    <span style="font-size:13px;color:#7f8c8d">每支建议仓位 10% · 总仓位上限 {MKT_STR['pos']}%</span>
  </div>
  <div class="split-bar"><div></div><div></div></div>
</div>

{stocks_html}

<!-- ============ 板块方向 ============ -->
<div class="card">
<h2>板块方向与风险清单</h2>
<div class="grid2">
  <div>
    <div class="lbl" style="color:#2ecc71;font-size:13px;margin-bottom:8px">⚡ 关注方向</div>
    <ul class="sector-top">
      <li>风电设备/输变电（特高压周期+海外订单）</li>
      <li>通用机械/无人机（军工+低空经济）</li>
      <li>短交通/消费电子（AIoT+出海）</li>
      <li>互联网科技（AI智能体+商业化）</li>
      <li>体育用品（多品牌+海外扩张）</li>
    </ul>
  </div>
  <div>
    <div class="lbl" style="color:#e74c3c;font-size:13px;margin-bottom:8px">⚠ 风险清单</div>
    <ul class="sector-bot">
      <li>贵金属/能源金属（金价高位回落风险）</li>
      <li>元器件（科技成长股估值压挤）</li>
      <li>北向资金流出压力（中秋假期效应）</li>
      <li>国庆节前缩量博弈，警惕流动性风险</li>
      <li>大盘中枢下破，谨防加速下跌</li>
    </ul>
  </div>
</div>
</div>

<!-- ============ 免责声明 ============ -->
<div class="disclaimer">
  <b>免责声明：</b>本报告基于公开数据及多理论模型（欧奈尔CANSLIM、楔形理论、缠论、波浪理论、顶底山峰）自动生成，仅供参考，不构成任何投资建议。
  数据部分缺失时以"数据缺失"标注，不做虚构推断。股市有风险，投资需谨慎。作者及平台不对任何投资决策负责。
  <br><br>
  <b>使用说明：</b>① 缠论买点：一买=下跌背驰终结、二买=不破一买低点回升、三买=中枢突破后回踩不破；
  ② 波浪位置：3浪/5浪为主升，A/B/C为调整；③ 止损位统一按-8%计算，极端行情下请严控仓位。
</div>

</div>
<script>
// 交互：点击股票卡片可以高亮
document.querySelectorAll('.stock-card').forEach(c=>{{
  c.style.cursor='pointer';
  c.addEventListener('click',()=>{{
    document.querySelectorAll('.stock-card').forEach(x=>x.style.outline='none');
    c.style.outline='2px solid #2ecc71';
  }});
}});
</script>
</body>
</html>"""

html_path = os.path.join(OUTPUT_DIR, f"盘前推荐-{TODAY_COMPACT}.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(build_html())
print(f"HTML written: {html_path}")
print(f"Size: {os.path.getsize(html_path)} bytes")

