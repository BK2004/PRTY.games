function getFITBScreen(gameStatus, extra={}) {
    var target = "";

    switch (gameStatus) {
        case 0: // Entering question phase
            target = "submit question";

            return PROMPT_TEMPLATE.replaceAll("{prompt}", "Ask a question!").replaceAll("{target}", target);
        case 1: // Entering response phase
            target = "submit response";

            return PROMPT_TEMPLATE.replaceAll("{prompt}", extra.question).replaceAll("{target}", target);
        case 2: // Voting on best response
            target = "submit vote";

            let voteFrames = [];
            for (let k in extra.responses) {
                voteFrames.push(VOTE_FRAME_TEMPLATE.replaceAll("{content}", k).replaceAll("{votes}", extra.responses[k]));
            }

            return GAME_VOTE_TEMPLATE.replaceAll("{prompt}", extra.question).replaceAll("{target}", target).replaceAll("{voting-frames}", voteFrames.concat(""));
        case 3: // Results
            let resultFrames = [];
            for (let k in extra.results) {
                resultFrames.push(RESULT_FRAME.replaceAll("{content}", k).replaceAll("{most-voted}", extra.results[k]));
            }

            return RESULT_TEMPLATE.replaceAll("{result-frames}", resultFrames.concat(""));
        default:
            return ``;
    }
}

function getWordyScreen(gameStatus, extra={}) {
    switch (gameStatus) {
        case 0: // Live response
            if (extra.responding) {
                return LIVE_PROMPT_TEMPLATE.replaceAll("{prompt}", extra.prompt).replaceAll("{target}", "submit live response");
            }

            return RESPONSE_UPDATE_TEMPLATE.replaceAll("{prompt}", extra.prompt).replaceAll("{response}", extra.response).replaceAll("{player}", extra.current);
        case 1: // Results
            return WINNER_FRAME.replaceAll("{player}", extra.results);
        default:
            return '';
    }
}