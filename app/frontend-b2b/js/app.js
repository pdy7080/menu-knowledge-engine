/**
 * Menu Knowledge Engine - B2B Admin Application
 * Sprint 3 P0-3: OCR + Menu Review System
 */

// ===========================
// Configuration
// ===========================
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    API_ENDPOINTS: {
        OCR: '/api/v1/menu/recognize',
        IDENTIFY: '/api/v1/menu/identify',
    },
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
};

// ===========================
// State Management
// ===========================
const state = {
    currentStep: 'upload', // 'upload', 'review', 'success'
    uploadedImage: null,
    ocrResult: null,
    menuItems: [],
};

// ===========================
// DOM Elements
// ===========================
const DOM = {
    // Sections
    uploadSection: document.getElementById('uploadSection'),
    reviewSection: document.getElementById('reviewSection'),
    successSection: document.getElementById('successSection'),

    // Upload
    uploadArea: document.getElementById('uploadArea'),
    imageInput: document.getElementById('imageInput'),
    uploadBtn: document.getElementById('uploadBtn'),
    imagePreview: document.getElementById('imagePreview'),
    previewImg: document.getElementById('previewImg'),
    changeImageBtn: document.getElementById('changeImageBtn'),

    // Review
    ocrResult: document.getElementById('ocrResult'),
    ocrText: document.getElementById('ocrText'),
    ocrConfidence: document.getElementById('ocrConfidence'),
    menuItemsContainer: document.getElementById('menuItemsContainer'),
    backBtn: document.getElementById('backBtn'),
    confirmAllBtn: document.getElementById('confirmAllBtn'),

    // Success
    successStats: document.getElementById('successStats'),
    registerAnotherBtn: document.getElementById('registerAnotherBtn'),

    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingProgress: document.getElementById('loadingProgress'),
};

// ===========================
// UI Functions
// ===========================
function showLoading(message = 'Processing...') {
    DOM.loadingOverlay.classList.remove('hidden');
    document.querySelector('.loading-text').textContent = message;
}

function hideLoading() {
    DOM.loadingOverlay.classList.add('hidden');
}

function updateLoadingProgress(text) {
    DOM.loadingProgress.textContent = text;
}

function switchStep(step) {
    // Hide all sections
    DOM.uploadSection.classList.add('hidden');
    DOM.reviewSection.classList.add('hidden');
    DOM.successSection.classList.add('hidden');

    // Show target section
    if (step === 'upload') {
        DOM.uploadSection.classList.remove('hidden');
    } else if (step === 'review') {
        DOM.reviewSection.classList.remove('hidden');
    } else if (step === 'success') {
        DOM.successSection.classList.remove('hidden');
    }

    state.currentStep = step;
    window.scrollTo(0, 0);
}

// ===========================
// File Upload Handlers
// ===========================
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file size
    if (file.size > CONFIG.MAX_FILE_SIZE) {
        alert(`파일 크기가 너무 큽니다. 최대 ${CONFIG.MAX_FILE_SIZE / 1024 / 1024}MB까지 업로드 가능합니다.`);
        return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('이미지 파일만 업로드 가능합니다.');
        return;
    }

    state.uploadedImage = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        DOM.previewImg.src = e.target.result;
        DOM.uploadArea.classList.add('hidden');
        DOM.imagePreview.classList.remove('hidden');
    };
    reader.readAsDataURL(file);

    // Auto-process after preview
    setTimeout(() => {
        processImage();
    }, 500);
}

// ===========================
// OCR Processing
// ===========================
async function processImage() {
    if (!state.uploadedImage) return;

    showLoading('메뉴판을 분석 중입니다...');
    updateLoadingProgress('1/3 - OCR 텍스트 추출 중...');

    try {
        // Step 1: OCR Recognition
        const formData = new FormData();
        formData.append('file', state.uploadedImage);

        const ocrResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.OCR}`, {
            method: 'POST',
            body: formData,
        });

        if (!ocrResponse.ok) {
            const errorData = await ocrResponse.json();
            throw new Error(errorData.detail || 'OCR 처리 실패');
        }

        const ocrResult = await ocrResponse.json();
        state.ocrResult = ocrResult;

        updateLoadingProgress(`2/3 - 메뉴 ${ocrResult.menu_items.length}개 발견됨, 매칭 중...`);

        // Step 2: Match each menu item
        const menuItems = [];
        for (let i = 0; i < ocrResult.menu_items.length; i++) {
            const item = ocrResult.menu_items[i];

            updateLoadingProgress(`2/3 - 매칭 중 (${i + 1}/${ocrResult.menu_items.length})...`);

            try {
                const matchResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.IDENTIFY}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ menu_name_ko: item.name_ko }),
                });

                if (matchResponse.ok) {
                    const matchResult = await matchResponse.json();
                    menuItems.push({
                        ocr: item,
                        match: matchResult,
                    });
                } else {
                    // Matching failed, add as-is
                    menuItems.push({
                        ocr: item,
                        match: { match_type: 'no_match', confidence: 0.0 },
                    });
                }
            } catch (error) {
                console.error(`Matching error for ${item.name_ko}:`, error);
                menuItems.push({
                    ocr: item,
                    match: { match_type: 'error', confidence: 0.0 },
                });
            }
        }

        state.menuItems = menuItems;

        updateLoadingProgress('3/3 - 결과 준비 중...');
        await new Promise(resolve => setTimeout(resolve, 300));

        hideLoading();

        // Display results
        displayReviewSection();

    } catch (error) {
        hideLoading();
        alert(`처리 중 오류가 발생했습니다: ${error.message}`);
        console.error('Processing error:', error);
    }
}

// ===========================
// Display Review Section
// ===========================
function displayReviewSection() {
    // OCR Result
    DOM.ocrText.textContent = state.ocrResult.raw_text || '(인식된 텍스트 없음)';

    const confidencePct = Math.round(state.ocrResult.ocr_confidence * 100);
    DOM.ocrConfidence.textContent = `신뢰도: ${confidencePct}%`;

    if (confidencePct >= 85) {
        DOM.ocrConfidence.style.background = 'var(--confidence-high)';
    } else if (confidencePct >= 65) {
        DOM.ocrConfidence.style.background = 'var(--confidence-mid)';
    } else {
        DOM.ocrConfidence.style.background = 'var(--confidence-low)';
    }

    // Menu Items
    DOM.menuItemsContainer.innerHTML = state.menuItems.map((item, index) => {
        return createMenuItemCard(item, index);
    }).join('');

    switchStep('review');
}

function createMenuItemCard(item, index) {
    const { ocr, match } = item;
    const confidence = match.confidence || 0;
    const confidencePct = Math.round(confidence * 100);

    // Determine confidence class
    let confidenceClass = 'low-confidence';
    let confidenceBadgeClass = 'low';
    let confidenceIcon = '❓';

    if (confidence >= 0.85) {
        confidenceClass = 'high-confidence';
        confidenceBadgeClass = 'high';
        confidenceIcon = '✅';
    } else if (confidence >= 0.65) {
        confidenceClass = 'mid-confidence';
        confidenceBadgeClass = 'mid';
        confidenceIcon = '⚠️';
    }

    // Build card HTML
    let html = `
        <div class="menu-item-card ${confidenceClass}" data-index="${index}">
            <div class="menu-item-header">
                <div class="menu-item-names">
                    <div class="menu-name-ko korean-text">${escapeHtml(ocr.name_ko)}</div>
    `;

    if (match.canonical) {
        html += `<div class="menu-name-en english-text">${escapeHtml(match.canonical.name_en)}</div>`;
    } else {
        html += `<div class="menu-name-en english-text" style="color: var(--color-error);">매칭 실패</div>`;
    }

    html += `
                </div>
                <div class="menu-price">${escapeHtml(ocr.price_ko)}원</div>
            </div>
    `;

    // Details
    if (match.canonical) {
        html += `
            <div class="menu-item-details">
                <div class="detail-row">
                    <span class="detail-label">설명:</span>
                    <span>${escapeHtml(match.canonical.explanation_short?.en || 'N/A')}</span>
                </div>
        `;

        // Modifiers
        if (match.modifiers && match.modifiers.length > 0) {
            html += `
                <div class="detail-row">
                    <span class="detail-label">수식어:</span>
                    <div class="modifiers-list">
            `;
            match.modifiers.forEach(mod => {
                html += `<span class="modifier-tag">${escapeHtml(mod.text_ko)} = ${escapeHtml(mod.translation_en)}</span>`;
            });
            html += `
                    </div>
                </div>
            `;
        }

        // Allergens
        if (match.canonical.allergens && match.canonical.allergens.length > 0) {
            html += `
                <div class="detail-row">
                    <span class="detail-label">알레르기:</span>
                    <span>${match.canonical.allergens.join(', ')}</span>
                </div>
            `;
        }

        html += `
                <div class="detail-row">
                    <span class="detail-label">매운맛:</span>
                    <span>${'🌶️'.repeat(match.canonical.spice_level || 0) || '없음'}</span>
                </div>
            </div>
        `;
    }

    // Confidence Badge
    html += `
            <div class="menu-item-footer">
                <div class="confidence-badge ${confidenceBadgeClass}">
                    ${confidenceIcon} ${confidencePct}% 일치 (${match.match_type})
                </div>
            </div>
        </div>
    `;

    return html;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// ===========================
// Confirm All
// ===========================
function handleConfirmAll() {
    // For now, just show success
    // In real implementation, this would POST to /api/v1/shop/{shop_id}/menu/confirm

    const totalMenus = state.menuItems.length;
    const highConfidence = state.menuItems.filter(item => item.match.confidence >= 0.85).length;
    const midConfidence = state.menuItems.filter(item => item.match.confidence >= 0.65 && item.match.confidence < 0.85).length;
    const lowConfidence = state.menuItems.filter(item => item.match.confidence < 0.65).length;

    DOM.successStats.innerHTML = `
        <div><strong>총 메뉴 수:</strong> ${totalMenus}개</div>
        <div><strong>높은 확신:</strong> ${highConfidence}개 (✅)</div>
        <div><strong>확인 필요:</strong> ${midConfidence}개 (⚠️)</div>
        <div><strong>수동 입력 권장:</strong> ${lowConfidence}개 (❓)</div>
    `;

    switchStep('success');
}

// ===========================
// Event Listeners
// ===========================
function initEventListeners() {
    // Upload button
    DOM.uploadBtn.addEventListener('click', () => {
        DOM.imageInput.click();
    });

    // File input change
    DOM.imageInput.addEventListener('change', handleFileSelect);

    // Change image button
    DOM.changeImageBtn.addEventListener('click', () => {
        DOM.imageInput.value = '';
        DOM.imagePreview.classList.add('hidden');
        DOM.uploadArea.classList.remove('hidden');
        state.uploadedImage = null;
    });

    // Drag and drop
    DOM.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        DOM.uploadArea.style.borderColor = 'var(--color-accent)';
    });

    DOM.uploadArea.addEventListener('dragleave', () => {
        DOM.uploadArea.style.borderColor = 'var(--color-border)';
    });

    DOM.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        DOM.uploadArea.style.borderColor = 'var(--color-border)';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            DOM.imageInput.files = files;
            handleFileSelect({ target: { files } });
        }
    });

    // Back button
    DOM.backBtn.addEventListener('click', () => {
        switchStep('upload');
        DOM.imageInput.value = '';
        DOM.imagePreview.classList.add('hidden');
        DOM.uploadArea.classList.remove('hidden');
        state.uploadedImage = null;
        state.ocrResult = null;
        state.menuItems = [];
    });

    // Confirm all button
    DOM.confirmAllBtn.addEventListener('click', handleConfirmAll);

    // Register another button
    DOM.registerAnotherBtn.addEventListener('click', () => {
        switchStep('upload');
        DOM.imageInput.value = '';
        DOM.imagePreview.classList.add('hidden');
        DOM.uploadArea.classList.remove('hidden');
        state.uploadedImage = null;
        state.ocrResult = null;
        state.menuItems = [];
    });
}

// ===========================
// Initialization
// ===========================
async function init() {
    console.log('🍜 Menu Knowledge Engine B2B - Initializing...');
    initEventListeners();
    console.log('✅ App initialized successfully');
}

// Start app
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
