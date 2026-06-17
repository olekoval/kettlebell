"""
Модуль форм для внесення даних по тренуваннях.

Містить класи Flask-WTF форм для:
  * WorkoutPlanForm      — створення/редагування плану тренування (+ вкладені вправи плану)
  * WorkoutPlanSetForm   — один рядок плану (вправа, вага, підходи, повтори, відпочинок)
  * WorkoutForm          — реєстрація фактично виконаного тренування (+ вкладені факти)
  * WorkoutFactForm      — один фактично виконаний підхід

Довідникові поля (вправа, вага, план) заповнюються динамічно з бази даних,
тому choices для відповідних SelectField встановлюються в __init__, а не
на рівні класу — це гарантує актуальний список навіть після сидування БД.

Узгоджено з ТЗ: фронтенд на Bootstrap 5, без використання користувацького
JavaScript. Тому довільну кількість рядків (вправ плану / підходів
тренування) додають через окрему submit-кнопку «+ Додати ще ...»: клік
по ній лише дописує до FieldList ще один порожній FormField і повторно
рендерить ту саму форму (без збереження в БД, з усіма вже введеними
даними), а основна кнопка «Зберегти» — валідовує й зберігає. Див.
WorkoutPlanForm.add_exercise / WorkoutForm.add_set та відповідну логіку
в app.py. Порожні рядки (без обраної вправи) при збереженні просто
ігноруються — див. is_filled().
"""

from wtforms import (
    BooleanField,
    DateField,
    DateTimeField,
    FieldList,
    FormField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

# pyrefly: ignore [missing-import]
from flask_wtf import FlaskForm

from models import Exercise, Weight, WorkoutPlan

# ─── Допоміжні функції для довідників ──────────────────────────────────────

# Значення-«пустишка» для необов'язкових SelectField (FK), що означає
# «нічого не обрано» — при збереженні замінюється на None.
EMPTY_CHOICE = 0


def exercise_choices():
    """Список вправ для SelectField: [(id, 'Назва (English)'), ...]."""
    exercises = Exercise.query.order_by(Exercise.name_ua).all()
    return [(e.id, f"{e.name_ua} ({e.name_en})") for e in exercises]


def weight_choices():
    """Список ваг для SelectField: [(id, 'Інвентар — N кг'), ...]."""
    weights = Weight.query.order_by(Weight.weight_value).all()
    return [(w.id, f"{w.tools} — {w.weight_value:g} кг") for w in weights]


def plan_choices():
    """Список планів тренувань для SelectField (від найновіших)."""
    plans = WorkoutPlan.query.order_by(WorkoutPlan.created_at.desc()).all()
    return [(p.id, p.title) for p in plans]


# ─── Форми для плану тренування (WorkoutPlan / WorkoutPlanSet) ─────────────

class WorkoutPlanSetForm(FlaskForm):
    """Один елемент плану: запланована вправа з вагою, підходами та відпочинком."""

    class Meta:
        # CSRF-токен видається лише батьківською формою (WorkoutPlanForm),
        # вкладені під-форми його не дублюють.
        csrf = False

    exercise_id = SelectField(
        "Вправа",
        coerce=int,
        validators=[Optional()],
    )
    weight_id = SelectField(
        "Вага",
        coerce=int,
        validators=[Optional()],
    )
    number_approaches = IntegerField(
        "Підходів",
        default=1,
        validators=[Optional(), NumberRange(min=0, max=50, message="0–50")],
    )
    repeat_exercise = IntegerField(
        "Повторень у підході",
        default=0,
        validators=[Optional(), NumberRange(min=0, max=200, message="0–200")],
    )
    rest_time = IntegerField(
        "Відпочинок, сек",
        validators=[Optional(), NumberRange(min=0, max=3600, message="0–3600")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exercise_id.choices = [(EMPTY_CHOICE, "— оберіть вправу —")] + exercise_choices()
        self.weight_id.choices = [(EMPTY_CHOICE, "— без ваги —")] + weight_choices()

    def is_filled(self):
        """Рядок вважається заповненим, якщо обрано вправу."""
        return bool(self.exercise_id.data) and self.exercise_id.data != EMPTY_CHOICE


class WorkoutPlanForm(FlaskForm):
    """Форма створення/редагування плану тренування зі списком вправ."""

    title = StringField(
        "Назва плану",
        validators=[DataRequired(message="Вкажіть назву плану"), Length(max=100)],
    )
    planned_date = DateField(
        "Запланована дата",
        validators=[Optional()],
        render_kw={"type": "date"},
    )
    status = SelectField(
        "Статус",
        choices=[
            ("active", "Активний"),
            ("completed", "Завершений"),
            ("cancelled", "Скасований"),
        ],
        default="active",
        validators=[Optional()],
    )
    plan_sets = FieldList(FormField(WorkoutPlanSetForm), min_entries=4, max_entries=100)
    add_exercise = SubmitField("+ Додати ще вправу")
    submit = SubmitField("Зберегти план")


# ─── Форми для факту тренування (Workout / WorkoutFact) ────────────────────

class WorkoutFactForm(FlaskForm):
    """Один фактично виконаний підхід у межах тренування."""

    class Meta:
        csrf = False

    completed = BooleanField("Виконано", default=True)
    exercise_id = SelectField(
        "Вправа",
        coerce=int,
        validators=[Optional()],
    )
    weight_id = SelectField(
        "Вага",
        coerce=int,
        validators=[Optional()],
    )
    number_approaches = IntegerField(
        "Підходів виконано",
        default=1,
        validators=[Optional(), NumberRange(min=0, max=50, message="0–50")],
    )
    repeat_exercise = IntegerField(
        "Повторень виконано",
        default=0,
        validators=[Optional(), NumberRange(min=0, max=200, message="0–200")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exercise_id.choices = [(EMPTY_CHOICE, "— оберіть вправу —")] + exercise_choices()
        self.weight_id.choices = [(EMPTY_CHOICE, "— без ваги —")] + weight_choices()

    def is_filled(self):
        """Рядок зберігається лише якщо обрано вправу І позначено «Виконано»."""
        has_exercise = bool(self.exercise_id.data) and self.exercise_id.data != EMPTY_CHOICE
        return has_exercise and self.completed.data


class WorkoutForm(FlaskForm):
    """Форма реєстрації фактично виконаного тренування зі списком підходів."""

    workout_plan_id = SelectField(
        "План тренування",
        coerce=int,
        validators=[Optional()],
    )
    actual_date = DateTimeField(
        "Дата і час виконання",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message="Вкажіть дату та час")],
        render_kw={"type": "datetime-local"},
    )
    status = SelectField(
        "Статус",
        choices=[
            ("completed", "Виконано"),
            ("partial", "Виконано частково"),
            ("skipped", "Пропущено"),
        ],
        default="completed",
        validators=[Optional()],
    )
    notes = TextAreaField(
        "Примітки (самопочуття, пульс тощо)",
        validators=[Optional(), Length(max=2000)],
    )
    actual_sets = FieldList(FormField(WorkoutFactForm), min_entries=6, max_entries=100)
    load_plan = SubmitField("Підставити вправи з плану")
    add_set = SubmitField("+ Додати ще підхід")
    submit = SubmitField("Зберегти тренування")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workout_plan_id.choices = [(EMPTY_CHOICE, "— без плану —")] + plan_choices()
