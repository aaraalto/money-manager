// Card Expansion System
class CardExpander {
    constructor() {
        this.expandedCard = null;
        this.originalParent = null;
        this.originalIndex = null;
        this.init();
    }

    init() {
        // Create fullscreen overlay
        this.createOverlay();

        // Add click handlers to all cards
        this.attachCardHandlers();

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.expandedCard) {
                this.collapseCard();
            }
        });
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'card-overlay';
        overlay.innerHTML = `
            <div class="overlay-header">
                <button class="overlay-close" aria-label="Close">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <div class="overlay-nav">
                    <button class="overlay-prev" aria-label="Previous">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                        Previous
                    </button>
                    <button class="overlay-next" aria-label="Next">
                        Next
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="overlay-content"></div>
        `;
        document.body.appendChild(overlay);

        // Add event listeners
        overlay.querySelector('.overlay-close').addEventListener('click', () => this.collapseCard());
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) this.collapseCard();
        });
        overlay.querySelector('.overlay-prev').addEventListener('click', () => this.navigateCard(-1));
        overlay.querySelector('.overlay-next').addEventListener('click', () => this.navigateCard(1));
    }

    attachCardHandlers() {
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            // Add expand button to card
            const expandBtn = document.createElement('button');
            expandBtn.className = 'card-expand-btn';
            expandBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <polyline points="9 21 3 21 3 15"></polyline>
                    <line x1="21" y1="3" x2="14" y2="10"></line>
                    <line x1="3" y1="21" x2="10" y2="14"></line>
                </svg>
            `;
            expandBtn.setAttribute('aria-label', 'Expand card');
            expandBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.expandCard(card, index);
            });

            // Insert expand button into card header
            const cardHeader = card.querySelector('h2');
            if (cardHeader) {
                cardHeader.style.position = 'relative';
                cardHeader.appendChild(expandBtn);
            }

            // Make card clickable
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                // Don't expand if clicking on interactive elements
                if (e.target.closest('button, a, input, select, textarea')) {
                    return;
                }
                this.expandCard(card, index);
            });

            card.dataset.cardIndex = index;
        });
    }

    expandCard(card, index) {
        const overlay = document.querySelector('.card-overlay');
        const overlayContent = overlay.querySelector('.overlay-content');

        // Save original state
        this.expandedCard = card;
        this.originalParent = card.parentNode;
        this.originalIndex = index;

        // Clone card content
        const cardClone = card.cloneNode(true);
        cardClone.classList.add('expanded-card');

        // Remove expand button from clone
        const expandBtn = cardClone.querySelector('.card-expand-btn');
        if (expandBtn) expandBtn.remove();

        overlayContent.innerHTML = '';
        overlayContent.appendChild(cardClone);

        // Update navigation buttons
        const cards = document.querySelectorAll('.card');
        overlay.querySelector('.overlay-prev').disabled = index === 0;
        overlay.querySelector('.overlay-next').disabled = index === cards.length - 1;

        // Show overlay with animation
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Animate card
        setTimeout(() => {
            cardClone.classList.add('expanded');
        }, 50);
    }

    collapseCard() {
        const overlay = document.querySelector('.card-overlay');
        const expandedCard = overlay.querySelector('.expanded-card');

        if (expandedCard) {
            expandedCard.classList.remove('expanded');
        }

        setTimeout(() => {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
            this.expandedCard = null;
            this.originalParent = null;
            this.originalIndex = null;
        }, 300);
    }

    navigateCard(direction) {
        const cards = document.querySelectorAll('.card');
        const newIndex = this.originalIndex + direction;

        if (newIndex >= 0 && newIndex < cards.length) {
            this.collapseCard();
            setTimeout(() => {
                this.expandCard(cards[newIndex], newIndex);
            }, 350);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new CardExpander();
});
