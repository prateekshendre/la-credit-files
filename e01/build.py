"""LA Credit Files, Episode 1: LA runs more credit than you think.
Builds a 1080x1350 LinkedIn carousel (PNG per slide + one PDF) from SEC Form ADV data.
Usage: python3 e01/build.py   (run from repo root)
"""
import math, os, pandas as pd
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "e01", "out" if os.environ.get("THEME", "night") == "night" else "out_" + os.environ["THEME"])
os.makedirs(OUT, exist_ok=True)
d = pd.read_csv(os.path.join(ROOT, "data", "e01_form_adv_la_credit.csv"))
la = d[d.in_set == "LA"].copy()
left = d[d.in_set == "LEFT"].copy()

g = la.groupby("group").agg(raum=("raum_total", "sum"), pooled=("raum_pooled_vehicles", "sum"),
                            reg=("raum_registered_funds", "sum"), bdc=("raum_bdcs", "sum"),
                            area=("area", "first")).sort_values("raum", ascending=False)
g["B"] = g.raum / 1e9
g["priv"] = g.pooled / g.raum
g["regf"] = (g.reg + g.bdc) / g.raum
g["sma"] = 1 - g.priv - g.regf

TOTAL_T = la.raum_total.sum() / 1e12
EX_PIMCO_B = la[la.group != "PIMCO"].raum_total.sum() / 1e9
PIMCO_B = g.loc["PIMCO", "B"]
BUNKER_B = la[la.area == "Bunker Hill"].raum_total.sum() / 1e9
N_FIRMS = la.group.nunique()
WEST_B = la[la.area.isin(["Century City","West LA","Santa Monica","Marina del Rey"])].raum_total.sum() / 1e9
LEFT_B = left.raum_total.sum() / 1e9

THEMES = {
 # name: ink, accent, background, muted, rest-of-bar, body text, panel, text-on-accent
 "night": ("#EEF2F6", "#F2B33D", "#0D1B2A", "#8FA0B3", "#2A3B4F", "#C9D3DE", "#16273A", "#0D1B2A"),
 "slate": ("#13202E", "#E8682A", "#EDF0F3", "#66737F", "#CDD3DA", "#33414F", "#FFFFFF", "#FFFFFF"),
 "dodger": ("#111827", "#1D5BBF", "#FFFFFF", "#6B7280", "#D9DDE3", "#374151", "#F3F4F6", "#FFFFFF"),
}
THEME = os.environ.get("THEME", "night")
INK, ACC, BG, MUTE, LINE, BODY, PANEL, ONACC = THEMES[THEME]
SRC = "Source: SEC Form ADV, Item 5.F regulatory AUM, registered adviser roster Nov 2026."
N = 11

def fmtB(b):
    return f"${b/1000:.2f}T" if b >= 1000 else f"${b:,.0f}B" if b >= 10 else f"${b:.1f}B"

def frame(i, body, src=SRC):
    return f"""<section class="s"><div class="top"><span class="brand">LA CREDIT FILES <b>/ 01</b></span><span class="pg">{i}/{N}</span></div>
{body}<div class="foot"><span>{src}</span><span class="me">Prateek Shendre</span></div></section>"""

# ---------- slide 2: giant vs everyone ----------
def giant_svg():
    W, H = 900, 760
    mx = PIMCO_B * 1.08
    bars = [("PIMCO", PIMCO_B, ACC), (f"The other {N_FIRMS-1} combined", EX_PIMCO_B, INK)]
    bw, gap, base = 300, 150, 690
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    for k, (lab, v, c) in enumerate(bars):
        x = 75 + k * (bw + gap); h = (base - 60) * v / mx
        s += f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" fill="{c}"/>'
        s += f'<text x="{x+bw/2}" y="{base-h-34}" text-anchor="middle" class="big">{fmtB(v)}</text>'
        s += f'<text x="{x+bw/2}" y="{base+40}" text-anchor="middle" class="lab">{lab}</text>'
    s += f'<line x1="40" x2="{W-40}" y1="{base}" y2="{base}" stroke="{INK}" stroke-width="2"/></svg>'
    return s

# ---------- slide 3: ranked ex-PIMCO ----------
def rank_svg():
    r = g.drop("PIMCO")
    W, rowh, lab = 900, 62, 230
    H = rowh * len(r) + 10
    mx = r.B.max()
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    for k, (name, row) in enumerate(r.iterrows()):
        y = k * rowh + 8; w = (W - lab - 150) * row.B / mx
        c = ACC if k == 0 else INK
        s += f'<text x="{lab-16}" y="{y+32}" text-anchor="end" class="lab">{name}</text>'
        s += f'<rect x="{lab}" y="{y+8}" width="{max(w,4)}" height="36" fill="{c}"/>'
        s += f'<text x="{lab+max(w,4)+12}" y="{y+34}" class="val">{fmtB(row.B)}</text>'
    return s + "</svg>"

# ---------- slide 4: schematic map ----------
PTS = {"Westlake Village": (34.146, -118.806), "Santa Monica": (34.030, -118.470), "Marina del Rey": (33.980, -118.452),
       "West LA": (34.050, -118.445), "Century City": (34.058, -118.417), "Bunker Hill": (34.052, -118.253),
       "Pasadena": (34.146, -118.144), "Newport Beach": (33.616, -117.876)}
COAST = [(34.035, -118.95), (34.035, -118.78), (34.03, -118.60), (34.01, -118.50), (33.975, -118.46), (33.92, -118.42),
         (33.84, -118.40), (33.77, -118.42), (33.74, -118.36), (33.74, -118.28), (33.76, -118.19), (33.72, -118.07),
         (33.66, -118.00), (33.60, -117.88), (33.53, -117.77), (33.45, -117.68)]
def proj(lat, lon, W=960, H=760):
    x = (lon + 118.98) / (1.30) * W
    y = (34.42 - lat) / (0.95) * H
    return x, y

NODE = {"Westlake Village": "Westlake Village", "Santa Monica": "Westside", "Marina del Rey": "Westside", "West LA": "Westside",
        "Century City": "Westside", "Bunker Hill": "Bunker Hill", "Pasadena": "Pasadena", "Newport Beach": "Newport Beach"}
NPT = {"Westlake Village": (34.146, -118.806), "Westside": (34.035, -118.44), "Bunker Hill": (34.052, -118.253),
       "Pasadena": (34.146, -118.144), "Newport Beach": (33.616, -117.876)}
LAB = {"Westlake Village": (0, -1), "Westside": (0, 1), "Bunker Hill": (0, 1), "Pasadena": (0, -1), "Newport Beach": (-1, 0)}
ORDER = ["Westlake Village", "Westside", "Bunker Hill", "Pasadena", "Newport Beach"]
FIRMS_TXT = {"Westlake Village": ["PennyMac"], "Westside": ["Ares, Crescent,", "Cliffwater, Beach Point,", "Mesa West, Silver Rock"],
             "Bunker Hill": ["Oaktree, TCW,", "Payden & Rygel"], "Pasadena": ["Western Asset"], "Newport Beach": ["PIMCO"]}
def map_svg():
    W, H = 920, 640
    la["node"] = la.area.map(NODE)
    area = la.groupby("node").raum_total.sum() / 1e9
    rads = {n: min(max(14, 3.2 * math.sqrt(area[n])), 96) for n in ORDER}
    gap = (W - 2 * sum(rads.values())) / (len(ORDER) + 1)
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    cy = 250
    s += f'<line x1="0" x2="{W}" y1="{cy}" y2="{cy}" stroke="{LINE}" stroke-width="3" stroke-dasharray="6 8"/>'
    s += f'<text x="{W}" y="{cy-140}" text-anchor="end" class="mfirm">west to east</text>'
    x = gap
    for n in ORDER:
        r = rads[n]; cx = x + r
        c = ACC if n in ("Westside", "Bunker Hill") else INK
        s += f'<circle cx="{cx:.0f}" cy="{cy}" r="{r:.0f}" fill="{c}"/>'
        if n == "Westlake Village":
            tx, ty, anc = 0, cy - 190, "start"
        else:
            tx, ty, anc = cx, cy + 96 + 56, "middle"
        s += f'<text x="{tx:.0f}" y="{ty}" text-anchor="{anc}" class="mval2">{fmtB(area[n])}</text>'
        s += f'<text x="{tx:.0f}" y="{ty+36}" text-anchor="{anc}" class="mlab">{n}</text>'
        for j, ln in enumerate(FIRMS_TXT[n]):
            s += f'<text x="{tx:.0f}" y="{ty+64+26*j}" text-anchor="{anc}" class="mfirm">{ln}</text>'
        x = cx + r + gap
    return s + "</svg>"

# ---------- slide 5: two tribes ----------
def tribes_svg():
    r = g.sort_values("priv", ascending=False)
    W, rowh, lab = 900, 58, 230
    H = rowh * len(r) + 70
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    bw = W - lab - 20
    for k, (name, row) in enumerate(r.iterrows()):
        y = k * rowh + 6
        s += f'<text x="{lab-16}" y="{y+30}" text-anchor="end" class="lab">{name}</text>'
        x = lab
        for frac, c in ((row.priv, ACC), (row.regf, INK), (row.sma, LINE)):
            w = bw * max(frac, 0)
            s += f'<rect x="{x}" y="{y+8}" width="{w}" height="34" fill="{c}"/>'
            x += w
        s += f'<text x="{lab+8}" y="{y+32}" class="inbar">{row.priv*100:.0f}%</text>' if row.priv > 0.08 else ""
    y = H - 40
    for k, (t, c) in enumerate((("Private funds", ACC), ("Public funds, BDCs", INK), ("Accounts, other", LINE))):
        x = 40 + k * 290
        s += f'<rect x="{x}" y="{y-18}" width="22" height="22" fill="{c}"/><text x="{x+32}" y="{y}" class="leg">{t}</text>'
    return s + "</svg>"

# ---------- slide 6: assets per investment professional ----------
PRIMARY = {"PIMCO": 104559, "Ares": 130074, "TCW": 105742, "Western Asset": 110441, "Oaktree": 106793,
           "Payden & Rygel": 107160, "Crescent": 153966, "Cliffwater": 132167, "Beach Point": 148885,
           "PennyMac": 147101, "Mesa West": 158959, "Silver Rock": 283335}
def lean_svg():
    rows = []
    for gname, crd in PRIMARY.items():
        x = la[la.crd == crd].iloc[0]
        rows.append((gname, x.raum_total / x.employees_advisory / 1e9))
    rows.sort(key=lambda t: -t[1])
    W, rowh, lab = 900, 60, 230
    H = rowh * len(rows) + 10
    mx = rows[0][1]
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    for k, (name, v) in enumerate(rows):
        y = k * rowh + 6; w = (W - lab - 150) * v / mx
        c = ACC if k == 0 else INK
        s += f'<text x="{lab-16}" y="{y+32}" text-anchor="end" class="lab">{name}</text>'
        s += f'<rect x="{lab}" y="{y+8}" width="{max(w,4)}" height="36" fill="{c}"/>'
        val = f"${v:.1f}B" if v >= 1 else f"${v*1000:,.0f}M"
        s += f'<text x="{lab+max(w,4)+12}" y="{y+34}" class="val">{val}</text>'
    return s + "</svg>", rows

lean, lean_rows = lean_svg()
def cheat_html():
    per = dict(lean_rows)
    rows = "".join(f'<tr class="{"hl" if n=="PIMCO" else ""}"><td>{n}</td><td class="ar">{r.area}</td><td>{fmtB(r.B)}</td><td>{r.priv*100:.0f}%</td><td>{("$%.1fB" % per[n]) if per[n] >= 1 else ("$%.0fM" % (per[n]*1000))}</td></tr>' for n, r in g.iterrows())
    return f'<table class="cheat"><tr><th>Firm</th><th style="text-align:left">Where</th><th>AUM</th><th>In private funds</th><th>AUM per inv. pro</th></tr>{rows}</table>'
priv_firms = ", ".join(n for n, row in g.iterrows() if row.priv > 0.75)
dl = left[left.group == "DoubleLine"].iloc[0]; cy = left[left.group == "Canyon"].iloc[0]

GDP_SRC = " GDP: IMF World Economic Outlook, Apr 2026, 2026 projection. AUM is a stock and GDP a yearly flow; shown for scale."
JAPAN, NORWAY, UK, INDIA = 4379, 599, 4260, 4150  # IMF 2026 nominal GDP, $B
REG_SHARE = (la.raum_registered_funds + la.raum_bdcs).sum() / la.raum_total.sum()
ARES_B = g.loc["Ares", "B"]
GRAND_B = la[la.address.str.contains("333 S")].raum_total.sum() / 1e9
pm = la[la.group == "PennyMac"].iloc[0]; wa = la[la.group == "Western Asset"].iloc[0]
MAP_COLORS = dict(sea="#0A1622", land="#15283C", edge="#2C4258", hood="#1C3249", ink=INK, acc=ACC, mute=MUTE, bg=BG)
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import map as lamap
import viz
real_map, _ = lamap.map_svg(g.B.to_dict(), fmtB, MAP_COLORS)

slides = [
frame(1, f"""<div class="cover"><div class="kick">Episode 01 &nbsp;/&nbsp; Nov 2026</div>
<h1>Los Angeles manages more money than Japan's economy</h1>
<p class="sub">{N_FIRMS} credit firms headquartered between Westlake Village and Newport Beach manage <b class="a">{fmtB(TOTAL_T*1000)}</b>.</p>
<div class="chart" style="margin-top:46px">{viz.country_bars_svg(920, 330, [("LA credit firms", TOTAL_T, True), ("Japan GDP", JAPAN/1000, False), ("UK GDP", UK/1000, False), ("India GDP", INDIA/1000, False)], ACC, INK, MUTE)}</div>
<div class="byline"><b>Prateek Shendre</b><br>Structured credit risk &amp; analytics</div>
<div class="swipe">swipe for more</div></div>""", SRC + GDP_SRC),
frame(2, f"""<h2>Why should you care?</h2>
<p class="lede">These firms lend out other people's money. If you have a pension, a 401(k), a mutual fund or an insurance policy, some of your money may already sit with one of them.</p>
<div class="chart" style="margin-top:56px">{viz.flow_svg(920, 520, ACC, INK, MUTE, PANEL, ["Pension funds", "Insurance companies", "Mutual funds, ETFs", "Endowments, family offices"], ["12 LA firms", fmtB(TOTAL_T*1000)], ["Companies", "Homebuyers", "Governments, cities", "Real estate projects"])}</div>
<p class="lede small">Whoever manages this money decides who gets a loan, and at what price.</p>""", "Illustrative. Client and asset types vary by firm; see each firm's Form ADV."),
frame(3, f"""<h2>The money map</h2>
<p class="lede">The Westside, from Century City to Marina del Rey, holds <b class="a">{fmtB(WEST_B)}</b>. Downtown holds <b class="a">{fmtB(BUNKER_B)}</b> in two buildings a block apart. The biggest of all sits by the beach in Newport.</p>
<div class="chart realmap">{real_map}</div>""", SRC + " Circle area scales with assets; PIMCO capped. Pins at each adviser's main office address."),
frame(4, f"""<h2>One building vs a country</h2>
<p class="lede">All four of Ares' advisers file from one tower: 1800 Avenue of the Stars, Century City.</p>
<div class="duel">
<div class="side">{viz.tower_svg(300, 430, ACC, BG)}<div class="dv">{fmtB(ARES_B)}</div><div class="dl">One building in Century City</div></div>
<div class="vs2">vs</div>
<div class="side">{viz.norway_svg(300, 430, INK)}<div class="dv" style="color:{INK}">${NORWAY}B</div><div class="dl">Norway's entire economy, one year</div></div></div>
<p class="lede small">Downtown, 333 S Grand Ave is home to both Oaktree and Payden &amp; Rygel: <b class="a">{fmtB(GRAND_B)}</b> under one roof.</p>""", SRC + GDP_SRC),
frame(5, f"""<h2>One firm is bigger than the other 11 combined</h2>
<p class="lede">PIMCO, in Newport Beach, manages <b class="a">{PIMCO_B/EX_PIMCO_B:.1f} times</b> as much as everyone else on the list put together.</p>
<div class="chart" style="margin-top:50px">{viz.bubbles_svg(920, 640, ("PIMCO", PIMCO_B), [(n, r.B) for n, r in g.drop("PIMCO").iterrows()], ACC, INK, fmtB)}</div>""", SRC + " Circle area scales with assets. Groups sum affiliated advisers (Ares: 4, TCW: 3)."),
frame(6, f"""<h2>One client vs 31,895</h2>
<div class="pair">
<div class="card"><div class="cn">PennyMac</div><div class="cv">1</div><div class="cd">account, holding {fmtB(pm.raum_total/1e9)}</div></div>
<div class="card"><div class="cn">Western Asset</div><div class="cv">{int(wa.accounts_discretionary):,}</div><div class="cd">accounts, holding {fmtB(wa.raum_discretionary/1e9)}</div></div></div>
<p class="lede">Same filing, same city, opposite ends of the business. PennyMac's adviser runs one very large mandate. Western Asset runs tens of thousands of separate client accounts.</p>
<div class="chart" style="margin-top:50px">{viz.accounts_svg(920, 300, ACC, INK, round(wa.accounts_discretionary/100), 100)}</div>
<p class="lede">Average account: <b class="a">{fmtB(pm.raum_discretionary/1e9)}</b> at PennyMac vs <b class="a">${wa.raum_discretionary/wa.accounts_discretionary/1e6:.1f}M</b> at Western Asset. About a <b class="a">{round((pm.raum_discretionary)/(wa.raum_discretionary/wa.accounts_discretionary),-1):,.0f}x</b> gap.</p>""",
 SRC + " Item 5.F(2) number of discretionary accounts."),
frame(7, f"""<h2>Most of this money is not in funds you can buy</h2>
<p class="lede">About <b class="a">{REG_SHARE*100:.0f}%</b> sits in mutual funds, ETFs and BDCs. The rest is private funds and separate accounts for big institutions. Bond houses lean public; private credit shops lean private.</p>
<div class="chart">{tribes_svg()}</div>""", SRC + " Item 5.D client type split of regulatory AUM. Cliffwater's private credit sits in registered interval funds."),
frame(8, f"""<h2>Private credit needs more people per dollar</h2>
<p class="lede">Assets per investment professional. PIMCO runs ${lean_rows[0][1]:.1f}B per head; Ares runs ${lean_rows[-1][1]*1000:.0f}M. That is a <b class="a">{lean_rows[0][1]/lean_rows[-1][1]:.0f}x</b> gap.</p>
<div class="chart">{lean}</div>""", SRC + " Item 5.B(1) staff doing investment advisory work, main adviser entity only."),
frame(9, f"""<h2>Two LA names now file from somewhere else</h2>
<div class="pair" style="margin-top:50px;margin-bottom:0">
<div class="card"><div class="cn">DoubleLine</div><div class="cv">{fmtB(dl.raum_total/1e9)}</div><div class="cd">Main office on file: Tampa, FL</div></div>
<div class="card"><div class="cn">Canyon Partners</div><div class="cv">{fmtB(cy.raum_total/1e9)}</div><div class="cd">Main office on file: Dallas, TX</div></div></div>
<div class="chart" style="margin-top:30px">{viz.moves_svg(920, 430, "#15283C", "#2C4258", ACC, INK, [("DoubleLine to Tampa", -82.46, 27.95, -10, 44), ("Canyon to Dallas", -96.80, 32.78, 0, 46)])}</div>
<p class="lede">Both built their names in LA and still have people here. Count them back in and LA ex-PIMCO goes from {fmtB(EX_PIMCO_B)} to <b class="a">{fmtB(EX_PIMCO_B+LEFT_B)}</b>.</p>""",
 SRC + " Main office as listed on each adviser's latest Form ADV. DoubleLine began its move to Tampa in 2022."),
frame(10, f"""<h2>The cheat sheet</h2>
<p class="lede">All 12 on one page. Save it for your next coffee chat.</p>
{cheat_html()}""", SRC + " Per head uses the main adviser entity and Item 5.B(1) investment staff."),
frame(11, f"""<h2>What I take from this</h2>
<ol class="take">
<li><b>LA is one giant plus a dense cluster.</b> PIMCO is {PIMCO_B/TOTAL_T/10:.0f}% of the total; the other {N_FIRMS-1} still add up to {fmtB(EX_PIMCO_B)}.</li>
<li><b>Two models, two talent markets.</b> Bond houses scale with fewer people; private credit needs more hands per dollar.</li>
<li><b>The Westside is the biggest cluster outside Newport.</b> {fmtB(WEST_B)}, against {fmtB(BUNKER_B)} downtown.</li></ol>
<div class="method"><b>Method.</b> SEC registered adviser roster, Nov 2026. Firms with main offices in LA, Orange and Ventura counties whose business is mainly credit. Regulatory AUM is gross and as filed; filing dates differ by firm. Not investment advice.</div>
<div class="next">Next Tuesday: Ares Capital's loan book</div>
<div class="cta">Know someone in LA credit? Repost this for them.<br>Follow me for a new file every Tuesday.</div>""", "Source and method: see first comment"),
]

CSS = f"""@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-400-normal.woff2');font-weight:400}}@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-500-normal.woff2');font-weight:500}}@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-600-normal.woff2');font-weight:600}}@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-700-normal.woff2');font-weight:700}}@font-face{{font-family:'PlexMono';src:url('../fonts/ibm-plex-mono-latin-400-normal.woff2');font-weight:400}}@font-face{{font-family:'PlexMono';src:url('../fonts/ibm-plex-mono-latin-500-normal.woff2');font-weight:500}}@font-face{{font-family:'PlexMono';src:url('../fonts/ibm-plex-mono-latin-600-normal.woff2');font-weight:600}}@page{{size:1080px 1350px;margin:0}}*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Plex,sans-serif;background:{BG};color:{INK}}}
.s{{width:1080px;height:1350px;padding:64px 80px;position:relative;background:{BG};page-break-after:always;overflow:hidden;border-top:14px solid {ACC}}}
.top{{display:flex;justify-content:space-between;font-family:PlexMono;font-size:21px;letter-spacing:1px;color:{MUTE};font-weight:500}}
.brand b{{color:{ACC};font-weight:600}}
h1{{font-size:88px;line-height:1.04;font-weight:700;letter-spacing:-1.5px;margin-top:34px}}
h2{{font-size:58px;line-height:1.1;font-weight:700;letter-spacing:-0.8px;margin-top:44px}}
.lede{{font-size:29px;line-height:1.4;color:{BODY};margin-top:24px;max-width:900px}}
.a{{color:{ACC};font-weight:600}}
.kick{{margin-top:90px;font-family:PlexMono;font-size:24px;font-weight:500;color:{ACC};text-transform:uppercase;letter-spacing:1px}}
.hero{{font-size:220px;font-weight:700;color:{ACC};letter-spacing:-6px;margin-top:36px;line-height:1}}
.sub{{font-size:34px;line-height:1.35;margin-top:24px;max-width:880px}}.sub2{{font-family:PlexMono;font-size:23px;color:{MUTE};margin-top:28px}}
.byline{{position:absolute;left:80px;bottom:130px;font-size:24px;line-height:1.45;color:{MUTE};border-left:4px solid {ACC};padding-left:18px}}.byline b{{color:{INK}}}
.swipe{{position:absolute;right:80px;bottom:140px;font-family:PlexMono;font-size:26px;font-weight:500;color:{ACC}}}
.chart{{margin-top:50px}}.chart.map{{margin-top:80px}}
.big{{font-family:Plex;font-size:56px;font-weight:600;fill:{INK}}}
.lab{{font-family:Plex;font-size:27px;font-weight:500;fill:{INK}}}.val{{font-family:PlexMono;font-size:25px;font-weight:600;fill:{INK}}}
.inbar{{font-family:PlexMono;font-size:21px;font-weight:600;fill:{ONACC}}}.leg{{font-family:Plex;font-size:21px;fill:{INK}}}
.mlab{{font-family:Plex;font-size:25px;font-weight:600;fill:{INK}}}.mval{{fill:{ACC}}}.mval2{{font-family:Plex;font-size:40px;font-weight:700;fill:{INK}}}.mfirm{{font-family:Plex;font-size:20px;fill:{MUTE}}}
.foot{{position:absolute;left:80px;right:80px;bottom:36px;display:flex;justify-content:space-between;gap:40px;font-family:PlexMono;font-size:17px;color:{MUTE};line-height:1.4;border-top:1px solid {LINE};padding-top:14px}}
.me{{font-family:Plex;font-size:17px;font-weight:600;color:{INK};white-space:nowrap}}
.pair{{display:flex;gap:30px;margin-top:90px;margin-bottom:50px}}.card{{flex:1;border-top:4px solid {INK};padding:28px 0 0}}
.cn{{font-size:32px;font-weight:600}}.cv{{font-size:96px;font-weight:700;color:{ACC};margin-top:10px;letter-spacing:-2px}}.cd{{font-family:PlexMono;font-size:21px;color:{MUTE};margin-top:12px}}
.take{{margin:40px 0 0 34px;font-size:28px;line-height:1.42}}.take li{{margin-bottom:22px}}
.method{{margin-top:30px;font-size:20px;line-height:1.5;color:{BODY};background:{PANEL};padding:22px 26px}}
.scale{{margin-top:34px;font-size:30px;color:{BODY};border-left:4px solid {ACC};padding-left:18px}}.scale b{{color:{INK}}}.chart.realmap{{margin:40px -80px 0;width:1080px}}.chart.realmap svg{{width:1080px;height:auto;display:block}}.place{{font-family:Plex;font-weight:500;font-size:17px;fill:#6F8296}}.sea{{font-family:Plex;font-style:normal;font-size:20px;fill:#4E6378}}.pin{{font-family:Plex;font-weight:600;font-size:20px;fill:{INK}}}.pinv{{font-family:PlexMono;font-weight:600;fill:{ACC}}}.stat{{margin-top:44px}}.sv{{font-size:150px;font-weight:700;color:{ACC};letter-spacing:-4px;line-height:1}}.sl{{font-family:PlexMono;font-size:24px;color:{MUTE};margin-top:8px}}.stat.dim .sv{{color:{INK}}}.vs{{font-family:PlexMono;font-size:26px;color:{MUTE};margin-top:28px}}.lede.small{{font-size:26px;margin-top:48px}}.duel{{display:flex;align-items:flex-end;gap:20px;margin-top:40px}}.side{{flex:1}}.vs2{{font-family:PlexMono;font-size:28px;color:{MUTE};padding-bottom:110px}}.dv{{font-size:84px;font-weight:700;color:{ACC};letter-spacing:-2px;margin-top:22px;line-height:1}}.dl{{font-family:PlexMono;font-size:21px;color:{MUTE};margin-top:10px}}.vlab{{font-family:Plex;font-size:22px;font-weight:500;fill:{MUTE}}}.cb{{font-family:Plex;font-size:28px;font-weight:500;fill:{BODY}}}.cbh{{font-family:Plex;font-size:28px;font-weight:700;fill:{ACC}}}.cv2{{font-family:PlexMono;font-size:26px;font-weight:600;fill:{INK}}}.cvh{{font-family:PlexMono;font-size:26px;font-weight:600;fill:{ACC}}}.fh{{font-family:PlexMono;font-size:20px;fill:{MUTE};text-transform:uppercase}}.fi{{font-family:Plex;font-size:22px;font-weight:500;fill:{INK}}}.fmb{{font-family:Plex;font-size:30px;font-weight:700;fill:{BG}}}.fm{{font-family:Plex;font-size:44px;font-weight:700;fill:{BG}}}.bb{{font-family:Plex;font-size:40px;font-weight:700;fill:{BG}}}.bbv{{font-family:PlexMono;font-size:34px;font-weight:600;fill:{BG}}}.bs{{font-family:Plex;font-size:17px;font-weight:600;fill:{BG}}}.bl{{font-family:Plex;font-size:24px;fill:{MUTE}}}.next{{margin-top:30px;font-size:29px;font-weight:600;color:{ACC}}}.cta{{margin-top:22px;font-size:25px;line-height:1.45;color:{INK};border-left:4px solid {ACC};padding-left:18px}}.cheat{{width:100%;border-collapse:collapse;margin-top:34px;font-size:24px}}.cheat th{{font-family:PlexMono;font-size:17px;font-weight:500;color:{MUTE};text-align:right;padding:0 0 12px;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid {INK}}}.cheat th:first-child,.cheat td:first-child{{text-align:left}}.cheat td{{padding:13px 0;border-bottom:1px solid {LINE};text-align:right;font-family:PlexMono;font-weight:500}}.cheat td:first-child{{font-family:Plex;font-weight:600}}.cheat td.ar{{font-family:Plex;font-weight:400;color:{MUTE};text-align:left;font-size:21px}}.cheat tr.hl td{{color:{ACC}}}"""

html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(slides)}</body></html>"
open(os.path.join(OUT, "e01_carousel.html"), "w").write(html)

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
    pg.goto("file://" + os.path.join(OUT, "e01_carousel.html")); pg.wait_for_load_state("networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    for i, el in enumerate(pg.query_selector_all("section.s"), 1):
        el.screenshot(path=os.path.join(OUT, f"e01_slide{i}.png"))
    pg.pdf(path=os.path.join(OUT, "LA_Credit_Files_E01.pdf"), width="1080px", height="1350px", print_background=True)
    b.close()
print(f"total {TOTAL_T:.2f}T exPIMCO {EX_PIMCO_B:.0f}B bunker {BUNKER_B:.0f}B left {LEFT_B:.0f}B lean {lean_rows}")
