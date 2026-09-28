#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML盘前推荐报告 + CSV台账生成器"""
import csv
import os
from datetime import datetime

OUTPUT_DIR = "/workspace/outputs"
TODAY = "2026-09-28"
TODAY_COMPACT = "20260928"
PREV_CLOSE = "2026-09-24"

# ================== 数据（同前两脚本，自包含） ==================
MARKET_SUMMARY = {
    "sh_close": 3888.37, "sh_change": -1.22,
    "sz_close": 13316.97, "sz_change": -2.34,
    "cyb_close": 3288.95, "cyb_change": -2.68,
    "hs300_close": 4439.14, "hs300_change": -1.73,
    "total_volume": "1.67万亿", "volume_change": "缩量1140亿",
    "up_count": 1134, "down_count": 4352,
    "limit_up": 52, "limit_down": 15,
    "north_flow": "数据缺失",
    "top_sectors": ["风电设备", "纺织制造"],
    "bottom_sectors": ["贵金属", "元器件", "能源金属"],
}

MARKET_STRUCTURE = {
    "ma200": "跌破（上证3888 vs MA200~4000，沪深300 4439 vs MA200~4700）",
    "chanlun_level": "日线级别",
    "chanlun_zs": "【4026, 4242】（2026年4-5月中枢）",
    "chanlun_pos": "3888跌破中枢下沿，中枢下破，无一买信号",
    "wave": "4浪深调或A浪启动（5月高点4242回撤8.3%，已破0.618回撤位4024）",
    "conclusion": "MA200跌破+中枢下破+波浪深调，三空共振，整体偏空。总仓位50%防守。",
    "position_pct": 50,
}

EMOTION_5D = {
    "turnover_trend": "逐步缩量（近5日日均9133亿）",
    "limit_up_change": "9/18涨停87家→9/24仅52家，晋级率下滑",
    "up_ratio": "9/24上涨仅21%（1134/5486）",
    "combo_height": "连板高度2板（内蒙一机）",
    "score": 3,
}

OVERSEAS = {
    "道指": ("-0.50%", "跌162点，涨跌不一"),
    "标普500": ("+0.51%", "微涨"),
    "纳指": ("+0.48%", "微涨"),
    "中概金龙": ("+2.83%", "阿里+8%领涨，中概反弹"),
    "美债10Y": ("5.0-5.2%", "高位震荡"),
    "布伦特原油": ("$88.58/桶", "回落"),
    "黄金": ("$4378/盎司", "高位整理"),
}

# 最终10支
STOCKS = [
    # --- A股5支 ---
    {
        "seq": 1, "code": "002847.SZ", "name": "盐津铺子", "market": "A股",
        "industry": "食品加工/烘焙", "cap": "105亿",
        "canslim": 95, "c_profit": 25.86, "a_cagr": 48.66, "roe": 36.82, "rps": 78,
        "north": "北向稳定",
        "pattern": "下跌楔形收敛末端", "pattern_detail": "9/16低点42.94后缩量横盘，楔形下轨收敛",
        "chan": {"buy_type": "二买/三买临界", "zhongshu": "【42.5, 46.3】", "tag": "日线·中枢震荡类二买"},
        "wave": "主升浪3浪回调到位（ABC调整C浪末端）", "wave_tag": "3浪回调完成",
        "peak_bottom": "阶段新低后缩量企稳MA20",
        "close_924": 43.15, "change_924": -0.12, "vr": 0.58,
        "buy_range": "43.0-44.5", "stop_loss": 39.70, "observe": "放量站上46.3",
        "position_pct": 10,
        "trigger": ["楔形收敛", "缠论二买", "波浪回调到位", "顶底山峰企稳"],
    },
    {
        "seq": 2, "code": "600550.SH", "name": "保变电气", "market": "A股",
        "industry": "输变电设备", "cap": "190亿",
        "canslim": 96, "c_profit": 34.63, "a_cagr": 60.0, "roe": 27.44, "rps": 72,
        "north": "QFII新进",
        "pattern": "收敛平台整理，突破在即", "pattern_detail": "9/18放量涨停后回踩，平台10.3-11.0收敛",
        "chan": {"buy_type": "三买", "zhongshu": "【10.2, 11.0】", "tag": "日线·中枢三买"},
        "wave": "主升浪2浪回调完成，酝酿3浪", "wave_tag": "2浪回调完成"},
        "peak_bottom": "缩量至地量企稳，量能萎缩",
        "close_924": 10.29, "change_924": -1.06, "vr": 0.69,
        "buy_range": "10.3-10.8", "stop_loss": 9.47, "observe": "放量站上11.0",
        "position_pct": 10,
        "trigger": ["平台收敛", "缠论三买", "波浪2浪完成", "地量企稳"],
    },
    {
        "seq": 3, "code": "603766.SH", "name": "隆鑫通用", "market": "A股",
        "industry": "通用机械/无人机", "cap": 299亿,
        "canslim": 97, "c_profit": 48.88, "a_cagr": 44.5, "roe": 17.50, "rps": 82,
        "north": "北向持续加仓",
        "pattern": "上涨楔形蓄势", "pattern_detail": "8/24放量暴涨+5.12%后缩量回踩MA10/20",
        "chan": {"buy_type": "三买", "zhongshu": "【13.5, 14.8】", "tag": "日线·中枢三买"},
        "wave": "主升浪3浪起点（1浪13.09→14.8，2浪回调14.55完成）", "wave_tag": "3浪起点"},
        "peak_bottom": "顶底山峰典型形态，MA10/20双支撑",
        "close_924": 14.55, "change_924": -0.07, "vr": 0.52,
        "buy_range": "14.4-14.9", "stop_loss": 13.39, "observe": "放量突破14.85",
        "position_pct": 10,
        "trigger": ["上涨楔形", "缠论三买", "波浪3浪起点", "顶底山峰"],
    },
    {
        "seq": 4, "code": "689009.SH", "name": "九号公司", "market": "A股",
        "industry": "短交通", "cap": 208亿,
        "canslim": 95, "c_profit": 63.48, "a_cagr": 47.8, "roe": 26.08, "rps": 80,
        "north": "北向持仓稳定",
        "pattern": "底部反转楔形", "pattern_detail": "9/16低点18.85后连续3天缩量企稳",
        "chan": {"buy_type": "二买", "zhongshu": "【20.0, 22.8】", "tag": "日线·中枢二买"},
        "wave": "4浪回调到位（ABC调整接近0.618位）", "wave_tag": "4浪回调到位"},
        "peak_bottom": "9/16低点后回踩MA20企稳，地量",
        "close_924": 19.50, "change_924": -2.10, "vr": 0.65,
        "buy_range": "19.3-20.2", "stop_loss": 17.74, "observe": "重返21以上放量",
        "position_pct": 10,
        "trigger": ["底部楔形", "缠论二买", "波浪4浪到位", "地量企稳"],
    },
    {
        "seq": 5, "code": "600961.SH", "name": "株冶集团", "market": "A股",
        "industry": "有色金属/锌", "cap": 253亿,
        "canslim": 92, "c_profit": 99.71, "a_cagr": 50.2, "roe": 31.40, "rps": 68,
        "north": "北向增持",
        "pattern": "下跌楔形接近支撑", "pattern_detail": "8/25放量急跌-6.2%后缩量横盘",
        "chan": {"buy_type": "一买候选", "zhongshu": "【24.5, 28.0】", "tag": "日线·下跌背驰一买候选"},
        "wave": "4浪回调末端（ABC调整接近尾声）", "wave_tag": "4浪末端"},
        "peak_bottom": "23.6-24.5构筑短期底部",
        "close_924": 23.61, "change_924": -3.51, "vr": 0.78,
        "buy_range": "23.5-24.5", "stop_loss": 21.72, "observe": "重返25以上",
        "position_pct": 10,
        "trigger": ["下跌楔形", "缠论一买候选", "波浪4浪末端", "短期底部"],
    },
    # --- 港股5支 ---
    {
        "seq": 6, "code": "02020.HK", "name": "安踏体育", "market": "港股通",
        "industry": "体育用品", "cap": "350亿港元",
        "canslim": 96, "c_profit": 25, "a_cagr": 22, "roe": 20, "rps": 85,
        "north": "南向加仓",
        "pattern": "上升楔形健康", "pattern_detail": "主升通道内缩量回踩MA20",
        "chan": {"buy_type": "三买", "zhongshu": "【70, 82】", "tag": "日线·中枢三买"},
        "wave": "主升浪3浪中后段", "wave_tag": "3浪推进中"},
        "peak_bottom": "缩量回踩MA10/20双支撑后放量",
        "close_924": 78.20, "change_924": -0.85, "vr": 0.60,
        "buy_range": "76-80", "stop_loss": 71.94, "observe": "突破82.5放量",
        "position_pct": 10,
        "trigger": ["上升楔形", "缠论三买", "波浪3浪", "顶底山峰"],
    },
    {
        "seq": 7, "code": "01024.HK", "name": "快手-W", "market": "港股通",
        "industry": "短视频/电商", "cap": "350亿港元",
        "canslim": 93, "c_profit": 40, "a_cagr": 35, "roe": 15, "rps": 72,
        "north": "南向关注",
        "pattern": "底部反转形态", "pattern_detail": "放量突破颈线44后缩量回踩",
        "chan": {"buy_type": "三买", "zhongshu": "【40, 46】", "tag": "日线·中枢三买"},
        "wave": "主升浪1浪末端/2浪起点", "wave_tag": "1→2浪衔接"},
        "peak_bottom": "47附近放量后缩量回踩MA10",
        "close_924": 44.80, "change_924": -1.30, "vr": 0.70,
        "buy_range": "44-46", "stop_loss": 41.22, "observe": "突破47放量",
        "position_pct": 10,
        "trigger": ["底部反转", "缠论三买", "波浪1→2浪", "颈线回踩"],
    },
    {
        "seq": 8, "code": "01810.HK", "name": "小米集团-W", "market": "港股通",
        "industry": "消费电子/汽车", "cap": "4000亿港元",
        "canslim": 90, "c_profit": 18, "a_cagr": 20, "roe": 14, "rps": 74,
        "north": "南向标配",
        "pattern": "箱体蓄势整理", "pattern_detail": "26-30区间横盘，下沿26.5买",
        "chan": {"buy_type": "二买", "zhongshu": "【26.5, 29.5】", "tag": "日线·中枢二买"},
        "wave": "主升浪2浪回调末端，蓄势3浪", "wave_tag": "2浪末端→3浪"},
        "peak_bottom": "26.5附近放量止跌构筑底部",
        "close_924": 27.40, "change_924": 0.50, "vr": 0.65,
        "buy_range": "26.5-28.0", "stop_loss": 25.21, "observe": "突破30放量",
        "position_pct": 10,
        "trigger": ["箱体蓄势", "缠论二买", "波浪2→3浪", "底部放量"],
    },
    {
        "seq": 9, "code": "03690.HK", "name": "美团-W", "market": "港股通",
        "industry": "本地生活", "cap": "1164亿港元",
        "canslim": 90, "c_profit": 22, "a_cagr": 25, "roe": 16, "rps": 68,
        "north": "南向活跃",
        "pattern": "下跌楔形收敛", "pattern_detail": "180→130下跌楔形末端，130强支撑",
        "chan": {"buy_type": "一买候选", "zhongshu": "【130, 155】", "tag": "日线·下跌背驰一买"},
        "wave": "4浪回调末端/ABC完成", "wave_tag": "ABC调整末端"},
        "peak_bottom": "130附近多次放量止跌，W底雏形",
        "close_924": 132.50, "change_924": -2.10, "vr": 0.75,
        "buy_range": "130-138", "stop_loss": 121.90, "observe": "重返150放量",
        "position_pct": 10,
        "trigger": ["下跌楔形", "缠论一买", "波浪ABC末端", "W底雏形"],
    },
    {
        "seq": 10, "code": "00700.HK", "name": "腾讯控股", "market": "港股通",
        "industry": "互联网科技", "cap": "3500亿港元",
        "canslim": 89, "c_profit": 15, "a_cagr": 18, "roe": 18, "rps": 68,
        "north": "南向净买入",
        "pattern": "收敛三角形整理", "pattern_detail": "年线附近缩量三角形收敛",
        "chan": {"buy_type": "三买", "zhongshu": "【360, 400】", "tag": "日线·中枢三买"},
        "wave": "ABC调整浪B浪反弹中", "wave_tag": "B浪反弹"},
        "peak_bottom": "340附近放量止跌，回踩MA20企稳",
        "close_924": 378.50, "change_924": 1.20, "vr": 0.80,
        "buy_range": "370-390", "stop_loss": 348.22, "observe": "突破400放量",
        "position_pct": 10,
        "trigger": ["三角形收敛", "缠论三买", "波浪B浪", "止跌企稳"],
    },
]

