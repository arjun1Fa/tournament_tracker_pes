import sqlalchemy
from sqlalchemy import text
import sys

# The URL from user, trying without brackets first (as they are usually placeholders)
url = "postgresql://postgres:tJMeUKxwubMDaSUn@db.ahrvfxrwwkgmumuonixj.supabase.co:5432/postgres"
url_with_brackets = "postgresql://postgres:[tJMeUKxwubMDaSUn]@db.ahrvfxrwwkgmumuonixj.supabase.co:5432/postgres"

def run_script(db_url):
    try:
        engine = sqlalchemy.create_engine(db_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            with open("schema.sql", "r") as f:
                sql_script = f.read()
                
            # Split the script into individual statements
            statements = sql_script.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement))
        return True
    except Exception as e:
        print(f"Error connecting/executing: {e}")
        return False

if __name__ == "__main__":
    print("Trying connection without brackets...")
    if run_script(url):
        print("Successfully created all tables in Supabase!")
    else:
        print("\nTrying connection with brackets...")
        if run_script(url_with_brackets):
            print("Successfully created all tables in Supabase!")
        else:
            print("\nFailed to connect. Please check the password.")
            sys.exit(1)
