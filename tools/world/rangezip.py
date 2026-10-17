"""List, and optionally extract one file from, the Offline DAoC release zip (split in parts)
without downloading it: reads only the needed bytes with HTTP range requests.

  python3 -I rangezip.py                        list the DB and progress-policy entries
  python3 -I rangezip.py <entry> <out file>     extract one entry and print its SHA-256
Edit BASE for another release (parts .001, .002, .003).
"""
import io, sys, zipfile, urllib.request, re, hashlib
BASE = "https://github.com/shadowofze/OfflineDAoC/releases/download/v0.36b/OfflineDAoC-v0.36b.zip.%03d"
def get(url, a, b):
    for _ in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}"}), timeout=120)
            return r.read(), r.headers.get("Content-Range")
        except Exception as e:
            err = e
    raise err
class R(io.RawIOBase):
    def __init__(s):
        s.parts = []
        for i in (1, 2, 3):
            _, cr = get(BASE % i, 0, 0)
            s.parts.append(int(cr.split("/")[1]))
        s.size = sum(s.parts); s.pos = 0
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s, o, w=0):
        s.pos = o if w == 0 else s.pos + o if w == 1 else s.size + o
        return s.pos
    def read(s, n=-1):
        if n < 0 or s.pos + n > s.size: n = s.size - s.pos
        out = b""; pos = s.pos; end = pos + n; base = 0
        for i, sz in enumerate(s.parts):
            lo, hi = max(pos, base), min(end, base + sz)
            if lo < hi: out += get(BASE % (i + 1), lo - base, hi - base - 1)[0]
            base += sz
        s.pos = end
        return out
    def readinto(s, b):
        d = s.read(len(b)); b[:len(d)] = d; return len(d)
z = zipfile.ZipFile(io.BufferedReader(R(), 8 * 1024 * 1024))
names = z.namelist()
print(len(names), "entries")
for n in names:
    if re.search(r"(progress-policy|opendaoc\.sqlite3\.db$|download-manifest)", n): print(n, z.getinfo(n).file_size, z.getinfo(n).compress_size)
if len(sys.argv) > 1:
    want, out = sys.argv[1], sys.argv[2]
    h = hashlib.sha256()
    with z.open(want) as src, open(out, "wb") as dst:
        while chunk := src.read(1 << 20): dst.write(chunk); h.update(chunk)
    print("sha256", h.hexdigest())
