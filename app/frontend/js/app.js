/**
 * Menu Guide Korea - Frontend Application
 * API Integration with Menu Knowledge Engine
 */

// ===========================
// Configuration
// ===========================
const CONFIG = {
    // API_BASE_URL: 동적으로 환경에 맞게 자동 설정
    API_BASE_URL: window.location.origin || 'http://localhost:8000',
    API_ENDPOINTS: {
        IDENTIFY: '/api/v1/menu/identify',
        HEALTH: '/health'
    },
    LANGUAGE: 'en', // Default language (managed by LanguageManager)
};

// ===========================
// Language Manager (Multi-Language Support)
// ===========================
const LanguageManager = {
    SUPPORTED_LANGUAGES: ['en', 'ja', 'zh'],
    STORAGE_KEY: 'menu_guide_language',

    /**
     * Initialize language system
     */
    init() {
        // Load saved language or default to English
        const savedLang = localStorage.getItem(this.STORAGE_KEY);
        const currentLang = this.SUPPORTED_LANGUAGES.includes(savedLang) ? savedLang : 'en';

        CONFIG.LANGUAGE = currentLang;
        this.updateUILanguageButtons(currentLang);

        console.log(`🌐 Language initialized: ${currentLang}`);
    },

    /**
     * Get current language
     */
    getCurrentLanguage() {
        return CONFIG.LANGUAGE;
    },

    /**
     * Set language and persist to localStorage
     */
    setLanguage(lang) {
        if (!this.SUPPORTED_LANGUAGES.includes(lang)) {
            console.warn(`⚠️ Unsupported language: ${lang}`);
            return;
        }

        CONFIG.LANGUAGE = lang;
        localStorage.setItem(this.STORAGE_KEY, lang);
        this.updateUILanguageButtons(lang);

        console.log(`✅ Language changed to: ${lang}`);
    },

    /**
     * Update language button states
     */
    updateUILanguageButtons(lang) {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const btnLang = btn.getAttribute('data-lang');
            if (btnLang === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
};

/**
 * Get localized field from object with fallback chain
 * @param {Object} obj - Object containing localized fields
 * @param {string} fieldKey - Field key without language suffix (e.g., 'name', 'explanation_short')
 * @returns {string} - Localized value with fallback
 */
function getLocalizedField(obj, fieldKey) {
    if (!obj) return '';

    const lang = LanguageManager.getCurrentLanguage();

    // Special handling for JSONB fields (explanation_short, explanation_long, cultural_context)
    const jsonbFields = ['explanation_short', 'explanation_long', 'cultural_context'];
    if (jsonbFields.includes(fieldKey)) {
        if (typeof obj[fieldKey] === 'object') {
            // Fallback chain: current lang → en → ko
            const langMap = { 'ja': 'ja', 'zh': 'zh', 'en': 'en' };
            return obj[fieldKey][langMap[lang]] || obj[fieldKey]['en'] || obj[fieldKey]['ko'] || '';
        }
        return obj[fieldKey] || '';
    }

    // Regular fields (name_en, name_ja, name_zh_cn)
    const langSuffixes = {
        'en': '',       // name_en → name + _en
        'ja': '_ja',    // name_ja
        'zh': '_zh_cn'  // name_zh_cn (simplified Chinese)
    };

    const suffix = langSuffixes[lang] || '';
    const localizedKey = `${fieldKey}${suffix}`;

    // Fallback chain: ja/zh → en → ko
    return obj[localizedKey] || obj[`${fieldKey}_en`] || obj[`${fieldKey}_ko`] || obj[fieldKey] || '';
}

/**
 * Get modifier translation (locale-aware)
 * @param {Object} modifier - Modifier object from API
 * @returns {string} - Translated modifier text
 */
function getModifierTranslation(modifier) {
    if (!modifier) return '';

    const lang = LanguageManager.getCurrentLanguage();

    // Fallback chain: ja/zh → en → ko
    if (lang === 'ja' && modifier.translation_ja) {
        return modifier.translation_ja;
    }
    if (lang === 'zh' && modifier.translation_zh) {
        return modifier.translation_zh;
    }
    return modifier.translation_en || modifier.text_ko || '';
}

/**
 * Get ingredient name (locale-aware)
 * @param {Object} ingredient - Ingredient object {ko: "...", en: "...", ja: "...", zh: "..."}
 * @returns {string} - Translated ingredient name
 */
function getIngredientName(ingredient) {
    if (!ingredient) return '';
    if (typeof ingredient === 'string') return ingredient;

    const lang = LanguageManager.getCurrentLanguage();

    // Fallback chain: ja/zh → en → ko
    if (lang === 'ja' && ingredient.ja) return ingredient.ja;
    if (lang === 'zh' && ingredient.zh) return ingredient.zh;
    return ingredient.en || ingredient.ko || '';
}

// ===========================
// DOM Elements
// ===========================
const DOM = {
    // Sections
    landingSection: document.getElementById('landingSection'),
    resultsSection: document.getElementById('resultsSection'),

    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),

    // Search
    menuInput: document.getElementById('menuInput'),
    searchBtn: document.getElementById('searchBtn'),

    // Popular dishes
    dishTags: document.querySelectorAll('.dish-tag'),

    // Results
    backBtn: document.getElementById('backBtn'),
    resultsContainer: document.getElementById('resultsContainer'),
};

// ===========================
// State Management
// ===========================
const state = {
    currentView: 'landing', // 'landing' or 'results'
    searchResults: [],
};

// ===========================
// API Functions
// ===========================
async function identifyMenu(menuName) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.IDENTIFY}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                menu_name_ko: menuName.trim()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function searchMultipleMenus(menuNames) {
    const results = [];

    for (const menuName of menuNames) {
        if (!menuName.trim()) continue;

        try {
            const result = await identifyMenu(menuName);
            results.push({
                input: menuName,
                data: result,
                success: true
            });
        } catch (error) {
            results.push({
                input: menuName,
                error: error.message,
                success: false
            });
        }
    }

    return results;
}

// ===========================
// UI Functions
// ===========================
function showLoading() {
    DOM.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    DOM.loadingOverlay.classList.add('hidden');
}

function switchView(view) {
    if (view === 'landing') {
        DOM.landingSection.classList.remove('hidden');
        DOM.resultsSection.classList.add('hidden');
        state.currentView = 'landing';
    } else if (view === 'results') {
        DOM.landingSection.classList.add('hidden');
        DOM.resultsSection.classList.remove('hidden');
        state.currentView = 'results';
    }
}

function getSpiceEmoji(level) {
    const emojis = ['🟢', '🟡', '🟠', '🔴', '🔥'];
    const emoji = emojis[Math.min(level, 4)];
    return emoji.repeat(Math.max(1, level));
}

function getDifficultyEmoji(score) {
    const emojis = ['😊', '🤔', '😰'];
    return emojis[Math.min(score - 1, 2)] || '😊';
}

function formatAllergens(allergens) {
    if (!allergens || allergens.length === 0) {
        return '<span style="color: var(--spice-0);">✓ No common allergens</span>';
    }

    const allergenEmojis = {
        'peanut': '🥜',
        'tree nuts': '🌰',
        'soy': '🫘',
        'wheat': '🌾',
        'milk': '🥛',
        'egg': '🥚',
        'fish': '🐟',
        'shellfish': '🦐',
        'beef': '🥩',
        'pork': '🐷',
        'chicken': '🐔',
    };

    return allergens.map(allergen => {
        const emoji = allergenEmojis[allergen.toLowerCase()] || '⚠️';
        return `${emoji} ${allergen}`;
    }).join(', ');
}

function createMenuCard(result) {
    const { input, data, success, error } = result;

    if (!success) {
        return `
            <div class="menu-card">
                <div class="menu-name-ko korean-text">${escapeHtml(input)}</div>
                <div class="menu-divider"></div>
                <p style="color: #F44336;">❌ Error: ${escapeHtml(error)}</p>
            </div>
        `;
    }

    const { match_type, canonical, modifiers, confidence } = data;

    // AI Discovery (no match found)
    if (match_type === 'ai_discovery_needed' || !canonical) {
        return `
            <div class="menu-card ai-discovery-card">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <div class="menu-name-ko korean-text">${escapeHtml(input)}</div>
                <div class="ai-discovery-message">
                    This menu is being analyzed by our AI.<br>
                    Check back soon for detailed information!
                </div>
            </div>
        `;
    }

    // Successful match
    const {
        name_ko,
        main_ingredients,
        allergens,
        spice_level,
        difficulty_score,
        image_url
    } = canonical;

    // Localized fields
    const nameLocalized = getLocalizedField(canonical, 'name');
    const descriptionLocalized = getLocalizedField(canonical, 'explanation_short');
    const currentLang = LanguageManager.getCurrentLanguage();

    const spiceEmoji = getSpiceEmoji(spice_level || 0);
    const difficultyEmoji = getDifficultyEmoji(difficulty_score || 1);

    // Create composed name (with modifiers)
    let composedName = '';
    if (modifiers && modifiers.length > 0) {
        const modifierTexts = modifiers.map(m => getModifierTranslation(m)).join(' ');
        composedName = `${modifierTexts} ${nameLocalized.split('(')[0].trim()}`;
    } else {
        composedName = nameLocalized.split('(')[0].trim();
    }

    // Add language indicator if not in original language
    const langSuffix = currentLang !== 'en' ? ` (${currentLang.toUpperCase()})` : '';
    const description = descriptionLocalized || 'No description available';

    // Food image HTML
    const imageHtml = image_url ? `
        <div class="menu-image-container">
            <img src="${escapeHtml(image_url)}"
                 alt="${escapeHtml(nameLocalized)}"
                 class="menu-image"
                 loading="lazy"
                 onerror="this.parentElement.classList.add('image-error'); this.style.display='none';">
            <div class="image-credit">📷 Wikimedia Commons</div>
        </div>
    ` : '';

    let html = `
        <div class="menu-card" onclick="navigateToMenuDetail('${escapeHtml(name_ko)}')" style="cursor: pointer;">
            ${imageHtml}
            <div class="menu-name-ko korean-text">${escapeHtml(name_ko)}</div>
            <div class="menu-name-en">${escapeHtml(nameLocalized)}${langSuffix}</div>
            <div class="menu-name-composed">${escapeHtml(composedName)}</div>

            <div class="menu-divider"></div>

            <div class="menu-stats">
                <div class="stat-item">
                    ${spiceEmoji} Spice Level ${spice_level || 0}
                </div>
                <div class="stat-item">
                    ${difficultyEmoji} Adventure ${difficulty_score || 1}
                </div>
            </div>

            <div class="menu-description">
                ${escapeHtml(description)}
            </div>
    `;

    // Allergens
    if (allergens && allergens.length > 0) {
        html += `
            <div class="menu-allergens">
                <div class="allergen-title">⚠️ Allergens:</div>
                ${formatAllergens(allergens)}
            </div>
        `;
    }

    // Modifiers (if present)
    if (modifiers && modifiers.length > 0) {
        html += `
            <div class="modifiers-section">
                <div class="modifiers-title">📝 Modifiers:</div>
        `;

        modifiers.forEach(modifier => {
            html += `
                <div class="modifier-item">
                    <span class="modifier-ko korean-text">${escapeHtml(modifier.text_ko)}</span>
                    <span>=</span>
                    <span class="modifier-en">${escapeHtml(getModifierTranslation(modifier))}</span>
                </div>
            `;
        });

        html += `</div>`;
    }

    // Allergen disclaimer (shown when allergens exist)
    if (allergens && allergens.length > 0) {
        html += `
            <div class="allergen-disclaimer">
                ⚠️ Allergen info is based on general recipes and may not reflect the actual restaurant's ingredients. 
                Always confirm with restaurant staff.
            </div>
        `;
    }

    // Confidence badge
    const confidencePct = Math.round(confidence * 100);
    const confidenceColor = confidence >= 0.9 ? 'var(--spice-0)' :
                           confidence >= 0.7 ? 'var(--spice-2)' : 'var(--spice-4)';

    html += `
            <div class="menu-divider"></div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 0.85rem; color: ${confidenceColor};">
                    ✓ ${confidencePct}% Match (${match_type})
                </div>
                <div style="color: var(--primary-color); font-weight: 600; font-size: 0.9rem;">
                    Full details →
                </div>
            </div>
        </div>
    `;

    return html;
}

function navigateToMenuDetail(menuName) {
    window.location.href = `menu-detail.html?name=${encodeURIComponent(menuName)}`;
}

function displayResults(results) {
    state.searchResults = results;

    const html = results.map(result => createMenuCard(result)).join('');
    DOM.resultsContainer.innerHTML = html;

    switchView('results');
    window.scrollTo(0, 0);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ===========================
// Event Handlers
// ===========================
async function handleSearch() {
    const input = DOM.menuInput.value.trim();

    if (!input) {
        alert('Please enter a menu name');
        return;
    }

    // Parse multiple menus (comma or newline separated)
    const menuNames = input.split(/[,\n]+/).map(s => s.trim()).filter(s => s);

    if (menuNames.length === 0) {
        alert('Please enter at least one menu name');
        return;
    }

    showLoading();

    try {
        const results = await searchMultipleMenus(menuNames);
        displayResults(results);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function handleBack() {
    switchView('landing');
}

function handleDishTagClick(event) {
    const menuName = event.target.dataset.menu;
    if (menuName) {
        DOM.menuInput.value = menuName;
        handleSearch();
    }
}

// ===========================
// Event Listeners
// ===========================
function initEventListeners() {
    // Search button
    DOM.searchBtn.addEventListener('click', handleSearch);

    // Enter key on input
    DOM.menuInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // Back button
    DOM.backBtn.addEventListener('click', handleBack);

    // Dish tags
    DOM.dishTags.forEach(tag => {
        tag.addEventListener('click', handleDishTagClick);
    });

    // Language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', handleLanguageSwitch);
    });
}

/**
 * Handle language switching
 */
function handleLanguageSwitch(event) {
    const selectedLang = event.currentTarget.getAttribute('data-lang');
    LanguageManager.setLanguage(selectedLang);

    // Re-render current view
    if (state.currentView === 'results' && state.searchResults.length > 0) {
        // Re-render search results with new language
        renderResults(state.searchResults);
    }

    console.log(`🌐 Language switched to: ${selectedLang}`);
}

// ===========================
// Initialization
// ===========================
async function init() {
    console.log('🍜 Menu Guide Korea - Initializing...');

    // Initialize language system
    LanguageManager.init();

    // Check API health
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.HEALTH}`);
        const health = await response.json();
        console.log('✅ API Status:', health);
    } catch (error) {
        console.warn('⚠️ API may not be running:', error.message);
        console.warn('Please start the backend: cd app/backend && uvicorn main:app --reload');
    }

    // Initialize event listeners
    initEventListeners();

    console.log('✅ App initialized successfully');
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
