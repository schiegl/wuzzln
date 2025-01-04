from litestar import get


@get("/robots.txt")
async def get_robots_txt() -> str:
    return "User-agent: *\nDisallow: /"
