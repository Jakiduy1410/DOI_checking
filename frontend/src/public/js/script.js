
// ============ CANVAS PARTICLES ============
const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');
let particles = [];
let W, H;

function resize() {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

for (let i = 0; i < 60; i++) {
  particles.push({
    x: Math.random() * 1920, y: Math.random() * 1080,
    vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
    r: Math.random() * 1.5 + 0.5, a: Math.random() * 0.4 + 0.05
  });
}

function drawParticles() {
  ctx.clearRect(0, 0, W, H);
  const teal = '45, 212, 191';
  particles.forEach((p, i) => {
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
    if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${teal}, ${p.a})`;
    ctx.fill();
    // connect close particles
    for (let j = i + 1; j < particles.length; j++) {
      const q = particles[j];
      const dx = p.x - q.x, dy = p.y - q.y;
      const d = Math.sqrt(dx*dx + dy*dy);
      if (d < 120) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
        ctx.strokeStyle = `rgba(${teal}, ${0.06 * (1 - d/120)})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
  });
  requestAnimationFrame(drawParticles);
}
drawParticles();

// ============ FILE HANDLING ============
let files = [];
let allResults = [];

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const processBtn = document.getElementById('processBtn');

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => addFiles([...e.target.files]));

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  addFiles([...e.dataTransfer.files]);
});

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
  return (bytes/1024/1024).toFixed(1) + ' MB';
}

function addFiles(newFiles) {
  const allowed = ['pdf','docx','doc','txt'];
  newFiles.forEach(f => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) { showToast(`File "${f.name}" không được hỗ trợ`, 'error'); return; }
    if (files.find(x => x.name === f.name && x.size === f.size)) return;
    files.push(f);
  });
  renderFileList();
}

function renderFileList() {
  fileList.innerHTML = '';
  files.forEach((f, i) => {
    const ext = f.name.split('.').pop().toLowerCase();
    const item = document.createElement('div');
    item.className = 'file-item';
    item.id = `file-${i}`;
    item.innerHTML = `
      <div class="file-ext ext-${ext}">${ext.toUpperCase()}</div>
      <div class="file-info">
        <div class="file-name">${f.name}</div>
        <div class="file-size">${formatSize(f.size)}</div>
      </div>
      <span class="file-status status-ready" id="status-${i}">Sẵn sàng</span>
      <button class="remove-btn" onclick="removeFile(${i})" title="Xóa file">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    `;
    fileList.appendChild(item);
  });
  processBtn.disabled = files.length === 0;
}

function removeFile(i) {
  files.splice(i, 1);
  renderFileList();
}

function clearAll() {
  files = [];
  allResults = [];
  renderFileList();
  document.getElementById('results-section').style.display = 'none';
  document.getElementById('divider').style.display = 'none';
  document.getElementById('progressWrap').classList.remove('active');
  updateStats(0, 0, 0, 0);
  fileInput.value = '';
}

// ============ PROCESSING ============
// [THÊM MỚI]: Gắn sự kiện click cho 2 nút bấm để nó hết bị "liệt"
processBtn.addEventListener('click', processFiles);
document.getElementById('clearAllBtn').addEventListener('click', clearAll);

async function processFiles() {
  if (files.length === 0) return;

  processBtn.disabled = true;
  document.getElementById('progressWrap').classList.add('active');
  allResults = [];

  const total = files.length;
  
  // Hiển thị trạng thái đang xử lý cho tất cả các file
  files.forEach((_, i) => setStatus(i, 'processing', 'Đang gửi dữ liệu...'));
  setProgress(0.2, `Đang tải lên ${total} file...`);

  try {
    const formData = new FormData();
    // Gom tất cả các file vào một key 'files' (Backend đang đợi list[UploadFile])
    files.forEach(file => {
      formData.append('files', file);
    });

    setProgress(0.5, `Hệ thống đang trích xuất & xác thực DOI...`);
    
    const resp = await fetch('http://localhost:8000/api/process', { 
      method: 'POST', 
      body: formData 
    });
    
    if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
    
    const data = await resp.json();
    allResults = data.results;

    // Cập nhật trạng thái UI cho từng file dựa trên kết quả trả về
    allResults.forEach((result, i) => {
      setStatus(i, result.status === 'error' ? 'error' : 'done',
        result.status === 'error' ? 'Lỗi' : `${result.totalFound} DOI`);
    });

    setProgress(1, 'Hoàn thành!');
    renderResults();
    updateStatsSummary();
    showToast(`Đã xử lý xong toàn bộ ${total} file`, 'success');

  } catch(e) {
    console.error(e);
    files.forEach((_, i) => setStatus(i, 'error', 'Lỗi hệ thống'));
    showToast(`Có lỗi xảy ra: ${e.message}`, 'error');
  } finally {
    processBtn.disabled = false;
  }
}

// Hàm processFile cũ không còn dùng nữa vì đã gộp vào processFiles

function setStatus(i, type, text) {
  const el = document.getElementById(`status-${i}`);
  if (!el) return;
  el.className = `file-status status-${type}`;
  el.textContent = text;
}

function setProgress(pct, text) {
  const fill = document.getElementById('progressFill');
  const pctEl = document.getElementById('progressPct');
  const textEl = document.getElementById('progressText');
  const p = Math.round(pct * 100);
  fill.style.width = p + '%';
  pctEl.textContent = p + '%';
  textEl.textContent = text;
}


// ============ RENDER RESULTS ============
function renderResults() {
  const container = document.getElementById('resultsContainer');
  container.innerHTML = '';

  if (allResults.length === 0) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </div>
      <div class="empty-title">Chưa có kết quả</div>
      <div class="empty-sub">Tải lên file và nhấn "Bắt đầu kiểm tra" để trích xuất DOI</div>
    </div>`;
  } else {
    allResults.forEach((r, ri) => {
      const card = document.createElement('div');
      card.className = 'file-result';
      card.style.animationDelay = (ri * 0.1) + 's';

      const ext = (r.filename || '').split('.').pop().toLowerCase();
      const doiHtml = r.dois && r.dois.length > 0
        ? r.dois.map((d, di) => doiCardHtml(d, ri, di)).join('')
        : `<div style="padding:1.5rem;text-align:center;color:var(--text-muted);font-size:0.85rem;">Không tìm thấy DOI trong tài liệu này</div>`;

      card.innerHTML = `
        <div class="file-result-header">
          <div class="file-result-icon">
            <div class="file-ext ext-${ext}">${ext.toUpperCase()}</div>
          </div>
          <div class="file-result-meta">
            <div class="file-result-name">${r.filename}</div>
            <div class="file-result-sub">${r.status === 'error' ? '⚠ ' + r.error : `${r.textLength?.toLocaleString() || 0} ký tự được phân tích`}</div>
          </div>
          <div class="file-result-badges">
            <span class="badge badge-total">${r.totalFound || 0} DOI</span>
            ${r.validCount ? `<span class="badge badge-valid">✓ ${r.validCount}</span>` : ''}
            ${r.invalidCount ? `<span class="badge badge-invalid">✗ ${r.invalidCount}</span>` : ''}
          </div>
        </div>
        <div class="doi-list">${doiHtml}</div>
      `;
      container.appendChild(card);
    });
  }

  document.getElementById('results-section').style.display = 'block';
  document.getElementById('divider').style.display = 'flex';
  document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function doiCardHtml(d, ri, di) {
  const isValid = d.valid;
  const id = `doi-${ri}-${di}`;
  
  // SỬA Ở ĐÂY: Tạo một cái băng rôn báo lỗi nếu nó không hợp lệ
  const errorBanner = !isValid ? `<div class="error-msg" style="margin-bottom: 1rem; padding: 0.5rem; background: #ffebee; color: #c62828; border-radius: 4px;">⚠ ${d.error || 'DOI không hợp lệ'}</div>` : '';

  // SỬA Ở ĐÂY: Dùng chung 1 layout chi tiết (detail-grid) cho cả 2 trường hợp
  const detailsHtml = `
    ${errorBanner}
    <div class="detail-grid" style="${!isValid ? 'opacity: 0.8;' : ''}">
      <div class="detail-item" style="grid-column:1/-1">
        <label>Tiêu đề</label>
        <span>${d.title}</span>
      </div>
      <div class="detail-item">
        <label>Tác giả</label>
        <span>${d.authors}</span>
      </div>
      <div class="detail-item">
        <label>Tạp chí / Nhà xuất bản</label>
        <span>${d.journal}</span>
      </div>
      <div class="detail-item">
        <label>Năm xuất bản</label>
        <span>${d.year}</span>
      </div>
      <div class="detail-item">
        <label>Loại tài liệu</label>
        <span>${d.type}</span>
      </div>

      <div class="detail-item" style="grid-column:1/-1">
        <label>Link DOI</label>
        <a class="detail-link" href="${d.doi !== 'No DOI' ? 'https://doi.org/' + d.doi : '#'}" target="_blank" rel="noopener">
          ${d.doi !== 'No DOI' ? 'https://doi.org/' + d.doi : 'Không có DOI gốc'}
        </a>
      </div>
    </div>
  `;

  return `
    <div class="doi-card ${isValid ? 'valid' : 'invalid'}" id="${id}">
      <div class="doi-card-header" onclick="toggleDOI('${id}')">
        <div class="doi-status-dot"></div>
        <div class="doi-string">${d.doi}</div>
        <div class="doi-toggle">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>
      <div class="doi-details">${detailsHtml}</div>
    </div>
  `;
}

function toggleDOI(id) {
  document.getElementById(id).classList.toggle('open');
}

function updateStatsSummary() {
  let totalDOIs = 0, totalValid = 0, totalInvalid = 0;
  allResults.forEach(r => {
    totalDOIs += r.totalFound || 0;
    totalValid += r.validCount || 0;
    totalInvalid += r.invalidCount || 0;
  });
  updateStats(allResults.length, totalDOIs, totalValid, totalInvalid);
}

function updateStats(files, dois, valid, invalid) {
  animateNumber('stat-files', files);
  animateNumber('stat-dois', dois);
  animateNumber('stat-valid', valid);
  animateNumber('stat-invalid', invalid);
}

function animateNumber(id, target) {
  const el = document.getElementById(id);
  const start = parseInt(el.textContent) || 0;
  const dur = 600;
  const startTime = performance.now();
  function step(now) {
    const t = Math.min((now - startTime) / dur, 1);
    el.textContent = Math.round(start + (target - start) * t);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function exportResults() {
  if (!allResults.length) return;
  const blob = new Blob([JSON.stringify(allResults, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `doi-results-${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  showToast('Đã xuất file JSON', 'success');
}

// ============ TOAST ============
function showToast(msg, type='success') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<div class="toast-dot"></div><span>${msg}</span>`;
  document.body.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'slideInRight 0.3s ease reverse both';
    setTimeout(() => t.remove(), 300);
  }, 3000);
}

