def dev_nav(active=None):
    from uliweb import settings

    out = "<span>"
    for i in settings.MENUS_DEVELOP.nav:
        if active!=i["name"]:
            out += "<a href='%s'>%s<a> "%(i["link"],i["title"])
        else:
            out += "<strong>%s</strong> "%(i["title"])
    out += "</span>"
    return out
