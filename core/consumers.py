import asyncio, json, uuid, random
from channels.generic.websocket import AsyncWebsocketConsumer
from core.game import BASE_POSITION, MAP_WIDTH, MAP_HEIGHT, MAP_OBJECTS, active_players
from core.npcs import npc_data

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.player_id = str(uuid.uuid4())
        color = "#%06x" % random.randint(0, 0xFFFFFF)
        active_players[self.player_id] = {"color": color, "position": BASE_POSITION.copy()}
        await self.channel_layer.group_add("game_room", self.channel_name)
        await self.accept()
        await self.send(json.dumps({
            "action": "initialize", "player_id": self.player_id,
            "map_objects": MAP_OBJECTS, "players": active_players, "npcs": npc_data
        }))
        await self.broadcast_update()

    async def disconnect(self, close_code):
        active_players.pop(self.player_id, None)
        await self.channel_layer.group_discard("game_room", self.channel_name)
        await self.broadcast_update()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")
            if action == "move" and self.player_id in active_players:
                active_players[self.player_id]["position"] = {"x": data["x"], "y": data["y"]}
                await self.broadcast_update()
            elif action == "mine":
                await self.mine_asteroid(self.player_id)
        except Exception as e:
            print(f"❌ Error en receive: {e}")

    async def broadcast_update(self):
        """🔄 Envía actualización del mundo."""
        await self.channel_layer.group_send("game_room", {
            "type": "update_world", "players": active_players,
            "npcs": npc_data, "map_objects": MAP_OBJECTS
        })

    async def update_world(self, event):
        """🔄 Enviar actualización de mundo al cliente."""
        await self.send(json.dumps({
            "action": "update_world", "players": event.get("players", {}),
            "npcs": event.get("npcs", {}), "map_objects": event.get("map_objects", MAP_OBJECTS)
        }))

    async def mine_asteroid(self, player_id):
        """⛏️ Minar un asteroide y hacerlo reaparecer tras 10s."""
        if player_id not in active_players:
            return
        pos = active_players[player_id]["position"]
        closest, best_dist = None, float("inf")

        for ast in MAP_OBJECTS:
            dist = ((ast["x"] - pos["x"])**2 + (ast["y"] - pos["y"])**2)**0.5
            if dist < 100 and dist < best_dist:
                best_dist, closest = dist, ast

        if closest:
            MAP_OBJECTS.remove(closest)
            await self.channel_layer.group_send("game_room", {
                "type": "asteroid_removed", "asteroid": closest, "player_id": player_id
            })
            await asyncio.sleep(10)
            new_ast = {"x": random.randint(0, MAP_WIDTH), "y": random.randint(0, MAP_HEIGHT)}
            MAP_OBJECTS.append(new_ast)
            await self.channel_layer.group_send("game_room", {"type": "asteroid_respawn", "asteroid": new_ast})

    async def asteroid_removed(self, event):
        """🔄 Notifica que un asteroide fue minado."""
        await self.send(json.dumps({
            "action": "asteroid_removed", "asteroid": event["asteroid"], "player_id": event["player_id"]
        }))

    async def asteroid_respawn(self, event):
        """🔄 Notifica que un asteroide reapareció."""
        await self.send(json.dumps({"action": "asteroid_respawn", "asteroid": event["asteroid"]}))
