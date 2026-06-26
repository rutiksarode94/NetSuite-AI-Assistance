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
SYSTEM_PROMPT = """You are an expert NetSuite assistant.

When user asks to create a customer (or any record), you MUST return JSON in this exact format:

{
  "response": "Short confirmation message",
  "action": {
    "type": "create_customer",
    "data": {
      "companyname": "Test001-RS",
      "email": "test001@gmail.com"
    }
  }
}

Do NOT give step-by-step instructions. Keep "response" very short (1-2 lines)."""
