import random
import string
from pymongo import MongoClient
import time
import os
from flask import request, session
from flask_socketio import emit
from threading import Timer
from words import isWord

STEPS = {
    'Fill in the blank': [
        "question",
        "response",
        "voting",
        "results"
    ],
    'Wordy': [
        "live-response",
        "results"
    ],
}

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
        self.playerNames = {}
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
        availableModes = list(STEPS.keys())
        for i in range(2):
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
            else:
                emit('update votes', {'votes': self.getVotes()}, to=self.roomCode)


    def removeGameVote(self, playerId):
        if not hasattr(self, 'gameVotes'):
            return

        for k in self.gameVotes:
            if playerId in self.gameVotes[k]:
                self.gameVotes[k].remove(playerId)

                return

    def getGameVotes(self):
        if not hasattr(self, 'gameVotes'):
            return

        return {key: len(self.gameVotes[key]) for key in self.gameVotes}

    def addGameVote(self, item, playerId):
        if not hasattr(self, 'gameVotes') or item not in self.gameVotes:
            return
        
        self.removeGameVote(playerId)
        self.gameVotes[item].append(playerId)

        playerVotes = 0
        for sid in self.players:
            for vote in self.gameVotes:
                if sid in self.gameVotes[vote]:
                    playerVotes += 1

        if playerVotes == self.playerCount:
            # Next vote, add to results
            if not hasattr(self, 'voteResults'):
                self.voteResults = {}

            if self.currentVote not in self.voteResults:
                self.voteResults[self.currentVote] = {}

            newData = {'status': 3, 'game': self.getGame(), 'gameStatus': self.getGameStatus()}
            self.voteResults[self.currentVote] = self.getGameVotes()

            del self.playerResponses[self.currentVote]

            if len(self.playerResponses.keys()) == 0:
                return self.nextPhase()
            
            self.currentVote = list(self.playerResponses.keys())[0]
            newData['question'] = self.currentVote

            self.gameVotes = {}
            for response in self.playerResponses[self.currentVote]:
                self.gameVotes[self.playerResponses[self.currentVote][response]] = []
            newData['responses'] = {key: len(self.gameVotes[key]) for key in self.gameVotes}

            emit('update', newData, to=self.roomCode)

        emit('update game votes', {'votes': self.getGameVotes()}, to=self.roomCode)


    # Check if all players are in a table
    def allPlayersIn(self, t):
        for plrSid in self.players:
            if plrSid not in t:
                return False
            
        return True

    # Try to update player's game status
    def updatePlayerInGame(self, playerId, content, updateType):
        if self.getGame() is None:
            return
        
        if not self.playerInRoom(playerId) or updateType is None or content is None:
            return
        
        # Check if updateType is up to date with current game status
        if not updateType.lower() == STEPS[self.getGame()][self.getGameStatus()]:
            return
        
        if updateType == 'question':
            # Check length
            if len(content) < 5 or len(content) > 40:
                return self.notify("Outside of character range. (5 < length <= 40)")

            if not hasattr(self, 'playerQuestions'):
                self.playerQuestions = {}

            # Check for duplicate question
            for plrSid in self.playerQuestions:
                if self.playerQuestions[plrSid] == content:
                    return self.notify('Question already inputted.', roomId=playerId)
            
            self.playerQuestions[request.sid] = content

            if self.allPlayersIn(self.playerQuestions):
                self.nextPhase()

                return
        elif updateType == 'response':
            if len(content) <= 0 or len(content) > 200:
                return self.notify("Outside character range. (0 < length <= 200)")
            if not hasattr(self, 'playerResponses'):
                self.playerResponses = {}

            if self.playerQuestions[self.questionKey] not in self.playerResponses:
                self.playerResponses[self.playerQuestions[self.questionKey]] = {}

            if request.sid in self.playerResponses[self.playerQuestions[self.questionKey]]:
                return self.notify('Response already submitted.', roomId=playerId)

            # Check for duplicates
            for plrSid in self.playerResponses[self.playerQuestions[self.questionKey]]:
                if self.playerResponses[self.playerQuestions[self.questionKey]][plrSid] == content:
                    # TODO: Notify error
                    return self.notify('Somebody already used this response.', roomId=playerId)

            self.playerResponses[self.playerQuestions[self.questionKey]][request.sid] = content

            if self.allPlayersIn(self.playerResponses[self.playerQuestions[self.questionKey]]):
                self.respondNext()

                return
        
        emit('wait', to=request.sid)

    def respondNext(self):
        if not hasattr(self, "playerQuestions") or not hasattr(self, "questionKey"):
            return

        del self.playerQuestions[self.questionKey]

        if len(list(self.playerQuestions.keys())) == 0:
            # Next phase, all questions answered
            self.nextPhase()

            return

        newData = {'status': 3, 'game': self.getGame(), 'gameStatus': self.getGameStatus()}
        self.questionKey = list(self.playerQuestions.keys())[0]
        newData['question'] = self.playerQuestions[self.questionKey]

        emit('update', newData, to=self.roomCode)

    # Go on to next game phase
    def nextPhase(self):
        if self.getGameStatus() >= len(STEPS[self.getGame()]) - 1:
            # End game
            self.stopGame()

            return
        
        self.gameStatus += 1
        newData = {'status': 3, 'game': self.getGame(), 'gameStatus': self.getGameStatus()}

        self.turnCount += 1

        waitTime = 20

        # Update question if game type is 'response'
        if STEPS[self.getGame()][self.getGameStatus()] == 'response':
            self.questionKey = list(self.playerQuestions.keys())[0]
            newData['question'] = self.playerQuestions[self.questionKey]

            waitTime = 45
        # Send table of responses to vote on
        elif STEPS[self.getGame()][self.getGameStatus()] == 'voting':
            self.currentVote = list(self.playerResponses.keys())[0]
            newData['question'] = self.currentVote

            self.gameVotes = {}
            for response in self.playerResponses[self.currentVote]:
                self.gameVotes[self.playerResponses[self.currentVote][response]] = []
            newData['responses'] = {key: len(self.gameVotes[key]) for key in self.gameVotes}
        # Send game results and schedule task to end game
        elif STEPS[self.getGame()][self.getGameStatus()] == 'results':
            if hasattr(self, 'gameVotes'):
                self.output = {}

                for k in self.voteResults:
                    self.output[k] = ""

                    for resp in self.voteResults[k]:
                        if self.output[k] == '' or self.voteResults[k][resp] > self.voteResults[k][self.output[k]]:
                            self.output[k] = resp

                newData['results'] = self.output
            if hasattr(self, 'playersRemaining'):
                self.output = self.playerNames[self.playersRemaining[0]]
                newData['results'] = self.output
        elif STEPS[self.getGame()][self.getGameStatus()] == 'live-response':
            self.playersRemaining = [plr for plr in self.players]
            self.lastResponse = random.choice(string.ascii_lowercase)
            self.currPlayer = 0
            self.wordsUsed = []
            newData['current'] = self.playerNames[self.playersRemaining[0]]
            newData['prompt'] = "Enter a word starting with " + self.lastResponse
            newData['response'] = ''

            for player in self.players:
                if player != self.playersRemaining[0]:
                    emit('update', newData, to=player)
                else:
                    data = {}
                    for k in newData:
                        data[k] = newData[k]

                    data['responding'] = True
                    emit('update', data, to=player)

            return

        emit('update', newData, to=self.roomCode)

        if 'results' in newData:
            self.startTimer(15, self.stopGame)
        else:
            self.timeoutNextPhase(waitTime)

    def timeoutNextPhase(self, sleepTime):
        currTurn = self.turnCount

        self.startTimer(sleepTime)
        if currTurn == self.turnCount:
            self.nextPhase()

    # Next live phase player
    def nextLiveResponse(self, plr, response, elim=False, ignoreWord=False):
        if  len(response) == 0 or len(response) > 20:
            return self.notify("Response outside of character range (0 < length <= 20)")
        
        if self.getGame() is None or plr is None or not hasattr(self, "currPlayer") or plr != self.playersRemaining[self.currPlayer]:
            return

        # Make sure response first letter starts with last letter of currResponse if game is Wordy
        if self.getGame() == "Wordy":
            if response.lower()[0] != self.lastResponse[len(self.lastResponse) - 1]:
                return self.notify("Response invalid. (Must start with letter of last word.)", roomId=plr)
            elif response.lower() in self.wordsUsed:
                return self.notify("Word already used!", roomId=plr)
            elif not (ignoreWord or isWord(response)):
                return self.notify("Not a word!", roomId=plr)

        data = {'status': 3, 'game': self.getGame(), 'gameStatus': self.getGameStatus()}

        self.turnCount += 1
        
        if not elim:
            self.currPlayer = (self.currPlayer + 1) % len(self.playersRemaining)
        else:
            self.playersRemaining.remove(self.playersRemaining[self.currPlayer])

            self.notify("You have been eliminated!", plr)

            if len(self.playersRemaining) == 1:
                return self.nextPhase()

        self.lastResponse = response.lower()

        data['current'] = self.playerNames[self.playersRemaining[self.currPlayer]]
        data['prompt'] = "Enter a word starting with " + response[len(response) - 1].lower()
        data['response'] = ''

        if not ignoreWord:
            self.wordsUsed.append(response.lower())

        for plr in self.players:
            if plr != self.playersRemaining[self.currPlayer]:
                emit('update', data, to=plr)

        newData = {}
        for k in data:
            newData[k] = data[k]
            newData['responding'] = True

        emit('update', newData, to=self.playersRemaining[self.currPlayer])

        self.liveResponseTimeout(self.playersRemaining[self.currPlayer])

    # Wait ten seconds and try to remove
    def liveResponseTimeout(self, plr):
        curr = self.turnCount

        self.startTimer(5)

        if self.turnCount == curr:
            self.nextLiveResponse(plr, self.lastResponse[len(self.lastResponse) - 1] + random.choice(string.ascii_lowercase), True, True)

    # Remove player from live response
    def removeFromLiveResponse(self, plr):
        if self.getGame() is None or self.getGameType() != "live-response":
            return

        if plr == self.playersRemaining[self.currPlayer]:
            self.nextLiveResponse(plr, self.lastResponse[len(self.lastResponse) - 1] + random.choice(string.ascii_lowercase), True)
        elif plr in self.playersRemaining:
            i = self.playersRemaining.index(plr)
            if i < self.currPlayer:
                i -= 1
                self.playersRemaining.remove(plr)

                if len(self.playersRemaining) == 1:
                    self.nextPhase()
    
    # Update live response text
    def updateLiveResponse(self, response):
        if self.getGame() is None or self.getGameType() != "live-response" or request.sid != self.playersRemaining[self.currPlayer]:
            return

        self.response = response

        for plrId in self.players:
            if plrId != self.playersRemaining[self.currPlayer]:
                emit('update', {'prompt': "Enter a word starting with " + self.lastResponse[len(self.lastResponse) - 1], 'status': 3, 'game': self.getGame(), 'gameStatus': self.getGameStatus(), 'current': self.playerNames[self.players[self.currPlayer]], 'response': response}, to=plrId)
    
    # Remove player from current game stats
    def removeFromGame(self, plrId):
        if self.getGameStatus() == -1:
            return

        if STEPS[self.getGame()][self.getGameStatus()] == 'question' and self.allPlayersIn(self.playerQuestions):
            self.nextPhase()
        elif STEPS[self.getGame()][self.getGameStatus()] == 'response' and self.allPlayersIn(self.playerResponses[self.playerQuestions[self.questionKey]]):
            self.respondNext()
        elif STEPS[self.getGame()][self.getGameStatus()] == 'voting':
            playerVotes = 0
            for sid in self.players:
                for vote in self.gameVotes:
                    if sid in self.gameVotes[vote]:
                        playerVotes += 1

            if playerVotes == self.playerCount:
                # Next vote, add to results
                if not hasattr(self, 'voteResults'):
                    self.voteResults = {}

                if self.currentVote not in self.voteResults:
                    self.voteResults[self.currentVote] = {}

                newData = {'status': 3, 'game': self.getGame(), 'gameStatus': self.getGameStatus()}
                self.voteResults[self.currentVote] = self.getGameVotes()

                del self.playerResponses[self.currentVote]

                if len(self.playerResponses.keys()) == 0:
                    return self.nextPhase()
                
                self.currentVote = list(self.playerResponses.keys())[0]
                newData['question'] = self.currentVote

                self.gameVotes = {}
                for response in self.playerResponses[self.currentVote]:
                    self.gameVotes[self.playerResponses[self.currentVote][response]] = []
                newData['responses'] = {key: len(self.gameVotes[key]) for key in self.gameVotes}

                emit('update', newData, to=self.roomCode)
        elif self.getGameType() == 'live-response':
            self.removeFromLiveResponse(plrId)

    # Set selected game, update status, change phase
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
        self.gameStatus = -1

        self.clearVotes()
        self.updateStatus(3)

        self.turnCount = 0

        return self.nextPhase()

    # Ends game, clears game information
    def stopGame(self):
        if not hasattr(self, 'selectedGame'):
            return
        
        delattr(self, 'selectedGame')
        delattr(self, 'gameStatus')
        
        if hasattr(self, 'playerQuestions'):
            delattr(self, 'playerQuestions')
        if hasattr(self, 'playerAnswers'):
            delattr(self, 'playerAnswers')
        if hasattr(self, 'playerResponses'):
            delattr(self, 'playerResponses')
        if hasattr(self, 'questionKey'):
            delattr(self, 'questionKey')
        if hasattr(self, 'output'):
            delattr(self, 'output')
        if hasattr(self, 'voteResults'):
            delattr(self, 'voteResults')
        if hasattr(self, 'gameVotes'):
            delattr(self, 'gameVotes')
        if hasattr(self, 'playersReady'):
            delattr(self, 'playersReady')
        if hasattr(self, 'playersRemaining'):
            delattr(self, 'playersRemaining')
        if hasattr(self, 'turnCount'):
            delattr(self, 'turnCount')
        if hasattr(self, 'currPlayer'):
            delattr(self, 'currPlayer')
        if hasattr(self, 'wordsUsed'):
            delattr(self, 'wordsUsed')
        if hasattr(self, 'response'):
            delattr(self, 'response')

        if self.playerCount >= 2:
            self.updateStatus(1)
            self.initReady()
            emit('update', {'status': 1}, to=self.roomCode)
        else:
            self.updateStatus(0)
            emit('update', {'status': 0}, to=self.roomCode)

    # Get current game status
    def getGameStatus(self):
        if not hasattr(self, 'gameStatus'):
            return -1
        else:
            return self.gameStatus

    # Get game type
    def getGameType(self):
        if self.getGameStatus() == -1:
            return
        return STEPS[self.getGame()][self.getGameStatus()]

    # Has game started
    def isStarted(self):
        return hasattr(self, 'selectedGame')

    # Return gamemode
    def getGame(self):
        if not hasattr(self, 'selectedGame'):
            return None

        return self.selectedGame

    # Remove player vote
    def removeVote(self, playerId):
        if not hasattr(self, 'roomVotes'):
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
        self.playerNames[playerId] = session['player-name']

        if self.playerCount >= 2 and self.getStatus() == 0:
            self.initReady()
            self.updateStatus(1)
            emit('update', {'status': 1}, to=self.roomCode)
        elif self.getStatus() == 1:
            emit('update', {'status': 1}, to=request.sid)
        elif self.playerCount >= 2:
            # in game, send update
            data = {'status': 2}
            if self.getStatus() == 3:
                data['status'] = 3
                data['game'] = self.getGame()
                data['gameStatus'] =  self.getGameStatus()

                stat = STEPS[self.getGame()][self.getGameStatus()]
                if stat == "response":
                    data['question'] = self.playerQuestions[self.questionKey]
                elif stat == "voting":
                    data['question'] = self.currentVote
                    data['responses'] = {key: len(self.gameVotes[key]) for key in self.gameVotes}
                elif stat == 'live-response':
                    data['response'] = self.response
                    data['prompt'] = "Enter a word starting with " + self.lastResponse[len(self.lastResponse) - 1]

                emit('update', data, to=request.sid)
            else:
                emit('update', data, to=request.sid)
                emit('update votes', {'votes': self.getVotes()}, to=request.sid)

        emit('update players', {'players': [self.playerNames[n] for n in self.playerNames]}, to=self.roomCode)
        
        return True

    # Remove player from room
    def removePlayer(self, playerId):
        if not self.playerInRoom(playerId):
            return False

        self.playerCount -= 1
        self.removeVote(playerId)
        self.unreadyPlayer(playerId)
        self.players.remove(playerId)

        if self.playerCount == 0:
            self.destroy()
        elif self.playerCount == 1:
            self.updateStatus(0)
            self.clearVotes()
            self.clearReady()
            self.stopGame()

            if self.getStatus() != 0:
                emit('update', {'status': 0}, to=session['room-code'])
        else:
            self.removeFromGame(playerId)

        del self.playerNames[playerId]

        emit('update players', {'players': [self.playerNames[n] for n in self.playerNames]}, to=self.roomCode)

    # Adds callback when room is destroyed
    def setDestroyCallback(self, destroyCallback):
        self.destroyCallback = destroyCallback

    # Destroys room
    def destroy(self):
        roomsDB.delete_one({'code': self.roomCode})
        self.destroyCallback()
    
    # Returns map of all modes and their vote counts
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
        if len(self.playersReady) >= self.playerCount/2:
            self.updateStatus(2)
            self.initVotes()
            emit('update', {'status': 2}, to=self.roomCode)

            newData = {'votes': self.getVotes()}
            emit('update votes', newData, to=self.roomCode)

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

    def startTimer(self, duration, callback=None):
        emit('start timer', {'duration': duration}, to=self.roomCode)
        time.sleep(duration)
        if callback is not None:
            callback()

    def notify(self, message, roomId=None):
        if roomId is None:
            roomId = self.roomCode
        
        emit('notify', {'message': message}, to=roomId)

def genCode():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(6))