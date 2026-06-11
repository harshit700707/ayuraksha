// Ambulance JS
let map, userMarker, ambulanceMarkers = [], trackInterval = null;
let selectedAmbType = 'Basic', selectedAmb = null, pickupLatLng = null;
let trackingAmbMarker = null, trackingUserMarker = null;

const AMB_ICONS = { Basic: '🚑', ALS: '🏥', Neonatal: '👶' };

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const bookingId = urlParams.get('booking_id');

  if (bookingId) {
    // Initialize map for tracking
    map = L.map('ambulance-map').setView([26.9270, 81.1989], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    await loadBookingTracking(bookingId);
    return;
  }

  // Normal flow
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
    // Save booking_id to url and reload in tracking mode
    window.location.search = `?booking_id=${res.data.booking_id}`;
  } else {
    showToast(res.message || 'Booking failed', 'error');
  }
}

async function loadBookingTracking(bookingId) {
  const res = await apiCall('GET', `/api/ambulance/${bookingId}/track`);
  if (!res.success) {
    showToast('Failed to load tracking details.', 'error');
    setTimeout(() => { window.location.href = '/ambulance'; }, 3000);
    return;
  }

  const data = res.data;

  // Set up patient location marker
  const uIcon = L.divIcon({ className: '', html: '<div style="background:#0a6e5c;width:18px;height:18px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4)"></div>' });
  trackingUserMarker = L.marker([data.pickup_lat, data.pickup_lng], { icon: uIcon })
    .addTo(map)
    .bindPopup('📍 Your location')
    .openPopup();

  // Set up ambulance marker
  const ambIcon = L.divIcon({
    className: '',
    html: `<div style="background:#ef4444;color:white;border-radius:8px;padding:4px 8px;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.3)">🚑 Driver En Route</div>`,
    iconAnchor: [45, 15]
  });
  trackingAmbMarker = L.marker([data.current_lat, data.current_lng], { icon: ambIcon }).addTo(map);

  // Fit bounds to show both markers
  const group = new L.featureGroup([trackingUserMarker, trackingAmbMarker]);
  map.fitBounds(group.getBounds().pad(0.25));

  showTrackingPanel(data);
  startLiveTracking(bookingId);
}

function startLiveTracking(bookingId) {
  if (trackInterval) clearInterval(trackInterval);

  trackInterval = setInterval(async () => {
    const res = await apiCall('GET', `/api/ambulance/${bookingId}/track`);
    if (res.success) {
      const data = res.data;

      // Move ambulance marker
      if (trackingAmbMarker) {
        trackingAmbMarker.setLatLng([data.current_lat, data.current_lng]);
      }

      // Update ETA
      const etaEl = document.getElementById('liveEta');
      if (etaEl) {
        etaEl.textContent = `${data.eta_min} min`;
      }

      if (data.status === 'Completed' || data.eta_min <= 0) {
        clearInterval(trackInterval);
        if (etaEl) etaEl.textContent = 'Arrived!';
        showToast('Ambulance has arrived!', 'success');
      }
    }
  }, 5000);
}

function showTrackingPanel(booking) {
  // Hide standard booking controls
  const controls = document.getElementById('bookingControls');
  if (controls) controls.style.display = 'none';

  document.getElementById('bottomSheet').innerHTML = `
    <div class="driver-card">
      <div style="font-size:12px;font-weight:700;color:var(--accent);margin-bottom:8px;display:flex;align-items:center;gap:6px">
        <span class="pulse-dot" style="background:var(--accent);width:8px;height:8px"></span> AMBULANCE DISPATCHED (LIVE)
      </div>
      <div class="driver-header" style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <div class="driver-avatar" style="font-size:28px">🚑</div>
        <div>
          <div class="driver-name" style="font-weight:800;font-size:15px">${booking.driver_name || 'Driver'}</div>
          <div class="driver-meta" style="font-size:12px;color:var(--text-muted)">${booking.vehicle_no || ''} &bull; ${booking.amb_type || 'Basic'}</div>
        </div>
        <a href="tel:${booking.driver_phone}" class="btn btn-sm btn-success" style="margin-left:auto;border-radius:20px;padding:6px 14px">📞 Call Driver</a>
      </div>
      <div class="eta-container" style="background:var(--surface2);border-radius:var(--radius-sm);padding:14px;text-align:center;margin-bottom:12px">
        <div class="eta-display" id="liveEta" style="font-size:32px;font-weight:900;color:var(--primary)">${booking.eta_min} min</div>
        <div class="eta-label" style="font-size:12px;color:var(--text-muted);font-weight:700">Estimated Time of Arrival</div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:12.5px;color:var(--text-muted);padding-top:8px;border-top:1px solid var(--border)">
        <span>Booking ID: <strong>${booking.booking_id}</strong></span>
        <span>Est. Fare: <strong>₹${booking.total_fare || '300'}</strong></span>
      </div>
      <a href="tel:112" class="btn btn-outline btn-sm btn-block" style="margin-top:12px;border-color:var(--accent);color:var(--accent);border-radius:8px">🚨 Call 112 for Police/Fire</a>
    </div>`;
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

