# -*- coding: utf-8 -*-
"""生成A股推荐观察清单图片（精确数字）"""
from PIL import Image, ImageDraw, ImageFont

# 字体路径
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# 画布尺寸
W, H = 1200, 1700
BG = (12, 22, 48)          # 深蓝背景
CARD = (22, 38, 72)        # 卡片背景
CARD_BORDER = (40, 65, 110)
ORANGE = (255, 140, 40)    # 进攻标签
GREEN = (46, 204, 113)     # 防御标签 / 涨
RED = (231, 76, 60)        # 跌 / 止损
GOLD = (241, 196, 15)      # 止盈
WHITE = (255, 255, 255)
GRAY = (160, 175, 200)
SUBTLE = (110, 130, 160)

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def text(draw, xy, s, f, fill=WHITE, **kw):
    draw.text(xy, s, font=f, fill=fill, **kw)

def rounded_rect(draw, xy, r, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

def draw_stock_card(draw, x, y, w, h, stock):
    """绘制单只股票卡片"""
    # 卡片背景
    rounded_rect(draw, (x, y, x+w, y+h), 14, fill=CARD, outline=CARD_BORDER, width=2)

    # 策略标签
    tag = stock["tag"]
    tag_color = ORANGE if tag == "进攻" else GREEN
    tag_w = 90
    rounded_rect(draw, (x+w-tag_w-20, y+18, x+w-20, y+18+32), 8, fill=tag_color)
    text(draw, (x+w-tag_w-20+18, y+22), tag, font(20, bold=True), fill=WHITE)

    # 股票名称 + 代码
    text(draw, (x+24, y+20), stock["name"], font(30, bold=True), fill=WHITE)
    text(draw, (x+24+len(stock["name"])*32+10, y+28), stock["code"], font(18), fill=GRAY)

    # 现价 + 涨跌幅
    price_y = y + 70
    text(draw, (x+24, price_y), "现价:", font(20), fill=GRAY)
    text(draw, (x+24+70, price_y-4), stock["price"], font(34, bold=True), fill=WHITE)
    chg_color = GREEN if stock["chg"].startswith("+") else RED
    text(draw, (x+24+70+len(stock["price"])*22+12, price_y+2), stock["chg"], font(24, bold=True), fill=chg_color)

    # 开高低
    oh_y = price_y + 48
    text(draw, (x+24, oh_y), f"今开{stock['open']} | 最高{stock['high']} | 最低{stock['low']}", font(18), fill=SUBTLE)

    # 买卖点行
    bp_y = oh_y + 34
    text(draw, (x+24, bp_y), "买点:", font(18), fill=GRAY)
    text(draw, (x+24+62, bp_y), stock["buy"], font(18, bold=True), fill=GREEN)

    cur_x = x+24+62+len(stock["buy"])*11+16
    if stock.get("stop"):
        text(draw, (cur_x, bp_y), "止损:", font(18), fill=GRAY)
        text(draw, (cur_x+52, bp_y), stock["stop"], font(18, bold=True), fill=RED)
        cur_x += 52+len(stock["stop"])*11+16
    if stock.get("tp"):
        text(draw, (cur_x, bp_y), "止盈:", font(18), fill=GRAY)
        text(draw, (cur_x+52, bp_y), stock["tp"], font(18, bold=True), fill=GOLD)

    # 指标行
    metric_y = bp_y + 32
    text(draw, (x+24, metric_y), stock["metrics"], font(18), fill=SUBTLE)

    # 理由
    reason_y = metric_y + 32
    text(draw, (x+24, reason_y), "理由:", font(18), fill=GRAY)
    text(draw, (x+24+58, reason_y), stock["reason"], font(18), fill=(200, 210, 230))

    # 右侧迷你折线
    draw_mini_chart(draw, x+w-130, y+h-70, stock["chg"].startswith("+"))

def draw_mini_chart(draw, x, y, up=True):
    """绘制迷你折线图"""
    import random
    random.seed(42)
    pts = []
    base = y + 40
    for i in range(12):
        px = x + i * 10
        if up:
            py = base - (i * 2.5 + random.randint(-3, 5))
        else:
            py = base - (10 - i) * 2.5 + random.randint(-3, 5)
        pts.append((px, py))
    color = GREEN if up else RED
    for i in range(len(pts)-1):
        draw.line([pts[i], pts[i+1]], fill=color, width=2)
    # 末端箭头
    draw.polygon([(pts[-1][0], pts[-1][1]-5),
                  (pts[-1][0]-4, pts[-1][1]+3),
                  (pts[-1][0]+4, pts[-1][1]+3)], fill=color)

# 股票数据
stocks = [
    {"name": "宁德时代", "code": "300750", "tag": "进攻",
     "price": "305.56", "chg": "+2.85%",
     "open": "298.00", "high": "308.69", "low": "297.74",
     "buy": "300 / 293 / 286", "stop": "280", "tp": "325 / 335",
     "metrics": "量比0.99 | 换手0.97% | TTM PE 16.63",
     "reason": "超跌反弹(20日-18.9%)，资金净流入6.96亿，缩量上攻抛压轻"},
    {"name": "浪潮信息", "code": "000977", "tag": "进攻",
     "price": "72.21", "chg": "+0.50%",
     "open": "73.00", "high": "73.46", "low": "72.05",
     "buy": "71 / 69 / 67", "stop": "65", "tp": "78 / 80",
     "metrics": "量比1.06 | 换手3.36% | TTM PE 23.22",
     "reason": "高开冲高回落，主力净流入0.39亿护盘，5日涨5%后获利盘压力"},
    {"name": "比亚迪", "code": "002594", "tag": "进攻",
     "price": "86.55", "chg": "+1.56%",
     "open": "85.59", "high": "87.20", "low": "85.46",
     "buy": "85 / 83 / 81", "stop": "79", "tp": "93 / 95",
     "metrics": "量比1.50(放量) | 换手0.86% | TTM PE 26.81",
     "reason": "放量稳步上行，资金净流入3.95亿，60日涨9.09%趋势健康"},
    {"name": "中国神华", "code": "601088", "tag": "防御",
     "price": "47.52", "chg": "+1.54%",
     "open": "46.43", "high": "47.60", "low": "46.15",
     "buy": "47 / 46.5 / 46", "stop": "收息无止损", "tp": "",
     "metrics": "股息率4.29% | TTM PE 19.09 | 年初至今+20.39%",
     "reason": "低开V型反转，防御属性突出，高股息压舱"},
    {"name": "贵州茅台", "code": "600519", "tag": "防御",
     "price": "1254.50", "chg": "+0.15%",
     "open": "1252.15", "high": "1265.88", "low": "1248.10",
     "buy": "1250 / 1220 / 1190", "stop": "收息无止损", "tp": "",
     "metrics": "股息率4.15% | TTM PE 19.26 | 20日-3.79%",
     "reason": "缩量窄幅震荡蓄势，估值合理，盘中已触及1250买点"},
]

# 创建画布
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# 顶部红色装饰条
draw.rectangle([(0, 0), (W, 6)], fill=(220, 50, 50))

# 标题
text(draw, (40, 30), "A股推荐观察清单", font(52, bold=True), fill=WHITE)
text(draw, (40, 92), "2026-09-22  ｜  双轨制策略：进攻仓 + 高股息防御仓", font(22), fill=GRAY)

# 卡片布局
card_w = W - 80
card_h = 230
gap = 20
start_y = 150

for i, s in enumerate(stocks):
    y = start_y + i * (card_h + gap)
    draw_stock_card(draw, 40, y, card_w, card_h, s)

# 底部免责声明
footer_y = start_y + len(stocks) * (card_h + gap) + 20
text(draw, (40, footer_y),
     "数据来源：通达信实时行情（2026-09-22 14:21）  ｜  仅供研究参考，不构成投资建议，市场有风险，决策需谨慎",
     font(16), fill=SUBTLE)

# 保存
out = "/workspace/recommend_astock_20260922.jpg"
img.save(out, "JPEG", quality=95)
print(f"saved: {out}  size={img.size}")
