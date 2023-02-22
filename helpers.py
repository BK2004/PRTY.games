import random
import string
from pymongo import MongoClient
import time
import os

GAMEMODES = [
    "Fill in the blank",
    "Trivia",
    "Song Guesser",
    "Wordy"
]

client = MongoClient(os.getenv("MONGODB_URI"))

db = client.prty_db
roomsDB = db.rooms

# Clear database when starting up
roomsDB.delete_many({})

class Room:
    def __init__(self, lobbyName, roomType):
        self.roomCode = genCode()
        while roomsDB.count_documents({"code": self.roomCode}, limit=1) != 0:
            self.roomCode = genCode()
        
        self.lobbyName = lobbyName
        self.status = 0
        self.lastStatusUpdate = time.time()
        self.players = []
        self.playerCount = 0

        roomsDB.insert_one({"code": self.roomCode, "type": roomType, "name": lobbyName})

    def getStatus(self):
        return self.status

    # Updates to given status code
    def updateStatus(self, statusCode):
        self.status = statusCode
        self.lastStatusUpdate = time.time()

    # Generate mode voting
    def initVotes(self):
        # Check for already initialized
        if hasattr(self, 'roomVotes'):
            return

        self.roomVotes = {"Random": []}

        # Generate and fill with random modes
        availableModes = [mode for mode in GAMEMODES]
        for i in range(3):
            rand = random.randint(0, len(availableModes) - 1)

            self.roomVotes[availableModes[rand]] = []
            availableModes.remove(availableModes[rand])

    # Gets list of gamemodes
    def getModes(self):
        if self.roomVotes is not None:
            return [mode for mode in self.roomVotes]

    # Empty votes and remove room from dictionary
    def clearVotes(self):
        if self.roomVotes is not None:
            delattr(self, 'roomVotes')

    # Add vote from player
    def addVote(self, gamemode, playerId):
        if self.roomVotes is not None and gamemode in self.roomVotes and playerId not in self.roomVotes[gamemode]:
            self.roomVotes[gamemode].append(playerId)

    # Remove player vote
    def removeVote(self, playerId):
        if self.roomVotes is None:
            return

        for mode in self.roomVotes:
            if playerId in self.roomVotes[mode]:
                self.roomVotes[mode].remove(playerId)

    # Is player in the room
    def playerInRoom(self, playerId):
        return playerId in self.players

    # Add player to room
    def addPlayer(self, playerId):
        if self.playerInRoom(playerId):
            return False
        
        self.playerCount += 1
        self.players.append(playerId)

        return True

    # Remove player from room
    def removePlayer(self, playerId):
        if not self.playerInRoom(playerId):
            return False

        self.playerCount -= 1
        self.players.remove(playerId)


        if self.playerCount == 0:
            self.destroy()
        elif self.playerCount == 1 and self.getStatus() < 3:
            self.updateStatus(0)
            self.clearVotes()

    def setDestroyCallback(self, destroyCallback):
        self.destroyCallback = destroyCallback

    def destroy(self):
        roomsDB.delete_one({'code': self.roomCode})
        self.destroyCallback()

def genCode():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(6))