import random

MAP_WIDTH, MAP_HEIGHT = 5000, 5000
BASE_POSITION = {"x": MAP_WIDTH // 2, "y": MAP_HEIGHT // 2}
active_players = {}

def generate_map_objects(num_objects=100):
    """Generar objetos en el mapa (Ej: Asteroides)."""
    return [
        {"x": random.randint(0, MAP_WIDTH), "y": random.randint(0, MAP_HEIGHT)}
        for _ in range(num_objects)
    ]

MAP_OBJECTS = generate_map_objects()
