import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from core.routing import websocket_urlpatterns
from core.consumers import move_npcs
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ws.settings")
django.setup()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(websocket_urlpatterns),
    }
)


# Iniciar NPCs en segundo plano
async def start_npcs():
    await move_npcs()


loop = asyncio.get_event_loop()
loop.create_task(start_npcs())
