/* ── Cosmetica Frontend JS ── */

const API_BASE = '';

// ─── Tab switching ────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
  });
});

// ─── Category selector ────────────────────────────────────────────────────────
let selectedCategory = 'full';
document.querySelectorAll('.cat-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedCategory = btn.dataset.cat;
  });
});

// ─── Generic upload + camera handler factory ──────────────────────────────────
function setupUploadFlow(prefix, endpoint, renderFn, getCat) {
  const fileInput = document.getElementById(`${prefix}-file`);
  const dropZone = document.getElementById(`${prefix}-drop-zone`);
  const cameraBtn = document.getElementById(`${prefix}-camera-btn`);
  const cameraWrap = document.getElementById(`${prefix}-camera-wrap`);
  const video = document.getElementById(`${prefix}-video`);
  const captureBtn = document.getElementById(`${prefix}-capture-btn`);
  const cameraClose = document.getElementById(`${prefix}-camera-close`);
  const previewWrap = document.getElementById(`${prefix}-preview-wrap`);
  const previewImg = document.getElementById(`${prefix}-preview-img`);
  const analyzeBtn = document.getElementById(`${prefix}-analyze-btn`);
  const retakeBtn = document.getElementById(`${prefix}-retake-btn`);
  const loadingEl = document.getElementById(`${prefix}-loading`);
  const resultsEl = document.getElementById(`${prefix}-results`);

  let stream = null;
  let selectedBlob = null;

  fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) showPreview(file);
  });

  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) showPreview(file);
  });

  cameraBtn.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
      video.srcObject = stream;
      dropZone.classList.add('hidden');
      cameraWrap.classList.remove('hidden');
    } catch {
      alert('Could not access camera. Please allow camera permissions or upload an image instead.');
    }
  });

  cameraClose.addEventListener('click', () => stopCamera());

  captureBtn.addEventListener('click', () => {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob(blob => { showPreview(blob, true); stopCamera(); }, 'image/jpeg', 0.92);
  });

  function stopCamera() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    cameraWrap.classList.add('hidden');
    if (!selectedBlob) dropZone.classList.remove('hidden');
  }

  function showPreview(fileOrBlob) {
    selectedBlob = fileOrBlob;
    previewImg.src = URL.createObjectURL(fileOrBlob);
    dropZone.classList.add('hidden');
    previewWrap.classList.remove('hidden');
    resultsEl.classList.add('hidden');
    loadingEl.classList.add('hidden');
  }

  retakeBtn.addEventListener('click', () => {
    selectedBlob = null;
    previewWrap.classList.add('hidden');
    dropZone.classList.remove('hidden');
    resultsEl.classList.add('hidden');
    fileInput.value = '';
  });

  analyzeBtn.addEventListener('click', async () => {
    if (!selectedBlob) return;
    previewWrap.classList.add('hidden');
    loadingEl.classList.remove('hidden');
    resultsEl.classList.add('hidden');
    try {
      const formData = new FormData();
      formData.append('file', selectedBlob, selectedBlob.name || 'image.jpg');
      if (getCat) formData.append('category', getCat());
      const res = await fetch(`${API_BASE}${endpoint}`, { method: 'POST', body: formData });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Analysis failed'); }
      const data = await res.json();
      loadingEl.classList.add('hidden');
      resultsEl.classList.remove('hidden');
      renderFn(data, resultsEl);
      setTimeout(() => resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      loadingEl.classList.add('hidden');
      resultsEl.classList.remove('hidden');
      resultsEl.innerHTML = `
        <div style="text-align:center;padding:60px 40px;background:var(--glass);backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:var(--radius)">
          <p style="font-size:32px;margin-bottom:16px">⚠</p>
          <p style="font-family:'Cormorant Garamond',serif;font-size:22px;margin-bottom:8px">Analysis failed</p>
          <p style="color:var(--text-muted);font-size:14px">${err.message}</p>
          <button class="btn btn-outline" style="margin-top:24px" onclick="location.reload()">Try Again</button>
        </div>`;
    }
  });
}

// ─── Product Analysis Renderer ────────────────────────────────────────────────
function renderProductResults(data, container) {
  const score = data.safety_score || 0;
  const rating = data.safety_rating || 'Unknown';
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;
  const strokeColor = score >= 70 ? '#5A9E6F' : score >= 50 ? '#C9963A' : '#C05050';
  const ratingBadge = { 'Excellent': 'badge-safe', 'Good': 'badge-safe', 'Fair': 'badge-caution', 'Poor': 'badge-danger', 'Dangerous': 'badge-danger' }[rating] || 'badge-caution';
  const veganBadge = data.is_vegan ? `<span class="badge badge-vegan">✓ Vegan</span>` : `<span class="badge badge-nvegan">✕ Not Vegan</span>`;
  const cfBadge = data.is_cruelty_free ? `<span class="badge badge-cf">✓ Cruelty-Free</span>` : `<span class="badge badge-nvegan">✕ Animal Tested</span>`;
  const concernsHTML = (data.concerns || []).map(c => `<span class="tag tag-concern">${c}</span>`).join('');
  const benefitsHTML = (data.benefits || []).map(b => `<span class="tag tag-benefit">${b}</span>`).join('');
  const skinHTML = (data.skin_types || []).map(s => `<span class="tag">${s}</span>`).join('');
  const ingredientsHTML = (data.ingredients || []).map(ing => {
    const safeClass = ing.safety === 'Safe' ? 'safe' : ing.safety === 'Caution' ? 'caution' : 'avoid';
    const concernHTML = ing.concern ? `<div class="ingredient-concern">⚠ ${ing.concern}</div>` : '';
    return `
      <div class="ingredient-row">
        <div>
          <div class="ingredient-name">${ing.name}${ing.is_toxic ? ' <span style="color:var(--danger);font-size:11px">●</span>' : ''}</div>
          <div class="ingredient-purpose">${ing.purpose}</div>
          ${concernHTML}
        </div>
        <div class="ingredient-right">
          <div class="safety-dot ${safeClass}"></div>
          <div class="safety-label ${safeClass}">${ing.safety}</div>
        </div>
      </div>`;
  }).join('');

  container.innerHTML = `
    <div class="score-card">
      <div class="product-name">${data.product_name}</div>
      <div class="score-ring">
        <svg viewBox="0 0 120 120">
          <circle class="track" cx="60" cy="60" r="54"/>
          <circle class="fill" cx="60" cy="60" r="54" stroke="${strokeColor}" stroke-dasharray="${circumference}" stroke-dashoffset="${circumference}" id="score-arc"/>
        </svg>
        <div class="score-number">
          <span style="color:${strokeColor}">${score}</span>
          <span>/100</span>
        </div>
      </div>
      <div class="score-badges">
        <span class="badge ${ratingBadge}">${rating}</span>
        ${veganBadge}
        ${cfBadge}
      </div>
    </div>
    <div class="info-grid">
      ${concernsHTML ? `<div class="info-card"><div class="info-card-title">⚠ Concerns</div><div class="tag-list">${concernsHTML}</div></div>` : ''}
      ${benefitsHTML ? `<div class="info-card"><div class="info-card-title">✓ Benefits</div><div class="tag-list">${benefitsHTML}</div></div>` : ''}
      ${skinHTML ? `<div class="info-card"><div class="info-card-title">Skin Types</div><div class="tag-list">${skinHTML}</div></div>` : ''}
      <div class="info-card">
        <div class="info-card-title">Safety Legend</div>
        <div style="display:flex;flex-direction:column;gap:8px">
          <div style="display:flex;align-items:center;gap:8px"><div class="safety-dot safe"></div><span style="font-size:13px;color:var(--text-muted)">Safe — No concerns</span></div>
          <div style="display:flex;align-items:center;gap:8px"><div class="safety-dot caution"></div><span style="font-size:13px;color:var(--text-muted)">Caution — Use mindfully</span></div>
          <div style="display:flex;align-items:center;gap:8px"><div class="safety-dot avoid"></div><span style="font-size:13px;color:var(--text-muted)">Avoid — Known risks</span></div>
        </div>
      </div>
    </div>
    ${ingredientsHTML ? `
    <div class="ingredients-card">
      <div class="ingredients-header">
        <h3>Ingredient Breakdown</h3>
        <span style="font-size:12px;color:var(--text-light)">${data.ingredients.length} ingredients</span>
      </div>
      ${ingredientsHTML}
    </div>` : ''}
    <div class="summary-card">
      <p>${data.summary}</p>
      <p class="recommendation">${data.recommendation}</p>
    </div>
    <div class="summary-card" style="margin-top:20px">
      <div style="font-size:10px;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;color:var(--text-light);margin-bottom:14px">🛍️ Find Safer Alternatives</div>
      <p style="font-size:13px;color:var(--text-muted);margin-bottom:16px">Enter your budget to find better products in the Indian market</p>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:12px">
        <input type="number" id="min-price" placeholder="Min ₹" style="width:100px;padding:8px 12px;border:1px solid var(--border);border-radius:50px;font-family:'DM Sans',sans-serif;font-size:13px;background:var(--warm-white);color:var(--text);outline:none"/>
        <span style="color:var(--text-muted);font-size:13px">to</span>
        <input type="number" id="max-price" placeholder="Max ₹" style="width:100px;padding:8px 12px;border:1px solid var(--border);border-radius:50px;font-family:'DM Sans',sans-serif;font-size:13px;background:var(--warm-white);color:var(--text);outline:none"/>
        <button class="btn btn-primary" id="find-alternatives-btn">Find Alternatives</button>
      </div>
      <div id="alternatives-results"></div>
    </div>
    <div style="text-align:center;padding:16px 0">
      <button class="btn btn-outline" id="product-new-scan">← Scan Another Product</button>
    </div>`;

  setTimeout(() => {
    const arc = document.getElementById('score-arc');
    if (arc) arc.style.strokeDashoffset = offset;
  }, 200);

  document.getElementById('product-new-scan').addEventListener('click', () => {
    container.classList.add('hidden');
    document.getElementById('product-name-input').value = '';
  });

  document.getElementById('find-alternatives-btn').addEventListener('click', async () => {
    const min = document.getElementById('min-price').value;
    const max = document.getElementById('max-price').value;
    const altResults = document.getElementById('alternatives-results');
    if (!min || !max) { altResults.innerHTML = `<p style="color:var(--danger);font-size:13px">Please enter both min and max price</p>`; return; }
    altResults.innerHTML = `<p style="font-size:13px;color:var(--text-muted);padding:12px 0">Finding alternatives<span class="dots"></span></p>`;
    try {
      const formData = new FormData();
      formData.append('product_name', data.product_name);
      formData.append('safety_rating', data.safety_rating);
      formData.append('min_price', min);
      formData.append('max_price', max);
      const res = await fetch('/api/alternatives', { method: 'POST', body: formData });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail);
      const cards = (result.alternatives || []).map(a => `
        <div style="padding:16px;border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:10px;background:var(--warm-white)">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
            <div>
              <div style="font-size:13px;font-weight:500;color:var(--text)">${a.brand} — ${a.name}</div>
              <div style="font-size:12px;color:var(--rose);font-weight:600">${a.price}</div>
            </div>
            <span class="badge badge-safe" style="font-size:10px">${a.safety_rating}</span>
          </div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">✓ ${a.why_better}</div>
          <div style="font-size:11px;color:var(--text-light)">🛒 ${a.where_to_buy}</div>
        </div>`).join('');
      altResults.innerHTML = cards || `<p style="font-size:13px;color:var(--text-muted)">No alternatives found in this range.</p>`;
    } catch (e) {
      altResults.innerHTML = `<p style="color:var(--danger);font-size:13px">${e.message}</p>`;
    }
  });
}

// ─── Shade Match Renderer ─────────────────────────────────────────────────────
function renderShadeResults(data, container) {
  function makeSection(title, emoji, items) {
    if (!items || items.length === 0) return '';
    const cards = items.map(s => {
      const matchClass = s.match_quality === 'Perfect' ? 'match-perfect' : s.match_quality === 'Great' ? 'match-great' : 'match-good';
      return `
        <div class="shade-item">
          <div class="shade-brand">${s.brand}</div>
          <div class="shade-product">${s.product}</div>
          <div class="shade-name">${s.shade}</div>
          <span class="shade-match ${matchClass}">${s.match_quality}</span>
        </div>`;
    }).join('');
    return `
      <div style="margin-bottom:28px">
        <div style="font-size:11px;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;color:var(--text-light);margin-bottom:12px">${emoji} ${title}</div>
        <div class="shades-grid">${cards}</div>
      </div>`;
  }

  const tipsHTML = (data.tips || []).map((t, i) => `
    <div class="tip-item">
      <div class="tip-num">${i + 1}</div>
      <div class="tip-text">${t}</div>
    </div>`).join('');

  container.innerHTML = `
    <div class="tone-card">
      <div class="tone-label">Your Skin Tone</div>
      <div class="tone-name">${data.skin_tone}</div>
      <div class="undertone-badge">${data.undertone} Undertone</div>
      <p style="font-size:14px;color:var(--text-muted);line-height:1.7;max-width:500px;margin:0 auto">${data.summary}</p>
    </div>
    <div style="background:var(--glass);backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:var(--radius);padding:32px;margin-bottom:20px;box-shadow:var(--shadow-sm)">
      <h3 style="font-family:'Cormorant Garamond',serif;font-size:24px;font-weight:400;margin-bottom:24px">Your Makeup Profile</h3>
      ${makeSection('Foundation', '🫧', data.foundation)}
      ${makeSection('Concealer', '✨', data.concealer)}
      ${makeSection('Blush', '🌸', data.blush)}
      ${makeSection('Bronzer', '☀️', data.bronzer)}
      ${makeSection('Eyeshadow', '👁️', data.eyeshadow)}
      ${makeSection('Lip Colour', '💄', data.lipcolour)}
      ${makeSection('Highlighter', '⭐', data.highlighter)}
    </div>
    <div class="tips-card">
      <h3>Personalised Tips</h3>
      ${tipsHTML}
    </div>
    <div class="summary-card" style="margin-top:20px">
      <div style="font-size:10px;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;color:var(--text-light);margin-bottom:14px">🛍️ Find Products In Your Budget</div>
      <p style="font-size:13px;color:var(--text-muted);margin-bottom:16px">Enter your budget to find matching products in the Indian market</p>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:12px">
        <input type="number" id="shade-min-price" placeholder="Min ₹" style="width:100px;padding:8px 12px;border:1px solid var(--border);border-radius:50px;font-family:'DM Sans',sans-serif;font-size:13px;background:var(--warm-white);color:var(--text);outline:none"/>
        <span style="color:var(--text-muted);font-size:13px">to</span>
        <input type="number" id="shade-max-price" placeholder="Max ₹" style="width:100px;padding:8px 12px;border:1px solid var(--border);border-radius:50px;font-family:'DM Sans',sans-serif;font-size:13px;background:var(--warm-white);color:var(--text);outline:none"/>
        <button class="btn btn-primary" id="shade-find-budget-btn">Find Products</button>
      </div>
      <div id="shade-budget-results"></div>
    </div>
    <div style="text-align:center;padding:16px 0">
      <button class="btn btn-outline" id="shade-new-scan">← Try Another Photo</button>
    </div>`;

  document.getElementById('shade-new-scan').addEventListener('click', () => {
    container.classList.add('hidden');
    document.getElementById('shade-drop-zone').classList.remove('hidden');
    document.getElementById('shade-preview-wrap').classList.add('hidden');
    document.getElementById('shade-file').value = '';
  });

  document.getElementById('shade-find-budget-btn').addEventListener('click', async () => {
    const min = document.getElementById('shade-min-price').value;
    const max = document.getElementById('shade-max-price').value;
    const budgetResults = document.getElementById('shade-budget-results');
    if (!min || !max) { budgetResults.innerHTML = `<p style="color:var(--danger);font-size:13px">Please enter both min and max price</p>`; return; }
    budgetResults.innerHTML = `<p style="font-size:13px;color:var(--text-muted);padding:12px 0">Finding products<span class="dots"></span></p>`;
    try {
      const formData = new FormData();
      formData.append('product_name', `${data.skin_tone} ${data.undertone} skin tone makeup`);
      formData.append('safety_rating', 'Good');
      formData.append('min_price', min);
      formData.append('max_price', max);
      const res = await fetch('/api/alternatives', { method: 'POST', body: formData });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail);
      const cards = (result.alternatives || []).map(a => `
        <div style="padding:16px;border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:10px;background:var(--warm-white)">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
            <div>
              <div style="font-size:13px;font-weight:500;color:var(--text)">${a.brand} — ${a.name}</div>
              <div style="font-size:12px;color:var(--rose);font-weight:600">${a.price}</div>
            </div>
            <span class="badge badge-safe" style="font-size:10px">${a.safety_rating}</span>
          </div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">✓ ${a.why_better}</div>
          <div style="font-size:11px;color:var(--text-light)">🛒 ${a.where_to_buy}</div>
        </div>`).join('');
      budgetResults.innerHTML = cards || `<p style="font-size:13px;color:var(--text-muted)">No products found in this range.</p>`;
    } catch (e) {
      budgetResults.innerHTML = `<p style="color:var(--danger);font-size:13px">${e.message}</p>`;
    }
  });
}

// ─── Product scan (text input) ────────────────────────────────────────────────
const productAnalyzeBtn = document.getElementById('product-analyze-btn');
const productLoading = document.getElementById('product-loading');
const productResults = document.getElementById('product-results');

productAnalyzeBtn.addEventListener('click', async () => {
  const name = document.getElementById('product-name-input').value.trim();
  if (!name) { alert('Please enter a product name'); return; }
  productLoading.classList.remove('hidden');
  productResults.classList.add('hidden');
  try {
    const formData = new FormData();
    formData.append('product_name', name);
    const res = await fetch('/api/analyze-product', { method: 'POST', body: formData });
    if (!res.ok) { const err = await res.json(); throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)); }
    const data = await res.json();
    productLoading.classList.add('hidden');
    productResults.classList.remove('hidden');
    renderProductResults(data, productResults);
    setTimeout(() => productResults.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
  } catch (err) {
    productLoading.classList.add('hidden');
    productResults.classList.remove('hidden');
    productResults.innerHTML = `<div style="text-align:center;padding:60px 40px;background:var(--glass);backdrop-filter:blur(16px);border:1px solid var(--border);border-radius:var(--radius)"><p style="font-size:32px;margin-bottom:16px">⚠</p><p style="font-family:'Cormorant Garamond',serif;font-size:22px;margin-bottom:8px">Analysis failed</p><p style="color:var(--text-muted);font-size:14px">${err.message}</p></div>`;
  }
});

document.getElementById('product-name-input').addEventListener('keypress', e => {
  if (e.key === 'Enter') productAnalyzeBtn.click();
});

// ─── Init ─────────────────────────────────────────────────────────────────────
setupUploadFlow('shade', '/api/shade-match', renderShadeResults, () => selectedCategory);