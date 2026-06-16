from datetime import datetime, date
from typing import Optional, List
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Text, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Weight(db.Model):
    """Довідник інвентарю (ваги)"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tools: Mapped[str] = mapped_column(String(50))           # Напр. "Гиря чавунна"
    weight_value: Mapped[float] = mapped_column(Float)       # Напр. 16.0

class Exercise(db.Model):
    """1. Довідник вправ"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_en: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_ua: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class WorkoutPlan(db.Model):
    """2. Заплановане тренування (Сесія)"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    planned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(20)) # Напр. "active", "completed"

    plan_sets: Mapped[List["WorkoutPlanSet"]] = relationship(back_populates="workout_plan", cascade="all, delete-orphan")

class WorkoutPlanSet(db.Model):
    """3. Елементи плану (заплановані вправи та підходи)"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_plan_id: Mapped[int] = mapped_column(ForeignKey('workout_plan.id', ondelete='CASCADE'), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey('exercise.id'), nullable=False)
    weight_id: Mapped[Optional[int]] = mapped_column(ForeignKey('weight.id'), nullable=True) # Зв'язок з вагою
    number_approaches: Mapped[int] = mapped_column(Integer, default=1)  # Кількість підходів
    repeat_exercise: Mapped[int] = mapped_column(Integer, default=0)    # Кількість повторень
    rest_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Час відпочинку в сек.

    workout_plan: Mapped["WorkoutPlan"] = relationship(back_populates="plan_sets")
    exercise: Mapped["Exercise"] = relationship()
    weight: Mapped[Optional["Weight"]] = relationship()

class Workout(db.Model):
    """4. Факт виконання тренування (Сесія)"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey('workout_plan.id', ondelete='SET NULL'), nullable=True)
    actual_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20)) # Напр. "completed", "skipped"

    workout_plan: Mapped[Optional["WorkoutPlan"]] = relationship()
    actual_sets: Mapped[List["WorkoutFact"]] = relationship(back_populates="workout", cascade="all, delete-orphan")

class WorkoutFact(db.Model):
    """5. Фактично виконані підходи (Факти)"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey('workout.id', ondelete='CASCADE'), nullable=False)
    workout_plan_set_id: Mapped[Optional[int]] = mapped_column(ForeignKey('workout_plan_set.id', ondelete='SET NULL'), nullable=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey('exercise.id'), nullable=False)
    weight_id: Mapped[int] = mapped_column(ForeignKey('weight.id'), nullable=False) # Зв'язок з фактичною вагою
    number_approaches: Mapped[int] = mapped_column(Integer, default=1)  # Фактичні підходи
    repeat_exercise: Mapped[int] = mapped_column(Integer, default=0)    # Фактичні повторення

    workout: Mapped["Workout"] = relationship(back_populates="actual_sets")
    exercise: Mapped["Exercise"] = relationship()
    weight: Mapped["Weight"] = relationship()
