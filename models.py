import django
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import IntegrityError
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import timedelta, tzinfo
import pytz
from pytz import timezone
from datetime import datetime
from django.utils import timezone
from django.db.models import Max

from .signals import system_update, system_offline, reading_logs

# Create your models here.
from django.core.exceptions import ValidationError


class Location(models.Model):
    loc_name = models.CharField(max_length=30)
    notes = models.CharField(max_length=50, default='', blank=True)

    def __str__(self):
        return self.loc_name

    class Meta:
        ordering = ['loc_name']


class Rack(models.Model):
    rack_name = models.CharField(max_length=30)
    location = models.ForeignKey(Location, null=False, on_delete=models.CASCADE, blank=False)
    notes = models.CharField(max_length=50, default='', blank=True)

    def __str__(self):
        return self.rack_name

    class Meta:
        ordering = ['rack_name']


class SystemType(models.Model):
    system_type_name = models.CharField(max_length=50)
    is_dut = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.system_type_name

    class Meta:
        ordering = ['system_type_name']


class SystemCategory(models.Model):
    system_category_name = models.CharField(max_length=21)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.system_category_name

    class Meta:
        ordering = ['system_category_name']


class SystemConfig(models.Model):
    system_config_name = models.CharField(max_length=30, null=False, blank=False)
    notes = models.TextField(blank=True)
    sys_type = models.ForeignKey(SystemType, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.system_config_name

    class Meta:
        ordering = ['system_config_name']


# class ModelIsProtectedError(IntegrityError):
#     pass
#
#
# @receiver(pre_delete, sender=SystemConfig)
# def prevent_deletions(sender, instance, *args, **kwargs):
#         raise ValidationError("This model can not be deleted")


class System(models.Model):
    sys_name = models.CharField(max_length=50, null=True, blank=True)
    sys_serial_number = models.CharField(max_length=50, null=True, blank=True)
    lab_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    sys_dns = models.CharField(max_length=35, default='', null=True, blank=True)
    sysIp = models.CharField(max_length=35, default='', null=True, blank=True)
    lab = models.ForeignKey(Rack, on_delete=models.SET_NULL, null=True, blank=True)  # this is the rack.info
    status = models.CharField(max_length=10, null=True, blank=True)  # status of the system
    notes = models.TextField(null=True, blank=True)
    is_dut = models.BooleanField(editable=True, default=True)
    can_power = models.BooleanField(editable=True, default=False)
    can_reserve = models.BooleanField(editable=True, default=False)
    system_category = models.ForeignKey(SystemCategory, on_delete=models.PROTECT, null=False, blank=False)
    system_type = models.ForeignKey(SystemType, on_delete=models.PROTECT, null=False, blank=False)
    sys_config = models.ForeignKey(SystemConfig, on_delete=models.SET_NULL, null=True, blank=True)
    primary_maintainer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                           blank=True)  # create a default user
    sys_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=False)
    power_state = models.BooleanField(editable=True, default=True)
    conn_summary = models.TextField(blank=True, default='', max_length=100)
    auto_power = models.BooleanField(editable=True, default=True)
    availability = models.TextField(blank=True, default='', max_length=70)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        try:
            syid = self.pk
            if not self.system_type.is_dut:
                self.is_dut = False
                super(System, self).save()
            elif self.system_type.system_type_name != 'FRIO':
                self.is_dut = False
                super(System, self).save()
            elif self.status == 'Failed':
                super(System, self).save()
                system_update.send(sender=System, system=self, user='')
            elif self.status == 'Offline':
                super(System, self).save()
                system_update.send(sender=System, system=self, user='')
            elif self.status == 'Restricted':
                super(System, self).save()
                system_update.send(sender=System, system=self, user='')
            elif self.status == 'Good':
                super(System, self).save()
                reading_logs.send(sender=System, system=self)
            f = Port.inherit_objects.filter(system=syid)
            if f.exists():
                f.update(access_name=self.sys_dns, ip_address=self.sysIp)
            else:
                super(System, self).save()
        except ValidationError as e:
            non_field_errors = e.message_dict[NON_FIELD_ERRORS]

    def delete(self, force_update=False, update_fields=True, using=None):
        t = Port.Connected_objects.filter(system=self.pk)
        if t.exists():
            raise ValidationError('You cannot delete this system')
        else:
            super(System, self).delete()

    def sys_reserved_status(self):
        if self.system_category == 'Patch panel':
            return 'Out of order'

        # Getting System Category_name

    def get_category(self):
        return "{}".format(self.system_category.system_category_name)

    def get_configuration(self):
        if self.sys_config is None:
            return ""
        else:
            return self.sys_config.system_config_name

    # Group Name
    def get_group(self):
        if self.sys_group is None:
            return ""
        else:
            return self.sys_group.name

    # Getting System Type.
    def get_sys_type(self):
        return "{}".format(self.system_type.system_type_name)

    # Getting System Type Note
    def get_sys_type_note(self):
        return "{}".format(self.system_type.notes)

    def __str__(self):
        return self.sys_name

    class Meta:
        ordering = ['system_category', 'system_type', 'sys_name']


# Patch Panel Port

class PatchPanelPort(models.Model):
    pp_port_pos = models.CharField(max_length=20)
    TYPE = (
        ('RJ45', 'RJ45'),
        ('RJ45-Serial', 'RJ45-Serial'),
        ('Fiber', 'Fiber'),
        ('CPRI', 'CPRI'),
        ('OBSI', 'OBSI'),
        ('LAN', 'LAN'),
        ('Serial', 'Serial'),
        ('SFP Cable', 'SFP Cable'),
    )
    SPEED = (
        ('GbE', 'GbE'),
        ('10G', '10G'),
        ('100G', '100G'),
        ('100M', '100M'),
        ('1G/10G', '1G/10G'),
    )
    port_type = models.CharField(max_length=15, choices=TYPE, default='RJ45')
    port_speed = models.CharField(max_length=10, choices=SPEED, default='GbE')
    connected = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.port_type + '@' + self.pp_port_pos


class PatchPanel(models.Model):
    pp_name = models.CharField(max_length=20, unique=True)
    serial_number = models.CharField(max_length=50)
    dut_location = models.CharField(max_length=20)
    test_location = models.CharField(max_length=20)
    pp_port = models.ForeignKey(PatchPanelPort, related_name='PatchPort')

    def __str__(self):
        return self.pp_name

    class Meta:
        ordering = ['pp_port']


# Power cycle Information
class PowerInfo(models.Model):
    pc_name = models.CharField(max_length=24, blank=True)
    pc_method_name = models.CharField(max_length=22, blank=True)
    pc_Domain_name = models.CharField(max_length=30, blank=True)
    pc_ip_address = models.CharField(max_length=40, blank=True, default='')
    pc_local_port = models.CharField(max_length=35, blank=True)
    pc_mac_address = models.CharField(max_length=35, blank=True)
    pc_command = models.CharField(max_length=200, blank=True)
    pc_type = models.CharField(max_length=200, blank=True, default='Power')
    pc_delay = models.IntegerField(null=True, blank=True)
    pc_action = models.CharField(max_length=35, blank=True, default='Cycle')
    system = models.ForeignKey(System, blank=True, on_delete=models.CASCADE, null=True)

    # Cleaning the save
    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        try:
            self.full_clean()
            super(PowerInfo, self).save()
        except ValidationError as m:
            non_field_errors = m.message_dict[NON_FIELD_ERRORS]

    # elif self.pc_method_name == 'Lambda' and self.pc_command == '':
    # raise ValidationError('Lambda power cycling needs a command')
    def clean(self, **kwargs):
        if self.pc_name == '':
            raise ValidationError('Power cycle should have an operation name')
        elif self.pc_method_name == '':
            raise ValidationError('Power cycle should have a method name')
        elif self.pc_Domain_name == '':
            raise ValidationError('Power cycle must have a DNS')
        elif self.pc_method_name == 'Web Server' and self.pc_local_port == '':
            raise ValidationError('Web Server power cycling needs Bit/Value')
        elif self.pc_action == '':
            raise ValidationError('Please select an action:: CYCLE, ON or OFF')
        elif self.pc_method_name == 'APC' and self.pc_local_port == '':
            raise ValidationError('APC power cycling needs an outlet# and/or a command')
        else:
            pass

    def __str__(self):
        return self.pc_method_name

    class Meta:
        ordering = ['id']


# add board type table
class BoardType(models.Model):
    bt_name = models.CharField(max_length=20)
    abbreviation = models.CharField(max_length=20)

    def __str__(self):
        return self.bt_name


class Board(models.Model):
    board_name = models.CharField(max_length=30, blank=False, null=True)
    # add type field
    board_type = models.ForeignKey(BoardType)
    serial_number = models.CharField(max_length=30, blank=True, null=True)
    board_position = models.PositiveSmallIntegerField() # this is the relative position at the boards current level
    # if the board is at slot 7 this will be 7
    # but any boards nested on that board will have different numbers, the first one will be 1, then 2
    # the full position down bellow will derive the actual position of the board
    position_detail = models.CharField(max_length=30, blank=True)  # used to specify the position  (like amc)
    nested = models.BooleanField(default=False)
    system = models.ForeignKey(System, related_name='boards', null=True, blank=True, on_delete=models.CASCADE)
    parent_board = models.ForeignKey('self', null=True, blank=True, related_name='subboards', on_delete=models.CASCADE)

    # if a board is nested the system fk must be null and parent_board fk must not be null
    # if a board is not nested then system fk must not be null, and the parent board must be null

    # this overwrites the default save method, it calls the clean method bellow before calling the default save method

    # use when you need the parent systems id (it finds the parent system id for all boards even nested boards)
    def get_system_id(self):
        if self.nested is False:
            return self.system.id
        else:
            return self.parent_board.get_system_id()

    # this the the method that should be used when using serializers that require the parent system
    # see the dut-to-system serializer for usage
    def board_type_name(self):
        return self.board_type.bt_name

    def get_sys_category(self):
        return str(self.system.get_category())

    def get_sys_type(self):
        return str(self.system.get_sys_type())

    def get_system(self):
        if self.nested is False:
            return self.system
        elif self.nested and self.system is None:
            return self.parent_board.get_system()
        else:
            return self.parent_board.get_system()

    def full_position(self):
        if self.nested is False:
            return "{}".format(self.board_position)
        else:
            return "{}.{}".format(self.parent_board.full_position(), self.board_position)

    def autoPosition(self):
        return Board.objects.aggregate(max_pos=Max('board_position'))

    def SysLocation(self):
        return self.system.lab

    class Meta:
        ordering = ['board_position', 'id']
        unique_together = ("board_position", "system")

    # Cleaning the save
    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        try:
            self.full_clean()
            super(Board, self).save()
        except ValidationError as m:
            non_field_errors = m.message_dict[NON_FIELD_ERRORS]

    def clean(self, **kwargs):
        # return self.board_type.bt_name + '-' + self.serial_number
        # bd = Board.objects.select_related('system')
        # if bd.filter(board_position=self.board_position, system=self.system).exists():
        #         raise ValidationError('System cannot have a duplicated slot number')
        # elif bd.filter(board_position=self.board_position, system=None).exists():
        #     bd.save()
        # else:
        #     bd.save()
        if self.board_position is None:
            raise ValidationError('cannot be null')

    def __str__(self):
        return "{}".format(self.id)


# class PortManager(models.Manager):
#     def connected_count(self, keyword):
#         return self.filter(connected=keyword).count()


class InheritPortManager(models.Manager):
    def get_queryset(self):
        return super(InheritPortManager, self).get_queryset().filter(inherit=True)


class ConnectedPortManager(models.Manager):
    def get_queryset(self):
        return super(ConnectedPortManager, self).get_queryset().filter(connected=True)


class Port(models.Model):
    TYPE = (
        ('RJ45', 'RJ45'),
        ('Fiber', 'Fiber'),
        ('14-Pin Header', '14-Pin Header'),
        ('20-Pin Header', '20-Pin Header'),
        ('Mictor', 'Mictor'),
        ('SFP', 'SFP'),
        ('Firewire', 'Firewire'),
        ('USB', 'USB'),
        ('Virtual', 'Virtual'),
        ('Other', 'Other'),
    )
    SPEED = (
        ('10/100M', '10/100M'),
        ('1G', '1G'),
        ('10G', '10G'),
        ('40G', '40G'),
        ('N/A', 'N/A'),

    )
    ROTATION = (('Front', 'Front'), ('Back', 'Back'), ('N/A', 'N/A'))
    numb = models.PositiveSmallIntegerField()
    port_physical_pos = models.CharField(max_length=23)
    description = models.CharField(max_length=23, default='', blank=True)
    port_local = models.CharField(max_length=5, default='', blank=True)
    inherit = models.BooleanField(default=False)
    access_name = models.CharField(max_length=30, default='', blank=True)
    ip_address = models.CharField(max_length=40, default='', blank=True)
    port_type = models.CharField(max_length=15, choices=TYPE, default='RJ45')
    port_speed = models.CharField(max_length=15, choices=SPEED, default='GbE')
    port_rotation = models.CharField(max_length=7, choices=ROTATION, default='Front')

    mac_address = models.CharField(max_length=23, blank=True)
    # change to mac address later, create custom validator, can handle
    # 64 bit EUI-64
    connected = models.BooleanField(default=False, editable=False,)
    board = models.ForeignKey(Board, related_name='ports')
    system = models.ForeignKey(System, null=False, blank=False)
    objects = models.Manager()  # counting connected port
    inherit_objects = InheritPortManager()  # getting all inheritPort.
    Connected_objects = ConnectedPortManager()  # getting connected port

    # call the parent boards get system id method and returns the system.id

    def get_system_id(self):
        return self.board.get_system_id()

    # calls the parent boards get system method and returns a full system object
    def get_system(self):
        return self.board.get_system()

    def get_sys_type(self):
        return self.board.get_sys_type()

    def get_boardtype(self):
        return "{}".format(self.board.board_type_name())

    def get_board(self):
        if self.board.nested is False:
            return "{}".format(self.board.board_position)
        else:
            return "{}.{}".format(self.board.parent_board.full_position(), self.board.board_position)

    def getboardport(self):
        # fs = "".join(str(ord(c)) for c in self.port_physical_pos)
        return "{}.{}".format(self.get_board(), self.numb)

    # Deleting a port
    def delete(self, force_update=False, update_fields=True, using=None):
        if self.connected is True:
            raise ValidationError('You cannot delete a connected Port')
        else:
            super(Port, self).delete()

    # Return String from Object
    def __str__(self):
        return self.port_type + "@" + self.port_physical_pos + ' on board ' + self.board.serial_number + ' system ' \
               + self.system.sys_name

    # add a method to return the full port_type
    class Meta:
        ordering = ['numb', 'port_physical_pos', 'board']
        # unique_together = ("numb", "port_physical_pos", "board")


# class PortManager(models.Manager):
#     def get_queryset(self):
#         return super(InheritPortManager, self).get_queryset().filter(inherit=True)


class Link(models.Model):
    TYPE = (
        ('Patch Panel', 'Patch Panel'),
        ('Direct', 'Direct'),
    )
    link_type = models.CharField(max_length=20, choices=TYPE, default='')
    from_port = models.OneToOneField(Port, db_column='from_port', related_name='from_port')
    pp_port = models.OneToOneField(Port, db_column='pp_port', related_name='pp_port', null=True, blank=True)
    to_port = models.OneToOneField(Port, db_column='to_port', related_name='to_port')

    # Getting Full_board_from
    def get_board_from(self):
        return str(self.from_port.get_board())

    # Getting Full_board_to
    def get_board_to(self):
        return str(self.to_port.get_board())

    # PP board
    def get_board_pp(self):
        if self.pp_port is not None:
            return str(self.pp_port.get_board())
        else:
            return ''

    # Getting board_Type_to
    def get_board_type_to(self):
        return str(self.to_port.get_boardtype())

    # Getting board_Type_from
    def get_board_type_from(self):
        return str(self.from_port.get_boardtype())

    # From port label
    def get_from_label(self):
        return self.from_port.port_physical_pos

    # To port label
    def get_to_label(self):
            return self.to_port.port_physical_pos

    # PP port label
    def get_pp_label(self):
        if self.pp_port is not None:
            return self.pp_port.port_physical_pos
        else:
            return ''

    # PP port Description
    def get_pp_describe(self):
        if self.pp_port is not None:
            return self.pp_port.description
        else:
            return ''

    # From port Description
    def get_from_describe(self):
        return self.from_port.description

    # To port Description
    def get_to_describe(self):
        return self.to_port.description

    # From port Access_name
    def get_from_access_name(self):
        return self.from_port.access_name

    def get_to_access_name(self):
        return self.to_port.access_name

    # From port IP_address
    def get_from_ip_address(self):
        return self.from_port.ip_address

    # To port IP_address
    def get_to_ip_address(self):
        return self.to_port.ip_address

    # From port local_port
    def get_from_local(self):
        return self.from_port.port_local

    def get_to_local(self):
        return self.to_port.port_local

    # PP port local_port
    def get_pp_local(self):
        if self.pp_port is not None:
            return self.pp_port.port_local
        else:
            return ''

    # From port Port_type
    def get_from_port_type(self):
        return self.from_port.port_type

    # To port Port_type
    def get_to_port_type(self):
        return self.to_port.port_type

    # PP port port type
    def get_pp_port_type(self):
        if self.pp_port is not None:
            return self.pp_port.port_type
        else:
            return ''

    # From port Port_speed
    def get_from_port_speed(self):
        return self.from_port.port_speed

    # To port Port_speed
    def get_to_port_speed(self):
        return self.to_port.port_speed

    # PP port Speed
    def get_pp_port_speed(self):
        if self.pp_port is not None:
            return self.pp_port.port_speed
        else:
            return ''

    # From port Port_rotation
    def get_from_port_rotation(self):
        return self.from_port.port_rotation

    def get_to_port_rotation(self):
        return self.to_port.port_rotation

    # PP port port_rotation
    def get_pp_port_rotation(self):
        if self.pp_port is not None:
            return self.pp_port.port_rotation
        else:
            return ''

    # From port Port_MAC
    def get_from_mac_address(self):
        return self.from_port.mac_address

    def get_to_mac_address(self):
        return self.to_port.mac_address

    # From port Port_Connected
    def get_from_connected(self):
        return self.from_port.connected

    def get_to_connected(self):
        return self.to_port.connected

    # PP port Port_connected
    def get_pp_connected(self):
        if self.pp_port is not None:
            return self.pp_port.connected
        else:
            return ''

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        try:
            self.full_clean()
            super(Link, self).save()
        except ValidationError as e:
            field_errors = e.message_dict[NON_FIELD_ERRORS]

    def clean(self, **kwargs):

        if self.pk is not None:
            raise ValidationError("you can't update links")
        elif self.from_port == self.to_port:
            raise ValidationError("A port cannot connect to itself")
        elif self.from_port is None:
            raise ValidationError("Device under test port cannot be null")
        elif self.to_port is None:
            raise ValidationError("Test port cannot be null")
        else:
            self.from_port.connected = True
            self.from_port.save()
            self.to_port.connected = True
            self.to_port.save()
            if self.pp_port is None:
                pass
            else:
                self.pp_port.connected = True
                self.pp_port.save()

    def delete(self, force_update=False, update_fields=True, using=None):
        self.from_port.connected = False
        self.from_port.save()
        if self.pp_port is not None:
            self.pp_port.connected = False
            self.pp_port.save()
        else:
            pass
        self.to_port.connected = False
        self.to_port.save()
        super(Link, self).delete()

    # gets the to_port's parent system
    def get_to_system(self):
        return str(self.to_port.get_system())

    # gets the PP_port's parent system
    def get_pp_system(self):
        if self.pp_port is not None:
            return str(self.pp_port.get_system())
        else:
            return ''

    # Location
    def get_pp_location(self):
        if self.pp_port is not None:
            return str(self.pp_port.board.system.lab)
        else:
            return ''

    # gets the to_port's system Category
    def get_to_sys_cat(self):
        return self.to_port.system.get_category()

    # gets the From_system Category
    def get_from_sys_cat(self):
        return self.from_port.system.get_category()


    # gets the From_sys_cat
    # def get_from_sys_type(self):
    #     Sid = self.from_port.board.get_system_id()
    #     ST = System.objects.get(pk=Sid)
    #     return str(ST.system_type.system_type_name)

    # gets the PP_port system Category
    def get_pp_sys_cat(self):
        if self.pp_port is not None:
            return str(self.pp_port.board.system.get_category())
        else:
            return ''

    # get to_port system type
    def get_to_sys_type(self):
        return self.to_port.system.get_sys_type()

    # get to_port system type notes
    def get_to_type_note(self):
        return self.to_port.system.get_sys_type_note()

    # gets pp_port system type
    def get_pp_sys_type(self):
        if self.pp_port is not None:
            return str(self.pp_port.get_sys_type())
        else:
            return ''

    # get to_port's system type
    def get_from_sys_type(self):
        return self.from_port.system.get_sys_type()

    # get to_port system type
    def get_from_type_note(self):
        return self.from_port.system.get_sys_type_note()

    # gets the from_port's parent system
    def get_from_system(self):
        return str(self.from_port.get_system())

    # gets the to_port's parent system.id
    def get_to_system_id(self):
        return self.to_port.get_system_id()

    # gets the from_port's parent system.id
    def get_from_system_id(self):
        return self.from_port.get_system_id()

    def __str__(self):
        return " Id: {}, From {}, To {}".format(self.id, self.from_port, self.to_port)


class Connection(models.Model):
    ip_address = models.GenericIPAddressField(default='0.0.0.0')
    logical_server_port = models.IntegerField(default=0)
    dns_name = models.CharField(max_length=30)
    system = models.ForeignKey(System, related_name='connections')
    board = models.ForeignKey(Board, null=True)

    def __str__(self):
        return self.ip_address

    class Meta:
        ordering = ['system']


class LatestLogManager(models.Manager):
    def get_queryset(self):
        return super(LatestLogManager, self).get_queryset().filter(notes__gt='').latest('on_dated')


class SystemHistory(models.Model):
    on_dated = models.DateTimeField(default=django.utils.timezone.now, editable=True)
    usr = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    log_message = models.CharField(max_length=256, blank=True, default='')
    notes = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=25, blank=True)
    system = models.ForeignKey(System)
    objects = models.Manager()
    specs_objects = LatestLogManager()

    def title(self):
        return self.usr.get_full_name()

    def fmat_dtime(self):
        current_tz = timezone.get_current_timezone()
        on_times = current_tz.normalize(self.on_dated.astimezone(current_tz))
        return on_times

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        lgId = self.pk
        sysid = self.system.id
        sysrel = System.objects.get(pk=sysid)
        href = SystemHistory.objects.filter(system=sysid, notes__gt='')
        sref = SystemHistory.objects.filter(system=sysid, status__gt='')
        try:
            if self.status == "" and self.notes == "" and href.exists():
                last = href.latest('on_dated')

                if sysrel.status and sysrel.notes:
                    self.full_clean()
                    super(SystemHistory, self).save()

                else:
                    sysrel.status = last.status
                    sysrel.notes = last.notes
                    sysrel.save(update_fields=['status', 'notes'])
                    self.full_clean()
                    super(SystemHistory, self).save()

            elif self.status == "" and href.exists():
                last = sref.latest('on_dated')

                if sysrel.status == "":
                    sysrel.status = last.status
                    sysrel.notes = self.notes
                    sysrel.save(update_fields=['status', 'notes'])
                    self.full_clean()
                    super(SystemHistory, self).save()

                else:
                    sysrel.notes = self.notes
                    sysrel.save(update_fields=['notes'])
                    self.full_clean()
                    super(SystemHistory, self).save()

            elif self.notes == "" and href.exists():
                last = href.latest('on_dated')
                sysrel.status = self.status
                sysrel.notes = last.notes
                sysrel.save(update_fields=['notes', 'status'])
                self.full_clean()
                super(SystemHistory, self).save()

            elif self.log_message == "" and self.notes == "" and sysrel.notes:
                sysrel.status = self.status
                sysrel.save(update_fields=['status'])
                self.sys_id = sysrel.id
                self.full_clean()
                super(SystemHistory, self).save()

            else:
                sysrel.notes = self.notes
                sysrel.status = self.status
                sysrel.save(update_fields=['notes', 'status'])
                self.sys_id = sysrel.id
                self.full_clean()
                super(SystemHistory, self).save()

        except ValidationError as e:
            non_field_errors = e.message_dict[NON_FIELD_ERRORS]

    def delete(self, force_update=False, update_fields=True, using=None):
        current_tz = timezone.get_current_timezone()
        Chicago = pytz.timezone("America/Chicago")
        se = Chicago.normalize(now())
        Now_Dated = current_tz.normalize(se.astimezone(current_tz))
        on_dated = current_tz.normalize(self.on_dated.astimezone(current_tz))
        sw_date = on_dated.date()
        se_date = se.date()

        if sw_date < se_date:
            raise ValidationError("You cannot delete a log history in the past.")
        else:
            super(SystemHistory, self).delete()

    def __str__(self):
        return "{},{},{}".format(self.usr.email, self.status, self.on_dated.strftime('%Y/%m/%d %H:%M:%S %z'))

    class Meta:
        ordering = ['-on_dated']

    def clean(self, **kwargs):
        current_tz = timezone.get_current_timezone()
        # Chicago = pytz.timezone("America/Chicago")
        se = now()
        Now_Dated = current_tz.normalize(se.astimezone(current_tz))
        on_dated = current_tz.normalize(self.on_dated.astimezone(current_tz))
        sw_date = on_dated.date()
        se_date = se.date()
        if sw_date < se_date:
            raise ValidationError("You cannot update a log history in the past. Please create a new log")
        elif self.log_message == "" and self.status == "" and self.notes == "":
            raise ValidationError("You cannot create or update logs with empty fields")
        else:
            pass



