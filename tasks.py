from __future__ import absolute_import
from celery.schedules import crontab
from celery.task import periodic_task
from django.contrib.auth.models import User
from reservations.models import SystemReservation, ReserveLogs
from .models import System
from datetime import datetime
from datetime import timedelta
from django.utils.timezone import now
from django.utils import timezone
import math
import pytz
# from time import  sleep
from celery import chain, signature
from django.core.mail import send_mail, send_mass_mail,EmailMessage
from celery.utils.log import get_task_logger
from celery import shared_task, task
from .signals import notify_and_delete


# Sending Email notification
def emailSending(sb, msg, frm, to):
    s_mail = EmailMessage(sb, msg, frm, to)
    s_mail.content_subtype = "html"
    s_mail.send()
    if s_mail:
        logger.info('Message has been successfully send !')
    else:
        logger.info('message has failed')


@periodic_task(name='ReservationExpires', ignore_result=False, run_every=crontab())
def CollectData():
    UTC = pytz.timezone("UTC")
    server_time = now()
    current_tz = timezone.get_current_timezone()
    tzi = UTC.normalize(server_time)
    for e in SystemReservation.objects.filter(start__lte=server_time, reserve_tag='online', end__gte=server_time):
        print(str(e.dut.id), end=' ')
        sys_t = System.objects.get(pk=e.dut.id)
        sys_name = str(sys_t.sys_name).upper()
        # changing timezone from UTC to the user tz
        user_curr_timezone = pytz.timezone(e.tzname)
        # converting the server to the user tz
        user_tz_convert = timezone.localtime(server_time, pytz.timezone(e.tzname))
        # converting the server_time datetime.datetime to iso-format()
        now_time = user_tz_convert.isoformat()

        # sw = current_tz.normalize(e.end.astimezone(current_tz))
        end_d_time = timezone.localtime(e.end).astimezone(user_curr_timezone)
        # converting end time to iso-format()
        end_time = end_d_time.isoformat()
        # se = Chicago.normalize(now())
        user_d_time = timezone.localtime(server_time, pytz.timezone(e.tzname))

        sw_date = end_d_time.date()
        se_time = user_tz_convert
        se_munite = se_time.time()
        se_D = end_d_time.strftime("%I:%M %p")
        sub = 'MyAxxia Database Notification >>> {}'.format(sys_name)
        SysR = User.objects.get(pk=e.user.id)
        u_mail = str(SysR.email)

        # Calculating the remaining time
        time_difference = e.end - now()
        result_in_minutes = time_difference / timedelta(minutes=1)
        minutes = math.ceil(result_in_minutes)
        minute_f = math.floor(result_in_minutes)

        if minutes == 5:

            # creating the string notification message 5 minutes before the expiration
            html_content = str(
                e.user.get_short_name()) + ',' + '<br><br>' + 'Your Reservation for {} system'.format(sys_name) + \
                           ' will expire in ' + str(minutes) + ' minutes.<br><br>' + \
                           'System Name \t:' + ' {}'.format(sys_name) + '<br>' + \
                           'End Date \t:' + ' {}'.format(sw_date) + '<br>' + \
                           'End Time \t:' + ' {}'.format(se_D) + '<br><br>' + \
                           'If more time is needed, create a new reservation using this link: ' + \
                           '<a href="https://myaxxia.amr.corp.intel.com/#/reservation/' \
                           + str(e.dut.id) + '\"' + '>' + '<i>MyAxxia</i>.' + '</a></br>'

            fr_mail = 'myaxxia@intel.com'
            return emailSending(sub, html_content, fr_mail, [u_mail])

        elif minute_f == 0:

            e.reserve_tag = 'Done'
            rez_obj = SystemReservation.objects.get(pk=e.id)
            new_reservation_log = ReserveLogs(request_start=e.start, request_end=e.end, reserve_status='Done',
                                              system=sys_t, reservation=rez_obj, user=SysR)
            new_reservation_log.save(force_insert=True)

            # creating the string notification message when the reservation expires
            html_content_1 = str(e.user.get_short_name()) + ',' + '<br><br>' + 'Your Reservation for {} system'.format(
                sys_name) + ' has expired. <br><br>' + \
                'System Name&ensp;:' + ' {}'.format(sys_name) + '<br>' + \
                'End date <span></span>:' + ' {}'.format(sw_date) + '<br>' + \
                'End Time <span></span>:' + ' {}'.format(se_D) + '<br><br>' + \
                '<a href="http://myaxxia.amr.corp.intel.com/#/reservation/' \
                + str(e.dut.id) + '\"' + '>' + '<i>MyAxxia</i>.' + '</a></br>'

            fr_mails = 'myaxxia@intel.com'
            return emailSending('MyAxxia Database Notification >>> {}'.format(sys_name), html_content_1, fr_mails,
                                [u_mail])
            # Dtx = SystemReservation.objects.get(end=e.end) josue.kula.ntete@intel.com
            # Dtx.delete()
            # print('This is the User ID: ' + str(e.dut.id))
        else:
            print('it ' + str(minutes) + ' Local time is :' + str(se_munite), end=' ')


# Checking the system status for the current Reservation
@periodic_task(name='NextReservation', ignore_result=False, run_every=crontab())
def check_system_status():
    tday = datetime.today()
    # changing timezone from UTC to the user tz
    for e in SystemReservation.objects.filter(start__lte=now(), reserve_tag='online', end__gte=now()):
        current_sys = System.objects.filter(pk=e.dut.id, status='Failed')

        # getting user First Name
        user_shortname = e.user.get_short_name()

        # changing timezone from UTC to the user tz
        user_curr_timezone = pytz.timezone(e.tzname)
        SysR = User.objects.get(pk=e.user.id)
        u_mail = str(SysR.email)
        if current_sys.exists():

            # read from reserve_log and get the las time the system failed log_time__day=tday.day
            get_logs = ReserveLogs.objects.filter(system=e.dut.id, reserve_status='Failed')
            if get_logs.exists():
                last_log = get_logs.latest('log_time')
                # us_email = str(last_log).split(',')[-1]
                sys_nam = str(last_log).split(',')[-1]
                log_me = str(last_log).split(',')[-3]

                # Converting String datetime to datetime type
                log_failed_time = datetime.strptime(log_me, "%Y/%m/%d %H:%M:%S %z")

                # localizing the current user datetime to its specific Tz
                end_d_time = timezone.localtime(log_failed_time).astimezone(user_curr_timezone)

                # creating Date and time for the current user
                cuser_date = str(end_d_time.date())
                cuser_time = str(end_d_time.strftime("%I:%M %p"))

                cuser_date_time = 'on {} at {}'.format(cuser_date, cuser_time)

                # signaling user that the status of the system hasn't changed :: still failed
                notify_and_delete.send(sender=ReserveLogs, usr_email=u_mail, system=sys_nam,
                                       reserve_id=e.id, time_log=cuser_time, date_log=cuser_date,
                                       user_firstname=user_shortname)
            else:
                print('lasted record is not found')
        else:
            print('Proceed further:: keep the reservation')


# A periodic task that will run every minute (the symbol '*' means every )
logger = get_task_logger(__name__)
