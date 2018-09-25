import django.dispatch

# Triggers when system status equal to failed
system_update = django.dispatch.Signal(providing_args=["system", "user"])

# Triggers when system status equal to Offline
system_offline = django.dispatch.Signal(providing_args=["system"])

# Triggers when system status to Good
reading_logs = django.dispatch.Signal(providing_args=["system"])

# Trigger when the next reservation bumps up. It sends a current user a message about
# its reservation

notify_and_delete = django.dispatch.Signal(providing_args=["usr_email", "system",
                                                           "reserve_id", "time_log", "date_log",
                                                           "user_firstname"])
