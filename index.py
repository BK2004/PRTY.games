from helpers import genCode
from flask import Flask, render_template, redirect, request, session
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = 'BAD_KEY'

client = MongoClient(os.getenv("DATABASE_URI"))

db = client.prty_db
rooms = db.rooms

@app.errorhandler(404)
def routeError(code):
    return redirect("/")

@app.route("/", methods=["POST", "GET"])
def index():
    checkName()
    if request.method == "POST":
        roomType = request.form['type']
        name = 'PRTY room'
        if roomType == 'public' and request.form['lobby-name'] is not None and request.form['lobby-name'].strip() != "":
            name = request.form['lobby-name'].strip()
        
        # Generate unique code
        code = genCode()
        while rooms.count_documents({"code": code}, limit=1) != 0:
            code = genCode()
        rooms.insert_one({"code": code, "type": roomType, "name": name})

        return redirect("/room/" + code)
    else:        
        return render_template("index.html", username=session['player-name'])

@app.route("/room/<code>", methods=["POST", "GET"])
def join(code=None):
    checkName()

    if code is None or code.strip() == "":
        return redirect("/")

    # Check if lobby exists
    queryRes = rooms.find_one({"code": code})
    if queryRes is None:
        return redirect("/")

    # Lobby exists, so join
    return render_template("room.html", game=True, code=code, username=session['player-name'])

@app.route("/updateName", methods=['POST'])
def updateName():
    name = request.form['player-name']
    if name is None or name.strip() == "" or len(name) > 20:
        return "FAILED"

    session['player-name'] = name
    return "SUCCESS"

def checkName():
    if session.get('player-name') is None:
        session['player-name'] = "Guest"

if __name__ == "__main__":
    app.run(debug=True)