/**
 * Menu Detail Page - UI Components
 * Sprint 2 Phase 1 - Frontend Development
 *
 * Modular components for rendering menu detail sections
 */

// ===========================
// Image Carousel Component
// ===========================
const ImageCarousel = {
    /**
     * Create Swiper carousel with menu images
     * @param {Array} images - Array of image objects [{url, credit}, ...]
     * @param {HTMLElement} container - Container element
     */
    render(images, container) {
        if (!images || images.length === 0) {
            container.innerHTML = `
                <div class="carousel-placeholder">
                    🍽️
                </div>
            `;
            return;
        }

        // Create Swiper HTML
        const swiperHTML = `
            <div class="swiper menu-carousel">
                <div class="swiper-wrapper">
                    ${images.map(img => `
                        <div class="swiper-slide menu-carousel-slide">
                            <img src="${escapeHtml(img.url)}"
                                 alt="Menu image"
                                 loading="lazy"
                                 onerror="this.src='assets/placeholder-food.png'">
                            ${img.credit ? `
                                <div class="carousel-image-credit">
                                    📷 ${escapeHtml(img.credit)}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                <div class="swiper-button-next"></div>
                <div class="swiper-button-prev"></div>
                <div class="swiper-pagination"></div>
            </div>
        `;

        container.innerHTML = swiperHTML;

        // Initialize Swiper
        new Swiper('.menu-carousel', {
            loop: images.length > 1,
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            autoplay: images.length > 1 ? {
                delay: 4000,
                disableOnInteraction: false,
            } : false,
            lazy: true,
        });
    }
};


// ===========================
// Description Component
// ===========================
const DescriptionComponent = {
    /**
     * Render detailed description section
     * @param {Object} data - Menu data object
     */
    render(data) {
        const {
            explanation_long,
            cultural_context,
            allergens,
            dietary_tags,
            main_ingredients
        } = data;

        let html = '';

        // Long description
        if (explanation_long && explanation_long.en) {
            html += `
                <div class="description-section">
                    <h3>📖 What is this dish?</h3>
                    <p class="description-text">${escapeHtml(explanation_long.en)}</p>
                </div>
            `;
        }

        // Cultural context
        if (cultural_context && cultural_context.en) {
            html += `
                <div class="description-section">
                    <h3>🎎 Cultural Significance</h3>
                    <p class="description-text">${escapeHtml(cultural_context.en)}</p>
                </div>
            `;
        }

        // Main ingredients
        if (main_ingredients && main_ingredients.length > 0) {
            html += `
                <div class="description-section">
                    <h3>🥬 Main Ingredients</h3>
                    <ul class="ingredients-list">
                        ${main_ingredients.map(ing => `
                            <li>${escapeHtml(ing.en || ing.ko)}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Allergens
        if (allergens && allergens.length > 0) {
            html += `
                <div class="allergen-section">
                    <h3>⚠️ Allergen Information</h3>
                    <div class="allergen-list">
                        ${allergens.map(allergen => `
                            <span class="allergen-tag">${getAllergenEmoji(allergen)} ${escapeHtml(allergen)}</span>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Dietary tags
        if (dietary_tags && dietary_tags.length > 0) {
            html += `
                <div class="dietary-section">
                    <h3>🏷️ Dietary Information</h3>
                    <div class="dietary-list">
                        ${dietary_tags.map(tag => `
                            <span class="dietary-tag">${getDietaryEmoji(tag)} ${escapeHtml(tag.replace(/_/g, ' '))}</span>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        return html;
    }
};


// ===========================
// Preparation Steps Component
// ===========================
const PreparationStepsComponent = {
    /**
     * Render cooking steps
     * @param {Array} steps - Array of step objects [{number, description}, ...]
     */
    render(steps) {
        if (!steps || steps.length === 0) {
            return `
                <p style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                    Preparation steps coming soon!
                </p>
            `;
        }

        return `
            <ol class="preparation-steps-list">
                ${steps.map(step => `
                    <li class="preparation-step">
                        <div class="step-number">${step.number}</div>
                        <div class="step-content">
                            <p class="step-description">${escapeHtml(step.description)}</p>
                        </div>
                    </li>
                `).join('')}
            </ol>
        `;
    }
};


// ===========================
// Nutrition Table Component
// ===========================
const NutritionTableComponent = {
    /**
     * Render nutrition information
     * @param {Object} nutrition - Nutrition data {calories, protein, fat, carbs, fiber, sodium}
     * @param {Array} health_benefits - Health benefits list
     */
    render(nutrition, health_benefits) {
        if (!nutrition) {
            return `
                <p style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                    Nutritional information coming soon!
                </p>
            `;
        }

        let html = `
            <div class="nutrition-grid">
                ${this._renderNutritionCard('Calories', nutrition.calories, 'kcal', '🔥')}
                ${this._renderNutritionCard('Protein', nutrition.protein, 'g', '💪')}
                ${this._renderNutritionCard('Fat', nutrition.fat, 'g', '🧈')}
                ${this._renderNutritionCard('Carbs', nutrition.carbs, 'g', '🌾')}
            </div>
        `;

        // Health benefits
        if (health_benefits && health_benefits.length > 0) {
            html += `
                <div class="health-benefits">
                    <h3>✨ Health Benefits</h3>
                    <ul class="health-benefits-list">
                        ${health_benefits.map(benefit => `
                            <li class="health-benefit-item">${escapeHtml(benefit)}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        return html;
    },

    _renderNutritionCard(label, value, unit, emoji) {
        return `
            <div class="nutrition-card">
                <div class="nutrition-label">${emoji} ${label}</div>
                <div class="nutrition-value">
                    ${value || '-'}<span class="nutrition-unit">${unit}</span>
                </div>
            </div>
        `;
    }
};


// ===========================
// Visitor Tips Component
// ===========================
const VisitorTipsComponent = {
    /**
     * Render visitor tips
     * @param {Object} tips - Tips object {ordering, eating, pairing}
     */
    render(tips) {
        if (!tips) {
            return `
                <p style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                    Visitor tips coming soon!
                </p>
            `;
        }

        let html = '';

        if (tips.ordering) {
            html += `
                <div class="tips-section">
                    <h3>📝 How to Order</h3>
                    <div class="tip-card">
                        <p>${escapeHtml(tips.ordering)}</p>
                    </div>
                </div>
            `;
        }

        if (tips.eating) {
            html += `
                <div class="tips-section">
                    <h3>🍴 How to Eat</h3>
                    <div class="tip-card">
                        <p>${escapeHtml(tips.eating)}</p>
                    </div>
                </div>
            `;
        }

        if (tips.pairing) {
            html += `
                <div class="tips-section">
                    <h3>🍺 Recommended Pairings</h3>
                    <div class="tip-card">
                        <p>${escapeHtml(tips.pairing)}</p>
                    </div>
                </div>
            `;
        }

        return html;
    }
};


// ===========================
// Similar Dishes Component
// ===========================
const SimilarDishesComponent = {
    /**
     * Render similar dishes
     * @param {Array} dishes - Array of similar dish objects or strings
     */
    render(dishes) {
        if (!dishes || dishes.length === 0) {
            return '';
        }

        return dishes.map(dish => {
            // Handle string format (legacy): "갈비구이 (Galbi Gui - Description)"
            if (typeof dish === 'string') {
                return `
                    <div class="similar-dish-card-simple">
                        <div class="similar-dish-placeholder">🍽️</div>
                        <div class="similar-dish-name">${escapeHtml(dish)}</div>
                    </div>
                `;
            }

            // Handle object format (Sprint 2 Phase 2)
            const hasImage = dish.image_url && dish.image_url !== 'null';
            const canNavigate = dish.id && dish.id !== 'null';

            return `
                <div class="similar-dish-card ${canNavigate ? 'clickable' : ''}"
                     ${canNavigate ? `data-menu-id="${dish.id}" onclick="navigateToMenu('${dish.id}')" style="cursor: pointer;"` : ''}>
                    ${hasImage ? `
                        <img src="${escapeHtml(dish.image_url)}"
                             alt="${escapeHtml(dish.name_en)}"
                             class="similar-dish-image"
                             loading="lazy"
                             onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'similar-dish-placeholder\\'>🍽️</div>'">
                    ` : `
                        <div class="similar-dish-placeholder">🍽️</div>
                    `}
                    <div class="similar-dish-info">
                        <div class="similar-dish-name-ko korean-text">${escapeHtml(dish.name_ko)}</div>
                        <div class="similar-dish-name-en">${escapeHtml(dish.name_en)}</div>
                    </div>
                </div>
            `;
        }).join('');
    }
};


// ===========================
// Helper Functions
// ===========================
function getAllergenEmoji(allergen) {
    const emojis = {
        'peanut': '🥜',
        'peanuts': '🥜',
        'tree nuts': '🌰',
        'tree_nuts': '🌰',
        'soy': '🫘',
        'wheat': '🌾',
        'milk': '🥛',
        'egg': '🥚',
        'eggs': '🥚',
        'fish': '🐟',
        'shellfish': '🦐',
        'beef': '🥩',
        'pork': '🐷',
        'chicken': '🐔',
        'sesame': '🌱'
    };
    return emojis[allergen.toLowerCase()] || '⚠️';
}

function getDietaryEmoji(tag) {
    const emojis = {
        'contains_pork': '🐷',
        'contains_beef': '🥩',
        'spicy': '🌶️',
        'mild': '🟢',
        'vegan': '🌱',
        'vegetarian': '🥗',
        'gluten_free': '🌾❌',
        'halal': '☪️',
    };
    return emojis[tag] || '🏷️';
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function navigateToMenu(menuId) {
    window.location.href = `menu-detail.html?id=${menuId}`;
}
