// LabConnect JS
let allTests = [], cart = [], nearbyLabs = [];

async function loadTests() {
  const category = document.getElementById('filterCategory')?.value || '';
  const search = document.getElementById('searchTests')?.value || '';
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (search) params.append('search', search);

  const res = await apiCall('GET', `/api/lab/tests?${params}`);
  if (res.success) {
    allTests = res.data;
    renderTests(allTests);
  }
}

async function loadNearbyLabs() {
  const { lat, lng } = window.userLocation;
  const res = await apiCall('GET', `/api/location/nearby-labs?lat=${lat}&lng=${lng}`);
  if (res.success) {
    nearbyLabs = res.data;
    renderLabList(nearbyLabs);
  }
}

function renderLabList(labs) {
  const container = document.getElementById('labList');
  if (!container) return;
  if (!labs.length) { container.innerHTML = '<p style="color:var(--text-muted);font-size:13px">No labs found nearby.</p>'; return; }
  container.innerHTML = labs.map(lab => `
    <div style="padding:12px;border:1.5px solid var(--border);border-radius:var(--radius-sm);margin-bottom:10px;cursor:pointer;transition:all 0.18s" onclick="selectLab(${lab.id})" id="labitem-${lab.id}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div style="font-weight:800;font-size:14px">${lab.name}</div>
          <div style="font-size:12px;color:var(--text-muted)">${lab.accreditation} &bull; ${lab.distance_km ? lab.distance_km + ' km' : ''}</div>
        </div>
        ${lab.home_collection ? '<span style="background:#dcfce7;color:#166534;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:700">🏠 Home</span>' : ''}
      </div>
      <div style="margin-top:6px;font-size:12px;color:var(--text-muted)">
        ⏰ ${lab.timings} &nbsp;|&nbsp; Collection: ₹${lab.collection_charge}
      </div>
    </div>
  `).join('');
}

let selectedLabId = null;
function selectLab(labId) {
  selectedLabId = labId;
  document.querySelectorAll('[id^=labitem-]').forEach(el => el.style.borderColor = 'var(--border)');
  const el = document.getElementById(`labitem-${labId}`);
  if (el) { el.style.borderColor = 'var(--primary)'; el.style.background = '#f0fdf4'; }
  // Filter tests for this lab
  const filtered = allTests.filter(t => t.lab_id === labId);
  renderTests(filtered.length ? filtered : allTests);
}

function renderTests(tests) {
  const container = document.getElementById('testList');
  if (!container) return;
  const resultEl = document.getElementById('testResultCount');
  if (resultEl) resultEl.textContent = `${tests.length} tests found`;

  if (!tests.length) { container.innerHTML = '<div class="loading-overlay">No tests found.</div>'; return; }

  // Group by category
  const groups = {};
  tests.forEach(t => {
    if (!groups[t.category]) groups[t.category] = [];
    groups[t.category].push(t);
  });

  container.innerHTML = Object.entries(groups).map(([cat, items]) => `
    <div style="margin-bottom:20px">
      <div style="font-weight:800;font-size:13px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px">${cat}</div>
      ${items.map(t => testCardHTML(t)).join('')}
    </div>
  `).join('');
}

function testCardHTML(t) {
  const inCart = cart.some(c => c.id === t.id);
  return `
  <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:var(--surface);border:1.5px solid ${inCart ? 'var(--primary)' : 'var(--border)'};border-radius:var(--radius-sm);margin-bottom:8px;transition:all 0.18s" id="testcard-${t.id}">
    <div style="flex:1">
      <div style="font-weight:700;font-size:14px">${t.name}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:2px">
        🕐 Report in ${t.tat_hours}h &nbsp;|&nbsp; ${t.fasting ? '🚫 Fasting required' : '✅ No fasting'} &nbsp;|&nbsp; ${t.lab_name}
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;margin-left:16px">
      <div style="text-align:right">
        <div style="font-weight:900;font-size:16px;color:var(--primary)">₹${t.price}</div>
      </div>
      <button class="btn btn-sm ${inCart ? 'btn-danger' : 'btn-outline'}" onclick="${inCart ? 'removeFromCart' : 'addToCart'}(${t.id})">
        ${inCart ? 'Remove' : '+ Add'}
      </button>
    </div>
  </div>`;
}

function addToCart(testId) {
  const test = allTests.find(t => t.id === testId);
  if (!test || cart.some(c => c.id === testId)) return;
  cart.push(test);
  updateCart();
  loadTests(); // re-render
}

function removeFromCart(testId) {
  cart = cart.filter(c => c.id !== testId);
  updateCart();
  loadTests();
}

function updateCart() {
  const count = document.getElementById('cartCount');
  const total = document.getElementById('cartTotal');
  const cartItems = document.getElementById('cartItems');
  const cartBar = document.getElementById('cartBar');

  if (count) count.textContent = cart.length;
  const sum = cart.reduce((a, t) => a + t.price, 0);
  if (total) total.textContent = `₹${sum}`;

  if (cartItems) {
    if (!cart.length) { cartItems.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:8px 0">No tests added yet</div>'; }
    else {
      cartItems.innerHTML = cart.map(t => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border)">
          <div>
            <div style="font-weight:700;font-size:13px">${t.name}</div>
            <div style="font-size:11px;color:var(--text-muted)">${t.lab_name}</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-weight:800">₹${t.price}</span>
            <button onclick="removeFromCart(${t.id})" style="background:none;border:none;color:var(--red);font-size:16px;cursor:pointer">&times;</button>
          </div>
        </div>`).join('');
    }
  }

  if (cartBar) cartBar.style.display = cart.length ? 'flex' : 'none';
}

function openBookingModal() {
  if (!cart.length) { showToast('Please add at least one test', 'warning'); return; }
  const labId = cart[0].lab_id;
  document.getElementById('cartSummary').innerHTML = cart.map(t => `<div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0"><span>${t.name}</span><span>₹${t.price}</span></div>`).join('');
  const collection = nearbyLabs.find(l => l.id === labId)?.collection_charge || 50;
  const sub = cart.reduce((a,t) => a + t.price, 0);
  document.getElementById('cartSummaryTotal').textContent = `₹${sub + collection}`;
  generateSlots();
  openModal('bookingModal');
}

// Generate slot times
function generateSlots() {
  const date = document.getElementById('slotDate').value;
  if (!date) return;
  const slotEl = document.getElementById('slotTime');
  slotEl.innerHTML = '';
  const slots = ['6:00 AM', '7:00 AM', '8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', '2:00 PM', '3:00 PM', '4:00 PM', '5:00 PM', '6:00 PM'];
  slots.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s; opt.textContent = s;
    slotEl.appendChild(opt);
  });
}

async function submitLabBooking() {
  const patientName = document.getElementById('bookPatientName').value.trim();
  const patientPhone = document.getElementById('bookPatientPhone').value.trim();
  const address = document.getElementById('bookAddress').value.trim();
  const slotDate = document.getElementById('slotDate').value;
  const slotTime = document.getElementById('slotTime').value;

  if (!patientName || !patientPhone || !address || !slotDate || !slotTime) {
    showToast('Please fill all required fields', 'error'); return;
  }
  if (!cart.length) { showToast('Cart is empty', 'error'); return; }

  const labId = selectedLabId || cart[0].lab_id;
  const btn = document.getElementById('bookSubmitBtn');
  btn.textContent = 'Booking...'; btn.disabled = true;

  const res = await apiCall('POST', '/api/lab/book', {
    lab_id: labId,
    test_ids: cart.map(t => t.id),
    patient_name: patientName,
    patient_phone: patientPhone,
    address, slot_date: slotDate, slot_time: slotTime,
  });

  btn.textContent = 'Confirm Booking'; btn.disabled = false;

  if (res.success) {
    closeModal('bookingModal');
    document.getElementById('confirmBookingId').textContent = res.data.booking_id;
    document.getElementById('confirmTotal').textContent = `₹${res.data.total_amount}`;
    openModal('confirmModal');
    cart = [];
    updateCart();
  } else {
    showToast(res.message || 'Booking failed', 'error');
  }
}

// Set min date to today
document.addEventListener('DOMContentLoaded', async () => {
  const dateEl = document.getElementById('slotDate');
  if (dateEl) {
    const today = new Date().toISOString().split('T')[0];
    dateEl.min = today;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateEl.value = tomorrow.toISOString().split('T')[0];
    generateSlots();
  }

  document.getElementById('searchTests')?.addEventListener('input', loadTests);
  document.getElementById('filterCategory')?.addEventListener('change', loadTests);

  await loadNearbyLabs();
  await loadTests();
  updateCart();
});
