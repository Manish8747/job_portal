from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from routes.config import Config
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.models import db
from routes.job import job_bp
from flask_migrate import Migrate


app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(job_bp, url_prefix='/job')

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

jwt = JWTManager(app)


if __name__ == '__main__':
    app.run(debug=True)
