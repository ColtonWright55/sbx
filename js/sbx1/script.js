const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

const massInput = document.getElementById('mass');
const stiffnessInput = document.getElementById('stiffness');
const dampingInput = document.getElementById('damping');
const lengthInput = document.getElementById('length');

const posOut = document.getElementById('posOut');
const velOut = document.getElementById('velOut');
const timeOut = document.getElementById('timeOut');

const anchor = { x: canvas.width / 2, y: 30 };

// state: x = displacement (px) from rest length, v = velocity (px/s)
let x = 100;
let v = 0;
let t = 0;
let running = false;
let lastFrame = null;

function stepPhysics(dt) {
  const m = parseFloat(massInput.value) || 1;
  const k = parseFloat(stiffnessInput.value) || 0;
  const c = parseFloat(dampingInput.value) || 0;

  // sub-step for stability
  const subSteps = 8;
  const h = dt / subSteps;
  for (let i = 0; i < subSteps; i++) {
    const a = (-k * x - c * v) / m;
    v += a * h;
    x += v * h;
  }
  t += dt;
}

function draw() {
  const restLength = parseFloat(lengthInput.value) || 150;
  const massY = anchor.y + restLength + x;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // spring (zigzag)
  ctx.strokeStyle = '#6cf';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(anchor.x, anchor.y);
  const coils = 12;
  const segLen = (massY - anchor.y) / coils;
  for (let i = 1; i < coils; i++) {
    const dir = i % 2 === 0 ? 1 : -1;
    ctx.lineTo(anchor.x + dir * 15, anchor.y + i * segLen);
  }
  ctx.lineTo(anchor.x, massY);
  ctx.stroke();

  // anchor
  ctx.fillStyle = '#eee';
  ctx.fillRect(anchor.x - 20, anchor.y - 6, 40, 6);

  // mass
  ctx.beginPath();
  ctx.arc(anchor.x, massY, 18, 0, Math.PI * 2);
  ctx.fillStyle = '#f66';
  ctx.fill();
  ctx.strokeStyle = '#900';
  ctx.stroke();

  posOut.textContent = x.toFixed(2);
  velOut.textContent = v.toFixed(2);
  timeOut.textContent = t.toFixed(2);
}

function loop(now) {
  if (!running) return;
  if (lastFrame === null) lastFrame = now;
  const dt = Math.min((now - lastFrame) / 1000, 0.05);
  lastFrame = now;

  stepPhysics(dt);
  draw();

  requestAnimationFrame(loop);
}

document.getElementById('startBtn').addEventListener('click', () => {
  if (running) return;
  running = true;
  lastFrame = null;
  requestAnimationFrame(loop);
});

document.getElementById('stopBtn').addEventListener('click', () => {
  running = false;
});

document.getElementById('resetBtn').addEventListener('click', () => {
  running = false;
  x = 100;
  v = 0;
  t = 0;
  draw();
});

draw();
