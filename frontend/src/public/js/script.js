// ============ CANVAS PARTICLES ============
const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');
let particles = [];
let W, H;
function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
resize();
window.addEventListener('resize', resize);
for (let i = 0; i < 60; i++) {
  particles.push({ x: Math.random()*1920, y: Math.random()*1080,
    vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3,
    r: Math.random()*1.5+0.5, a: Math.random()*0.4+0.05 });
}
function drawParticles() {
  ctx.clearRect(0, 0, W, H);
  const teal = '45, 212, 191';
  particles.forEach((p, i) => {
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
    if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
    ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
    ctx.fillStyle = `rgba(${teal}, ${p.a})`; ctx.fill();
    for (let j = i+1; j < particles.length; j++) {
      const q = particles[j], dx = p.x-q.x, dy = p.y-q.y, d = Math.sqrt(dx*dx+dy*dy);
      if (d < 120) {
        ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y);
        ctx.strokeStyle = `rgba(${teal}, ${0.06*(1-d/120)})`; ctx.lineWidth=0.5; ctx.stroke();
      }
    }
  });
  requestAnimationFrame(drawParticles);
}
drawParticles();

// ============ FILE HANDLING ============
let files = [];
let allResults = [];
let activeTab = 0;

const dropZone   = document.getElementById('dropZone');
const fileInput  = document.getElementById('fileInput');
const fileList   = document.getElementById('fileList');
const processBtn = document.getElementById('processBtn');

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => addFiles([...e.target.files]));
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('drag-over'); addFiles([...e.dataTransfer.files]); });

function formatSize(b) {
  if (b < 1024) return b+' B';
  if (b < 1024*1024) return (b/1024).toFixed(1)+' KB';
  return (b/1024/1024).toFixed(1)+' MB';
}

function addFiles(newFiles) {
  const allowed = ['pdf','docx','doc','txt'];
  newFiles.forEach(f => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) { showToast(`File "${f.name}" không được hỗ trợ`, 'error'); return; }
    if (files.find(x => x.name===f.name && x.size===f.size)) return;
    files.push(f);
  });
  renderFileList();
}

function renderFileList() {
  fileList.innerHTML = '';
  files.forEach((f, i) => {
    const ext = f.name.split('.').pop().toLowerCase();
    const item = document.createElement('div');
    item.className = 'file-item'; item.id = `file-${i}`;
    item.innerHTML = `
      <div class="file-ext ext-${ext}">${ext.toUpperCase()}</div>
      <div class="file-info">
        <div class="file-name">${f.name}</div>
        <div class="file-size">${formatSize(f.size)}</div>
      </div>
      <span class="file-status status-ready" id="status-${i}">Sẵn sàng</span>
      <button class="remove-btn" onclick="removeFile(${i})">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>`;
    fileList.appendChild(item);
  });
  processBtn.disabled = files.length === 0;
}

function removeFile(i) { files.splice(i, 1); renderFileList(); }

function clearAll() {
  files = []; allResults = []; activeTab = 0;
  renderFileList();
  document.getElementById('results-section').style.display = 'none';
  document.getElementById('divider').style.display = 'none';
  document.getElementById('progressWrap').classList.remove('active');
  updateStats(0, 0, 0, 0);
  fileInput.value = '';
}

// ============ PROCESSING ============
async function processFiles() {
  if (!files.length) return;
  processBtn.disabled = true;
  document.getElementById('progressWrap').classList.add('active');
  allResults = [];
  const total = files.length;
  
  setProgress(0.3, `Đang khởi tạo và gửi ${total} file...`);
  
  try {
    const results = await processAllFiles(files);
    allResults = results;
    
    // Cập nhật trạng thái từng file trong danh sách
    results.forEach((res, idx) => {
        setStatus(idx, res.status==='error' ? 'error' : 'done',
            res.status==='error' ? 'Lỗi' : `${res.totalFound||0} refs`);
    });
    
    setProgress(1, 'Hoàn thành!');
  } catch(e) {
    console.error(e);
    showToast(`Lỗi: ${e.message}`, 'error');
    setProgress(0, 'Gặp sự cố khi xử lý');
  }

  activeTab = 0;
  renderResults();
  updateStatsSummary();
  processBtn.disabled = false;
  showToast(`Đã xử lý ${total} file thành công`, 'success');
}

function setStatus(i, type, text) {
  const el = document.getElementById(`status-${i}`);
  if (!el) return;
  el.className = `file-status status-${type}`;
  el.textContent = text;
}
function setProgress(pct, text) {
  const p = Math.round(pct*100);
  document.getElementById('progressFill').style.width = p+'%';
  document.getElementById('progressPct').textContent  = p+'%';
  document.getElementById('progressText').textContent = text;
}

async function processAllFiles(filesToUpload) {
  const formData = new FormData();
  filesToUpload.forEach(file => {
    formData.append('files', file);
  });
  
  const resp = await fetch('/api/process', { method:'POST', body: formData });
  if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
  
  const data = await resp.json();
  return data.results;
}

// ============ SUY RA DOI_STATUS ============
function inferStatus(d) {
  if (d.valid) return 'valid_doi';
  if (!d.error) return 'valid_doi';
  const err = d.error.toLowerCase();
  if (err.includes('web') || err.includes('bỏ qua'))                return 'web_resource';
  if (err.includes('kết nối') || err.includes('xác thực'))          return 'unverified';
  if (err.includes('không tồn tại') || err.includes('không hợp lệ')) return 'invalid_doi';
  if (err.includes('không tìm thấy'))                               return 'no_doi';
  return 'no_doi';
}

const STATUS_CFG = {
  valid_doi:    { label:'HỢP LỆ',         color:'#2dd4bf', bg:'rgba(45,212,191,0.12)',  icon:'✅' },
  found_doi:    { label:'TÌM THẤY',       color:'#60a5fa', bg:'rgba(96,165,250,0.12)',  icon:'🔍' },
  invalid_doi:  { label:'SAI / GIẢ',      color:'#f87171', bg:'rgba(248,113,113,0.12)', icon:'❌' },
  no_doi:       { label:'KHÔNG CÓ DOI',   color:'#fc0303', bg:'rgba(156,163,175,0.10)', icon:'—'  },
  web_resource: { label:'WEB',            color:'#a78bfa', bg:'rgba(167,139,250,0.12)', icon:'🌐' },
  unverified:   { label:'CHƯA XÁC THỰC', color:'#fbbf24', bg:'rgba(251,191,36,0.12)',  icon:'❓' },
};

// ============ SWITCH TAB ============
function switchTab(idx) {
  activeTab = idx;

  // Cập nhật tab active
  document.querySelectorAll('.file-tab').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });

  // Render nội dung bên phải
  renderTabContent(allResults[idx], idx);
}

// ============ RENDER RESULTS — layout 2 cột ============
function renderResults() {
  const container = document.getElementById('resultsContainer');
  container.innerHTML = '';

  if (!allResults.length) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div>
      <div class="empty-title">Chưa có kết quả</div>
      <div class="empty-sub">Tải lên file và nhấn "Bắt đầu kiểm tra"</div></div>`;
    return;
  }

  // ── Wrapper 2 cột ──
  const wrapper = document.createElement('div');
  wrapper.style.cssText = 'display:flex;gap:1.25rem;align-items:flex-start;margin-top:0.5rem';

  // ── Cột trái: danh sách file ──
  const sidebar = document.createElement('div');
  sidebar.id = 'file-tab-list';
  sidebar.style.cssText = `
    width: 240px;
    flex-shrink: 0;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    overflow: hidden;
    position: sticky;
    top: 1rem;
  `;

  const sidebarHeader = document.createElement('div');
  sidebarHeader.style.cssText = 'padding:0.75rem 1rem;font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em;border-bottom:1px solid rgba(255,255,255,0.06)';
  sidebarHeader.textContent = `${allResults.length} file`;
  sidebar.appendChild(sidebarHeader);

  allResults.forEach((r, i) => {
    const ext    = (r.filename||'').split('.').pop().toLowerCase();
    const dois   = r.dois || [];
    const counts = getCounts(dois);
    const tab    = document.createElement('div');
    tab.className = 'file-tab' + (i === activeTab ? ' active' : '');
    tab.onclick   = () => switchTab(i);
    tab.innerHTML = `
      <div style="display:flex;align-items:center;gap:0.6rem;padding:0.75rem 1rem;cursor:pointer;transition:background 0.15s;border-bottom:1px solid rgba(255,255,255,0.04)">
        <div class="file-ext ext-${ext}" style="font-size:0.55rem;padding:2px 5px;min-width:auto">${ext.toUpperCase()}</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:0.78rem;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r.filename}</div>
          <div style="font-size:0.68rem;color:var(--text-muted);margin-top:2px">
            ${r.status==='error' ? '⚠ Lỗi' : `${r.totalFound||0} refs · ✅${counts.valid_doi+counts.found_doi} ❌${counts.invalid_doi}`}
          </div>
        </div>
      </div>`;
    sidebar.appendChild(tab);
  });

  // ── Cột phải: nội dung chi tiết ──
  const content = document.createElement('div');
  content.id    = 'tab-content';
  content.style.cssText = 'flex:1;min-width:0;';

  wrapper.appendChild(sidebar);
  wrapper.appendChild(content);
  container.appendChild(wrapper);

  // Render tab đầu tiên
  renderTabContent(allResults[activeTab], activeTab);

  document.getElementById('results-section').style.display = 'block';
  document.getElementById('divider').style.display = 'flex';
  document.getElementById('results-section').scrollIntoView({ behavior:'smooth', block:'start' });
}

// ── Render nội dung 1 tab ────────────────────────────────────
function renderTabContent(r, ri) {
  const content = document.getElementById('tab-content');
  if (!content || !r) return;

  const ext    = (r.filename||'').split('.').pop().toLowerCase();
  const dois   = r.dois || [];
  const counts = getCounts(dois);

  content.innerHTML = `
    <div class="file-result" style="margin:0">
      <div class="file-result-header" style="flex-wrap:wrap;gap:0.75rem">
        <div class="file-result-icon"><div class="file-ext ext-${ext}">${ext.toUpperCase()}</div></div>
        <div class="file-result-meta" style="flex:1;min-width:120px">
          <div class="file-result-name">${r.filename}</div>
          <div class="file-result-sub">${r.status==='error' ? '⚠ '+r.error : `${r.totalFound||0} tài liệu tham khảo`}</div>
        </div>
        <div class="file-result-badges" style="flex-wrap:wrap;gap:0.4rem;align-items:center">
          <span class="badge badge-total">${r.totalFound||0} refs</span>
          ${counts.valid_doi    ? `<span class="badge badge-valid">✅ ${counts.valid_doi} hợp lệ</span>`:''}
          ${counts.found_doi    ? `<span class="badge" style="background:rgba(96,165,250,0.15);color:#60a5fa;border-color:rgba(96,165,250,0.25)">🔍 ${counts.found_doi} tìm thấy</span>`:''}
          ${counts.invalid_doi  ? `<span class="badge badge-invalid">❌ ${counts.invalid_doi} sai/giả</span>`:''}
          ${counts.no_doi ? `<span class="badge" style="background:rgba(252,3,3,0.1);color:#fc0303;border-color:rgba(252,3,3,0.2)">— ${counts.no_doi} không DOI</span>`:''}
          ${counts.web_resource ? `<span class="badge" style="background:rgba(167,139,250,0.12);color:#a78bfa;border-color:rgba(167,139,250,0.25)">🌐 ${counts.web_resource} web</span>`:''}
          ${counts.unverified   ? `<span class="badge" style="background:rgba(251,191,36,0.12);color:#fbbf24;border-color:rgba(251,191,36,0.25)">❓ ${counts.unverified} chưa xác thực</span>`:''}
          <button class="results-export-btn" onclick="exportSingle(${ri})" style="margin-left:0.5rem">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Xuất JSON
          </button>
        </div>
      </div>
      ${summaryBarHtml(counts, dois.length)}
      <div class="doi-list" style="padding:0">
        ${dois.length ? dois.map((d,di) => refRowHtml(d, ri, di)).join('') :
          '<div style="padding:1.5rem;text-align:center;color:var(--text-muted);font-size:0.85rem">Không tìm thấy tài liệu tham khảo</div>'}
      </div>
    </div>`;
}

// ── Helper đếm từng loại ─────────────────────────────────────
function getCounts(dois) {
  const counts = { valid_doi:0, found_doi:0, invalid_doi:0, no_doi:0, web_resource:0, unverified:0 };
  dois.forEach(d => { const s = inferStatus(d); if (counts[s]!==undefined) counts[s]++; });
  return counts;
}

// ── Thanh màu tóm tắt ────────────────────────────────────────
function summaryBarHtml(counts, total) {
  if (!total) return '';
  const bars = [
    { pct:(counts.valid_doi||0)/total*100,    color:'#2dd4bf' },
    { pct:(counts.found_doi||0)/total*100,    color:'#60a5fa' },
    { pct:(counts.invalid_doi||0)/total*100,  color:'#f87171' },
    { pct:(counts.web_resource||0)/total*100, color:'#a78bfa' },
    { pct:(counts.unverified||0)/total*100,   color:'#fbbf24' },
    { pct:(counts.no_doi||0)/total*100,       color:'#ff0101' },
  ];
  const segs = bars.map(b =>
    `<div style="flex:${b.pct};background:${b.color};min-width:${b.pct>0?2:0}px"></div>`
  ).join('');
  return `<div style="display:flex;height:6px;border-radius:3px;overflow:hidden;margin:0 1.5rem 1rem">${segs}</div>`;
}

// ── Render 1 dòng reference ───────────────────────────────────
function refRowHtml(d, ri, di) {
  const id     = `ref-${ri}-${di}`;
  const status = inferStatus(d);
  const cfg    = STATUS_CFG[status] || STATUS_CFG['no_doi'];

  const doiStr = (d.doi && d.doi !== 'No DOI') ? d.doi : '';
  const doiUrl = doiStr.startsWith('http') ? doiStr : (doiStr ? `https://doi.org/${doiStr}` : '');
  const doiLink = doiUrl
    ? `<a href="${doiUrl}" target="_blank" rel="noopener"
         style="color:${cfg.color};font-family:var(--font-mono);font-size:0.78rem;word-break:break-all">${doiUrl}</a>`
    : `<span style="color:var(--text-muted);font-size:0.8rem;font-style:italic">Không có DOI</span>`;

  return `
    <div style="border-bottom:1px solid rgba(255,255,255,0.04)">
      <div onclick="toggleRef('${id}')"
           style="display:flex;align-items:flex-start;gap:0.75rem;padding:0.85rem 1.25rem;cursor:pointer;transition:background 0.2s"
           onmouseover="this.style.background='rgba(255,255,255,0.02)'"
           onmouseout="this.style.background=''">
        <div style="min-width:28px;height:28px;border-radius:6px;background:rgba(255,255,255,0.05);display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-family:var(--font-mono);color:var(--text-muted);flex-shrink:0">${di+1}</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:0.88rem;color:var(--text-primary);margin-bottom:0.2rem;line-height:1.4">${d.title||'<em style="color:var(--text-muted)">Không rõ tiêu đề</em>'}</div>
          <div style="font-size:0.76rem;color:var(--text-muted)">${d.authors||''}${d.year && d.year!=='N/A' ? ' · '+d.year : ''}</div>
        </div>
        <div style="flex-shrink:0;display:flex;align-items:center;gap:0.4rem">
          <span style="font-size:0.62rem;font-weight:700;padding:3px 8px;border-radius:4px;background:${cfg.bg};color:${cfg.color};border:1px solid ${cfg.color}33;letter-spacing:.04em;white-space:nowrap">
            ${cfg.icon} ${cfg.label}
          </span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;color:var(--text-muted);flex-shrink:0">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>
      <div id="${id}" style="display:none;padding:0.75rem 1.25rem 1rem 3.2rem;background:rgba(0,0,0,0.15)">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem 1rem">
          <div>
            <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Tác giả</div>
            <div style="font-size:0.82rem;color:var(--text-secondary)">${d.authors||'N/A'}</div>
          </div>
          <div>
            <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Năm</div>
            <div style="font-size:0.82rem;color:var(--text-secondary)">${d.year||'N/A'}</div>
          </div>
          <div>
            <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Loại</div>
            <div style="font-size:0.82rem;color:var(--text-secondary)">${d.type||'Article'}</div>
          </div>
          <div>
            <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Tạp chí / Nguồn</div>
            <div style="font-size:0.82rem;color:var(--text-secondary)">${d.journal||'N/A'}</div>
          </div>
          <div>
            <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Trạng thái</div>
            <div style="font-size:0.82rem;color:${cfg.color}">${cfg.icon} ${cfg.label}</div>
          </div>
          <div style="grid-column:1/-1">
            <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">DOI</div>
            <div>${doiLink}</div>
          </div>
          ${d.error ? `<div style="grid-column:1/-1">
            <div style="font-size:0.78rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-left:3px solid ${cfg.color};border-radius:6px;padding:0.6rem 0.75rem;color:var(--text-muted)">
              ⚠ ${d.error}
            </div>
          </div>` : ''}
        </div>
      </div>
    </div>`;
}

function toggleRef(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

// ============ STATS ============
function updateStatsSummary() {
  let totalFiles=0, totalDOIs=0, totalValid=0, totalInvalid=0;
  allResults.forEach(r => {
    totalFiles++;
    totalDOIs    += r.totalFound   || 0;
    totalValid   += r.validCount   || 0;
    totalInvalid += r.invalidCount || 0;
  });
  updateStats(totalFiles, totalDOIs, totalValid, totalInvalid);
}

function updateStats(files, dois, valid, invalid) {
  animateNumber('stat-files',   files);
  animateNumber('stat-dois',    dois);
  animateNumber('stat-valid',   valid);
  animateNumber('stat-invalid', invalid);
}

function animateNumber(id, target) {
  const el = document.getElementById(id);
  const start = parseInt(el.textContent)||0;
  const dur = 600, t0 = performance.now();
  function step(now) {
    const t = Math.min((now-t0)/dur, 1);
    el.textContent = Math.round(start+(target-start)*t);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ============ EXPORT ============
function exportSingle(ri) {
  const r = allResults[ri];
  if (!r) return;
  const name = (r.filename || 'result').replace(/\.[^.]+$/, '');
  const blob = new Blob([JSON.stringify(r, null, 2)], { type:'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${name}_doi-result.json`;
  a.click();
  showToast(`Đã xuất ${name}.json`, 'success');
}

function exportResults() {
  if (!allResults.length) return;
  allResults.forEach((r, i) => exportSingle(i));
}

// ============ TOAST ============
function showToast(msg, type='success') { 
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<div class="toast-dot"></div><span>${msg}</span>`;
  document.body.appendChild(t);
  setTimeout(() => { t.style.animation='slideInRight 0.3s ease reverse both'; setTimeout(()=>t.remove(),300); }, 3000);
}
