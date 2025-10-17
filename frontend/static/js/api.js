// frontend/static/js/api.js
(function () {
  // 로컬 Flask 서버 주소
  const API_BASE = 'http://127.0.0.1:5000/api';

  // GitHub Pages나 정적 서버(5500)에서 JSON으로 읽을 경로
  const STATIC_MAP = {
    '/accounts/':   'data/accounts.json',
    '/categories/': 'data/categories.json',
    '/requests/':   'data/requests.json',
  };

  async function fetchJson(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  // 자동으로 JSON 폴백 기능 포함
  async function apiGet(path) {
    const isStatic = location.hostname.endsWith('github.io') || location.port === '5500';
    if (isStatic) {
      // 정적 모드일 때는 data/*.json에서 바로 읽기
      return fetchJson(STATIC_MAP[path]);
    } else {
      // 로컬 개발 모드일 때 Flask API 사용
      return fetchJson(`${API_BASE}${path}`);
    }
  }

  // 페이지에서 사용할 함수
  window.apiGet = apiGet;

  window.apiJson = async function (path, method, bodyObj) {
    const r = await fetch(`${API_BASE}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyObj || {})
    });
    const txt = await r.text();
    let data = null; try { data = txt ? JSON.parse(txt) : null; } catch (e) {}
    if (!r.ok) throw new Error(data?.error || txt || 'request failed');
    return data;
  };
})();
