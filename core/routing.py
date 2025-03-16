from django.urls import re_path
from core.consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r"ws/game/$", GameConsumer.as_asgi()),  # Asegúrate de usar el mismo path en tu frontend
]
