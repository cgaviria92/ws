import json
import random
import uuid
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

MAP_WIDTH, MAP_HEIGHT = 5000, 5000
BASE_POSITION = {"x": MAP_WIDTH // 2, "y": MAP_HEIGHT // 2}
active_players = {}

def generate_map_objects(num_objects=100):
    """Generar objetos en el mapa (Ej: Asteroides)."""
    return [{"x": random.randint(0, MAP_WIDTH), "y": random.randint(0, MAP_HEIGHT)} for _ in range(num_objects)]

MAP_OBJECTS = generate_map_objects()

# Diccionario de NPCs
npc_data = {}
def generate_npcs(num_npcs=5):
    """Generar NPCs con posiciones y direcciones aleatorias."""
    new_npcs = {}
    for i in range(num_npcs):
        npc_id = f"npc_{i}"
        new_npcs[npc_id] = {
            "position": {"x": random.randint(0, MAP_WIDTH), "y": random.randint(0, MAP_HEIGHT)},
            "direction": random.choice(["up", "down", "left", "right"]),
            "speed": 5
        }
    return new_npcs

npc_data = generate_npcs()

# Corrutina para mover NPCs
async def move_npcs():
    """Mueve los NPCs cada segundo y actualiza el estado en tiempo real."""
    channel_layer = get_channel_layer()
    while True:
        for npc_id, npc in npc_data.items():
            direction = npc["direction"]
            speed = npc["speed"]

            # Movimiento en el mapa
            if direction == "up":
                npc["position"]["y"] = max(npc["position"]["y"] - speed, 0)
            elif direction == "down":
                npc["position"]["y"] = min(npc["position"]["y"] + speed, MAP_HEIGHT)
            elif direction == "left":
                npc["position"]["x"] = max(npc["position"]["x"] - speed, 0)
            elif direction == "right":
                npc["position"]["x"] = min(npc["position"]["x"] + speed, MAP_WIDTH)

            # Cambiar dirección aleatoriamente
            if random.random() < 0.1:
                npc["direction"] = random.choice(["up", "down", "left", "right"])

        # Enviar actualización del mundo
        await channel_layer.group_send("game_room", {
            "type": "update_world",
            "players": active_players,
            "npcs": npc_data
        })

        await asyncio.sleep(1)  # Esperar 1 segundo

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.player_id = str(uuid.uuid4())
        self.color = f"#{random.randint(0, 0xFFFFFF):06x}"
        self.position = BASE_POSITION.copy()

        active_players[self.player_id] = {
            "color": self.color,
            "position": self.position
        }

        await self.channel_layer.group_add("game_room", self.channel_name)
        await self.accept()

        await self.send(json.dumps({
            "action": "initialize",
            "player_id": self.player_id,
            "map": MAP_OBJECTS,
            "players": active_players,
            "npcs": npc_data
        }))

        await self.broadcast_update()

    async def disconnect(self, close_code):
        active_players.pop(self.player_id, None)
        await self.channel_layer.group_discard("game_room", self.channel_name)
        await self.broadcast_update()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("action") == "move" and self.player_id in active_players:
            active_players[self.player_id]["position"] = {
                "x": data["x"],
                "y": data["y"]
            }
            await self.broadcast_update()

    async def broadcast_update(self):
        """Enviar actualización de jugadores y NPCs a todos."""
        await self.channel_layer.group_send("game_room", {
            "type": "update_world",
            "players": active_players,
            "npcs": npc_data
        })

    async def update_world(self, event):
        """Se llama cuando se hace group_send("game_room", {...})."""
        await self.send(json.dumps({
            "action": "update_world",
            "players": event["players"],
            "npcs": event["npcs"]
        }))
