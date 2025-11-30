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
            ...options
        };

        this.value = this.options.initialValue;

        // Elements
        this.knob = this.container.querySelector('.rotary-knob-group');
        this.progressPath = this.container.querySelector('.rotary-progress');
        this.hiddenInput = document.querySelector(this.options.inputSelector);
        this.display = document.querySelector(this.options.displaySelector);

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

    updateFromValue(val) {
        // Clamp value
        val = Math.max(this.options.minValue, Math.min(this.options.maxValue, val));
        this.value = val;

        const pct = (val - this.options.minValue) / (this.options.maxValue - this.options.minValue);
        const rot = pct * 360;

        // Set Knob Rotation
        gsap.set(this.knob, { rotation: rot, transformOrigin: "center center" });

        this.updateVisuals(rot);
    }

    updateVisuals(rot) {
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
            this.animateNumber(this.display, this.value);
        }
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

    commitValue() {
        if (this.hiddenInput) {
            this.hiddenInput.value = this.value;
            // Trigger HTMX
            this.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
}

