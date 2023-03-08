function getFITBScreen(gameStatus, extra="") {
    var target = "";

    switch (gameStatus) {
        case 0: // Entering question phase
            target = "submit question";

            return PROMPT_TEMPLATE.replaceAll("{prompt}", "Ask a question!").replaceAll("{target}", target);
        case 1: // Entering response phase
            target = "submit response";

            return PROMPT_TEMPLATE.replaceAll("{prompt}", extra).replaceAll("{target}", target);
        default:
            return ``;

    }
}