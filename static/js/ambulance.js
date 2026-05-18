// Ambulance JS
let map, userMarker, ambulanceMarkers = [], trackInterval = null;
let selectedAmbType = 'Basic', selectedAmb = null, pickupLatLng = null;

const AMB_ICONS = { Basic: '🚑', ALS: '🏥', Neonatal: '👶' };

document.addEventListener('DOMContentLoaded', async () => {
  map = L.map('ambulance-map').setView([window.userLocation.lat, window.userLocation.lng], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // User location
  pickupLatLng = { lat: window.userLocation.lat, lng: window.userLocation.lng };
  const uIcon = L.divIcon({ className: '', html: '<div style="background:#0a6e5c;width:18px;height:18px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4)"></div>' });
  userMarker = L.marker([pickupLatLng.lat, pickupLatLng.lng], { icon: uIcon, draggable: true })
    .addTo(map)
    .bindPopup('📍 Your pickup location<br><small>Drag to adjust</small>')
    .openPopup();

  userMarker.on('dragend', (e) => {
    const pos = e.target.getLatLng();
    pickupLatLng = { lat: pos.lat, lng: pos.lng };
    reverseGeocode(pos.lat, pos.lng).then(addr => {
      document.getElementById('pickupAddress').textContent = addr;
    });
    loadNearbyAmbulances();
  });

  // Ripple animation
  addRipple(pickupLatLng.lat, pickupLatLng.lng);

  await loadNearbyAmbulances();
});

function addRipple(lat, lng) {
  const rippleHtml = `<div style="width:40px;height:40px;border-radius:50%;border:2px solid #0a6e5c;animation:ripple 1.5s infinite;opacity:0.6"></div>`;
  L.marker([lat, lng], {
    icon: L.divIcon({ className: '', html: rippleHtml, iconSize: [40, 40], iconAnchor: [20, 20] })
  }).addTo(map);
}

async function reverseGeocode(lat, lng) {
  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`, {
      headers: { 'User-Agent': 'AyuRaksha/2.0' }
    });
    const data = await res.json();
    return data.display_name?.split(',').slice(0, 3).join(', ') || 'Your location';
  } catch { return 'Your location'; }
}

async function loadNearbyAmbulances() {
  const { lat, lng } = pickupLatLng;
  const res = await apiCall('GET', `/api/ambulance/nearby?lat=${lat}&lng=${lng}&type=${selectedAmbType === 'All' ? '' : selectedAmbType}`);
  if (!res.success) return;

  ambulanceMarkers.forEach(m => map.removeLayer(m));
  ambulanceMarkers = [];

  const ambulances = res.data;
  const container = document.getElementById('ambList');
  if (!ambulances.length) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted)">No ambulances available nearby right now.</div>';
    return;
  }

  ambulances.forEach(amb => {
    if (!amb.lat || !amb.lng) return;
    const icon = L.divIcon({
      className: '',
      html: `<div style="background:${amb.type==='ALS'?'#1e40af':amb.type==='Neonatal'?'#7c3aed':'#0a6e5c'};color:white;border-radius:8px;padding:4px 8px;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.3)">${AMB_ICONS[amb.type]||'🚑'} ${amb.eta_min}min</div>`,
      iconAnchor: [30, 15]
    });
    const m = L.marker([amb.lat, amb.lng], { icon }).addTo(map);
    m.bindPopup(`<strong>${amb.driver_name}</strong><br>${amb.vehicle_no}<br>ETA: ${amb.eta_min} min<br>₹${amb.base_fare} base`);
    m.on('click', () => selectAmbulance(amb));
    ambulanceMarkers.push(m);
  });

  container.innerHTML = ambulances.map(amb => `
    <div class="patient-row" id="amb-${amb.id}" onclick="selectAmbulance(${JSON.stringify(amb).replace(/"/g,'&quot;')})">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div style="font-weight:800">${AMB_ICONS[amb.type]||'🚑'} ${amb.type} Ambulance</div>
          <div style="font-size:12px;color:var(--text-muted)">${amb.driver_name} &bull; ${amb.vehicle_no}</div>
        </div>
        <div style="text-align:right">
          <div style="font-weight:900;color:var(--primary);font-size:16px">${amb.eta_min} min</div>
          <div style="font-size:11px;color:var(--text-muted)">${amb.distance_km} km</div>
        </div>
      </div>
      <div style="margin-top:6px;display:flex;gap:12px;font-size:12px;color:var(--text-muted)">
        <span>⭐ ${amb.rating}</span>
        <span>🏁 ${amb.total_trips} trips</span>
        <span>₹${amb.base_fare} + ₹${amb.per_km_fare}/km</span>
      </div>
    </div>`).join('');
}

function selectAmbType(type) {
  selectedAmbType = type;
  document.querySelectorAll('.amb-type-btn').forEach(b => b.classList.remove('selected'));
  document.querySelector(`[data-type="${type}"]`)?.classList.add('selected');
  loadNearbyAmbulances();
}

function selectAmbulance(amb) {
  selectedAmb = amb;
  document.querySelectorAll('.patient-row').forEach(r => r.classList.remove('selected'));
  document.getElementById(`amb-${amb.id}`)?.classList.add('selected');
  map.setView([amb.lat, amb.lng], 15);
  document.getElementById('bookBtn')?.removeAttribute('disabled');
}

function openBookModal() {
  if (!selectedAmb) { showToast('Please select an ambulance first', 'warning'); return; }
  document.getElementById('selectedAmbInfo').textContent = `${AMB_ICONS[selectedAmb.type]||'🚑'} ${selectedAmb.type} — ${selectedAmb.driver_name} — ${selectedAmb.vehicle_no}`;
  openModal('bookModal');
}

async function submitAmbBooking() {
  const patientName = document.getElementById('ambPatientName').value.trim();
  const patientPhone = document.getElementById('ambPatientPhone').value.trim();
  const destAddress = document.getElementById('destAddress').value.trim();
  const paymentMethod = document.getElementById('paymentMethod').value;

  if (!patientName || !patientPhone) { showToast('Please fill patient details', 'error'); return; }

  const btn = document.getElementById('ambBookBtn');
  btn.textContent = 'Booking...'; btn.disabled = true;

  const res = await apiCall('POST', '/api/ambulance/book', {
    ambulance_id: selectedAmb.id,
    patient_name: patientName,
    patient_phone: patientPhone,
    pickup_lat: pickupLatLng.lat,
    pickup_lng: pickupLatLng.lng,
    pickup_address: document.getElementById('pickupAddress').textContent || 'Your location',
    dest_address: destAddress,
    amb_type: selectedAmb.type,
    payment_method: paymentMethod,
  });

  btn.textContent = 'Confirm Booking'; btn.disabled = false;

  if (res.success) {
    closeModal('bookModal');
    showTrackingPanel(res.data);
  } else {
    showToast(res.message || 'Booking failed', 'error');
  }
}

function showTrackingPanel(booking) {
  document.getElementById('bottomSheet').innerHTML = `
    <div class="driver-card">
      <div style="font-size:12px;font-weight:700;opacity:0.7;margin-bottom:8px">AMBULANCE DISPATCHED</div>
      <div class="driver-header">
        <div class="driver-avatar">🚑</div>
        <div>
          <div class="driver-name">${booking.driver_name}</div>
          <div class="driver-meta">${booking.vehicle_no} &bull; ${booking.amb_type}</div>
        </div>
        <a href="tel:${booking.driver_phone}" class="btn btn-sm btn-success" style="margin-left:auto">📞 Call</a>
      </div>
      <div class="eta-display" id="liveEta">${booking.eta_min} min</div>
      <div class="eta-label">Estimated Time of Arrival</div>
      <div style="margin-top:12px;display:flex;justify-content:space-between;font-size:13px;opacity:0.85">
        <span>Booking: <strong>${booking.booking_id}</strong></span>
        <span>Fare: <strong>₹${booking.total_fare}</strong></span>
      </div>
    </div>`;

  // Live tracking simulation
  let eta = booking.eta_min;
  trackInterval = setInterval(() => {
    if (eta > 0) eta--;
    const etaEl = document.getElementById('liveEta');
    if (etaEl) etaEl.textContent = `${eta} min`;
    if (eta === 0) { clearInterval(trackInterval); if (etaEl) etaEl.textContent = 'Arrived!'; }
  }, 30000);
}

// Fare estimator
async function estimateFare() {
  const { lat, lng } = pickupLatLng;
  const destLat = 26.9310; const destLng = 81.2050; // default District Hospital
  const res = await apiCall('POST', '/api/ambulance/fare-estimate', {
    pickup_lat: lat, pickup_lng: lng,
    dest_lat: destLat, dest_lng: destLng,
    type: selectedAmbType,
  });
  if (res.success) {
    showToast(`Estimated fare: ₹${res.data.total_fare} (${res.data.distance_km} km)`, 'info');
  }
}
