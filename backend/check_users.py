import sqlalchemy
from sqlalchemy import text

url = "postgresql://postgres:tJMeUKxwubMDaSUn@db.ahrvfxrwwkgmumuonixj.supabase.co:5432/postgres"

def check_users():
    engine = sqlalchemy.create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT username, email, is_admin FROM users"))
        users = [dict(row._mapping) for row in result]
        print("Users in DB:", users)

if __name__ == "__main__":
    check_users()
