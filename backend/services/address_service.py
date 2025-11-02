import re
from typing import Dict, Any, Optional
from backend.repositories.geo_repository import GeoRepository

class AddressService:
    def __init__(self, repo: GeoRepository):
        self.repo = repo

    def lookup(self, postal_code: str) -> Dict[str, Any]:
        if not postal_code or not postal_code.strip():
            return None

        ext = self.repo.fetch_external_by_postal(postal_code.strip())
        if not ext:
            return {"error": "postal code not found"}

        lat = ext.get("lat")
        lng = ext.get("lng")
        addr = ext.get("address") or ""

        mapped = None
        if lat is not None and lng is not None:
            mapped = self.repo.resolve_region_district_by_point(lat, lng)

        resp = {
            "postal_code": postal_code,
            "address": addr,
            "lat": lat,
            "lng": lng,
            "planning_area": mapped.get("planning_area") if mapped else None,
            "district_id": mapped.get("district_id") if mapped else None,
            "district_name": mapped.get("district_name") if mapped else None,
            "region_id": mapped.get("region_id") if mapped else None,
            "region_name": mapped.get("region_name") if mapped else None,
        }
        return resp

    def enrich_request_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(payload)
        postal = (out.get("postal_code") or "").strip()
        need_region = out.get("region_id") in (None, "")
        need_district = out.get("district_id") in (None, "")

        if postal and (need_region or need_district or not out.get("address")):
            looked = self.lookup(postal)
            out.setdefault("region_id", looked.get("region_id"))
            out.setdefault("district_id", looked.get("district_id"))
            out.setdefault("address", looked.get("address"))
            out.setdefault("lat", looked.get("lat"))
            out.setdefault("lng", looked.get("lng"))
        return out
