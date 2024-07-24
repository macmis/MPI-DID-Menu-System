# MPI_DIDs/routing.py
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from didmenusystem.consumers import ProgressConsumer

websocket_urlpatterns = [
    path("ws/progress/", ProgressConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # This will handle traditional HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),  # This will handle WebSocket connections
})
