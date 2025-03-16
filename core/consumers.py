import json
import random
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer

MAP_WIDTH, MAP_HEIGHT = 5000, 5000
BASE_POSITION = {"x": MAP_WIDTH // 2, "y": MAP_HEIGHT // 2}
active_players = {}

def generate_map_objects(num_objects=100):
    return [{"x": random.randint(0, MAP_WIDTH), "y": random.randint(0, MAP_HEIGHT)} for _ in range(num_objects)]

MAP_OBJECTS = generate_map_objects()

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.player_id = str(uuid.uuid4())
        self.color = f"#{random.randint(0, 0xFFFFFF):06x}"
        self.position = BASE_POSITION.copy()

        active_players[self.player_id] = {"color": self.color, "position": self.position}

        await self.channel_layer.group_add("game_room", self.channel_name)
        await self.accept()

        await self.send(json.dumps({
            "action": "initialize",
            "player_id": self.player_id,
            "map": MAP_OBJECTS,
            "players": active_players
        }))

        await self.broadcast_update()

    async def disconnect(self, close_code):
        active_players.pop(self.player_id, None)
        await self.channel_layer.group_discard("game_room", self.channel_name)
        await self.broadcast_update()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("action") == "move" and self.player_id in active_players:
            active_players[self.player_id]["position"].update({"x": data["x"], "y": data["y"]})
            await self.broadcast_update()

    async def broadcast_update(self):
        """Envía actualizaciones de jugadores a todos los clientes."""
        await self.channel_layer.group_send("game_room", {
            "type": "update_players",
            "players": active_players
        })

    async def update_players(self, event):
        """Envía actualización de jugadores a cada cliente."""
        await self.send(json.dumps({"action": "update_players", "players": event["players"]}))
