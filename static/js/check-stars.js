// ===== VISTARA REWARDS — CHECK STARS PAGE JS v2 =====
// Now shows: approved stars + pending/under_review breakdown

document.addEventListener('DOMContentLoaded', () => {
  LangManager.init();
  document.getElementById('checkEmail').focus();
});

const checkStarsForm   = document.getElementById('checkStarsForm');
const checkEmailInput  = document.getElementById('checkEmail');
const resultsSection   = document.getElementById('resultsSection');
const noResultsSection = document.getElementById('noResultsSection');
const errorSection     = document.getElementById('errorSection');
const loadingSection   = document.getElementById('loadingSection');
const checkEmailError  = document.getElementById('checkEmailError');

let isChecking = false;

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ===== SECTION HELPERS =====
function hideAllSections() {
  [resultsSection, noResultsSection, errorSection, loadingSection].forEach(s => {
    s.style.display = 'none';
    s.classList.remove('fade-in');
  });
}

function showResults(apiData) {
  hideAllSections();
  resultsSection.style.display = 'block';
  setTimeout(() => resultsSection.classList.add('fade-in'), 10);
  updateStarsDisplay(apiData);
}

function showNoResults() {
  hideAllSections();
  noResultsSection.style.display = 'block';
  setTimeout(() => noResultsSection.classList.add('fade-in'), 10);
  const t = id => document.getElementById(id);
  if (t('noResultsTitle')) t('noResultsTitle').textContent = LangManager.get('noResultsTitle');
  if (t('noResultsText'))  t('noResultsText').textContent  = LangManager.get('noResultsText');
  if (t('submitFirstOrderBtn')) t('submitFirstOrderBtn').textContent = LangManager.get('submitFirstOrder');
}

function showErrorState(message) {
  hideAllSections();
  errorSection.style.display = 'block';
  setTimeout(() => errorSection.classList.add('fade-in'), 10);
  const t = id => document.getElementById(id);
  if (t('errorText'))          t('errorText').textContent          = message;
  if (t('errorSectionTitle'))  t('errorSectionTitle').textContent  = LangManager.get('errorSectionTitle');
  if (t('tryAgainSectionBtn')) t('tryAgainSectionBtn').textContent = LangManager.get('tryAgain');
}

function showLoading() {
  hideAllSections();
  loadingSection.style.display = 'flex';
  const el = document.getElementById('loadingTextEl');
  if (el) el.textContent = LangManager.get('loadingText');
}

// ===== STARS DISPLAY (v2 — uses full API response) =====
function updateStarsDisplay(apiData) {
  const approvedStars  = parseInt(apiData.approved_count  ?? apiData.total_stars ?? 0, 10);
  const pendingCount   = parseInt(apiData.pending_count   ?? 0, 10);
  const underReview    = parseInt(apiData.under_review_count ?? 0, 10);
  const rejectedCount  = parseInt(apiData.rejected_count  ?? 0, 10);

  // --- Star emoji display ---
  const starsDisplay = document.getElementById('starsDisplay');
  const starsCountEl = document.getElementById('starsCount');
  if (starsDisplay) {
    let starStr = '';
    for (let i = 0; i < Math.min(approvedStars, 20); i++) starStr += '⭐';
    starsDisplay.textContent = starStr || (approvedStars === 0 ? '—' : starStr);
  }
  if (starsCountEl) {
    const word = approvedStars === 1 ? LangManager.get('starWord') : LangManager.get('starsWord');
    starsCountEl.textContent = `${approvedStars} ${word}`;
  }

  // --- Static labels ---
  const setTxt = (id, key) => { const el = document.getElementById(id); if (el) el.textContent = LangManager.get(key); };
  setTxt('resultLabelEl',   'resultLabel');
  setTxt('progressLabelEl', 'progressLabel');
  setTxt('tiersTitleEl',    'tiersTitle');
  setTxt('tier5NameEl',     'tier5Name');
  setTxt('tier5RewardEl',   'tier5Reward');
  setTxt('tier10NameEl',    'tier10Name');
  setTxt('tier10RewardEl',  'tier10Reward');

  // --- Progress bar ---
  const progressBar  = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const milestoneMsg = document.getElementById('milestonMessage');

  if (approvedStars < 5) {
    const rem = 5 - approvedStars;
    if (progressBar)  progressBar.style.width = (approvedStars / 5 * 100) + '%';
    if (progressText) progressText.textContent = `${approvedStars} / 5 ${LangManager.get('starsWord')}`;
    if (milestoneMsg) milestoneMsg.textContent = `${LangManager.get('onlyMore')} ${rem} ${LangManager.get('milestoneToFree')}`;
  } else if (approvedStars < 10) {
    const rem = 10 - approvedStars;
    if (progressBar)  progressBar.style.width = ((approvedStars - 5) / 5 * 100) + '%';
    if (progressText) progressText.textContent = `${approvedStars - 5} / 5 ${LangManager.get('starsWord')}`;
    if (milestoneMsg) milestoneMsg.textContent = `${LangManager.get('onlyMore')} ${rem} ${LangManager.get('milestoneToPremium')}`;
  } else {
    if (progressBar)  progressBar.style.width = '100%';
    if (progressText) progressText.textContent = LangManager.get('maxTier');
    if (milestoneMsg) milestoneMsg.textContent = LangManager.get('milestoneMax');
  }

  // --- Tier locks ---
  updateTierStatus(approvedStars);

  // --- Status breakdown panel ---
  renderStatusBreakdown(pendingCount, underReview, approvedStars, rejectedCount);
}

function updateTierStatus(approvedStars) {
  const tier5  = document.getElementById('tier5');
  const tier10 = document.getElementById('tier10');
  if (tier5)  { tier5.classList.toggle('unlocked', approvedStars >= 5);  tier5.classList.toggle('locked', approvedStars < 5);  }
  if (tier10) { tier10.classList.toggle('unlocked', approvedStars >= 10); tier10.classList.toggle('locked', approvedStars < 10); }
}

// --- Status Breakdown: pending / under_review / approved / rejected ---
function renderStatusBreakdown(pending, underReview, approved, rejected) {
  const panel = document.getElementById('statusBreakdownPanel');
  if (!panel) return;

  // Only show panel if there's something interesting to display
  if (pending === 0 && underReview === 0 && rejected === 0) {
    panel.style.display = 'none';
    return;
  }
  panel.style.display = 'block';

  const title = panel.querySelector('.breakdown-title');
  if (title) title.textContent = LangManager.get('orderBreakdownTitle');

  const rows = [
    { id: 'bd-pending',      count: pending,     labelKey: 'pendingLabel',     icon: '⏳', cls: 'status-pending'   },
    { id: 'bd-review',       count: underReview, labelKey: 'underReviewLabel', icon: '🔍', cls: 'status-review'    },
    { id: 'bd-approved',     count: approved,    labelKey: 'approvedLabel',    icon: '⭐', cls: 'status-approved'  },
    { id: 'bd-rejected',     count: rejected,    labelKey: 'rejectedLabel',    icon: '❌', cls: 'status-rejected'  },
  ];

  rows.forEach(row => {
    const el = document.getElementById(row.id);
    if (!el) return;
    el.style.display = row.count > 0 ? 'flex' : 'none';
    const labelEl = el.querySelector('.bd-label');
    const countEl = el.querySelector('.bd-count');
    if (labelEl) labelEl.textContent = `${row.icon} ${LangManager.get(row.labelKey)}`;
    if (countEl) countEl.textContent = row.count;
  });

  // Contextual note for pending/under_review
  const noteEl = document.getElementById('statusNote');
  if (noteEl) {
    if (underReview > 0) {
      noteEl.textContent = LangManager.get('underReviewNote');
      noteEl.style.display = 'block';
    } else if (pending > 0) {
      noteEl.textContent = LangManager.get('pendingNote');
      noteEl.style.display = 'block';
    } else {
      noteEl.style.display = 'none';
    }
  }
}

// ===== FORM SUBMISSION =====
checkStarsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = checkEmailInput.value.trim();

  checkEmailError.classList.remove('show');
  checkEmailError.textContent = '';

  if (!email) {
    checkEmailError.textContent = LangManager.get('checkEmailError');
    checkEmailError.classList.add('show');
    checkEmailInput.focus();
    return;
  }
  if (!isValidEmail(email)) {
    checkEmailError.textContent = LangManager.get('checkEmailInvalid');
    checkEmailError.classList.add('show');
    checkEmailInput.focus();
    return;
  }
  if (isChecking) return;

  isChecking = true;
  showLoading();

  try {
    const response = await fetch('/api/get-stars', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await response.json();

    if (data.success) {
      if (data.found) {
        showResults(data);
      } else {
        showNoResults();
      }
    } else {
      showErrorState(data.error || 'Failed to fetch stars. Please try again.');
    }
  } catch (err) {
    showErrorState('An unexpected error occurred. Please try again later.');
  } finally {
    isChecking = false;
  }
});

// ===== EMAIL INPUT =====
checkEmailInput.addEventListener('blur', () => {
  const email = checkEmailInput.value.trim();
  if (email && !isValidEmail(email)) {
    checkEmailError.textContent = LangManager.get('checkEmailInvalid');
    checkEmailError.classList.add('show');
  } else {
    checkEmailError.classList.remove('show');
  }
});
checkEmailInput.addEventListener('input', () => checkEmailError.classList.remove('show'));

// ===== RESET =====
function resetCheck() {
  checkStarsForm.reset();
  hideAllSections();
  checkEmailInput.focus();
  checkEmailError.classList.remove('show');
}

// ===== KEYBOARD =====
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') checkStarsForm.dispatchEvent(new Event('submit'));
  if (e.key === 'Escape') resetCheck();
});

window.addEventListener('load', () => {
  console.log('Vistara Rewards v2 — Check Stars loaded');
});