from rich.tree import Tree
from rich import print

tree = Tree("kettlebell")

def add_node(target_tree, name: str, desc: str = ""):
    """
    Додає елемент до дерева. 
    Фарбує .py у жовтий, .html/.css у зелений, та ідеально вирівнює описи.
    """
    # Визначаємо колір залежно від розширення
    if name.endswith(".py"):
        color = "yellow"
    elif name.endswith(".html") or name.endswith(".css"):
        color = "green"
    elif name.endswith(".md") or name.endswith(".css"):
        color = "dodger_blue2"
    else:
        color = "white"
        
    if desc:
        # Спочатку вирівнюємо чисте ім'я пробілами (наприклад, до 35 символів)
        aligned_name = name.ljust(35)
        # Потім огортаємо в теги кольору й додаємо опис
        target_tree.add(f"[{color}]{aligned_name}[/{color}][grey70]<- {desc}[/grey70]")
    else:
        target_tree.add(f"[{color}]{name}[/{color}]")

# --- 1. Файли в корені проекту ---
root_files = [
    (".gitignore", "Ігнорування непотрібних файлів у Git"),
    ("app.py", "Головний файл запуску Flask-додатку"),
    ("dashboard.py", "Панель аналітики та метрик"),
    ("database_schema.md", "Опис структури та зв'язків БД"),
    ("forms.py", "Валідація форм (WTForms)"),
    ("models.py", "Опис моделей SQLAlchemy / таблиць БД"),
    ("poetry.lock", "Фіксація точних версій залежностей Poetry"),
    ("pyproject.toml", "Конфігурація проекту та залежностей"),
    ("README.md", "Документація проекту"),
    ("seed.py", "Базове наповнення БД первинними даними"),
    ("seed_faker.py", "Генерація фейкових користувачів/тренувань"),
    ("ТЗ Kettlbery.md", "Технічне завдання проекту")
]

for file, desc in root_files:
    add_node(tree, file, desc)

# --- 2. Папка міграцій (Alembic) ---
mig_tree = tree.add("migrations")
add_node(mig_tree, "alembic.ini", "Конфігурація Alembic")
add_node(mig_tree, "env.py", "Скрипт налаштування середовища міграцій")
add_node(mig_tree, "README", "Інфо про міграції")
add_node(mig_tree, "script.py.mako", "Шаблон для генерації нових міграцій")

# Підпапка версій
ver_tree = mig_tree.add("versions")
add_node(ver_tree, "a892baa22d42_initial_migration.py", "Перша міграція (створення таблиць)")

# --- 3. Статичні файли (CSS / JS) ---
static_tree = tree.add("static")
css_tree = static_tree.add("css")
add_node(css_tree, "style.css", "Головні стилі додатку")

# --- 4. Шаблони (HTML Jinja2) ---
templates_tree = tree.add("templates")
templates = [
    ("base.html", "Базовий шаблон (Layout)"),
    ("index.html", "Головна сторінка"),
    ("plans.html", "Список планів тренувань"),
    ("plan_form.html", "Форма створення/редагування плану"),
    ("workouts.html", "Журнал тренувань"),
    ("workout_detail.html", "Деталі конкретного тренування"),
    ("workout_form.html", "Форма запису тренування"),
    ("_formhelpers.html", "Макроси для рендерингу полів форм")
]

for tpl, desc in templates:
    add_node(templates_tree, tpl, desc)

# Виведення готового дерева в консоль
print(tree)