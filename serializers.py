import time

__author__ = 'jkulante'

from rest_framework import  serializers
from .models import *
from django.contrib.auth.models import  User, Group
from reservations.models import SystemReservation
import pytz
import datetime
import math


# Group
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


# User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')


# Group_and_User
class UserGroupSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'groups')


# Lab Location
class LocationSerializer(serializers.ModelSerializer):
        class Meta:
            model = Location
            fields = '__all__'
            ordering = ['loc_name']


# Rack Location
class RackSerializer(serializers.ModelSerializer):
        class Meta:
            model = Rack
            fields = '__all__'
            ordering = ['rack_name']


# System Category
class SystemCategorySerializer(serializers.ModelSerializer):
    Inter_index = serializers.SerializerMethodField()

    class Meta:
        model = SystemCategory
        fields = ('id', 'system_category_name', 'notes', 'Inter_index')
        ordering = ['id']

    def get_Inter_index(self, obj):
        inst = SystemCategory
        if isinstance(inst, list):
            return inst.index(obj.id)


# System Type
class SystemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemType
        fields = ('id', 'system_type_name', 'notes')

    def validate(self, attrs):
        instance = SystemType(**attrs)
        instance.clean()
        return attrs


# System
class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        ordering = ['sys_name']

    def validate(self, attrs):
        instance = System(**attrs)
        instance.clean()
        return attrs

    # def create(self, validated_data):
    #     obj = System.objects.create(**validated_data)
    #     failed = validated_data['status']
    #
    #     obj.save(foo=validated_data['foo'])
    #     return obj


# Board Type
class BoardTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardType


# System Config
class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = '__all__'

    def validate(self, attrs):
        instance = SystemConfig(**attrs)
        instance.clean()
        return attrs


# Board
# uses the get_system_id method instead of the system field, so that it can handle nested boards

class BoardSerializer(serializers.ModelSerializer):

    # def to_representation(self, instance):
    #     if 'branches' not in self.fields:
    #         self.fields['subboards'] = BoardSerializer(instance, many=True)
    #     return super(BoardSerializer, self).to_representation(instance)

    class Meta:
        model = Board
        # extra_kwargs = {'system': {'required': 'False'}}
        # read_only_fields = ('board_type_name',)
        # validators = [
        #     serializers.UniqueTogetherValidator(
        #         queryset=Board.objects.all(),
        #         fields=("board_position", "system"),
        #         message=("System cannot have a duplicated slot number",)
        #     )
        # ]

    def validate(self, attrs):
        instance = Board(**attrs)
        instance.clean()
        return attrs


# Patch Panel Serializer
# pp_ name is patch panel name
class PatchPanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchPanel
        fields = ('id', 'pp_name', 'serial_number', 'dut_location', 'test_location', 'pp_port')
        ordering = ['id']


# PowerCycle information
class PowerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerInfo
        fields = '__all__'

    def validate(self, attrs):
        instance = PowerInfo(**attrs)
        instance.clean()
        return attrs


# SystemHistory Model
class SystemHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemHistory
        fields = ('id', 'on_dated', 'log_message', 'notes', 'usr', 'title', 'status', 'system')
        read_only_fields = ('title',)

    def validate(self, attrs):
        instance = SystemHistory(**attrs)
        instance.clean()
        return attrs


# Generic Port Serializer
class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ('id', 'numb', 'port_physical_pos', 'inherit', 'mac_address', 'port_local', 'access_name',
                  'ip_address', 'port_type', 'port_speed', 'connected', 'port_rotation', 'description', 'get_board',
                  'getboardport', 'board', 'system')

        ordering = ['numb']
        # validators = [
        #     serializers.UniqueTogetherValidator(
        #         queryset=Port.objects.all(),
        #         fields=("numb", "port_physical_pos", "board"),
        #         message=("Port order and port Label cannot be duplicated for a board"),
        #     )
        # ]

    def validate(self, attrs):
        instance = Port(**attrs)
        instance.clean()
        return attrs


# Patch Panel Port
# pp_port_pos is patch panel port position, pp is patch panel
class PatchPanelPortSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchPanelPort
        fields = ('id', 'pp_port_pos', 'port_type', 'port_speed')


# Link
class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('id', 'link_type', 'pp_port', 'from_port', 'to_port', 'get_from_system', 'get_to_system',
                  'get_board_from', 'get_board_to', 'get_board_type_from', 'get_board_type_to', 'get_board_pp',
                  'get_from_label', 'get_to_label', 'get_pp_label', 'get_from_describe', 'get_to_describe',
                  'get_pp_describe', 'get_from_access_name', 'get_to_access_name', 'get_from_ip_address',
                  'get_to_ip_address', 'get_from_local', 'get_to_local', 'get_pp_local', 'get_from_port_type',
                  'get_to_port_type', 'get_pp_port_type', 'get_from_port_speed', 'get_to_port_speed',
                  'get_pp_port_speed', 'get_from_port_rotation', 'get_to_port_rotation', 'get_pp_port_rotation',
                  'get_from_mac_address', 'get_to_mac_address', 'get_from_connected', 'get_to_connected',
                  'get_pp_connected', 'get_pp_system', 'get_pp_location', 'get_from_sys_cat', 'get_to_sys_cat',
                  'get_from_sys_type', 'get_to_sys_type', 'get_from_type_note', 'get_to_type_note')

        read_only_fields = ('get_from_system', 'get_to_system', 'get_board_to', 'get_board_from', 'get_board_pp'
                            'get_board_type_from', 'get_board_type_to', 'get_from_label', 'get_to_label',
                            'get_pp_label', 'get_from_describe', 'get_to_describe', 'get_pp_describe',
                            'get_from_access_name', 'get_to_access_name', 'get_from_ip_address', 'get_to_ip_address',
                            'get_from_local', 'get_to_local', 'get_pp_local', 'get_from_port_type', 'get_to_port_type',
                            'get_pp_port_type', 'get_from_port_speed', 'get_to_port_speed', 'get_pp_port_speed',
                            'get_from_port_rotation', 'get_to_port_rotation', 'get_pp_port_rotation',
                            'get_from_mac_address', 'get_to_mac_address', 'get_from_connected', 'get_to_connected',
                            'get_pp_connected', 'get_pp_system', 'get_pp_location', 'get_from_sys_cat', 'get_to_sys_cat',
                            'get_from_sys_type', 'get_to_sys_type', 'get_from_type_note', 'get_to_type_note')

        extra_kwargs = {
                        "from_port": {
                                       "error_messages": {"required": "Port at the left side is not selected."}
                                      },
                        "to_port": {
                                     "error_messages": {"required": "Port at the right side is not selected."}
                                   }
                      }

    def validate(self, attrs):
        instance = Link(**attrs)
        instance.clean()
        return attrs

#
# Total connected ports with systems
# class TotalConnectedSystemsSerializer(serializers.ModelSerializer):
#     total_type = serializers.IntegerField()
#     ports = serializers.SerializerMethodField()
#
#     def get_ports(self, obj):
#         rx = Port.objects.filter(system=obj.system)


# Connection
class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ('id', 'ip_address', 'logical_server_port', 'dns_name', 'system', 'board')
        ordering = ['id']


# Link to Systems Serializer
# same as the link serializer except it also returns the system ids of each port
class LinkSystemIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('id', 'link_type', 'pp_port', 'from_port', 'to_port', 'get_from_system', 'get_to_system',
                  'get_board_from', 'get_board_to', 'get_board_type_from', 'get_board_type_to', 'get_board_pp',
                  'get_from_label', 'get_to_label', 'get_pp_label', 'get_from_describe', 'get_to_describe',
                  'get_pp_describe', 'get_from_access_name', 'get_to_access_name', 'get_from_ip_address',
                  'get_to_ip_address', 'get_from_local', 'get_to_local', 'get_pp_local', 'get_from_port_type',
                  'get_to_port_type', 'get_pp_port_type', 'get_from_port_speed', 'get_to_port_speed',
                  'get_pp_port_speed', 'get_from_port_rotation', 'get_to_port_rotation', 'get_pp_port_rotation',
                  'get_from_mac_address', 'get_to_mac_address', 'get_from_connected', 'get_to_connected',
                  'get_pp_connected', 'get_pp_system', 'get_pp_location', 'get_from_sys_cat', 'get_to_sys_cat',
                  'get_from_sys_type', 'get_to_sys_type', 'get_from_type_note', 'get_to_type_note')

        read_only_fields = ('get_from_system', 'get_to_system', 'get_board_type_from', 'get_board_type_to',
                            'get_board_pp', 'get_from_label', 'get_to_label', 'get_pp_label', 'get_from_describe',
                            'get_to_describe', 'get_pp_describe', 'get_from_access_name', 'get_to_access_name',
                            'get_from_ip_address', 'get_to_ip_address', 'get_from_local', 'get_to_local',
                            'get_pp_local', 'get_from_port_type', 'get_to_port_type', 'get_pp_port_type',
                            'get_from_port_speed', 'get_to_port_speed', 'get_pp_port_speed', 'get_from_port_rotation',
                            'get_to_port_rotation', 'get_pp_port_rotation', 'get_from_mac_address', 'get_to_mac_address',
                            'get_from_connected', 'get_to_connected', 'get_pp_connected', 'get_pp_system',
                            'get_pp_location', 'get_from_sys_cat', 'get_to_sys_cat', 'get_from_sys_type',
                            'get_to_sys_type', 'get_from_type_note', 'get_to_type_note')

    def validate(self, attrs):
        instance = Link(**attrs)
        instance.clean()
        return attrs


class PortToSystemSerializer(serializers.ModelSerializer):
    from_port = LinkSystemIDSerializer(many=False)
    to_port = LinkSystemIDSerializer(many=False)

    class Meta:
        model = Port
        fields = ('id', 'numb', 'port_physical_pos', 'inherit', 'mac_address', 'port_local', 'access_name', 'ip_address',
                    'port_type', 'port_speed', 'connected', 'port_rotation', 'description', 'get_board',
                    'getboardport', 'board', 'system', 'get_boardtype', 'from_port', 'to_port')

        ordering = ['numb']

# Advanced Serializers

# Start System-Board-Port Serializer
# used three serializers to handle getting all of the boards on a system
# this allows for up to 3 levels of boards down to A.B.C
# to handle another layer of nested boards copy the code from SubBoardSerializer, change the name and place above
# SubBoardSerializer remembering to change the references


class SubSubBoardSerializer(serializers.ModelSerializer):
    ports = PortToSystemSerializer(many=True)

    class Meta:
        model = Board
        fields = ('id', 'serial_number', 'board_name', 'board_type_name', 'board_type', 'board_position', 'full_position', 'nested', 'ports',)

        ordering = ['id', 'full_position']


class SubBoardSerializer(serializers.ModelSerializer):
    ports = PortToSystemSerializer(many=True)
    subboards = SubSubBoardSerializer(many=True)

    class Meta:
        model = Board
        fields = (
            'id', 'serial_number',  'board_name', 'board_type', 'board_type_name', 'board_position', 'full_position',
            'system', 'nested', 'ports', 'subboards',)

        ordering = ['id', 'full_position']


# this serializer exposes boards data with it sub-boards
class BoardPortSerializer(serializers.ModelSerializer):
    ports = PortSerializer(many=True)
    subboards = SubBoardSerializer(many=True)
    # board_type = BoardTypeSerializer(many=False)

    class Meta:
        model = Board
        fields = ('id', 'board_name', 'serial_number', 'board_type_name', 'board_type', 'board_position',
                  'full_position', 'system', 'nested', 'ports', 'subboards')

        # ordering = ['board_position', 'full_position']


# This Serializer exposes system detail with boards and ports
class SystemBoardPortsSerializer(serializers.ModelSerializer):
    boards = BoardPortSerializer(many=True)
    system_category = SystemCategorySerializer(many=False)
    sys_config = SystemConfigSerializer(many=False)
    system_type = SystemTypeSerializer(many=False)
    primary_maintainer = UserSerializer(many=False)
    lab_location = LocationSerializer(many=False)
    lab = RackSerializer(many=False)
    sys_group = GroupSerializer(many=False)

    class Meta:
        model = System
        fields = ('id', 'sys_name', 'system_category', 'system_type', 'sys_dns', 'sysIp', 'lab_location', 'lab', 'primary_maintainer',
                  'sys_group', 'sys_config', 'status', 'notes', 'boards')

    ordering = ['id', 'boards']


# END System-Board-Port Serializer

# System Connection
# displays all of the connections a system has (IP address and how to access it)
class SystemConnectionSerializer(serializers.ModelSerializer):
    connections = ConnectionSerializer(many=True)

    class Meta:
        model = System
        fields = ('id', 'sys_name', 'lab', 'system_type', 'status', 'connections')


# START DUTToSystem serializer
# used for displaying all of the test gear connected to a DUT
class LinkSystemSerializer(serializers.ModelSerializer):
    get_to_system = SystemConnectionSerializer(many=False)

    class Meta:
        model = Link
        fields = ('id', 'link_type', 'to_port', 'get_to_system')
        ordering = ['id']


# for DUT to system serializer
class SystemToConnectionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = System


class ReserveInSerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemReservation
        fields = ('id', 'start_reserve', 'st_reserve', 'end_reserve', 'user_email',)
        ordering = ['dut']
        read_only_fields = ('title', 'user_email', 'start_reserve')


class SystemConfigInfoSerializer(serializers.ModelSerializer):
    sys_config = SystemConfigSerializer(many=False)
    primary_maintainer = UserSerializer(many=False)
    sys_group = GroupSerializer(many=False)
    system_category = SystemCategorySerializer(many=False)
    system_type = SystemTypeSerializer(many=False)
    lab_location = LocationSerializer(many=False)
    lab = RackSerializer(many=False)
    reserve = serializers.SerializerMethodField()

    def get_reserve(self, obj):
        sj = SystemReservation.objects.all().prefetch_related('dut')
        se = now()
        results = sj.filter(end__gte=se, reserve_tag='online', start__lte=se, dut=obj.id)
        if results.exists():
            return ReserveInSerializer(results, many=True).data
        else:
            sysrel = System.objects.get(pk=obj.id)
            sysrel.availability = 'free'
            sysrel.save(update_fields=['notes'])
            return []

    class Meta:
        model = System
        fields = (
            'id', 'sys_name', 'sys_dns', 'sysIp', 'status', 'can_power', 'power_state', 'can_reserve', 'conn_summary',
            'sys_config', 'primary_maintainer', 'sys_group', 'system_category', 'system_type', 'lab_location', 'lab',
            'reserve', 'notes')


# This is the Serialization of the PP relative to its ports properties
class PatchInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchPanel
        fields = ('id', 'pp_name', 'serial_number', 'dut_location', 'test_location',)


# This is the BoardPortLink
class BoardPortLinkSerializer(serializers.ModelSerializer):
    ports = PortToSystemSerializer(many=True)
    subboards = SubBoardSerializer(many=True)
    # board_type = BoardTypeSerializer(many=False)

    class Meta:
        model = Board
        fields = ('full_position', 'ports', 'subboards')

        ordering = ['full_position']


class SystemLinkSerializer(serializers.ModelSerializer):
    system_category = SystemCategorySerializer(many=False)
    system_type = SystemTypeSerializer(many=False)
    sys_config = SystemConfigSerializer(many=False)
    boards = BoardPortLinkSerializer(many=True)

    class Meta:
        model = System
        fields = ('id', 'sys_name', 'system_category', 'system_type', 'sys_config', 'boards')
        ordering = ['boards']


# Select fields port Serializer for the automated reservation
class ConnectedPortSerializer(serializers.ModelSerializer):
    from_port = LinkSystemIDSerializer(many=False)
    to_port = LinkSystemIDSerializer(many=False)
    class Meta:
        model = Port
        fields = ('id', 'numb', 'port_physical_pos', 'mac_address', 'port_local', 'access_name',
                  'ip_address', 'port_type', 'port_speed', 'connected', 'port_rotation', 'description', 'get_board',
                  'getboardport', 'board', 'from_port', 'to_port', 'system')

        ordering = ['numb']

