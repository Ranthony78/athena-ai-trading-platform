import os
import sys
import subprocess
import ast

# Always use the same Python that is running this script (respects .venv)
PY = sys.executable
PIP = [PY, '-m', 'pip']

output = []

SKIP_DIRS = ['__pycache__', '.git', 'venv', '.venv', 'env', 'node_modules', '.idea', '.vs']
SKIP_DIRS_MIGRATIONS = SKIP_DIRS + ['migrations']

# ══════════════════════════════════════════════════════════════
# PROJECT INSTRUCTIONS
# ══════════════════════════════════════════════════════════════
output.append("""# CLAUDE.md — Project Reference

## Project Instructions
- This is a Django project using **SQLite (`db.sqlite3`)** database
- Always check existing models before creating new ones — never duplicate
- Never overwrite existing logic, only extend it
- Always use existing naming conventions found in the codebase
- Check for duplicate functions/classes before adding new ones


### API & Backend Rules
- Follow Django REST Framework (DRF) patterns for all APIs
- Always add proper error handling (try/except, form validation, API errors)
- Add comments to complex logic
- Prefer class-based views (CBV) over function-based where possible
- Always use csrf_token in forms
- Use messages.success/error for user feedback

### Frontend & UI Rules
- Use Bootstrap 5 for all frontend layouts
- Use Font Awesome 6 for all icons
- Use Chart.js for graphs and reports
- Use DataTables for all list/table views with search and pagination
- Use Bootstrap cards with shadows for data display panels
- Use Bootstrap modals for create/edit forms
- Use gradient headers on cards and navbars for modern look
- Use toasts for success/error notifications
- Keep templates DRY — always use extends base.html and include tags
- All pages must have a consistent sidebar and topbar from base.html
- Color scheme: follow existing styles found in static/css/
- Never use inline styles — always use CSS classes

""")

# ══════════════════════════════════════════════════════════════
# 1. FOLDER STRUCTURE
# ══════════════════════════════════════════════════════════════
print("📁 Scanning folder structure...")
output.append("## 1. Folder Structure\n```")
for root, dirs, files in os.walk('.'):
    dirs[:] = sorted([d for d in dirs if d not in SKIP_DIRS])
    level = root.replace('.', '').count(os.sep)
    indent = ' ' * 2 * level
    output.append(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in sorted(files):
        output.append(f"{subindent}{file}")
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 2. DATABASE STRUCTURE (Live MySQL)
# ══════════════════════════════════════════════════════════════
print("🗄️  Extracting live MySQL DB structure...")
output.append("## 2. Database Structure (Live MySQL — inspectdb)\n```python")
try:
    result = subprocess.run(
        [PY, 'manage.py', 'inspectdb'],
        capture_output=True, text=True
    )
    output.append(result.stdout if result.stdout else "# No output from inspectdb")
    if result.stderr:
        output.append(f"# stderr: {result.stderr[:800]}")
except Exception as e:
    output.append(f"# Could not extract DB: {e}")
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 3. MIGRATION HISTORY
# ══════════════════════════════════════════════════════════════
print("🔀 Extracting migration history...")
output.append("## 3. Migration History\n```")
try:
    result = subprocess.run(
        [PY, 'manage.py', 'showmigrations'],
        capture_output=True, text=True
    )
    output.append(result.stdout if result.stdout else "# No migrations found")
except Exception as e:
    output.append(f"# Could not extract migrations: {e}")
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 4. ALL URL ENDPOINTS
# ══════════════════════════════════════════════════════════════
print("🌐 Extracting URL endpoints...")
output.append("## 4. All URL Endpoints\n```")
try:
    result = subprocess.run(
        [PY, 'manage.py', 'show_urls'],
        capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout:
        output.append(result.stdout)
    else:
        output.append("# django-extensions not installed — run: pip install django-extensions")
        output.append("# Then add 'django_extensions' to INSTALLED_APPS in settings.py")
except Exception as e:
    output.append(f"# Could not extract URLs: {e}")
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 5. INSTALLED PACKAGES
# ══════════════════════════════════════════════════════════════
print("📦 Extracting installed packages...")
output.append("## 5. Installed Packages\n```")
try:
    result = subprocess.run(PIP + ['freeze'], capture_output=True, text=True)
    output.append(result.stdout if result.stdout else "# No packages found")
except Exception as e:
    output.append(f"# Could not extract packages: {e}")
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 6. ENVIRONMENT VARIABLES (keys only)
# ══════════════════════════════════════════════════════════════
print("🔑 Scanning environment variables...")
output.append("## 6. Environment Variables (keys only — values hidden)\n```")
env_found = False
for env_file in ['.env', '.env.local', '.env.dev', '.env.production']:
    if os.path.exists(env_file):
        env_found = True
        output.append(f"# From {env_file}:")
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key = line.split('=')[0]
                        output.append(f"{key}=***")
        except Exception as e:
            output.append(f"# Could not read {env_file}: {e}")
if not env_found:
    output.append("# No .env file found")
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 7. DUPLICATE FUNCTION & CLASS CHECKER
# ══════════════════════════════════════════════════════════════
print("🔍 Checking for duplicate functions and classes...")
output.append("## 7. Duplicate Function & Class Report\n```")
func_map = {}
class_map = {}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS_MIGRATIONS]
    for filename in files:
        if filename.endswith('.py'):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_map.setdefault(node.name, []).append(filepath)
                    elif isinstance(node, ast.ClassDef):
                        class_map.setdefault(node.name, []).append(filepath)
            except Exception:
                pass

ignore_funcs = {'__str__', '__repr__', '__init__', 'get', 'post', 'save',
                'delete', 'clean', 'setUp', 'tearDown', 'dispatch', 'form_valid',
                'form_invalid', 'get_queryset', 'get_context_data', 'get_object'}
dup_found = False

for name, paths in func_map.items():
    if len(paths) > 1 and name not in ignore_funcs:
        output.append(f"WARNING: Duplicate function '{name}' in:")
        for p in paths:
            output.append(f"    - {p}")
        dup_found = True

for name, paths in class_map.items():
    if len(paths) > 1:
        output.append(f"WARNING: Duplicate class '{name}' in:")
        for p in paths:
            output.append(f"    - {p}")
        dup_found = True

if not dup_found:
    output.append("OK: No duplicate functions or classes found.")
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 8. KEY DJANGO PYTHON FILES (all apps)
# ══════════════════════════════════════════════════════════════
print("🐍 Reading Django Python files...")
key_filenames = [
    'settings.py', 'models.py', 'views.py', 'urls.py',
    'forms.py', 'serializers.py', 'admin.py', 'signals.py',
    'managers.py', 'middleware.py', 'permissions.py', 'filters.py',
    'apps.py', 'utils.py', 'constants.py', 'helpers.py',
    'decorators.py', 'validators.py', 'tasks.py', 'requirements.txt',
    'context_processors.py', 'mixins.py', 'choices.py', 'exceptions.py',
]

output.append("## 8. Django Python Files\n")
seen_files = set()
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS_MIGRATIONS]
    for filename in sorted(files):
        if filename in key_filenames:
            filepath = os.path.join(root, filename)
            if filepath in seen_files:
                continue
            seen_files.add(filepath)
            output.append(f"### {filepath}\n```python")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    output.append(f.read())
            except Exception as e:
                output.append(f"# Could not read file: {e}")
            output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 9. BASE & LAYOUT TEMPLATES (frontend foundation)
# ══════════════════════════════════════════════════════════════
print("🎨 Reading base/layout templates...")
output.append("## 9. Base & Layout Templates (Frontend Foundation)\n")

base_names = [
    'base.html', 'base_template.html', 'layout.html', 'master.html',
    'navbar.html', 'sidebar.html', 'footer.html', 'header.html',
    'topbar.html', 'breadcrumb.html', 'pagination.html',
    'messages.html', 'alerts.html',
]

seen_templates = set()
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for filename in sorted(files):
        if filename in base_names:
            filepath = os.path.join(root, filename)
            if filepath in seen_templates:
                continue
            seen_templates.add(filepath)
            output.append(f"### BASE: {filepath}\n```html")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    output.append(f.read())
            except Exception as e:
                output.append(f"<!-- Could not read: {e} -->")
            output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 10. ALL OTHER HTML TEMPLATES (per app)
# ══════════════════════════════════════════════════════════════
print("🌐 Reading all HTML templates...")
output.append("## 10. All HTML Templates (per app)\n")

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for filename in sorted(files):
        if filename.endswith('.html'):
            filepath = os.path.join(root, filename)
            if filepath in seen_templates:
                continue
            seen_templates.add(filepath)
            output.append(f"### {filepath}\n```html")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    output.append(f.read())
            except Exception as e:
                output.append(f"<!-- Could not read: {e} -->")
            output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 11. CUSTOM CSS FILES
# ══════════════════════════════════════════════════════════════
print("🎨 Reading CSS files...")
output.append("## 11. Custom CSS Files\n")

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for filename in sorted(files):
        if filename.endswith('.css'):
            filepath = os.path.join(root, filename)
            output.append(f"### {filepath}\n```css")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if len(content) < 80000:
                    output.append(content)
                else:
                    output.append(f"/* File too large (minified) — {len(content)} chars, skipped */")
            except Exception as e:
                output.append(f"/* Could not read: {e} */")
            output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 12. CUSTOM JS FILES
# ══════════════════════════════════════════════════════════════
print("⚡ Reading JS files...")
output.append("## 12. Custom JavaScript Files\n")

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for filename in sorted(files):
        if filename.endswith('.js'):
            filepath = os.path.join(root, filename)
            output.append(f"### {filepath}\n```javascript")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if len(content) < 80000:
                    output.append(content)
                else:
                    output.append(f"// File too large (minified) — {len(content)} chars, skipped")
            except Exception as e:
                output.append(f"// Could not read: {e}")
            output.append("```\n")

# ══════════════════════════════════════════════════════════════
# 13. FRONTEND COMPONENT INVENTORY
# ══════════════════════════════════════════════════════════════
print("📋 Building frontend component inventory...")
output.append("## 13. Frontend Component Inventory\n```")

template_count = 0
extends_base = 0
uses_datatables = 0
uses_charts = 0
uses_modals = 0
uses_forms = 0
component_list = []

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for filename in sorted(files):
        if filename.endswith('.html'):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                template_count += 1
                features = []
                if 'extends' in content:
                    extends_base += 1
                    features.append('extends base')
                if 'datatable' in content:
                    uses_datatables += 1
                    features.append('DataTable')
                if 'chart' in content:
                    uses_charts += 1
                    features.append('Chart')
                if 'modal' in content:
                    uses_modals += 1
                    features.append('Modal')
                if '<form' in content:
                    uses_forms += 1
                    features.append('Form')
                component_list.append(f"  {filepath}: [{', '.join(features) if features else 'standalone'}]")
            except Exception:
                pass

output.append(f"Total templates     : {template_count}")
output.append(f"Extend base.html    : {extends_base}")
output.append(f"Use DataTables      : {uses_datatables}")
output.append(f"Use Charts          : {uses_charts}")
output.append(f"Use Modals          : {uses_modals}")
output.append(f"Have Forms          : {uses_forms}")
output.append("")
output.append("Per-template breakdown:")
output.extend(component_list)
output.append("```\n")

# ══════════════════════════════════════════════════════════════
# WRITE CLAUDE.md
# ══════════════════════════════════════════════════════════════
print("\n💾 Writing CLAUDE.md...")
with open('CLAUDE.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

file_size_kb = os.path.getsize('CLAUDE.md') / 1024
file_size_mb = file_size_kb / 1024

print(f"""
+----------------------------------------------------------+
|        CLAUDE.md Generated Successfully!                 |
+----------------------------------------------------------+
|  Location : {os.getcwd()}\\CLAUDE.md
|  Size     : {file_size_kb:.1f} KB  ({file_size_mb:.2f} MB)
|  Templates: {template_count} HTML files scanned
+----------------------------------------------------------+
|  Next Steps:                                             |
|  1. Go to claude.ai and open Projects                    |
|  2. Open or create your Django project                   |
|  3. Click Add Content and upload CLAUDE.md               |
|  4. Start chatting with full project context!            |
+----------------------------------------------------------+
""")