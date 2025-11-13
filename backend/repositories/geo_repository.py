import time
from pathlib import Path
from dotenv import load_dotenv
import json
import os
import requests
from sqlite3 import Connection
from urllib.parse import urlencode
from typing import Optional, Dict, Any, List, Tuple

# Load project root and environment variables
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# Static resource and token file paths
PA_PATH = Path(__file__).resolve().parent.parent / "resources" / "planning_areas.json"
TOKEN_PATH = Path(__file__).resolve().parent.parent / "resources" / "onemap_token.json"

# Token expiry skew (in seconds)
SKEW = 60


class GeoRepository:
    """Handles OneMap postal lookup, region/district listing, and spatial mapping."""

    def __init__(self, conn: Connection):
        self.conn = conn
        self._pa_loaded = False
        self._pa_polys: Dict[str, List[Tuple[float, float]]] = {}
        self._pa_bbox: Dict[str, Tuple[float, float, float, float]] = {}

    # ===================== Token Handling =====================
    def _get_token(self, refresh: bool = False) -> Optional[str]:
        """
        Retrieve a valid OneMap access token.
        - If refresh=True, bypass cache and request a new token.
        - Otherwise, reuse cached token if not expired.
        """
        # Try to reuse cached token (unless refresh is requested)
        if not refresh and TOKEN_PATH.exists():
            try:
                data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
                exp = int(data.get("expiry_timestamp", 0))
                if time.time() + SKEW < exp:
                    return data.get("access_token")
            except Exception:
                pass  # ignore cache errors and fall through

        # Request a new token
        email = os.getenv("ONEMAP_EMAIL")
        password = os.getenv("ONEMAP_EMAIL_PASSWORD") or os.getenv("ONEMAP_PASSWORD")
        if not email or not password:
            # Token is optional for some public APIs; return None if creds are missing
            return None

        url = "https://www.onemap.gov.sg/api/auth/post/getToken"
        resp = requests.post(url, json={"email": email, "password": password}, timeout=5)
        resp.raise_for_status()
        token_data = resp.json()

        access_token = token_data.get("access_token")
        expiry_raw = token_data.get("expiry_timestamp")
        if not access_token or not expiry_raw:
            raise RuntimeError(f"Invalid token payload: {token_data}")

        exp = int(expiry_raw)
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(
            json.dumps({"access_token": access_token, "expiry_timestamp": exp}, indent=2),
            encoding="utf-8",
        )
        return access_token

    # ===================== Postal Lookup =====================
    def fetch_external_by_postal(self, postal_code: str) -> Optional[Dict[str, Any]]:
        """Return {postal_code, address, lat, lng} or None. Retry once on 401/403/token error."""
        url = "https://www.onemap.gov.sg/api/common/elastic/search"
        params = {
            "searchVal": postal_code,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": 1,
        }

        def _once(token: str | None):
            headers = {"Authorization": token} if token else {}
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            return resp

        token = self._get_token()
        resp = _once(token)

        if resp.status_code in (401, 403) or "token" in (resp.text or "").lower():
            token = self._get_token(refresh=True) 
            resp = _once(token)

        resp.raise_for_status()
        data = resp.json()
        items = data.get("results") or []
        if not items:
            return None

        top = items[0]
        try:
            lat = float(top["LATITUDE"])
            lng = float(top["LONGITUDE"])
        except (KeyError, TypeError, ValueError):
            return None

        address = top.get("ADDRESS") or top.get("BLK_NO") or ""
        return {"postal_code": postal_code, "address": address, "lat": lat, "lng": lng}

    # ===================== Region and District Listing =====================
    def list_regions(self) -> list[dict]:
        """Return all regions sorted alphabetically (for dropdown lists)."""
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM regions ORDER BY name COLLATE NOCASE ASC")
        rows = cur.fetchall()
        return [dict(id=row[0], name=row[1]) for row in rows]

    def list_districts(self, region_id: int | None = None) -> list[dict]:
        """
        Return districts filtered by region_id (if provided),
        sorted alphabetically for UI dropdown lists.
        """
        cur = self.conn.cursor()
        if region_id is not None:
            cur.execute(
                "SELECT id, name FROM districts WHERE region_id = ? ORDER BY name COLLATE NOCASE ASC",
                (region_id,),
            )
        else:
            cur.execute("SELECT id, name FROM districts ORDER BY name COLLATE NOCASE ASC")
        rows = cur.fetchall()
        return [dict(id=row[0], name=row[1]) for row in rows]

    # ===================== Coordinate to Region/District Resolution =====================
    def resolve_region_district_by_point(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        # --- 1) Call OneMap POP API ---
        url = "https://www.onemap.gov.sg/api/public/popapi/getPlanningarea"
        params = {"latitude": lat, "longitude": lng, "year": 2019}
        token = self._get_token()  # token may be optional for some public APIs, but include if we have it
        headers = {"Authorization": token} if token else {}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            # If token was invalid/expired, try once more with a refreshed token
            if resp.status_code in (401, 403):
                token = self._get_token(refresh=True)
                headers = {"Authorization": token} if token else {}
                resp = requests.get(url, params=params, headers=headers, timeout=5)

            resp.raise_for_status()
            data = resp.json()
        except Exception:
            # If the external call fails, return None (or you can log and fall back if needed)
            return None

        if not isinstance(data, list) or not data:
            return None

        pa_name = (data[0].get("pln_area_n") or "").strip()
        if not pa_name:
            return None

        pa_upper = pa_name.upper()

        # --- 2) Map planning area → our districts/regions ---
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, region_id FROM districts WHERE UPPER(name)=?", (pa_upper,))
        row = cur.fetchone()
        if not row:
            # PA is known, but we do not have a matching district
            return {"planning_area": pa_name.title()}

        did, dname, rid = row[0], row[1], row[2]
        cur.execute("SELECT name FROM regions WHERE id=?", (rid,))
        rrow = cur.fetchone()

        return {
            "planning_area": pa_name.title(),
            "district_id": did,
            "district_name": dname,
            "region_id": rid,
            "region_name": (rrow[0] if rrow else None),
        }

