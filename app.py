from google import genai
from PIL import Image
import requests
import base64
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv
from openai import OpenAI
from database import (
    init_db,
    create_chat,
    save_message,
    get_chats,
    get_messages,
    delete_chat
)
import os

# Load Environment Variables
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise Exception("OPENROUTER_API_KEY not found in .env file")

# OpenRouter Client
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)
print("Gemini Key:", gemini_api_key)
gemini = genai.Client(api_key=gemini_api_key)
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
GEMINI_MODEL = "gemini-3.5-flash-lite"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Initialize Database
init_db()


@app.route("/")
def home():
    return render_template("index.html")


# Create New Chat
@app.route("/new-chat", methods=["POST"])
def new_chat():

    chat_id = create_chat()

    return jsonify({
        "chat_id": chat_id
    })
@app.route("/history", methods=["GET"])
def history():

    chats = get_chats()

    history = []

    for chat in chats:

        history.append({
            "id": chat[0],
            "title": chat[1]
        })

    return jsonify(history)
@app.route("/delete-chat/<int:chat_id>", methods=["DELETE"])
def remove_chat(chat_id):

    delete_chat(chat_id)

    return jsonify({
        "success": True
    })
@app.route("/chat/<int:chat_id>", methods=["GET"])
def load_chat(chat_id):

    messages = get_messages(chat_id)

    print("==========")
    print("Chat ID:", chat_id)
    print("Messages:", messages)
    print("==========")

    data = []

    for role, message in messages:
        data.append({
            "role": role,
            "message": message
        })

    return jsonify(data)
@app.route("/stream-chat", methods=["POST"])
def stream_chat():

    data = request.get_json()

    user_message = data.get("message", "")
    chat_id = data.get("chat_id")

    if chat_id:
        save_message(chat_id, "user", user_message)

    def generate():

        import time

        start = time.time()
        first_token = False
        reply = ""

        messages = [
            {
                "role": "system",
                "content": """
You are Strom AI.



You are an AI assistant developed by Puskar.



If anyone asks:

- Who are you?

- Who created you?

- What is your name?



Always answer:

'I am Strom AI, developed by Puskar.'



Do not say you are Nemotron.

Do not say you were created by NVIDIA.

Do not mention the underlying AI model unless the user specifically asks about it.

"""
            }
        ]

        if chat_id:
            history = get_messages(chat_id)[-10:]

            for role, message in history:
                messages.append({
                    "role": role,
                    "content": message
                })

        try:

            response = client.chat.completions.create(
                model="openrouter/free",
                messages=messages,
                stream=True,
                temperature=0.4,
                max_tokens=512
            )

            for chunk in response:

                if chunk.choices[0].delta.content:

                    if not first_token:
                        print("First Token:",
                              round(time.time() - start, 2),
                              "seconds")
                        first_token = True

                    text = chunk.choices[0].delta.content

                    reply += text

                    yield text

            print("Total Time:",
                  round(time.time() - start, 2),
                  "seconds")

            if chat_id:
                save_message(chat_id, "assistant", reply)

        except Exception as e:

            print(e)

            yield "Something went wrong."

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain"
    )
# Chat Route
@app.route("/chat", methods=["POST"])
def chat():
    print("CHAT ROUTE")

    try:

        data = request.get_json()

        user_message = data.get("message", "")
        chat_id = data.get("chat_id")

        # Save User Message
        if chat_id:
            save_message(chat_id, "user", user_message)

        response = client.chat.completions.create(
   model="openrouter/free",
    messages=[
        {
            "role": "system",
            "content": """
You are Strom AI.

You are an AI assistant developed by Puskar.

If anyone asks:
- Who are you?
- Who created you?
- What is your name?

Always answer:
'I am Strom AI, developed by Puskar.'

Do not say you are Nemotron.
Do not say you were created by NVIDIA.
Do not mention the underlying AI model unless the user specifically asks about the underlying model.
"""
        },
        
        {
        "role": "user",
        "content": user_message
    }
    ],
    stream=True
)
        reply = ""

        for chunk in response:

            if chunk.choices[0].delta.content:

                reply += chunk.choices[0].delta.content

        # Save AI Reply
        if chat_id:
            save_message(chat_id, "assistant", reply)

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print(e)

        return jsonify({
            "reply": str(e)
        }), 500


@app.route("/upload-image", methods=["POST"])
def upload_image():

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": "No image uploaded"
        }), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "message": "No file selected"
        }), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    image = Image.open(filepath)

    try:
        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                "Describe this image in detail.",
                image
            ]   
        )

        print("========== GEMINI RESPONSE ==========")
        print(response)
        print("--------------------------------------")
        print("TEXT:", response.text)
        print("======================================")

        return jsonify({
            "success": True,
            "reply": response.text
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
if __name__ == "__main__":
    app.run(debug=True)
