// ===== VISTARA REWARDS - MAIN PAGE JS =====

// ===== CONFIG — SET YOUR WHATSAPP NUMBER HERE =====
const WHATSAPP_NUMBER = '919054396696'; // Vistara Essentials WhatsApp
const SHOP_NAME = 'Vistara Essentials';

document.addEventListener('DOMContentLoaded', () => {
  LangManager.init();
  setupWhatsAppButtons();
  prewarmServer(); // Wake up Render + DB on page load so submit is instant
});

// ── PRE-WARM: ping server on page load so DB is ready when user submits ──
function prewarmServer() {
  fetch('/api/wake', { method: 'GET' })
    .then(r => r.json())
    .then(d => console.log('Server status:', d.status))
    .catch(() => {
      // Server still waking — retry after 8 seconds
      setTimeout(() => {
        fetch('/api/wake', { method: 'GET' }).catch(() => {});
      }, 8000);
    });
}

// ===== WHATSAPP SUPPORT POPUP =====
function waLink(msg) {
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(msg)}`;
}

function toggleSupportPopup() {
  const popup = document.getElementById('supportPopup');
  if (!popup) return;
  const isOpen = popup.style.display !== 'none';
  popup.style.display = isOpen ? 'none' : 'block';
}

// Close support popup when clicking outside
document.addEventListener('click', (e) => {
  const popup   = document.getElementById('supportPopup');
  const btn     = document.getElementById('floatingSupportBtn');
  if (!popup || !btn) return;
  if (popup.style.display !== 'none' && !popup.contains(e.target) && !btn.contains(e.target)) {
    popup.style.display = 'none';
  }
});

function setupWhatsAppButtons() {
  // Support popup quick buttons
  const q1 = document.getElementById('supportQuickBtn1');
  const q2 = document.getElementById('supportQuickBtn2');
  const q3 = document.getElementById('supportQuickBtn3');
  if (q1) q1.href = waLink(`Hi Vistara Essentials! My stars are not showing.\nMy Email: [your email]\nMy Token: [your token]\nPlease help me check my star status.`);
  if (q2) q2.href = waLink(`Hi Vistara Essentials! I have reached my reward milestone and want to claim my free product!\nMy Email: [your email]\nMy Token: [your token]\nPlease help me claim my reward.`);
  if (q3) q3.href = waLink(`Hi Vistara Essentials! I have a question about my order/reward.\nMy Email: [your email]\nMy Token: [your token]`);
}

// ===== CLAIM REWARD POPUP (5 or 10 stars) =====
function showClaimPopup(stars, token, name, email) {
  const overlay = document.getElementById('claimRewardOverlay');
  if (!overlay) return;

  // Populate user details
  document.getElementById('claimUserName').textContent  = name  || '—';
  document.getElementById('claimUserEmail').textContent = email || '—';
  document.getElementById('claimUserStars').textContent = `${stars} ⭐`;
  document.getElementById('claimUserToken').textContent = token || '—';

  let productName, productDesc, productEmoji, titleText, subtitleText, waMsg;

  if (stars >= 10) {
    titleText    = "🏆 You've reached 10 Stars!";
    subtitleText = "Your Premium Prize is ready to claim!";
    productEmoji = "🎀";
    productName  = "FREE Kids Clothing Set";
    productDesc  = "Worth ₹399 — our best reward, delivered free!";
    waMsg = `🏆 *Claiming 10-Star Premium Prize!*\n\n` +
            `Name: ${name || '—'}\n` +
            `Email: ${email || '—'}\n` +
            `Stars: ${stars} ⭐\n` +
            `Token: ${token || '—'}\n` +
            `Reward: FREE Kids Clothing Set (₹399)\n\n` +
            `Please confirm my claim and share delivery details. Thank you! 🙏`;
  } else {
    titleText    = "🎉 You've reached 5 Stars!";
    subtitleText = "Your FREE T-Shirt is ready to claim!";
    productEmoji = "👕";
    productName  = "FREE Boys T-Shirt";
    productDesc  = "Worth ₹199 — delivered free to your address!";
    waMsg = `🎉 *Claiming 5-Star Reward!*\n\n` +
            `Name: ${name || '—'}\n` +
            `Email: ${email || '—'}\n` +
            `Stars: ${stars} ⭐\n` +
            `Token: ${token || '—'}\n` +
            `Reward: FREE Boys T-Shirt (₹199)\n\n` +
            `Please confirm my claim and share delivery details. Thank you! 🙏`;
  }

  document.getElementById('claimEmoji').textContent        = stars >= 10 ? '🏆' : '🎉';
  document.getElementById('claimTitle').textContent        = titleText;
  document.getElementById('claimSubtitle').textContent     = subtitleText;
  document.getElementById('claimProductEmoji').textContent = productEmoji;
  document.getElementById('claimProductName').textContent  = productName;
  document.getElementById('claimProductDesc').textContent  = productDesc;
  document.getElementById('claimWhatsappLink').href        = waLink(waMsg);

  overlay.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeClaimPopup() {
  const overlay = document.getElementById('claimRewardOverlay');
  if (overlay) { overlay.style.display = 'none'; document.body.style.overflow = 'auto'; }
}

// Close claim popup on overlay click
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('claimRewardOverlay');
  if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay) closeClaimPopup(); });
});

// ===== MILESTONE BANNER (kept for backwards compat, now also triggers claim popup) =====
function showMilestoneBanner(stars, token, name, email) {
  const banner  = document.getElementById('milestoneBanner');
  const emoji   = document.getElementById('milestoneEmoji');
  const title   = document.getElementById('milestoneTitle');
  const msg     = document.getElementById('milestoneMsg');
  const waBtn   = document.getElementById('milestoneWhatsapp');
  if (!banner) return;

  let milestoneHit = false;
  if (stars >= 10) {
    if (emoji) emoji.textContent = '🏆';
    if (title) title.textContent = LangManager.get('milestone10Title');
    if (msg)   msg.textContent   = LangManager.get('milestone10Msg');
    milestoneHit = true;
  } else if (stars >= 5) {
    if (emoji) emoji.textContent = '🎉';
    if (title) title.textContent = LangManager.get('milestone5Title');
    if (msg)   msg.textContent   = LangManager.get('milestone5Msg');
    milestoneHit = true;
  }

  if (milestoneHit) {
    if (waBtn) waBtn.style.display = 'none'; // claim popup replaces this
    banner.style.display = 'block';
    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
    banner.classList.add('milestone-pulse');
    setTimeout(() => banner.classList.remove('milestone-pulse'), 1500);
    // Show claim popup after short delay
    setTimeout(() => showClaimPopup(stars, token, name, email), 800);
  }
}

// ===== FORM ELEMENTS =====
const orderForm              = document.getElementById('orderForm');
const submitBtn              = document.getElementById('submitBtn');
const successModal           = document.getElementById('successModal');
const errorModal             = document.getElementById('errorModal');
const orderIdConfirmModal    = document.getElementById('orderIdConfirmModal');

let isSubmitting = false;

const nameInput             = document.getElementById('name');
const emailInput            = document.getElementById('email');
const mobileInput           = document.getElementById('mobile_number');
const orderIdInput          = document.getElementById('order_id');

const nameError             = document.getElementById('nameError');
const emailError            = document.getElementById('emailError');
const mobileError           = document.getElementById('mobileError');
const orderIdError          = document.getElementById('orderIdError');

// ===== MEESHO ORDER ID VALIDATION =====
// Format: 15-19 digits, underscore, 1-2 digits  e.g. 265437129718567616_1
const MEESHO_ORDER_REGEX = /^\d{15,19}_\d{1,2}$/;

function isValidMeeshoOrderId(id) {
  return MEESHO_ORDER_REGEX.test(id.trim());
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim());
}

function isValidName(name) {
  return name.trim().length >= 2 &&
    /^[\u0900-\u097F\u0A00-\u0A7F\u0B00-\u0B7Fa-zA-Z\s.\-']+$/.test(name.trim());
}


function isValidMobile(mobile) {
  if (!mobile) return true; // optional field
  return /^[6-9][0-9]{9}$/.test(mobile.trim());
}

function isValidImage(file) {
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  const maxSize = 5 * 1024 * 1024;
  return validTypes.includes(file.type) && file.size <= maxSize;
}

// ===== ERROR HELPERS =====
function showError(element, message) {
  element.textContent = message;
  element.classList.add('show');
}

function clearError(element) {
  element.textContent = '';
  element.classList.remove('show');
}

function clearErrors() {
  [nameError, emailError, orderIdError, mobileError].forEach(clearError);
}

// ===== FULL FORM VALIDATION =====
function validateForm() {
  let isValid = true;
  clearErrors();

  const nameVal = nameInput.value.trim();
  if (!nameVal) {
    showError(nameError, LangManager.get('errNameRequired'));
    nameInput.focus(); isValid = false;
  } else if (nameVal.length < 2) {
    showError(nameError, LangManager.get('errNameShort'));
    nameInput.focus(); isValid = false;
  } else if (!isValidName(nameVal)) {
    showError(nameError, LangManager.get('errNameInvalid'));
    nameInput.focus(); isValid = false;
  }

  const emailVal = emailInput.value.trim();
  if (!emailVal) {
    showError(emailError, LangManager.get('errEmailRequired'));
    if (isValid) emailInput.focus(); isValid = false;
  } else if (!isValidEmail(emailVal)) {
    showError(emailError, LangManager.get('errEmailInvalid'));
    if (isValid) emailInput.focus(); isValid = false;
  }

  const mobileVal = mobileInput ? mobileInput.value.trim() : '';
  if (mobileVal && !isValidMobile(mobileVal)) {
    showError(mobileError, LangManager.get('errMobileInvalid'));
    isValid = false;
  }

  const orderIdVal = orderIdInput.value.trim();
  if (!orderIdVal) {
    showError(orderIdError, LangManager.get('errOrderIdRequired'));
    if (isValid) orderIdInput.focus(); isValid = false;
  } else if (!isValidMeeshoOrderId(orderIdVal)) {
    showError(orderIdError, LangManager.get('errOrderIdInvalid'));
    if (isValid) orderIdInput.focus(); isValid = false;
  }


  // Rating image is REQUIRED
  const ratingFile = document.getElementById('rating_image');
  const ratingErr  = document.getElementById('ratingImageError');
  if (!ratingFile || !ratingFile.files || ratingFile.files.length === 0) {
    if (ratingErr) { ratingErr.textContent = 'Please upload your Meesho rating screenshot — it is required.'; ratingErr.classList.add('show'); }
    // Scroll to upload area
    const area = document.getElementById('ratingUploadArea');
    if (area) area.scrollIntoView({ behavior: 'smooth', block: 'center' });
    isValid = false;
  } else if (!isValidImage(ratingFile.files[0])) {
    if (ratingErr) { ratingErr.textContent = 'Invalid file — use JPG/PNG/WEBP under 5MB.'; ratingErr.classList.add('show'); }
    isValid = false;
  } else {
    if (ratingErr) { ratingErr.textContent = ''; ratingErr.classList.remove('show'); }
  }

  return isValid;
}

// ===== ORDER ID BLUR → CONFIRM POPUP =====
orderIdInput.addEventListener('blur', () => {
  const val = orderIdInput.value.trim();
  if (!val) return;
  if (!isValidMeeshoOrderId(val)) {
    showError(orderIdError, LangManager.get('errOrderIdInvalid'));
    return;
  }
  clearError(orderIdError);
  showOrderIdConfirmPopup(val);
});

orderIdInput.addEventListener('input', () => clearError(orderIdError));

// ===== ORDER ID CONFIRM POPUP LOGIC =====
function showOrderIdConfirmPopup(orderId) {
  const modal = document.getElementById('orderIdConfirmModal');
  if (!modal) return;
  document.getElementById('confirmOrderIdDisplay').textContent = orderId;
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
}

function closeOrderIdConfirmModal() {
  const modal = document.getElementById('orderIdConfirmModal');
  if (modal) { modal.classList.remove('show'); document.body.style.overflow = 'auto'; }
}

// Block ghost clicks on upload areas after modal closes
let _modalJustClosed = false;

function confirmOrderId() {
  _modalJustClosed = true;
  closeOrderIdConfirmModal();
  setTimeout(() => { _modalJustClosed = false; }, 400);
}

function reenterOrderId() {
  _modalJustClosed = true;
  closeOrderIdConfirmModal();
  orderIdInput.value = '';
  orderIdInput.classList.remove('valid-input', 'invalid-input');
  setTimeout(() => { _modalJustClosed = false; orderIdInput.focus(); }, 400);
}

// ===== FILE UPLOAD =====
function setupFileUpload(inputElement) {
  const uploadArea = inputElement.parentElement;
  ['dragenter', 'dragover'].forEach(e => {
    uploadArea.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); uploadArea.classList.add('drag-over'); });
  });
  ['dragleave', 'drop'].forEach(e => {
    uploadArea.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); uploadArea.classList.remove('drag-over'); });
  });
  uploadArea.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) { inputElement.files = files; updateFileDisplay(inputElement); }
  });
  uploadArea.addEventListener('click', () => { if (_modalJustClosed) return; inputElement.click(); });
}

function updateFileDisplay(inputElement) {
  const uploadArea = inputElement.parentElement;
  const uploadText = uploadArea.querySelector('.upload-text');
  const fileName = inputElement.files[0]?.name || '';
  if (fileName) uploadText.textContent = `✓ ${fileName}`;
}

// File uploads removed — no screenshots needed

// ===== RATING IMAGE UPLOAD =====
(function () {
  const area  = document.getElementById('ratingUploadArea');
  const input = document.getElementById('rating_image');
  const text  = document.getElementById('ratingUploadText');
  if (!area || !input || !text) return;

  // Click to open file picker
  area.addEventListener('click', () => {
    if (_modalJustClosed) return;
    input.click();
  });

  // File selected
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    if (!isValidImage(file)) {
      text.innerHTML = '<div style="color:#c0392b;font-weight:600">❌ Invalid file — use JPG/PNG/WEBP under 5MB</div>';
      input.value = '';
      area.style.borderColor = '#c0392b';
      area.style.background  = '#fff5f5';
      return;
    }
    text.innerHTML = `
      <div style="font-size:1.5rem">✅</div>
      <div style="color:#27ae60;font-weight:600;font-size:13px">${file.name}</div>
      <div style="font-size:11px;color:#888;margin-top:2px">Tap to change</div>`;
    area.style.borderColor = '#27ae60';
    area.style.background  = '#f0fdf4';
  });

  // Drag & drop
  ['dragenter', 'dragover'].forEach(e =>
    area.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); area.style.background = '#fff3d0'; })
  );
  ['dragleave', 'drop'].forEach(e =>
    area.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); })
  );
  area.addEventListener('drop', ev => {
    const files = ev.dataTransfer.files;
    if (files.length > 0) {
      // Assign to input and fire change
      const dt = new DataTransfer();
      dt.items.add(files[0]);
      input.files = dt.files;
      input.dispatchEvent(new Event('change'));
    }
  });
})();

// ===== FORM SUBMISSION =====
orderForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validateForm() || isSubmitting) return;

  isSubmitting = true;
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner-sm"></span><span>${LangManager.get('submitting')}</span>`;

  try {
    const formData = new FormData(orderForm);
    const response = await fetch('/api/submit', { method: 'POST', body: formData });
    const data = await response.json();

    if (data.success) {
      showSuccessModal(data.token, data.total_stars);
      orderForm.reset();
      clearErrors();

    } else {
      showErrorModal(data.error || 'Submission failed. Please try again.');
    }
  } catch (err) {
    showErrorModal('An unexpected error occurred. Please try again later.');
  } finally {
    isSubmitting = false;
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<span>${LangManager.get('submitBtn')}</span>`;
  }
});

// ===== MODALS =====
function showSuccessModal(token, totalStars) {
  const name  = nameInput  ? nameInput.value.trim()  : '';
  const email = emailInput ? emailInput.value.trim() : '';
  document.getElementById('tokenValue').textContent = token;
  let displayStars = '';
  for (let i = 0; i < Math.min(totalStars, 10); i++) displayStars += '⭐';
  document.getElementById('starsCount').textContent = displayStars || '⭐';
  document.getElementById('successModalTitle').textContent = LangManager.get('successTitle');
  document.getElementById('successModalMsg').textContent   = LangManager.get('successMessage');
  document.getElementById('tokenLabelEl').textContent      = LangManager.get('tokenLabel');
  document.getElementById('starsLabelEl').textContent      = LangManager.get('starsLabel');
  document.getElementById('copyBtnEl').textContent         = LangManager.get('copyBtn');
  document.getElementById('continueBtnEl').textContent     = LangManager.get('continueBtn');
  document.getElementById('checkStarsBtnEl').textContent   = LangManager.get('checkStarsBtn');
  successModal.classList.add('show');
  document.body.style.overflow = 'hidden';
  // Check for milestone after showing modal
  setTimeout(() => {
    if (totalStars >= 5) showMilestoneBanner(totalStars, token, name, email);
  }, 1500);
}

function closeModal() { successModal.classList.remove('show'); document.body.style.overflow = 'auto'; }
function showErrorModal(message) {
  document.getElementById('errorMessage').textContent    = message;
  document.getElementById('errorModalTitle').textContent = LangManager.get('errorTitle');
  document.getElementById('tryAgainBtnEl').textContent   = LangManager.get('tryAgainBtn');
  errorModal.classList.add('show'); document.body.style.overflow = 'hidden';
}
function closeErrorModal() { errorModal.classList.remove('show'); document.body.style.overflow = 'auto'; }

successModal.addEventListener('click', e => { if (e.target === successModal) closeModal(); });
errorModal.addEventListener('click',   e => { if (e.target === errorModal) closeErrorModal(); });

document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  if (successModal.classList.contains('show'))     closeModal();
  if (errorModal.classList.contains('show'))       closeErrorModal();
  if (orderIdConfirmModal && orderIdConfirmModal.classList.contains('show')) closeOrderIdConfirmModal();
});

// ===== COPY TOKEN =====
function copyToken() {
  const tokenText = document.getElementById('tokenValue').textContent;
  const copyBtn   = document.getElementById('copyBtnEl');
  navigator.clipboard.writeText(tokenText).then(() => {
    copyBtn.textContent = LangManager.get('copied');
    setTimeout(() => { copyBtn.textContent = LangManager.get('copyBtn'); }, 2000);
  }).catch(() => {
    copyBtn.textContent = 'Copy failed';
    setTimeout(() => { copyBtn.textContent = LangManager.get('copyBtn'); }, 2000);
  });
}

// ===== SCROLL TO FORM =====
function scrollToForm() {
  document.getElementById('formSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
  setTimeout(() => { nameInput.focus(); }, 600);
}

// ===== REAL-TIME BLUR VALIDATION =====
nameInput.addEventListener('blur', () => {
  const val = nameInput.value.trim();
  if (!val) return;
  if (val.length < 2) showError(nameError, LangManager.get('errNameShort'));
  else if (!isValidName(val)) showError(nameError, LangManager.get('errNameInvalid'));
  else clearError(nameError);
});

emailInput.addEventListener('blur', () => {
  const val = emailInput.value.trim();
  if (!val) return;
  if (!isValidEmail(val)) showError(emailError, LangManager.get('errEmailInvalid'));
  else clearError(emailError);
});

[nameInput, emailInput, mobileInput, orderIdInput].forEach(input => {
  input.addEventListener('input', () => {
    const err = document.getElementById(input.id + 'Error');
    if (err) clearError(err);
  });
});

window.addEventListener('load', () => console.log('Vistara Rewards - Homepage loaded'));

// ===== LIVE ORDER ID FORMAT FEEDBACK =====
// Show green/red border while typing so user knows instantly
orderIdInput.addEventListener('input', () => {
  const val = orderIdInput.value.trim();
  clearError(orderIdError);
  if (!val) {
    orderIdInput.classList.remove('valid-input', 'invalid-input');
    return;
  }
  if (isValidMeeshoOrderId(val)) {
    orderIdInput.classList.add('valid-input');
    orderIdInput.classList.remove('invalid-input');
  } else {

    // Only show red after user has typed something substantial
    if (val.length >= 5) {
      orderIdInput.classList.add('invalid-input');
      orderIdInput.classList.remove('valid-input');
    }
  }
});