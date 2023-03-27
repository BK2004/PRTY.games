from helpers import *
from flask import Flask, render_template, redirect, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import time

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
        session['room-code'] = None
        return render_template("index.html", username=session['player-name'])

@app.route("/room/<code>", methods=["POST", "GET"])
def join(code=None):
    checkName()

    if code is None or code.strip() == "":
        return redirect("/")

    # Check if lobby exists
    queryRes = code in rooms
    if not queryRes:
        return redirect("/")
    
    session['room-code'] = code
    
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

    # If in status 0 and enough players, move to status 1 (Allow players to ready up before voting)
    if rooms[data['code']].getStatus() == 1:
        emit('update', {'status': 1}, to=data['code'])
    else:
        # Send game data to player
        if rooms[data['code']].getStatus() == 3:
            emit('update', {'status': 3, 'game': rooms[data['code']].getGame()}, to=request.sid)
        else:
            emit('update', {'status': rooms[data['code']].getStatus()}, to=request.sid)

@socketio.on("ready")
def ready_up(data):
    if session.get("room-code") is None or session['room-code'] not in rooms or rooms[session['room-code']].getStatus() != 1:
        return
    
    res = rooms[session['room-code']].readyPlayer(request.sid)
    if res:
        # Check if should be changed to voting phase
        if rooms[session['room-code']].getStatus() == 2:
            emit('update', {'status': 2}, to=session['room-code'])

            newData = {'votes': rooms[session['room-code']].getVotes()}
            emit('update votes', newData, to=session['room-code'])
            

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

    # Has game been started
    if rooms[session['room-code']].isStarted():
        emit('update', {'status': 3, 'game': rooms[session['room-code']].getGame(), 'gameStatus': rooms[session['room-code']].getGameStatus()}, to=session['room-code'])

    emit('update votes', {'votes': rooms[session['room-code']].getVotes()}, to=session['room-code'])

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
    if len(data) == 0 or data.get('content') is None or len(data['content'].strip()) <= 5 or len(data['content'].strip()) > 40:
        return
    
    # Check if in room
    if session.get('room-code') is None or not session['room-code'] in rooms:
        return
    
    rooms[session['room-code']].updatePlayerInGame(request.sid, data['content'], "question")

@socketio.on("submit response")
def submit_response(data={}):
    if len(data) == 0 or data.get('content') is None or len(data['content'].strip()) == 0 or len(data['content'].strip()) > 40:
        return

    # Check if in room
    if session.get('room-code') is None or not session['room-code'] in rooms:
        return

    rooms[session['room-code']].updatePlayerInGame(request.sid, data['content'], "response")

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
        return

    if rooms[session['room-code']].playerCount == 1 and rooms[session['room-code']].getStatus() == 0:
        emit('update', {'status': 0}, to=session['room-code'])

if __name__ == "__main__":
    socketio.run(app, debug=True)