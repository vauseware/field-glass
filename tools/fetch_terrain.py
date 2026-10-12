#!/usr/bin/env python3
"""Fetch a square elevation grid from USGS 3DEP (10 m, US only) as terrain.json.

usage: python3 tools/fetch_terrain.py LAT LON HALF_METERS COLS OUT.json

Grid is row-major, north row first, west column first, metres above sea level.
Local coords: x east, y north, metres from (LAT, LON) at the grid centre.
"""
import json, math, struct, sys, urllib.parse, urllib.request

SERVICE = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage"


def read_tiff(buf):
    bo = {b"II": "<", b"MM": ">"}[buf[:2]]
    (ifd,) = struct.unpack_from(bo + "I", buf, 4)
    (n,) = struct.unpack_from(bo + "H", buf, ifd)
    size = {1: 1, 2: 1, 3: 2, 4: 4, 11: 4, 12: 8}
    fmt = {1: "B", 2: "c", 3: "H", 4: "I", 11: "f", 12: "d"}
    tags = {}
    for i in range(n):
        tag, typ, cnt, val = struct.unpack_from(bo + "HHII", buf, ifd + 2 + 12 * i)
        if typ not in size:
            continue
        off = ifd + 2 + 12 * i + 8 if size[typ] * cnt <= 4 else val
        tags[tag] = struct.unpack_from(bo + fmt[typ] * cnt, buf, off)
    w, h = tags[256][0], tags[257][0]
    assert tags.get(259, (1,))[0] == 1, "compressed TIFF; ask the service for uncompressed"
    bits, sf = tags[258][0], tags.get(339, (1,))[0]
    kind = {(32, 3): "f", (64, 3): "d", (16, 2): "h", (16, 1): "H", (8, 1): "B"}[(bits, sf)]
    if 273 in tags:  # strips
        data = b"".join(buf[o : o + c] for o, c in zip(tags[273], tags[279]))
        return w, h, struct.unpack(bo + kind * (w * h), data[: w * h * struct.calcsize(kind)])
    tw, th = tags[322][0], tags[323][0]  # tiles, row-major, edge tiles padded
    across = -(-w // tw)
    z = [0.0] * (w * h)
    for i, (o, c) in enumerate(zip(tags[324], tags[325])):
        tile = struct.unpack(bo + kind * (tw * th), buf[o : o + tw * th * struct.calcsize(kind)])
        ty, tx = divmod(i, across)
        for r in range(th):
            y = ty * th + r
            if y >= h:
                break
            for cc in range(min(tw, w - tx * tw)):
                z[y * w + tx * tw + cc] = tile[r * tw + cc]
    return w, h, z


def fetch(lat, lon, half, cols):
    dlat = half / 111320.0
    dlon = half / (111320.0 * math.cos(math.radians(lat)))
    q = dict(bbox=f"{lon-dlon},{lat-dlat},{lon+dlon},{lat+dlat}", bboxSR=4326, imageSR=4326,
             size=f"{cols},{cols}", format="tiff", pixelType="F32", noData=0,
             interpolation="RSP_BilinearInterpolation", f="image")
    with urllib.request.urlopen(SERVICE + "?" + urllib.parse.urlencode(q), timeout=120) as r:
        w, h, z = read_tiff(r.read())
    return dict(origin=dict(lat=lat, lon=lon), spacing=round(2 * half / cols, 3), cols=w, rows=h,
                source="USGS 3DEP via elevation.nationalmap.gov", z=[round(v, 1) for v in z])


if __name__ == "__main__":
    lat, lon, half, cols, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    t = fetch(lat, lon, half, cols)
    zs = [v for v in t["z"] if v]
    with open(out, "w") as f:
        json.dump(t, f, separators=(",", ":"))
    print(f"{out}: {t['cols']}x{t['rows']} @ {t['spacing']} m, z {min(zs):.0f}-{max(zs):.0f} m")
