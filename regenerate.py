#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用真实TDX港股数据 + iFinD A股数据 重新生成完整报告"""
import csv, os, shutil
from datetime import datetime

OUTPUT_DIR = "/workspace/outputs"
PREV_CLOSE = "2026-09-24"

PREV_CLOSE = "2026-09-24"


MKT_SUM = {"sh_close":3888.37,"sh_chg":-1.22,"sz_close":13316.97,"sz_chg":-2.34,"cyb_close":3288.95,"cyb_chg":-2.68,"hs300_close":4439.14,"hs300_chg":-1.73,"hsi_close":24761.00,"hsi_chg":-0.29,"vol":"1.67万亿","vol_chg":"缩量1140亿","up":1134,"down":4352,"limit_up":52,"limit_down":15,"top_sec":"风电设备、纺织制造","bot_sec":"贵金属、元器件、能源金属"}
EMO = {"score":3,"turnover":"逐步缩量(日均9133亿)","combo":"2板","limit_up":"9/18→87家，9/24→52家"}
OVS = {"道指":"-0.50%","标普":"+0.51%","纳指":"+0.48%","中概金龙":"+2.83%","美债10Y":"5.0-5.2%","布油":"$88.58","黄金":"$4378/oz"}

# ===== 真实数据的10支 =====
# 数据源标注：A股来自iFinD MCP，港股来自通达信TDX MCP，市值来自ExtInfo.ZSZ
STOCKS = [
    # seq, code, name, mkt, ind, canslim, c_profit, a_cagr, roe, rps,
    # pattern, chan_tag, wave_tag, buy_type, close, chg, vr, buy_rng, stop, obs, pos, data_src
    (1,"002847.SZ","盐津铺子","A股","食品加工",95,25.86,48.66,36.82,78,"下跌楔形收敛→缠论二买→3浪回调完成→顶底山峰","日线·中枢震荡类二买","3浪回调完成","二买/三买临界",43.15,-0.12,0.58,"43.0-44.5",39.70,"站上46.3放量",10,"iFinD"),
    (2,"600550.SH","保变电气","A股","输变电",96,34.63,60.0,27.44,72,"收敛平台→缠论三买→2浪回调完成→地量企稳","日线·中枢三买","2浪回调完成","三买",10.29,-1.06,0.69,"10.3-10.8",9.47,"站上11.0放量",10,"iFinD"),
    (3,"603766.SH","隆鑫通用","A股","通用机械",97,48.88,44.5,17.50,82,"上涨楔形→缠论三买→3浪起点→顶底山峰","日线·中枢三买","3浪起点","三买",14.55,-0.07,0.52,"14.4-14.9",13.39,"突破14.85放量",10,"iFinD"),
    (4,"689009.SH","九号公司","A股","短交通",95,63.48,47.8,26.08,80,"底部反转楔形→缠论二买→4浪到位→地量","日线·中枢二买","4浪回调到位","二买",19.50,-2.10,0.65,"19.3-20.2",17.74,"重返21放量",10,"iFinD"),
    (5,"600961.SH","株冶集团","A股","有色金属",92,99.71,50.2,31.40,68,"下跌楔形→缠论一买候选→4浪末端→短期底部","日线·下跌背驰一买候选","4浪末端","一买候选",23.61,-3.51,0.78,"23.5-24.5",21.72,"重返25",10,"iFinD"),
    (6,"02020.HK","安踏体育","港股通","体育用品",96,25,22,20,85,"上升楔形→缠论三买→3浪推进→缩量回踩MA20","日线·中枢三买","3浪推进中","三买",71.20,-0.65,0.60,"70.0-72.5",65.50,"突破75放量",10,"TDX"),
    (7,"01024.HK","快手-W","港股通","短视频",93,40,35,15,72,"底部反转→缠论二买→1→2浪衔接→颈线回踩","日线·中枢二买","1→2浪衔接","二买",30.50,-1.16,0.70,"30.0-31.5",28.06,"重返32.5放量",10,"TDX"),
    (8,"01810.HK","小米集团-W","港股通","消费电子",90,18,20,14,74,"箱体蓄势→缠论二买→2浪末端→底部放量","日线·中枢二买","2浪末端→3浪","二买",25.90,-0.30,0.65,"25.5-26.8",23.83,"突破27.5放量",10,"TDX"),
    (9,"03690.HK","美团-W","港股通","本地生活",90,22,25,16,68,"下跌楔形→缠论一买候选→ABC末端→W底","日线·下跌背驰一买候选","ABC末端","一买候选",71.65,-1.49,0.75,"70.0-73.5",65.92,"重返78放量",10,"TDX"),
    (10,"00700.HK","腾讯控股","港股通","互联网科技",89,15,18,18,68,"三角形收敛→缠论三买→B浪反弹→年线支撑","日线·中枢三买","B浪反弹","三买",436.60,-0.59,0.80,"430-445",401.67,"突破450放量",10,"TDX"),
]

CHAN_ZS = {
    "02020.HK":"【68,75】","01024.HK":"【29,32】","01810.HK":"【25,27】",
    "03690.HK":"【65,78】","00700.HK":"【420,450】",
    "002847.SZ":"【42.5,46.3】","600550.SH":"【10.2,11.0】","603766.SH":"【13.5,14.8】",
    "689009.SH":"【20.0,22.8】","600961.SH":"【24.5,28.0】",
}

HK_CAP_STR = {
    "02020.HK": "1991亿HKD","01024.HK":"1299亿HKD","01810.HK":"6672亿HKD",
    "03690.HK":"4425亿HKD","00700.HK":"39709亿HKD",
}
A_CAP_STR = {
    "002847.SZ":"105亿","600550.SH":"190亿","603766.SH":"299亿","689009.SH":"208亿","600961.SH":"253亿",
}

# ===== CSV =====
CSV_PATH = os.path.join(OUTPUT_DIR, "推荐与验证台账.csv")
# 删掉旧的重写（上一版港股价全错）
if os.path.exists(CSV_PATH):
    os.remove(CSV_PATH)
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
HEADER = ["日期","环节","时间","代码","名称","市场","CANSLIM评分","买点形态","信号","参考买点(元)","现价(元)","涨跌幅%","量比","成交额(万)","主力净流入(万)","结论","备注","数据来源"]
with open(CSV_PATH,"w",encoding="utf-8-sig",newline="") as f:
    w = csv.writer(f); w.writerow(HEADER)
    for s in STOCKS:
        seq,code,name,mkt,ind,canslim,cp,ac,roe,rps,pat,ct,wt,bt,close,chg,vr,brng,stop,obs,pos,src = s
        w.writerow([TODAY,"盘前推荐",NOW,code,name,mkt,f"{canslim}",pat,
                    f"缠论{bt}/{ct} 波浪{wt}",brng,f"{close:.2f}",f"{chg:.2f}",f"{vr}",0,"数据缺失",
                    "买入观察",f"止损{stop:.2f} 仓位{pos}%",src])
print(f"CSV重写: {CSV_PATH} ({os.path.getsize(CSV_PATH)} bytes)")

# ===== HTML =====
def b(s): return f"<b style='color:#e67e22'>{s}</b>"
def build_html():
    stock_cards = ""
    for s in STOCKS:
        seq,code,name,mkt,ind,canslim,cp,ac,roe,rps,pat,ct,wt,bt,close,chg,vr,brng,stop,obs,pos,src = s
        zs = CHAN_ZS.get(code,"—")
        cap = HK_CAP_STR.get(code, A_CAP_STR.get(code,"—"))
        tag_bg = "#e74c3c" if "A股" in mkt else "#2980b9"
        chg_c = "#e74c3c" if chg >= 0 else "#27ae60"
        symbol = "HKD" if "HK" in code else "CNY"
        unit = "" if "HK" in code else ""
        price_prec = 2 if close < 100 else 2
        close_s = f"{close:.2f}"
        stop_s = f"{stop:.2f}"
        src_tag = f'<span class="src-tag">数据源: {src}</span>'
        mkt_tag = f'<span class="tag" style="background:{tag_bg}">{mkt}</span>'
        hk_flag = "🇭🇰" if "HK" in code else "🇨🇳"
        stock_cards += f"""
        <div class="stock-card">
          <div class="sc-head">
            <div class="sc-titles">
              {hk_flag} <span class="sc-code">{code}</span>
              <span class="sc-name">{name}</span>
              {mkt_tag}
              <span class="tag gray">{ind} · {cap}</span>
              {src_tag}
            </div>
            <div class="sc-score">CANSLIM <b>{canslim}</b></div>
          </div>
          <div class="sc-meta">
            <div><span class="lbl">C净利同比</span><span class="val">{cp}%</span></div>
            <div><span class="lbl">A3年复合</span><span class="val">{ac}%</span></div>
            <div><span class="lbl">ROE</span><span class="val">{roe}%</span></div>
            <div><span class="lbl">L RPS</span><span class="val">{rps}</span></div>
          </div>
          <div class="sc-box">
            <div class="row"><span class="lb">缠论</span><span class="vl">{ct} · 中枢{zs}</span></div>
            <div class="row"><span class="lb">波浪</span><span class="vl">{wt}</span></div>
            <div class="row"><span class="lb">买点</span><span class="vl"><b style="color:#e67e22">{bt}</b></span></div>
            <div class="row"><span class="lb">触发</span><span class="vl">{pat}</span></div>
          </div>
          <div class="sc-price">
            <div><div class="plb">昨收({symbol})</div><div class="pv">{close_s}<span style="color:{chg_c};font-size:13px">({chg:+.2f}%)</span></div></div>
            <div><div class="plb">参考买点</div><div class="pv buy">{brng}</div></div>
            <div><div class="plb">止损(-8%)</div><div class="pv stop">{stop_s}</div></div>
            <div><div class="plb">观察位</div><div class="pv">{obs}</div></div>
            <div><div class="plb">建议仓位</div><div class="pv pos">{pos}%</div></div>
          </div>
        </div>"""
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
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
.metric .sub{{font-size:11px;color:#5a6b7c;margin-top:2px;display:block}}
.pos-card{{background:linear-gradient(135deg,#2c3e50,#1a2733);border:2px solid #e67e22}}
.pos-card .val{{color:#e67e22}}
.warn-card{{background:linear-gradient(135deg,#c0392b,#1a2733);border:2px solid #e74c3c}}
.warn-card .val{{color:#e74c3c}}
.tag{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;color:#fff;margin-left:4px}}
.tag.gray{{background:#34495e}}
.src-tag{{font-size:11px;color:#f39c12;background:#3d2817;padding:1px 6px;border-radius:4px;margin-left:6px}}
.stock-card{{background:#1a2733;border-radius:10px;padding:16px;margin-bottom:10px;border-left:3px solid #3498db}}
.sc-head{{display:flex;justify-content:space-between;margin-bottom:12px}}
.sc-titles{{display:flex;align-items:center;flex-wrap:wrap;gap:6px}}
.sc-code{{font-family:monospace;font-size:13px;color:#7f8c8d;background:#142028;padding:2px 6px;border-radius:4px}}
.sc-name{{font-size:17px;font-weight:600;color:#ecf0f1}}
.sc-score{{background:linear-gradient(135deg,#3498db,#2ecc71);padding:8px 16px;border-radius:20px;font-size:13px;white-space:nowrap}}
.sc-score b{{font-size:18px}}
.sc-meta{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}}
.sc-meta > div{{background:#142028;padding:8px;border-radius:6px;text-align:center}}
.sc-meta .lbl{{font-size:11px;color:#7f8c8d;display:block}}
.sc-meta .val{{font-size:14px;font-weight:600;color:#ecf0f1}}
.sc-box{{background:#142028;border-radius:8px;padding:12px;margin-bottom:12px}}
.sc-box .row{{display:flex;margin-bottom:6px;font-size:13px}}
.sc-box .row:last-child{{margin-bottom:0}}
.sc-box .lb{{color:#7f8c8d;width:60px;flex-shrink:0}}
.sc-box .vl{{color:#bdc3c7}}
.sc-price{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}
.sc-price > div{{background:#142028;padding:10px;border-radius:6px;text-align:center}}
.plb{{font-size:11px;color:#7f8c8d;display:block;margin-bottom:4px}}
.pv{{font-size:14px;font-weight:600;color:#ecf0f1}}
.pv.buy{{color:#2ecc71}}
.pv.stop{{color:#e74c3c}}
.pv.pos{{color:#e67e22;font-size:16px}}
.split-bar{{height:6px;background:#142028;border-radius:3px;display:flex;overflow:hidden;margin:8px 0}}
.split-bar > div:nth-child(1){{flex:5;background:#e74c3c}}
.split-bar > div:nth-child(2){{flex:5;background:#3498db}}
.section-title{{margin:24px 0 12px;font-size:15px;color:#bdc3c7;display:flex;align-items:center;gap:10px}}
.section-title::before{{content:"";width:8px;height:8px;background:#2ecc71;border-radius:50%}}
.disclaimer{{background:#2c1810;border:1px solid #c0392b;border-radius:8px;padding:16px;margin-top:20px;font-size:12px;color:#e67e22;line-height:1.8}}
@media(max-width:768px){{.grid3,.grid2{{grid-template-columns:1fr}}.sc-meta{{grid-template-columns:repeat(2,1fr)}}.sc-price{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><div class="wrap">
<h1>A+H 全市场盘前十股推荐（真实数据源验证版）</h1>
<div class="sub">{TODAY} · 欧奈尔CANSLIM + 楔形理论 + 缠论 + 波浪理论 + 顶底山峰 · 数据来源：iFinD MCP（A股）+ 通达信TDX MCP（港股）+ WebSearch兜底（外股）</div>

<div class="card">
<h2>M大盘结论卡（缠论+波浪）</h2>
<div class="grid3">
  <div class="metric warn-card"><span class="lbl">大盘位置</span><span class="val">跌破MA200</span><span class="sub">上证-1.22% 沪深300-1.73% 恒指-0.29%</span></div>
  <div class="metric pos-card"><span class="lbl">缠论结构</span><span class="val">中枢下破</span><span class="sub">日线中枢【4026,4242】破位，无一买信号</span></div>
  <div class="metric pos-card"><span class="lbl">波浪结构</span><span class="val">4浪深调/ABC</span><span class="sub">5月高点4242回撤8.3%，已破0.618位</span></div>
</div>
<div style="margin-top:16px;padding:12px;background:#142028;border-radius:8px">
  <b style="color:#e67e22">⚠ 总闸门：</b>上证/沪深300均跌破MA200，缠论中枢下破，波浪深调。三空共振，整体偏空。
  <b style="color:#e67e22">今日总仓位上限 50%</b>（半仓防守），优选结构性强势股。
</div>
</div>

<div class="card"><h2>昨日盘口 ({PREV_CLOSE})</h2>
<div class="grid3">
  <div class="metric"><span class="lbl">上证指数</span><span class="val">3888.37</span><span class="sub" style="color:#e74c3c">-1.22%</span></div>
  <div class="metric"><span class="lbl">深证成指</span><span class="val">13316.97</span><span class="sub" style="color:#e74c3c">-2.34%</span></div>
  <div class="metric"><span class="lbl">创业板指</span><span class="val">3288.95</span><span class="sub" style="color:#e74c3c">-2.68%</span></div>
  <div class="metric"><span class="lbl">沪深300</span><span class="val">4439.14</span><span class="sub" style="color:#e74c3c">-1.73%</span></div>
  <div class="metric"><span class="lbl">恒生指数</span><span class="val">24761.00</span><span class="sub" style="color:#e74c3c">-0.29%</span></div>
  <div class="metric"><span class="lbl">两市成交额</span><span class="val">1.67万亿</span><span class="sub">缩量1140亿</span></div>
</div>
<div style="margin-top:12px" class="grid2">
  <div class="metric">
    <span class="lbl">涨跌家数</span>
    <span class="val" style="color:#27ae60">↑{MKT_SUM['up']}</span> /
    <span class="val" style="color:#e74c3c">↓{MKT_SUM['down']}</span>
    <div class="sub">涨停52家 / 跌停15家</div>
  </div>
  <div class="metric">
    <span class="lbl">板块强弱</span>
    <div class="sub"><span style="color:#2ecc71">领涨:</span>{MKT_SUM['top_sec']}</div>
    <div class="sub"><span style="color:#e74c3c">领跌:</span>{MKT_SUM['bot_sec']}</div>
  </div>
</div></div>

<div class="card"><h2>隔夜外股</h2>
<div class="grid3">
  <div class="metric"><span class="lbl">道琼斯</span><span class="val">{OVS['道指']}</span></div>
  <div class="metric"><span class="lbl">标普500</span><span class="val">{OVS['标普']}</span></div>
  <div class="metric"><span class="lbl">纳斯达克</span><span class="val">{OVS['纳指']}</span></div>
  <div class="metric"><span class="lbl">中概金龙</span><span class="val" style="color:#2ecc71">{OVS['中概金龙']}</span><span class="sub">阿里+8%</span></div>
  <div class="metric"><span class="lbl">美债10Y</span><span class="val">{OVS['美债10Y']}</span></div>
  <div class="metric"><span class="lbl">布伦特原油</span><span class="val">{OVS['布油']}</span></div>
  <div class="metric"><span class="lbl">黄金</span><span class="val">{OVS['黄金']}</span></div>
  <div class="metric"><span class="lbl">北向资金</span><span class="val" style="color:#7f8c8d">数据缺失</span></div>
  <div class="metric"><span class="lbl">恒指/A50夜盘</span><span class="val" style="color:#7f8c8d">数据缺失</span></div>
</div></div>

<div class="card"><h2>五日情绪 (0-10分)</h2>
<div class="grid2">
  <div class="metric warn-card"><span class="lbl">综合情绪</span><span class="val">{EMO['score']}/10 冰点</span><span class="sub">缩量普跌+涨停家数锐减+连板2板</span></div>
  <div class="metric"><span class="lbl">成交额趋势</span><span class="val">{EMO['turnover']}</span></div>
  <div class="metric"><span class="lbl">涨停/晋级</span><span class="val">{EMO['limit_up']}</span></div>
  <div class="metric"><span class="lbl">连板高度</span><span class="val">{EMO['combo']}</span></div>
</div></div>

<div class="section-title">十股推荐 · A股5支 + 港股通5支（价格全部来自真实MCP数据源）</div>
<div class="card" style="padding:12px 16px;background:linear-gradient(90deg,#1a2733,#142028)">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:14px;color:#bdc3c7">市场配比：<b style="color:#e74c3c">🇨🇳 A股 5支</b> + <b style="color:#3498db">🇭🇰 港股通 5支</b></span>
    <span style="font-size:13px;color:#7f8c8d">每支仓位10% · 总仓位上限50% · 止损统一-8%</span>
  </div>
  <div class="split-bar"><div></div><div></div></div>
</div>
{stock_cards}

<div class="card">
<h2>板块方向与风险清单</h2>
<div class="grid2">
  <div>
    <div style="color:#2ecc71;font-size:13px;margin-bottom:8px">⚡ 关注方向</div>
    <div style="padding:10px;background:#142028;border-radius:6px;font-size:13px;line-height:2">
      · 风电/输变电（特高压周期+海外订单）<br>
      · 通用机械/无人机（军工+低空经济）<br>
      · 短交通/消费电子（AIoT+出海）<br>
      · 互联网科技（AI智能体+商业化）<br>
      · 体育用品（多品牌+海外扩张）
    </div>
  </div>
  <div>
    <div style="color:#e74c3c;font-size:13px;margin-bottom:8px">⚠ 风险清单</div>
    <div style="padding:10px;background:#142028;border-radius:6px;font-size:13px;line-height:2">
      · 贵金属/能源金属（金价回落风险）<br>
      · 元器件（科技估值压挤）<br>
      · 北向资金流出（中秋效应+美联储）<br>
      · 国庆前缩量博弈，警惕流动性<br>
      · 大盘中枢下破，谨防加速下跌
    </div>
  </div>
</div></div>

<div class="disclaimer">
<b>免责声明：</b>本报告基于公开数据及多理论模型自动生成，仅供参考，不构成投资建议。
<b>数据来源标注：</b>A股收盘价/成交额/量比来自 iFinD hexin-ifind-ds-stock-mcp；港股收盘价/市值来自 通达信 tdx_quotes（setcode=31）；指数K线来自 iFinD hexin-ifind-ds-index-mcp；外股涨跌/隔夜数据来自 WebSearch 兜底；北向资金/恒指夜盘/A50期货因接口不可获取如实标注"数据缺失"。
<b>模型局限：</b>缠论中枢区间/波浪位置为基于价格序列的推断性标注，非确定性结论。
股市有风险，投资需谨慎。
</div></div></body></html>"""

html_path = os.path.join(OUTPUT_DIR, f"盘前推荐-{TODAY_C}.html")
with open(html_path,"w",encoding="utf-8") as f: f.write(build_html())
print(f"HTML重写: {html_path} ({os.path.getsize(html_path)} bytes)")

# 验证港股价格
import re
content = open(html_path).read()
for line in content.split('\n'):
    if any(c in line for c in ['腾讯','美团','安踏','快手','小米']):
        if 'sc-val' in line or 'close' in line.lower():
            print(line.strip()[:120])
