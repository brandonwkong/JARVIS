import sqlite3
import openai

openai.api_key = "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"

def create_db():
    conn = sqlite3.connect('assistant.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS personal_info
                 (name TEXT, favorite_food TEXT, birthday TEXT)''')
    conn.commit()
    conn.close()

create_db()

def insert_data(name, favorite_food, birthday):
    conn = sqlite3.connect('assistant.db')
    c = conn.cursor()
    c.execute('INSERT INTO personal_info (name, favorite_food, birthday) VALUES (?, ?, ?)',
              (name, favorite_food, birthday))
    conn.commit()
    conn.close()

# Insert your details (adjust these as needed)
insert_data("Brandon", "Pizza", "04-04-2005")

def fetch_all_data():
    conn = sqlite3.connect('assistant.db')
    c = conn.cursor()

    # Get all table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()

    context = ""
    for table in tables:
        table_name = table[0]
        context += f"\n--- {table_name.upper()} ---\n"

        # Get column names
        c.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in c.fetchall()]

        # Fetch all data from the table
        c.execute(f"SELECT * FROM {table_name}")
        rows = c.fetchall()

        for row in rows:
            row_data = ", ".join(f"{col}: {val}" for col, val in zip(columns, row))
            context += row_data + "\n"

    conn.close()
    return context

def generate_response(user_query):
    # Build dynamic context from all tables
    personal_info = fetch_all_data()

    prompt = f"""
    You are my personal assistant. Here is some information about me:
    {personal_info}

    Now, answer this question using the information above:
    {user_query}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # GPT-3.5 or GPT-4
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )

    return response['choices'][0]['message']['content'].strip()

# Example usage:
response = generate_response("What is my favorite food?")
print(response)
