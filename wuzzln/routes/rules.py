from litestar import get
from litestar.response import Template


@get("/rules")
async def get_rules_page() -> Template:
    return Template("rules.html")
