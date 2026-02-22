import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "app.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("SQLite interactive shell. Type 'exit' or 'quit' to exit.")
print()

while True:
    try:
        query = input("sqlite> ").strip()
        
        if query.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        
        if not query:
            continue
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Check if it's a SELECT (returns rows)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(dict(row))
            else:
                print("(No results)")
        else:
            # INSERT, UPDATE, DELETE
            conn.commit()
            print(f"OK ({cursor.rowcount} rows affected)")
        
        cursor.close()
    
    except sqlite3.Error as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break
    except Exception as e:
        print(f"Error: {e}")

conn.close()
