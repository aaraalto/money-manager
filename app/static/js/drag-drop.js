// Drag and Drop for Dashboard Cards
class DashboardDragDrop {
    constructor() {
        this.draggableCards = document.querySelectorAll('.card');
        this.init();
    }

    init() {
        this.draggableCards.forEach(card => {
            // Add draggable class for styling
            card.classList.add('draggable');
            card.setAttribute('draggable', 'true');

            // Add event listeners
            card.addEventListener('dragstart', this.handleDragStart.bind(this));
            card.addEventListener('dragend', this.handleDragEnd.bind(this));
            card.addEventListener('dragover', this.handleDragOver.bind(this));
            card.addEventListener('drop', this.handleDrop.bind(this));
            card.addEventListener('dragleave', this.handleDragLeave.bind(this));
        });
    }

    handleDragStart(e) {
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.innerHTML);
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        // Remove drag-over class from all cards
        this.draggableCards.forEach(card => {
            card.classList.remove('drag-over');
        });
    }

    handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';

        const draggingCard = document.querySelector('.dragging');
        if (e.target.classList.contains('card') && e.target !== draggingCard) {
            e.target.classList.add('drag-over');
        }
        return false;
    }

    handleDragLeave(e) {
        e.target.classList.remove('drag-over');
    }

    handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }

        const draggingCard = document.querySelector('.dragging');
        const dropTarget = e.target.closest('.card');

        if (draggingCard && dropTarget && draggingCard !== dropTarget) {
            // Get parent containers
            const draggingParent = draggingCard.parentNode;
            const dropTargetParent = dropTarget.parentNode;

            // Swap positions
            const draggingIndex = Array.from(draggingParent.children).indexOf(draggingCard);
            const dropTargetIndex = Array.from(dropTargetParent.children).indexOf(dropTarget);

            if (draggingIndex < dropTargetIndex) {
                dropTargetParent.insertBefore(draggingCard, dropTarget.nextSibling);
            } else {
                dropTargetParent.insertBefore(draggingCard, dropTarget);
            }

            // Save order to localStorage
            this.saveOrder();
        }

        return false;
    }

    saveOrder() {
        const order = [];
        this.draggableCards = document.querySelectorAll('.card');
        this.draggableCards.forEach((card, index) => {
            const cardId = card.id || `card-${index}`;
            order.push(cardId);
        });
        localStorage.setItem('dashboardCardOrder', JSON.stringify(order));
    }

    restoreOrder() {
        const savedOrder = localStorage.getItem('dashboardCardOrder');
        if (!savedOrder) return;

        try {
            const order = JSON.parse(savedOrder);
            // Implementation depends on your card structure
            // This is a placeholder for the restore logic
        } catch (e) {
            console.error('Failed to restore card order:', e);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    const dragDrop = new DashboardDragDrop();
});
