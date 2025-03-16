import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from core.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ws.settings')  # Asegúrate de usar el nombre correcto

django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # HTTP estándar (para Django)
    "websocket": AuthMiddlewareStack(  # Middleware para manejar autenticación en WebSockets
        URLRouter(websocket_urlpatterns)
    ),
})
