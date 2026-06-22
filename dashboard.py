import dash
from dash import dcc, html, Input, Output
import pandas as pd
from sqlalchemy import case
from models import db, WorkoutFact, Exercise, Workout, Weight
import plotly.graph_objects as go 
import dash_bootstrap_components as dbc


def get_dashboard_data(server):
    """
    Виконує запит до БД на основі визначених моделей 
    та повертає Pandas DataFrame для Dash Plotly.
    """
    with server.app_context():
        # 1. Множник для тоннажу: якщо вага 0.0 або NULL, вважаємо коефіцієнт рівним 1.0
        actual_weight = case(
            (Weight.weight_value == 0.0, 1.0),
            (Weight.weight_value.is_(None), 1.0),
            else_=Weight.weight_value
        )

        # 2. Побудова запиту за допомогою outerjoin
        stmt = db.select(
            Workout.actual_date,
            Exercise.name_en,
            WorkoutFact.number_approaches,
            WorkoutFact.repeat_exercise,
            Weight.weight_value,
            (WorkoutFact.number_approaches * WorkoutFact.repeat_exercise * actual_weight).label("total_weight")
        ).outerjoin(
            WorkoutFact, Workout.id == WorkoutFact.workout_id
        ).outerjoin(
            Exercise, WorkoutFact.exercise_id == Exercise.id
        ).outerjoin(
            Weight, WorkoutFact.weight_id == Weight.id
        )

        results = db.session.execute(stmt).all()

        data = []
        for row in results:
            data.append({
                "actual_date": row.actual_date,
                "name_en": row.name_en,
                "number_approaches": row.number_approaches,
                "repeat_exercise": row.repeat_exercise,
                "weight_value": row.weight_value,
                "total_weight": row.total_weight
            })

        df = pd.DataFrame(data)

        if not df.empty:
            df["actual_date"] = pd.to_datetime(df["actual_date"])

        return df


def init_dashboard(server):
    """Ініціалізує Dash додаток всередині Flask."""
    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/dash/',
        external_stylesheets=[dbc.themes.DARKLY],
        suppress_callback_exceptions=True
    )

    # ВИПРАВЛЕНО: Зсув відступів тепер строго 4 пробіли
    dash_app.layout = dbc.Container(
        fluid=True, # розтягує контейнер на всю ширину
        className="p-4", # вбудований відступ Bootstrap (padding)
        children=[
            # Шапка (Header)
            dbc.Row(
                dbc.Col(
                    html.Div(
                        className="kb-header-card", # твій кастомний стиль для рамки
                        children=[
                            html.H1("Аналітика тренувань", className="kb-dashboard-title m-0"),
                            html.P("Візуалізація вашого прогресу та загального тоннажу", className="text-muted mt-2")
                        ]
                    ),
                    width=12
                ),
                className="mb-4"
            ),

            # Селектор дат (DatePicker)
            dbc.Row(
                dbc.Col(
                    html.Div([
                        dcc.DatePickerRange(
                            id="date-picker",
                            min_date_allowed=pd.to_datetime("2024-01-01"),
                            max_date_allowed=pd.to_datetime("2030-12-31"),
                            start_date=pd.to_datetime("2025-01-01"),
                            end_date=pd.to_datetime("2026-12-31"),
                            # ДОДАНО: Базове виправлення стилю відображення для темної теми
                            style={
                                "border": "1px solid var(--steel)",
                                "borderRadius": "4px",
                                "background": "var(--iron)"
                            }
                        )
                    ], className="text-center"),
                    width=12
                ),
                className="mb-4"
            ),

            # Графік всередині Bootstrap Картки (Card)
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            # ДОДАНО: Спінер завантаження графіка для кращого UX
                            dbc.Spinner(
                                dcc.Graph(id="pie-chart"),
                                color="warning" # буде під колір твоєї міді/amber
                            )
                        ]),
                        className="kb-card" # застосує твій стиль з forge-bg та steel-border
                    ),
                    width=12,
                    lg=8, # на великих екранах графік займе 8 з 12 колонок
                    className="mx-auto" # центрування
                )
            )
        ]
    )

    @dash_app.callback(
        Output("pie-chart", "figure"),
        Input("date-picker", "start_date"),
        Input("date-picker", "end_date")
    )
    def generate_chart(start_date, end_date):
        df = get_dashboard_data(server)

        empty_layout_kwargs = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font_color": "#b8b4ae", 
            "font_family": "Oswald, sans-serif"
        }

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title_text="У базі даних ще немає записів про тренування", **empty_layout_kwargs)
            return fig

        # ЗАХИСТ: Якщо користувач стер дати в інтерфейсі, ставимо мінімальну/максимальну дату з наявних в БД
        if not start_date:
            start_date = df["actual_date"].min()
        if not end_date:
            end_date = df["actual_date"].max()

        end_date_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        filtered_df = df[
            (df["actual_date"] >= pd.to_datetime(start_date)) & 
            (df["actual_date"] < end_date_dt)
        ]
        
        if filtered_df.empty:
            fig = go.Figure()
            fig.update_layout(title_text="За вказаний період тренувань не знайдено", **empty_layout_kwargs)
            return fig

        df_grouped = filtered_df.groupby("name_en", as_index=False)["total_weight"].sum()
        
        fig = go.Figure(data=[go.Pie(
            labels=df_grouped["name_en"],
            values=df_grouped["total_weight"],
            hole=.3,
            marker=dict(colors=["#e8a020", "#374151", "#2c2c2c", "#b8b4ae", "#9e6c12"])
        )])
        
        fig.update_layout(
            title_text="Розподіл загального тоннажу за вправами (кг)",
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f0ede8",           
            font_family="Oswald, sans-serif", 
            template="plotly_dark"          
        )
        return fig

    return dash_app