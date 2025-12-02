import os
import markdown
from pathlib import Path
from typing import List, Dict, Any, Optional

class DocsService:
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)

    def get_flat_menu(self) -> List[Dict[str, str]]:
        """
        Returns a flat list of docs for the sidebar, ordered intelligently.
        """
        menu = []
        
        # Define preferred order for top-level items
        priority_order = ["specs", "context", "fin-advice"]
        
        # 1. Add root files first (e.g. design_system.md)
        root_files = sorted([f for f in os.listdir(self.docs_dir) if f.endswith('.md')])
        for f in root_files:
            name = f.replace('.md', '').replace('_', ' ').title()
            clean_url = f.replace('.md', '')
            menu.append({
                "title": name,
                "url": f"/docs/{clean_url}",
                "active": False,
                "level": 0
            })
            
        # 2. Add subdirectories
        # Get all dirs in root
        dirs = sorted([d for d in os.listdir(self.docs_dir) if os.path.isdir(self.docs_dir / d) and not d.startswith('.')])
        
        # Sort dirs by priority
        sorted_dirs = sorted(dirs, key=lambda x: priority_order.index(x) if x in priority_order else 999)
        
        for d in sorted_dirs:
            # Add Section Header
            menu.append({
                "title": d.upper().replace('_', ' '),
                "url": "#",
                "is_header": True,
                "level": 0
            })
            
            # List files in subdir
            subdir = self.docs_dir / d
            files = sorted([f for f in os.listdir(subdir) if f.endswith('.md')])
            for f in files:
                # Clean up name
                name = f.replace('.md', '').replace('_', ' ').title()
                clean_filename = f.replace('.md', '')
                
                # Remove numbering if present (e.g. 01_ONBOARDING -> Onboarding)
                parts = name.split(' ')
                if parts[0].isdigit():
                    name = ' '.join(parts[1:])
                
                menu.append({
                    "title": name,
                    "url": f"/docs/{d}/{clean_filename}",
                    "active": False,
                    "level": 1
                })
                
        return menu

    def get_page_content(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Reads and renders a markdown file.
        """
        # Security check: prevent directory traversal
        safe_path = os.path.normpath(path)
        if '..' in safe_path:
            return None
            
        # Try adding .md if not present
        if not safe_path.endswith('.md'):
            safe_path += '.md'
            
        full_path = self.docs_dir / safe_path
        
        if not full_path.exists():
            return None
            
        with open(full_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Render Markdown
        # Use extra extensions for better rendering (tables, fenced code, etc.)
        html_content = markdown.markdown(
            text,
            extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists', 'toc']
        )
        
        title = safe_path.split('/')[-1].replace('.md', '').replace('_', ' ').title()
        if title.split(' ')[0].isdigit():
             title = ' '.join(title.split(' ')[1:])
             
        return {
            "title": title,
            "content": html_content,
            "raw": text
        }
