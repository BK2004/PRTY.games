var messages = [];

const gameContainer = document.querySelector('.game');
const titleStatus = document.querySelector('.title-status');

var votingConns = [];

$(document).ready(socket.on("connect", function() {
    changeScreen(0, {message: "Joining room..."});
    socket_joinRoom();
    updateScreen();
    socket_initializeEvents();
}));

function socket_initializeEvents() {
    socket.on("disconnect", () => {
        window.close();
    });

    // Send and receive messages
    $('.chat-input .input').keydown(function(e) {
        if (e.keyCode === 13 && !e.shiftKey) {
            e.preventDefault();
            socket_onMessageSend($(this).val());
            $(this).val('');
        }
    });

    socket.on('message recieve', socket_onMessageRecieve);
    socket.on('update', socket_onStatusChange);
    socket.on('update votes', socket_onVoteUpdate);
    socket.on('update game votes', socket_onGameVoteUpdate);
    socket.on('wait', socket_onWait);
}

function socket_joinRoom() {
    // Join room
    socket.emit('join', {'code': ROOM_CODE});
}

function socket_onMessageSend(message) {
    // Attempt to send message
    const data = {
        'content': message,
    };

    socket.emit('message send', data);
}

function socket_onMessageRecieve(data) {
    // Create new chat entry with given data
    const newElement = document.createElement('div');
    newElement.classList.add('chat-entry');
    newElement.innerHTML = '<p><strong>' + data.username + ': </strong>' + data.content + '</p>';
    document.querySelector('.chat-entries').appendChild(newElement);
    messages.push(newElement);
}

function socket_onVoteUpdate(data) {
    Object.keys(data.votes).forEach((key) => {
        // Set frame to be given mode if not exists
        if (document.querySelector(`.vote-frame[data-type="${key}"]`) === null) {
            document.querySelector(`.vote-frame[data-type=UNDEF]`).dataset.type = key;
        }
        document.querySelector(`.vote-frame[data-type="${key}"]`).querySelector('.vote-count').innerHTML = `${data.votes[key]} votes`;
        document.querySelector(`.vote-frame[data-type="${key}"]`).querySelector('.frame-header').innerHTML = `${key}`;
    });
}

function socket_onGameVoteUpdate(data) {
    Object.keys(data.votes).forEach((key) => {
        document.querySelector(`.game-vote-frame[data-type="${key}"]`).querySelector('.vote-count').innerHTML = `${data.votes[key]} votes`;
    })
}

function socket_onWait() {
    gameContainer.innerHTML = '<div class="waiting" disabled="true">' + gameContainer.innerHTML + '</div>';

    gameContainer.querySelectorAll('input button').forEach((obj) => {
        obj.ariaDisabled = true;
    });
}

function socket_onStatusChange(data) {
    roomStatus = data.status;

    updateScreen(data);
}

function initVoting() {
    changeScreen(1);
    const votingFrames = document.querySelectorAll('.vote-frame');
    votingFrames.forEach((item) => {
        // Click event
        item.addEventListener("click", (e) => {
            // if item is not selected, change it to the voted game
            if (item.dataset.selected === "false") {
                const currentlySelected = document.querySelector('.vote-frame[data-selected="true"]');
                if (currentlySelected) {
                    currentlySelected.dataset.selected = "false";
                }

                item.dataset.selected = "true";

                socket.emit('vote', {'gamemode': item.dataset.type});
            } else {
                return;
            }
        });
    });
}

function connectGameVotes() {
    document.querySelectorAll('.game-vote-frame').forEach((item) => {
        item.addEventListener('click', (e) => {
            if (item.dataset.selected === "false") {
                const curr = document.querySelector('.game-vote-frame[data-selected="true"]');
                if (curr) {
                    curr.dataset.selected = "false";
                }

                item.dataset.selected = "true";

                socket.emit('game vote', {'item': item.dataset.type});
            }
        });
    });
}

function updateScreen(data={}) {
    if (roomStatus == 0) {
        changeScreen(0, {message: 'Waiting on players...'});
    } else if (roomStatus == 1) {
        changeScreen(0, {message: 'Waiting on players to ready up...', showReady: true});
    } else if (roomStatus == 2) {
        initVoting();
    } else if (roomStatus == 3) {
        initGame(data);
    }
}

function changeScreen(screenId, extra) {
    switch (screenId) {
        case (0): // Status
            gameContainer.innerHTML = STATUS_TEMPLATE.replace("{message}", extra.message);
            if (extra.showReady) {
                gameContainer.innerHTML += READY_TEMPLATE;

                // Add button listener
                document.querySelector(".ready-button").addEventListener('click', (e) => {
                    socket.emit('ready', {});
                });
            }
            titleStatus.innerHTML = "";
            break;
        case(1): // Map Voting
            gameContainer.innerHTML = VOTING_TEMPLATE;
            titleStatus.innerHTML = "GAME VOTING";
            break;
        case(2): // Game
            gameContainer.innerHTML = GAME_TEMPLATE.replaceAll("{game}", extra.game);
            titleStatus.innerHTML = extra.game.toUpperCase();

            var content = "";

            // Switch that checks game type and changes screen based off game status
            switch (extra.game.toLowerCase().replaceAll(" ", "")) {
                case 'fillintheblank':
                    content = getFITBScreen(extra.gameStatus, extra);
        
                    break;
            }

            gameContainer.innerHTML = gameContainer.innerHTML.replaceAll("{content}", content);

            // Do queries with prompts
            gameContainer.querySelectorAll('.prompt-container').forEach((obj) => {
                const submitButton = obj.querySelector('.prompt-button');
                const promptInput = obj.querySelector('.prompt-input');

                submitButton.addEventListener("click", (e) => {
                    socket.emit(submitButton.dataset.target, {'content': promptInput.value});
                });
            });

            connectGameVotes();

            break;
    }
}

// Starts game
function initGame(data) {
    changeScreen(2, data);
}