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

manageName();