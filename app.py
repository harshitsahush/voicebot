from utils import *


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "dev"
Session()


@app.route("/", methods = ["GET", "POST"])
def index():
    return redirect("/result")


@app.route("/result", methods = ["GET","POST"])
def fun1():
    if(request.is_json):
        if("uid" not in session):
            session["uid"] = str(uuid.uuid4())

        data = process_query(request.json)
        return jsonify(data)

    else:
        if("uid" not in session):
            session["uid"] = str(uuid.uuid4())

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
    app.run(debug=True, host = "0.0.0.0", ssl_context ="adhoc", port = 1050)
