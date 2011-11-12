def startup_installed(sender):
    from uliweb.utils.date import set_timezone, set_local_timezone
    
    set_timezone(sender.settings.GLOBAL.TIME_ZONE)
    set_local_timezone(sender.settings.GLOBAL.LOCAL_TIME_ZONE)