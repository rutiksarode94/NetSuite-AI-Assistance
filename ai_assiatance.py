from flask import Flask, request, jsonify
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

groq_key = os.getenv("GROQ_API_KEY")

if not groq_key:
    raise ValueError("GROQ_API_KEY not found in .env file! Please check your .env file.")

client = Groq(api_key=groq_key)

chat_history = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        user_message = data.get('message')

        if not session_id or not user_message:
            return jsonify({"error": "Missing sessionId or message"}), 400

        if session_id not in chat_history:
            chat_history[session_id] = [
                {"role": "system", "content": "You are a helpful assistant specialized in NetSuite ERP, accounting, and business operations."}
            ]

        chat_history[session_id].append({"role": "user", "content": user_message})

        # ✅ Correct Current Model
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # ← This is the correct one
            messages=chat_history[session_id],
            temperature=0.7,
            max_tokens=800
        )

        ai_response = response.choices[0].message.content.strip()

        chat_history[session_id].append({"role": "assistant", "content": ai_response})

        return jsonify({
            "success": True,
            "response": ai_response
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)