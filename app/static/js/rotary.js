console.log(`%c
                          ,,   ,,                         
\`7MM"""Mq.              \`7MM   db                    mm   
  MM   \`MM.               MM                         MM   
  MM   ,M9  ,6"Yb.   ,M""bMM \`7MM  ,6"Yb. \`7MMpMMMbmmMMmm 
  MMmmdM9  8)   MM ,AP    MM   MM 8)   MM   MM    MM MM   
  MM  YM.   ,pm9MM 8MI    MM   MM  ,pm9MM   MM    MM MM   
  MM   \`Mb.8M   MM \`Mb    MM   MM 8M   MM   MM    MM MM   
.JMML. .JMM\`Moo9^Yo.\`Wbmd"MML.JMML\`Moo9^Yo.JMML  JMML\`Mbmo
`, "color: #f59e0b; font-weight: bold;");

class RotaryKnob {
    constructor(selector, options = {}) {
        this.container = document.querySelector(selector);
        if (!this.container) {
            console.error(`RotaryKnob: Container ${selector} not found`);
            return;
        }

        this.options = {
            minValue: 0,
            maxValue: 3000,
            initialValue: 500,
            inputSelector: null,
            displaySelector: null,
            limitSelector: null, // New option for limit checking
            ...options
        };

        this.value = this.options.initialValue;
        this.lastShakeTime = 0;

        // Elements
        this.knob = this.container.querySelector('.rotary-knob-group');
        this.progressPath = this.container.querySelector('.rotary-progress');
        this.hiddenInput = document.querySelector(this.options.inputSelector);
        this.display = document.querySelector(this.options.displaySelector);
        this.limitDisplay = document.querySelector(this.options.limitSelector);

        if (!this.knob || !this.progressPath) {
            console.error("RotaryKnob: Missing SVG elements (.rotary-knob-group or .rotary-progress)");
            return;
        }

        // Measurements
        this.pathLength = this.progressPath.getTotalLength();
        this.progressPath.style.strokeDasharray = this.pathLength;

        this.init();
    }

    init() {
        const self = this;

        // Set initial state
        this.updateFromValue(this.value);

        // Setup manual input if display is an input element
        if (this.display && (this.display.tagName === 'INPUT')) {
            this.setupManualInput();
        }

        // Make draggable
        // We rotate the group around the center of the SVG
        Draggable.create(this.knob, {
            type: "rotation",
            trigger: this.container.querySelector('svg'), // Allow dragging anywhere on SVG to rotate
            inertia: true,
            bounds: { minRotation: 0, maxRotation: 360 }, // Standard 360 dial

            onDrag: function () {
                self.handleRotation(this.rotation);
            },
            onThrowUpdate: function () {
                self.handleRotation(this.rotation);
            },
            onDragEnd: function () {
                self.commitValue();
            },
            onThrowComplete: function () {
                self.commitValue();
            }
        });

        // Listen for changes on limit display (e.g., via HTMX updates)
        if (this.limitDisplay) {
            const observer = new MutationObserver(() => {
                this.checkLimit();
            });
            observer.observe(this.limitDisplay, { childList: true, characterData: true, subtree: true });
        }
    }

    setupManualInput() {
        // Update rotary when user types
        this.display.addEventListener('input', (e) => {
            this.resizeInput();
            const val = parseInt(e.target.value, 10);
            if (!isNaN(val)) {
                // Don't update visuals fully to avoid cursor jumping, just knob and internal value
                // However, we need to clamp for the logic but maybe let user type freely until blur?
                // Let's clamp for safety but maybe allow typing.
                // For now, simple approach: update everything.
                // To avoid cursor jumping, we might skip updating the input value in updateVisuals if it's the active element.
                this.updateFromValue(val, true); // true = fromInput
            }
        });

        // Commit on blur or enter
        this.display.addEventListener('blur', () => {
            this.updateFromValue(this.value); // Clamp and normalize
            this.commitValue();
        });

        this.display.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.display.blur();
            }
        });
    }

    handleRotation(degrees) {
        // Normalize to 0-360
        let rot = degrees % 360;
        if (rot < 0) rot += 360;

        // Calculate Value
        const pct = rot / 360;
        this.value = Math.round(pct * (this.options.maxValue - this.options.minValue) + this.options.minValue);

        // Update Visuals
        this.updateVisuals(rot);
    }

    updateFromValue(val, fromInput = false) {
        // Clamp value
        val = Math.max(this.options.minValue, Math.min(this.options.maxValue, val));
        this.value = val;

        const pct = (val - this.options.minValue) / (this.options.maxValue - this.options.minValue);
        const rot = pct * 360;

        // Set Knob Rotation
        gsap.set(this.knob, { rotation: rot, transformOrigin: "center center" });

        this.updateVisuals(rot, fromInput);
    }

    updateVisuals(rot, fromInput = false) {
        // Update Progress Arc
        // Stroke-dashoffset: pathLength * (1 - pct)
        const pct = rot / 360;
        const offset = this.pathLength * (1 - pct);

        gsap.to(this.progressPath, {
            strokeDashoffset: offset,
            duration: 0.2,
            ease: "power2.out"
        });

        // Update Display Text with flip animation
        if (this.display) {
            if (this.display.tagName === 'INPUT') {
                if (!fromInput && document.activeElement !== this.display) {
                    this.display.value = this.value;
                }
                this.resizeInput();
            } else {
                this.animateNumber(this.display, this.value);
            }
        }

        // Check Limit
        this.checkLimit();
    }

    checkLimit() {
        if (!this.limitDisplay) return;

        // Parse limit value from text (remove non-numeric chars except decimal)
        const limitText = this.limitDisplay.textContent;
        const limitVal = parseFloat(limitText.replace(/[^0-9.-]+/g, ""));

        if (isNaN(limitVal)) return;

        const isOver = this.value > limitVal;

        if (isOver) {
            if (!this.container.classList.contains('is-over-limit')) {
                this.container.classList.add('is-over-limit');
                this.triggerShake();
            }
        } else {
            this.container.classList.remove('is-over-limit');
        }
    }

    triggerShake() {
        const now = Date.now();
        if (now - this.lastShakeTime < 500) return; // Throttle shake
        
        this.lastShakeTime = now;
        this.container.classList.add('shake');
        setTimeout(() => {
            this.container.classList.remove('shake');
        }, 500);
    }

    animateNumber(element, newValue) {
        const oldValue = element.textContent;

        if (oldValue === newValue.toString()) return;

        // Wrap each digit in a span for flip animation
        const newValueStr = newValue.toString();
        const oldValueStr = oldValue.toString();

        // Simple approach: add flipping class
        element.classList.add('flipping');

        // Update the number with a slight delay to sync with animation
        setTimeout(() => {
            element.textContent = newValue;
        }, 200);

        // Remove flipping class after animation
        setTimeout(() => {
            element.classList.remove('flipping');
        }, 600);
    }

    resizeInput() {
        if (!this.display || this.display.tagName !== 'INPUT') return;
        
        // Just update the state, let CSS handle the math.
        // This is more performant and keeps styling logic in CSS.
        this.display.style.setProperty('--char-count', this.display.value.toString().length);
    }

    commitValue() {
        if (this.hiddenInput) {
            this.hiddenInput.value = this.value;
            // Trigger HTMX
            this.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
}
