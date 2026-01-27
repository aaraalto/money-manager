/**
 * Toast Notification System
 * 
 * A lightweight, accessible toast notification system for user feedback.
 * Supports multiple types: success, error, warning, info
 * 
 * Usage:
 *   import { toast, ToastType } from './toast.js';
 *   toast('Operation successful!', ToastType.SUCCESS);
 *   toast('Something went wrong', ToastType.ERROR, 5000);
 */

export const ToastType = {
    SUCCESS: 'success',
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
};

// Toast configuration
const TOAST_CONFIG = {
    defaultDuration: 4000,
    maxToasts: 5,
    position: 'bottom-right', // Options: top-right, top-left, bottom-right, bottom-left
    animationDuration: 300,
};

// Icons for each toast type (SVG strings)
const TOAST_ICONS = {
    success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>`,
    error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="15" y1="9" x2="9" y2="15"></line>
        <line x1="9" y1="9" x2="15" y2="15"></line>
    </svg>`,
    warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
        <line x1="12" y1="9" x2="12" y2="13"></line>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
    </svg>`,
    info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
    </svg>`
};

// Active toasts
let activeToasts = [];

/**
 * Initialize the toast container if it doesn't exist
 */
function initToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = `toast-container toast-${TOAST_CONFIG.position}`;
        container.setAttribute('role', 'region');
        container.setAttribute('aria-label', 'Notifications');
        container.setAttribute('aria-live', 'polite');
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Create a toast element
 */
function createToastElement(message, type, duration) {
    const toast = document.createElement('div');
    const id = `toast-${Date.now()}`;
    toast.id = id;
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    
    // Progress bar for auto-dismiss
    const hasProgress = duration > 0;
    
    toast.innerHTML = `
        <div class="toast-icon">${TOAST_ICONS[type]}</div>
        <div class="toast-content">
            <p class="toast-message">${escapeHtml(message)}</p>
        </div>
        <button class="toast-close" aria-label="Dismiss notification">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
        ${hasProgress ? `<div class="toast-progress" style="animation-duration: ${duration}ms"></div>` : ''}
    `;
    
    // Close button handler
    toast.querySelector('.toast-close').addEventListener('click', () => {
        dismissToast(id);
    });
    
    return { element: toast, id };
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show a toast notification
 * 
 * @param {string} message - The message to display
 * @param {string} type - Toast type (success, error, warning, info)
 * @param {number} duration - Duration in ms (0 for persistent)
 * @returns {string} Toast ID for programmatic dismissal
 */
export function toast(message, type = ToastType.INFO, duration = TOAST_CONFIG.defaultDuration) {
    const container = initToastContainer();
    
    // Limit number of active toasts
    while (activeToasts.length >= TOAST_CONFIG.maxToasts) {
        const oldest = activeToasts.shift();
        dismissToast(oldest, true);
    }
    
    const { element, id } = createToastElement(message, type, duration);
    
    // Add to DOM
    container.appendChild(element);
    activeToasts.push(id);
    
    // Trigger enter animation
    requestAnimationFrame(() => {
        element.classList.add('toast-enter');
    });
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            dismissToast(id);
        }, duration);
    }
    
    return id;
}

/**
 * Dismiss a toast by ID
 * 
 * @param {string} id - Toast ID
 * @param {boolean} immediate - Skip animation
 */
export function dismissToast(id, immediate = false) {
    const toast = document.getElementById(id);
    if (!toast) return;
    
    // Remove from active list
    activeToasts = activeToasts.filter(t => t !== id);
    
    if (immediate) {
        toast.remove();
        return;
    }
    
    // Exit animation
    toast.classList.add('toast-exit');
    toast.classList.remove('toast-enter');
    
    setTimeout(() => {
        toast.remove();
    }, TOAST_CONFIG.animationDuration);
}

/**
 * Dismiss all active toasts
 */
export function dismissAllToasts() {
    activeToasts.forEach(id => dismissToast(id));
}

/**
 * Convenience methods for each type
 */
export const toastSuccess = (message, duration) => toast(message, ToastType.SUCCESS, duration);
export const toastError = (message, duration) => toast(message, ToastType.ERROR, duration || 6000);
export const toastWarning = (message, duration) => toast(message, ToastType.WARNING, duration);
export const toastInfo = (message, duration) => toast(message, ToastType.INFO, duration);

/**
 * Initialize HTMX event listeners for automatic toasts
 */
export function initHtmxToastHandlers() {
    // Success response handler
    document.body.addEventListener('htmx:afterSwap', (event) => {
        const response = event.detail.xhr;
        
        // Check for custom toast header
        const toastMessage = response.getResponseHeader('X-Toast-Message');
        const toastType = response.getResponseHeader('X-Toast-Type') || 'success';
        
        if (toastMessage) {
            toast(toastMessage, toastType);
        }
    });
    
    // Error response handler
    document.body.addEventListener('htmx:responseError', (event) => {
        const status = event.detail.xhr?.status;
        let message = 'Something went wrong. Please try again.';
        
        if (status === 429) {
            message = 'Too many requests. Please wait a moment.';
        } else if (status >= 500) {
            message = 'Server error. Our team has been notified.';
        } else if (status === 403) {
            message = 'You don\'t have permission to do that.';
        } else if (status === 404) {
            message = 'The requested resource was not found.';
        }
        
        toastError(message);
    });
    
    // Network error handler
    document.body.addEventListener('htmx:sendError', () => {
        toastError('Network error. Check your connection and try again.');
    });
    
    // Timeout handler
    document.body.addEventListener('htmx:timeout', () => {
        toastWarning('Request timed out. Please try again.');
    });
}

// Auto-initialize HTMX handlers when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHtmxToastHandlers);
} else {
    initHtmxToastHandlers();
}
