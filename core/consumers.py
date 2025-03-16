import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "game_room"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")
        x = data.get("x")
        y = data.get("y")

        if action == "move":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "player_move",
                    "x": x,
                    "y": y
                }
            )

    async def player_move(self, event):
        await self.send(text_data=json.dumps({
            "action": "update_position",
            "x": event["x"],
            "y": event["y"]
        }))
