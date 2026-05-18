// Register JS — Hospital & Lab
let currentStep = 1;
const totalSteps = 4;
let selectedSpecialties = [];
let selectedInsurance = [];
let userLatLng = null;

function goToStep(step) {
  if (step < 1 || step > totalSteps) return;
  document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.wizard-step-dot').forEach((d, i) => {
    d.classList.remove('active', 'done');
    if (i + 1 < step) d.classList.add('done');
    else if (i + 1 === step) d.classList.add('active');
  });
  document.querySelectorAll('.wizard-connector').forEach((c, i) => {
    c.classList.toggle('done', i + 1 < step);
  });
  document.getElementById(`step${step}`)?.classList.add('active');
  currentStep = step;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function nextStep() { validateAndNext(); }
function prevStep() { goToStep(currentStep - 1); }

function validateAndNext() {
  const step = currentStep;

  if (step === 1) {
    const gst = document.getElementById('gst_number')?.value.trim().toUpperCase() || '';
    const reg = document.getElementById('registration_no')?.value.trim() || '';
    const name = document.getElementById('name')?.value.trim() || '';
    if (!name) { showToast('Hospital/Lab name required', 'error'); return; }
    if (!reg) { showToast('Registration number required', 'error'); return; }
    if (!validateGST(gst)) { showToast('Invalid GST number. Format: 09AABCU9603R1ZX', 'error'); return; }
  }

  if (step === 2) {
    const phone = document.getElementById('phone')?.value.trim() || '';
    const contact = document.getElementById('contact_person')?.value.trim() || '';
    if (!contact) { showToast('Contact person name required', 'error'); return; }
    if (!/^[6-9][0-9]{9}$/.test(phone)) { showToast('Invalid phone number', 'error'); return; }
  }

  if (step === 4) {
    const pass = document.getElementById('password')?.value || '';
    const conf = document.getElementById('confirm_password')?.value || '';
    if (pass.length < 8) { showToast('Password must be at least 8 characters', 'error'); return; }
    if (pass !== conf) { showToast('Passwords do not match', 'error'); return; }
  }

  goToStep(step + 1);
}

// Real-time GST validation
function onGSTInput() {
  const gst = document.getElementById('gst_number')?.value.trim().toUpperCase() || '';
  const msgEl = document.getElementById('gstMsg');
  const inputEl = document.getElementById('gst_number');
  if (!gst) { msgEl && (msgEl.textContent = ''); return; }
  if (validateGST(gst)) {
    inputEl?.classList.add('field-valid'); inputEl?.classList.remove('field-invalid');
    msgEl && (msgEl.textContent = '✓ Valid GST format');
    msgEl && (msgEl.className = 'field-msg msg-valid');
    // Extract state code
    const stateCodes = { '09': 'Uttar Pradesh', '27': 'Maharashtra', '07': 'Delhi', '19': 'West Bengal' };
    const code = gst.substring(0, 2);
    if (stateCodes[code]) { msgEl && (msgEl.textContent += ` | State: ${stateCodes[code]}`); }
  } else {
    inputEl?.classList.remove('field-valid'); inputEl?.classList.add('field-invalid');
    msgEl && (msgEl.textContent = gst.length < 15 ? `${gst.length}/15 characters` : '✗ Invalid format. Example: 09AABCU9603R1ZX');
    msgEl && (msgEl.className = 'field-msg msg-invalid');
  }
}

// Toggle specialty
function toggleSpecialty(val) {
  const idx = selectedSpecialties.indexOf(val);
  if (idx > -1) selectedSpecialties.splice(idx, 1);
  else selectedSpecialties.push(val);
  document.querySelectorAll('.spec-check').forEach(el => {
    const checkbox = el.querySelector('input');
    el.classList.toggle('checked', selectedSpecialties.includes(checkbox?.value));
  });
}

// Toggle insurance
function toggleInsurance(val) {
  const idx = selectedInsurance.indexOf(val);
  if (idx > -1) selectedInsurance.splice(idx, 1);
  else selectedInsurance.push(val);
  document.querySelectorAll('.ins-check').forEach(el => {
    const checkbox = el.querySelector('input');
    el.classList.toggle('checked', selectedInsurance.includes(checkbox?.value));
  });
}

// Detect GPS
async function detectGPS() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) { resolve(null); return; }
    navigator.geolocation.getCurrentPosition(
      pos => {
        userLatLng = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        document.getElementById('latDisplay') && (document.getElementById('latDisplay').textContent = userLatLng.lat.toFixed(6));
        document.getElementById('lngDisplay') && (document.getElementById('lngDisplay').textContent = userLatLng.lng.toFixed(6));
        document.getElementById('gpsStatus') && (document.getElementById('gpsStatus').textContent = '✓ Location detected');
        document.getElementById('gpsStatus') && (document.getElementById('gpsStatus').style.color = 'var(--green)');
        resolve(userLatLng);
      },
      () => resolve(null),
      { timeout: 8000 }
    );
  });
}

// Submit hospital registration
async function submitHospitalRegistration() {
  const form = {
    name: document.getElementById('name')?.value.trim(),
    type: document.getElementById('type')?.value,
    registration_no: document.getElementById('registration_no')?.value.trim(),
    gst_number: document.getElementById('gst_number')?.value.trim().toUpperCase(),
    contact_person: document.getElementById('contact_person')?.value.trim(),
    phone: document.getElementById('phone')?.value.trim(),
    email: document.getElementById('email')?.value.trim(),
    password: document.getElementById('password')?.value,
    address: document.getElementById('address')?.value.trim(),
    city: document.getElementById('city')?.value.trim() || 'Barabanki',
    state: 'Uttar Pradesh',
    pincode: document.getElementById('pincode')?.value.trim(),
    lat: userLatLng?.lat,
    lng: userLatLng?.lng,
    specialties: selectedSpecialties,
    insurance_accepted: selectedInsurance,
    icu_beds_total: parseInt(document.getElementById('icu_beds')?.value) || 0,
    general_beds_total: parseInt(document.getElementById('general_beds')?.value) || 0,
    emergency_beds_total: parseInt(document.getElementById('emergency_beds')?.value) || 0,
    maternity_beds_total: parseInt(document.getElementById('maternity_beds')?.value) || 0,
  };

  const btn = document.getElementById('submitBtn');
  btn.textContent = 'Submitting...'; btn.disabled = true;

  const res = await apiCall('POST', '/api/hospital/register', form);
  btn.textContent = 'Submit Registration'; btn.disabled = false;

  if (res.success) {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('successScreen').style.display = 'block';
  } else {
    showToast(res.message || 'Registration failed. Please check all fields.', 'error');
  }
}

// Submit lab registration
async function submitLabRegistration() {
  const form = {
    name: document.getElementById('name')?.value.trim(),
    accreditation: document.getElementById('accreditation')?.value,
    registration_no: document.getElementById('registration_no')?.value.trim(),
    gst_number: document.getElementById('gst_number')?.value.trim().toUpperCase(),
    contact_person: document.getElementById('contact_person')?.value.trim(),
    phone: document.getElementById('phone')?.value.trim(),
    email: document.getElementById('email')?.value.trim(),
    password: document.getElementById('password')?.value,
    address: document.getElementById('address')?.value.trim(),
    city: document.getElementById('city')?.value.trim() || 'Barabanki',
    pincode: document.getElementById('pincode')?.value.trim(),
    lat: userLatLng?.lat,
    lng: userLatLng?.lng,
    home_collection: document.getElementById('home_collection')?.checked || false,
    collection_charge: parseInt(document.getElementById('collection_charge')?.value) || 50,
    coverage_radius_km: parseInt(document.getElementById('coverage_radius')?.value) || 10,
    timings: document.getElementById('timings')?.value.trim(),
  };

  const btn = document.getElementById('submitBtn');
  btn.textContent = 'Submitting...'; btn.disabled = true;

  const res = await apiCall('POST', '/api/lab/register', form);
  btn.textContent = 'Submit Registration'; btn.disabled = false;

  if (res.success) {
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('successScreen').style.display = 'block';
  } else {
    showToast(res.message || 'Registration failed. Please check all fields.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  goToStep(1);
  detectGPS();
});
