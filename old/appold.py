import openai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__, static_folder='.')
CORS(app)

openai.api_key = "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"

# Database functions
def create_db():
    conn = sqlite3.connect('assistant.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS personal_info
                 (name TEXT, favorite_food TEXT, birthday TEXT)''')
    conn.commit()
    conn.close()

def insert_data(name, favorite_food, birthday):
    conn = sqlite3.connect('assistant.db')
    c = conn.cursor()
    c.execute('INSERT INTO personal_info (name, favorite_food, birthday) VALUES (?, ?, ?)',
              (name, favorite_food, birthday))
    conn.commit()
    conn.close()

def fetch_all_data():
    conn = sqlite3.connect('assistant.db')
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()

    context = ""
    for table in tables:
        table_name = table[0]
        context += f"\n--- {table_name.upper()} ---\n"

        c.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in c.fetchall()]

        c.execute(f"SELECT * FROM {table_name}")
        rows = c.fetchall()

        for row in rows:
            row_data = ", ".join(f"{col}: {val}" for col, val in zip(columns, row))
            context += row_data + "\n"

    conn.close()
    return context

# Initialize database and insert data
create_db()
# Only run this once or when you need to update the data
insert_data("Brandon", "Pizza", "04-04-2005")

@app.route('/')
def serve_html():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')

    try:
        # Get personal information from database
        personal_info = fetch_all_data()

        # Create the complete prompt with personal context
        messages = [
            {"role": "system", "content": f"""You are my personal assistant. Here is some information about me:
            {personal_info}
            Please use this information when relevant to answer questions."""},
            {"role": "user", "content": user_message}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error: {e}")  # Log the full error
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)