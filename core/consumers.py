import json
import uuid
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from core.game import BASE_POSITION, MAP_OBJECTS, active_players
from core.npcs import npc_data

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.player_id = str(uuid.uuid4())
        self.color = f"#{random.randint(0, 0xFFFFFF):06x}"
        self.position = BASE_POSITION.copy()

        active_players[self.player_id] = {
            "color": self.color,
            "position": self.position,
        }

        await self.channel_layer.group_add("game_room", self.channel_name)
        await self.accept()

        await self.send(
            json.dumps(
                {
                    "action": "initialize",
                    "player_id": self.player_id,
                    "map": MAP_OBJECTS,
                    "players": active_players,
                    "npcs": npc_data,
                }
            )
        )

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
                "y": data["y"],
            }
            await self.broadcast_update()

    async def broadcast_update(self):
        """Enviar actualización de jugadores y NPCs a todos."""
        await self.channel_layer.group_send(
            "game_room",
            {"type": "update_world", "players": active_players, "npcs": npc_data},
        )

    async def update_world(self, event):
        """Se llama cuando se hace group_send("game_room", {...})."""
        await self.send(
            json.dumps(
                {
                    "action": "update_world",
                    "players": event["players"],
                    "npcs": event["npcs"],
                }
            )
        )
