document.onkeydown = updateKey;
document.onkeyup = resetKey;

var server_port = 65432;
var server_addr = '127.0.0.1';

var telemetryIntervalId = null;

const KEY_TO_CMD = {
  KeyW: 'forward',
  KeyS: 'backward',
  KeyA: 'left',
  KeyD: 'right',
};

const KEY_TO_ARROW = {
  KeyW: 'upArrow',
  KeyS: 'downArrow',
  KeyA: 'leftArrow',
  KeyD: 'rightArrow',
};

const pressedMovement = new Set();

function baseUrl() {
  return `http://${server_addr}:${server_port}`;
}

function applyTelemetry(data) {
  if (!data) return;
  if (data.direction !== undefined) {
    document.getElementById('direction').textContent = data.direction;
  }
  if (data.speed !== undefined) {
    document.getElementById('speed').textContent = Number(data.speed).toFixed(1);
  }
  document.getElementById('distance').textContent = '—';
  if (data.temperature !== undefined) {
    document.getElementById('temperature').textContent = Number(data.temperature).toFixed(1);
  }
  if (data.battery_percentage !== undefined) {
    document.getElementById('battery').textContent = data.battery_percentage + '%';
  }
}

function refreshArrowColors() {
  for (const code of Object.keys(KEY_TO_ARROW)) {
    const arrowId = KEY_TO_ARROW[code];
    document.getElementById(arrowId).style.color = pressedMovement.has(code) ? 'green' : 'grey';
  }
}

async function postCommand(cmd) {
  try {
    const res = await fetch(`${baseUrl()}/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd }),
    });
    const body = await res.json().catch(() => ({}));
    if (body.telemetry) {
      applyTelemetry(body.telemetry);
    }
    if (!res.ok) {
      document.getElementById('bluetooth').textContent = body.message || `${res.status} ${res.statusText}`;
    } else {
      document.getElementById('bluetooth').textContent = 'ok';
    }
  } catch (err) {
    console.error(err);
    document.getElementById('bluetooth').textContent = err.message || String(err);
  }
}

async function fetchTelemetry() {
  try {
    const res = await fetch(`${baseUrl()}/telemetry`);
    const data = await res.json();
    applyTelemetry(data);
  } catch (err) {
    console.error(err);
    document.getElementById('bluetooth').textContent = err.message || String(err);
  }
}

function startTelemetryPolling() {
  if (telemetryIntervalId !== null) return;
  fetchTelemetry();
  telemetryIntervalId = setInterval(fetchTelemetry, 400);
}

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('upButton').addEventListener('click', function () {
    showButtonPressed('upButton', 'upArrow');
    postCommand('forward');
  });
  document.getElementById('downButton').addEventListener('click', function () {
    showButtonPressed('downButton', 'downArrow');
    postCommand('backward');
  });
  document.getElementById('leftButton').addEventListener('click', function () {
    showButtonPressed('leftButton', 'leftArrow');
    postCommand('left');
  });
  document.getElementById('rightButton').addEventListener('click', function () {
    showButtonPressed('rightButton', 'rightArrow');
    postCommand('right');
  });
  startTelemetryPolling();
});

function updateKey(e) {
  e = e || window.event;
  const cmd = KEY_TO_CMD[e.code];
  if (!cmd) return;
  pressedMovement.add(e.code);
  refreshArrowColors();
  postCommand(cmd);
}

function resetKey(e) {
  e = e || window.event;
  const cmd = KEY_TO_CMD[e.code];
  if (!cmd) return;
  pressedMovement.delete(e.code);
  refreshArrowColors();
  if (pressedMovement.size === 0) {
    postCommand('stop');
  } else {
    const codes = Array.from(pressedMovement);
    const last = codes[codes.length - 1];
    postCommand(KEY_TO_CMD[last]);
  }
}

function showButtonPressed(buttonId, arrowId) {
  document.getElementById(arrowId).style.color = 'green';
  setTimeout(() => {
    document.getElementById(arrowId).style.color = 'grey';
  }, 200);
}

function update_data() {
  const ip = document.getElementById('message').value.trim();
  if (ip) {
    server_addr = ip;
  }
  startTelemetryPolling();
  fetchTelemetry();
}
