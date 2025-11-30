// Data Density Control System
class DensityControl {
    constructor() {
        this.container = document.querySelector('.container');
        this.densityButtons = document.querySelectorAll('.density-btn');
        this.currentDensity = this.loadDensity();
        this.init();
    }

    init() {
        // Set initial density
        this.setDensity(this.currentDensity);

        // Add click handlers to density buttons
        this.densityButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const density = btn.dataset.density;
                this.setDensity(density);
                this.saveDensity(density);
            });
        });
    }

    setDensity(density) {
        // Update container data attribute
        this.container.setAttribute('data-density', density);

        // Update active button state
        this.densityButtons.forEach(btn => {
            if (btn.dataset.density === density) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        this.currentDensity = density;

        // Animate transition
        this.animateDensityChange();
    }

    animateDensityChange() {
        // Add subtle animation class
        this.container.style.transition = 'all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1)';

        // Reset transition after animation
        setTimeout(() => {
            this.container.style.transition = '';
        }, 300);
    }

    saveDensity(density) {
        try {
            localStorage.setItem('radiant_density', density);
        } catch (e) {
            console.warn('Could not save density preference:', e);
        }
    }

    loadDensity() {
        try {
            const saved = localStorage.getItem('radiant_density');
            return saved || 'comfortable'; // Default to comfortable
        } catch (e) {
            console.warn('Could not load density preference:', e);
            return 'comfortable';
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new DensityControl();
});
