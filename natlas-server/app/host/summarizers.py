from flask import current_app, abort


def hostinfo(ip):
    hostinfo = {}
    count, context = current_app.elastic.get_host(ip)
    if count == 0:
        return abort(404)
    hostinfo["history"] = count
    screenshot_count = current_app.elastic.count_host_screenshots(ip)
    hostinfo["screenshot_count"] = screenshot_count
    screenshots = 0
    screenshotTypes = [
        "screenshots",
        "headshot",
        "vncheadshot",
        "httpheadshot",
        "httpsheadshot",
    ]
    for hs in screenshotTypes:
        if context.get(hs):
            if hs == "screenshots":
                # 0.6.5 iterating screenshots instead of screenshot types
                for _ in context.get(hs):
                    screenshots += 1
            else:
                screenshots += 1
    hostinfo["screenshots"] = screenshots
    if context.get("hostname"):
        hostinfo["hostname"] = context.get("hostname")
    return hostinfo, context
