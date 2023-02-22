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

function socket_onStatusChange(data) {
    roomStatus = data.status;

    updateScreen();
}

function initVoting() {
    changeScreen(1);
    const votingFrames = document.querySelectorAll('.game-frame');
    votingFrames.forEach((item) => {
        // Click event
        item.addEventListener("click", (e) => {
            // if item is not selected, change it to the voted game
            if (item.dataset.selected === "false") {
                document.querySelector('.game-frame[data-selected="true"]').dataset.selected = "false";
                item.dataset.selected = "true";
            } else {
                return;
            }
        });
    });
}

function updateScreen() {
    if (roomStatus == 0) {
        changeScreen(0, {message: 'Waiting on players...'});
    } else if (roomStatus == 1) {
        changeScreen(0, {message: 'Waiting on players to ready up...', showReady: true});
    } else if (roomStatus == 2) {
        initVoting();
    }
}

function changeScreen(screenId, extra) {
    switch (screenId) {
        case (0): // Status
            gameContainer.innerHTML = STATUS_TEMPLATE.replace("{message}", extra.message);
            if (extra.showReady) {
                gameContainer.innerHTML += READY_TEMPLATE;
            }
            titleStatus.innerHTML = "";
            break;
        case(1): // Map Voting
            gameContainer.innerHTML = VOTING_TEMPLATE;
            titleStatus.innerHTML = "GAME VOTING";
            break;
    }
}

const STATUS_TEMPLATE = `
<div>
    <h1 class="text-tertiary status-message ml-auto mr-auto">{message}</h1>
    <span class="loading-image mt-5 ml-auto mr-auto"></span>
</div>
`;

const READY_TEMPLATE = `
<button class="ready-button m-auto mt-3 mb-5 text-primary fs-1 background-green">READY</button>
`

const VOTING_TEMPLATE = `
<div class="voting-wrap h-25 fill">
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="true" data-type="random">
        <img src="/static/images/random.svg">
        <p class="text-primary">0 votes</p>
    </div>
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="random">
        <img src="/static/images/random.svg">
        <p class="text-primary">0 votes</p>
    </div>
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="random">
        <img src="/static/images/random.svg">
        <p class="text-primary">0 votes</p>
    </div>
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="random">
        <img src="/static/images/random.svg">
        <p class="text-primary">0 votes</p>
    </div>
</div>
`;