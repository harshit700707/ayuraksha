// ICU Guard JS
let selectedPatient = null, vitalsChart = null;

async function loadPatients() {
  const token = Auth.getToken();
  if (!token) { window.location = '/hospital/dashboard'; return; }
  const res = await apiCall('GET', '/api/icu/patients');
  if (res.success) renderPatientList(res.data);
}

async function loadStats() {
  const res = await apiCall('GET', '/api/icu/stats');
  if (!res.success) return;
  const d = res.data;
  setText('statTotal', d.total_patients);
  setText('statCritical', d.critical);
  setText('statModerate', d.moderate);
  setText('statStable', d.stable);
  setText('statAlerts', d.alerts_today);
}

function setText(id, val) { const e = document.getElementById(id); if (e) e.textContent = val; }

function renderPatientList(patients) {
  const container = document.getElementById('patientList');
  if (!patients.length) {
    container.innerHTML = '<div style="padding:20px;color:var(--text-muted);font-size:13px;text-align:center">No ICU patients added yet</div>';
    return;
  }
  container.innerHTML = patients.map(p => `
    <div class="patient-row ${p.status}-row ${selectedPatient?.id === p.id ? 'selected' : ''}" onclick="selectPatient(${JSON.stringify(p).replace(/"/g,'&quot;')})">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div class="patient-name-sm">${p.patient_name}</div>
          <div class="patient-meta">Bed ${p.bed_number} &bull; ${p.age}y ${p.gender}</div>
        </div>
        <span class="risk-indicator risk-${p.status}">${p.risk_score}%</span>
      </div>
      <div style="font-size:11px;color:var(--text-muted);margin-top:4px">${p.diagnosis}</div>
    </div>`).join('');
}

async function selectPatient(p) {
  selectedPatient = p;
  renderPatientList((await apiCall('GET', '/api/icu/patients')).data || []);
  document.getElementById('detailPanel').style.display = 'block';
  document.getElementById('emptyDetail').style.display = 'none';

  document.getElementById('detailName').textContent = p.patient_name;
  document.getElementById('detailBed').textContent = `Bed ${p.bed_number}`;
  document.getElementById('detailMeta').textContent = `${p.age}y ${p.gender} | ${p.diagnosis}`;
  document.getElementById('detailDoctor').textContent = p.doctor_name;
  document.getElementById('detailRisk').className = `risk-indicator risk-${p.status}`;
  document.getElementById('detailRisk').textContent = `${p.risk_score}% Risk`;

  // Set patient_id in vitals form
  document.getElementById('vitalPatientId').value = p.id;

  // Load vitals history
  await loadVitalsHistory(p.id);
  await loadAlerts(p.id);
}

async function loadVitalsHistory(patientId) {
  const res = await apiCall('GET', `/api/icu/patient/${patientId}/vitals-history`);
  if (!res.success || !res.data.length) return;
  const vitals = res.data;

  // Render chart
  const labels = vitals.map(v => new Date(v.recorded_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
  const hrData = vitals.map(v => v.heart_rate);
  const riskData = vitals.map(v => v.risk_score);
  const spo2Data = vitals.map(v => v.spo2);

  const ctx = document.getElementById('vitalsChart')?.getContext('2d');
  if (!ctx) return;

  if (vitalsChart) vitalsChart.destroy();

  if (window.Chart) {
    vitalsChart = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Heart Rate', data: hrData, borderColor: '#ef4444', tension: 0.4, fill: false },
          { label: 'Risk Score', data: riskData, borderColor: '#f97316', tension: 0.4, fill: false },
          { label: 'SpO2', data: spo2Data, borderColor: '#22c55e', tension: 0.4, fill: false },
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: true } },
        scales: { y: { min: 0, max: 200 } }
      }
    });
  }

  // Latest vitals display
  const latest = vitals[vitals.length - 1];
  if (latest) {
    setText('vHR', latest.heart_rate);
    setText('vBP', `${latest.systolic_bp}/${latest.diastolic_bp}`);
    setText('vTemp', latest.temperature?.toFixed(1));
    setText('vRR', latest.respiratory_rate);
    setText('vSpO2', latest.spo2);
    setText('vGCS', latest.gcs);
  }
}

async function loadAlerts(patientId) {
  const res = await apiCall('GET', '/api/icu/alerts');
  if (!res.success) return;
  const alerts = res.data.filter(a => a.patient_id === patientId).slice(0, 5);
  const container = document.getElementById('alertList');
  if (!container) return;
  if (!alerts.length) { container.innerHTML = '<div style="font-size:13px;color:var(--text-muted);padding:8px 0">No alerts yet</div>'; return; }
  container.innerHTML = alerts.map(a => `
    <div style="padding:10px;border-radius:var(--radius-sm);margin-bottom:8px;background:${a.risk_score >= 70 ? '#fee2e2' : '#fef3c7'};border-left:3px solid ${a.risk_score >= 70 ? 'var(--red)' : 'var(--orange)'}">
      <div style="font-weight:800;font-size:13px">${a.alert_type} — Score: ${a.risk_score}/100</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${a.message}</div>
      <div style="font-size:11px;color:var(--text-muted);margin-top:4px">${new Date(a.created_at).toLocaleString('en-IN')} ${a.whatsapp_sent ? '&bull; WhatsApp sent ✅' : ''}</div>
    </div>`).join('');
}

async function submitVitals() {
  const patientId = document.getElementById('vitalPatientId').value;
  if (!patientId) { showToast('Please select a patient first', 'error'); return; }

  const data = {
    patient_id: parseInt(patientId),
    heart_rate: parseInt(document.getElementById('inHR').value),
    systolic_bp: parseInt(document.getElementById('inSBP').value),
    diastolic_bp: parseInt(document.getElementById('inDBP').value),
    temperature: parseFloat(document.getElementById('inTemp').value),
    respiratory_rate: parseInt(document.getElementById('inRR').value),
    spo2: parseInt(document.getElementById('inSpO2').value),
    gcs: parseInt(document.getElementById('inGCS').value),
    wbc_count: parseFloat(document.getElementById('inWBC').value) || null,
    lactate: parseFloat(document.getElementById('inLactate').value) || null,
    recorded_by: document.getElementById('inRecordedBy').value || 'Nurse',
  };

  const btn = document.getElementById('submitVitalsBtn');
  btn.textContent = 'Calculating...'; btn.disabled = true;

  const res = await apiCall('POST', '/api/icu/vitals', data);
  btn.textContent = 'Record Vitals'; btn.disabled = false;

  if (res.success) {
    const d = res.data;
    document.getElementById('riskResult').style.display = 'block';
    document.getElementById('riskScore').textContent = d.risk_score;
    document.getElementById('qsofaScore').textContent = d.qsofa_score;
    document.getElementById('riskStatus').className = `risk-indicator risk-${d.status}`;
    document.getElementById('riskStatus').textContent = d.status.toUpperCase();
    document.getElementById('recommendations').innerHTML = d.recommendations.map(r =>
      `<div style="padding:6px 10px;background:var(--surface2);border-radius:6px;margin-bottom:6px;font-size:13px">⚡ ${r}</div>`
    ).join('');
    if (d.alert_sent) { showToast('🚨 HIGH RISK! Alert sent to doctor via WhatsApp', 'error'); }
    else { showToast('Vitals recorded successfully', 'success'); }
    // Refresh
    await loadPatients();
    await loadStats();
    if (selectedPatient) await loadVitalsHistory(selectedPatient.id);
  } else {
    showToast(res.message || 'Error recording vitals', 'error');
  }
}

async function addPatient() {
  const data = {
    bed_number: document.getElementById('newBed').value.trim(),
    patient_name: document.getElementById('newName').value.trim(),
    age: parseInt(document.getElementById('newAge').value),
    gender: document.getElementById('newGender').value,
    diagnosis: document.getElementById('newDiagnosis').value.trim(),
    doctor_name: document.getElementById('newDoctor').value.trim(),
    doctor_phone: document.getElementById('newDoctorPhone').value.trim(),
  };
  if (!data.bed_number || !data.patient_name) { showToast('Bed number and name required', 'error'); return; }
  const res = await apiCall('POST', '/api/icu/patient/add', data);
  if (res.success) {
    closeModal('addPatientModal');
    showToast('Patient added to ICU', 'success');
    loadPatients(); loadStats();
  } else {
    showToast(res.message || 'Error', 'error');
  }
}

// Auto refresh every 60s
document.addEventListener('DOMContentLoaded', async () => {
  const token = Auth.getToken();
  if (!token) { document.getElementById('icuLoginPrompt').style.display = 'block'; return; }
  document.getElementById('icuLoginPrompt').style.display = 'none';
  document.getElementById('icuContent').style.display = 'flex';
  await loadPatients();
  await loadStats();
  setInterval(() => { loadPatients(); loadStats(); }, 60000);
});
