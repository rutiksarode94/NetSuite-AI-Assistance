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

# ✅ Much Stronger System Prompt
# SYSTEM_PROMPT = """You are an expert NetSuite assistant.

# **STRICT RULE - YOU MUST FOLLOW THIS:**
# - If the user wants to **create a customer**, reply **ONLY** with a valid JSON object. No explanations, no extra text, no markdown.
# - Never give step-by-step instructions when the user asks to create something.

# **Exact JSON Format to return:**

# {
#   "response": "Customer creation requested.",
#   "action": {
#     "type": "create_customer",
#     "data": {
#       "companyname": "Exact name from user",
#       "email": "Exact email from user"
#     }
#   }
# }

# If no action is needed, use:
# {
#   "response": "Your normal answer here.",
#   "action": null
# }

# Always output valid JSON only. Do not add any text before or after the JSON."""

SYSTEM_PROMPT = """You are an expert NetSuite assistant.

You can create, search, or update ANY record in NetSuite.

**Always respond with valid JSON only.**

**For Create:**
{
  "response": "Creating records...",
  "action": [
    {
      "type": "create_record",
      "data": {
        "recordtype": "customer",           // or vendor, item, salesorder, customrecord_xxx
        "fields": {
          "companyname": "Test Company",
          "email": "test@email.com",
          "subsidiary": 2
        }
      }
    }
  ]
}

**For Search:**
{
  "response": "Searching customers...",
  "action": [{
    "type": "search_record",
    "data": {
      "recordtype": "customer",
      "filters": [["companyname", "contains", "Test"]],
      "columns": ["companyname", "email", "internalid"]
    }
  }]
}
"""

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
            temperature=0.1,          # Even lower for consistency
            max_tokens=600,
            response_format={"type": "json_object"}
        )

        ai_content = response.choices[0].message.content.strip()
        print("=== RAW GROQ RESPONSE ===")
        print(ai_content)
        print("=========================")

        try:
            ai_result = json.loads(ai_content)
        except json.JSONDecodeError:
            print("JSON Parse Failed - Fallback")
            ai_result = {
                "response": ai_content,
                "action": None
            }

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
