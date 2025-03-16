import json
import random
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer

# Almacenar los jugadores activos en memoria (clave: ID del jugador)
active_players = {}

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Crear un ID único para cada jugador
        self.player_id = str(uuid.uuid4())

        # Asignar un color aleatorio al jugador
        self.color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        # Iniciar la posición del jugador
        self.position = {"x": random.randint(0, 380), "y": random.randint(0, 380)}

        # Agregar al jugador a la lista de jugadores activos
        active_players[self.player_id] = {"color": self.color, "position": self.position}

        # Grupo para comunicación en tiempo real
        self.room_group_name = "game_room"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Aceptar la conexión
        await self.accept()

        # Enviar la lista actualizada de jugadores a todos
        await self.send_players_update()

    async def disconnect(self, close_code):
        # Remover al jugador de la lista al desconectarse
        if self.player_id in active_players:
            del active_players[self.player_id]

        # Eliminar de la sala de WebSocket
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Enviar actualización a los demás
        await self.send_players_update()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "move":
            # Actualizar posición del jugador
            self.position["x"] = data["x"]
            self.position["y"] = data["y"]
            active_players[self.player_id]["position"] = self.position

            # Enviar la nueva posición a todos
            await self.send_players_update()

    async def send_players_update(self):
        """Enviar la lista actualizada de jugadores a todos los clientes"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "update_players",
                "players": active_players
            }
        )

    async def update_players(self, event):
        """Enviar la información de los jugadores a cada cliente"""
        await self.send(text_data=json.dumps({
            "action": "update_players",
            "players": event["players"]
        }))
