'use strict';

const YardMotion = (() => {
  const pose = {rest: 0, breathe: 1, look: 2, lean: 3, peck: 4, stride: 5,
    pass: 6, strideBack: 7, crouch: 8, wingUp: 9, wingDown: 10, land: 11};
  const steps = [pose.stride, pose.pass, pose.strideBack, pose.pass];
  const readTime = 220, runTime = 580, crouchTime = 125, settleTime = 210;
  const featherTime = 690, stagger = 170;
  const clamp = value => Math.max(0, Math.min(1, value));
  const mix = (a, b, t) => a + (b - a) * t;
  const smooth = t => t * t * (3 - 2 * t);

  function plan(before, after, actor) {
    const player = before.players[actor], next = after.players[actor];
    const count = before.track.length;
    const distance = (next.position - player.position + count) % count;
    if (!distance) return null;
    const path = Array.from({length: distance + 1}, (_, i) => (player.position + i) % count);
    const transfers = [];
    for (const space of path.slice(1, -1)) {
      const donor = before.players.find(p => p.position === space);
      if (!donor) continue;
      for (const color of donor.feathers) {
        if (next.feathers.includes(color) && !after.players[donor.id].feathers.includes(color)) {
          transfers.push({from: donor.id, color});
        }
      }
    }
    const jumping = distance > 1;
    const airTime = jumping ? 540 + 145 * (distance - 1) : 0;
    const landing = readTime + (jumping ? 180 + crouchTime + airTime : runTime);
    const transferStart = landing + settleTime;
    const duration = transfers.length ? transferStart + featherTime + (transfers.length - 1) * stagger : landing + 345;
    return {actor, path, distance, jumping, airTime, landing, transferStart, transfers, duration};
  }

  function footwork(move, elapsed) {
    const t = elapsed - readTime;
    if (t < 0) return {along: 0, lift: 0, frame: pose.look};
    if (elapsed >= move.landing) {
      const onGround = elapsed - move.landing;
      return {along: move.distance, lift: 0, frame: onGround < 105 ? pose.land : pose.rest};
    }
    if (!move.jumping) {
      const progress = clamp(t / runTime);
      return {along: smooth(progress), lift: 0, frame: steps[Math.floor(t / 82) % 4]};
    }
    if (t < 180) return {along: .20 * t / 180, lift: 0, frame: steps[Math.floor(t / 60) % 4]};
    if (t < 180 + crouchTime) return {along: .20, lift: 0, frame: pose.crouch};
    const air = clamp((t - 180 - crouchTime) / move.airTime);
    return {along: mix(.20, move.distance, air), lift: 4 * air * (1 - air),
      frame: Math.floor(air * 5) % 2 === 0 ? pose.wingUp : pose.wingDown};
  }

  function facing(a, b, aspect) {
    const dx = (b[0] - a[0]) * aspect, dy = b[1] - a[1];
    if (Math.abs(dy) > Math.abs(dx) * .93) return dy > 0 ? 'front' : 'back';
    return dx < 0 ? 'left' : 'right';
  }

  function animate(duration, preference, draw) {
    return new Promise(resolve => {
      const start = performance.now();
      let raf;
      function finish() {
        cancelAnimationFrame(raf);
        document.removeEventListener('visibilitychange', onChange);
        preference.removeEventListener('change', onChange);
        draw(duration);
        resolve();
      }
      function onChange() {
        if (document.hidden || preference.matches) finish();
      }
      function tick(time) {
        const elapsed = time - start;
        if (elapsed >= duration) { finish(); return; }
        draw(elapsed);
        raf = requestAnimationFrame(tick);
      }
      if (document.hidden || preference.matches) { finish(); return; }
      document.addEventListener('visibilitychange', onChange);
      preference.addEventListener('change', onChange);
      draw(0);
      raf = requestAnimationFrame(tick);
    });
  }

  class Yard {
    constructor(field, layer, spaces, preference) {
      this.field = field;
      this.layer = layer;
      this.spaces = spaces;
      this.preference = preference;
      this.birds = [];
      this.idle = false;
      this.moving = false;
      this.beat = 0;
      this.observer = new ResizeObserver(() => {
        if (this.state && !this.moving) this.placeFlock(this.state);
      });
      this.observer.observe(field);
      document.addEventListener('visibilitychange', () => this.scheduleIdle());
      preference.addEventListener('change', () => this.scheduleIdle());
    }

    sync(state) {
      if (this.state?.id !== state.id) {
        this.birds = state.players.map(() => {
          const bird = document.createElement('div');
          bird.className = 'pawn';
          bird.append(document.createElement('span'));
          bird.firstChild.className = 'bird';
          return bird;
        });
        this.layer.replaceChildren(...this.birds);
      }
      this.state = state;
      this.placeFlock(state);
    }

    placeFlock(state) {
      const aspect = this.field.clientWidth / Math.max(1, this.field.clientHeight);
      for (const p of state.players) {
        const current = this.spaces[p.position];
        const next = this.spaces[(p.position + 1) % this.spaces.length];
        this.place(p.id, current, facing(current, next, aspect), pose.rest);
        this.tail(p.id, p.feathers);
      }
    }

    tail(id, feathers) {
      const mask = feathers.reduce((bits, color) => bits | (1 << color), 0);
      this.birds[id].style.setProperty('--tail', (100 * mask / 15) + '%');
    }

    frame(id, index) {
      this.birds[id].style.setProperty('--frame', (100 * (id * 12 + index) / 47) + '%');
    }

    place(id, [x, y], direction, index, lift = 0) {
      const bird = this.birds[id];
      bird.style.left = x + '%';
      bird.style.top = y + '%';
      bird.style.zIndex = Math.round(y) + (lift > 0 ? 110 : 0);
      bird.style.setProperty('--lift', -Math.round(lift) + 'px');
      bird.dataset.facing = direction;
      this.frame(id, index);
    }

    setIdle(enabled) {
      this.idle = enabled;
      this.beat = 0;
      this.scheduleIdle();
    }

    scheduleIdle() {
      clearTimeout(this.timer);
      if (!this.state || this.moving) return;
      const id = this.state.active;
      this.frame(id, pose.rest);
      if (!this.idle || this.preference.matches || document.hidden || this.state.winner !== -1) return;
      const sequence = [[pose.rest,1550],[pose.breathe,280],[pose.rest,1600],[pose.look,410],
        [pose.rest,1300],[pose.lean,150],[pose.peck,170],[pose.lean,150],[pose.rest,1250],
        [pose.breathe,300],[pose.rest,1800],[pose.look,350]];
      const [index, duration] = sequence[this.beat++ % sequence.length];
      if (!document.querySelector('dialog[open]')) this.frame(id, index);
      this.timer = setTimeout(() => this.scheduleIdle(), duration);
    }

    effect(cssClass) {
      const item = document.createElement('span');
      item.className = cssClass;
      item.hidden = true;
      this.layer.append(item);
      return item;
    }

    async move(before, after, actor, updateFlock, updateEgg) {
      const move = plan(before, after, actor);
      if (!move) return;
      this.moving = true;
      const dust = this.effect('landing-dust');
      const feathers = before.players.map(p => [...p.feathers]);
      const flights = move.transfers.map(({from, color}) => {
        const item = this.effect('flying-quill');
        item.style.setProperty('--color-x', color * 100 / 3 + '%');
        return {from, color, item, departed: false, arrived: false};
      });
      const destination = this.spaces[move.path.at(-1)];
      let leftEgg = false, landed = false;
      try {
        await animate(move.duration, this.preference, elapsed => {
          const width = this.field.clientWidth, height = this.field.clientHeight;
          const aspect = width / Math.max(1,height);
          const size = this.birds[actor].offsetWidth;
          const {along, lift, frame} = footwork(move, elapsed);
          if (!leftEgg && along > .20) {
            leftEgg = true;
            updateEgg(move.path[0]);
          }
          if (!landed && elapsed >= move.landing) {
            landed = true;
            updateEgg(move.path.at(-1));
          }
          const step = Math.min(Math.floor(along), move.distance - 1);
          const a = this.spaces[move.path[step]], b = this.spaces[move.path[step + 1]];
          const point = [mix(a[0], b[0], along - step), mix(a[1], b[1], along - step)];
          const endDirection = facing(destination, this.spaces[(move.path.at(-1) + 1) % this.spaces.length], aspect);
          const direction = along >= move.distance ? endDirection : facing(a, b, aspect);
          const clearance = Math.max(0, point[1] * height / 100 - size * .72 - 2);
          this.place(actor, point, direction, frame, lift * Math.min(size * .76, clearance));
          const groundTime = elapsed - move.landing;
          dust.hidden = !(groundTime >= 0 && groundTime < 345);
          if (!dust.hidden) {
            dust.style.left = destination[0] + '%';
            dust.style.top = destination[1] + '%';
            dust.style.setProperty('--dust-x', Math.min(4, Math.floor(groundTime / 69)) * 25 + '%');
          }
          let changed = false;
          const anchor = (p, dir) => [
            p[0]*width/100 + (dir === 'left' ? .30 : dir === 'right' ? -.30 : -.08)*size,
            p[1]*height/100 - size*(dir === 'left' || dir === 'right' ? .34 : .50)
          ];
          for (const [i, flight] of flights.entries()) {
            const t = (elapsed - move.transferStart - i*stagger) / featherTime;
            if (t < 0 || flight.arrived) continue;
            if (!flight.departed) {
              flight.departed = true;
              feathers[flight.from] = feathers[flight.from].filter(f => f !== flight.color);
              this.tail(flight.from, feathers[flight.from]);
              changed = true;
            }
            if (t >= 1) {
              flight.arrived = true;
              flight.item.hidden = true;
              feathers[actor].push(flight.color);
              this.tail(actor, feathers[actor]);
              changed = true;
              continue;
            }
            const donor = before.players[flight.from].position;
            const start = this.spaces[donor], ahead = this.spaces[(donor+1) % this.spaces.length];
            const from = anchor(start, facing(start, ahead, aspect)), to = anchor(destination, endDirection);
            const u = smooth(t), arc = 4*t*(1-t);
            const room = Math.max(3, Math.min(from[1], to[1]) - size*.19);
            flight.item.hidden = false;
            flight.item.style.left = (mix(from[0],to[0],u) + Math.sin(t*2*Math.PI)*size*.06) + 'px';
            flight.item.style.top = (mix(from[1],to[1],u) - arc*Math.min(size*.72,room)) + 'px';
            flight.item.style.setProperty('--angle', Math.round(14*Math.sin(t*3*Math.PI) - 30 + t*70) + 'deg');
          }
          if (changed) updateFlock({...before, players: before.players.map(p => ({...p, feathers: feathers[p.id]}))});
        });
      } finally {
        dust.remove();
        flights.forEach(f => f.item.remove());
        this.moving = false;
        this.sync(after);
        updateFlock(after);
      }
    }
  }
  return {Yard, plan, footwork, facing};
})();

if (typeof module !== 'undefined' && module.exports) module.exports = YardMotion;
