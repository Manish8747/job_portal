from flask import Flask
from flask_jwt_extended import JWTManager
from routes.config import Config
from routes.auth import auth_bp
from routes.models import db


app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp, url_prefix='/auth')

db.init_app(app)
with app.app_context():
    db.create_all()

jwt = JWTManager(app)

if __name__ == '__main__':
    app.run(debug=True)
