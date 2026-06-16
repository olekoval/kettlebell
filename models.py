from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

# 1. Створюємо базовий клас, як вимагає нова документація
class Base(DeclarativeBase):
    pass

# Ініціалізуємо розширення, передаючи наш базовий клас
db = SQLAlchemy(model_class=Base)


class Exercise(db.Model):
    """1. Довідник вправ"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Workout(db.Model):
    """2. Тренувальні сесії"""
    __tablename__ = 'workouts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Зв'язок один-до-багатьох (Workout -> WorkoutSet) з каскадним видаленням
    sets: Mapped[List["WorkoutSet"]] = relationship(
        back_populates="workout", 
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Workout {self.date}>"


class WorkoutSet(db.Model):
    """3. Виконання підходів"""
    __tablename__ = 'workout_sets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Зовнішні ключі
    workout_id: Mapped[int] = mapped_column(ForeignKey('workouts.id'), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey('exercises.id'), nullable=False)
    
    # Специфічні поля підходу
    weight: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False) # вага гирі
    reps: Mapped[int] = mapped_column(Integer, nullable=False)          # повторення
    rest_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # відпочинок
    set_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)    # черговість

    # Зворотні зв'язки для зв'язування об'єктів у коді
    workout: Mapped["Workout"] = relationship(back_populates="sets")
    exercise: Mapped["Exercise"] = relationship(back_populates="sets")

    def __repr__(self) -> str:
        return f"<WorkoutSet {self.weight}kg x {self.reps}>"
