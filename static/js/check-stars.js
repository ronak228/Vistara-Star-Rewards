// ===== VISTARA ESSENTIALS — CHECK STARS PAGE =====

document.addEventListener('DOMContentLoaded', () => {
  LangManager.init();
  document.getElementById('checkEmail').focus();
  fetch('/api/wake', { method: 'GET' }).catch(() => {});
});

const form          = document.getElementById('checkStarsForm');
const emailInput    = document.getElementById('checkEmail');
const emailError    = document.getElementById('checkEmailError');
const resultsEl     = document.getElementById('resultsSection');
const noResultsEl   = document.getElementById('noResultsSection');
const errorEl       = document.getElementById('errorSection');
const loadingEl     = document.getElementById('loadingSection');

let isChecking = false;

function isValidEmail(e) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e); }

function hideAll() {
  [resultsEl, noResultsEl, errorEl, loadingEl].forEach(el => {
    if (el) { el.style.display = 'none'; el.classList.remove('fade-in'); }
  });
}

function show(el) {
  hideAll();
  if (el) { el.style.display = 'block'; setTimeout(() => el.classList.add('fade-in'), 10); }
}

// ===== STATUS CONFIG =====
const STATUS_CONFIG = {
  approved:     { icon: '⭐', label: 'Approved',    color: '#2ECC71', bg: '#f0fff8', note: 'Star credited to your account!' },
  pending:      { icon: '⏳', label: 'Pending',     color: '#F39C12', bg: '#fffbf0', note: 'Waiting for delivery confirmation from Meesho CSV' },
  under_review: { icon: '🔍', label: 'Under Review',color: '#3498DB', bg: '#f0f8ff', note: 'Delivered! Star will be credited after 21-day return window' },
  rejected:     { icon: '❌', label: 'Rejected',    color: '#E74C3C', bg: '#fff5f5', note: 'Order was returned or cancelled — no star given' },
  disputed:     { icon: '⚠️', label: 'Disputed',   color: '#E67E22', bg: '#fff8f0', note: 'Please contact support with your token' },
  stale:        { icon: '💤', label: 'Expired',     color: '#95A5A6', bg: '#f8f9fa', note: 'Order not found in Meesho CSV after 60 days' },
};

// ===== RENDER RESULTS =====
function renderResults(data) {
  const approved    = parseInt(data.approved     || 0);
  const pending     = parseInt(data.pending      || 0);
  const underReview = parseInt(data.under_review || 0);
  const rejected    = parseInt(data.rejected     || 0);
  const orders      = data.orders || [];

  // --- Stars display ---
  const starsEl = document.getElementById('starsDisplay');
  const countEl = document.getElementById('starsCount');
  if (starsEl) starsEl.textContent = approved > 0 ? '⭐'.repeat(Math.min(approved, 15)) : '—';
  if (countEl) countEl.textContent = approved;

  // --- Stats badges ---
  const showStat = (id, numId, count) => {
    const el = document.getElementById(id);
    const ne = document.getElementById(numId);
    if (el) el.style.display = count > 0 ? 'flex' : 'none';
    if (ne) ne.textContent = count;
  };
  showStat('summaryPending',  'statPendingNum',  pending);
  showStat('summaryReview',   'statReviewNum',   underReview);
  showStat('summaryApproved', 'statApprovedNum', approved);
  showStat('summaryRejected', 'statRejectedNum', rejected);

  // --- Progress bar ---
  const progressBar  = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const milestone    = document.getElementById('milestonMessage');
  if (approved < 5) {
    if (progressBar)  progressBar.style.width = (approved / 5 * 100) + '%';
    if (progressText) progressText.textContent = `${approved} / 5 ⭐`;
    if (milestone)    milestone.textContent = `${5 - approved} more star${5 - approved !== 1 ? 's' : ''} to FREE GIFT 🎁`;
  } else if (approved < 10) {
    if (progressBar)  progressBar.style.width = ((approved - 5) / 5 * 100) + '%';
    if (progressText) progressText.textContent = `${approved - 5} / 5 ⭐`;
    if (milestone)    milestone.textContent = `${10 - approved} more star${10 - approved !== 1 ? 's' : ''} to PREMIUM PRIZE 🏆`;
  } else {
    if (progressBar)  progressBar.style.width = '100%';
    if (progressText) progressText.textContent = '10 / 10 ⭐';
    if (milestone)    milestone.textContent = '🏆 All rewards unlocked!';
  }

  // --- Status note ---
  const noteEl = document.getElementById('statusNote');
  if (noteEl) {
    if (underReview > 0) {
      noteEl.textContent = '🔍 Delivery confirmed! Stars credited after 21-day return window closes.';
      noteEl.style.display = 'block';
    } else if (pending > 0) {
      noteEl.textContent = '⏳ Your order is being verified. Stars added once delivery is confirmed by Meesho.';
      noteEl.style.display = 'block';
    } else {
      noteEl.style.display = 'none';
    }
  }

  // --- Tiers ---
  const t5  = document.getElementById('tier5');
  const t10 = document.getElementById('tier10');
  if (t5)  { t5.classList.toggle('unlocked', approved >= 5);  t5.classList.toggle('locked', approved < 5); }
  if (t10) { t10.classList.toggle('unlocked', approved >= 10); t10.classList.toggle('locked', approved < 10); }

  // --- Claim button if 5+ stars ---
  const existingClaimBtn = document.getElementById('claimRewardBtnCS');
  if (existingClaimBtn) existingClaimBtn.remove();
  if (approved >= 5) {
    const claimBtn = document.createElement('div');
    claimBtn.id = 'claimRewardBtnCS';
    claimBtn.style.cssText = 'margin-top:16px;text-align:center';
    const isPremium = approved >= 10;
    claimBtn.innerHTML = `
      <button onclick="openClaimFromCheckStars(${approved})"
        style="display:inline-flex;align-items:center;gap:10px;background:linear-gradient(135deg,#FF6B6B,#ee5a24);color:#fff;font-weight:700;font-size:1rem;padding:14px 28px;border-radius:12px;border:none;cursor:pointer;box-shadow:0 4px 18px rgba(255,107,107,0.35);width:100%;justify-content:center;max-width:340px">
        ${isPremium ? '🏆' : '🎁'} Claim My ${isPremium ? 'Premium Prize' : 'Free Reward'} Now →
      </button>
      <p style="font-size:11px;color:#888;margin-top:8px">You'll be redirected to WhatsApp with all your details pre-filled</p>`;
    const tiersEl = document.querySelector('.cs-tiers');
    if (tiersEl) tiersEl.after(claimBtn);
  }

  // --- Order records ---
  renderOrderRecords(orders);

  show(resultsEl);
}

// ===== ORDER RECORDS — the main table users wanted =====
function renderOrderRecords(orders) {
  const list = document.getElementById('orderRecordsList');
  if (!list) return;

  if (!orders || orders.length === 0) {
    list.innerHTML = '<p style="text-align:center;color:#aaa;padding:20px;font-size:.85rem">No orders found</p>';
    return;
  }

  list.innerHTML = '';

  orders.forEach((order, idx) => {
    const cfg   = STATUS_CONFIG[order.status] || STATUS_CONFIG.pending;
    const date  = order.submitted
      ? new Date(order.submitted).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })
      : '—';
    const approvedDate = order.approved
      ? new Date(order.approved).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })
      : null;

    const card = document.createElement('div');
    card.className = 'order-record-card';
    card.style.borderLeftColor = cfg.color;
    card.style.background = cfg.bg;

    card.innerHTML = `
      <div class="orc-top">
        <div class="orc-left">
          <span class="orc-num">#${idx + 1}</span>
          <span class="orc-status-icon">${cfg.icon}</span>
          <div class="orc-info">
            <span class="orc-order-id">Order ID: ${order.order_id}</span>
            <span class="orc-date">Submitted: ${date}</span>
          </div>
        </div>
        <span class="orc-badge" style="background:${cfg.color}18;color:${cfg.color};border:1px solid ${cfg.color}40">
          ${cfg.icon} ${cfg.label}
        </span>
      </div>
      <div class="orc-bottom">
        <div class="orc-token">
          <span class="orc-token-label">🎫 Token:</span>
          <span class="orc-token-value">${order.token || '—'}</span>
        </div>
        ${approvedDate ? `<div class="orc-approved-date">✅ Approved: ${approvedDate}</div>` : ''}
        <div class="orc-note">${cfg.note}</div>
      </div>
    `;
    list.appendChild(card);
  });
}

// ===== FORM SUBMIT =====
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = emailInput.value.trim();
  emailError.classList.remove('show');

  if (!email) {
    emailError.textContent = 'Please enter your email address';
    emailError.classList.add('show');
    return;
  }
  if (!isValidEmail(email)) {
    emailError.textContent = 'Please enter a valid email address';
    emailError.classList.add('show');
    return;
  }
  if (isChecking) return;

  isChecking = true;
  show(loadingEl);
  if (loadingEl) loadingEl.style.display = 'flex';

  try {
    const res  = await fetch('/api/get-stars', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email })
    });
    const data = await res.json();

    if (data.success) {
      if (data.found) {
        renderResults(data);
      } else {
        show(noResultsEl);
        const t = id => document.getElementById(id);
        if (t('noResultsTitle')) t('noResultsTitle').textContent = LangManager.get('noResultsTitle');
        if (t('noResultsText'))  t('noResultsText').textContent  = LangManager.get('noResultsText');
      }
    } else {
      show(errorEl);
      const et = document.getElementById('errorText');
      if (et) et.textContent = data.error || 'Failed to fetch. Please try again.';
    }
  } catch (err) {
    show(errorEl);
    const et = document.getElementById('errorText');
    if (et) et.textContent = 'Connection error. Please try again.';
  } finally {
    isChecking = false;
  }
});

// ===== HELPERS =====
emailInput.addEventListener('input',  () => emailError.classList.remove('show'));
emailInput.addEventListener('blur',   () => {
  if (emailInput.value.trim() && !isValidEmail(emailInput.value.trim())) {
    emailError.textContent = 'Please enter a valid email address';
    emailError.classList.add('show');
  }
});

function resetCheck() {
  form.reset();
  hideAll();
  emailInput.focus();
  emailError.classList.remove('show');
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') resetCheck();
});