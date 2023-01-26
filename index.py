from helpers import genCode
from flask import Flask, render_template, redirect, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = 'BAD_KEY'
socketio = SocketIO(app)

client = MongoClient(os.getenv("MONGODB_URI"))

db = client.prty_db
rooms = db.rooms

# Clear database when starting up
rooms.delete_many({})

roomCounts = {}

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
    if code in roomCounts:
        roomCounts[code] += 1
    else:
        roomCounts[code] = 1
    
    return render_template("room.html", game=True, code=code, username=session['player-name'])

# Changing player names
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

# Test socket.io
'''@socketio.on("test event")
def test_event(data):
    print(data)

    emit('server message', {'response': 'HI THERE'})'''

@socketio.on("join")
def room_join(data):
    join_room(data['code'])
    session['room-code'] = data['code']
    emit('message recieve', {'username': 'SERVER', 'content': session['player-name'] + " has joined the room."}, to=data['code'])

@socketio.on("message send")
def message_send(data):
    res = {
        'username': session['player-name'],
        'content': data['content']
    }

    # Check that message is valid
    if res['content'].strip() == '':
        return

    emit('message recieve', res, to=session['room-code'])

@socketio.on("disconnect")
def socket_disconnect():
    leave_room(session['room-code'])
    emit('message recieve', {'username': 'SERVER', 'content': session['player-name'] + " has left the room."}, to=session['room-code'])

    # Remove from room count and check if room is vacated
    roomCounts[session['room-code']] -= 1
    if roomCounts[session['room-code']] == 0:
        # Delete room
        rooms.delete_one({'code': session['room-code']})

if __name__ == "__main__":
    socketio.run(app)