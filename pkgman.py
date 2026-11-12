"""PyPI-dən saf Python (pure-python) kitabxanaları yükləyib quraşdıran sadə menecer.

Android-də pip yoxdur, ona görə wheel faylını özümüz yükləyib site qovluğuna açırıq.
Yalnız "py3-none-any" tipli wheel-lər dəstəklənir (C kodlu paketlər olmur).
"""
import hashlib
import importlib
import io
import json
import os
import re
import shutil
import ssl
import sys
import urllib.error
import urllib.request
import zipfile

PYPI_URL = "https://pypi.org/pypi/{}/json"
TIMEOUT = 30


class PkgError(Exception):
    pass


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _vtuple(text):
    parts = []
    for p in re.split(r"[.]", text.strip()):
        m = re.match(r"\d+", p)
        parts.append(int(m.group()) if m else 0)
    return tuple(parts)


def _compare(op, left, right):
    return {
        "==": left == right, "!=": left != right,
        "<": left < right, "<=": left <= right,
        ">": left > right, ">=": left >= right,
    }.get(op, True)


def marker_ok(marker):
    """Requires-Dist şərtini (marker) sadə qaydada yoxlayır."""
    if not marker:
        return True
    if " or " in marker:
        return True
    env = {
        "sys_platform": "linux", "platform_system": "Linux", "os_name": "posix",
        "platform_machine": "aarch64", "implementation_name": "cpython",
        "platform_python_implementation": "CPython",
    }
    ver = ".".join(map(str, sys.version_info[:3]))
    short = ".".join(map(str, sys.version_info[:2]))
    for part in marker.replace("(", " ").replace(")", " ").split(" and "):
        part = part.strip()
        if not part:
            continue
        if "extra" in part:
            return False
        m = re.match(r"""(\w+)\s*(==|!=|<=|>=|<|>)\s*['"]([^'"]+)['"]""", part)
        if not m:
            continue
        key, op, value = m.groups()
        if key == "python_version":
            if not _compare(op, _vtuple(short), _vtuple(value)):
                return False
        elif key == "python_full_version":
            if not _compare(op, _vtuple(ver), _vtuple(value)):
                return False
        elif key in env:
            if not _compare(op, env[key], value):
                return False
    return True


def parse_requirement(line):
    """'requests (>=2.0) ; python_version>"3"' -> ('requests', marker_str)"""
    req, _, marker = line.partition(";")
    m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", req)
    if not m:
        return None, marker.strip()
    return m.group(1), marker.strip()


def pick_wheel(files):
    """Saf Python wheel-i seçir (py3-none-any). Tapılmasa None."""
    best = None
    for f in files:
        fn = f.get("filename", "")
        if not fn.endswith(".whl") or f.get("yanked"):
            continue
        tags = fn[:-4].split("-")
        if len(tags) < 5:
            continue
        py, abi, plat = tags[-3], tags[-2], tags[-1]
        if plat != "any" or abi != "none":
            continue
        pys = py.split(".")
        if any(p.startswith("py3") for p in pys):
            best = f
    return best


class PackageManager:
    def __init__(self, site_dir, log=print):
        self.site_dir = site_dir
        self.log = log
        self.meta_path = os.path.join(site_dir, ".installed.json")
        os.makedirs(site_dir, exist_ok=True)
        self.enable()

    def enable(self):
        if self.site_dir not in sys.path:
            sys.path.insert(0, self.site_dir)

    # ---------- metadata ----------
    def _load(self):
        try:
            with open(self.meta_path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def _save(self, data):
        with open(self.meta_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)

    def installed(self):
        """[(ad, versiya)] siyahısı, əlifba sırası ilə."""
        data = self._load()
        return sorted((v.get("name", k), v.get("version", "?")) for k, v in data.items())

    def is_installed(self, name):
        return normalize(name) in self._load()

    # ---------- şəbəkə ----------
    def _get(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "PyCreator/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_context()) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise PkgError("Belə paket PyPI-də tapılmadı.")
            raise PkgError("Server xətası: %s" % e.code)
        except (urllib.error.URLError, OSError) as e:
            raise PkgError("İnternet bağlantısı yoxdur və ya server cavab vermir.")

    def lookup(self, name):
        """PyPI-dən paket məlumatı: dict(name, version, summary, wheel, requires)."""
        raw = self._get(PYPI_URL.format(normalize(name)))
        try:
            data = json.loads(raw.decode("utf-8"))
        except ValueError:
            raise PkgError("PyPI-dən gözlənilməz cavab gəldi.")
        info = data.get("info", {})
        return {
            "name": info.get("name", name),
            "version": info.get("version", "?"),
            "summary": info.get("summary") or "",
            "wheel": pick_wheel(data.get("urls", [])),
            "requires": info.get("requires_dist") or [],
        }

    # ---------- quraşdırma ----------
    def install(self, name, _seen=None):
        """Paketi və asılılıqlarını quraşdırır. Quraşdırılan adların siyahısını qaytarır."""
        seen = _seen if _seen is not None else set()
        key = normalize(name)
        if key in seen or self.is_installed(key):
            return []
        seen.add(key)
        self.log("Axtarılır: %s" % name)
        pkg = self.lookup(name)
        wheel = pkg["wheel"]
        if wheel is None:
            raise PkgError(
                "'%s' saf Python wheel təqdim etmir (ehtimal ki, C kodludur, "
                "məsələn numpy/pandas). Android-də bu üsulla quraşdırıla bilmir." % pkg["name"])
        done = []
        for line in pkg["requires"]:
            dep, marker = parse_requirement(line)
            if dep and marker_ok(marker):
                done += self.install(dep, seen)
        self.log("Yüklənir: %s %s" % (pkg["name"], pkg["version"]))
        blob = self._get(wheel["url"])
        want = (wheel.get("digests") or {}).get("sha256")
        if want and hashlib.sha256(blob).hexdigest() != want:
            raise PkgError("Yüklənən fayl zədəlidir (yoxlama məbləği uyğun deyil).")
        entries = self._extract(blob)
        data = self._load()
        data[key] = {"name": pkg["name"], "version": pkg["version"], "files": entries}
        self._save(data)
        importlib.invalidate_caches()
        self.log("Quraşdırıldı: %s %s" % (pkg["name"], pkg["version"]))
        return done + [pkg["name"]]

    def _extract(self, blob):
        root = os.path.realpath(self.site_dir)
        tops = set()
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                rel = member.filename.replace("\\", "/")
                m = re.match(r"[^/]+\.data/(purelib|platlib)/(.*)", rel)
                if m:
                    rel = m.group(2)
                elif rel.split("/")[0].endswith(".data"):
                    continue
                target = os.path.realpath(os.path.join(root, rel))
                if not target.startswith(root + os.sep):
                    raise PkgError("Paketdə təhlükəli fayl yolu var, ləğv edildi.")
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                tops.add(rel.split("/")[0])
        return sorted(tops)

    # ---------- silmə ----------
    def remove(self, name):
        data = self._load()
        key = normalize(name)
        if key not in data:
            raise PkgError("'%s' quraşdırılmayıb." % name)
        keep = set()
        for other, meta in data.items():
            if other != key:
                keep.update(meta.get("files", []))
        for entry in data[key].get("files", []):
            if entry in keep:
                continue
            path = os.path.join(self.site_dir, entry)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.exists(path):
                os.remove(path)
        del data[key]
        self._save(data)
        importlib.invalidate_caches()
        self.log("Silindi: %s" % name)
