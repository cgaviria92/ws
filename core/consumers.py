import json
import random
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer

# Tamaño del mapa
MAP_WIDTH = 5000
MAP_HEIGHT = 5000
BASE_POSITION = {"x": MAP_WIDTH // 2, "y": MAP_HEIGHT // 2}

# Almacenar los jugadores activos
active_players = {}

def generate_map_objects():
    objects = []
    for _ in range(100):  # Aumentamos el número de objetos espaciales
        objects.append({
            "type": "asteroid",
            "x": random.randint(0, MAP_WIDTH),  # Ahora cubre toda el área
            "y": random.randint(0, MAP_HEIGHT)
        })
    return objects

MAP_OBJECTS = generate_map_objects()

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.player_id = str(uuid.uuid4())
        self.color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        self.position = BASE_POSITION.copy()

        active_players[self.player_id] = {"color": self.color, "position": self.position}

        self.room_group_name = "game_room"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            "action": "initialize",
            "player_id": self.player_id,
            "map": MAP_OBJECTS,
            "players": active_players
        }))

        await self.send_players_update()

    async def disconnect(self, close_code):
        if self.player_id in active_players:
            del active_players[self.player_id]
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.send_players_update()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "move":
            if self.player_id in active_players:
                self.position["x"] = data["x"]
                self.position["y"] = data["y"]
                active_players[self.player_id]["position"] = self.position
                await self.send_players_update()

    async def send_players_update(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "update_players",
                "players": active_players
            }
        )

    async def update_players(self, event):
        await self.send(text_data=json.dumps({
            "action": "update_players",
            "players": event["players"]
        }))
