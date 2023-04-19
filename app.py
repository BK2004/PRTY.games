from helpers import *
from flask import Flask, render_template, redirect, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import time
from words import isWord

PAGE_SIZE = 5

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

rooms = {}

@app.errorhandler(404)
def routeError(code):
    return redirect("/")

@app.route("/ingame")
def in_game():
    return render_template('ingame.html', game=True)

@app.route("/", methods=["POST", "GET"])
def index():
    checkName()
    if request.method == "POST":
        roomType = request.form['type']
        name = 'PRTY room'
        if roomType == 'public' and request.form['lobby-name'] is not None and request.form['lobby-name'].strip() != "":
            name = request.form['lobby-name'].strip()

        newRoom = Room(name, roomType)
        rooms[newRoom.roomCode] = newRoom
        rooms[newRoom.roomCode].setDestroyCallback(lambda : rooms.pop(newRoom.roomCode))
        
        return redirect("/room/" + newRoom.roomCode)
    else:        
        return render_template("index.html", username=session['player-name'], lobbies=getLobbyPage(1))

@app.route("/getPublics/<int:pageNumber>")
def getLobbyPage(pageNumber=1):
    out = []
    res = roomsDB.find({"type": "public"}).skip((pageNumber - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    for doc in res:
        out.append({"code": doc['code'], "name": doc['name'], "playerCount": rooms[doc['code']].playerCount})

    return out

@app.route("/room/<code>", methods=["POST", "GET"])
def join(code=None):
    checkName()

    if code is None or code.strip() == "":
        return redirect("/")

    # Check if lobby exists
    queryRes = code in rooms
    if not queryRes:
        return redirect("/")
    
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
    if data['code'] not in rooms:
        return
        
    join_room(request.sid)
    join_room(data['code'])
    session['room-code'] = data['code']
    emit('message recieve', {'username': 'SERVER', 'content': session['player-name'] + " has joined the room."}, to=data['code'])
    rooms[data['code']].addPlayer(request.sid)

@socketio.on("ready")
def ready_up(data):
    if session.get("room-code") is None or session['room-code'] not in rooms or rooms[session['room-code']].getStatus() != 1:
        return
    
    rooms[session['room-code']].readyPlayer(request.sid)   

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

@socketio.on("vote")
def socket_vote(data):
    # Does room exist
    if session.get('room-code') is None or not session['room-code'] in rooms:
        return

    if 'gamemode' not in data:
        return

    rooms[session['room-code']].addVote(data['gamemode'], request.sid)
    
@socketio.on("game vote")
def socket_game_vote(data):
    # Does room exist
    if session.get('room-code') is None or not session['room-code'] in rooms:
        return

    if 'item' not in data:
        return
    
    rooms[session['room-code']].addGameVote(data['item'], request.sid)

@socketio.on("submit question")
def submit_question(data={}):
    # Entering questions
    if data.get('content') is None:
        return
    
    # Check if in room
    if session.get('room-code') is None or not session['room-code'] in rooms:
        return
    
    rooms[session['room-code']].updatePlayerInGame(request.sid, data['content'].strip(), "question")

@socketio.on("submit response")
def submit_response(data={}):
    if data.get('content') is None:
        return

    # Check if in room
    if session.get('room-code') is None or not session['room-code'] in rooms:
        return

    rooms[session['room-code']].updatePlayerInGame(request.sid, data['content'].strip(), "response")

@socketio.on("submit live response")
def submit_live_response(data={}):
    if data.get('content') is None:
        return 

    # Check if in room
    if session.get("room-code") is None or not session['room-code'] in rooms:
        return
    
    rooms[session['room-code']].nextLiveResponse(request.sid, data.get("content").strip())

@socketio.on("update live response")
def update_live_response(data={}):
    if len(data) == 0 or data.get('content') is None or len(data['content'].strip()) > 20:
        return

    # Check if in room
    if session.get("room-code") is None or not session['room-code'] in rooms:
        return

    rooms[session['room-code']].updateLiveResponse(data.get("content"))

@socketio.on("disconnect")
def socket_disconnect():
    # Does room exist
    if session.get('room-code') is None or not session['room-code'] in rooms:
        return
    
    leave_room(session['room-code'])
    leave_room(request.sid)
    emit('message recieve', {'username': 'SERVER', 'content': session['player-name'] + " has left the room."}, to=session['room-code'])

    # Remove from room count and check if room is vacated
    rooms[session['room-code']].removePlayer(request.sid)
    if rooms.get(session['room-code']) is None:
        session['room-code'] = None
        return
    
    session['room-code'] = None

if __name__ == "__main__":
    socketio.run(app, debug=True)