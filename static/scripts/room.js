var messages = [];

$(document).ready(socket.on("connect", function() {
    socket_joinRoom();
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