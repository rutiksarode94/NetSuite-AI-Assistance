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

# System Prompt with Action Instructions
SYSTEM_PROMPT = """You are an expert NetSuite assistant. You help users perform operations in NetSuite.

**Important Rules:**
- If the user asks you to **create, update, or retrieve** any record (Customer, Vendor, Sales Order, Invoice, etc.), you MUST respond with a valid JSON object.
- If no action is needed (just explanation or general question), respond with normal text.

**Response Format:**

If action is needed:
```json
{
  "response": "Friendly message to the user",
  "action": {
    "type": "create_customer",
    "data": {
      "companyname": "Test001-RS",
      "email": "test001@gmail.com",
      "phone": "1234567890"
    }
  }
}
