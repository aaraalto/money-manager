import json
import os

def generate_css_variables(tokens_path, output_path):
    with open(tokens_path, 'r') as f:
        tokens = json.load(f)

    css_lines = [":root {"]

    # Colors
    for category, values in tokens['colors'].items():
        for name, value in values.items():
            css_lines.append(f"    --{category}-{name}: {value};")
            if category == "brand":
                # Alias for legacy support if needed, or cleaner access
                css_lines.append(f"    --{name}: {value};")
            if category == "status":
                css_lines.append(f"    --{name}: {value};")

    # Spacing
    for name, value in tokens['spacing'].items():
        css_lines.append(f"    --space-{name}: {value};")
    
    # Spacing Aliases
    aliases = {
        "xs": "2", "sm": "3", "md": "4", "lg": "6", "xl": "8", "2xl": "12"
    }
    for alias, target in aliases.items():
        css_lines.append(f"    --space-{alias}: var(--space-{target});")

    # Radius
    for name, value in tokens['radius'].items():
        css_lines.append(f"    --radius-{name}: {value};")

    # Shadows
    for name, value in tokens['shadows'].items():
        css_lines.append(f"    --shadow-{name}: {value};")

    # Typography
    for name, value in tokens['typography'].items():
        css_lines.append(f"    --{name}: {value};")

    css_lines.append("}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(css_lines))
    
    print(f"Generated {output_path} from {tokens_path}")

if __name__ == "__main__":
    generate_css_variables('design_system/tokens.json', 'frontend/css/variables.css')
