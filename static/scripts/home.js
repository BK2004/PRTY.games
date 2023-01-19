// Private/public radios
const radios = document.querySelectorAll("input[type=radio]");
const lobbyName = document.querySelector(".lobby-input");

function handleRadio() {
    radios.forEach((radio) => {
        radio.addEventListener("click", (e) => {
            if (radio.checked) {
                if (radio.id === "private") {
                    lobbyName.disabled = true;
                } else {
                    lobbyName.disabled = false;
                }
            }
        });
    });
}

// Join handler
const joinInput = document.querySelector('.code-input');
const joinForm = document.querySelector('.join > form');

function handleJoinInput() {
    joinInput.addEventListener("input", (e) => {
        joinForm.action = "/room/" + joinInput.value;
        console.log(joinInput.value);
    });
}

// Name input
const maxNameLength = 12;
const nameInput = document.querySelector('.name-input');
const updateURL = "/updateName"

function manageName() {
    nameInput.addEventListener("focusout", (e) => {
        if (nameInput.value.trim() === "") {
            nameInput.value = "Guest";
        } else {
            nameInput.value = nameInput.value.trim().substring(0, maxNameLength);
        }

        const httpRequest = new XMLHttpRequest();
        httpRequest.open("POST", updateURL);
        httpRequest.setRequestHeader("content-type", "application/x-www-form-urlencoded;charset=UTF-8");

        httpRequest.onload = () => {
            console.log(httpRequest.responseText);
        };

        httpRequest.send('player-name=' + nameInput.value);
    });

    nameInput.addEventListener("input", (e) => {
        nameInput.value = nameInput.value.substring(0, maxNameLength);
    });
}

manageName();
handleRadio();
handleJoinInput();