import sqlalchemy
from sqlalchemy import text

url = "postgresql://postgres:tJMeUKxwubMDaSUn@db.ahrvfxrwwkgmumuonixj.supabase.co:5432/postgres"

def check_tables():
    engine = sqlalchemy.create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print("Tables in public schema:")
        for t in tables:
            print(f"- {t}")

if __name__ == "__main__":
    check_tables()
