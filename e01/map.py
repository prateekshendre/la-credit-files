"""Map of LA-area credit managers drawn from GeoJSON boundaries (no tiles)."""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LON0, LON1, LAT0, LAT1 = -118.98, -117.70, 33.50, 34.30
K = math.cos(math.radians(33.9))

# Main office of each adviser group, geocoded by hand from the Form ADV address.
# (group, lat, lon, label dx, label dy, anchor)
PINS = [
    ("PIMCO",          33.6155, -117.8770, -150,   20, "end"),
    ("Ares",           34.0585, -118.4145,   70, -120, "start"),
    ("TCW",            34.0509, -118.2556,  110,   70, "start"),
    ("Western Asset",  34.1458, -118.1430,   70,  -75, "start"),
    ("Oaktree",        34.0527, -118.2513,  110,   10, "start"),
    ("Payden & Rygel", 34.0530, -118.2510,  110,  -50, "start"),
    ("Crescent",       34.0507, -118.4436,  -55, -150, "end"),
    ("Cliffwater",     33.9806, -118.4400, -110,   70, "end"),
    ("Beach Point",    34.0327, -118.4740, -150,   34, "end"),
    ("PennyMac",       34.1523, -118.8160,  -10,  -42, "start"),
    ("Mesa West",      34.0478, -118.4630,  -40, -108, "end"),
    ("Silver Rock",    34.0440, -118.4720,  -45,  -64, "end"),
]
PLACES = [("Malibu", 34.02, -118.70), ("Santa Monica", 34.012, -118.52), ("Downtown", 34.018, -118.245),
          ("Pasadena", 34.168, -118.16), ("Long Beach", 33.79, -118.17), ("Newport Beach", 33.522, -117.82),
          ("LAX", 33.943, -118.40)]

def make_proj(W):
    k = W / ((LON1 - LON0) * K)
    H = (LAT1 - LAT0) * k
    return (lambda lat, lon: ((lon - LON0) * K * k, (LAT1 - lat) * k)), H

def _paths(geom, P):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out = []
    for poly in polys:
        for ring in poly:
            pts = [P(lat, lon) for lon, lat in ring]
            if not any(-50 < x < 2000 and -50 < y < 2000 for x, y in pts):
                continue
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts[::1]) + "Z")
    return "".join(out)

def map_svg(groups, fmtB, c, W=920, highlight=("Ares",)):
    """groups: dict group -> AUM in $B. c: dict of colors (land, edge, ink, acc, mute, bg)."""
    P, H = make_proj(W)
    s = f'<svg viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" style="overflow:hidden">'
    s += f'<defs><clipPath id="clip"><rect width="{W}" height="{H:.0f}"/></clipPath></defs><g clip-path="url(#clip)">'
    s += f'<rect width="{W}" height="{H:.0f}" fill="{c["sea"]}"/>'
    cty = json.load(open(os.path.join(ROOT, "data", "geo", "socal_counties.geojson")))
    for f in cty["features"]:
        s += f'<path d="{_paths(f["geometry"], P)}" fill="{c["land"]}" stroke="{c["edge"]}" stroke-width="1.2"/>'
    hood = json.load(open(os.path.join(ROOT, "data", "geo", "los-angeles-county.geojson")))
    s += f'<g fill="{c["land"]}" stroke="{c["hood"]}" stroke-width="0.7">'
    for f in hood["features"]:
        if f["properties"]["name"] in ("Avalon", "Unincorporated Catalina Island"):
            continue
        s += f'<path d="{_paths(f["geometry"], P)}"/>'
    s += "</g>"
    for name, lat, lon in PLACES:
        x, y = P(lat, lon)
        s += f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" class="place">{name}</text>'
    x, y = P(33.70, -118.70)
    s += f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" class="sea">Pacific Ocean</text>'
    # circles, biggest first
    for g, lat, lon, *_ in sorted(PINS, key=lambda p: -groups[p[0]]):
        x, y = P(lat, lon); r = min(max(4.5, 1.45 * math.sqrt(groups[g])), 58)
        s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c["acc"]}" fill-opacity="0.78" stroke="{c["bg"]}" stroke-width="1.5"/>'
    # labels with leader lines
    for g, lat, lon, dx, dy, anc in PINS:
        x, y = P(lat, lon); tx, ty = x + dx, y + dy
        ex = tx + (6 if anc == "end" else -6)
        s += f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ty-7:.1f}" stroke="{c["ink"]}" stroke-opacity="0.55" stroke-width="1.3"/>'
        s += f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anc}" class="pin">{g} <tspan class="pinv">{fmtB(groups[g])}</tspan></text>'
    return s + "</g></svg>", H
