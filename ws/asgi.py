import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import asyncio
import logging

# Para mostrar mensajes en consola si algo falla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ws.settings")
django.setup()

from core.routing import websocket_urlpatterns
from core.npcs import move_npcs

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(websocket_urlpatterns),
    }
)

# Creamos la tarea en el event loop para que se ejecute en segundo plano
loop = asyncio.get_event_loop()

async def start_npcs():
    logger.info("Iniciando corrutina de NPCs...")
    await move_npcs()

logger.info("Programando la tarea 'move_npcs' en el event loop...")
loop.create_task(start_npcs())
