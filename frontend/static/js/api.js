<script>
  // API 기본 URL (필요시 127.0.0.1 대신 다른 호스트/포트로 변경)
  const API_BASE = 'http://127.0.0.1:5000/api';

  async function apiGet(path) {
    const r = await fetch(`${API_BASE}${path}`);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
  async function apiJson(path, method, bodyObj) {
    const r = await fetch(`${API_BASE}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyObj || {})
    });
    const txt = await r.text();
    let data = null; try { data = txt ? JSON.parse(txt) : null; } catch(e) {}
    if (!r.ok) throw new Error(data?.error || txt || 'request failed');
    return data;
  }
</script>
