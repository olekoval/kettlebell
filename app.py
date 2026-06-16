from flask import Flask
from flask_migrate import Migrate
from models import db  # Імпортуємо db з  файлу models.py
from seed import register_seed_commands  # Імпортуємо функцію реєстрації CLI

app = Flask(__name__)

# Рядок підключення до бази PostgreSQL:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:#kettlebell@localhost:5433/kettlebell_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ініціалізуємо БД та Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Реєструємо CLI команду для сідингу
register_seed_commands(app)

if __name__ == '__main__':
    app.run(debug=True)
