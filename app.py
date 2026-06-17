from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from models import db, Workout, WorkoutFact, WorkoutPlan
from seed import register_seed_commands

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
    """Форма додавання нового виконаного тренування (заглушка)."""
    # Full implementation comes in the next iteration (forms + WorkoutFact creation)
    flash('Форма запису тренування — в розробці.', 'info')
    return redirect(url_for('index'))


@app.route('/workouts/<int:workout_id>')
def workout_detail(workout_id):
    """Деталі одного виконаного тренування (заглушка)."""
    workout = db.get_or_404(Workout, workout_id)
    return render_template('workout_detail.html', workout=workout)


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
