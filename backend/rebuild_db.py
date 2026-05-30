import os
import sqlalchemy
from sqlalchemy import text

# Connect using SQLAlchemy with the Remote DB URL
url = os.environ.get('DATABASE_URL')

def rebuild_db():
    print("Connecting to DB to drop and recreate tables...")
    try:
        engine = sqlalchemy.create_engine(url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # 1. Drop old tables
            conn.execute(text("DROP TABLE IF EXISTS matches CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS players CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS tournaments CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS admins CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS tournament_participants CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS match_stats CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS device_tokens CASCADE;"))

            print("Old tables dropped.")

            # 2. Re-create new tables using app context so models are fully respected
            from app import create_app
            from app.extensions import db
            app = create_app('development')
            with app.app_context():
                db.create_all()
                print("New tables created via SQLAlchemy models.")
                
            # 3. Seed admin
            with app.app_context():
                from app.models.admin import Admin
                if not Admin.query.filter_by(username='WinterFA').first():
                    admin = Admin(username='WinterFA')
                    admin.set_password('WinterFA2026!')
                    db.session.add(admin)
                    db.session.commit()
                    print("Admin user 'WinterFA' seeded.")

    except Exception as e:
        print(f"Error rebuilding DB: {e}")

if __name__ == '__main__':
    rebuild_db()
