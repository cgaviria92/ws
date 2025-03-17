import random
import asyncio
from channels.layers import get_channel_layer
from core.game import MAP_WIDTH, MAP_HEIGHT, active_players

npc_data = {}


def generate_npcs(num_npcs=5):
    """Generar NPCs con posiciones y direcciones aleatorias."""
    new_npcs = {}
    for i in range(num_npcs):
        npc_id = f"npc_{i}"
        new_npcs[npc_id] = {
            "position": {
                "x": random.randint(0, MAP_WIDTH),
                "y": random.randint(0, MAP_HEIGHT),
            },
            "direction": random.choice(["up", "down", "left", "right"]),
            "speed": 5,
        }
    return new_npcs


npc_data = generate_npcs()


async def move_npcs():
    """Mueve los NPCs continuamente en el mapa y envía actualizaciones."""
    channel_layer = get_channel_layer()
    while True:
        for npc_id, npc in npc_data.items():
            direction = npc["direction"]
            speed = npc["speed"]

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

        # Enviar actualización del estado del juego
        await channel_layer.group_send(
            "game_room",
            {"type": "update_world", "players": active_players, "npcs": npc_data},
        )

        await asyncio.sleep(0.1)  # Hacer que los NPCs se muevan más fluidamente
