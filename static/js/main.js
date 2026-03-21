// ===== VISTARA REWARDS - MAIN PAGE JS =====

// ===== CONFIG — SET YOUR WHATSAPP NUMBER HERE =====
const WHATSAPP_NUMBER = '919876543210'; // ← Replace with your number (country code + number, no +)
const SHOP_NAME = 'Vistara Essentials';

document.addEventListener('DOMContentLoaded', () => {
  LangManager.init();
  setupWhatsAppButtons();
});

// ===== WHATSAPP BUTTON SETUP =====
function waLink(msg) {
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(msg)}`;
}

function setupWhatsAppButtons() {
  // Support button
  const supportBtn = document.getElementById('supportWhatsappBtn');
  if (supportBtn) {
    supportBtn.href = waLink(
      `Hi ${SHOP_NAME} Team! I need help with my reward.\nMy Token: [paste your token here]\nMy Email: [your email]`
    );
  }
  // Share button
  const shareBtn = document.getElementById('shareWhatsappBtn');
  if (shareBtn) {
    shareBtn.href = waLink(
      `I just rated ${SHOP_NAME} on Meesho! 🌟 Entering the lucky draw!\n[Attach your rating screenshot]`
    );
  }
}

// ===== MILESTONE WHATSAPP BANNER =====
function showMilestoneBanner(stars, token) {
  const banner  = document.getElementById('milestoneBanner');
  const emoji   = document.getElementById('milestoneEmoji');
  const title   = document.getElementById('milestoneTitle');
  const msg     = document.getElementById('milestoneMsg');
  const waBtn   = document.getElementById('milestoneWhatsapp');
  if (!banner) return;

  let milestoneHit = false;
  if (stars >= 10) {
    emoji.textContent  = '🏆';
    title.textContent  = LangManager.get('milestone10Title');
    msg.textContent    = LangManager.get('milestone10Msg');
    milestoneHit = true;
    waBtn.href = waLink(
      `🏆 I've reached 10 Stars on ${SHOP_NAME}!\nMy Token: ${token}\nPlease help me claim my PREMIUM PRIZE!`
    );
  } else if (stars >= 5) {
    emoji.textContent  = '🎉';
    title.textContent  = LangManager.get('milestone5Title');
    msg.textContent    = LangManager.get('milestone5Msg');
    milestoneHit = true;
    waBtn.href = waLink(
      `🎉 I've reached 5 Stars on ${SHOP_NAME}!\nMy Token: ${token}\nPlease help me claim my FREE GIFT!`
    );
  }

  if (milestoneHit) {
    banner.style.display = 'block';
    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Pulse animation
    banner.classList.add('milestone-pulse');
    setTimeout(() => banner.classList.remove('milestone-pulse'), 1500);
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
const orderIdInput          = document.getElementById('order_id');
const orderScreenshotInput  = document.getElementById('order_screenshot');
const ratingScreenshotInput = document.getElementById('rating_screenshot');

const nameError             = document.getElementById('nameError');
const emailError            = document.getElementById('emailError');
const orderIdError          = document.getElementById('orderIdError');
const orderScreenshotError  = document.getElementById('orderScreenshotError');

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
  [nameError, emailError, orderIdError, orderScreenshotError].forEach(clearError);
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

  const orderIdVal = orderIdInput.value.trim();
  if (!orderIdVal) {
    showError(orderIdError, LangManager.get('errOrderIdRequired'));
    if (isValid) orderIdInput.focus(); isValid = false;
  } else if (!isValidMeeshoOrderId(orderIdVal)) {
    showError(orderIdError, LangManager.get('errOrderIdInvalid'));
    if (isValid) orderIdInput.focus(); isValid = false;
  }

  if (!orderScreenshotInput.files.length) {
    showError(orderScreenshotError, LangManager.get('errScreenshotRequired'));
    isValid = false;
  } else if (!isValidImage(orderScreenshotInput.files[0])) {
    showError(orderScreenshotError, LangManager.get('errScreenshotInvalid'));
    isValid = false;
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

setupFileUpload(orderScreenshotInput);
setupFileUpload(ratingScreenshotInput);
orderScreenshotInput.addEventListener('change', () => updateFileDisplay(orderScreenshotInput));
ratingScreenshotInput.addEventListener('change', () => updateFileDisplay(ratingScreenshotInput));

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
      setTimeout(() => { updateFileDisplay(orderScreenshotInput); updateFileDisplay(ratingScreenshotInput); }, 100);
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
    if (totalStars >= 5) showMilestoneBanner(totalStars, token);
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

[nameInput, emailInput, orderIdInput].forEach(input => {
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