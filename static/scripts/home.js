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

// Handle lobby browser
const rightTarget = document.querySelector(".right");
const leftTarget = document.querySelector(".left");
const lobbyBrowser = document.querySelector(".browser-holder");
function handleBrowser() {
    rightTarget.addEventListener("click", (e) => {
        const httpRequest = new XMLHttpRequest();
        httpRequest.open("GET", "/getPublics/" + rightTarget.dataset.target);
        httpRequest.onload = () => {
            if (httpRequest.response === "[]") { return; }
            lobbyBrowser.innerHTML = "";
            const req = JSON.parse(httpRequest.response);
            req.forEach(data => {
                lobbyBrowser.innerHTML += `<tr class="fs-4 w-100">
                <td class="text-center pt-6 pb-6 w-75"><a href="/room/${data.code}">${data.name}</a></td>
                <td class="text-center pt-6 pb-6 w-25">${data.playerCount}</td>
            </tr>`;
            });

            if (lobbyBrowser.innerHTML !== "") {
                leftTarget.dataset.target = Math.min(Math.max(parseInt(leftTarget.dataset.target) + 1, 1), parseInt(rightTarget.dataset.target));
                rightTarget.dataset.target = Math.min(Math.max(parseInt(rightTarget.dataset.target) + 1, 2), parseInt(rightTarget.dataset.target));
            }
        }
        httpRequest.send();
    });

    leftTarget.addEventListener("click", (e) => {
        const httpRequest = new XMLHttpRequest();
        httpRequest.open("GET", "/getPublics/" + leftTarget.dataset.target);
        httpRequest.onload = () => {
            if (httpRequest.response === "[]") { return; }

            lobbyBrowser.innerHTML = "";
            const req = JSON.parse(httpRequest.response);
            req.forEach(data => {
                lobbyBrowser.innerHTML += `<tr class="fs-4 w-100">
                <td class="text-center pt-6 pb-6 w-75"><a href="/room/${data.code}">${data.name}</a></td>
                <td class="text-center pt-6 pb-6 w-25">${data.playerCount}</td>
            </tr>`;
            });

            leftTarget.dataset.target = Math.min(Math.max(parseInt(leftTarget.dataset.target) - 1, 1), parseInt(rightTarget.dataset.target));
            rightTarget.dataset.target = Math.min(Math.max(parseInt(rightTarget.dataset.target) - 1, 2), parseInt(rightTarget.dataset.target));
        }
        httpRequest.send();
    });
}

manageName();
handleRadio();
handleJoinInput();
handleBrowser();