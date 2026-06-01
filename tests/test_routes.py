from run import create_app
from app import db
import sqlalchemy

print('=== ROUTES TEST ===')
app = create_app()

with app.app_context():
    client = app.test_client()
    # create a user
    resp = client.post('/users', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password_hash': 'hash123'
    })
    print('POST /users ->', resp.status_code, resp.get_json())

    engine = db.engine
    inspector = sqlalchemy.inspect(engine)
    print('Tables:', inspector.get_table_names())

    from app.models import User
    print('Users count:', User.query.count())
