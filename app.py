from flask import Flask, request, render_template, redirect, jsonify
from utils import *

app = Flask(__name__)

@app.route("/", methods = ["GET", "POST"])
def index():
    return redirect("/result")

@app.route("/result", methods = ["GET","POST"])
def fun1():
    if(request.is_json):
        data = process_query(request.json)
        return jsonify(data)

    else:
        return render_template("voicebot.html")

@app.route("/process_file", methods = ["GET","POST"])
def fun2():
    if('file' not in request.files):
        return jsonify({
            "msg" : "No file"
        })

    file = request.files['file']

    if(file):
        process_file(file)
        return jsonify({
            "msg" : "File saved successfully"
        })

    else:
        return jsonify({
                "msg" : "No file"
            })


if(__name__ == "__main__"):
    app.run(debug=True)
