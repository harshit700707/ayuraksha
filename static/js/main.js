// ── AyuRaksha — Main JS ──
const API = '';

// Auth helpers
const Auth = {
  getToken: () => localStorage.getItem('ar_token'),
  setToken: (t) => localStorage.setItem('ar_token', t),
  getRole: () => localStorage.getItem('ar_role'),
  setRole: (r) => localStorage.setItem('ar_role', r),
  getUser: () => { try { return JSON.parse(localStorage.getItem('ar_user')); } catch { return null; } },
  setUser: (u) => localStorage.setItem('ar_user', JSON.stringify(u)),
  logout: () => { localStorage.removeItem('ar_token'); localStorage.removeItem('ar_role'); localStorage.removeItem('ar_user'); window.location = '/'; },
  isLoggedIn: () => !!localStorage.getItem('ar_token'),
};

// API helper
async function apiCall(method, url, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  const token = Auth.getToken();
  if (token) opts.headers['Authorization'] = `Bearer ${token}`;
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  return res.json();
}

// Location detection
window.userLocation = { lat: 26.9270, lng: 81.1989, city: 'Barabanki' };

async function detectAndSetLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ lat: 26.9270, lng: 81.1989, city: 'Barabanki' });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`, {
            headers: { 'User-Agent': 'AyuRaksha/2.0' }
          });
          const data = await res.json();
          const addr = data.address || {};
          const city = addr.city || addr.town || addr.village || 'Barabanki';
          resolve({ lat, lng, city });
        } catch {
          resolve({ lat, lng, city: 'Barabanki' });
        }
      },
      () => resolve({ lat: 26.9270, lng: 81.1989, city: 'Barabanki' }),
      { timeout: 6000 }
    );
  });
}

// Toast notifications
function showToast(msg, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;min-width:280px;animation:slideUp 0.3s ease;box-shadow:0 4px 20px rgba(0,0,0,0.15)';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// Format currency
function formatCurrency(n) { return '₹' + Number(n).toLocaleString('en-IN'); }

// Bed color class
function bedColorClass(available, total) {
  if (!total) return 'none';
  const pct = available / total;
  if (pct > 0.4) return 'high';
  if (pct > 0.1) return 'medium';
  if (available > 0) return 'low';
  return 'none';
}

// Stars
function renderStars(rating) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  let s = '';
  for (let i = 0; i < full; i++) s += '★';
  if (half) s += '☆';
  return s;
}

// Distance string
function distStr(km) {
  if (!km && km !== 0) return '';
  if (km < 1) return `${Math.round(km * 1000)}m`;
  return `${km.toFixed(1)} km`;
}

// Modal helpers
function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// GST validator (frontend)
function validateGST(gst) {
  const pattern = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
  return gst && gst.length === 15 && pattern.test(gst.toUpperCase());
}

// Load platform stats
async function loadPlatformStats() {
  try {
    const res = await apiCall('GET', '/api/stats');
    if (res.success) {
      const d = res.data;
      const el = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
      el('stat-hospitals', d.hospitals);
      el('stat-labs', d.labs);
      el('stat-ambulances', d.ambulances);
    }
  } catch (e) { /* silent */ }
}

// On page load
document.addEventListener('DOMContentLoaded', async () => {
  // Detect location
  window.userLocation = await detectAndSetLocation();
  const locEl = document.getElementById('locationDisplay');
  if (locEl) locEl.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg> ${window.userLocation.city}`;

  // Update login button
  const loginBtn = document.getElementById('loginBtn');
  if (loginBtn && Auth.isLoggedIn()) {
    loginBtn.textContent = 'My Account';
    loginBtn.href = `/${Auth.getRole()}/dashboard`;
  }

  // Load stats if on home
  loadPlatformStats();

  // Mark active nav
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });
});
