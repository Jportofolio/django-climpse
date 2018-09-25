from django.contrib import admin

# Register your models here.
from django.contrib import admin
from systems.models import *
# Register your models here.

admin.site.register(SystemType)
admin.site.register(System)
admin.site.register(Board)
admin.site.register(PatchPanel)
admin.site.register(PowerInfo)
admin.site.register(Port)
admin.site.register(PatchPanelPort)
admin.site.register(Link)
admin.site.register(Connection)
admin.site.register(BoardType)
admin.site.register(SystemConfig)
admin.site.register(SystemCategory)
admin.site.register(Location)
admin.site.register(Rack)
admin.site.register(SystemHistory)