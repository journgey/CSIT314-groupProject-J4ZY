import json
import requests
from sqlite3 import Connection
from urllib.parse import urlencode
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

PA_PATH = Path(__file__).resolve().parent.parent / "resources" / "planning_areas.json"

class GeoRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self._pa_loaded = False
        self._pa_polys: Dict[str, List[Tuple[float, float]]] = {}
        self._pa_bbox: Dict[str, Tuple[float, float, float, float]] = {}

    def fetch_external_by_postal(self, postal_code: str) -> Optional[Dict[str, Any]]:
        try:
            url = "https://www.onemap.gov.sg/api/common/elastic/search?" + urlencode({
                "searchVal": postal_code,
                "returnGeom": "Y",
                "getAddrDetails": "Y",
                "pageNum": 1,
            })
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results") or []
            if not results:
                return None
            top = results[0]
            lat = float(top.get("LATITUDE"))
            lng = float(top.get("LONGITUDE"))
            addr = top.get("ADDRESS") or top.get("BLK_NO") or ""
            return {"postal_code": postal_code, "address": addr, "lat": lat, "lng": lng}
        except Exception:
            return None

    def list_regions(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM regions ORDER BY id")
        return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

    def list_districts(self, region_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if region_id:
            cur.execute("SELECT id, name, region_id FROM districts WHERE region_id=? ORDER BY id", (region_id,))
        else:
            cur.execute("SELECT id, name, region_id FROM districts ORDER BY id")
        return [{"id": d[0], "name": d[1], "region_id": d[2]} for d in cur.fetchall()]

    def _ensure_pa_loaded(self) -> None:
        if self._pa_loaded:
            return
        if not PA_PATH.exists():
            self._pa_loaded = True
            return
        try:
            data = json.loads(PA_PATH.read_text(encoding="utf-8"))
            for name, pts in data.items():
                if not pts:
                    continue
                poly = [(float(lat), float(lng)) for lat, lng in pts]
                name_u = name.upper()
                self._pa_polys[name_u] = poly
                self._pa_bbox[name_u] = self._compute_bbox(poly)
        except Exception:
            self._pa_polys = {}
            self._pa_bbox = {}
        finally:
            self._pa_loaded = True

    @staticmethod
    def _compute_bbox(poly: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
        lats = [p[0] for p in poly]
        lngs = [p[1] for p in poly]
        return (min(lats), min(lngs), max(lats), max(lngs))

    @staticmethod
    def _point_in_poly(lat: float, lng: float, poly: List[Tuple[float, float]]) -> bool:
        inside = False
        n = len(poly)
        if n < 3:
            return False
        for i in range(n):
            y1, x1 = poly[i]
            y2, x2 = poly[(i + 1) % n]
            if (y1 > lat) != (y2 > lat):
                x_at_y = x1 + (x2 - x1) * (lat - y1) / (y2 - y1 + 1e-15)
                if x_at_y > lng:
                    inside = not inside
        return inside

    def resolve_region_district_by_point(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        self._ensure_pa_loaded()
        if not self._pa_polys:
            return None

        target_pa = None
        for name_u, bbox in self._pa_bbox.items():
            minLat, minLng, maxLat, maxLng = bbox
            if not (minLat <= lat <= maxLat and minLng <= lng <= maxLng):
                continue
            if self._point_in_poly(lat, lng, self._pa_polys[name_u]):
                target_pa = name_u
                break

        if not target_pa:
            return None

        cur = self.conn.cursor()
        cur.execute("SELECT id, name, region_id FROM districts WHERE UPPER(name)=?", (target_pa,))
        row = cur.fetchone()
        if not row:
            return {"planning_area": target_pa.title()}

        did, dname, rid = row[0], row[1], row[2]
        cur.execute("SELECT name FROM regions WHERE id=?", (rid,))
        rrow = cur.fetchone()
        return {
            "planning_area": target_pa.title(),
            "district_id": did,
            "district_name": dname,
            "region_id": rid,
            "region_name": (rrow[0] if rrow else None),
        }
