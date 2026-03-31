// ===== VISTARA REWARDS - TRANSLATIONS =====
// Centralized translation file for English and Hindi

const translations = {
  en: {
    // Navigation
    navHome: "Home",
    navCheckStars: "Check Stars",
    langToggle: "हिंदी",

    // Hero Section
    heroTitle1: "Unlock Your",
    heroHighlight: "Reward Stars",
    heroSubtitle: "Every Meesho order earns 1 star. Collect 5 stars → get a FREE Boys T-Shirt (₹199 value)!",
    heroCta: "Submit Your Order",

    // Hero Badges
    badge1: "1 Order = 1 Star",
    badge2: "5 Stars = Free T-Shirt",
    badge3: "Secure & Verified",

    // How It Works
    howItWorksTitle: "How It Works",
    howCard1Title: "1 Order = 1 Star",
    howCard1Desc: "Every purchase you make earns you one reward star",
    howCard2Title: "5 Stars = Free T-Shirt",
    howCard2Desc: "Collect 5 stars → claim a FREE Boys T-Shirt (₹199 value) delivered to you",
    howCard3Title: "10 Stars = Premium Set",
    howCard3Desc: "10 stars → get a FREE Kids Clothing Set (₹399 value) — our best reward!",

    // Form Section
    formTitle: "Submit Your Order",
    formSubtitle: "Quick and easy – takes less than 2 minutes",
    labelName: "Your Name",
    labelEmail: "Email Address",
    labelMobile: "Mobile Number",
    placeholderMobile: "e.g., 9876543210",
    mobileHint: "Optional — only used to contact you about your reward if needed 🔒",
    errMobileInvalid: "Please enter a valid 10-digit Indian mobile number",
    labelOrderId: "Order ID",
    labelOrderScreenshot: "Order Screenshot",
    labelRatingScreenshot: "Rating Screenshot",
    optional: "(Optional)",
    required: "*",
    placeholderName: "e.g., Priya Sharma",
    placeholderEmail: "your.email@example.com",
    placeholderOrderId: "e.g., 265437129718567616_1",
    orderIdHint: "Find this in Meesho app → My Orders → tap order → Order ID (e.g., 265437129718567616_1)",
    uploadText: "Tap to upload screenshot",
    uploadHint: "PNG, JPG or GIF (max. 5MB)",
    submitBtn: "Unlock My Stars ⭐",
    submitting: "Processing...",

    // Validation Errors
    errNameRequired: "Name is required",
    errNameShort: "Name must be at least 2 characters",
    errEmailRequired: "Email is required",
    errEmailInvalid: "Please enter a valid email address",
    errOrderIdRequired: "Order ID is required",
    errOrderIdInvalid: "Invalid Order ID format. Meesho Order IDs look like: 265437129718567616_1 (15-19 digits, underscore, 1-2 digits). Please check and re-enter.",
    errNameInvalid: "Name can only contain letters and spaces",
    orderIdConfirmTitle: "Confirm Your Order ID",
    orderIdConfirmMsg: "Please verify this is the exact Order ID from your Meesho app. A wrong ID means no star will be given.",
    orderIdConfirmWarning: "⚠️ Wrong Order ID = No Star — please double-check!",
    orderIdYesCorrect: "Yes, it's correct ✓",
    orderIdReenter: "Re-enter Order ID",
    errScreenshotRequired: "Order screenshot is required",
    errScreenshotInvalid: "Please upload a valid image file (max 5MB)",

    // Success Modal
    successTitle: "Submission Received!",
    successMessage: "Your order has been successfully submitted.",
    tokenLabel: "Your Reward Token",
    starsLabel: "Total Stars Earned",
    copyBtn: "Copy",
    copied: "✓ Copied!",
    continueBtn: "Continue Shopping",
    checkStarsBtn: "Check My Stars",

    // Error Modal
    errorTitle: "Submission Failed",
    tryAgainBtn: "Try Again",

    // Trust Section
    trustTitle: "Why Trust Vistara Essentials?",
    trust1Title: "Safe & Secure",
    trust1Desc: "Your data is encrypted and protected with industry-standard security",
    trust2Title: "Real Buyers, Real Rewards",
    trust2Desc: "Every reward is personally sent by us — no middleman, no fake promises",
    trust3Title: "Verified Rewards",
    trust3Desc: "100% authentic rewards program backed by Vistara Essentials",

    // Footer
    footerCopy: "© 2025 Vistara Essentials. All rights reserved.",
    privacyPolicy: "Privacy Policy",
    termsOfService: "Terms of Service",
    contactUs: "Contact Us",

    // Check Stars Page
    checkStarsTitle: "Check Your Stars",
    checkStarsSubtitle: "Enter your email to see how many reward stars you've earned",
    checkEmailLabel: "Email Address",
    checkBtn: "Check My Stars",
    checkEmailError: "Please enter your email address",
    checkEmailInvalid: "Please enter a valid email address",

    // Results
    resultLabel: "Your Total Stars",
    progressLabel: "Progress to Next Reward",
    milestoneToFree: "more to unlock your free gift! 🎁",
    milestoneToPremium: "more to unlock the premium gift! 🎉",
    milestoneMax: "Congratulations! You have unlocked all rewards! 🏆",
    tiersTitle: "Reward Tiers",
    tier5Name: "5 Stars",
    tier5Reward: "Free Gift",
    tier10Name: "10 Stars",
    tier10Reward: "Premium Gift",
    starWord: "Star",
    starsWord: "Stars",
    onlyMore: "Only",

    // No Results
    noResultsTitle: "No Account Found",
    noResultsText: "We couldn't find any orders associated with this email address.",
    submitFirstOrder: "Submit Your First Order",

    // Error Section
    errorSectionTitle: "Something Went Wrong",
    errorSectionDefault: "Please try again later",
    tryAgain: "Try Again",

    // Loading
    loadingText: "Checking your stars...",

    // Maximize Rewards
    maximizeTitle: "How to Maximize Your Rewards",
    step1Title: "Submit Order Details",
    step1Desc: "Upload your order confirmation and rating screenshots",
    step2Title: "Earn Stars",
    step2Desc: "Get 1 star for every verified purchase",
    step3Title: "Claim Rewards",
    step3Desc: "Trade your stars for exclusive gifts and offers",

    // CTA
    submitAnother: "Submit Another Order",

    // Language Popup
    popupTitle: "Select Language",
    popupSubtitle: "भाषा चुनें",
    popupEnglish: "English",
    popupHindi: "हिंदी",

    // Maximum
    maxTier: "Maximum Tier Reached!",

    // Order status breakdown (v2)
    statusApproved:       "Confirmed Stars",
    statusPending:        "Awaiting Delivery Confirmation",
    statusUnderReview:    "Delivery Confirmed — In Cooling Period",
    statusRejected:       "Rejected Orders",
    pendingNote:          "⏳ Your order is being verified. Stars are added once delivery is confirmed.",
    underReviewNote:      "🔍 Delivery confirmed! Your star will be credited within 7 days.",
    pendingLabel:         "Pending",
    underReviewLabel:     "Under Review",
    approvedLabel:        "Approved",
    rejectedLabel:        "Rejected",
    orderBreakdownTitle:  "Order Status Breakdown",
    // ── Return Warning ────────────────────────────────────────────────
    returnWarnTitle: "⚠️ Important: Returns = No Star",
    returnWarnDesc:  "If you return or cancel this order, your star will NOT be counted — even if already submitted. Only completed, kept orders earn stars.",


    // ── Steps / How It Works ──────────────────────────────────────────
    stepsTitle:    "How to Earn Stars & Win Prizes",
    stepsSubtitle: "Follow these 4 simple steps",
    step1Title:    "Follow Our Shop",
    step1Desc:     "Find and follow Vistara Essentials on Meesho. Tap the link below to visit our store",
    step2Title:    "Place Your Order",
    step2Desc:     "Order any product from our Meesho store and submit the Order ID here after purchase",
    step3Title:    "Get Your Star",
    step3Desc:     "Submit your Order ID here. After delivery is confirmed, your star is added within 7 days",
    step4Title:    "Win Amazing Prizes",
    step4Desc:     "5 Stars = Free T-Shirt 🎁  |  10 Stars = Free Clothing Set 🏆  |  Rate us on Meesho to enter monthly lucky draw!",
    shopUrl:       "https://www.meesho.com/VistaraEssentials?_ms=3.0.1",
    visitShop:     "Visit Our Meesho Store →",

    // ── Share & Win ───────────────────────────────────────────────────
    shareTitle:    "Rate Us on Meesho & Win!",
    shareDesc:     "Give us a 5⭐ rating on Meesho, upload the screenshot below — we pick 1 winner every month and send a FREE product worth ₹199 to their address!",
    prize1:        "🎁 Winner gets a FREE Boys T-Shirt delivered",
    prize2:        "🗓️ 1 winner picked every month",
    prize3:        "📲 Upload rating screenshot to enter",
    shareWhatsapp: "📲 Upload Rating Screenshot to Enter Draw",

    // ── Support / Contact ─────────────────────────────────────────────
    supportTitle:      "Need Help? Contact Us on WhatsApp",
    supportDesc:       "Stars not showing after 7 days of delivery? Or reached 5/10 stars and ready to claim your free product? Message us on WhatsApp with your token",
    supportTokenLabel: "Your Reward Token",
    supportStep1:      "After submitting, you receive a Reward Token (e.g. VST-1234) — save it",
    supportStep2:      "Open WhatsApp → tap our number → send your Token + Email",
    supportStep3:      "We verify within 24 hours and process your reward or star credit",
    contactWhatsapp:   "💬 Chat on WhatsApp Now",
    claimWhatsapp:     "🎁 Claim My Reward on WhatsApp",

    // ── Milestone banner ──────────────────────────────────────────────
    milestone5Title: "🎉 You've Reached 5 Stars!",
    milestone5Msg:   "Your FREE Boys T-Shirt (₹199) is ready! Tap below to claim via WhatsApp",
    milestone10Title:"🏆 You've Reached 10 Stars!",
    milestone10Msg:  "Your FREE Kids Clothing Set (₹399) is ready! Tap below to claim via WhatsApp",

  },

  hi: {
    // Navigation
    navHome: "होम",
    navCheckStars: "स्टार देखें",
    langToggle: "English",

    // Hero Section
    heroTitle1: "पाएं अपने",
    heroHighlight: "रिवॉर्ड स्टार",
    heroSubtitle: "हर Meesho ऑर्डर पर 1 स्टार। 5 स्टार इकट्ठा करें → मुफ्त बॉयज़ टी-शर्ट पाएं (₹199 की कीमत)!",
    heroCta: "ऑर्डर जमा करें",

    // Hero Badges
    badge1: "1 ऑर्डर = 1 स्टार",
    badge2: "5 स्टार = फ्री टी-शर्ट",
    badge3: "सुरक्षित और सत्यापित",

    // How It Works
    howItWorksTitle: "यह कैसे काम करता है",
    howCard1Title: "1 ऑर्डर = 1 स्टार",
    howCard1Desc: "हर खरीदारी पर आपको एक रिवॉर्ड स्टार मिलता है",
    howCard2Title: "5 स्टार = फ्री टी-शर्ट",
    howCard2Desc: "5 स्टार इकट्ठा करें → मुफ्त बॉयज़ टी-शर्ट (₹199) घर पर डिलीवर होगी",
    howCard3Title: "10 स्टार = प्रीमियम सेट",
    howCard3Desc: "10 स्टार → मुफ्त किड्स क्लोदिंग सेट (₹399) — हमारा सबसे बड़ा इनाम!",

    // Form Section
    formTitle: "अपना ऑर्डर जमा करें",
    formSubtitle: "आसान और जल्दी – 2 मिनट से कम समय",
    labelName: "आपका नाम",
    labelEmail: "ईमेल पता",
    labelMobile: "मोबाइल नंबर",
    placeholderMobile: "जैसे: 9876543210",
    mobileHint: "वैकल्पिक — केवल आपके रिवॉर्ड के बारे में जरूरत पड़ने पर संपर्क करने के लिए 🔒",
    errMobileInvalid: "कृपया एक वैध 10 अंकों का भारतीय मोबाइल नंबर दर्ज करें",
    labelOrderId: "ऑर्डर ID",
    labelOrderScreenshot: "ऑर्डर स्क्रीनशॉट",
    labelRatingScreenshot: "रेटिंग स्क्रीनशॉट",
    optional: "(वैकल्पिक)",
    required: "*",
    placeholderName: "जैसे: प्रिया शर्मा",
    placeholderEmail: "your.email@example.com",
    placeholderOrderId: "जैसे: 265437129718567616_1",
    orderIdHint: "Meesho ऐप → मेरे ऑर्डर → ऑर्डर पर टैप करें → ऑर्डर ID (जैसे: 265437129718567616_1)",
    uploadText: "स्क्रीनशॉट अपलोड करें",
    uploadHint: "PNG, JPG या GIF (अधिकतम 5MB)",
    submitBtn: "मेरे स्टार अनलॉक करें ⭐",
    submitting: "जमा हो रहा है...",

    // Validation Errors
    errNameRequired: "नाम आवश्यक है",
    errNameShort: "नाम कम से कम 2 अक्षर का होना चाहिए",
    errEmailRequired: "ईमेल आवश्यक है",
    errEmailInvalid: "कृपया एक वैध ईमेल दर्ज करें",
    errOrderIdRequired: "ऑर्डर ID आवश्यक है",
    errOrderIdInvalid: "ऑर्डर ID का फ़ॉर्मेट गलत है। Meesho ऑर्डर ID ऐसी होती है: 265437129718567616_1 (15-19 अंक, अंडरस्कोर, 1-2 अंक)। कृपया जांचें और दोबारा दर्ज करें।",
    errNameInvalid: "नाम में केवल अक्षर और स्पेस हो सकते हैं",
    orderIdConfirmTitle: "ऑर्डर ID की पुष्टि करें",
    orderIdConfirmMsg: "कृपया जांचें कि यह आपके Meesho ऐप का सही ऑर्डर ID है। गलत ID पर कोई स्टार नहीं मिलेगा।",
    orderIdConfirmWarning: "⚠️ गलत ऑर्डर ID = कोई स्टार नहीं — कृपया ध्यान से जांचें!",
    orderIdYesCorrect: "हाँ, यह सही है ✓",
    orderIdReenter: "ऑर्डर ID फिर से दर्ज करें",
    errScreenshotRequired: "ऑर्डर स्क्रीनशॉट आवश्यक है",
    errScreenshotInvalid: "कृपया एक वैध इमेज फ़ाइल अपलोड करें (अधिकतम 5MB)",

    // Success Modal
    successTitle: "जमा हो गया!",
    successMessage: "आपका ऑर्डर सफलतापूर्वक जमा हो गया।",
    tokenLabel: "आपका रिवॉर्ड टोकन",
    starsLabel: "अर्जित कुल स्टार",
    copyBtn: "कॉपी करें",
    copied: "✓ कॉपी हो गया!",
    continueBtn: "शॉपिंग जारी रखें",
    checkStarsBtn: "मेरे स्टार देखें",

    // Error Modal
    errorTitle: "जमा नहीं हो सका",
    tryAgainBtn: "पुनः प्रयास करें",

    // Trust Section
    trustTitle: "Vistara Essentials पर भरोसा क्यों?",
    trust1Title: "सुरक्षित और भरोसेमंद",
    trust1Desc: "आपका डेटा एन्क्रिप्टेड और सुरक्षित है",
    trust2Title: "असली खरीदार, असली इनाम",
    trust2Desc: "हर रिवॉर्ड हम खुद भेजते हैं — कोई बिचौलिया नहीं, कोई झूठा वादा नहीं",
    trust3Title: "सत्यापित रिवॉर्ड",
    trust3Desc: "Vistara Essentials का 100% प्रामाणिक रिवॉर्ड प्रोग्राम",

    // Footer
    footerCopy: "© 2025 Vistara Essentials. सर्वाधिकार सुरक्षित।",
    privacyPolicy: "गोपनीयता नीति",
    termsOfService: "सेवा की शर्तें",
    contactUs: "संपर्क करें",

    // Check Stars Page
    checkStarsTitle: "अपने स्टार देखें",
    checkStarsSubtitle: "अपना ईमेल दर्ज करें और देखें आपने कितने रिवॉर्ड स्टार कमाए हैं",
    checkEmailLabel: "ईमेल पता",
    checkBtn: "मेरे स्टार देखें",
    checkEmailError: "कृपया अपना ईमेल दर्ज करें",
    checkEmailInvalid: "कृपया एक वैध ईमेल दर्ज करें",

    // Results
    resultLabel: "आपके कुल स्टार",
    progressLabel: "अगले रिवॉर्ड तक की प्रगति",
    milestoneToFree: "और स्टार से फ्री गिफ्ट मिलेगा! 🎁",
    milestoneToPremium: "और स्टार से प्रीमियम गिफ्ट मिलेगा! 🎉",
    milestoneMax: "बधाई हो! आपने सभी रिवॉर्ड अनलॉक कर लिए! 🏆",
    tiersTitle: "रिवॉर्ड स्तर",
    tier5Name: "5 स्टार",
    tier5Reward: "फ्री बॉयज़ टी-शर्ट (₹199)",
    tier10Name: "10 स्टार",
    tier10Reward: "फ्री किड्स क्लोदिंग सेट (₹399)",
    starWord: "स्टार",
    starsWord: "स्टार",
    onlyMore: "केवल",

    // No Results
    noResultsTitle: "कोई अकाउंट नहीं मिला",
    noResultsText: "इस ईमेल से जुड़ा कोई ऑर्डर नहीं मिला।",
    submitFirstOrder: "पहला ऑर्डर जमा करें",

    // Error Section
    errorSectionTitle: "कुछ गलत हुआ",
    errorSectionDefault: "कृपया बाद में पुनः प्रयास करें",
    tryAgain: "पुनः प्रयास करें",

    // Loading
    loadingText: "आपके स्टार देखे जा रहे हैं...",

    // Maximize Rewards
    maximizeTitle: "रिवॉर्ड अधिकतम कैसे करें",
    step1Title: "ऑर्डर विवरण जमा करें",
    step1Desc: "अपने ऑर्डर कन्फर्मेशन और रेटिंग स्क्रीनशॉट अपलोड करें",
    step2Title: "स्टार कमाएं",
    step2Desc: "हर सत्यापित खरीदारी पर 1 स्टार पाएं",
    step3Title: "रिवॉर्ड पाएं",
    step3Desc: "अपने स्टार को एक्सक्लूसिव गिफ्ट और ऑफर से बदलें",

    // CTA
    submitAnother: "एक और ऑर्डर जमा करें",

    // Language Popup
    popupTitle: "Select Language",
    popupSubtitle: "भाषा चुनें",
    popupEnglish: "English",
    popupHindi: "हिंदी",

    // Maximum
    maxTier: "अधिकतम स्तर प्राप्त!",

    // Order status breakdown (v2)
    statusApproved:       "पुष्टि किए गए स्टार",
    statusPending:        "डिलीवरी पुष्टि का इंतज़ार",
    statusUnderReview:    "डिलीवरी हुई — कूलिंग पीरियड में",
    statusRejected:       "अस्वीकृत ऑर्डर",
    pendingNote:          "⏳ आपका ऑर्डर सत्यापित हो रहा है। डिलीवरी पुष्टि के बाद स्टार मिलेंगे।",
    underReviewNote:      "🔍 डिलीवरी कन्फर्म! आपका स्टार 7 दिन में मिलेगा।",
    pendingLabel:         "लंबित",
    underReviewLabel:     "समीक्षा में",
    approvedLabel:        "स्वीकृत",
    rejectedLabel:        "अस्वीकृत",
    orderBreakdownTitle:  "ऑर्डर स्थिति विवरण",
    // ── Return Warning ────────────────────────────────────────────────
    returnWarnTitle: "⚠️ ज़रूरी बात: रिटर्न करने पर स्टार नहीं मिलेगा",
    returnWarnDesc:  "अगर आप यह ऑर्डर रिटर्न या कैंसिल करते हैं, तो स्टार नहीं मिलेगा — चाहे यहाँ सबमिट किया हो। केवल डिलीवर्ड और रखे गए ऑर्डर पर ही स्टार मिलते हैं।",


    // ── Steps / How It Works ──────────────────────────────────────────
    stepsTitle:    "स्टार कमाएं और पुरस्कार जीतें",
    stepsSubtitle: "इन 4 आसान चरणों का पालन करें",
    step1Title:    "हमारी दुकान फॉलो करें",
    step1Desc:     "Meesho पर Vistara Essentials को फॉलो करें। हमारी स्टोर देखने के लिए नीचे टैप करें",
    step2Title:    "ऑर्डर करें",
    step2Desc:     "हमारी Meesho स्टोर से कोई भी प्रोडक्ट ऑर्डर करें और खरीदारी के बाद यहाँ ऑर्डर ID जमा करें",
    step3Title:    "स्टार पाएं",
    step3Desc:     "यहाँ ऑर्डर ID जमा करें। डिलीवरी कन्फर्म होने के 7 दिन में स्टार मिलेगा",
    step4Title:    "अमेज़िंग पुरस्कार जीतें",
    step4Desc:     "5 स्टार = फ्री टी-शर्ट 🎁  |  10 स्टार = फ्री क्लोदिंग सेट 🏆  |  Meesho पर रेटिंग दें → मंथली लकी ड्रा में शामिल हों!",
    shopUrl:       "https://www.meesho.com/VistaraEssentials?_ms=3.0.1",
    visitShop:     "हमारी Meesho स्टोर देखें →",

    // ── Share & Win ───────────────────────────────────────────────────
    shareTitle:    "Meesho पर रेटिंग दें और जीतें!",
    shareDesc:     "Meesho पर 5⭐ रेटिंग दें, नीचे स्क्रीनशॉट अपलोड करें — हम हर महीने 1 विजेता को उनके पते पर मुफ्त प्रोडक्ट (₹199) भेजते हैं!",
    prize1:        "🎁 विजेता को फ्री बॉयज़ टी-शर्ट डिलीवर होगी",
    prize2:        "🗓️ हर महीने 1 विजेता चुना जाता है",
    prize3:        "📲 रेटिंग स्क्रीनशॉट अपलोड करें और शामिल हों",
    shareWhatsapp: "📲 रेटिंग स्क्रीनशॉट अपलोड करें",

    // ── Support / Contact ─────────────────────────────────────────────
    supportTitle:      "मदद चाहिए? WhatsApp पर हमसे बात करें",
    supportDesc:       "डिलीवरी के 7 दिन बाद भी स्टार नहीं आया? या 5/10 स्टार पूरे हो गए और फ्री प्रोडक्ट क्लेम करना है? टोकन लेकर WhatsApp पर मैसेज करें",
    supportTokenLabel: "आपका रिवॉर्ड टोकन",
    supportStep1:      "सबमिट करने के बाद आपको एक रिवॉर्ड टोकन मिलेगा (जैसे VST-1234) — इसे सेव करें",
    supportStep2:      "WhatsApp खोलें → हमारा नंबर टैप करें → टोकन + ईमेल भेजें",
    supportStep3:      "हम 24 घंटे में वेरीफाई करके आपका रिवॉर्ड या स्टार प्रोसेस करेंगे",
    contactWhatsapp:   "💬 अभी WhatsApp पर चैट करें",
    claimWhatsapp:     "🎁 WhatsApp पर रिवॉर्ड क्लेम करें",

    // ── Milestone banner ──────────────────────────────────────────────
    milestone5Title: "🎉 आपने 5 स्टार पा लिए!",
    milestone5Msg:   "आपकी फ्री बॉयज़ टी-शर्ट (₹199) तैयार है! WhatsApp पर क्लेम करें",
    milestone10Title:"🏆 आपने 10 स्टार पा लिए!",
    milestone10Msg:  "आपका फ्री किड्स क्लोदिंग सेट (₹399) तैयार है! WhatsApp पर क्लेम करें",

  },
    // Steps section
    stepsTitle: "ज़्यादा स्टार और पुरस्कार कैसे जीतें",
    stepsSubtitle: "इन चरणों का पालन करें और तेज़ी से रिवॉर्ड पाएं",
    step1Title: "हमारी दुकान से ऑर्डर करें",
    step1Desc: "Meesho पर Vistara Essentials से खरीदारी करें और यहाँ ऑर्डर ID जमा करके 1 स्टार कमाएं",
    step2Title: "ऑर्डर स्क्रीनशॉट अपलोड करें",
    step2Desc: "अपने कन्फर्म ऑर्डर का स्क्रीनशॉट लें और जमा करते समय अपलोड करें। डिलीवरी वेरीफाई होने के बाद स्टार मिलेंगे",
    step3Title: "हमारे प्रोडक्ट को रेट करें",
    step3Desc: "Meesho पर 5-स्टार रेटिंग दें और रेटिंग स्क्रीनशॉट अपलोड करें — इससे आप हमारे मंथली लकी ड्रा में शामिल हो जाते हैं!",
    step4Title: "अपना रिवॉर्ड क्लेम करें",
    step4Desc: "5 स्टार पर फ्री गिफ्ट और 10 स्टार पर प्रीमियम पुरस्कार। अपना टोकन लेकर WhatsApp पर हमसे संपर्क करें",

    // Share & Win
    shareTitle: "Meesho पर रेटिंग दें और जीतें!",
    shareDesc: "Meesho पर 5⭐ रेटिंग दें, नीचे स्क्रीनशॉट अपलोड करें — हम हर महीने 1 विजेता को मुफ्त प्रोडक्ट (₹199) भेजते हैं!",
    prize1: "🎁 विजेता को फ्री बॉयज़ टी-शर्ट डिलीवर होगी",
    prize2: "🗓️ हर महीने 1 विजेता चुना जाता है",
    prize3: "📲 रेटिंग स्क्रीनशॉट अपलोड करें और शामिल हों",
    shareWhatsapp: "📲 रेटिंग स्क्रीनशॉट अपलोड करें",

    // Support section
    supportTitle: "मदद चाहिए? हम यहाँ हैं!",
    supportDesc: "अपना रिवॉर्ड टोकन तैयार रखें और WhatsApp पर हमसे संपर्क करें। हम 24 घंटे में आपका रिवॉर्ड प्रोसेस करेंगे",
    supportStep1: "कन्फर्मेशन स्क्रीन से अपना रिवॉर्ड टोकन कॉपी करें",
    supportStep2: "WhatsApp खोलें और टोकन + ईमेल भेजें",
    supportStep3: "हम 24 घंटे में आपका रिवॉर्ड वेरीफाई और प्रोसेस करेंगे",
    contactWhatsapp: "WhatsApp पर सपोर्ट से संपर्क करें",

    // Milestone banner
    claimWhatsapp: "WhatsApp पर क्लेम करें",
    milestone5Title: "🎉 5 स्टार हो गए!",
    milestone5Msg: "आपकी फ्री बॉयज़ टी-शर्ट (₹199) रेडी है! नीचे टैप करके WhatsApp पर क्लेम करें",
    milestone10Title: "🏆 10 स्टार हो गए!",
    milestone10Msg: "आपका फ्री किड्स क्लोदिंग सेट (₹399) रेडी है! WhatsApp पर क्लेम करें",


};

// ===== LANGUAGE MANAGER =====
const LangManager = {
  currentLang: 'en',

  init() {
    const saved = localStorage.getItem('vistara_lang');
    if (saved && (saved === 'en' || saved === 'hi')) {
      this.currentLang = saved;
      this.applyTranslations();
    } else {
      this.showPopup();
    }
  },

  get(key) {
    return translations[this.currentLang][key] || translations['en'][key] || key;
  },

  setLang(lang) {
    this.currentLang = lang;
    localStorage.setItem('vistara_lang', lang);
    this.applyTranslations();
    this.hidePopup();
    this.updateToggleButton();
  },

  applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const attr = el.getAttribute('data-i18n-attr');
      const val = this.get(key);
      if (attr) {
        el.setAttribute(attr, val);
      } else {
        el.textContent = val;
      }
    });
    document.documentElement.lang = this.currentLang === 'hi' ? 'hi' : 'en';
    this.updateToggleButton();
  },

  updateToggleButton() {
    const btn = document.getElementById('langToggleBtn');
    if (btn) btn.textContent = this.get('langToggle');
  },

  showPopup() {
    const popup = document.getElementById('langPopup');
    if (popup) {
      popup.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  },

  hidePopup() {
    const popup = document.getElementById('langPopup');
    if (popup) {
      popup.classList.remove('show');
      document.body.style.overflow = '';
    }
  }
};