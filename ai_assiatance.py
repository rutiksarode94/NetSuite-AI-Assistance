from flask import Flask, request, jsonify
import os
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)

groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise ValueError("GROQ_API_KEY not found in .env file!")

client = Groq(api_key=groq_key)

chat_history = {}

# Strong System Prompt
SYSTEM_PROMPT = """You are an expert NetSuite assistant.

**CRITICAL RULE:**
If the user asks to CREATE, UPDATE, or perform any action on a record (customer, sales order, etc.), you MUST reply with a valid JSON object ONLY. No extra text outside the JSON.

**Response Format:**

{
  "response": "Short confirmation message to the user",
  "action": {
    "type": "create_customer",
    "data": {
      "companyname": "Test001-RS",
      "email": "test001@gmail.com"
    }
  }
}

If no action is needed, still return JSON:
{
  "response": "Your normal helpful answer",
  "action": null
}

Supported action: create_customer only for now.
Be concise. Do not give steps or code examples when action is possible."""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        user_message = data.get('message')

        if not session_id or not user_message:
            return jsonify({"success": False, "error": "Missing sessionId or message"}), 400

        if session_id not in chat_history:
            chat_history[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        chat_history[session_id].append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history[session_id],
            temperature=0.2,                    # Lower = more consistent
            max_tokens=800,
            response_format={"type": "json_object"}   # ← This forces JSON
        )

        ai_content = response.choices[0].message.content.strip()
        print("Raw Groq Response:", ai_content)   # ← For debugging

        try:
            ai_result = json.loads(ai_content)
        except json.JSONDecodeError as e:
            print("JSON Parse Error:", str(e))
            ai_result = {
                "response": ai_content,
                "action": None
            }

        # Save only the response part to history
        chat_history[session_id].append({
            "role": "assistant", 
            "content": ai_result.get("response", ai_content)
        })

        return jsonify({
            "success": True,
            "response": ai_result.get("response"),
            "action": ai_result.get("action")
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
