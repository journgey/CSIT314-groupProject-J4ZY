import re
from typing import Dict, Any, Optional
from backend.repositories.geo_repository import GeoRepository

class AddressController:
    def __init__(self, repo):
        self.repo = repo
        self._sg_postal_re = re.compile(r"^\d{6}$")  # Singapore 6-digit postal code

    def lookup(self, postal_code: str) -> Dict[str, Any]:
        """
        Normalize postal code, call external geocoder, resolve planning area → region/district,
        and return a consistent payload. Never raises; returns {"error": "..."} on failures.
        """
        pc = (postal_code or "").strip()
        if not pc or not self._sg_postal_re.match(pc):
            return {"error": "invalid postal code", "postal_code": pc or None}

        try:
            ext = self.repo.fetch_external_by_postal(pc)
        except Exception as e:
            return {"error": f"address lookup failed: {e}", "postal_code": pc}

        if not ext:
            return {"error": "postal code not found", "postal_code": pc}

        # External payload normalization
        lat = ext.get("lat")
        lng = ext.get("lng")
        addr = ext.get("address") or ""

        # Resolve planning area → our district/region via OneMap POP API
        mapped: Optional[Dict[str, Any]] = None
        if lat is not None and lng is not None:
            try:
                mapped = self.repo.resolve_region_district_by_point(lat, lng)
            except Exception as e:
                # Mapping failure should not kill the whole response
                mapped = {"_mapping_error": str(e)}

        # Compose consistent response
        return {
            "postal_code": pc,
            "address": addr or None,
            "lat": lat,
            "lng": lng,
            "planning_area": (mapped or {}).get("planning_area"),
            "district_id": (mapped or {}).get("district_id"),
            "district_name": (mapped or {}).get("district_name"),
            "region_id": (mapped or {}).get("region_id"),
            "region_name": (mapped or {}).get("region_name"),
            # Optional diagnostic (not required by client; remove if undesired)
            # "_mapping_error": (mapped or {}).get("_mapping_error"),
        }

    def enrich_request_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill region_id / district_id / address / lat / lng from postal code when missing.
        Only sets fields if lookup succeeds and values exist.
        """
        out = dict(payload or {})
        postal = (out.get("postal_code") or "").strip()

        need_region   = out.get("region_id")   in (None, "")
        need_district = out.get("district_id") in (None, "")
        need_address  = not (out.get("address") or "").strip()
        need_coords   = out.get("lat") in (None, "") or out.get("lng") in (None, "")

        if postal and (need_region or need_district or need_address or need_coords):
            looked = self.lookup(postal)

            # Abort silently if lookup failed
            if not looked or looked.get("error"):
                return out

            # Set only when value exists
            if need_region and looked.get("region_id") is not None:
                out["region_id"] = looked["region_id"]
            if need_district and looked.get("district_id") is not None:
                out["district_id"] = looked["district_id"]
            if need_address and looked.get("address"):
                out["address"] = looked["address"]
            if need_coords:
                if looked.get("lat") is not None:
                    out["lat"] = looked["lat"]
                if looked.get("lng") is not None:
                    out["lng"] = looked["lng"]

            # Optional: propagate planning_area for UI hints (does not affect DB)
            if looked.get("planning_area"):
                out.setdefault("planning_area", looked["planning_area"])

        return out