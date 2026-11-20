const {test} = require('node:test');
const assert = require('node:assert/strict');
const {Yard, plan, footwork, facing} = require('../../../web/yard-motion.js');

function board(placements) {
  return {id: 'test-yard', active: 0, winner: -1, track: Array(24).fill(0),
    players: placements.map(([position, feathers], id) => ({id, position, feathers}))};
}

const before = board([[23,[0]], [0,[3,1]], [1,[]], [2,[2]]]);
const after = board([[3,[0,3,1,2]], [0,[]], [1,[]], [2,[]]]);

test('a running chicken visits the next egg and a miss leaves everyone still', () => {
  const a = board([[23,[0]],[8,[1]]]), b = board([[0,[0]],[8,[1]]]);
  assert.equal(plan(a,a,0), null);
  const move = plan(a,b,0);
  assert.deepEqual(move.path, [23,0]);
  assert.deepEqual(move.transfers, []);
  assert.equal(move.jumping, false);
  assert.equal(footwork(move,0).along, 0);
  const during = [300,390,470].map(t => footwork(move,t));
  assert.ok(during.every(p => p.along > 0 && p.along < 1 && p.lift === 0));
  assert.ok(new Set(during.map(p => p.frame)).size >= 2);
  assert.equal(footwork(move,move.duration).along, 1);
});

test('a chain crossing egg zero keeps the donor and original colour of each quill', () => {
  const move = plan(before,after,0);
  assert.deepEqual(move.path, [23,0,1,2,3]);
  assert.deepEqual(move.transfers, [{from:1,color:3},{from:1,color:1},{from:3,color:2}]);
  const midpoint = footwork(move,move.landing - move.airTime/2);
  assert.ok(midpoint.lift > .99 && midpoint.along > 1 && midpoint.along < 3);
  assert.equal(footwork(move,move.landing).lift, 0);
  assert.equal(footwork(move,move.landing).along, 4);
  assert.equal(facing([90,25],[93,36],1.65), 'front');
  assert.equal(facing([7,36],[10,23],1.65), 'back');
  assert.equal(facing([50,15],[61,15],1.65), 'right');
  assert.equal(facing([50,87],[39,87],1.65), 'left');
});

test('jumping a bare-tailed chicken still plays the arc without creating a feather', () => {
  const a = board([[5,[0]],[6,[]],[20,[1,2]]]), b = board([[7,[0]],[6,[]],[20,[1,2]]]);
  const move = plan(a,b,0);
  assert.ok(move.jumping);
  assert.deepEqual(move.transfers, []);
});

// Advance the real animation one frame at a time. No HTTP game or user session is involved.
test('quills leave on takeoff, attach individually on arrival, and settle on visibility changes', async t => {
  class Element {
    children = [];
    dataset = {};
    style = {setProperty(key,value) { this[key] = value; }};
    offsetWidth = 80;
    get firstChild() { return this.children[0]; }
    append(node) { node.parent = this; this.children.push(node); }
    replaceChildren(...nodes) { this.children = []; nodes.forEach(node => this.append(node)); }
    remove() { this.parent.children = this.parent.children.filter(x => x !== this); }
  }
  const doc = Object.assign(new EventTarget(), {hidden:false, createElement:() => new Element()});
  const pref = Object.assign(new EventTarget(), {matches:false});
  let tick;
  for (const [key,value] of Object.entries({document:doc, ResizeObserver:class { observe() {} },
    requestAnimationFrame:fn => { tick = fn; return 1; }, cancelAnimationFrame:() => {}})) {
    const old = Object.getOwnPropertyDescriptor(globalThis,key);
    Object.defineProperty(globalThis,key,{value,configurable:true});
    t.after(() => old ? Object.defineProperty(globalThis,key,old) : delete globalThis[key]);
  }
  const yard = new Yard({clientWidth:900,clientHeight:550}, new Element(),
    Array.from({length:24},(_,i) => [10+i*3,30+i]), pref);
  const move = plan(before,after,0);
  let latest;
  const record = state => { latest = state.players.map(p => [...p.feathers]); };
  const spaces = [];
  const updateEgg = i => spaces.push(i);
  yard.sync(before);
  const started = performance.now();
  const playing = yard.move(before,after,0,record,updateEgg);
  tick(started + move.landing - move.airTime/2);
  assert.deepEqual(spaces, [23]);
  tick(started + move.landing + 10);
  assert.deepEqual(spaces, [23,3]);
  assert.equal(latest, undefined);
  tick(started + move.transferStart + 20);
  assert.deepEqual(latest, [[0],[1],[],[2]]);
  assert.equal(yard.layer.children.filter(n => n.className === 'flying-quill' && !n.hidden).length, 1);
  tick(started + move.transferStart + 715);
  assert.deepEqual(latest, [[0,3],[],[],[]]);
  doc.hidden = true;
  doc.dispatchEvent(new Event('visibilitychange'));
  await playing;
  assert.deepEqual(latest, after.players.map(p => p.feathers));
  assert.equal(yard.layer.children.length, 4);
  assert.deepEqual(before.players[1].feathers, [3,1]);
  doc.hidden = false;
  pref.matches = true;
  yard.sync(before);
  await yard.move(before,after,0,record,updateEgg);
  assert.deepEqual(spaces, [23,3,23,3]);
  assert.deepEqual(latest, after.players.map(p => p.feathers));
  assert.equal(yard.layer.children.length, 4);
});
