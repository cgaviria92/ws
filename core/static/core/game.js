const socket = new WebSocket(`ws://${window.location.host}/ws/game/`);
const map = document.getElementById("map");
const miniMapCanvas = document.getElementById("mini-map");
const miniCtx = miniMapCanvas.getContext("2d");

const MAP_WIDTH = 5000, MAP_HEIGHT = 5000;
let playerId = null;
let players = {}, npcs = {}, mapObjects = {};

socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.action === "initialize") {
        playerId = data.player_id;
        mapObjects = data.map;
        npcs = data.npcs;
        renderObjects();
        renderNPCs();
        updatePlayers(data.players);
        drawMiniMap();
    } else if (data.action === "update_world") {
        updatePlayers(data.players);
        updateNPCs(data.npcs);
    }
};

function renderObjects() {
    map.innerHTML = "";
    mapObjects.forEach(({ x, y }) => {
        const asteroid = document.createElement("div");
        asteroid.classList.add("asteroid");
        asteroid.style.transform = `translate(${x}px, ${y}px)`;
        map.appendChild(asteroid);
    });
}

function renderNPCs() {
    Object.keys(npcs).forEach(id => {
        let npc = document.createElement("div");
        npc.id = id;
        npc.classList.add("npc");
        map.appendChild(npc);
    });
}

function updatePlayers(playersData) {
    players = playersData;
    Object.keys(players).forEach(id => {
        let player = document.getElementById(id);
        if (!player) {
            player = document.createElement("div");
            player.id = id;
            player.classList.add("player");
            player.style.backgroundColor = players[id].color;
            map.appendChild(player);
        }
        player.style.transform = `translate(${players[id].position.x}px, ${players[id].position.y}px)`;
    });

    updateCamera();
    drawMiniMap();
}

function updateNPCs(npcData) {
    npcs = npcData;
    Object.keys(npcs).forEach(id => {
        let npc = document.getElementById(id);
        if (!npc) {
            npc = document.createElement("div");
            npc.id = id;
            npc.classList.add("npc");
            map.appendChild(npc);
        }
        npc.style.transform = `translate(${npcs[id].position.x}px, ${npcs[id].position.y}px)`;
    });
}

function updateCamera() {
    if (!playerId || !players[playerId]) return;
    const { x, y } = players[playerId].position;
    map.style.transform = `translate(${-x + window.innerWidth / 2}px, ${-y + window.innerHeight / 2}px)`;
}

function drawMiniMap() {
    const aspectRatio = MAP_WIDTH / MAP_HEIGHT;
    const miniMapWidth = 200;
    const miniMapHeight = miniMapWidth / aspectRatio;

    miniMapCanvas.width = miniMapWidth;
    miniMapCanvas.height = miniMapHeight;
    miniCtx.clearRect(0, 0, miniMapWidth, miniMapHeight);
    miniCtx.fillStyle = "black";
    miniCtx.fillRect(0, 0, miniMapWidth, miniMapHeight);

    const scaleX = miniMapWidth / MAP_WIDTH;
    const scaleY = miniMapHeight / MAP_HEIGHT;

    mapObjects.forEach(({ x, y }) => {
        miniCtx.fillStyle = "gray";
        miniCtx.fillRect(x * scaleX, y * scaleY, 3, 3);
    });

    Object.values(players).forEach(({ position, color }) => {
        miniCtx.fillStyle = color;
        miniCtx.fillRect(position.x * scaleX, position.y * scaleY, 5, 5);
    });

    Object.values(npcs).forEach(({ position }) => {
        miniCtx.fillStyle = "red";
        miniCtx.fillRect(position.x * scaleX, position.y * scaleY, 4, 4);
    });

    if (playerId && players[playerId]) {
        const { x, y } = players[playerId].position;
        miniCtx.strokeStyle = "red";
        miniCtx.strokeRect(x * scaleX - 2, y * scaleY - 2, 6, 6);
    }
}

document.addEventListener("keydown", ({ key }) => {
    if (!playerId || !players[playerId]) return;
    let { x, y } = players[playerId].position;
    let speed = 10;

    if (key === "ArrowUp" && y - speed >= 0) y -= speed;
    else if (key === "ArrowDown" && y + speed <= MAP_HEIGHT) y += speed;
    else if (key === "ArrowLeft" && x - speed >= 0) x -= speed;
    else if (key === "ArrowRight" && x + speed <= MAP_WIDTH) x += speed;

    socket.send(JSON.stringify({ action: "move", x, y }));
});
