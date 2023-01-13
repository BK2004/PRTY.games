// Name input
const maxNameLength = 12;
const nameInput = document.querySelector('.name-input');

function manageName() {
    nameInput.addEventListener("focusout", (e) => {
        if (nameInput.value.trim() === "") {
            nameInput.value = "Guest";
        } else {
            nameInput.value = nameInput.value.trim().substring(0, maxNameLength);
        }
    });

    nameInput.addEventListener("input", (e) => {
        nameInput.value = nameInput.value.substring(0, maxNameLength);
    });
}

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

manageName();
handleRadio();