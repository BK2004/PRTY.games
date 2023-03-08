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
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="UNDEF">
        <p class="text-primary frame-header">Random</p>
        <img src="/static/images/random.svg">
        <p class="text-primary vote-count">0 votes</p>
    </div>
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="UNDEF">
        <p class="text-primary frame-header">Random</p>
        <img src="/static/images/random.svg">
        <p class="text-primary vote-count">0 votes</p>
    </div>
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="UNDEF">
        <p class="text-primary frame-header">Random</p>
        <img src="/static/images/random.svg">
        <p class="text-primary vote-count">0 votes</p>
    </div>
    <div class="game-frame fill-h bs background-purple flex flex-column" data-selected="false" data-type="UNDEF">
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
`