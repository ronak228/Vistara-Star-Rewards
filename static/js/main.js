// ===== VISTARA REWARDS - MAIN PAGE JS =====

// Initialize language on load
document.addEventListener('DOMContentLoaded', () => {
  LangManager.init();
});

// ===== FORM ELEMENTS =====
const orderForm = document.getElementById('orderForm');
const submitBtn = document.getElementById('submitBtn');
const successModal = document.getElementById('successModal');
const errorModal = document.getElementById('errorModal');

let isSubmitting = false;

const nameInput = document.getElementById('name');
const emailInput = document.getElementById('email');
const orderIdInput = document.getElementById('order_id');
const orderScreenshotInput = document.getElementById('order_screenshot');
const ratingScreenshotInput = document.getElementById('rating_screenshot');

const nameError = document.getElementById('nameError');
const emailError = document.getElementById('emailError');
const orderIdError = document.getElementById('orderIdError');
const orderScreenshotError = document.getElementById('orderScreenshotError');

// ===== VALIDATION =====
function validateForm() {
  let isValid = true;
  clearErrors();

  if (!nameInput.value.trim()) {
    showError(nameError, LangManager.get('errNameRequired'));
    nameInput.focus();
    isValid = false;
  } else if (nameInput.value.trim().length < 2) {
    showError(nameError, LangManager.get('errNameShort'));
    nameInput.focus();
    isValid = false;
  }

  if (!emailInput.value.trim()) {
    showError(emailError, LangManager.get('errEmailRequired'));
    if (isValid) emailInput.focus();
    isValid = false;
  } else if (!isValidEmail(emailInput.value.trim())) {
    showError(emailError, LangManager.get('errEmailInvalid'));
    if (isValid) emailInput.focus();
    isValid = false;
  }

  if (!orderIdInput.value.trim()) {
    showError(orderIdError, LangManager.get('errOrderIdRequired'));
    if (isValid) orderIdInput.focus();
    isValid = false;
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

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidImage(file) {
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  const maxSize = 5 * 1024 * 1024;
  return validTypes.includes(file.type) && file.size <= maxSize;
}

function showError(element, message) {
  element.textContent = message;
  element.classList.add('show');
}

function clearErrors() {
  [nameError, emailError, orderIdError, orderScreenshotError].forEach(el => {
    el.textContent = '';
    el.classList.remove('show');
  });
}

// ===== FILE UPLOAD =====
function setupFileUpload(inputElement) {
  const uploadArea = inputElement.parentElement;

  ['dragenter', 'dragover'].forEach(e => {
    uploadArea.addEventListener(e, ev => {
      ev.preventDefault();
      ev.stopPropagation();
      uploadArea.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(e => {
    uploadArea.addEventListener(e, ev => {
      ev.preventDefault();
      ev.stopPropagation();
      uploadArea.classList.remove('drag-over');
    });
  });

  uploadArea.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      inputElement.files = files;
      updateFileDisplay(inputElement);
    }
  });

  uploadArea.addEventListener('click', () => inputElement.click());
}

function updateFileDisplay(inputElement) {
  const uploadArea = inputElement.parentElement;
  const uploadText = uploadArea.querySelector('.upload-text');
  const fileName = inputElement.files[0]?.name || '';
  if (fileName) {
    uploadText.textContent = `✓ ${fileName}`;
  }
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
      setTimeout(() => {
        updateFileDisplay(orderScreenshotInput);
        updateFileDisplay(ratingScreenshotInput);
      }, 100);
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

  // Apply i18n to modal
  document.getElementById('successModalTitle').textContent = LangManager.get('successTitle');
  document.getElementById('successModalMsg').textContent = LangManager.get('successMessage');
  document.getElementById('tokenLabelEl').textContent = LangManager.get('tokenLabel');
  document.getElementById('starsLabelEl').textContent = LangManager.get('starsLabel');
  document.getElementById('copyBtnEl').textContent = LangManager.get('copyBtn');
  document.getElementById('continueBtnEl').textContent = LangManager.get('continueBtn');
  document.getElementById('checkStarsBtnEl').textContent = LangManager.get('checkStarsBtn');

  successModal.classList.add('show');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  successModal.classList.remove('show');
  document.body.style.overflow = 'auto';
}

function showErrorModal(message) {
  document.getElementById('errorMessage').textContent = message;
  document.getElementById('errorModalTitle').textContent = LangManager.get('errorTitle');
  document.getElementById('tryAgainBtnEl').textContent = LangManager.get('tryAgainBtn');
  errorModal.classList.add('show');
  document.body.style.overflow = 'hidden';
}

function closeErrorModal() {
  errorModal.classList.remove('show');
  document.body.style.overflow = 'auto';
}

successModal.addEventListener('click', e => { if (e.target === successModal) closeModal(); });
errorModal.addEventListener('click', e => { if (e.target === errorModal) closeErrorModal(); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (successModal.classList.contains('show')) closeModal();
    if (errorModal.classList.contains('show')) closeErrorModal();
  }
});

// ===== COPY TOKEN =====
function copyToken() {
  const tokenText = document.getElementById('tokenValue').textContent;
  const copyBtn = document.getElementById('copyBtnEl');
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

// ===== REAL-TIME VALIDATION =====
nameInput.addEventListener('blur', () => {
  if (nameInput.value.trim() && nameInput.value.trim().length < 2) {
    showError(nameError, LangManager.get('errNameShort'));
  } else {
    nameError.classList.remove('show');
  }
});

emailInput.addEventListener('blur', () => {
  if (emailInput.value.trim() && !isValidEmail(emailInput.value.trim())) {
    showError(emailError, LangManager.get('errEmailInvalid'));
  } else {
    emailError.classList.remove('show');
  }
});

[nameInput, emailInput, orderIdInput].forEach(input => {
  input.addEventListener('input', () => {
    const err = document.getElementById(input.id + 'Error');
    if (err) err.classList.remove('show');
  });
});

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    if (validateForm()) orderForm.dispatchEvent(new Event('submit'));
  }
});

window.addEventListener('load', () => {
  console.log('Vistara Rewards - Homepage loaded');
});
