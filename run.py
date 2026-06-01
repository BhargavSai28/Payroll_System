from flask import Flask
from app.config import Config as config
from app import db
from app.models import User, Attendance, Salary, LeaveRequest
from app.routes.api import bp as api_bp
from app.routes.employee import employee
from app.routes.web import web


def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    print("✓ Flask app created successfully")

    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{config.USERNAME}:{config.PASSWORD}@{config.HOST}:{config.PORT}/{config.DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    print(f"✓ Configuring app with PostgreSQL URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app)
    # blueprints are registered after app creation

    with app.app_context():
        try:
            # Ensure models are imported so SQLAlchemy is aware of them
            
            db.create_all()
            print("✓ All 4 tables verified/created in PostgreSQL")
        except Exception as e:
            print(f"✗ ERROR creating tables: {e}")
            import traceback
            traceback.print_exc()
    return app


if __name__ == '__main__':
    app = create_app()
    app.register_blueprint(web)
    app.register_blueprint(employee, url_prefix='/user') 
    app.register_blueprint(api_bp, url_prefix='/api')
    app.run(debug=True, port=8080, use_reloader=False)
