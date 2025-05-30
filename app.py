# app.py

from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from routes.config import Config
from routes import db, mail  # <- Import from routes.__init__
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.job import job_bp
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions with app
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(job_bp, url_prefix='/job')

from flask_jwt_extended import JWTManager
jwt = JWTManager(app)

with app.app_context():
    db.create_all()
    
@app.route('/')
def home():
    return render_template('index.html')  # This will load templates/index.html


if __name__ == '__main__':
    app.run(debug=True)
