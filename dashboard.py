import dash
from dash import dcc, html
import pandas as pd
from sqlalchemy import case
# Переконайся, що імпорт моделей відповідає твоїй структурі проекту
from models import db, WorkoutFact, Exercise, Workout, Weight


def get_dashboard_data(server):
    """
    Виконує запит до БД на основі визначених моделей 
    та повертає Pandas DataFrame для Dash Plotly.
    """
    # Огортаємо в контекст додатка, щоб db.engine був доступний
    with server.app_context():
        
        # 1. Формуємо умову для ваги окремо, щоб SQL-запит згенерувався без помилок пріоритетів
        actual_weight = case(
            (Weight.weight_value == 0, 1.0), 
            (Weight.weight_value.is_(None), 1.0), 
            else_=Weight.weight_value
        )

        # 2. Побудова запиту (SQLAlchemy 2.0)
        stmt = db.select(
            Workout.actual_date,
            Exercise.name_en,
            WorkoutFact.number_approaches,
            WorkoutFact.repeat_exercise,
            Weight.weight_value,
            # Перемножуємо поля
            (WorkoutFact.number_approaches * WorkoutFact.repeat_exercise * actual_weight).label("total_weight")
        ).join(
            Exercise, WorkoutFact.exercise_id == Exercise.id
        ).join(
            Workout, WorkoutFact.workout_id == Workout.id
        ).outerjoin(  # outerjoin рятує, якщо weight_id є NULL
            Weight, WorkoutFact.weight_id == Weight.id
        )

        # 3. Завантаження результатів у Pandas DataFrame
        df = pd.read_sql_query(sql=stmt, con=db.engine)
    
    return df

    
def init_dashboard(server):
    """Ініціалізація Plotly Dash всередині Flask додатка."""
    
    dash_app = dash.Dash(
        __name__,
        server=server,            # Передаємо Flask сервер
        url_base_pathname='/dash/' # URL дашборду
    )


    df = get_dashboard_data(server)

    dash_app.layout = html.Div([
        html.H1("Аналітика тренувань (Kettlebell Progress)", style={'textAlign': 'center'}),
        html.P("Тут будуть майбутні графіки", style={'textAlign': 'center'}),
    ])
  
    return dash_app.server