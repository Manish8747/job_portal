<<<<<<< HEAD
from flask import Flask
from flask_jwt_extended import JWTManager
from routes.config import Config
from routes.auth import auth_bp
=======
from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from routes.config import Config
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
>>>>>>> dev
from routes.models import db


app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp, url_prefix='/auth')
<<<<<<< HEAD
=======
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
>>>>>>> dev

db.init_app(app)
with app.app_context():
    db.create_all()

jwt = JWTManager(app)

<<<<<<< HEAD
=======


>>>>>>> dev
if __name__ == '__main__':
    app.run(debug=True)
