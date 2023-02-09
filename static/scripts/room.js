var messages = [];

const gameContainer = document.querySelector('.game');
const titleStatus = document.querySelector('.title-status');

$(document).ready(socket.on("connect", function() {
    changeScreen(0, {message: "Joining room..."});
    socket_joinRoom();
    socket_initializeEvents();
    changeScreen(1);
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

function changeScreen(screenId, extra) {
    switch (screenId) {
        case (0): // Status
            gameContainer.innerHTML = STATUS_TEMPLATE.replace("{message}", extra.message);
            titleStatus.innerHTML = "";
            break;
        case(1): // Map Voting
            gameContainer.innerHTML = VOTING_TEMPLATE;
            titleStatus.innerHTML = "GAME VOTING";
            break;
    }
}

const STATUS_TEMPLATE = `
<h1 class="text-tertiary status-message">{message}</h1>
<span class="loading-image mt-5"></span>
`;

const VOTING_TEMPLATE = `
<h1>GAME VOTING</h1>
`;