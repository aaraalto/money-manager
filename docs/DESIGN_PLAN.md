# Creative Direction & Design Plan

## Philosophy
Radiant is not just a financial tool; it's a clarity engine. The design should feel **precise, futuristic, and calm**. We reject the clutter of traditional banking dashboards in favor of a "Majestic Monolith" aesthetic—solid, reliable, and beautiful.

## 1. Typography & Hierarchy
We utilize a dual-font stack to separate structural information from data.

- **Headings (Outfit)**: Geometric and bold. Used for page titles, card headers, and key metrics.
- **Body & Data (Inter)**: Highly legible, neutral. Used for table data, prose, and labels.

### Scale
- **Display**: 32px+ (Outfit, Bold)
- **H1**: 24px (Outfit, SemiBold)
- **H2**: 18px (Outfit, Medium)
- **Body**: 16px (Inter, Regular)
- **Small/Label**: 14px (Inter, Medium)

## 2. Color Palette
Retaining the current "Dark/Deep" theme but refining the accents for semantic meaning.

- **Backgrounds**: 
  - `bg-deep`: #0F1115 (Main background)
  - `surface-card`: #181B21 (Cards/Panels)
- **Accents**:
  - `primary`: #6366F1 (Action/Brand - Indigo)
  - `success`: #10B981 (Positive Cashflow/Growth - Emerald)
  - `danger`: #EF4444 (Debt/Burn - Red)
  - `warning`: #F59E0B (Caution - Amber)

## 3. Layouts & Navigation

### Navigation (Restored)
We have reverted to a **Top Navigation** pattern. This opens up the horizontal space for data tables and charts, which are wide by nature. 
- **Sticky Top Bar**: Branding on left, primary sections (Dashboard, Simulator, Spending) on right.
- **No Sidebar**: Maximizes screen real estate for complex views like the Simulator.

### Page Structures
1.  **Dashboard**: Grid-based. High-level KPIs at top. Actionable insights in middle. Charts at bottom.
2.  **Simulator**: Split view. Controls/Inputs on one side (or top), Real-time visualization on the other.
3.  **Spending Editor**: Focused "Document" mode. Centered table for distraction-free editing.

## 4. Data Visualization & Motion
Motion is not decoration; it is feedback.

- **GSAP Integration**:
  - **Enter Animations**: Cards stagger in from bottom (y: 20, opacity: 0).
  - **Number Counting**: Key metrics (Net Worth, FCF) count up from 0 to value on load.
  - **Charts**: Line charts draw their paths (SVG stroke-dashoffset trick).
- **Interactivity**:
  - Hover states on table rows highlight the specific debt/expense.
  - Simulator updates trigger a subtle "pulse" on the affected metrics.

## 5. Components (The Atomic Library)

### Tables
The "Table Component" is critical. It must be:
- **Scannable**: Good vertical spacing (padding: 1rem 0).
- **Aligned**: Numbers right-aligned, Text left-aligned.
- **Interactive**: Row hovers.

### Cards
- **Elevation**: Subtle border (1px solid var(--border-color)) rather than heavy shadows.
- **Padding**: Generous (1.5rem+).
- **Header**: Clear separation between title and content.

## Implementation Strategy
1.  **Base Styles**: Ensure `variables.css` captures the palette and typography.
2.  **Layout**: `base.html` handles the top nav and container width.
3.  **Components**: Refine `atoms.html` and `molecules.html` to match the new specs.
4.  **Motion**: Update `ui.js` to trigger GSAP animations on page load and HTMX swaps.

