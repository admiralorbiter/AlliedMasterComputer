# flask_app/routes/docs.py

"""
Documentation routes - serves markdown files from the docs directory
"""

import os
import markdown
from flask import render_template, abort, current_app
from markupsafe import Markup


def register_docs_routes(app):
    """Register documentation routes"""
    
    # Configure markdown with extensions
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'nl2br'
    ])
    
    def get_docs_dir():
        """Get the docs directory path"""
        # app.root_path is the project root (where app.py is)
        return os.path.join(app.root_path, 'docs')
    
    def get_docs_list():
        """Get list of available documentation files"""
        docs_dir = get_docs_dir()
        docs = []
        
        if os.path.exists(docs_dir):
            for filename in os.listdir(docs_dir):
                if filename.endswith('.md'):
                    # Read first line for title
                    filepath = os.path.join(docs_dir, filename)
                    title = filename.replace('.md', '').replace('-', ' ').title()
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            first_line = f.readline().strip()
                            if first_line.startswith('# '):
                                title = first_line[2:]
                    except Exception:
                        pass
                    
                    docs.append({
                        'filename': filename,
                        'title': title,
                        'is_readme': filename.lower() == 'readme.md'
                    })
        
        # Sort: README first, then alphabetically
        docs.sort(key=lambda x: (not x['is_readme'], x['title'].lower()))
        return docs
    
    @app.route('/docs')
    @app.route('/docs/')
    def docs_index():
        """Documentation index - shows README.md"""
        return docs_view('README.md')
    
    @app.route('/docs/<path:filename>')
    def docs_view(filename):
        """View a documentation file"""
        # Security: prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            abort(404)
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename = filename + '.md'
        
        docs_dir = get_docs_dir()
        filepath = os.path.join(docs_dir, filename)
        
        # Check file exists
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            abort(404)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reset markdown instance and convert
            md.reset()
            html_content = md.convert(content)
            
            # Get table of contents if available
            toc = getattr(md, 'toc', '')
            
            # Get list of all docs for sidebar
            docs_list = get_docs_list()
            
            return render_template('docs/view.html',
                                   content=Markup(html_content),
                                   toc=Markup(toc),
                                   filename=filename,
                                   docs_list=docs_list)
        
        except Exception as e:
            current_app.logger.error(f"Error reading doc {filename}: {str(e)}")
            abort(500)
