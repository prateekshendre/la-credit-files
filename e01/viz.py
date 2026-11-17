"""Small infographics for Episode 01: a tower, Norway's outline, an accounts dot grid, a US move map."""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(name):
    return json.load(open(os.path.join(ROOT, "data", "geo", name)))

def _fit(feats, W, H, pad=0):
    pts = [(lon, lat) for f in feats for poly in f["geometry"]["coordinates"] for ring in poly for lon, lat in ring]
    lat_m = sum(p[1] for p in pts) / len(pts); k0 = math.cos(math.radians(lat_m))
    xs = [p[0] * k0 for p in pts]; ys = [p[1] for p in pts]
    sx = (W - 2 * pad) / (max(xs) - min(xs)); sy = (H - 2 * pad) / (max(ys) - min(ys)); s = min(sx, sy)
    ox = pad + ((W - 2 * pad) - (max(xs) - min(xs)) * s) / 2; oy = pad + ((H - 2 * pad) - (max(ys) - min(ys)) * s) / 2
    x0, y1 = min(xs), max(ys)
    return lambda lon, lat: (ox + (lon * k0 - x0) * s, oy + (y1 - lat) * s)

def _path(feats, P):
    d = ""
    for f in feats:
        for poly in f["geometry"]["coordinates"]:
            for ring in poly:
                d += "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in (P(lon, lat) for lon, lat in ring)) + "Z"
    return d

def tower_svg(W, H, color, bg):
    """A plain modern office tower with a window grid."""
    tw = W * 0.46; x0 = (W - tw) / 2; top = H * 0.06
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    s += f'<rect x="{x0+tw*0.38:.0f}" y="0" width="{tw*0.04:.0f}" height="{top+4:.0f}" fill="{color}"/>'
    s += f'<rect x="{x0:.0f}" y="{top:.0f}" width="{tw:.0f}" height="{H-top:.0f}" fill="{color}"/>'
    cols, rows = 6, 22
    gw = tw * 0.8 / cols; gh = (H - top) * 0.9 / rows
    for r in range(rows):
        for c in range(cols):
            wx = x0 + tw * 0.1 + c * gw + gw * 0.18; wy = top + (H - top) * 0.05 + r * gh + gh * 0.2
            s += f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{gw*0.64:.1f}" height="{gh*0.55:.1f}" fill="{bg}" fill-opacity="0.55"/>'
    return s + "</svg>"

def norway_svg(W, H, color):
    feats = _load("norway.geojson")["features"]
    P = _fit(feats, W, H)
    return f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}"><path d="{_path(feats, P)}" fill="{color}"/></svg>'

def accounts_svg(W, H, acc, ink, n_dots, per):
    """Left: one big square. Right: a grid of small dots, each = `per` accounts."""
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    sq = min(H * 0.62, W * 0.3)
    s += f'<rect x="0" y="0" width="{sq:.0f}" height="{sq:.0f}" fill="{acc}"/>'
    s += f'<text x="0" y="{sq+40:.0f}" class="vlab">PennyMac: 1 account</text>'
    gx = W * 0.44; cols = 30; cell = (W - gx) / cols; r = cell * 0.36
    rows = math.ceil(n_dots / cols)
    for i in range(n_dots):
        cx = gx + (i % cols) * cell + cell / 2; cy = (i // cols) * cell + cell / 2
        s += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{ink}"/>'
    s += f'<text x="{gx:.0f}" y="{rows*cell+40:.0f}" class="vlab">Western Asset: each dot = {per} accounts</text>'
    return s + "</svg>"

def moves_svg(W, H, land, edge, acc, ink, moves):
    """US outline with arcs from LA. moves: [(label, lon, lat, dx, dy)]."""
    feats = _load("us_states.geojson")["features"]
    P = _fit(feats, W, H, pad=10)
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}"><path d="{_path(feats, P)}" fill="{land}" stroke="{edge}" stroke-width="1"/>'
    la = P(-118.25, 34.05)
    s += f'<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="{acc}"/></marker></defs>'
    for label, lon, lat, dx, dy in moves:
        x, y = P(lon, lat)
        mx, my = (la[0] + x) / 2, min(la[1], y) - 110
        s += f'<path d="M{la[0]:.0f},{la[1]:.0f} Q{mx:.0f},{my:.0f} {x:.0f},{y:.0f}" fill="none" stroke="{acc}" stroke-width="4" stroke-dasharray="2 10" stroke-linecap="round" marker-end="url(#ah)"/>'
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="{acc}"/>'
        s += f'<text x="{x+dx:.0f}" y="{y+dy:.0f}" class="vlab" text-anchor="middle">{label}</text>'
    s += f'<circle cx="{la[0]:.0f}" cy="{la[1]:.0f}" r="11" fill="{ink}"/><text x="{la[0]+6:.0f}" y="{la[1]+44:.0f}" class="vlab" text-anchor="middle">Los Angeles</text>'
    return s + "</svg>"

def country_bars_svg(W, H, rows, acc, ink, mute):
    """rows: [(label, value_in_T, highlight)] horizontal bars."""
    mx = max(v for _, v, _ in rows); lab = 250; rh = H / len(rows)
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    for i, (name, v, hl) in enumerate(rows):
        y = i * rh; w = (W - lab - 140) * v / mx; c = acc if hl else ink
        s += f'<text x="{lab-18}" y="{y+rh/2+9:.0f}" text-anchor="end" class="{"cbh" if hl else "cb"}">{name}</text>'
        s += f'<rect x="{lab}" y="{y+rh*0.18:.0f}" width="{w:.0f}" height="{rh*0.64:.0f}" fill="{c}" fill-opacity="{1 if hl else 0.85}"/>'
        s += f'<text x="{lab+w+14:.0f}" y="{y+rh/2+9:.0f}" class="{"cvh" if hl else "cv2"}">${v:.2f}T</text>'
    return s + "</svg>"

def flow_svg(W, H, acc, ink, mute, panel, left, mid, right):
    """Three-column flow: sources -> LA firms -> uses."""
    cw = 290; gap = (W - 3 * cw) / 2; s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    s += f'<defs><marker id="fa" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0L10,5L0,10z" fill="{acc}"/></marker></defs>'
    def col(x, title, items):
        out = f'<text x="{x}" y="26" class="fh">{title}</text>'
        bh = (H - 60 - 14 * (len(items) - 1)) / len(items)
        for i, it in enumerate(items):
            y = 50 + i * (bh + 14)
            out += f'<rect x="{x}" y="{y:.0f}" width="{cw}" height="{bh:.0f}" fill="{panel}"/>'
            out += f'<text x="{x+20}" y="{y+bh/2+9:.0f}" class="fi">{it}</text>'
        return out
    s += col(0, "Money comes from", left)
    mx = cw + gap
    s += f'<text x="{mx}" y="26" class="fh">Managed by</text>'
    s += f'<rect x="{mx}" y="50" width="{cw}" height="{H-60}" fill="{acc}"/>'
    for i, ln in enumerate(mid):
        s += f'<text x="{mx+cw/2}" y="{H/2 - 20 + i*44:.0f}" text-anchor="middle" class="{"fmb" if i==0 else "fm"}">{ln}</text>'
    s += col(2 * (cw + gap), "Lent out to", right)
    for x0 in (cw + 8, 2 * cw + gap + 8):
        s += f'<line x1="{x0}" y1="{H/2+25:.0f}" x2="{x0+gap-16:.0f}" y2="{H/2+25:.0f}" stroke="{acc}" stroke-width="5" marker-end="url(#fa)"/>'
    return s + "</svg>"

def bubbles_svg(W, H, big, smalls, acc, ink, fmtB):
    """One big circle vs a cluster of small ones; area = value."""
    k = min(H * 0.40, (W - 60) / 3.7) / math.sqrt(big[1])
    s = f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    R = k * math.sqrt(big[1]); cx = R + 10; cy = H / 2 - 20
    s += f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}" fill="{acc}"/>'
    s += f'<text x="{cx:.0f}" y="{cy-6:.0f}" text-anchor="middle" class="bb">{big[0]}</text><text x="{cx:.0f}" y="{cy+40:.0f}" text-anchor="middle" class="bbv">{fmtB(big[1])}</text>'
    # pack smalls greedily around a center on the right
    ox, oy = cx + R + 30 + (W - (cx + R + 30)) / 2, H / 2 - 20
    placed = []
    for name, v in sorted(smalls, key=lambda t: -t[1]):
        r = k * math.sqrt(v)
        if not placed:
            placed.append((ox, oy, r, name, v)); continue
        best = None
        for ang in range(0, 360, 6):
            for dist in range(0, 400, 3):
                x = ox + dist * math.cos(math.radians(ang)); y = oy + dist * math.sin(math.radians(ang))
                if all(math.hypot(x - px, y - py) >= r + pr + 4 for px, py, pr, *_ in placed):
                    if best is None or dist < best[0]: best = (dist, x, y)
                    break
        placed.append((best[1], best[2], r, name, v))
    for x, y, r, name, v in placed:
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{ink}" fill-opacity="0.9"/>'
        if r > 34:
            s += f'<text x="{x:.0f}" y="{y+7:.0f}" text-anchor="middle" class="bs">{name.split(" ")[0]}</text>'
    s += f'<text x="{ox:.0f}" y="{H-8:.0f}" text-anchor="middle" class="bl">The other 11 combined: {fmtB(sum(v for _, v in smalls))}</text>'
    return s + "</svg>"
