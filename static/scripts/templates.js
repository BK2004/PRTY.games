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
    <div class="vote-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="UNDEF">
        <p class="text-primary frame-header">Random</p>
        <img src="/static/images/random.svg">
        <p class="text-primary vote-count">0 votes</p>
    </div>
    <div class="vote-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="UNDEF">
        <p class="text-primary frame-header">Random</p>
        <img src="/static/images/random.svg">
        <p class="text-primary vote-count">0 votes</p>
    </div>
    <div class="vote-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="UNDEF">
        <p class="text-primary frame-header">Random</p>
        <img src="/static/images/random.svg">
        <p class="text-primary vote-count">0 votes</p>
    </div>
</div>
`;

const GAME_TEMPLATE = `
{content}
`;

const PROMPT_TEMPLATE = `
<div class="prompt-container">
    <h1 class="mb-5">{prompt}</h1>
    <input type="text" class="background-white text-center fs-3 m-auto inset-bs mb-4 block prompt-input w-75 p-6">
    <button class="prompt-button m-auto mt-3 mb-5 text-primary fs-1 background-purple" data-target="{target}">SUBMIT</button>
</div>
`;

const LIVE_PROMPT_TEMPLATE = `
<div class="prompt-container">
    <h1 class="mb-5">{prompt}</h1>
    <input type="text" class="live-response background-white text-center fs-3 m-auto inset-bs mb-4 block prompt-input w-75 p-6">
    <button class="prompt-button m-auto mt-3 mb-5 text-primary fs-1 background-purple" data-target="{target}">SUBMIT</button>
</div>
`;

const RESPONSE_UPDATE_TEMPLATE = `
<div class="response-update-container">
    <h1 class="mb-5">{prompt}</h1>
    <p class="background-white text-center fs-3 m-auto mb-4 block w-75">{response}</p>
    <h2 class="mt-3"><span class="color-purple">{player}</span> is going!</h2>
</div>
`

const VOTE_TEMPLATE = `
<div class="vote-container">
    <h1 class="mb-5">{prompt}</h1>
    <div class="response-voting-wrap">
        {voting-frames}
    </div>
</div>
`;

const GAME_VOTE_TEMPLATE = `
<div class="game-vote-container">
    <h1 class="mb-5">{prompt}</h1>
    <div class="response-voting-wrap">
        {voting-frames}
    </div>
</div>
`;

const VOTE_FRAME_TEMPLATE = `
<div class="game-vote-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="{content}">
    <p class="text-primary frame-header">{content}</p>
    <p class="text-primary vote-count">{votes} votes</p>
</div>
`;

const RESULT_TEMPLATE = `
<div class="result-container">
    <h1 class="mb-5">Results</h1>
    <div class="results-wrap">{result-frames}</div>
</div>
`;

const RESULT_FRAME = `
<div class="result-frame background-purple bs p-2">
    <p class="text-primary frame-header mt-4">{content}</p>
    <p class="text-primary frame-winner mb-4">{most-voted}</p>
</div>
`;

const WINNER_FRAME = `
<div class="result-frame background-purple bs p-3">
    <h1 class="text-primary m-auto"><strong>{player}</strong> has won!</h1>
</div>
`;

const TIMER_TEMPLATE = `
<div class="timer">
    {timeLeft}
</div>
`;

const PLAYER_TEMPLATE = `
<div class="player-frame">
    <p class="frame-name fill m-auto text-center pb-5 pt-5">{name}</p>
</div>
`;