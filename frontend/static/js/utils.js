// === Minimal utils.js for PIN_edit_request.html ===

// --- ENDPOINTS ---
const CONFIG = {
  ENDPOINTS: {
    AUTH_ME: "/api/auth/me",

    CATEGORY: "/api/category",   // GET /, GET /:id ...
    REQUEST:  "/api/request",    // GET /, GET /:id, POST /, PUT /:id, DELETE /:id

    REGION:   "/api/address/regions",
    DISTRICT: "/api/address/districts",
    LOOKUP:   "/api/address/lookup", // POST { postal_code }
  },
};

// --- HTTP core ---
async function _fetch(url, opts = {}) {
  const res = await fetch(url, { credentials: "include", ...opts });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const t = await res.text();
      try { const j = JSON.parse(t); msg = j?.error || j?.message || msg; }
      catch { msg = t || msg; }
    } catch {}
    throw new Error(`${url} → ${msg}`);
  }
  if (res.status === 204) return null;
  const txt = await res.text();
  return txt ? JSON.parse(txt) : null;
}
const _get  = (u)    => _fetch(u);
const _post = (u,b)  => _fetch(u, { method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify(b ?? {}) });
const _put  = (u,b)  => _fetch(u, { method:"PUT",  headers:{ "Content-Type":"application/json" }, body:JSON.stringify(b ?? {}) });
const _del  = (u)    => _fetch(u, { method:"DELETE" });

// --- Small helpers used by the page ---
function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>\"']/g, m => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[m]);
}

function normalizeRole(role) {
  const r = String(role || "").trim().toLowerCase();
  if (!r) return "";
  if (r === "useradmin" || r === "ua") return "UserAdmin";
  if (r === "platformmanager" || r === "pm") return "PlatformManager";
  if (r === "pin") return "PIN";
  if (r === "csr") return "CSR";
  return role;
}

function redirectByRole(role, fallback = "/") {
  const map = { UserAdmin: "/useradmin", PlatformManager: "/pm", PIN: "/pin", CSR: "/csr" };
  const key = normalizeRole(role);
  const target = map[key];
  if (!target) return false;
  window.location.href = target;
  return true;
}

async function getMe() { return _get(CONFIG.ENDPOINTS.AUTH_ME); }

async function installAuthGuard(requiredRole = null) {
  try {
    const me = await getMe();
    if (!me?.role) { window.location.href = "/"; return; }
    if (requiredRole && normalizeRole(me.role) !== requiredRole) {
      window.location.href = "/"; return;
    }
  } catch {
    window.location.href = "/";
  }
}

// URL/datetime/dom helpers actually used by utils.pin.edit
const url = {
  withTs: (u) => `${u}${u.includes("?") ? "&" : "?"}_ts=${Date.now()}`
};
const dt = {
  split(isoLike) {
    if (!isoLike) return { d:"", t:"" };
    const s = String(isoLike).trim().replace("T"," ");
    const [d, time=""] = s.split(" ");
    const t = time.slice(0,5);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return { d:"", t:"" };
    return { d, t };
  },
  join(dateStr, timeStr) {
    const d = (dateStr || "").trim();
    const t = (timeStr || "00:00").trim();
    if (!d) return null;
    return `${d} ${t}:00`;
  }
};
const dom = {
  $: (sel, root=document) => root.querySelector(sel),
  setText: (selOrEl, text) => {
    const el = typeof selOrEl === "string" ? document.querySelector(selOrEl) : selOrEl;
    if (el) el.textContent = text ?? "";
  }
};

// --- API facades used on this page ---
const categories = {
  list: async () => {
    const res = await _get(`${CONFIG.ENDPOINTS.CATEGORY}/`);
    return Array.isArray(res) ? res : (res?.items ?? []);
  }
};

const requests = {
  get:    (id)      => _get(`${CONFIG.ENDPOINTS.REQUEST}/${id}`),
  create: (payload) => _post(`${CONFIG.ENDPOINTS.REQUEST}/`, payload),
  update: (id,pay)  => _put(`${CONFIG.ENDPOINTS.REQUEST}/${id}`, pay),
  remove: (id)      => _del(`${CONFIG.ENDPOINTS.REQUEST}/${id}`),
};

const geo = {
  regions:   () => _get(CONFIG.ENDPOINTS.REGION),
  districts: (regionId) => {
    const qs = regionId ? `?region_id=${encodeURIComponent(regionId)}` : "";
    return _get(`${CONFIG.ENDPOINTS.DISTRICT}${qs}`);
  },
  fillSelect(selectEl, items, placeholder="-- Select --", nameKey="name") {
    if (!selectEl) return;
    const head = `<option value="">${escapeHtml(placeholder)}</option>`;
    const opts = (items || []).map(x =>
      `<option value="${x.id}">${escapeHtml(x[nameKey] ?? x.title ?? `#${x.id}`)}</option>`
    ).join("");
    selectEl.innerHTML = head + opts;
  }
};

const address = {
  lookupPostal: (postal_code) => _post(CONFIG.ENDPOINTS.LOOKUP, { postal_code })
};

// --- PIN edit helpers (only the 5 funcs the page calls) ---
const pin = {};
pin.edit = {
  async loadMasters($category, $region, $district) {
    const [cats, regs] = await Promise.all([ categories.list(), geo.regions() ]);
    geo.fillSelect($category, cats,   "-- Select service type --");
    geo.fillSelect($region,   regs,   "-- Region --");
    geo.fillSelect($district, [],     "-- District --");
  },

  async reloadDistricts(regionId, $district) {
    const items = await geo.districts(regionId || null);
    geo.fillSelect($district, items, "-- District --");
  },

  async loadRequest(reqId, refs) {
    dom.setText("#flash", `Loading #${reqId}...`);
    const it = await requests.get(reqId);

    refs.$title.value    = it.title || "";
    refs.$category.value = String(it.category_id || "");

    const s = dt.split(it.start_at);
    const e = dt.split(it.end_at);
    if (refs.$start_date && s.d) refs.$start_date.value = s.d;
    if (refs.$start_time && s.t) refs.$start_time.value = s.t;
    if (refs.$end_date   && e.d) refs.$end_date.value   = e.d;
    if (refs.$end_time   && e.t) refs.$end_time.value   = e.t;

    refs.$region.value = String(it.region_id || "");
    await pin.edit.reloadDistricts(it.region_id || null, refs.$district);
    refs.$district.value = String(it.district_id || "");

    refs.$desc.value = it.description || "";
    if (refs.$status) refs.$status.textContent = (it.computed_status || it.status || "").toString();
    dom.setText("#flash", "");
    return it;
  },

  async save(reqId, refs) {
    const title       = refs.$title.value.trim();
    const category_id = parseInt(refs.$category.value, 10);
    const district_id = parseInt(refs.$district.value, 10);
    const start_at    = dt.join(refs.$start_date.value, refs.$start_time.value);
    const end_at      = dt.join(refs.$end_date.value,   refs.$end_time.value);

    if (!title || !category_id || !district_id || !start_at || !end_at) {
      dom.setText("#flash", "Please fill all required fields.");
      return false;
    }

    const payload = { title, category_id, district_id, start_at, end_at, description: refs.$desc.value || "" };
    dom.setText("#flash", reqId ? "Saving..." : "Creating...");
    if (reqId) await requests.update(reqId, payload);
    else       await requests.create(payload);
    location.replace(url.withTs(`/pin${reqId ? `#req-${reqId}` : ""}`));
    return true;
  },

  async postalLookup($postal, $region, $district, $desc, $hintEl) {
    const postal = ($postal.value || "").trim();
    if (!postal) { if ($hintEl) $hintEl.textContent = "Please enter a postal code."; return; }
    try {
      if ($hintEl) $hintEl.textContent = "Looking up...";
      const res = await address.lookupPostal(postal);
      if (!res?.region_id) { if ($hintEl) $hintEl.textContent = "Invalid postal code."; return; }

      // set region → load districts → set district
      $region.value = String(res.region_id);
      await pin.edit.reloadDistricts(res.region_id, $district);
      $district.value = String(res.district_id || "");

      // upsert "Detailed address: ..."
      const addrLine = res.address_text || res.full_address || res.address || "";
      if (addrLine) {
        const marker = "Detailed address:";
        const lines = ( $desc.value || "" ).split(/\r?\n/);
        const idx = lines.findIndex(l => l.trim().toLowerCase().startsWith(marker.toLowerCase()));
        const newLine = `${marker} ${addrLine}`.trim();
        if (idx >= 0) lines[idx] = newLine; else lines.push(newLine);
        $desc.value = lines.join("\n").trim();
      }
      if ($hintEl) {
        const rd = [res.region_name, res.district_name].filter(Boolean).join(" · ");
        $hintEl.textContent = rd || "Address applied.";
      }
    } catch (e) {
      console.error(e);
      if ($hintEl) $hintEl.textContent = "Lookup failed.";
    }
  }
};

// --- export minimal namespace ---
window.utils = {
  // http
  get: _get, post: _post, put: _put, del: _del,
  // auth
  installAuthGuard, normalizeRole, redirectByRole,
  // small helpers
  escapeHtml, url, dt, dom,
  // domains used by the page
  categories, requests, geo, address,
  // pin/edit
  pin,
};
