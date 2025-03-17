const socket = new WebSocket(`ws://${window.location.host}/ws/game/`);
const map = document.getElementById("map"), miniMapCanvas = document.getElementById("mini-map"), miniCtx = miniMapCanvas.getContext("2d");
const MAP_WIDTH = 5000, MAP_HEIGHT = 5000;
let playerId = null, players = {}, npcs = {}, mapObjects = [];

socket.onopen = () => console.log("✅ Conectado WebSocket");
socket.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log("📩 Mensaje recibido:", data);
  switch (data.action) {
    case "initialize": playerId = data.player_id; players = data.players || {}; npcs = data.npcs || {}; mapObjects = Array.isArray(data.map_objects) ? data.map_objects : []; renderAll(); break;
    case "update_players": updatePlayers(data.players); break;
    case "update_npcs": updateNpcs(data.npcs); break;
    case "asteroid_removed": removeAsteroid(data.asteroid); break;
    case "asteroid_respawn": mapObjects.push(data.asteroid); renderObjects(); break;
    case "update_world": players = data.players || {}; npcs = data.npcs || {}; mapObjects = Array.isArray(data.map_objects) ? data.map_objects : []; renderAll(); break;
    default: console.warn("⚠ Acción no manejada:", data.action);
  }
};

function renderAll() { renderObjects(); renderNPCs(); updatePlayers(players); drawMiniMap(); }
function renderObjects() {
  map.innerHTML = "";
  if (!Array.isArray(mapObjects)) return;
  mapObjects.forEach(({ x, y }) => { let ast = document.createElement("div"); ast.classList.add("asteroid"); ast.style.transform = `translate(${x}px,${y}px)`; map.appendChild(ast); });
}

function renderNPCs() {
  Object.keys(npcs).forEach(id => { let npc = document.getElementById(id) || document.createElement("div"); if (!npc.id) { npc.id = id; npc.classList.add("npc"); map.appendChild(npc); } let { x, y } = npcs[id].position; npc.style.transform = `translate(${x}px,${y}px)`; });
}

function updatePlayers(pl) {
  players = pl || {}; Object.keys(players).forEach(id => {
    let p = document.getElementById(id) || document.createElement("div");
    if (!p.id) { p.id = id; p.classList.add("player"); p.style.backgroundColor = players[id].color; map.appendChild(p); }
    p.style.transform = `translate(${players[id].position.x}px,${players[id].position.y}px)`;
  });
  updateCamera(); drawMiniMap();
}

function removeAsteroid(ast) {
  if (!Array.isArray(mapObjects)) return;
  mapObjects = mapObjects.filter(a => a.x !== ast.x || a.y !== ast.y);
  renderObjects(); drawMiniMap();
}

function updateCamera() {
  if (!playerId || !players[playerId]) return;
  let { x, y } = players[playerId].position;
  map.style.transform = `translate(${-x + window.innerWidth / 2}px,${-y + window.innerHeight / 2}px)`;
}

function drawMiniMap() {
  let mw = 200, mh = mw / (MAP_WIDTH / MAP_HEIGHT);
  miniMapCanvas.width = mw; miniMapCanvas.height = mh;
  miniCtx.clearRect(0, 0, mw, mh);
  miniCtx.fillStyle = "black"; miniCtx.fillRect(0, 0, mw, mh);
  let sX = mw / MAP_WIDTH, sY = mh / MAP_HEIGHT;
  mapObjects.forEach(({ x, y }) => { miniCtx.fillStyle = "gray"; miniCtx.fillRect(x * sX, y * sY, 3, 3); });
  Object.values(players).forEach(({ position, color }) => { miniCtx.fillStyle = color; miniCtx.fillRect(position.x * sX, position.y * sY, 5, 5); });
  Object.values(npcs).forEach(({ position }) => { miniCtx.fillStyle = "red"; miniCtx.fillRect(position.x * sX, position.y * sY, 4, 4); });
}

document.addEventListener("keydown", ({ key }) => {
  if (!playerId || !players[playerId]) return;
  let { x, y } = players[playerId].position, speed = 10;
  if (key === "ArrowUp" && y - speed >= 0) y -= speed;
  else if (key === "ArrowDown" && y + speed <= MAP_HEIGHT) y += speed;
  else if (key === "ArrowLeft" && x - speed >= 0) x -= speed;
  else if (key === "ArrowRight" && x + speed <= MAP_WIDTH) x += speed;
  else if (key === " ") { socket.send(JSON.stringify({ action: "mine" })); return; }
  socket.send(JSON.stringify({ action: "move", x, y }));
});
