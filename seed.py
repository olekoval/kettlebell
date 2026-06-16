import click
from flask.cli import with_appcontext
from models import db, Weight, Exercise

def register_seed_commands(app):
    """Реєстрація CLI команд у Flask додатку"""
    
    @app.cli.command("seed-db")
    @with_appcontext
    def seed_db():
        """Наповнення бази даних початковими довідниками (Weight, Exercise)."""
        click.echo("Початок заповнення бази даних початковими даними...")

        # 1. Наповнення довідника ваг (Weight)
        # Включаємо стандартну лінійку гир + нульову вагу для вправ із власною вагою (bodyweight)
        weights_data = [
            {"tools": "Власна вага", "weight_value": 0.0},
            {"tools": "Гиря чавунна", "weight_value": 16.0},
            {"tools": "Гиря чавунна", "weight_value": 24.0},
            {"tools": "Гиря чавунна", "weight_value": 32.0}
        ]

        click.echo("Додавання ваг у довідник...")
        
        for w in weights_data:
            # Перевіряємо, чи немає вже такої ваги, щоб уникнути дублікатів
            exists = db.session.scalar(
                db.select(Weight).where(
                    Weight.tools == w["tools"], 
                    Weight.weight_value == w["weight_value"]
                )
            )
            if not exists:
                new_weight = Weight(tools=w["tools"], weight_value=w["weight_value"])
                db.session.add(new_weight)

        # 2. Наповнення довідника вправ (Exercise)
        # Базові вправи (Strong Endurance / СФП / Бігові вправи)
        exercises_data = [
            {
                "name_en": "Kettlebell Swing",
                "name_ua": "Махи з гирею",
                "description": "Базова балістична вправа за методикою Павла Цацуліна. Фокус на тазовому домінанті та вибуховій силі."
            },
            {
                "name_en": "Turkish Get-Up (TGU)",
                "name_ua": "Турецький підйом",
                "description": "Повільна вправа на стабільність усього тіла, контроль плечового поясу та координацію."
            },
            {
                "name_en": "Kettlebell Snatch",
                "name_ua": "Ривок гирі",
                "description": "Класична вправа гірового спорту та Hardstyle. Тест на силову витривалість та роботу заднього ланцюга м'язів."
            },
            {
                "name_en": "Kettlebell Clean & Jerk (Long Cycle)",
                "name_ua": "Поштовх за довгим циклом",
                "description": "Максимальна силова витривалість. Поєднання взяття на груди та поштовху двох гир."
            },
            {
                "name_en": "Kettlebell Goblet Squat",
                "name_ua": "Присідання Кубкові",
                "description": "Фундаментальний патерн присідань із утриманням гирі перед грудьми за дужки."
            },
            {
                "name_en": "Kettlebell Press",
                "name_ua": "Жим гирі стоячи",
                "description": "Сувора верхня тиснява сила стоячи (Strict Press) за канонами Hardstyle."
            }
        ]

        click.echo("Додавання вправ у довідник...")
        for ex in exercises_data:
            # Перевіряємо унікальність за name_en або name_ua
            exists = db.session.scalar(
                db.select(Exercise).where(
                    (Exercise.name_en == ex["name_en"]) | (Exercise.name_ua == ex["name_ua"])
                )
            )
            if not exists:
                new_exercise = Exercise(
                    name_en=ex["name_en"],
                    name_ua=ex["name_ua"],
                    description=ex["description"]
                )
                db.session.add(new_exercise)

        try:
            db.session.commit()
            click.echo("Базу даних успішно заповнено початковими даними!")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Помилка під час збереження даних: {e}", err=True)
