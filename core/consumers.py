import asyncio, json, uuid, random
from channels.generic.websocket import AsyncWebsocketConsumer
from core.game import BASE_POSITION, MAP_WIDTH, MAP_HEIGHT, MAP_OBJECTS, active_players
from core.npcs import npc_data

NPC_LIFE = {1: 50, 2: 75, 3: 100}  # Vida según nivel
NPC_DAMAGE = {1: 5, 2: 10, 3: 15}  # Daño según nivel


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.player_id = str(uuid.uuid4())
        color = "#%06x" % random.randint(0, 0xFFFFFF)
        active_players[self.player_id] = {
            "color": color,
            "position": BASE_POSITION.copy(),
            "health": 100,
        }
        await self.channel_layer.group_add("game_room", self.channel_name)
        await self.accept()
        await self.send(
            json.dumps(
                {
                    "action": "initialize",
                    "player_id": self.player_id,
                    "map_objects": MAP_OBJECTS,
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
        try:
            data = json.loads(text_data)
            action = data.get("action")
            if action == "move" and self.player_id in active_players:
                active_players[self.player_id]["position"] = {
                    "x": data["x"],
                    "y": data["y"],
                }
                await self.broadcast_update()
            elif action == "mine":
                asyncio.create_task(self.mine_asteroid(self.player_id))
            elif action == "shoot":
                asyncio.create_task(self.shoot(self.player_id))
        except Exception as e:
            print(f"❌ Error en receive: {e}")

    async def shoot(self, player_id):
        """🔫 Disparar a NPCs cercanos"""
        pos = active_players[player_id]["position"]
        closest, best = None, float("inf")

        for npc_id, npc in npc_data.items():
            dist = (
                (npc["position"]["x"] - pos["x"]) ** 2
                + (npc["position"]["y"] - pos["y"]) ** 2
            ) ** 0.5
            if dist < 200 and dist < best:
                best, closest = dist, npc_id

        if closest:
            npc_data[closest]["health"] -= 20
            if npc_data[closest]["health"] <= 0:
                del npc_data[closest]
                await self.channel_layer.group_send(
                    "game_room", {"type": "npc_killed", "npc_id": closest}
                )
                await asyncio.sleep(10)
                new_npc = {
                    "position": {
                        "x": random.randint(0, MAP_WIDTH),
                        "y": random.randint(0, MAP_HEIGHT),
                    },
                    "level": random.randint(1, 3),
                    "health": NPC_LIFE[random.randint(1, 3)],
                }
                npc_data[closest] = new_npc
                await self.channel_layer.group_send(
                    "game_room", {"type": "npc_respawn", "npc": new_npc}
                )

    async def npc_killed(self, event):
        """🛑 Notifica que un NPC fue eliminado."""
        await self.send(json.dumps({"action": "npc_killed", "npc_id": event["npc_id"]}))

    async def npc_respawn(self, event):
        """♻️ Notifica que un NPC ha reaparecido."""
        await self.send(json.dumps({"action": "npc_respawn", "npc": event["npc"]}))

    async def broadcast_update(self):
        """🔄 Envía actualización del mundo."""
        await self.channel_layer.group_send(
            "game_room",
            {
                "type": "update_world",
                "players": active_players,
                "npcs": npc_data,
                "map_objects": MAP_OBJECTS,
            },
        )

    async def update_world(self, event):
        """🔄 Enviar actualización de mundo al cliente."""
        await self.send(
            json.dumps(
                {
                    "action": "update_world",
                    "players": event.get("players", {}),
                    "npcs": event.get("npcs", {}),
                    "map_objects": event.get("map_objects", MAP_OBJECTS),
                }
            )
        )

    async def mine_asteroid(self, player_id):
        """🔨 Minar asteroides sin bloquear el servidor."""
        pos = active_players[player_id]["position"]
        closest, best = None, float("inf")

        for a in MAP_OBJECTS:
            dist = ((a["x"] - pos["x"]) ** 2 + (a["y"] - pos["y"]) ** 2) ** 0.5
            if dist < 100 and dist < best:
                best, closest = dist, a

        if closest:
            MAP_OBJECTS.remove(closest)

            # 🔥 Notificar a todos los jugadores que el asteroide fue minado
            await self.channel_layer.group_send(
                "game_room",
                {
                    "type": "asteroid_removed",
                    "asteroid": closest,
                    "player_id": player_id,
                },
            )

            # 🔥 Esperar 10 segundos en una tarea separada
            await asyncio.sleep(10)

            new_a = {
                "x": random.randint(0, MAP_WIDTH),
                "y": random.randint(0, MAP_HEIGHT),
            }
            MAP_OBJECTS.append(new_a)

            await self.channel_layer.group_send(
                "game_room", {"type": "asteroid_respawn", "asteroid": new_a}
            )

    async def asteroid_removed(self, event):
        """🔄 Notifica que un asteroide fue minado."""
        await self.send(
            json.dumps(
                {
                    "action": "asteroid_removed",
                    "asteroid": event["asteroid"],
                    "player_id": event["player_id"],
                }
            )
        )

    async def asteroid_respawn(self, event):
        """🔄 Notifica que un asteroide reapareció."""
        await self.send(
            json.dumps({"action": "asteroid_respawn", "asteroid": event["asteroid"]})
        )
