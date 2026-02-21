/**
 * Enriched Content Components - Sprint 2 Phase 2
 * Additional UI components for enriched menu data
 *
 * NOTE: LanguageManager, getLocalizedField, getIngredientName are defined in
 * menu-detail-components.js (loaded first). Do not redeclare them here.
 */

// ===========================
// Regional Variants Component
// ===========================
const RegionalVariantsComponent = {
    /**
     * Render regional variants
     * @param {Array} variants - Array of variant objects [{region, local_name, differences}, ...]
     */
    render(variants) {
        if (!variants || variants.length === 0) {
            return '';
        }

        return `
            <div class="regional-variants-section">
                <h3>${getLabel('section.regionalVariations')}</h3>
                <div class="regional-variants-grid">
                    ${variants.map(variant => `
                        <div class="regional-variant-card">
                            <div class="variant-region">${escapeHtml(variant.region)}</div>
                            ${variant.local_name ? `
                                <div class="variant-local-name">${escapeHtml(variant.local_name)}</div>
                            ` : ''}
                            <div class="variant-differences">${escapeHtml(variant.differences)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
};


// ===========================
// Flavor Profile Component
// ===========================
const FlavorProfileComponent = {
    /**
     * Render flavor profile as visual bars
     * @param {Object} profile - Flavor profile {spiciness, sweetness, saltiness, umami, sour, bitter}
     */
    render(profile) {
        if (!profile) {
            return '';
        }

        const flavors = [
            { key: 'spiciness', label: 'Spiciness', emoji: '🌶️', color: '#ef4444' },
            { key: 'sweetness', label: 'Sweetness', emoji: '🍯', color: '#f59e0b' },
            { key: 'saltiness', label: 'Saltiness', emoji: '🧂', color: '#3b82f6' },
            { key: 'umami', label: 'Umami', emoji: '🍄', color: '#8b5cf6' },
            { key: 'sour', label: 'Sourness', emoji: '🍋', color: '#eab308' },
            { key: 'bitter', label: 'Bitterness', emoji: '☕', color: '#78350f' },
        ];

        const activeFlavors = flavors.filter(f => profile[f.key] && profile[f.key] > 0);

        if (activeFlavors.length === 0) {
            return '';
        }

        return `
            <div class="flavor-profile-section">
                <h3>${getLabel('section.flavorProfile')}</h3>
                <div class="flavor-bars">
                    ${activeFlavors.map(flavor => `
                        <div class="flavor-bar-item">
                            <div class="flavor-label">
                                <span class="flavor-emoji">${flavor.emoji}</span>
                                <span class="flavor-name">${flavor.label}</span>
                                <span class="flavor-value">${profile[flavor.key]}/5</span>
                            </div>
                            <div class="flavor-bar-track">
                                <div class="flavor-bar-fill"
                                     style="width: ${(profile[flavor.key] / 5) * 100}%; background-color: ${flavor.color};">
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
};


// ===========================
// Enriched Description Component
// ===========================
const EnrichedDescriptionComponent = {
    /**
     * Render long descriptions and cultural context
     * @param {Object} data - Menu data with description_long_ko/en and cultural_background
     */
    render(data) {
        let html = '';

        // Long description (localized)
        // For JA/ZH: prefer explanation_long.{lang} (deep translation) over description_long_en fallback
        const lang = LanguageManager.getCurrentLanguage();
        let descriptionLong = '';
        if (lang !== 'en' && data.explanation_long && typeof data.explanation_long === 'object' && data.explanation_long[lang]) {
            descriptionLong = data.explanation_long[lang];
        }
        if (!descriptionLong) {
            descriptionLong = getLocalizedField(data, 'description_long');
        }
        if (descriptionLong) {
            html += `
                <div class="description-section">
                    <h3>${getLabel('section.whatIsThis')}</h3>
                    <p class="description-text-long">${escapeHtml(descriptionLong)}</p>
                </div>
            `;
        }

        // Cultural background
        if (data.cultural_background) {
            html += `
                <div class="description-section">
                    <h3>${getLabel('section.culturalSignificance')}</h3>
                    <p class="description-text">${escapeHtml(data.cultural_background)}</p>
                </div>
            `;
        }

        // Regional variants
        if (data.regional_variants && data.regional_variants.length > 0) {
            html += RegionalVariantsComponent.render(data.regional_variants);
        }

        // Flavor profile
        if (data.flavor_profile) {
            html += FlavorProfileComponent.render(data.flavor_profile);
        }

        // Fallback to basic description if no enriched content
        const explanationLong = getLocalizedField(data, 'explanation_long');
        if (!html && explanationLong) {
            html += `
                <div class="description-section">
                    <h3>${getLabel('section.whatIsThis')}</h3>
                    <p class="description-text">${escapeHtml(explanationLong)}</p>
                </div>
            `;
        }

        // Cultural context (fallback)
        const culturalContext = getLocalizedField(data, 'cultural_context');
        if (culturalContext) {
            html += `
                <div class="description-section">
                    <h3>${getLabel('section.culturalSignificance')}</h3>
                    <p class="description-text">${escapeHtml(culturalContext)}</p>
                </div>
            `;
        }

        // Main ingredients
        if (data.main_ingredients && data.main_ingredients.length > 0) {
            html += `
                <div class="description-section">
                    <h3>${getLabel('section.mainIngredients')}</h3>
                    <ul class="ingredients-list">
                        ${data.main_ingredients.map(ing => `
                            <li>${escapeHtml(getIngredientName(ing))}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Allergens
        if (data.allergens && data.allergens.length > 0) {
            html += `
                <div class="allergen-section">
                    <h3>${getLabel('section.allergens')}</h3>
                    <div class="allergen-list">
                        ${data.allergens.map(allergen => `
                            <span class="allergen-tag">${getAllergenEmoji(allergen)} ${escapeHtml(allergen)}</span>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Dietary tags
        if (data.dietary_tags && data.dietary_tags.length > 0) {
            html += `
                <div class="dietary-section">
                    <h3>${getLabel('section.dietaryInfo')}</h3>
                    <div class="dietary-list">
                        ${data.dietary_tags.map(tag => `
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
// Enriched Preparation Component
// ===========================
const EnrichedPreparationComponent = {
    /**
     * Render preparation steps with instructions
     * @param {Object} data - preparation_steps object or array
     */
    render(data) {
        // Handle enriched format: data.preparation_steps.steps (object) or data.steps (array) or direct array
        const steps = data?.preparation_steps?.steps || data?.steps || (Array.isArray(data) ? data : []);

        if (!steps || steps.length === 0) {
            return `
                <p style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                    Preparation steps coming soon!
                </p>
            `;
        }

        return `
            <ol class="preparation-steps-list">
                ${steps.map((step, index) => {
                    // Support both formats: object {step, instruction_en, ...} or plain string
                    const stepNum = typeof step === 'string' ? (index + 1) : (step.step || step.number || (index + 1));
                    const instruction = typeof step === 'string' ? step : (step.instruction_en || step.instruction_ko || step.description || '');

                    return `
                        <li class="preparation-step">
                            <div class="step-number">${stepNum}</div>
                            <div class="step-content">
                                <p class="step-description">${escapeHtml(instruction)}</p>
                            </div>
                        </li>
                    `;
                }).join('')}
            </ol>
        `;
    }
};


// ===========================
// Enriched Nutrition Component
// ===========================
const EnrichedNutritionComponent = {
    /**
     * Render nutrition detail from enriched data
     * @param {Object} data - nutrition_detail object {calories, protein_g, fat_g, carbs_g, ...}
     */
    render(data) {
        const nutrition = data?.nutrition_detail || data?.nutrition || null;

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
                ${this._renderNutritionCard('Protein', nutrition.protein_g || nutrition.protein, 'g', '💪')}
                ${this._renderNutritionCard('Fat', nutrition.fat_g || nutrition.fat, 'g', '🧈')}
                ${this._renderNutritionCard('Carbs', nutrition.carbs_g || nutrition.carbs, 'g', '🌾')}
            </div>
        `;

        // Health benefits
        const benefits = data?.health_benefits || [];
        if (benefits && benefits.length > 0) {
            html += `
                <div class="health-benefits">
                    <h3>${getLabel('section.healthBenefits')}</h3>
                    <ul class="health-benefits-list">
                        ${benefits.map(benefit => `
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
// Helper Functions
// ===========================
function getAllergenEmoji(allergen) {
    const emojis = {
        'peanut': '🥜', 'peanuts': '🥜',
        'tree nuts': '🌰', 'tree_nuts': '🌰',
        'soy': '🫘', 'wheat': '🌾',
        'milk': '🥛', 'egg': '🥚', 'eggs': '🥚',
        'fish': '🐟', 'shellfish': '🦐',
        'beef': '🥩', 'pork': '🐷', 'chicken': '🐔',
        'sesame': '🌱'
    };
    return emojis[allergen.toLowerCase()] || '⚠️';
}

function getDietaryEmoji(tag) {
    const emojis = {
        'contains_pork': '🐷', 'contains_beef': '🥩',
        'spicy': '🌶️', 'mild': '🟢',
        'vegan': '🌱', 'vegetarian': '🥗',
        'gluten_free': '🌾❌', 'halal': '☪️',
    };
    return emojis[tag] || '🏷️';
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;', '<': '&lt;', '>': '&gt;',
        '"': '&quot;', "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}
