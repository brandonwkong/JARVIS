import warnings
from flask import Flask, request, jsonify, send_from_directory
from utils.rag_handler import RAGHandler
from dotenv import load_dotenv
import os

# Ignore LangChain deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

app = Flask(__name__, static_folder='.')
load_dotenv()

# Initialize RAG handler
rag_handler = RAGHandler()

@app.route('/')
def serve_html():
    return send_from_directory('.', 'index.html')

@app.route('/toggle-admin', methods=['POST'])
def toggle_admin():
    password = request.json.get('password')
    result = rag_handler.toggle_admin_mode(password)
    return jsonify(result)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    response = rag_handler.get_response(user_message)
    return jsonify({
        'reply': response,
        'mode': 'admin' if rag_handler.admin_mode else 'public'
    })

@app.route('/learned-info', methods=['GET'])
def get_learned_info():
    if not rag_handler.admin_mode:
        return jsonify({"error": "Unauthorized"}), 401
    
    learned_info = rag_handler.db.get_all_verified_info()
    return jsonify({"learned_info": learned_info})

@app.route('/view-learned', methods=['GET'])
def view_learned():
    learned_info = rag_handler.view_learned_info()
    return jsonify({
        'learned_info': [
            {'category': cat, 'content': content} 
            for cat, content in learned_info
        ]
    })

@app.route('/view-conversations', methods=['GET'])
def view_conversations():
    if not rag_handler.admin_mode:
        return jsonify({"error": "Unauthorized"}), 401
    conversations = rag_handler.view_recent_conversations()
    return jsonify({'conversations': conversations})

if __name__ == '__main__':
    app.run(debug=True)