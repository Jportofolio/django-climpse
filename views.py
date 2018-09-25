import django_filters
from rest_framework import filters
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.core import exceptions
from reservations.models import SystemReservation
from .models import System, SystemType
from django.utils.timezone import now
from django.utils import timezone
import pytz

from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.decorators import parser_classes
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework import  mixins
from rest_framework import generics
from rest_framework import viewsets
# Create your views here.
# https://docs.djangoproject.com/en/1.8/topics/class-based-views/
# http://www.django-rest-framework.org/api-guide/generic-views/
# http://www.django-rest-framework.org/tutorial/3-class-based-views/


# System Views
class SystemViewSet(viewsets.ModelViewSet):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'is_dut', 'system_type', 'sys_config', 'availability')


# Board Type
class BoardTypeViewSet(viewsets.ModelViewSet):
    queryset = BoardType.objects.all()
    serializer_class = BoardTypeSerializer


# System Config
class SystemConfigViewSet(viewsets.ModelViewSet):
    queryset = SystemConfig.objects.all().prefetch_related('sys_type')
    serializer_class = SystemConfigSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'sys_type', 'system_config_name')


# System Type Views
class SystemTypeViewSet(viewsets.ModelViewSet):
    queryset = SystemType.objects.all()
    serializer_class = SystemTypeSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'system_type_name',)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        sysConf = SystemConfig.objects.filter(sys_type=obj.id)

        if sysConf.exists():
            return Response(data={'errorMessage': "You cannot delete " + obj.system_type_name +
                                                  " type. First delete  all related configuration(s)"},
                            status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Power Cycle views
class PowerInfoViewSet(viewsets.ModelViewSet):
    queryset = PowerInfo.objects.filter()
    serializer_class = PowerInfoSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'system',)


# SystemHistory views
class SystemHistoryViewSet(viewsets.ModelViewSet):
    queryset = SystemHistory.objects.all().prefetch_related('system')
    serializer_class = SystemHistorySerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'system',)


# Patch Panel Views
class PatchPanelViewSet(viewsets.ModelViewSet):
    queryset = PatchPanel.objects.all()
    serializer_class = PatchPanelSerializer


# Board Views
class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'system', 'nested')


# DUT system views


# Generic Port Views
class PortViewSet(viewsets.ModelViewSet):
    queryset = Port.objects.all().prefetch_related('system')
    serializer_class = PortSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'board', 'ip_address', 'access_name', 'inherit', 'system')


# Connected Port Views
class ConnectedPortViewSet(viewsets.ModelViewSet):
    queryset = Port.objects.all().prefetch_related('system')
    serializer_class = ConnectedPortSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'system', 'connected', 'port_speed')


# Patch Panel Ports
class PatchPanelPortViewSet(viewsets.ModelViewSet):
    queryset = PatchPanelPort.objects.all()
    serializer_class = PatchPanelPortSerializer


# Links
class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'from_port', 'to_port')


# LinkSystem
class LinkSystemIDViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSystemIDSerializer


# Connections
class ConnectionViewSet(viewsets.ModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer


# advanced serializers

# Board-Ports
class BoardPortViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardPortSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'system',)


# System-Boards-Ports
class SystemBoardPortViewSet(viewsets.ModelViewSet):
    queryset = System.objects.all().prefetch_related('sys_config')
    serializer_class = SystemBoardPortsSerializer


# System-ports-Links
class SystemLinkPortViewSet(viewsets.ModelViewSet):
    queryset = System.objects.all()
    serializer_class = SystemLinkSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'system_category')


class SystemToConnectionsViewSet(viewsets.ModelViewSet):
    queryset = System.objects.filter(is_dut=True)
    serializer_class = SystemToConnectionsSerializer


class SystemConfigInfoViewsSet(viewsets.ModelViewSet):
    queryset = System.objects.all().prefetch_related('sys_config')
    serializer_class = SystemConfigInfoSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'reserve', 'system_type',)


# Getting the viewset of the patch panel relative to its ports type
class PatchInfoViewSet(viewsets.ModelViewSet):
    queryset = PatchPanel.objects.all()
    serializer_class = PatchInfoSerializer


class UserGroupViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserGroupSerializer


class SystemCategoryViewSet(viewsets.ModelViewSet):
    queryset = SystemCategory.objects.all()
    serializer_class = SystemCategorySerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        sysCat = System.objects.filter(system_category=obj.id)

        if sysCat.exists():
            return Response(data={'errorMessage': "You cannot delete " + obj.system_category_name +
                                                  " category. First delete  all related system(s)"},
                            status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'loc_name')

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        rack = Rack.objects.filter(location=obj.id)

        if rack.exists():
            return Response(data={'errorMessage': "You cannot delete this location. First delete related rack(s)"},
                            status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'location')






