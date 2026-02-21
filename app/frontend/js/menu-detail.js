/**
 * Menu Detail Page - Main Controller
 * Sprint 2 Phase 1 - Frontend Development
 */

// ===========================
// Configuration
// ===========================
const CONFIG = {
    API_BASE_URL: window.location.origin || 'http://localhost:8000',
    API_ENDPOINTS: {
        MENU_DETAIL: '/api/v1/menu/detail',  // Future endpoint
        CANONICAL: '/api/v1/canonical-menus',
        IDENTIFY: '/api/v1/menu/identify',
    },
    LANGUAGE: 'en', // Default language (managed by LanguageManager)
};

// NOTE: LanguageManager and getLocalizedField are defined in
// menu-detail-components.js (loaded before this file). Do not redeclare.

// ===========================
// DOM Elements
// ===========================
const DOM = {
    // Sections
    menuDetailSection: document.getElementById('menuDetailSection'),
    errorSection: document.getElementById('errorSection'),
    loadingOverlay: document.getElementById('loadingOverlay'),

    // Header
    backBtn: document.getElementById('backBtn'),
    errorBackBtn: document.getElementById('errorBackBtn'),

    // Title
    menuNameKo: document.getElementById('menuNameKo'),
    menuNameEn: document.getElementById('menuNameEn'),
    menuStats: document.getElementById('menuStats'),

    // Carousel
    imageCarouselContainer: document.getElementById('imageCarouselContainer'),

    // Tabs
    tabButtons: document.querySelectorAll('.tab-btn'),
    tabPanels: {
        description: document.getElementById('descriptionTab'),
        preparation: document.getElementById('preparationTab'),
        nutrition: document.getElementById('nutritionTab'),
        tips: document.getElementById('tipsTab'),
    },

    // Content containers
    descriptionContent: document.getElementById('descriptionContent'),
    preparationContent: document.getElementById('preparationContent'),
    nutritionContent: document.getElementById('nutritionContent'),
    tipsContent: document.getElementById('tipsContent'),
    similarDishesContainer: document.getElementById('similarDishesContainer'),

    // Error
    errorMessage: document.getElementById('errorMessage'),
};

// ===========================
// State Management
// ===========================
const state = {
    currentMenuId: null,
    menuData: null,
    activeTab: 'description',
};

// ===========================
// API Functions
// ===========================
async function fetchMenuDetail(menuId) {
    try {
        // Sprint 2 Phase 2: Request enriched content with menu ID in URL
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.CANONICAL}/${menuId}?include_enriched=true`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        // API returns single menu object directly
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function fetchMenuByName(menuName) {
    try {
        // Step 1: Identify the menu to get its ID
        const identifyResponse = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.IDENTIFY}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                menu_name_ko: menuName
            })
        });

        if (!identifyResponse.ok) {
            throw new Error(`HTTP ${identifyResponse.status}`);
        }

        const identifyResult = await identifyResponse.json();
        const basicMenuData = identifyResult.canonical;
        const menuId = basicMenuData.id;

        // Step 2: Try to fetch full enriched detail using the menu ID
        if (menuId) {
            try {
                const enrichedData = await fetchMenuDetail(menuId);
                console.log('✅ Enriched data loaded for:', menuName);
                return enrichedData;
            } catch (enrichedError) {
                // If enriched fetch fails, fallback to basic data from identify
                console.warn('⚠️ Enriched data not available, using basic data:', enrichedError.message);
                return basicMenuData;
            }
        }

        // Fallback to basic canonical data if ID not available
        return basicMenuData;
    } catch (error) {
        console.error('❌ API Error in fetchMenuByName:', error);
        throw error;
    }
}

// ===========================
// UI Rendering Functions
// ===========================
function renderMenuDetail(data) {
    state.menuData = data;

    // Render title
    DOM.menuNameKo.textContent = data.name_ko || '-';
    DOM.menuNameEn.textContent = getLocalizedField(data, 'name') || '-';

    // Render stats
    renderStats(data);

    // Render image carousel (API returns 'images' array, with 'image_url' as legacy fallback)
    const images = data.images || (data.image_url ? [{url: data.image_url, credit: 'Wikimedia Commons'}] : []);
    ImageCarousel.render(images, DOM.imageCarouselContainer);

    // Render tab contents
    renderDescriptionTab(data);
    renderPreparationTab(data);
    renderNutritionTab(data);
    renderTipsTab(data);

    // Render similar dishes
    renderSimilarDishes(data);

    // Show menu detail section
    DOM.menuDetailSection.classList.remove('hidden');
    DOM.errorSection.classList.add('hidden');
}

function renderStats(data) {
    const spiceEmoji = getSpiceEmoji(data.spice_level || 0);
    const difficultyEmoji = getDifficultyEmoji(data.difficulty_score || 1);

    DOM.menuStats.innerHTML = `
        <div class="stat-badge">
            ${spiceEmoji} ${getLabel('label.spiceLevel')} ${data.spice_level || 0}
        </div>
        <div class="stat-badge">
            ${difficultyEmoji} ${getLabel('label.adventure')} ${data.difficulty_score || 1}
        </div>
        ${data.typical_price_min ? `
            <div class="stat-badge">
                💰 ₩${data.typical_price_min.toLocaleString()}${data.typical_price_max ? ` - ₩${data.typical_price_max.toLocaleString()}` : ''}
            </div>
        ` : ''}
    `;
}

function renderDescriptionTab(data) {
    // Use EnrichedDescriptionComponent for Sprint 2 Phase 2 enriched content
    DOM.descriptionContent.innerHTML = EnrichedDescriptionComponent.render(data);
}

function renderPreparationTab(data) {
    // Use EnrichedPreparationComponent for Sprint 2 Phase 2 format
    DOM.preparationContent.innerHTML = EnrichedPreparationComponent.render(data);
}

function renderNutritionTab(data) {
    // Use EnrichedNutritionComponent for Sprint 2 Phase 2 nutrition_detail format
    DOM.nutritionContent.innerHTML = EnrichedNutritionComponent.render(data);
}

function renderTipsTab(data) {
    const tips = data.visitor_tips || null;
    DOM.tipsContent.innerHTML = VisitorTipsComponent.render(tips);
}

function renderSimilarDishes(data) {
    const similarDishes = data.similar_dishes || [];
    DOM.similarDishesContainer.innerHTML = SimilarDishesComponent.render(similarDishes);

    // Hide section if no similar dishes
    if (similarDishes.length === 0) {
        document.getElementById('similarDishesSection').style.display = 'none';
    }
}

function showError(message) {
    DOM.errorMessage.textContent = message;
    DOM.errorSection.classList.remove('hidden');
    DOM.menuDetailSection.classList.add('hidden');
}

function showLoading() {
    DOM.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    DOM.loadingOverlay.classList.add('hidden');
}

function getSpiceEmoji(level) {
    const emojis = ['🟢', '🟡', '🟠', '🔴', '🔥'];
    return emojis[Math.min(level, 4)] || '🟢';
}

function getDifficultyEmoji(score) {
    const emojis = ['😊', '😊', '🤔', '🤔', '😰'];
    return emojis[Math.min(score - 1, 4)] || '😊';
}

// ===========================
// i18n Label Update
// ===========================
function updateTabLabels() {
    const tabLabelMap = {
        'description': 'tab.description',
        'preparation': 'tab.preparation',
        'nutrition': 'tab.nutrition',
        'tips': 'tab.tips',
    };
    DOM.tabButtons.forEach(btn => {
        const tabKey = btn.dataset.tab;
        if (tabLabelMap[tabKey]) {
            btn.textContent = getLabel(tabLabelMap[tabKey]);
        }
    });
    // Back button
    if (DOM.backBtn) {
        DOM.backBtn.textContent = getLabel('btn.back');
    }
    // Similar dishes section title
    const similarTitle = document.querySelector('#similarDishesSection .section-title');
    if (similarTitle) {
        similarTitle.textContent = getLabel('section.similarDishes');
    }
}

// ===========================
// Tab Navigation
// ===========================
function switchTab(tabName) {
    // Update active tab button
    DOM.tabButtons.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update active tab panel
    Object.keys(DOM.tabPanels).forEach(key => {
        if (key === tabName) {
            DOM.tabPanels[key].classList.add('active');
        } else {
            DOM.tabPanels[key].classList.remove('active');
        }
    });

    state.activeTab = tabName;
}

// ===========================
// Event Handlers
// ===========================
function handleBack() {
    window.location.href = 'index.html';
}

function handleTabClick(event) {
    const tabName = event.target.dataset.tab;
    if (tabName) {
        switchTab(tabName);
    }
}

// ===========================
// URL Parameter Parsing
// ===========================
function getMenuIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id') || params.get('name');
}

// ===========================
// Initialization
// ===========================
async function init() {
    console.log('🍜 Menu Detail Page - Initializing...');

    // Initialize language and update all UI labels
    LanguageManager.init();
    updateTabLabels();

    // Get menu ID from URL
    const menuParam = getMenuIdFromURL();

    if (!menuParam) {
        showError('No menu specified. Please search for a menu first.');
        hideLoading();
        return;
    }

    state.currentMenuId = menuParam;

    // Setup event listeners
    DOM.backBtn.addEventListener('click', handleBack);
    DOM.errorBackBtn.addEventListener('click', handleBack);

    DOM.tabButtons.forEach(btn => {
        btn.addEventListener('click', handleTabClick);
    });

    // Fetch and render menu data
    showLoading();

    try {
        let menuData;

        // Check if menuParam is UUID (36 chars with dashes) or Korean name
        if (menuParam.length === 36 && menuParam.includes('-')) {
            menuData = await fetchMenuDetail(menuParam);
        } else {
            menuData = await fetchMenuByName(menuParam);
        }

        if (!menuData) {
            throw new Error('Menu not found');
        }

        renderMenuDetail(menuData);
        console.log('✅ Menu detail loaded successfully');
    } catch (error) {
        console.error('❌ Failed to load menu:', error);
        showError(`Failed to load menu: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
