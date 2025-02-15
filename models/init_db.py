import os
import sqlite3

def init_database():
    # Database file path
    db_path = os.path.join(os.path.dirname(__file__), 'caringmind.db')
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    # Check if database already exists
    db_exists = os.path.exists(db_path)
    if db_exists:
        print(f"Database already exists at {db_path}")
        return
    
    # Create a new database connection
    print(f"Creating new database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Read schema file
        with open(schema_path, 'r') as schema_file:
            schema_sql = schema_file.read()
        
        # Execute schema SQL
        # Split on semicolon to execute multiple statements
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        # Commit the changes
        conn.commit()
        print("Database schema created successfully")
        
    except Exception as e:
        print(f"Error creating database: {e}")
        # If there's an error, try to remove the partially created database
        conn.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()