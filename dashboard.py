import dash
from dash import dcc, html, Input, Output
import pandas as pd
from sqlalchemy import case
# Переконайся, що імпорт моделей відповідає твоїй структурі проекту
from models import db, WorkoutFact, Exercise, Workout, Weight
import plotly.graph_objects as go 


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

    # Конвертуємо колонку з датами у формат datetime для надійної фільтрації в Pandas
    if not df.empty and "actual_date" in df.columns:
        df["actual_date"] = pd.to_datetime(df["actual_date"])
        min_date = df["actual_date"].min()
        max_date = df["actual_date"].max()
    else:
        # Дефолтні значення, якщо база даних раптом порожня
        min_date = pd.Timestamp.now() - pd.Timedelta(days=30)
        max_date = pd.Timestamp.now()

    dash_app.layout = html.Div([
        html.H1("Аналітика тренувань (Kettlebell Progress)", style={'textAlign': 'center'}),
        html.P("Тут будуть майбутні графіки", style={'textAlign': 'center'}),
        # Контейнер для вибору дат
        html.Div([
            html.Label("Виберіть період тренувань:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.DatePickerRange(
                id="date-picker",
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=min_date, # значення за замовчуванням (початок періоду)
                end_date=max_date,   # значення за замовчуванням (кінець періоду)
                display_format="YYYY-MM-DD",
                style={'marginBottom': '20px'}
            )
        ], style={'textAlign': 'center', 'margin': '20px'}),
        dcc.Graph(id="pie-chart"),
    ])

    @dash_app.callback(
        Output("pie-chart", "figure"),
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date")
    )
    def generate_chart(start_date, end_date):
        # Якщо дані порожні, повертаємо порожній графік
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title_text="Немає даних для відображення")
            return fig

        # Фільтруємо наш DataFrame відповідно до обраного таймлайну
        filtered_df = df[
            (df["actual_date"] >= pd.to_datetime(start_date)) & 
            (df["actual_date"] <= pd.to_datetime(end_date))
        ]
        
        # Якщо після фільтрації за датами нічого не знайшлося
        if filtered_df.empty:
            fig = go.Figure()
            fig.update_layout(title_text="За вказаний період тренувань не знайдено")
            return fig

        # Групуємо відфільтровані дані
        df_grouped = filtered_df.groupby("name_en", as_index=False)["total_weight"].sum()
        
        # Будуємо кругову діаграму
        fig = go.Figure(data=[go.Pie(labels=df_grouped["name_en"], values=df_grouped["total_weight"])])
        fig.update_layout(title_text="Розподіл сумарної ваги за вправами за обраний період")
        
        return fig                
  
    return dash_app.server