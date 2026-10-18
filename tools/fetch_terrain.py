#!/usr/bin/env python3
"""Fetch a square elevation grid as terrain.json: USGS 3DEP (10 m, US only) by default,
or Copernicus GLO-30 (30 m, worldwide) with --copernicus.

usage: python3 tools/fetch_terrain.py [--copernicus] LAT LON HALF_METERS COLS OUT.json

Grid is row-major, north row first, west column first, metres above sea level.
Local coords: x east, y north, metres from (LAT, LON) at the grid centre.
"""
import itertools, json, math, struct, sys, urllib.error, urllib.parse, urllib.request, zlib

SERVICE = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage"
COPERNICUS = "https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif"
COPERNICUS_CREDIT = ("Copernicus GLO-30 DSM via AWS Open Data. Produced using Copernicus WorldDEM-30 "
                     "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under "
                     "COPERNICUS by the European Union and ESA; all rights reserved")


def ifd_tags(read):
    """First IFD of a classic TIFF; read(offset, n) returns n bytes from the file."""
    head = read(0, 8)
    bo = {b"II": "<", b"MM": ">"}[head[:2]]
    assert struct.unpack_from(bo + "H", head, 2)[0] == 42, "not a classic TIFF"
    (ifd,) = struct.unpack_from(bo + "I", head, 4)
    (n,) = struct.unpack(bo + "H", read(ifd, 2))
    entries = read(ifd + 2, 12 * n)
    size = {1: 1, 2: 1, 3: 2, 4: 4, 11: 4, 12: 8}
    fmt = {1: "B", 2: "c", 3: "H", 4: "I", 11: "f", 12: "d"}
    tags = {}
    for i in range(n):
        tag, typ, cnt, val = struct.unpack_from(bo + "HHII", entries, 12 * i)
        if typ not in size:
            continue
        raw = entries[12 * i + 8 : 12 * i + 12] if size[typ] * cnt <= 4 else read(val, size[typ] * cnt)
        tags[tag] = struct.unpack_from(bo + fmt[typ] * cnt, raw)
    return bo, tags


def read_tiff(buf):
    bo, tags = ifd_tags(lambda o, n: buf[o : o + n])
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


class CopernicusTile:
    """One 1-degree GLO-30 cloud-optimised GeoTIFF. Reads the header, then only the
    1024-pixel tiles that get sampled, by HTTP range request. Open sea has no file: 0 m."""

    def __init__(self, ilat, ilon):
        ns, ew = "NS"[ilat < 0], "EW"[ilon < 0]
        name = f"Copernicus_DSM_COG_10_{ns}{abs(ilat):02d}_00_{ew}{abs(ilon):03d}_00_DEM"
        self.url, self.tiles = COPERNICUS.format(name=name), {}
        try:
            self.bo, t = ifd_tags(self.read)
        except urllib.error.HTTPError as e:
            if e.code not in (403, 404):
                raise
            self.url = None
            return
        self.w, self.h, self.tw, self.th = t[256][0], t[257][0], t[322][0], t[323][0]
        self.offsets, self.counts = t[324], t[325]
        self.deflate, self.predictor = t.get(259, (1,))[0] == 8, t.get(317, (1,))[0]
        assert t[258][0] == 32 and t.get(339, (1,))[0] == 3, "expected Float32 samples"
        assert self.predictor in (1, 3), f"predictor {self.predictor}"
        self.sx, self.sy = t[33550][0], t[33550][1]
        self.x0, self.y0 = t[33922][3], t[33922][4]
        keys = t.get(34735, ())
        point = any(keys[i] == 1025 and keys[i + 3] == 2 for i in range(4, len(keys), 4))
        self.half = 0.0 if point else 0.5  # PixelIsArea: the tiepoint is a pixel corner, not its centre

    def read(self, off, n):
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={off}-{off + n - 1}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()

    def tile(self, i):
        if i not in self.tiles:
            raw = self.read(self.offsets[i], self.counts[i])
            raw = zlib.decompress(raw) if self.deflate else raw
            tw, rows = self.tw, []
            for r in range(self.th):
                row = raw[4 * tw * r : 4 * tw * (r + 1)]
                if self.predictor == 3:  # undo byte differencing, then re-interleave the MSB-first byte planes
                    row = bytes(itertools.accumulate(row, lambda a, b: (a + b) & 255))
                    out = bytearray(4 * tw)
                    for k in range(4):
                        out[k::4] = row[k * tw : (k + 1) * tw]
                    rows.extend(struct.unpack(">" + "f" * tw, out))
                else:
                    rows.extend(struct.unpack(self.bo + "f" * tw, row))
            self.tiles[i] = rows
        return self.tiles[i]

    def pixel(self, r, c):
        r, c = min(max(r, 0), self.h - 1), min(max(c, 0), self.w - 1)
        across = -(-self.w // self.tw)
        t = self.tile((r // self.th) * across + c // self.tw)
        return t[(r % self.th) * self.tw + c % self.tw]

    def elevation(self, lat, lon):
        if not self.url:
            return 0.0
        fc, fr = (lon - self.x0) / self.sx - self.half, (self.y0 - lat) / self.sy - self.half
        c, r = math.floor(fc), math.floor(fr)
        u, v = fc - c, fr - r
        top = self.pixel(r, c) * (1 - u) + self.pixel(r, c + 1) * u
        bottom = self.pixel(r + 1, c) * (1 - u) + self.pixel(r + 1, c + 1) * u
        return top * (1 - v) + bottom * v


def fetch_copernicus(lat, lon, half, cols):
    dlat = half / 111320.0
    dlon = half / (111320.0 * math.cos(math.radians(lat)))
    tiles, z = {}, []
    for r in range(cols):  # pixel centres, as the 3DEP export lays them out
        la = lat + dlat - (r + 0.5) * 2 * dlat / cols
        for c in range(cols):
            lo = lon - dlon + (c + 0.5) * 2 * dlon / cols
            key = (math.floor(la), math.floor(lo))
            if key not in tiles:
                tiles[key] = CopernicusTile(*key)
            z.append(round(tiles[key].elevation(la, lo), 1))
    return dict(origin=dict(lat=lat, lon=lon), spacing=round(2 * half / cols, 3), cols=cols, rows=cols,
                source=COPERNICUS_CREDIT, z=z)


if __name__ == "__main__":
    args = sys.argv[1:]
    copernicus = "--copernicus" in args
    if copernicus:
        args.remove("--copernicus")
    lat, lon, half, cols, out = float(args[0]), float(args[1]), float(args[2]), int(args[3]), args[4]
    t = (fetch_copernicus if copernicus else fetch)(lat, lon, half, cols)
    zs = [v for v in t["z"] if v]
    with open(out, "w") as f:
        json.dump(t, f, separators=(",", ":"))
    print(f"{out}: {t['cols']}x{t['rows']} @ {t['spacing']} m, z {min(zs):.0f}-{max(zs):.0f} m")
