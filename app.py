from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from models import db, Workout, WorkoutFact, WorkoutPlan, WorkoutPlanSet
from seed import register_seed_commands
from forms import WorkoutForm, WorkoutPlanForm


# 1. Імпортуємо функцію ініціалізації дашборду
from dashboard import init_dashboard

app = Flask(__name__)

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:#kettlebell@localhost:5433/kettlebell_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-me-in-production'

# Init DB & Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Register seed CLI
register_seed_commands(app)

# 🌟 Ініціалізуємо Dash всередині Flask
init_dashboard(app)

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Головна сторінка — остання виконана сесія + коротка статистика."""

    # Last completed workout (most recent actual_date)
    last_workout = (
        db.session.query(Workout)
        .order_by(Workout.actual_date.desc())
        .first()
    )

    # Total workouts ever
    total_workouts = db.session.query(Workout).count()

    # Workouts this calendar month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = (
        db.session.query(Workout)
        .filter(Workout.actual_date >= month_start)
        .count()
    )

    # Total sets (WorkoutFact rows)
    total_sets = db.session.query(WorkoutFact).count()

    # Active workout plans
    active_plans = (
        db.session.query(WorkoutPlan)
        .filter(WorkoutPlan.status == 'active')
        .count()
    )

    # Ukrainian month name mapping
    ua_months = {
        1: 'Січень', 2: 'Лютий', 3: 'Березень', 4: 'Квітень',
        5: 'Травень', 6: 'Червень', 7: 'Липень', 8: 'Серпень',
        9: 'Вересень', 10: 'Жовтень', 11: 'Листопад', 12: 'Грудень',
    }

    stats = {
        'total_workouts': total_workouts,
        'this_month':     this_month,
        'total_sets':     total_sets,
        'active_plans':   active_plans,
        'month_name':     ua_months[now.month],
    }

    return render_template('index.html', last_workout=last_workout, stats=stats)


@app.route('/plans')
def plans():
    """Список планів тренувань."""
    all_plans = db.session.query(WorkoutPlan).order_by(WorkoutPlan.created_at.desc()).all()
    return render_template('plans.html', plans=all_plans)


@app.route('/plans/new', methods=['GET', 'POST'])
def plans_new():
    """Форма створення нового плану тренування (план + заплановані вправи)."""
    form = WorkoutPlanForm()

    # Кнопка "+ Додати ще вправу" — лише дописуємо порожній рядок і
    # повертаємо ту саму форму з усім уже введеним, без звернення до БД.
    if request.method == 'POST' and 'add_exercise' in request.form:
        form.plan_sets.append_entry()
        return render_template('plan_form.html', form=form)

    if form.validate_on_submit():
        plan = WorkoutPlan(
            title=form.title.data,
            planned_date=form.planned_date.data,
            status=form.status.data,
        )
        for set_form in form.plan_sets:
            if not set_form.is_filled():
                continue  # порожній рядок без обраної вправи — пропускаємо
            plan.plan_sets.append(WorkoutPlanSet(
                exercise_id=set_form.exercise_id.data,
                weight_id=set_form.weight_id.data or None,
                number_approaches=set_form.number_approaches.data or 1,
                repeat_exercise=set_form.repeat_exercise.data or 0,
                rest_time=set_form.rest_time.data,
            ))
        db.session.add(plan)
        db.session.commit()
        flash(f'План «{plan.title}» успішно створено.', 'success')
        return redirect(url_for('plans'))
    return render_template('plan_form.html', form=form)

@app.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
def plans_edit(plan_id):
    """Редагування існуючого плану тренування."""
    plan = db.get_or_404(WorkoutPlan, plan_id)
    
    # Передаємо об'єкт плану в конструктор форми, 
    # щоб WTForms автоматично заповнив базові поля (title, planned_date, status)
    form = WorkoutPlanForm(obj=plan)

    # Кнопка "+ Додати ще вправу"
    if request.method == 'POST' and 'add_exercise' in request.form:
        form.plan_sets.append_entry()
        return render_template('plan_form.html', form=form, is_edit=True, plan=plan)

    # Якщо форма пройшла валідацію (клік на "Зберегти")
    if form.validate_on_submit():
        plan.title = form.title.data
        plan.planned_date = form.planned_date.data
        plan.status = form.status.data

        # Очищуємо старі вправи плану, щоб записати оновлений список
        plan.plan_sets.clear()
        
        for set_form in form.plan_sets:
            if not set_form.is_filled():
                continue
            plan.plan_sets.append(WorkoutPlanSet(
                exercise_id=set_form.exercise_id.data,
                weight_id=set_form.weight_id.data or None,
                number_approaches=set_form.number_approaches.data or 1,
                repeat_exercise=set_form.repeat_exercise.data or 0,
                rest_time=set_form.rest_time.data,
            ))
            
        db.session.commit()
        flash(f'План «{plan.title}» успішно оновлено.', 'success')
        return redirect(url_for('plans'))

    # Для GET-запиту: якщо форма щойно відкрита і FieldList порожній,
    # заповнюємо його існуючими вправами з бази
    if request.method == 'GET' and not form.plan_sets.entries:
        for ps in plan.plan_sets:
            form.plan_sets.append_entry({
                'exercise_id': ps.exercise_id,
                'weight_id': ps.weight_id or 0,
                'number_approaches': ps.number_approaches,
                'repeat_exercise': ps.repeat_exercise,
                'rest_time': ps.rest_time
            })
        # Якщо в плані було менше 4 вправ, WTForms все одно може докинути порожні до min_entries.
        # Але оскільки ми передали дані, краще залишити як є.

    return render_template('plan_form.html', form=form, is_edit=True, plan=plan)

    
@app.route('/workouts')
def workouts():
    """Журнал виконаних тренувань."""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    pagination = (
        db.session.query(Workout)
        .order_by(Workout.actual_date.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return render_template('workouts.html', pagination=pagination)


@app.route('/workouts/new', methods=['GET', 'POST'])
def workouts_new():
    """Форма реєстрації фактично виконаного тренування (+ підходи)."""
    form = WorkoutForm()

    # Кнопка "+ Додати ще підхід" — лише дописуємо порожній рядок і
    # повертаємо ту саму форму з усім уже введеним, без звернення до БД.
    if request.method == 'POST' and 'add_set' in request.form:
        form.actual_sets.append_entry()
        return render_template('workout_form.html', form=form)

    # Кнопка "Підставити вправи з плану" — повністю замінює рядки
    # actual_sets вправами з обраного плану (без звернення до БД).
    if request.method == 'POST' and 'load_plan' in request.form:
        plan = db.session.get(WorkoutPlan, form.workout_plan_id.data) if form.workout_plan_id.data else None
        if plan and plan.plan_sets:
            prefill = [
                {
                    'completed': False,
                    'exercise_id': ps.exercise_id,
                    'weight_id': ps.weight_id or 0,
                    'number_approaches': ps.number_approaches,
                    'repeat_exercise': ps.repeat_exercise,
                }
                for ps in plan.plan_sets
            ]
            form.actual_sets.process(None, prefill)
        else:
            flash('У обраному плані ще немає запланованих вправ.', 'warning')
        return render_template('workout_form.html', form=form)

    if form.validate_on_submit():
        workout = Workout(
            workout_plan_id=form.workout_plan_id.data or None,
            actual_date=form.actual_date.data,
            notes=form.notes.data,
            status=form.status.data,
        )
        for fact_form in form.actual_sets:
            # Якщо користувач НЕ обрав вправу АБО НЕ поставив галочку — повністю ігноруємо цей рядок
            if not fact_form.is_filled():
                continue  
            
            # Логіка визначення ID ваги:
            # Якщо обрано "— без ваги —" (значення 0), записуємо ID 1 ("Власна вага")
            chosen_weight_id = fact_form.weight_id.data
            if chosen_weight_id == 0 or chosen_weight_id is None:
                final_weight_id = 1
            else:
                final_weight_id = chosen_weight_id

            # Записуємо в БД
            workout.actual_sets.append(WorkoutFact(
                exercise_id=fact_form.exercise_id.data,
                weight_id=final_weight_id,  # Тепер тут завжди буде або ID гирі, або 1 (Власна вага)
                number_approaches=fact_form.number_approaches.data if fact_form.number_approaches.data is not None else 1,
                repeat_exercise=fact_form.repeat_exercise.data if fact_form.repeat_exercise.data is not None else 0,
            ))
        db.session.add(workout)
        db.session.commit()
        flash('Тренування успішно збережено.', 'success')
        return redirect(url_for('workout_detail', workout_id=workout.id))

    return render_template('workout_form.html', form=form)


@app.route('/workouts/<int:workout_id>')
def workout_detail(workout_id):
    """Деталі одного виконаного тренування (заглушка)."""
    workout = db.get_or_404(Workout, workout_id)
    return render_template('workout_detail.html', workout=workout)

@app.route('/dashboard-route')
def open_dashboard():
    """Динамічний ендпоінт для кнопки дашборду без хардкоду"""
    return redirect('/dash/')
# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
