# save as: dump_pa_coords.py
import os, json, requests, argparse

URL = "https://www.onemap.gov.sg/api/public/popapi/getAllPlanningarea"

def extract_latlng_list(geojson_dict):
    t = geojson_dict.get("type")
    coords = geojson_dict.get("coordinates") or []
    out = []
    if t == "Polygon":
        for ring in coords:                # ring: [[lng,lat], ...]
            for lng, lat in ring:
                out.append([lat, lng])     # [lat,lng]로 뒤집어 저장
    elif t == "MultiPolygon":
        for poly in coords:                # poly: [ring0, ring1, ...]
            for ring in poly:
                for lng, lat in ring:
                    out.append([lat, lng])
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", help="OneMap token; or set ONEMAP_TOKEN")
    ap.add_argument("--year", default="2019")
    ap.add_argument("--out", default="planning_areas_coords.json")
    args = ap.parse_args()

    token = args.token or os.getenv("ONEMAP_TOKEN")
    if not token:
        raise SystemExit("ERROR: token required (use --token or ONEMAP_TOKEN)")

    headers = {"Authorization": token}  # 처음 코드와 동일: Bearer 없음
    resp = requests.get(URL, params={"year": args.year}, headers=headers, timeout=30)
    print("status:", resp.status_code)
    # 디버깅을 위해 401/403이면 본문을 일부 출력
    if resp.status_code >= 400:
        print(resp.text[:300])
    resp.raise_for_status()

    data = resp.json()
    items = data.get("SearchResults") or []
    print("count:", len(items), "first5:", [it.get("pln_area_n") for it in items[:5]])

    result = {}
    skipped = 0
    for it in items:
        name = (it.get("pln_area_n") or "").strip()
        gj_str = it.get("geojson")
        if not name or not gj_str:
            skipped += 1
            continue
        try:
            gj = json.loads(gj_str)        # 문자열 → dict
            result[name] = extract_latlng_list(gj)  # 외곽/내부 모두 평탄화
        except Exception:
            skipped += 1

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"OK: areas saved={len(result)}, skipped={skipped}, file={args.out}")

if __name__ == "__main__":
    main()
