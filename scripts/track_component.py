import json
import os
import sys

REGISTRY_PATH = 'design_system/registry.json'

def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {"components": {}, "version": "1.0.0"}
    with open(REGISTRY_PATH, 'r') as f:
        return json.load(f)

def save_registry(data):
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Updated {REGISTRY_PATH}")

def main():
    print("🎨 Design System Component Tracker")
    print("--------------------------------")
    
    name = input("Component Name (e.g., 'HeroBanner'): ").strip()
    if not name:
        print("Name is required.")
        return

    registry = load_registry()
    
    if name in registry['components']:
        print(f"Warning: '{name}' already exists. Updating...")
    
    description = input("Description: ").strip()
    status = input("Status (stable/beta/experimental) [stable]: ").strip() or "stable"
    
    variants_input = input("Variants (comma separated) [default]: ").strip()
    variants = [v.strip() for v in variants_input.split(',')] if variants_input else ["default"]
    
    css_class = input("CSS Class selector (e.g. .hero-banner): ").strip()
    
    files_input = input("Related Files (comma separated): ").strip()
    files = [f.strip() for f in files_input.split(',')] if files_input else []

    registry['components'][name] = {
        "status": status,
        "description": description,
        "variants": variants,
        "css_class": css_class,
        "files": files
    }
    
    save_registry(registry)
    print("✅ Component tracked successfully!")

if __name__ == "__main__":
    main()
