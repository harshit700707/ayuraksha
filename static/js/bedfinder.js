// BedFinder JS
let map, markers = [], allHospitals = [], selectedHospital = null;

const greenIcon = L.divIcon({ className: '', html: '<div style="background:#22c55e;width:14px;height:14px;border-radius:50%;border:2.5px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>' });
const yellowIcon = L.divIcon({ className: '', html: '<div style="background:#f97316;width:14px;height:14px;border-radius:50%;border:2.5px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>' });
const redIcon = L.divIcon({ className: '', html: '<div style="background:#ef4444;width:14px;height:14px;border-radius:50%;border:2.5px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>' });

function getMarkerIcon(h) {
  const total = h.icu_beds_total + h.general_beds_total + h.emergency_beds_total;
  const avail = h.icu_beds_available + h.general_beds_available + h.emergency_beds_available;
  if (!total) return redIcon;
  const pct = avail / total;
  if (pct > 0.3) return greenIcon;
  if (pct > 0) return yellowIcon;
  return redIcon;
}

async function loadHospitals() {
  const bedType = document.getElementById('filterBedType')?.value || '';
  const insurance = document.getElementById('filterInsurance')?.value || '';
  const specialty = document.getElementById('filterSpecialty')?.value || '';
  const radius = document.getElementById('filterRadius')?.value || 30;
  const { lat, lng } = window.userLocation;

  document.getElementById('hospitalList').innerHTML = '<div class="loading-overlay"><div class="spinner"></div><span>Finding hospitals near you...</span></div>';

  const params = new URLSearchParams({ lat, lng, radius });
  if (bedType) params.append('bed_type', bedType);
  if (insurance) params.append('insurance', insurance);
  if (specialty) params.append('specialty', specialty);

  const res = await apiCall('GET', `/api/hospital/search?${params}`);
  if (!res.success) { document.getElementById('hospitalList').innerHTML = '<div class="loading-overlay">No hospitals found.</div>'; return; }

  allHospitals = res.data;
  renderHospitals(allHospitals);
  plotMarkers(allHospitals);
}

function renderHospitals(hospitals) {
  const container = document.getElementById('hospitalList');
  if (!hospitals.length) {
    container.innerHTML = '<div class="loading-overlay">No hospitals found matching your filters.</div>';
    return;
  }
  container.innerHTML = hospitals.map(h => hospitalCardHTML(h)).join('');
}

function hospitalCardHTML(h) {
  const bedColor = (avail, total) => {
    if (!total) return 'none';
    const p = avail / total;
    return p > 0.4 ? 'high' : p > 0.1 ? 'medium' : avail > 0 ? 'low' : 'none';
  };
  const specs = (h.specialties || []).slice(0, 4).map(s => `<span class="tag">${s}</span>`).join('');
  const ins = (h.insurance_accepted || []).slice(0, 3).map(i => `<span class="tag" style="background:#dbeafe;color:#1e40af">${i}</span>`).join('');

  return `
  <div class="hospital-card" style="margin-bottom:14px" id="hcard-${h.id}">
    <div class="hospital-header">
      <div>
        <div class="hospital-name">${h.name}</div>
        <div style="font-size:13px;color:var(--text-muted);margin-top:2px">
          📍 ${h.address} &nbsp;|&nbsp; ${h.distance_km != null ? h.distance_km + ' km away' : ''}
        </div>
      </div>
      <span class="hospital-type-badge ${h.type === 'Government' ? 'badge-govt' : 'badge-private'}">${h.type}</span>
    </div>

    <div class="bed-grid">
      <div class="bed-item">
        <div class="bed-label">ICU Beds</div>
        <div class="bed-count ${bedColor(h.icu_beds_available, h.icu_beds_total)}">${h.icu_beds_available}<span style="font-size:12px;font-weight:500;color:var(--text-muted)">/${h.icu_beds_total}</span></div>
      </div>
      <div class="bed-item">
        <div class="bed-label">General</div>
        <div class="bed-count ${bedColor(h.general_beds_available, h.general_beds_total)}">${h.general_beds_available}<span style="font-size:12px;font-weight:500;color:var(--text-muted)">/${h.general_beds_total}</span></div>
      </div>
      <div class="bed-item">
        <div class="bed-label">Emergency</div>
        <div class="bed-count ${bedColor(h.emergency_beds_available, h.emergency_beds_total)}">${h.emergency_beds_available}<span style="font-size:12px;font-weight:500;color:var(--text-muted)">/${h.emergency_beds_total}</span></div>
      </div>
      <div class="bed-item">
        <div class="bed-label">Maternity</div>
        <div class="bed-count ${bedColor(h.maternity_beds_available, h.maternity_beds_total)}">${h.maternity_beds_available}<span style="font-size:12px;font-weight:500;color:var(--text-muted)">/${h.maternity_beds_total}</span></div>
      </div>
    </div>

    <div class="rating-row">
      <span class="stars">${renderStars(h.rating)}</span>
      <span class="rating-num">${h.rating.toFixed(1)}</span>
      <span class="review-count">(${h.total_reviews} reviews)</span>
    </div>

    <div class="tag-list">${specs}${ins}</div>

    <div class="card-actions">
      <button class="btn btn-primary btn-sm" onclick="openBookingModal(${JSON.stringify(h).replace(/"/g,'&quot;')})">Book Bed</button>
      <a href="https://maps.google.com/?q=${h.lat},${h.lng}" target="_blank" class="btn btn-outline btn-sm">Get Directions</a>
    </div>
  </div>`;
}

function plotMarkers(hospitals) {
  markers.forEach(m => map.removeLayer(m));
  markers = [];
  hospitals.forEach(h => {
    if (!h.lat || !h.lng) return;
    const icon = getMarkerIcon(h);
    const m = L.marker([h.lat, h.lng], { icon })
      .addTo(map)
      .bindPopup(`<strong>${h.name}</strong><br>ICU: ${h.icu_beds_available}/${h.icu_beds_total} | General: ${h.general_beds_available}/${h.general_beds_total}`);
    m.on('click', () => { document.getElementById(`hcard-${h.id}`)?.scrollIntoView({ behavior: 'smooth' }); });
    markers.push(m);
  });
  if (markers.length) {
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
}

// Booking Modal
let bookingHospital = null;
function openBookingModal(h) {
  bookingHospital = h;
  document.getElementById('bookHospitalName').textContent = h.name;
  openModal('bookingModal');
}

async function submitBedBooking() {
  const bedType = document.getElementById('bookBedType').value;
  const patientName = document.getElementById('bookPatientName').value.trim();
  const patientPhone = document.getElementById('bookPatientPhone').value.trim();
  const patientAge = document.getElementById('bookPatientAge').value;
  const diagnosis = document.getElementById('bookDiagnosis').value.trim();
  const insurance = document.getElementById('bookInsurance').value;

  if (!patientName || !patientPhone || !patientAge) { showToast('Please fill all required fields', 'error'); return; }

  const btn = document.getElementById('bookSubmitBtn');
  btn.textContent = 'Booking...'; btn.disabled = true;

  const res = await apiCall('POST', '/api/hospital/bed/book', {
    hospital_id: bookingHospital.id, bed_type: bedType,
    patient_name: patientName, patient_phone: patientPhone,
    patient_age: parseInt(patientAge), diagnosis, insurance_type: insurance,
  });

  btn.textContent = 'Confirm Booking'; btn.disabled = false;

  if (res.success) {
    closeModal('bookingModal');
    document.getElementById('confirmBookingId').textContent = res.data.booking_id;
    openModal('confirmModal');
    loadHospitals(); // refresh bed counts
  } else {
    showToast(res.message || 'Booking failed', 'error');
  }
}

// Emergency ICU search
async function findNearestICU() {
  const { lat, lng } = window.userLocation;
  const res = await apiCall('GET', `/api/hospital/search?lat=${lat}&lng=${lng}&bed_type=icu&radius=50`);
  if (res.success && res.data.length) {
    const top3 = res.data.slice(0, 3);
    alert('Nearest ICU Hospitals:\n\n' + top3.map((h, i) => `${i+1}. ${h.name}\n   ICU beds: ${h.icu_beds_available}/${h.icu_beds_total}\n   Distance: ${h.distance_km} km\n   Phone: ${h.phone}`).join('\n\n'));
  } else {
    showToast('No ICU beds available nearby', 'error');
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  // Init map
  map = L.map('map').setView([26.9270, 81.1989], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // User location marker
  const userMarker = L.divIcon({ className: '', html: '<div style="background:#0a6e5c;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4)"></div>' });
  L.marker([window.userLocation.lat, window.userLocation.lng], { icon: userMarker })
    .addTo(map).bindPopup('Your location');

  // Filter change listeners
  ['filterBedType', 'filterInsurance', 'filterSpecialty', 'filterRadius'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', loadHospitals);
  });

  await loadHospitals();
});
