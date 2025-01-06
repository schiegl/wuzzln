from litestar.contrib.htmx.response import HTMXTemplate
from litestar.response import Template


def error(message: str) -> Template:
    return HTMXTemplate(
        template_name="toast.html",
        re_target="#toast",
        context={
            "icon": "warning-circle",
            "message": message,
            "font_color": "#fff",
            "background": "var(--fg-failure)",
        },
    )


def info(message: str) -> Template:
    return HTMXTemplate(
        template_name="toast.html",
        re_target="#toast",
        context={
            "icon": "info",
            "message": message,
            "font_color": "#000",
            "background": "#fdfdfd",
        },
    )


def success(message: str) -> Template:
    return HTMXTemplate(
        template_name="toast.html",
        re_target="#toast",
        context={
            "icon": "check-circle",
            "message": message,
            "font_color": "#fff",
            "background": "var(--fg-success)",
        },
    )
