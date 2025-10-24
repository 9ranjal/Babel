/**
 * Type definitions for the chip-based information collection system
 * Note: These are JSDoc comments for type hints in JavaScript
 */

/**
 * @typedef {Object} ChipData
 * @property {string} id
 * @property {string} category
 * @property {string} label
 * @property {any} value
 * @property {'pending' | 'completed' | 'required' | 'optional'} status
 * @property {string[]} [dependencies]
 * @property {string[]} [options]
 * @property {'text' | 'select' | 'number' | 'boolean' | 'date'} type
 * @property {string} [description]
 * @property {string} [placeholder]
 * @property {Object} [validation]
 */

/**
 * @typedef {Object} ChipCategory
 * @property {string} id
 * @property {string} name
 * @property {string} description
 * @property {string} icon
 * @property {string} color
 * @property {ChipData[]} chips
 * @property {string[]} [dependencies]
 * @property {number} order
 */

/**
 * @typedef {Object} InformationState
 * @property {ChipData[]} chips
 * @property {string[]} completedCategories
 * @property {any} termSheetData
 * @property {boolean} canGenerateTermSheet
 * @property {ChipData[]} suggestions
 * @property {string} [currentCategory]
 */

/**
 * @typedef {Object} TermSheetThreshold
 * @property {string[]} requiredCategories
 * @property {number} minimumChips
 * @property {string[]} criticalChips
 */

/**
 * @typedef {Object} ChipSuggestion
 * @property {ChipData} chip
 * @property {string} reason
 * @property {'high' | 'medium' | 'low'} priority
 * @property {string[]} [basedOn]
 */

// Export empty object for compatibility
export {};
