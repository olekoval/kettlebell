
# Технічне завдання (ТЗ)

## Вебдодаток для обліку та аналізу тренувань із гирями (Kettlebell Progress Tracker)

## 1. Загальний опис проєкту

Проєкт являє собою особистий вебдодаток для реєстрації, збереження та аналізу тренувальних сесій із гирями. Основна мета — відстеження прогресу (об'єм, інтенсивність, кількість повторень) за допомогою графіків та аналітичної панелі (дашборду).

## 2. Стек технологій

- **Backend:** Python 3.12+, Flask
    
- **Аналітика та Візуалізація:** Plotly Dash (інтегрований у Flask)
    
- **База даних:** PostgreSQL (взаємодія через SQLAlchemy / Psycopg2)
    
- **Frontend:** HTML5, CSS Grid (для макетів сторінок), Bootstrap 5 (для стилізації компонентів та форм). **Використання користувацького JavaScript повністю виключено.**

## 3. Особливості інтеграції Plotly Dash у Flask

Щоб Dash не конфліктував із загальною структурою і не вимагав написання JS:

1. Dash ініціалізується всередині Flask-додатка: `dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dash/')`.
## 4. Дерево проєкту

kettlebell_tracker/
│
├── app.py                 # Головний файл запуску Flask, тут ініціалізується БД
├── models.py              # ТУТ ЖИВУТЬ НАШІ ТАБЛИЦІ (Weight, Exercise, WorkoutPlan, WorkoutPlanSet, Workout, WorkoutFact)
├── dash_app/              # Папка з логікою Plotly Dash (дашборди)
│   └── dashboard.py
│
├── templates/             # HTML-шаблони (Bootstrap + CSS Grid)
│   ├── base.html
│   ├── index.html
│   └── workouts.html
│
├── static/                # Статичні файли (твій custom css файл із Grid)
│   └── css/
│       └── style.css
│
├── requirements.txt       # Залежності (Flask, Flask-SQLAlchemy, pandas, dash)
└── config.py              # Налаштування підключення до PostgreSQL


## 5. Структура бази даних (Схема на основі зображення з виправленнями)

Згідно з погодженою архітектурою, база даних містить 6 основних таблиць для розділення запланованих тренувань та фактичних результатів:

### 0. `Weight` (Довідник інвентарю/ваг)
- `id` (Integer, Primary Key) — автоінкрементний ідентифікатор
- `tools` (String(50), Not Null) — тип інвентарю (наприклад, "Гиря чавунна")
- `weight_value` (Float, Not Null) — вага інвентарю в кг (наприклад, 16.0)

### 1. `Exercise` (Довідник вправ)
- `id` (Integer, Primary Key) — автоінкрементний ідентифікатор
- `name_en` (String(100), Unique, Not Null) — назва вправи англійською
- `name_ua` (String(100), Unique, Not Null) — назва вправи українською
- `description` (Text, Nullable) — детальний опис вправи

### 2. `WorkoutPlan` (Заплановане тренування - Сесія)
- `id` (Integer, Primary Key) — автоінкрементний ідентифікатор
- `title` (String(100), Not Null) — назва плану (наприклад, "Понеділок: Сила")
- `planned_date` (Date, Nullable) — очікувана дата виконання
- `created_at` (DateTime, Default: now) — дата створення плану
- `status` (String(20), Nullable) — статус плану (наприклад, "active", "completed")

### 3. `WorkoutPlanSet` (Елементи плану тренування)
- `id` (Integer, Primary Key) — автоінкрементний ідентифікатор
- `workout_plan_id` (Integer, ForeignKey -> WorkoutPlan.id, On Delete Cascade)
- `exercise_id` (Integer, ForeignKey -> Exercise.id)
- `weight_id` (Integer, ForeignKey -> Weight.id, Nullable) — орієнтовна вага гирі з довідника ваг
- `number_approaches` (Integer, Default: 1) — кількість підходів (approaches)
- `repeat_exercise` (Integer, Default: 0) — кількість повторень в одному підході
- `rest_time` (Integer, Nullable) — час відпочинку між підходами (у секундах)

### 4. `Workout` (Факт виконання тренування - Сесія)
- `id` (Integer, Primary Key) — автоінкрементний ідентифікатор
- `workout_plan_id` (Integer, ForeignKey -> WorkoutPlan.id, Nullable, On Delete Set Null) — посилання на план
- `actual_date` (DateTime, Default: now, Not Null) — дата та час реального виконання
- `notes` (Text, Nullable) — коментарі користувача (самопочуття, пульс тощо)
- `status` (String(20), Nullable) — статус виконання (наприклад, "completed", "skipped")

### 5. `WorkoutFact` (Фактично виконані підходи)
- `id` (Integer, Primary Key) — автоінкрементний ідентифікатор
- `workout_id` (Integer, ForeignKey -> Workout.id, On Delete Cascade) — зв'язок з виконаним тренуванням
- `workout_plan_set_id` (Integer, ForeignKey -> WorkoutPlanSet.id, Nullable, On Delete Set Null) — зв'язок із конкретним запланованим підходом
- `exercise_id` (Integer, ForeignKey -> Exercise.id) — зв'язок з вправою
- `weight_id` (Integer, ForeignKey -> Weight.id) — посилання на фактично використану гирю з довідника ваг
- `number_approaches` (Integer, Default: 1) — фактична кількість виконаних підходів
- `repeat_exercise` (Integer, Default: 0) — фактична кількість повторень


