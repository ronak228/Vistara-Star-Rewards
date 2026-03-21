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
    heroSubtitle: "Earn rewards on every purchase for your kids. Every order brings you closer to exclusive gifts!",
    heroCta: "Submit Your Order",

    // Hero Badges
    badge1: "1 Order = 1 Star",
    badge2: "5 Stars = Free Gift",
    badge3: "Secure & Verified",

    // How It Works
    howItWorksTitle: "How It Works",
    howCard1Title: "1 Order = 1 Star",
    howCard1Desc: "Every purchase you make earns you one reward star",
    howCard2Title: "5 Stars = Free Gift",
    howCard2Desc: "Collect 5 stars and claim your first reward gift",
    howCard3Title: "10 Stars = Premium Gift",
    howCard3Desc: "Reach 10 stars for an exclusive premium gift",

    // Form Section
    formTitle: "Submit Your Order",
    formSubtitle: "Quick and easy – takes less than 2 minutes",
    labelName: "Your Name",
    labelEmail: "Email Address",
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
    trust2Title: "Trusted by Customers",
    trust2Desc: "Thousands of happy families earning rewards every month",
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
    underReviewNote:      "🔍 Delivery confirmed! Stars will be credited in 10–14 days after the return window closes.",
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
    step3Desc:     "Upload your order screenshot. Once delivery is confirmed, your star is credited within 14-21 days",
    step4Title:    "Win Amazing Prizes",
    step4Desc:     "5 Stars = Free Gift 🎁  |  10 Stars = Premium Prize 🏆  |  Rate us for lucky draw entry!",
    shopUrl:       "https://www.meesho.com/VistaraEssentials?_ms=3.0.1",
    visitShop:     "Visit Our Meesho Store →",

    // ── Share & Win ───────────────────────────────────────────────────
    shareTitle:    "Share Your Review & Win!",
    shareDesc:     "Rate our product on Meesho, share the screenshot on WhatsApp or Instagram, and enter our monthly lucky draw for prizes worth ₹500+",
    prize1:        "1st Prize: ₹500 Gift Voucher",
    prize2:        "2nd Prize: Free Premium Product",
    prize3:        "3rd Prize: Extra Reward Stars",
    shareWhatsapp: "📲 Share on WhatsApp to Enter",

    // ── Support / Contact ─────────────────────────────────────────────
    supportTitle:      "Need Help? Contact Us on WhatsApp",
    supportDesc:       "If your stars haven't appeared after 21 days, or you've reached 5/10 stars and want to claim your reward — message us on WhatsApp with your token",
    supportTokenLabel: "Your Reward Token",
    supportStep1:      "After submitting, you receive a Reward Token (e.g. VST-1234) — save it",
    supportStep2:      "Open WhatsApp → tap our number → send your Token + Email",
    supportStep3:      "We verify within 24 hours and process your reward or star credit",
    contactWhatsapp:   "💬 Chat on WhatsApp Now",
    claimWhatsapp:     "🎁 Claim My Reward on WhatsApp",

    // ── Milestone banner ──────────────────────────────────────────────
    milestone5Title: "🎉 You've Reached 5 Stars!",
    milestone5Msg:   "Your FREE GIFT is ready! Tap below to claim via WhatsApp",
    milestone10Title:"🏆 You've Reached 10 Stars!",
    milestone10Msg:  "Your PREMIUM PRIZE is ready! Tap below to claim via WhatsApp",

  },

  hi: {
    // Navigation
    navHome: "होम",
    navCheckStars: "स्टार देखें",
    langToggle: "English",

    // Hero Section
    heroTitle1: "पाएं अपने",
    heroHighlight: "रिवॉर्ड स्टार",
    heroSubtitle: "हर खरीदारी पर रिवॉर्ड कमाएं। हर ऑर्डर आपको एक्सक्लूसिव गिफ्ट के करीब लाता है!",
    heroCta: "ऑर्डर जमा करें",

    // Hero Badges
    badge1: "1 ऑर्डर = 1 स्टार",
    badge2: "5 स्टार = फ्री गिफ्ट",
    badge3: "सुरक्षित और सत्यापित",

    // How It Works
    howItWorksTitle: "यह कैसे काम करता है",
    howCard1Title: "1 ऑर्डर = 1 स्टार",
    howCard1Desc: "हर खरीदारी पर आपको एक रिवॉर्ड स्टार मिलता है",
    howCard2Title: "5 स्टार = फ्री गिफ्ट",
    howCard2Desc: "5 स्टार इकट्ठा करें और पहला रिवॉर्ड गिफ्ट पाएं",
    howCard3Title: "10 स्टार = प्रीमियम गिफ्ट",
    howCard3Desc: "10 स्टार पर एक्सक्लूसिव प्रीमियम गिफ्ट पाएं",

    // Form Section
    formTitle: "अपना ऑर्डर जमा करें",
    formSubtitle: "आसान और जल्दी – 2 मिनट से कम समय",
    labelName: "आपका नाम",
    labelEmail: "ईमेल पता",
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
    trust2Title: "ग्राहकों का भरोसा",
    trust2Desc: "हर महीने हजारों परिवार रिवॉर्ड कमा रहे हैं",
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
    tier5Reward: "फ्री गिफ्ट",
    tier10Name: "10 स्टार",
    tier10Reward: "प्रीमियम गिफ्ट",
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
    underReviewNote:      "🔍 डिलीवरी पुष्टि हो गई! रिटर्न विंडो बंद होने के 10-14 दिन में स्टार मिलेंगे।",
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
    step3Desc:     "ऑर्डर स्क्रीनशॉट अपलोड करें। डिलीवरी कन्फर्म होने के 14-21 दिन में स्टार मिलेगा",
    step4Title:    "अमेज़िंग पुरस्कार जीतें",
    step4Desc:     "5 स्टार = फ्री गिफ्ट 🎁  |  10 स्टार = प्रीमियम पुरस्कार 🏆  |  रेटिंग दें और लकी ड्रा में शामिल हों!",
    shopUrl:       "https://www.meesho.com/VistaraEssentials?_ms=3.0.1",
    visitShop:     "हमारी Meesho स्टोर देखें →",

    // ── Share & Win ───────────────────────────────────────────────────
    shareTitle:    "रिव्यू शेयर करें और जीतें!",
    shareDesc:     "Meesho पर हमारे प्रोडक्ट को रेट करें, स्क्रीनशॉट WhatsApp या Instagram पर शेयर करें, और ₹500+ पुरस्कार के लिए मंथली लकी ड्रा में शामिल हों",
    prize1:        "पहला पुरस्कार: ₹500 गिफ्ट वाउचर",
    prize2:        "दूसरा पुरस्कार: फ्री प्रीमियम प्रोडक्ट",
    prize3:        "तीसरा पुरस्कार: एक्स्ट्रा रिवॉर्ड स्टार",
    shareWhatsapp: "📲 WhatsApp पर शेयर करें और शामिल हों",

    // ── Support / Contact ─────────────────────────────────────────────
    supportTitle:      "मदद चाहिए? WhatsApp पर हमसे बात करें",
    supportDesc:       "अगर 21 दिन बाद भी स्टार नहीं आया, या 5/10 स्टार पूरे हो गए और रिवॉर्ड क्लेम करना है — अपना टोकन लेकर WhatsApp पर मैसेज करें",
    supportTokenLabel: "आपका रिवॉर्ड टोकन",
    supportStep1:      "सबमिट करने के बाद आपको एक रिवॉर्ड टोकन मिलेगा (जैसे VST-1234) — इसे सेव करें",
    supportStep2:      "WhatsApp खोलें → हमारा नंबर टैप करें → टोकन + ईमेल भेजें",
    supportStep3:      "हम 24 घंटे में वेरीफाई करके आपका रिवॉर्ड या स्टार प्रोसेस करेंगे",
    contactWhatsapp:   "💬 अभी WhatsApp पर चैट करें",
    claimWhatsapp:     "🎁 WhatsApp पर रिवॉर्ड क्लेम करें",

    // ── Milestone banner ──────────────────────────────────────────────
    milestone5Title: "🎉 आपने 5 स्टार पा लिए!",
    milestone5Msg:   "आपका फ्री गिफ्ट तैयार है! WhatsApp पर क्लेम करें",
    milestone10Title:"🏆 आपने 10 स्टार पा लिए!",
    milestone10Msg:  "आपका प्रीमियम पुरस्कार तैयार है! WhatsApp पर क्लेम करें",

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
    shareTitle: "शेयर करें और जीतें अमेज़िंग पुरस्कार!",
    shareDesc: "अपना रेटिंग स्क्रीनशॉट WhatsApp, Instagram या Facebook पर शेयर करें — ₹500+ के एक्सक्लूसिव पुरस्कार के लिए मंथली लकी ड्रा में शामिल हों",
    prize1: "पहला पुरस्कार: ₹500 गिफ्ट वाउचर",
    prize2: "दूसरा पुरस्कार: फ्री प्रीमियम प्रोडक्ट",
    prize3: "तीसरा पुरस्कार: एक्स्ट्रा रिवॉर्ड स्टार",
    shareWhatsapp: "WhatsApp पर शेयर करें और शामिल हों",

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
    milestone5Msg: "आपने फ्री गिफ्ट अनलॉक कर लिया! नीचे टैप करके WhatsApp पर क्लेम करें",
    milestone10Title: "🏆 10 स्टार हो गए!",
    milestone10Msg: "आपने प्रीमियम पुरस्कार अनलॉक कर लिया! WhatsApp पर क्लेम करें",


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