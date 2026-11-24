"""LA Credit Files, Episode 2: Inside Ares Capital's loan book.
Builds a 1080x1350 LinkedIn carousel (PNG per slide + one PDF) from e02/data/arcc_q3_2026.json,
which holds figures from ARCC's Sep 30, 2026 Form 10-Q (as reported, or parsed from its Schedule of Investments).
Usage: python3 e02/build.py   (run from repo root)
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.path.join(HERE, "data", "arcc_q3_2026.json")))

INK, ACC, BG, MUTE, LINE, BODY, PANEL, ONACC = "#EEF2F6", "#F2B33D", "#0D1B2A", "#8FA0B3", "#2A3B4F", "#C9D3DE", "#16273A", "#0D1B2A"
RED, TEAL, PAPER, PAPERINK = "#F07A63", "#5DC6B0", "#F6F1E6", "#1B2530"
N = 11
SRC = "Source: Ares Capital Corp. Form 10-Q, quarter ended Sep 30, 2026 (SEC)."
P = D["portfolio"]; B = D["balance"]; Q = D["q3_income"]; MIX = D["asset_mix_fv"]; Y = D["yields_at_cost"]
FV = P["fv"]

def M(v):  # $ millions -> label
    return f"${v/1000:.1f}B" if v >= 1000 else f"${v:,.0f}M" if v >= 10 else f"${v:.1f}M"

def frame(i, body, src=SRC):
    return f"""<section class="s"><div class="top"><span class="brand">LA CREDIT FILES <b>/ 02</b></span><span class="pg">{i}/{N}</span></div>
{body}<div class="foot"><span>{src}</span><span class="me">Prateek Shendre</span></div></section>"""

def svg(W, H, inner):
    return f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'

# ---------------------------------------------------------------- slide 1: the receipt
def receipt_svg():
    W, H = 520, 760
    items = [("PACKAGED ICE", 317.3), ("PLUMBING + HVAC", 168.6), ("CAKE DECORATIONS", 144.0), ("VET HOSPITALS", 117.5),
             ("GOLF ENTERTAINMENT", 80.9), ("ONLINE CHESS", 56.2), ("LUXURY GYMS", 55.0), ("LAKE + POND CARE", 26.5),
             ("CAR WASHES", 22.5), ("+ 627 MORE COMPANIES", None)]
    s = f'<g transform="rotate(-3 {W/2} {H/2})">'
    # zigzag bottom edge
    zz = " ".join(f"{x},{H-30 + (0 if (x//20)%2==0 else 14)}" for x in range(0, W+1, 20))
    s += f'<polygon points="0,0 {W},0 {" ".join(reversed(zz.split()))}" fill="{PAPER}"/>'
    y = 70
    s += f'<text x="{W/2}" y="{y}" text-anchor="middle" class="rh">ARES CAPITAL CORP</text>'
    s += f'<text x="{W/2}" y="{y+34}" text-anchor="middle" class="rs">PORTFOLIO RECEIPT  09/30/2026</text>'
    s += f'<line x1="36" x2="{W-36}" y1="{y+58}" y2="{y+58}" stroke="{PAPERINK}" stroke-dasharray="6 6" stroke-width="2"/>'
    y += 104
    for name, v in items:
        s += f'<text x="40" y="{y}" class="ri">{name}</text>'
        if v is not None:
            s += f'<text x="{W-40}" y="{y}" text-anchor="end" class="ri">{M(v)}</text>'
        y += 44
    s += f'<line x1="36" x2="{W-36}" y1="{y-14}" y2="{y-14}" stroke="{PAPERINK}" stroke-dasharray="6 6" stroke-width="2"/>'
    s += f'<text x="40" y="{y+30}" class="rt">TOTAL</text><text x="{W-40}" y="{y+30}" text-anchor="end" class="rt">{M(FV)}</text>'
    s += f'<text x="{W/2}" y="{y+82}" text-anchor="middle" class="rs">636 COMPANIES  /  1,422 LINE ITEMS</text>'
    s += f'<text x="{W/2}" y="{y+116}" text-anchor="middle" class="rs">THANK YOU FOR LENDING</text>'
    return svg(W, H + 20, s + "</g>")

# ---------------------------------------------------------------- slide 2: where $100 goes
def waterfall_svg():
    W, H = 920, 560
    tot = Q["total_investment_income"]
    parts = [("Lenders", Q["interest_expense"], MUTE), ("Ares fees", Q["base_fee"] + Q["income_fee"], RED),
             ("Admin + tax", Q["admin_other"] + Q["tax"], "#4D6178"), ("Shareholders", Q["nii"], ACC)]
    k = 400 / 100; base = 480; bw = 150; gap = (W - 5 * bw) / 4
    s = ""
    x = 0
    s += f'<rect x="{x}" y="{base-100*k}" width="{bw}" height="{100*k}" fill="{INK}"/>'
    s += f'<text x="{x+bw/2}" y="{base-100*k-16}" text-anchor="middle" class="wv">$100</text>'
    s += f'<text x="{x+bw/2}" y="{base+38}" text-anchor="middle" class="wl">Income in</text>'
    top = 100
    for i, (lab, v, c) in enumerate(parts):
        x = (i + 1) * (bw + gap)
        pct = v / tot * 100
        y0 = base - top * k
        s += f'<line x1="{x-gap}" x2="{x}" y1="{y0}" y2="{y0}" stroke="{MUTE}" stroke-dasharray="4 5"/>'
        s += f'<rect x="{x}" y="{y0}" width="{bw}" height="{pct*k}" fill="{c}"/>'
        s += f'<text x="{x+bw/2}" y="{y0-16 if i<3 else y0-16}" text-anchor="middle" class="wv" fill="{INK if c!=ACC else ACC}">${pct:.0f}</text>'
        for j, ln in enumerate(lab.split(", ")):
            s += f'<text x="{x+bw/2}" y="{base+38+j*30}" text-anchor="middle" class="wl">{ln}</text>'
        top -= pct
    s += f'<line x1="0" x2="{W}" y1="{base}" y2="{base}" stroke="{INK}" stroke-width="2"/>'
    return svg(W, H, s)

def funding_svg():
    W, H = 920, 120
    e, d = B["equity"], B["debt_principal"]; t = e + d
    we = W * e / t
    s = f'<rect x="0" y="34" width="{we:.0f}" height="56" fill="{TEAL}"/><rect x="{we:.0f}" y="34" width="{W-we:.0f}" height="56" fill="{MUTE}"/>'
    s += f'<text x="0" y="22" class="fh">Shareholders put in</text><text x="{W}" y="22" text-anchor="end" class="fh">Borrowed from lenders</text>'
    s += f'<text x="18" y="72" class="fin">{M(e)}</text><text x="{W-18}" y="72" text-anchor="end" class="fin">{M(d)}</text>'
    return svg(W, H, s)

# ---------------------------------------------------------------- slide 3: a day in your life
def icon(kind, cx, cy, c):
    r = 34
    o = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PANEL}" stroke="{c}" stroke-width="3"/>'
    st = f'stroke="{c}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "wrench":
        o += f'<path d="M{cx},{cy-17} C{cx+11},{cy-3} {cx+13},{cy+3} {cx+13},{cy+6} A13,13 0 0 1 {cx-13},{cy+6} C{cx-13},{cy+3} {cx-11},{cy-3} {cx},{cy-17} Z" fill="{c}"/>'
    elif kind == "dumbbell":
        o += f'<path d="M{cx-12},{cy} L{cx+12},{cy}" {st}/><rect x="{cx-20}" y="{cy-11}" width="8" height="22" rx="2" fill="{c}"/><rect x="{cx+12}" y="{cy-11}" width="8" height="22" rx="2" fill="{c}"/>'
    elif kind == "pawn":
        o += f'<circle cx="{cx}" cy="{cy-10}" r="7" fill="{c}"/><path d="M{cx-6},{cy-2} L{cx+6},{cy-2} L{cx+9},{cy+12} L{cx-9},{cy+12} Z" fill="{c}"/><rect x="{cx-13}" y="{cy+12}" width="26" height="6" rx="2" fill="{c}"/>'
    elif kind == "paw":
        o += f'<ellipse cx="{cx}" cy="{cy+7}" rx="10" ry="8" fill="{c}"/>' + "".join(f'<circle cx="{cx+dx}" cy="{cy+dy}" r="4.5" fill="{c}"/>' for dx, dy in ((-13, -3), (-5, -12), (5, -12), (13, -3)))
    elif kind == "car":
        o += f'<path d="M{cx-18},{cy+6} L{cx-18},{cy-1} L{cx-10},{cy-10} L{cx+8},{cy-10} L{cx+16},{cy-1} L{cx+18},{cy+6} Z" fill="{c}"/><circle cx="{cx-9}" cy="{cy+8}" r="5" fill="{PANEL}" stroke="{c}" stroke-width="3"/><circle cx="{cx+9}" cy="{cy+8}" r="5" fill="{PANEL}" stroke="{c}" stroke-width="3"/>'
        o += "".join(f'<circle cx="{cx+dx}" cy="{cy-19}" r="2.5" fill="{c}"/>' for dx in (-8, 0, 8))
    elif kind == "cake":
        o += f'<rect x="{cx-16}" y="{cy-2}" width="32" height="16" fill="{c}"/><path d="M{cx-16},{cy-2} q4,6 8,0 q4,6 8,0 q4,6 8,0 q4,6 8,0" fill="{PANEL}" stroke="{PANEL}" stroke-width="2"/><rect x="{cx-2}" y="{cy-16}" width="4" height="12" fill="{c}"/><path d="M{cx},{cy-24} q5,5 0,8 q-5,-3 0,-8" fill="{c}"/>'
    elif kind == "golf":
        o += f'<path d="M{cx-6},{cy+16} L{cx-6},{cy-16}" {st}/><path d="M{cx-6},{cy-16} L{cx+14},{cy-9} L{cx-6},{cy-2} Z" fill="{c}"/><circle cx="{cx+8}" cy="{cy+13}" r="4" fill="{c}"/>'
    elif kind == "ice":
        o += f'<path d="M{cx-13},{cy-5} L{cx},{cy-12} L{cx+13},{cy-5} L{cx+13},{cy+10} L{cx},{cy+17} L{cx-13},{cy+10} Z" {st}/><path d="M{cx-13},{cy-5} L{cx},{cy+2} L{cx+13},{cy-5} M{cx},{cy+2} L{cx},{cy+17}" {st}/>'
    return o

def day_svg():
    W, H = 920, 830
    rows = [("7:00 AM", "AC dies. Call a plumber", "Plumbing + HVAC roll-up", "Essential Services", 168.6, "wrench"),
            ("8:00 AM", "Morning workout", "Luxury gyms", "Equinox", 55.0, "dumbbell"),
            ("12:30 PM", "Chess on your lunch break", "Online chess", "Chess.com", 56.2, "pawn"),
            ("3:00 PM", "Dog's checkup", "Vet hospitals", "PetVet Care Centers", 117.5, "paw"),
            ("5:00 PM", "Car wash on the way home", "Car washes", "Quick Quack Car Wash", 22.5, "car"),
            ("6:30 PM", "Grocery store birthday cake", "Cake decorations", "DecoPac", 144.0, "cake"),
            ("8:00 PM", "TopGolf with friends", "Golf entertainment", "TopGolf", 80.9, "golf"),
            ("10:00 PM", "Ice in your drink", "Bagged ice", "Reddy Ice", 317.3, "ice")]
    rh = H / len(rows); s = f'<line x1="200" x2="200" y1="{rh/2}" y2="{H-rh/2}" stroke="{LINE}" stroke-width="4"/>'
    mx = max(r[4] for r in rows)
    for i, (t, act, what, co, v, ic) in enumerate(rows):
        cy = i * rh + rh / 2
        s += f'<text x="150" y="{cy+9}" text-anchor="end" class="dt">{t}</text>'
        s += icon(ic, 200, cy, ACC)
        s += f'<text x="258" y="{cy-6}" class="da">{act}</text>'
        s += f'<text x="258" y="{cy+26}" class="dc">{co} · {what}</text>'
        bw = 150 * v / mx
        s += f'<rect x="{W-150}" y="{cy+4}" width="150" height="10" fill="{LINE}"/><rect x="{W-bw:.0f}" y="{cy+4}" width="{bw:.0f}" height="10" fill="{ACC}"/>'
        s += f'<text x="{W}" y="{cy-14}" text-anchor="end" class="dv2">{M(v)}</text>'
    return svg(W, H, s)

# ---------------------------------------------------------------- slide 4: the layer cake
def cake_svg():
    W, H = 920, 800
    layers = [("First lien loans", MIX["First lien senior secured loans"], f'{Y["First lien"]}%', "Paid first", "#E9A42F"),
              ("Second lien loans", MIX["Second lien senior secured loans"], f'{Y["Second lien"]}%', "", "#D58C2E"),
              ("Senior subordinated loans", MIX["Senior subordinated loans"], f'{Y["Senior subordinated"]}%', "", "#C0742D"),
              ("SDLP fund certificates", MIX["Subordinated certificates of the SDLP"], f'{Y["SDLP certificates"]}%', "", "#9E5E33"),
              ("Preferred equity", MIX["Preferred equity"], "n/a", "", "#7A4B35"),
              ("Ivy Hill (Ares-owned manager)", MIX["Ivy Hill Asset Management"], f'{Y["Ivy Hill"]}%', "", "#5E3B30"),
              ("Other equity", MIX["Other equity"], "n/a", "Paid last", "#4A2F2A")]
    tot = sum(l[1] for l in layers)
    cx0, cw, top0, ch = 30, 340, 150, 610
    s = ""
    y = top0 + ch
    s += f'<ellipse cx="{cx0+cw/2}" cy="{top0+ch+18}" rx="{cw/2+46}" ry="22" fill="{PANEL}"/>'  # plate
    boxes = []
    for name, v, yl, tag, col in layers:
        h = ch * v / tot
        y -= h
        s += f'<rect x="{cx0}" y="{y:.1f}" width="{cw}" height="{h:.1f}" fill="{col}"/>'
        s += f'<line x1="{cx0}" x2="{cx0+cw}" y1="{y:.1f}" y2="{y:.1f}" stroke="{BG}" stroke-width="3"/>'
        boxes.append((name, v, yl, tag, y + h / 2, h))
    # frosting + drips + cherry on the top layer
    yt = y
    drip = f'M{cx0},{yt} L{cx0+cw},{yt} L{cx0+cw},{yt+16} ' + " ".join(f'Q{cx0+cw-20-40*i},{yt+(40 if i%2 else 22)} {cx0+cw-40-40*i},{yt+16}' for i in range(9)) + " Z"
    s += f'<path d="{drip}" fill="{PAPER}"/>'
    s += f'<rect x="{cx0-6}" y="{yt-14}" width="{cw+12}" height="18" rx="9" fill="{PAPER}"/>'
    s += f'<circle cx="{cx0+cw/2}" cy="{yt-34}" r="20" fill="{RED}"/><path d="M{cx0+cw/2},{yt-52} q10,-30 34,-34" stroke="#6B8F3A" stroke-width="4" fill="none"/>'
    # labels with leader lines, spread so small layers don't collide
    lx = cx0 + cw + 70
    ys_adj = [max(boxes[0][4], 118 + 6 * 82 + 30)] + [118 + (6 - i) * 82 for i in range(1, 7)]
    s += f'<text x="{lx}" y="40" class="fh">Share of book</text><text x="{W}" y="40" text-anchor="end" class="fh">Yield at cost</text>'
    for (name, v, yl, tag, yc, h), ya in zip(boxes, ys_adj):
        s += f'<path d="M{cx0+cw+6},{yc:.0f} L{lx-14},{ya:.0f}" stroke="{MUTE}" stroke-width="1.5" fill="none"/>'
        s += f'<text x="{lx}" y="{ya-4:.0f}" class="cn2">{name}</text>'
        s += f'<text x="{lx}" y="{ya+28:.0f}" class="cp">{v/FV*100:.1f}%<tspan class="cm">  {M(v)}{("  · " + tag) if tag else ""}</tspan></text>'
        s += f'<text x="{W}" y="{ya+12:.0f}" text-anchor="end" class="cy">{yl}</text>'
    return svg(W, H, s)

# ---------------------------------------------------------------- slide 5: treemap of industries
def squarify(vals, x, y, w, h):
    rects = []
    vals = list(vals)
    def worst(row, side):
        s = sum(r[1] for r in row); mx = max(r[1] for r in row); mn = min(r[1] for r in row)
        return max(side * side * mx / (s * s), (s * s) / (side * side * mn))
    total = sum(v for _, v in vals); scale = w * h / total
    items = [(n, v * scale) for n, v in vals]
    while items:
        side = min(w, h); row = [items.pop(0)]
        while items and worst(row + [items[0]], side) <= worst(row, side):
            row.append(items.pop(0))
        s = sum(r[1] for r in row)
        if w >= h:
            cw = s / h; yy = y
            for n, a in row:
                rh = a / cw; rects.append((n, x, yy, cw, rh)); yy += rh
            x += cw; w -= cw
        else:
            chh = s / w; xx = x
            for n, a in row:
                rw = a / chh; rects.append((n, xx, y, rw, chh)); xx += rw
            y += chh; h -= chh
    return rects

def treemap_svg():
    W, H = 920, 780
    rows = D["industry_pct"]
    pct = {n: (p, p0) for n, p, p0 in rows}
    rects = squarify([(n, p) for n, p, _ in rows], 0, 0, W, H)
    shades = ["#24384D", "#2C445C", "#34506B", "#2A3F55"]
    s = ""
    for i, (n, x, y, w, h) in enumerate(rects):
        p, p0 = pct[n]
        hi = n == "Software and Services"
        fill = ACC if hi else (TEAL if n == "Financial Services" else shades[i % 4])
        s += f'<rect x="{x+3:.1f}" y="{y+3:.1f}" width="{w-6:.1f}" height="{h-6:.1f}" fill="{fill}"/>'
        tc = ONACC if (hi or n == "Financial Services") else INK
        short = {"Health Care Equipment and Services": "Health care", "Commercial and Professional Services": "Business services",
                 "Consumer Distribution and Retail": "Distribution & retail", "Investment Funds and Vehicles": "Investment funds",
                 "Sports, Media and Entertainment": "Sports & media", "Pharma, Biotech and Life Sciences": "Pharma",
                 "Consumer Durables and Apparel": "Durables", "Independent Power and Renewables": "Power",
                 "Food and Beverage": "Food", "Software and Services": "Software & Services"}.get(n, n)
        big = hi or n == "Financial Services"
        fs = 64 if big else (40 if w > 200 and h > 130 else 28 if w > 110 else 20)
        tfs = 22 if fs >= 28 else 17
        cpl = max(4, int((w - 30) / (tfs * 0.56)))
        words, lines, cur = short.split(" "), [], ""
        for wd in words:
            if len(cur) + len(wd) + 1 > cpl and cur: lines.append(cur); cur = wd
            else: cur = (cur + " " + wd).strip()
        lines.append(cur)
        if w > 50 and h > 40:
            s += f'<text x="{x+16:.0f}" y="{y+14+fs*0.82:.0f}" class="tp" font-size="{fs}" fill="{tc}">{p:.1f}%</text>'
            for j, ln in enumerate(lines[:3]):
                yy = y + 14 + fs + (tfs + 5) * (j + 1)
                if yy < y + h - 8 and len(ln) <= cpl + 1:
                    s += f'<text x="{x+16:.0f}" y="{yy:.0f}" class="tn" font-size="{tfs}" fill="{tc}">{ln}</text>'
            if big:
                s += f'<text x="{x+20:.0f}" y="{y+h-22:.0f}" class="tn2" fill="{tc}">Dec 2025: {p0:.1f}%</text>'
    return svg(W, H, s)

# ---------------------------------------------------------------- slide 6: biggest positions
def top_svg():
    W, H = 920, 640
    rows = [(("Ivy Hill" if i == 0 else "SDLP fund" if i == 1 else n), v, d) for i, (n, v, d) in enumerate(D["top_positions_parsed"])]
    mx = rows[0][1]; lab = 300; rh = H / len(rows)
    s = ""
    for i, (n, v, d) in enumerate(rows):
        y = i * rh
        fam = i < 2
        w = (W - lab - 120) * v / mx
        s += f'<text x="{lab-18}" y="{y+rh/2-2:.0f}" text-anchor="end" class="lab">{n}</text>'
        s += f'<text x="{lab-18}" y="{y+rh/2+24:.0f}" text-anchor="end" class="sub3">{d}</text>'
        s += f'<rect x="{lab}" y="{y+rh/2-20:.0f}" width="{max(w,3):.0f}" height="40" fill="{ACC if fam else INK}"/>'
        s += f'<text x="{lab+w+12:.0f}" y="{y+rh/2+9:.0f}" class="val">{M(v)}</text>'
    s += f'<rect x="{lab-290}" y="-6" width="{W-lab+290}" height="{2*rh+4:.0f}" fill="none" stroke="{ACC}" stroke-width="2" stroke-dasharray="6 6"/>'
    s += f'<text x="{W-10}" y="{rh*1.5+8:.0f}" text-anchor="end" class="fam">THE FAMILY</text>'
    return svg(W, H + 4, s)

# ---------------------------------------------------------------- slide 7: where it hurts
def dumbbell_svg():
    W, H = 920, 720
    rows = D["markdowns_parsed"]; soft = {"Cornerstone OnDemand", "Symplr", "DigiCert", "Huskies / GI Insurity", "Pluralsight"}
    lab = 330; x0, x1 = lab + 10, W - 70; mx = 450
    X = lambda v: x0 + (x1 - x0) * v / mx
    rh = (H - 50) / len(rows); s = ""
    for t in range(0, 451, 150):
        s += f'<line x1="{X(t):.0f}" x2="{X(t):.0f}" y1="0" y2="{H-40}" stroke="{LINE}"/><text x="{X(t):.0f}" y="{H-8}" text-anchor="middle" class="ax">${t}M</text>'
    for i, (n, c, f, d) in enumerate(rows):
        y = i * rh + rh / 2
        sw = n in soft
        s += f'<text x="{lab-18}" y="{y-2:.0f}" text-anchor="end" class="lab">{n}</text>'
        s += f'<text x="{lab-18}" y="{y+24:.0f}" text-anchor="end" class="{"sub3g" if sw else "sub3"}">{d}</text>'
        s += f'<line x1="{X(f):.0f}" x2="{X(c):.0f}" y1="{y:.0f}" y2="{y:.0f}" stroke="{RED}" stroke-width="6" opacity="0.55"/>'
        s += f'<circle cx="{X(c):.0f}" cy="{y:.0f}" r="11" fill="{MUTE}"/><circle cx="{X(f):.0f}" cy="{y:.0f}" r="12" fill="{RED}"/>'
        s += f'<text x="{X(c)+20:.0f}" y="{y+9:.0f}" class="dd">{(f/c-1)*100:.0f}%</text>'
    return svg(W, H, s)

# ---------------------------------------------------------------- slide 8: stress check
def grades_svg():
    W, H = 400, 640
    g = D["grades"]["sep26"]
    cols, r, gap = 22, 7.2, 17.8
    order = [("4", TEAL), ("3", "#3B5470"), ("2", ACC), ("1", RED)]
    s, k = "", 0
    for gr, c in order:
        for _ in range(g[gr][1]):
            x = (k % cols) * gap + 10; y = (k // cols) * gap + 10
            s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{c}"/>'; k += 1
    y = (k // cols + 1) * gap + 34
    labels = [("Grade 4: best", TEAL, g["4"][1]), ("Grade 3: as expected", "#6E8AA8", g["3"][1]), ("Grade 2: watch", ACC, g["2"][1]), ("Grade 1: trouble", RED, g["1"][1])]
    for i, (t, c, n) in enumerate(labels):
        yy = y + i * 34
        s += f'<circle cx="18" cy="{yy-7}" r="9" fill="{c}"/><text x="38" y="{yy}" class="gl">{t} <tspan class="glm">{n}</tspan></text>'
    return svg(W, y + 4 * 34, s)

def kpi_rows():
    g0, g1 = D["grades"]["dec25"], D["grades"]["sep26"]
    t0 = sum(v[0] for v in g0.values()); t1 = sum(v[0] for v in g1.values())
    w0 = (g0["1"][0] + g0["2"][0]) / t0 * 100; w1 = (g1["1"][0] + g1["2"][0]) / t1 * 100
    na = D["non_accrual"]
    pik = (Q["pik_interest"] + Q["pik_dividends"]) / Q["total_investment_income"] * 100
    rows = [("Loans not paying (non-accrual), at cost", f'{na["pct_cost_dec25"]}%', f'{na["pct_cost"]}%', True),
            ("Watch list (grades 1 + 2), share of book", f"{w0:.1f}%", f"{w1:.1f}%", True),
            ("Income paid in IOUs (PIK), Q3", "15.5%", f"{pik:.1f}%", True),
            ("NAV per share", f'${B["nav_ps_dec25"]}', f'${B["nav_ps"]}', True),
            (f'Core EPS, Q3 (dividend is ${Q["dividend_ps"]:.2f})', "$0.50", f'${Q["core_eps"]:.2f}', True)]
    h = '<div class="kpis"><div class="kh"><span></span><span>Before</span><span>Now</span></div>'
    for lab, a, b, bad in rows:
        h += f'<div class="kr"><span class="kl">{lab}</span><span class="ka">{a}</span><span class="kb">{b}</span></div>'
    return h + '<div class="knote">Before = Dec 31, 2025; for PIK and core EPS, Q3 2025.</div></div>'

# ---------------------------------------------------------------- slide 10: cheat sheet
def cheat_html():
    tiles = [(M(FV), "portfolio at fair value"), ("636", "companies"), (f'{MIX["First lien senior secured loans"]/FV*100:.0f}%', "first lien loans"),
             (f'{(MIX["Preferred equity"]+MIX["Ivy Hill Asset Management"]+MIX["Other equity"])/FV*100:.0f}%', "equity, not loans"),
             (f'{Y["Total portfolio"]}%', "yield at cost"), ("21.6%", "software and services"),
             (f'{D["non_accrual"]["pct_cost"]}%', "non-accrual at cost"), (f'{(Q["pik_interest"]+Q["pik_dividends"])/Q["total_investment_income"]*100:.0f}%', "of Q3 income was PIK"),
             (f'{B["debt_principal"]/B["equity"]:.2f}x', "debt to equity"), (f'${B["nav_ps"]}', "NAV per share"),
             (f'${Q["dividend_ps"]:.2f}', f'quarterly dividend, {Q["dividend_ps"]*4/B["nav_ps"]*100:.1f}% of NAV a year'), ("2030", "biggest maturity year")]
    return '<div class="tiles">' + "".join(f'<div class="tile"><div class="tv">{v}</div><div class="tl">{l}</div></div>' for v, l in tiles) + "</div>"

od = D["oddities_parsed"]; feh = od["FEH Group"]; sfm = od["South Florida Motorsports"]
fl_share = MIX["First lien senior secured loans"] / FV * 100
eq_share = (MIX["Preferred equity"] + MIX["Ivy Hill Asset Management"] + MIX["Other equity"]) / FV * 100

slides = [
frame(1, f"""<div class="cover2"><div class="cl">
<div class="kick">Episode 02 &nbsp;/&nbsp; Nov 2026</div>
<h1 class="h1c">I read all 1,422 line items in Ares Capital's loan book</h1>
<p class="sub">Ares Capital is the largest listed BDC, run by Century City's Ares Management. Here is what <b class="a">{M(FV)}</b> of private loans actually buys.</p>
</div><div class="cr">{receipt_svg()}</div></div>
<div class="byline"><b>Prateek Shendre</b><br>Structured credit risk &amp; analytics</div>
<div class="swipe">swipe for more</div>"""),
frame(2, f"""<h2>Wait, what is a BDC?</h2>
<p class="lede">A Business Development Company is a stock you can buy that holds a pile of loans to mid-sized private companies. It must pay out at least 90% of its taxable income, so most of what it earns flows to shareholders.</p>
<div class="chart" style="margin-top:40px">{funding_svg()}</div>
<p class="mini">Every $100 of income Ares Capital earned last quarter went here:</p>
<div class="chart" style="margin-top:14px">{waterfall_svg()}</div>""", SRC + " Q3 2026: $763M income, $221M interest, $191M base and income fees, $328M net investment income."),
frame(3, f"""<h2>A day in your life, financed by one lender</h2>
<p class="lede">Ares Capital has money in 636 companies. You may have used a few of them this week.</p>
<div class="chart" style="margin-top:34px">{day_svg()}</div>""", SRC + " Bars: Ares Capital's investment in each company at fair value. Other lenders may also finance them."),
frame(4, f"""<h2>It's a layer cake, not just loans</h2>
<p class="lede">The bottom layer gets paid first. Every layer above it takes more risk for more yield. About <b class="a">{eq_share:.0f}%</b> of this "loan book" is actually equity.</p>
<div class="chart" style="margin-top:30px">{cake_svg()}</div>""", SRC + " Fair value by asset type. Yields at amortized cost as reported; n/a = not reported for that layer."),
frame(5, f"""<h2>Who borrows? Software, mostly</h2>
<p class="lede">Software is the biggest slice at <b class="a">21.6%</b>, down from 23.8% in December. Financial Services is #2 mostly because of Ivy Hill, the asset manager Ares Capital owns.</p>
<div class="chart" style="margin-top:34px">{treemap_svg()}</div>""", SRC + " Industry split of the portfolio at fair value (GICS groups), as reported."),
frame(6, f"""<h2>The two biggest borrowers are family</h2>
<p class="lede">Ivy Hill is an asset manager Ares Capital owns outright ($17.7B across 25 funds). The SDLP is a joint fund that lends to {D["sdlp_borrowers"]} more companies. After those two, no company is more than <b class="a">1.3%</b> of the book.</p>
<div class="chart" style="margin-top:40px">{top_svg()}</div>
<p class="lede small">The typical (median) company position is just <b class="a">${P["median_company_fv_parsed"]:.1f}M</b>.</p>""", SRC + " Fair value summed across all securities of each company, parsed from the Schedule of Investments."),
frame(7, f"""<h2>Where it hurts: software</h2>
<p class="lede">The 8 biggest markdowns, cost vs today's fair value. <b class="a">5 of the 8</b> sell software. The biggest, Cornerstone OnDemand, is based in Santa Monica.</p>
<div class="chart" style="margin-top:36px">{dumbbell_svg()}</div>
<div class="legend2"><span><i style="background:{MUTE}"></i>Cost</span><span><i style="background:{RED}"></i>Fair value, Sep 30</span><span class="gold">Software names in gold</span></div>""", SRC + " Parsed; all securities per company. Context: the BIS (Jul 2026) puts software at about one-fifth of all BDC lending."),
frame(8, f"""<h2>Is anything breaking? A few things are bending</h2>
<p class="lede">Ares grades every company 1 to 4. One dot per company:</p>
<div class="stress"><div class="sl2">{grades_svg()}</div><div class="sr2">{kpi_rows()}</div></div>
<p class="lede small">Still, <b class="a">94%</b> of the book sits in grades 3 and 4, and the loans that stopped paying are 1.4% of fair value.</p>""", SRC + " Grades and non-accruals as reported. PIK = PIK interest plus PIK dividends over total investment income."),
frame(9, f"""<h2>Neighbors and head-turners</h2>
<p class="lede">A few names close to home, and a few you would not expect in a loan book.</p>
<div class="two">
<div class="panel"><div class="ph">LA neighbors</div>
{"".join(f'<div class="pr"><div><div class="pn">{n}</div><div class="pc">{c}</div></div><div class="pv">{M(f) if f>0 else "$0"}<span class="{"neg" if f<k else "pos"}">{(f/k-1)*100:+.0f}% vs cost</span></div></div>' for n,c,f,k in D["la_names_parsed"])}
<div class="mgr"><div class="ph" style="margin-bottom:6px">And the manager</div>Ares Management, 1800 Avenue of the Stars, Century City. The same tower from Episode 01.</div>
</div>
<div class="panel"><div class="ph">Head-turners</div>
<div class="ht"><b>A pro sports team and its entertainment complex</b>, bought Dec 2024: {M(feh[0])} cost, now <span class="pos">{M(feh[1])}</span>. Same month Ares funds bought 10% of the Miami Dolphins, Hard Rock Stadium and the F1 Miami Grand Prix.</div>
<div class="ht"><b>South Florida Motorsports</b> ("professional sporting event"): {M(sfm[0])} cost, now <span class="pos">{M(sfm[1])}</span>. That's {sfm[1]/sfm[0]:.1f}x.</div>
<div class="ht"><b>Databricks</b>: a $38.6M credit line. Drawn so far: $0.1M.</div>
<div class="ht"><b>Also on the list:</b> 8 music businesses, a lake and pond manager, a maker of baby head-shaping helmets, and a fully cooked ham retailer.</div>
</div></div>""", SRC + " HQs: company sources. Miami Dolphins release, Dec 11, 2024. The filing does not name the team."),
frame(10, f"""<h2>The cheat sheet</h2>
<p class="lede">Ares Capital on one page. Save it for your next private credit conversation.</p>
{cheat_html()}""", SRC + " Debt to equity uses debt principal outstanding. Dividend yield on NAV, not on share price."),
frame(11, f"""<h2>What I take from this</h2>
<ol class="take">
<li><b>Big, spread out, mostly senior.</b> 636 companies, a ${P["median_company_fv_parsed"]:.1f}M median position and {fl_share:.0f}% first lien loans.</li>
<li><b>Software is the swing factor.</b> 21.6% of the book and 5 of the 8 biggest markdowns.</li>
<li><b>Stress is rising from a low base.</b> Non-accruals 1.8% to 2.4%, the watch list 3.8% to 5.8%, and core EPS ($0.46) slipped under the $0.48 dividend.</li></ol>
<div class="method"><b>Coming next for ARCC:</b> a ~$2.6B deal to buy MidCap Financial (MFIC), a listed BDC managed by an Apollo affiliate. Signed Oct 26 and expected to close in the first half of 2027. Fun detail: Ares's management company pays the $1.21 a share cash part itself.</div>
<div class="method" style="margin-top:14px"><b>Method.</b> I parsed every line of the Sep 30, 2026 Schedule of Investments in the 10-Q; it ties to the filing's {M(FV)} total. Not investment advice.</div>
<div class="next">Next Tuesday: same loan, different price across BDCs</div>
<div class="cta">Know someone in private credit? Repost this for them.<br>Follow me for a new file every Tuesday.</div>""", "Data and code: github.com/prateekshendre/la-credit-files"),
]

CSS = f"""@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-400-normal.woff2');font-weight:400}}@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-500-normal.woff2');font-weight:500}}@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-600-normal.woff2');font-weight:600}}@font-face{{font-family:'Plex';src:url('../fonts/ibm-plex-sans-latin-700-normal.woff2');font-weight:700}}@font-face{{font-family:'PlexMono';src:url('../fonts/ibm-plex-mono-latin-400-normal.woff2');font-weight:400}}@font-face{{font-family:'PlexMono';src:url('../fonts/ibm-plex-mono-latin-500-normal.woff2');font-weight:500}}@font-face{{font-family:'PlexMono';src:url('../fonts/ibm-plex-mono-latin-600-normal.woff2');font-weight:600}}@page{{size:1080px 1350px;margin:0}}*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Plex,sans-serif;background:{BG};color:{INK}}}
.s{{width:1080px;height:1350px;padding:64px 80px;position:relative;background:{BG};page-break-after:always;overflow:hidden;border-top:14px solid {ACC}}}
.top{{display:flex;justify-content:space-between;font-family:PlexMono;font-size:21px;letter-spacing:1px;color:{MUTE};font-weight:500}}.brand b{{color:{ACC};font-weight:600}}
h1{{font-size:80px;line-height:1.04;font-weight:700;letter-spacing:-1.5px;margin-top:30px}}
h2{{font-size:56px;line-height:1.1;font-weight:700;letter-spacing:-0.8px;margin-top:40px}}
.lede{{font-size:28px;line-height:1.4;color:{BODY};margin-top:22px;max-width:910px}}.lede.small{{font-size:25px;margin-top:30px}}
.a{{color:{ACC};font-weight:600}}.mini{{font-family:PlexMono;font-size:21px;color:{MUTE};margin-top:44px;text-transform:uppercase;letter-spacing:.5px}}
.kick{{margin-top:56px;font-family:PlexMono;font-size:24px;font-weight:500;color:{ACC};text-transform:uppercase;letter-spacing:1px}}
.cover2{{display:flex;gap:10px}}.cl{{flex:1.05}}.cr{{flex:1;margin-top:70px;margin-right:-60px}}
.h1c{{font-size:74px}}.sub{{font-size:30px;line-height:1.4;margin-top:30px;color:{BODY}}}
.byline{{position:absolute;left:80px;bottom:130px;font-size:24px;line-height:1.45;color:{MUTE};border-left:4px solid {ACC};padding-left:18px}}.byline b{{color:{INK}}}
.swipe{{position:absolute;left:80px;bottom:240px;font-family:PlexMono;font-size:26px;font-weight:500;color:{ACC}}}
.foot{{position:absolute;left:80px;right:80px;bottom:36px;display:flex;justify-content:space-between;gap:40px;font-family:PlexMono;font-size:17px;color:{MUTE};line-height:1.4;border-top:1px solid {LINE};padding-top:14px}}
.me{{font-family:Plex;font-size:17px;font-weight:600;color:{INK};white-space:nowrap}}
.rh{{font-family:PlexMono;font-size:30px;font-weight:600;fill:{PAPERINK};letter-spacing:2px}}.rs{{font-family:PlexMono;font-size:17px;fill:#5A6672;letter-spacing:1px}}
.ri{{font-family:PlexMono;font-size:21px;font-weight:500;fill:{PAPERINK}}}.rt{{font-family:PlexMono;font-size:30px;font-weight:600;fill:{PAPERINK}}}
.wv{{font-family:PlexMono;font-size:34px;font-weight:600;fill:{INK}}}.wl{{font-family:Plex;font-size:24px;font-weight:500;fill:{BODY}}}
.fh{{font-family:PlexMono;font-size:19px;fill:{MUTE};text-transform:uppercase;letter-spacing:.5px}}.fin{{font-family:PlexMono;font-size:28px;font-weight:600;fill:{BG}}}
.dt{{font-family:PlexMono;font-size:22px;font-weight:500;fill:{MUTE}}}.da{{font-family:Plex;font-size:28px;font-weight:600;fill:{INK}}}.dc{{font-family:Plex;font-size:21px;fill:{MUTE}}}.dv2{{font-family:PlexMono;font-size:24px;font-weight:600;fill:{ACC}}}
.cn2{{font-family:Plex;font-size:25px;font-weight:600;fill:{INK}}}.cp{{font-family:PlexMono;font-size:24px;font-weight:600;fill:{ACC}}}.cm{{font-family:PlexMono;font-size:19px;font-weight:400;fill:{MUTE}}}.cy{{font-family:PlexMono;font-size:26px;font-weight:600;fill:{INK}}}
.tp{{font-family:Plex;font-weight:700}}.tn{{font-family:Plex;font-weight:500}}.tn2{{font-family:PlexMono;font-size:19px}}
.lab{{font-family:Plex;font-size:25px;font-weight:600;fill:{INK}}}.sub3{{font-family:Plex;font-size:19px;fill:{MUTE}}}.sub3g{{font-family:Plex;font-size:19px;font-weight:600;fill:{ACC}}}.val{{font-family:PlexMono;font-size:24px;font-weight:600;fill:{INK}}}
.fam{{font-family:PlexMono;font-size:20px;font-weight:600;fill:{ACC};letter-spacing:2px}}.ax{{font-family:PlexMono;font-size:18px;fill:{MUTE}}}.dd{{font-family:PlexMono;font-size:22px;font-weight:600;fill:{RED}}}
.legend2{{display:flex;gap:34px;font-family:PlexMono;font-size:20px;color:{MUTE};margin-top:18px}}.legend2 i{{display:inline-block;width:16px;height:16px;border-radius:50%;margin-right:8px;vertical-align:-2px}}.gold{{color:{ACC}}}
.stress{{display:flex;gap:44px;margin-top:30px;align-items:flex-start}}.sl2{{flex:0 0 400px}}.sr2{{flex:1}}
.gl{{font-family:Plex;font-size:21px;fill:{BODY}}}.glm{{font-family:PlexMono;font-weight:600;fill:{INK}}}
.kpis{{font-size:22px}}.kh,.kr{{display:grid;grid-template-columns:1fr 104px 112px;gap:10px;align-items:center}}.kh{{font-family:PlexMono;font-size:17px;color:{MUTE};text-transform:uppercase;border-bottom:2px solid {INK};padding-bottom:10px}}.kh span:nth-child(n+2){{text-align:right}}
.kr{{padding:17px 0;border-bottom:1px solid {LINE}}}.kl{{font-size:22px;line-height:1.3;color:{BODY}}}.ka{{font-family:PlexMono;font-size:21px;color:{MUTE};text-align:right}}.kb{{font-family:PlexMono;font-size:23px;font-weight:600;color:{RED};text-align:right}}.knote{{font-family:PlexMono;font-size:15px;color:{MUTE};margin-top:12px}}
.two{{display:flex;gap:28px;margin-top:34px}}.panel{{flex:1;background:{PANEL};padding:26px 26px 18px}}.ph{{font-family:PlexMono;font-size:19px;font-weight:600;color:{ACC};text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.pr{{display:flex;justify-content:space-between;gap:12px;padding:16px 0;border-bottom:1px solid {LINE}}}.pn{{font-size:23px;font-weight:600;line-height:1.25}}.pc{{font-family:PlexMono;font-size:17px;color:{MUTE};margin-top:4px}}.pv{{font-family:PlexMono;font-size:23px;font-weight:600;text-align:right;white-space:nowrap}}.pv span{{display:block;font-size:16px;margin-top:4px}}
.neg{{color:{RED}}}.pos{{color:{TEAL}}}.mgr{{margin-top:26px;font-size:23px;line-height:1.45;color:{BODY}}}.ht{{font-size:23px;line-height:1.42;color:{BODY};padding:14px 0;border-bottom:1px solid {LINE}}}.ht b{{color:{INK}}}
.tiles{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:40px}}.tile{{background:{PANEL};padding:26px 22px;border-top:4px solid {ACC};min-height:190px}}.tv{{font-size:54px;font-weight:700;color:{INK};letter-spacing:-1px}}.tl{{font-family:PlexMono;font-size:18px;color:{MUTE};margin-top:10px;line-height:1.35}}
.take{{margin:44px 0 0 36px;font-size:30px;line-height:1.42}}.take li{{margin-bottom:26px}}
.method{{margin-top:30px;font-size:23px;line-height:1.5;color:{BODY};background:{PANEL};padding:20px 24px}}.method b{{color:{INK}}}
.next{{margin-top:40px;font-size:31px;font-weight:600;color:{ACC}}}.cta{{margin-top:24px;font-size:27px;line-height:1.45;color:{INK};border-left:4px solid {ACC};padding-left:18px}}
"""

html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(slides)}</body></html>"
open(os.path.join(OUT, "e02_carousel.html"), "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
    pg.goto("file://" + os.path.join(OUT, "e02_carousel.html")); pg.wait_for_load_state("networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    for i, el in enumerate(pg.query_selector_all("section.s"), 1):
        el.screenshot(path=os.path.join(OUT, f"e02_slide{i}.png"))
    pg.pdf(path=os.path.join(OUT, "LA_Credit_Files_E02.pdf"), width="1080px", height="1350px", print_background=True)
    b.close()
print("built", len(slides), "slides")
