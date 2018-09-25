
from django.apps import AppConfig


class SystemsConfig(AppConfig):
    name = 'systems'

    def ready(self):
        import systems.signals