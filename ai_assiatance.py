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

#     You can create, search, update any record in NetSuite.

#     **STRICT RULES:**
#     - Always respond with **valid JSON only**. No extra text.
#     - Use the **exact internal record type** (very important).

#     **Correct Record Types to Use:**
#     - Customer → "customer"
#     - Vendor → "vendor"
#     - Non-Inventory Item → "noninventoryitem"
#     - Inventory Item → "inventoryitem"
#     - Service Item → "serviceitem"
#     - Kit/Package → "kititem"
#     - Sales Order → "salesorder"
#     - Purchase Order → "purchaseorder"
#     - Invoice → "invoice"
#     - Credit Memo → "creditmemo"
#     - Custom Record → use exact ID like "customrecord_your_record_id"

#     **Response Format:**

#     For Create:
#     {
#     "response": "Creating customer...",
#     "action": [
#         {
#         "type": "create_record",
#         "data": {
#             "recordtype": "customer",
#             "fields": {
#             "companyname": "ABC Corp",
#             "email": "contact@abccorp.com",
#             "subsidiary": 1
#             }
#         }
#         }
#     ]
#     }

#     For Search:
#     {
#     "response": "Searching customers...",
#     "action": [{
#         "type": "search_record",
#         "data": {
#         "recordtype": "customer",
#         "filters": [["companyname", "contains", "ABC"]],
#         "searchname": "AI Customer Search"
#         }
#     }]
#     }

#     **Important:**
#     - For items, always specify "noninventoryitem", "inventoryitem", or "serviceitem" — never just "item".
#     - Always use correct field internal IDs (companyname, email, itemid, etc.).
#     """

SYSTEM_PROMPT = """You are an expert NetSuite assistant.

    You can create, search, or update ANY record in NetSuite.

    **STRICT RULES:**
    - Always respond with **valid JSON only**. No extra text.
    - Use the **exact internal record type**.
    - Use correct field internal IDs.

    **Correct Record Types:**
    - Customer → "customer"
    - Vendor → "vendor"
    - Non-Inventory Item → "noninventoryitem"
    - Inventory Item → "inventoryitem"
    - Service Item → "serviceitem"
    - Kit Item → "kititem"
    - Sales Order → "salesorder"
    - Purchase Order → "purchaseorder"
    - Invoice → "invoice"
    - Credit Memo → "creditmemo"
    - Custom Record → use exact ID like "customrecord_your_id"

    **Search Filter Rules:**
    - For **Entity Records** (customer, vendor, etc.): Use companyname, email, subsidiary, isinactive, datecreated, lastmodifieddate
    - For **Item Records**: Use itemid, displayname, isinactive, quantityonhand, baseprice
    - For **Transaction Records**: Use tranid, trandate, entity, mainline, status, amount

    **Date Examples:**
    - Today: ["datecreated", "on", "today"]
    - Range: ["datecreated", "within", "30/06/2026..01/07/2026"]
    - Last 30 days: ["datecreated", "within", "last30days"]

    **Response Format:**

    For Create:
    {
    "response": "Creating customer...",
    "action": [{
        "type": "create_record",
        "data": {
        "recordtype": "customer",
        "fields": {
            "companyname": "ABC Corp",
            "email": "contact@abccorp.com"
        }
        }
    }]
    }

    For Search (with optional SuiteQL):
    {
    "response": "Searching inventory items out of stock...",
    "action": [{
        "type": "search_record",
        "data": {
        "recordtype": "inventoryitem",
        "filters": [["quantityonhand", "is", "0"]],
        "searchname": "Out of Stock Items",
        "query": "SELECT id, itemid, displayname FROM item WHERE quantityonhand = 0 AND isinactive = 'F'"   // Optional for fallback
        }
    }]
    }

    **Important:**
    - Never use "item" — always specify "noninventoryitem", "inventoryitem", or "serviceitem".
    - If Saved Search may fail, provide "query" for SuiteQL fallback.
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
