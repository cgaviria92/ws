const socketURL = `ws://${window.location.host}/ws/game/`;
let socket = null, reconnectInterval = null, playerId = null, players = {}, npcs = {}, mapObjects = [];

function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;
  socket = new WebSocket(socketURL);
  socket.onopen = () => { console.log("✅ Conectado WebSocket"); if (reconnectInterval) clearInterval(reconnectInterval); };
  socket.onclose = () => { console.warn("⚠ WebSocket cerrado. Intentando reconectar..."); reconnectInterval = setInterval(connectWebSocket, 3000); };
  socket.onerror = (err) => console.error("❌ Error WebSocket:", err);
  socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log("📩 Mensaje:", data);
    switch (data.action) {
      case "initialize":
        if (!playerId) playerId = data.player_id;
        players = data.players || {};
        npcs = data.npcs || {};
        mapObjects = Array.isArray(data.map_objects) ? data.map_objects : [];
        renderAll();
        break;
      case "update_players": updatePlayers(data.players); break;
      case "update_npcs": updateNpcs(data.npcs); break; // <--- En lugar de re-dibujar todo, llama updateNpcs
      case "asteroid_removed": removeAsteroid(data.asteroid); break;
      case "asteroid_respawn": mapObjects.push(data.asteroid); renderObjects(); break;
      case "update_world":
        players = data.players || {};
        npcs = data.npcs || {};
        mapObjects = Array.isArray(data.map_objects) ? data.map_objects : [];
        renderAll();
        break;
      default: console.warn("⚠ Acción no manejada:", data.action);
    }
  };
}
connectWebSocket();

// DOM
const map = document.getElementById("map"),
  miniMapCanvas = document.getElementById("mini-map"),
  miniCtx = miniMapCanvas.getContext("2d");
const mineButton = document.createElement("button");
mineButton.innerText = "⛏️ Minar";
mineButton.style = "position:fixed;bottom:20px;left:50%;transform:translateX(-50%);padding:10px 20px;background:gold;border:none;border-radius:5px;cursor:pointer;display:none;";
document.body.appendChild(mineButton);
const shootButton = document.createElement("button");
shootButton.innerText = "🔫 Disparar";
shootButton.style = "position:fixed;bottom:60px;left:50%;transform:translateX(-50%);padding:10px 20px;background:red;border:none;border-radius:5px;cursor:pointer;display:none;";
document.body.appendChild(shootButton);

const MAP_WIDTH = 5000, MAP_HEIGHT = 5000;

function renderAll() {
  renderObjects();
  renderNPCs();
  updatePlayers(players);
  drawMiniMap();
}


// Asteroides
function renderObjects() {
  map.innerHTML = "";
  if (!Array.isArray(mapObjects)) return;
  mapObjects.forEach(({ x, y }) => {
    let ast = document.createElement("div");
    ast.classList.add("asteroid");
    ast.style.transform = `translate(${x}px,${y}px)`;
    ast.dataset.x = x; ast.dataset.y = y;
    map.appendChild(ast);
  });
}

// NPCs con barra HP y nivel
function renderNPCs() {
  Object.keys(npcs).forEach(id => {
    let npc = document.getElementById(id) || document.createElement("div");
    if (!npc.id) { npc.id = id; npc.classList.add("npc"); map.appendChild(npc); }
    let { x, y } = npcs[id].position, health = npcs[id].health || 50, level = npcs[id].level || 1;
    npc.style.transform = `translate(${x}px,${y}px)`;
    // Barra verde y texto "LvX"
    npc.innerHTML = `
      <div style="position:absolute;bottom:-10px;left:-15px;width:60px;height:6px;background:gray;">
        <div style="width:${health}px;height:6px;background:lime;"></div>
      </div>
      <div style="position:absolute;bottom:-25px;left:-10px;color:white;font-size:10px;">Lv${level}</div>
    `;
  });
}

// NUEVO: re-render NPCs
function updateNpcs(newNpcs) {
  npcs = newNpcs || {};
  renderNPCs(); drawMiniMap(); highlightAttackableNpcs();
}

// Jugadores con HP
function updatePlayers(pl) {
  players = pl || {};
  Object.keys(players).forEach(id => {
    let p = document.getElementById(id) || document.createElement("div");
    if (!p.id) {
      p.id = id; p.classList.add("player");
      p.style.backgroundColor = players[id].color;
      map.appendChild(p);
    }
    let { x, y } = players[id].position, health = players[id].health || 100;
    p.style.transform = `translate(${x}px,${y}px)`;
    p.innerHTML = `
      <div style="position:absolute;bottom:-10px;left:-15px;width:60px;height:6px;background:gray;">
        <div style="width:${health}px;height:6px;background:lime;"></div>
      </div>
    `;
  });
  updateCamera(); drawMiniMap();
  highlightMineableAsteroids(); highlightAttackableNpcs();
}

// Quitar asteroide
function removeAsteroid(ast) {
  if (!Array.isArray(mapObjects)) return;
  mapObjects = mapObjects.filter(a => a.x !== ast.x || a.y !== ast.y);
  renderObjects(); drawMiniMap();
}

// Camara
function updateCamera() {
  if (!playerId || !players[playerId]) return;
  let { x, y } = players[playerId].position;
  map.style.transform = `translate(${-x + window.innerWidth / 2}px,${-y + window.innerHeight / 2}px)`;
}

// Minimapa
function drawMiniMap() {
  let mw = 200, mh = mw / (MAP_WIDTH / MAP_HEIGHT);
  miniMapCanvas.width = mw; miniMapCanvas.height = mh;
  miniCtx.clearRect(0, 0, mw, mh);
  miniCtx.fillStyle = "black"; miniCtx.fillRect(0, 0, mw, mh);
  let sX = mw / MAP_WIDTH, sY = mh / MAP_HEIGHT;
  mapObjects.forEach(({ x, y }) => {
    miniCtx.fillStyle = "gray"; miniCtx.fillRect(x * sX, y * sY, 3, 3);
  });
  Object.values(players).forEach(({ position, color }) => {
    miniCtx.fillStyle = color;
    miniCtx.fillRect(position.x * sX, position.y * sY, 5, 5);
  });
  Object.values(npcs).forEach(({ position }) => {
    miniCtx.fillStyle = "red";
    miniCtx.fillRect(position.x * sX, position.y * sY, 4, 4);
  });
}

// Asteroides minables
function highlightMineableAsteroids() {
  let found = false;
  document.querySelectorAll(".asteroid").forEach(ast => {
    let ax = parseInt(ast.dataset.x), ay = parseInt(ast.dataset.y);
    let px = players[playerId].position.x, py = players[playerId].position.y;
    let dist = Math.sqrt((ax - px) ** 2 + (ay - py) ** 2);
    if (dist < 100) { ast.style.border = "2px solid yellow"; found = true; }
    else ast.style.border = "none";
  });
  if (found && socket.readyState === WebSocket.OPEN) mineButton.style.display = "block"; else mineButton.style.display = "none";
}

// NPCs cercanos->Disparar
function highlightAttackableNpcs() {
  let foundNpc = false;
  Object.keys(npcs).forEach(id => {
    let { x, y } = npcs[id].position;
    let px = players[playerId].position.x, py = players[playerId].position.y;
    let dist = Math.sqrt((x - px) ** 2 + (y - py) ** 2);
    if (dist < 100) foundNpc = true;
  });
  if (foundNpc && socket.readyState === WebSocket.OPEN) shootButton.style.display = "block"; else shootButton.style.display = "none";
}

// Movement
function enablePlayerMovement() { document.addEventListener("keydown", handlePlayerMovement); }
function disablePlayerMovement() { document.removeEventListener("keydown", handlePlayerMovement); }
function handlePlayerMovement(e) {
  if (!playerId || !players[playerId] || socket.readyState !== WebSocket.OPEN) return;
  let { x, y } = players[playerId].position, speed = 10;
  if (e.key === "ArrowUp" && y - speed >= 0) y -= speed;
  else if (e.key === "ArrowDown" && y + speed <= MAP_HEIGHT) y += speed;
  else if (e.key === "ArrowLeft" && x - speed >= 0) x -= speed;
  else if (e.key === "ArrowRight" && x + speed <= MAP_WIDTH) x += speed;
  else return;
  socket.send(JSON.stringify({ action: "move", x, y }));
}

// KeyDown
document.addEventListener("keydown", ({ key }) => {
  if (!playerId || !players[playerId] || socket.readyState !== WebSocket.OPEN) return;
  let { x, y } = players[playerId].position, speed = 10;
  if (key === "ArrowUp" && y - speed >= 0) y -= speed;
  else if (key === "ArrowDown" && y + speed <= MAP_HEIGHT) y += speed;
  else if (key === "ArrowLeft" && x - speed >= 0) x -= speed;
  else if (key === "ArrowRight" && x + speed <= MAP_WIDTH) x += speed;
  else if (key === " ") { socket.send(JSON.stringify({ action: "mine" })); return; }
  socket.send(JSON.stringify({ action: "move", x, y }));
});

// Botón Minar
mineButton.addEventListener("click", () => {
  if (socket.readyState !== WebSocket.OPEN) {
    console.warn("⚠ No se pudo enviar: WebSocket no está OPEN.");
    return;
  }
  mineButton.style.display = "none";
  let closestAsteroid = null, bestDist = Infinity;
  document.querySelectorAll(".asteroid").forEach(ast => {
    let ax = parseInt(ast.dataset.x), ay = parseInt(ast.dataset.y);
    let px = players[playerId].position.x, py = players[playerId].position.y;
    let dist = Math.sqrt((ax - px) ** 2 + (ay - py) ** 2);
    if (dist < 100 && dist < bestDist) {
      bestDist = dist; closestAsteroid = ast;
    }
  });
  if (closestAsteroid) {
    mapObjects = mapObjects.filter(a => !(a.x == closestAsteroid.dataset.x && a.y == closestAsteroid.dataset.y));
    closestAsteroid.remove();
    drawMiniMap();
  }
  socket.send(JSON.stringify({ action: "mine" }));
  enablePlayerMovement();
});

// Botón Disparar
shootButton.addEventListener("click", () => {
  if (socket.readyState !== WebSocket.OPEN) {
    console.warn("⚠ No se pudo enviar: WebSocket no está OPEN.");
    return;
  }
  shootButton.style.display = "none";
  socket.send(JSON.stringify({ action: "shoot" }));
});
