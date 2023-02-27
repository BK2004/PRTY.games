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
        if hasattr(self, 'roomVotes'):
            delattr(self, 'roomVotes')

    # Add vote from player
    def addVote(self, gamemode, playerId):
        self.removeVote(playerId)
        if hasattr(self, 'roomVotes') and gamemode in self.roomVotes and playerId not in self.roomVotes[gamemode]:
            self.roomVotes[gamemode].append(playerId)
            if sum(len(self.roomVotes[key]) for key in self.roomVotes) == self.playerCount:
                # All players have voted, move on
                self.startGame()

    def startGame(self):
        if not hasattr(self, 'roomVotes'):
            return
        
        game = 'Random'
        for key in self.roomVotes.keys():
            if len(self.roomVotes[key]) > len(self.roomVotes[game]):
                game = key

        if game == 'Random':
            options = self.roomVotes.copy()
            options.pop('Random')
            game = list(options)[random.randint(0, 2)]
        
        self.selectedGame = game

        self.clearVotes()
        self.updateStatus(3)

    def isStarted(self):
        return hasattr(self, 'selectedGame')

    def getGame(self):
        if not hasattr(self, 'selectedGame'):
            return None

        return self.selectedGame

    # Remove player vote
    def removeVote(self, playerId):
        if not hasattr(self, 'roomVotes') is None:
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

        if self.playerCount >= 2 and self.getStatus() == 0:
            self.initReady()
            self.updateStatus(1)

        return True

    # Remove player from room
    def removePlayer(self, playerId):
        if not self.playerInRoom(playerId):
            return False

        self.playerCount -= 1
        self.players.remove(playerId)
        self.removeVote(playerId)
        self.unreadyPlayer(playerId)

        if self.playerCount == 0:
            self.destroy()
        elif self.playerCount == 1:
            self.updateStatus(0)
            self.clearVotes()
            self.clearReady()

    def setDestroyCallback(self, destroyCallback):
        self.destroyCallback = destroyCallback

    def destroy(self):
        roomsDB.delete_one({'code': self.roomCode})
        self.destroyCallback()
    
    def getVotes(self):
        if not hasattr(self, 'roomVotes'):
            return None
        
        return {mode: len(self.roomVotes[mode]) for mode in self.roomVotes}

    # Allow players to ready up
    def initReady(self):
        if hasattr(self, 'playersReady'):
            return False
        
        self.playersReady = []
    
    # Add player to ready list
    def readyPlayer(self, playerId):
        if playerId is None or playerId not in self.players or not hasattr(self, 'playersReady') or playerId in self.playersReady:
            return False
        
        self.playersReady.append(playerId)
        if len(self.playersReady) < self.playerCount:
            self.updateStatus(2)
            self.initVotes()

        return True
    
    # Remove player from ready list
    def unreadyPlayer(self, playerId):
        if playerId is None or playerId not in self.players or not hasattr(self, 'playersReady') or playerId not in self.playersReady:
            return False

        self.playersReady.remove(playerId)
        return True

    # Return count of players ready
    def getReady(self):
        if not hasattr(self, 'playersReady'):
            return -1

        return len(self.playersReady)

    def clearReady(self):
        if hasattr(self, 'playersReady'):
            delattr(self, 'playersReady')

def genCode():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(6))