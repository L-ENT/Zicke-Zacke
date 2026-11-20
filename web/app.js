'use strict';

const byId = id => document.getElementById(id);
const symbols = ['Carrot', 'Snail', 'Ladybug', 'Butterfly', 'Fried egg', 'Mushroom',
  'Feather', 'Apple', 'Sunflower', 'Strawberry', 'Nest', 'Corn'];
const defaultNames = ['Goldie', 'Ruby', 'Clover', 'Plum'];
// Translate the old stock names only when resuming data from the first edition.
const legacyNames = ['Gà Vàng', 'Gà Đỏ', 'Gà Xanh', 'Gà Tím'];
const legacyGameId = readStorage('sanga.game.v1');
const positions = [
  [18, 18], [28.7, 15.5], [39.35, 15], [50, 15], [60.65, 15], [71.3, 15.5],
  [82, 18], [90, 25], [93.1, 36], [93.5, 50], [93.1, 64], [90, 76.5],
  [82, 84], [71.3, 87], [60.65, 87.5], [50, 87.5], [39.35, 87.5], [28.7, 87],
  [18, 84], [10, 76.5], [6.9, 64], [6.5, 50], [6.9, 36], [10, 23.5]
];
const gameKey = 'sanga.game.v2';
const namesKey = 'sanga.names.v2';
const soundKey = 'sanga.sound.v1';
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const yard = new YardMotion.Yard(byId('field'), byId('pawns'), positions, reducedMotion);
const cards = [];
const eggs = [];
let game = null;
let busy = true;
let offline = false;
let soundOn = readStorage(soundKey) === 'yes';
let audioContext;

function readStorage(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function saveStorage(key, value) {
  try { localStorage.setItem(key, value); } catch { /* Play also works without storage. */ }
}
function migrateName(name, index) {
  return name === legacyNames[index] ? defaultNames[index] : name;
}
function rosterPreference() {
  try {
    const saved = readStorage(namesKey);
    const names = JSON.parse(saved || readStorage('sanga.names.v1'));
    if (Array.isArray(names) && names.length >= 2 && names.length <= 4
        && names.every(n => typeof n === 'string' && n.trim() && n.length <= 24)) {
      return saved ? names : names.map(migrateName);
    }
  } catch { /* Use the four chickens on the first visit. */ }
  return [...defaultNames];
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function icon(name, extra = '') {
  const node = element('i', 'icon i-' + name + (extra ? ' ' + extra : ''));
  node.setAttribute('aria-hidden', 'true');
  return node;
}
function setSymbol(node, symbol) {
  node.style.setProperty('--sx', (symbol % 4) * 100 / 3 + '%');
  node.style.setProperty('--sy', Math.floor(symbol / 4) * 50 + '%');
  node.hidden = false;
}
function setHen(node, id, feathers) {
  // Each row is a body color. Each column is one subset of the four original feathers.
  const mask = feathers.reduce((bits, owner) => bits | (1 << owner), 0);
  node.classList.add('chicken');
  node.style.setProperty('--sx', mask * 100 / 15 + '%');
  node.style.setProperty('--sy', id * 100 / 3 + '%');
}
function hen(id, feathers = [id]) {
  const sprite = element('span', 'sprite');
  setHen(sprite, id, feathers);
  return sprite;
}
function featherCount(n) {
  return n + (n === 1 ? ' tail feather' : ' tail feathers');
}
function atPosition(node, position) {
  const [x, y] = positions[position];
  node.style.setProperty('--x', x + '%');
  node.style.setProperty('--y', y + '%');
}
function showFeedback(message, kind = 'ready') {
  const icons = {ready: 'hand', match: 'check', miss: 'clockwise', jump: 'feather', win: 'trophy', error: 'alert'};
  byId('feedback').dataset.kind = kind;
  byId('feedback').querySelector('.feedback-mark').replaceChildren(icon(icons[kind]));
  byId('feedback-text').textContent = message;
}
function lockBoard(locked) {
  busy = locked;
  yard.setIdle(!locked && !offline);
  const unavailable = busy || offline || !game || game.winner !== -1;
  cards.forEach(card => card.setAttribute('aria-disabled', String(unavailable)));
  byId('new-game').disabled = busy;
}
function buildBoard() {
  for (let i = 0; i < positions.length; i++) {
    const egg = element('div', 'egg');
    egg.setAttribute('role', 'listitem');
    atPosition(egg, i);
    const art = element('span', 'sprite');
    art.hidden = true;
    egg.append(art);
    eggs.push(egg);
    byId('track').append(egg);
  }
  for (let slot = 0; slot < 12; slot++) {
    const button = element('button', 'memory-card');
    button.type = 'button';
    button.dataset.slot = slot;
    button.setAttribute('aria-label', 'Flip tile ' + (slot + 1));
    button.setAttribute('aria-disabled', 'true');
    const flip = element('span', 'flip-body');
    const back = element('span', 'card-face card-back');
    back.append(element('span', 'card-number', String(slot + 1).padStart(2, '0')));
    const front = element('span', 'card-face card-front');
    const art = element('span', 'sprite');
    art.hidden = true;
    front.append(art);
    flip.append(back, front);
    flip.setAttribute('aria-hidden', 'true');
    button.append(flip);
    button.addEventListener('click', () => flipCard(slot));
    button.addEventListener('keydown', event => {
      const steps = {ArrowLeft: -1, ArrowRight: 1, ArrowUp: -4, ArrowDown: 4};
      if (!(event.key in steps)) return;
      event.preventDefault();
      cards[(slot + steps[event.key] + 12) % 12].focus();
    });
    cards.push(button);
    byId('cards').append(button);
  }
  new ResizeObserver(drawTrail).observe(byId('field'));
}

function drawTrail() {
  const canvas = byId('trail');
  if (!canvas.clientWidth || !canvas.clientHeight) return;
  canvas.width = canvas.clientWidth > canvas.clientHeight * 1.25 ? 448 : 288;
  canvas.height = Math.round(canvas.width * canvas.clientHeight / canvas.clientWidth);
  const ctx = canvas.getContext('2d');
  const points = positions.map(([x, y]) => [x * canvas.width / 100, y * canvas.height / 100]);
  points.forEach((a, i) => {
    const b = points[(i + 1) % points.length];
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const length = Math.hypot(dx, dy);
    const forward = [dx / length, dy / length], side = [-forward[1], forward[0]];
    // Small three-toed tracks only in the gaps between egg shells.
    for (const [fraction, offset] of [[.44, -.8], [.6, .8]]) {
      const x = a[0] + fraction*dx + offset*side[0], y = a[1] + fraction*dy + offset*side[1];
      const toe = (f, s) => [Math.round(x+f*forward[0]+s*side[0]), Math.round(y+f*forward[1]+s*side[1])];
      ctx.fillStyle = '#a78356';
      ctx.fillRect(...toe(0,0), 2, 1);
      ctx.fillRect(...toe(2,0), 1, 1);
      ctx.fillRect(...toe(1,1), 1, 1);
      ctx.fillRect(...toe(1,-1), 1, 1);
    }
  });
}

function renderEgg(state, i) {
  const egg = eggs[i], symbol = state.track[i];
  const occupant = state.players.find(p => p.position === i);
  setSymbol(egg.firstChild, symbol);
  egg.classList.toggle('target', i === state.target);
  egg.classList.toggle('occupied', Boolean(occupant));
  egg.setAttribute('aria-label', 'Egg ' + (i + 1) + ', ' + symbols[symbol]
    + (occupant ? ', ' + occupant.name + ', ' + featherCount(occupant.feathers.length) : '')
    + (i === state.target ? ', target egg' : ''));
}
function renderState(state) {
  game = state;
  const ended = state.winner !== -1;
  const player = state.players[state.active];
  eggs.forEach((_,i) => renderEgg(state, i));
  yard.sync(state);
  byId('turn-panel').dataset.color = player.id;
  byId('turn-label').textContent = ended ? 'Winner' : 'Current player';
  byId('current-name').textContent = player.name;
  byId('turn-count').textContent = 'Turn ' + state.turn;
  byId('target-label').textContent = ended ? 'Finish' : 'Find this picture';
  byId('target-name').textContent = ended ? 'All feathers collected!' : symbols[state.track[state.target]];
  setSymbol(byId('target-art'), ended ? 6 : state.track[state.target]);
  byId('player-count').textContent = state.players.length + ' players';
  byId('goal-note').textContent = 'Collect all ' + state.players.length + ' feathers to win.';
  renderFlock(state);
  lockBoard(busy);
}
function renderFlock(state) {
  const player = state.players[state.active];
  setHen(byId('current-hen'), player.id, player.feathers);
  byId('players').replaceChildren(...state.players.map(p => {
    const row = element('li', 'player-row' + (p.id === player.id ? ' active' : ''));
    row.dataset.color = p.id;
    if (p.id === player.id) row.setAttribute('aria-current', 'true');
    const avatar = element('span', 'avatar');
    avatar.setAttribute('aria-hidden', 'true');
    avatar.append(hen(p.id, p.feathers));
    const score = element('span', 'feather-score');
    score.setAttribute('aria-label', featherCount(p.feathers.length));
    score.title = featherCount(p.feathers.length);
    const quills = element('span', 'feathers');
    if (!p.feathers.length) quills.append(icon('feather', 'empty'));
    p.feathers.forEach(owner => {
      const quill = icon('feather');
      quill.dataset.color = owner;
      quills.append(quill);
    });
    score.append(quills, element('b', '', p.feathers.length));
    row.append(avatar, element('span', 'player-name', p.name), score);
    return row;
  }));
}

async function request(path, form) {
  const options = form ? {method: 'POST', headers: {'X-Zicke-Game': '1'}, body: form} : {};
  const response = await fetch(path, {...options, cache: 'no-store'});
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error);
    error.status = response.status;
    throw error;
  }
  const state = data.game || data;
  if (legacyGameId && state.id === legacyGameId) {
    for (const player of state.players) player.name = migrateName(player.name, player.id);
  }
  return data;
}
async function createGame(names) {
  const form = new URLSearchParams();
  names.forEach(name => form.append('name', name));
  const state = await request('/api/games', form);
  saveStorage(gameKey, state.id);
  saveStorage(namesKey, JSON.stringify(names));
  return state;
}
function unavailable() {
  offline = true;
  byId('retry').hidden = false;
  showFeedback('The yard is offline. Start the local server, then reconnect.', 'error');
}
function openingMessage(state) {
  if (state.winner !== -1) return state.players[state.winner].name + ' collected every tail feather and won!';
  return 'Flip a tile to find the ' + symbols[state.track[state.target]].toLowerCase() + '.';
}
async function loadGame() {
  lockBoard(true);
  byId('retry').hidden = true;
  try {
    let state;
    const id = game?.id || readStorage(gameKey) || legacyGameId;
    if (id) {
      try { state = await request('/api/games/' + encodeURIComponent(id)); }
      catch (error) { if (error.status !== 404) throw error; }
    }
    if (!state) state = await createGame(rosterPreference());
    offline = false;
    renderState(state);
    showFeedback(openingMessage(state), state.winner === -1 ? 'ready' : 'win');
  } catch {
    unavailable();
  } finally {
    lockBoard(false);
  }
}

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function flipCard(slot) {
  if (busy || offline || !game || game.winner !== -1) return;
  lockBoard(true);
  const before = game;
  const button = cards[slot];
  let revealedArt;
  if (soundOn) prepareAudio();
  try {
    const form = new URLSearchParams({slot: String(slot), revision: String(before.revision)});
    const {game: next, reveal} = await request('/api/games/' + before.id + '/flip', form);
    const name = before.players[reveal.player].name;
    const picture = symbols[reveal.symbol].toLowerCase();
    revealedArt = button.querySelector('.card-front .sprite');
    setSymbol(revealedArt, reveal.symbol);
    button.classList.add('revealed', reveal.matched ? 'match' : 'miss');
    button.setAttribute('aria-label', 'Tile ' + (slot + 1) + ', ' + picture);
    let movement;
    if (reveal.matched) {
      const message = reveal.jumped
        ? name + ' jumped ' + reveal.jumped + (reveal.jumped === 1 ? ' chicken' : ' chickens')
          + (reveal.stolen ? ' and took ' + featherCount(reveal.stolen) + '!' : '!')
        : 'A match! ' + name + ' moves to the ' + picture + '.';
      showFeedback(message, reveal.jumped ? 'jump' : 'match');
      playTone(reveal.jumped ? 'jump' : 'match');
      movement = yard.move(before, next, reveal.player, renderFlock, index => renderEgg(next, index));
    } else {
      showFeedback('Tile ' + (slot + 1) + ' shows the ' + picture + '. Remember it for later!', 'miss');
      playTone('miss');
    }
    await Promise.all([movement, delay(reveal.matched ? 1150 : 1650)]);
    button.classList.remove('revealed');
    await delay(reducedMotion.matches ? 0 : 250);
    renderState(next);
    if (next.winner !== -1) {
      showFeedback(openingMessage(next), 'win');
      celebrate(next);
    } else {
      const nextPlayer = next.players[next.active].name;
      const target = symbols[next.track[next.target]].toLowerCase();
      const lead = reveal.matched ? nextPlayer + ' flips again. ' : nextPlayer + ' is up. ';
      showFeedback(lead + 'Find the ' + target + '.', reveal.matched ? 'match' : 'ready');
    }
  } catch {
    // The server might already have applied the move if the response was interrupted.
    await loadGame();
  } finally {
    button.classList.remove('match', 'miss', 'revealed');
    if (revealedArt) revealedArt.hidden = true;
    button.setAttribute('aria-label', 'Flip tile ' + (slot + 1));
    lockBoard(false);
  }
}

function prepareAudio() {
  try {
    const Audio = window.AudioContext || window.webkitAudioContext;
    if (!Audio) return;
    audioContext ||= new Audio();
    if (audioContext.state === 'suspended') audioContext.resume().catch(() => {});
  } catch { /* Sound is optional. */ }
}
function playTone(kind) {
  if (!soundOn || !audioContext || audioContext.state !== 'running') return;
  const notes = {match: [523, 659], miss: [349, 294], jump: [523, 659, 784], win: [523, 659, 784, 1047]};
  (notes[kind] || notes.match).forEach((frequency, i) => {
    const start = audioContext.currentTime + .1 * i;
    const oscillator = audioContext.createOscillator(), gain = audioContext.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(.001, start);
    gain.gain.exponentialRampToValueAtTime(.09, start + .012);
    gain.gain.exponentialRampToValueAtTime(.001, start + .19);
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start(start);
    oscillator.stop(start + .2);
  });
}
function soundButton() {
  const btn = byId('sound');
  const label = soundOn ? 'Turn sound off' : 'Turn sound on';
  btn.setAttribute('aria-label', label);
  btn.title = label;
  btn.setAttribute('aria-pressed', String(soundOn));
  btn.replaceChildren(icon(soundOn ? 'sound' : 'muted'));
}
function celebrate(state) {
  const player = state.players[state.winner];
  setHen(byId('winner-art'), player.id, player.feathers);
  byId('win-title').textContent = player.name + ' wins!';
  byId('winner-text').textContent = 'All ' + player.feathers.length + ' tail feathers collected on turn ' + state.turn + '.';
  const other = document.querySelector('dialog[open]');
  if (other) other.close();
  byId('win-modal').showModal();
  playTone('win');
  if (reducedMotion.matches) return;
  const shower = element('div', 'confetti');
  shower.setAttribute('aria-hidden', 'true');
  const palette = ['#edb43a', '#de775b', '#67a98e', '#bc95ca'];
  for (let i = 0; i < 38; i++) {
    const piece = element('span');
    piece.style.setProperty('--left', Math.random() * 100 + '%');
    piece.style.setProperty('--drift', Math.round(Math.random() * 130 - 65) + 'px');
    piece.style.setProperty('--delay', Math.random() * .75 + 's');
    piece.style.setProperty('--color', palette[i % palette.length]);
    shower.append(piece);
  }
  document.body.append(shower);
  setTimeout(() => shower.remove(), 3400);
}

function buildNameFields() {
  defaultNames.forEach((name, i) => {
    const field = element('label', 'name-field');
    field.dataset.color = i;
    const avatar = element('span', 'avatar');
    avatar.append(hen(i));
    const input = element('input');
    input.maxLength = 24;
    input.autocomplete = 'off';
    input.placeholder = name;
    input.setAttribute('aria-label', 'Player ' + (i + 1) + ' name (' + name + ')');
    field.append(avatar, input);
    byId('name-fields').append(field);
  });
}
function updateNameFields() {
  const count = Number(byId('setup-form').elements.count.value);
  Array.from(byId('name-fields').children).forEach((field, i) => { field.hidden = i >= count; });
}
function openSetup() {
  if (busy) return;
  const names = game ? game.players.map(p => p.name) : rosterPreference();
  byId('setup-form').elements.count.value = String(names.length);
  byId('name-fields').querySelectorAll('input').forEach((input, i) => { input.value = names[i] || defaultNames[i]; });
  byId('setup-error').hidden = true;
  updateNameFields();
  byId('setup-modal').showModal();
}
byId('setup-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  lockBoard(true);
  byId('setup-start').disabled = true;
  const count = Number(byId('setup-form').elements.count.value);
  const names = Array.from(byId('name-fields').querySelectorAll('input')).slice(0, count)
    .map((input, i) => input.value.trim() || defaultNames[i]);
  try {
    const state = await createGame(names);
    offline = false;
    byId('retry').hidden = true;
    renderState(state);
    showFeedback(openingMessage(state));
    byId('setup-modal').close();
  } catch (error) {
    byId('setup-error').textContent = error.status === 400
      ? 'Use 1 to 24 printable characters for each player name.'
      : 'Could not start the game. Check the local server and try again.';
    byId('setup-error').hidden = false;
  } finally {
    lockBoard(false);
    byId('setup-start').disabled = false;
  }
});
byId('new-game').addEventListener('click', openSetup);
byId('counts').addEventListener('change', updateNameFields);
byId('rules-open').addEventListener('click', () => byId('rules-modal').showModal());
byId('win-new').addEventListener('click', () => { byId('win-modal').close(); openSetup(); });
byId('retry').addEventListener('click', loadGame);
document.querySelectorAll('[data-close]').forEach(button =>
  button.addEventListener('click', () => button.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const box = dialog.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
}));
byId('sound').addEventListener('click', () => {
  soundOn = !soundOn;
  saveStorage(soundKey, soundOn ? 'yes' : 'no');
  if (soundOn) prepareAudio();
  soundButton();
});
function setPresentation(enabled) {
  document.body.classList.toggle('presenting', enabled);
  const btn = byId('fullscreen');
  const label = enabled ? 'Exit presentation mode' : 'Presentation mode';
  btn.title = enabled ? label + ' (Esc)' : label;
  btn.setAttribute('aria-label', label);
  btn.setAttribute('aria-pressed', String(enabled));
  btn.replaceChildren(icon(enabled ? 'collapse' : 'expand'));
  if (enabled) btn.append(element('span', '', 'Exit'));
}
async function leavePresentation() {
  setPresentation(false);
  if (document.fullscreenElement) {
    try { await document.exitFullscreen(); }
    catch { setPresentation(Boolean(document.fullscreenElement)); }
  }
}
byId('fullscreen').addEventListener('click', async () => {
  if (document.body.classList.contains('presenting')) {
    await leavePresentation();
    return;
  }
  setPresentation(true);
  // Embedded viewers can decline native fullscreen; the larger board still works there.
  if (document.fullscreenEnabled) {
    try { await document.documentElement.requestFullscreen(); } catch { /* Keep the in-page presentation. */ }
  }
});
document.addEventListener('fullscreenchange', () => setPresentation(Boolean(document.fullscreenElement)));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && document.body.classList.contains('presenting') && !document.querySelector('dialog[open]')) {
    leavePresentation();
  }
});

buildBoard();
buildNameFields();
for (let count = 0; count <= 4; count++) {
  const example = element('li');
  example.setAttribute('aria-label', featherCount(count));
  example.append(hen(0, [0, 1, 2, 3].slice(0, count)), element('b', '', String(count)));
  byId('tail-examples').append(example);
}
soundButton();
loadGame();
