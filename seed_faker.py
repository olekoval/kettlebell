import random
from datetime import datetime, timedelta, timezone
from faker import Faker
from app import app, db  # Зміни app на свій імпорт, якщо назва файлу інша
from models import Weight, Exercise, WorkoutPlan, WorkoutPlanSet, Workout, WorkoutFact

# Ініціалізуємо Faker з українською локалізацією
fake = Faker('uk_UA')
# Фіксуємо seed для відтворюваності результатів аналітики
Faker.seed(42)
random.seed(42)

def generate_bulk_data(num_plans=100):
    with app.app_context():
        # 1. Отримуємо існуючі ID з довідників
        exercise_ids = [e.id for e in Exercise.query.all()]
        weight_ids = [w.id for w in Weight.query.all()]
        
        if not exercise_ids:
            print("❌ Довідник вправ порожній. Заповніть Exercise перед запуском.")
            return

        print(f"🚀 Починаємо генерацію даних для {num_plans} тренувань...")

        # Початкова точка в минулому (наприклад, 90 днів тому)
        start_date = datetime.now(timezone.utc) - timedelta(days=90)

        for i in range(num_plans):
            # Імітуємо регулярність тренувань (наприклад, кожні 2-3 дні)
            plan_date = start_date + timedelta(days=i * 2 + random.choice([0, 1]))
            
            # --- КРОК 1: Створення WorkoutPlan ---
            status = random.choice(["completed", "completed", "active"]) # частіше виконані
            plan = WorkoutPlan(
                title=f"Силове тренування: {fake.word().upper()}",
                planned_date=plan_date.date(),
                created_at=plan_date - timedelta(days=1), # Створено за день до тренування
                status=status
            )
            db.session.add(plan)
            db.session.flush() # Отримуємо plan.id

            # --- КРОК 2: Створення WorkoutPlanSet (Вправи у плані) ---
            # У кожному тренуванні буде від 3 до 6 вправ
            num_exercises = random.randint(3, 6)
            # Вибираємо випадкові унікальні вправи для цього тренування
            sampled_exercises = random.sample(exercise_ids, min(num_exercises, len(exercise_ids)))
            
            plan_sets = []
            for ex_id in sampled_exercises:
                # 20% шанс, що вправа буде з власною вагою (weight_id = None)
                w_id = random.choice([None] + weight_ids) if weight_ids else None
                
                plan_set = WorkoutPlanSet(
                    workout_plan_id=plan.id,
                    exercise_id=ex_id,
                    weight_id=w_id,
                    number_approaches=random.randint(3, 5), # 3-5 підходів
                    repeat_exercise=random.choice([8, 10, 12, 15]),
                    rest_time=random.choice([60, 90, 120])
                )
                db.session.add(plan_set)
                plan_sets.append(plan_set)
            
            db.session.flush() # Отримуємо id для всіх plan_sets

            # --- КРОК 3: Створення Workout та WorkoutFact (якщо статус completed) ---
            if status == "completed":
                # Фактичний час тренування (планова дата + випадкові години/хвилини)
                actual_datetime = datetime.combine(
                    plan.planned_date, 
                    datetime.min.time()
                ).replace(tzinfo=timezone.utc) + timedelta(hours=random.randint(8, 20), minutes=random.randint(0, 59))

                workout = Workout(
                    workout_plan_id=plan.id,
                    actual_date=actual_datetime,
                    notes=random.choice([None, None, fake.sentence(nb_words=5), "Все пройшло чудово!", "Важко йшли останні підходи"]),
                    status="completed"
                )
                db.session.add(workout)
                db.session.flush()

                # Заповнюємо фактично виконані підходи на основі плану
                for p_set in plan_sets:
                    # Імітуємо реальність: іноді спортсмен робить на 1-2 повторення менше або більше
                    deviation = random.choice([-2, -1, 0, 0, 0, 1])
                    actual_repeats = max(1, p_set.repeat_exercise + deviation)
                    
                    # 5% шанс, що підхід було пропущено взагалі (не додаємо в факт)
                    if random.random() < 0.05:
                        continue

                    workout_fact = WorkoutFact(
                        workout_id=workout.id,
                        workout_plan_set_id=p_set.id,
                        exercise_id=p_set.exercise_id,
                        weight_id=p_set.weight_id,
                        number_approaches=p_set.number_approaches,
                        repeat_exercise=actual_repeats
                    )
                    db.session.add(workout_fact)

        # Фінальний комміт усієї пачки
        db.session.commit()
        print(f"✅ Базу успішно наповнено! Створено {num_plans} планів тренувань та пов'язаних таблиць факту.")

if __name__ == "__main__":
    generate_bulk_data(100) # Згенерує історію на ~100 тренувань (близько 6 місяців)
