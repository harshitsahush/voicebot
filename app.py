from flask import Flask, request, render_template, redirect, jsonify
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

@app.route("/", methods = ["GET", "POST"])
def index():
    return redirect("/result")

@app.route("/result", methods = ["GET","POST"])
def fun1():
    if(request.is_json):
        data = request.json
        print(data["query_text"])
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = client.chat.completions.create(
            messages = [
                {
                    "role" : "system",
                    "content" : """You are a very helpful personal assistant. Respond each query in a warm tone. Do not assume your own context. If some context is missing, simply tell the user that the question is missing some context."""
                },
                {
                    "role" : "user",
                    "content" : data["query_text"]
                }
            ],
            model = "llama3-70b-8192",
            temperature=0.1,
        )

        data = {"response" : chat_completion.choices[0].message.content}
        print(data)
        return jsonify(data)
        

    else:
        return render_template("voicebot.html")

if(__name__ == "__main__"):
    app.run(debug=True)
