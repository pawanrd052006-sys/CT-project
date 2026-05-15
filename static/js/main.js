/* main.js — BlockVerify Frontend Logic */

// ── Clock ──────────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('topbarTime');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toUTCString().replace(' GMT', ' UTC');
}
setInterval(updateClock, 1000);
updateClock();

// ── Chain Status (ping /api/stats) ─────────────────────────────
async function checkChainStatus() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    const dot  = document.getElementById('chainStatusDot');
    const txt  = document.getElementById('chainStatusText');
    if (!dot) return;
    if (data.chain_valid) {
      dot.style.background = '#10b981';
      dot.style.boxShadow  = '0 0 6px #10b981';
      txt.textContent = 'Chain Healthy';
    } else {
      dot.style.background = '#ef4444';
      dot.style.boxShadow  = '0 0 6px #ef4444';
      txt.textContent = 'Chain Compromised!';
    }
  } catch { /* silent */ }
}
checkChainStatus();
setInterval(checkChainStatus, 30000);

// ── Animated Counters ──────────────────────────────────────────
function animateCounters() {
  document.querySelectorAll('.counter').forEach(el => {
    const target = parseInt(el.dataset.target, 10) || 0;
    const duration = 1200;
    const step = Math.ceil(target / (duration / 16));
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(timer);
    }, 16);
  });
}
animateCounters();

// ── Sidebar mobile toggle ──────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const toggle  = document.getElementById('sidebarToggle');
if (toggle && sidebar) {
  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
  document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// ── Auto-fill today's date on add product form ─────────────────
const dateInput = document.querySelector('input[name="date_added"]');
if (dateInput && !dateInput.value) {
  dateInput.value = new Date().toISOString().split('T')[0];
}

// ── Flash auto-dismiss ─────────────────────────────────────────
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 5000);
});

// ── Hash table — copy on click ─────────────────────────────────
document.querySelectorAll('.hash-cell, .hash-value.mono').forEach(el => {
  el.style.cursor = 'pointer';
  el.title = 'Click to copy';
  el.addEventListener('click', () => {
    navigator.clipboard.writeText(el.textContent.trim()).then(() => {
      const orig = el.style.color;
      el.style.color = '#10b981';
      setTimeout(() => el.style.color = orig, 800);
    });
  });
});
