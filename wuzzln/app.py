import sqlite3
from collections import deque
from datetime import datetime
from pathlib import Path

from litestar import Litestar
from litestar.config.compression import CompressionConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures.state import State
from litestar.di import Provide
from litestar.logging.config import LoggingConfig
from litestar.static_files.config import StaticFilesConfig
from litestar.template import TemplateConfig

from wuzzln.routes.add import add_game, delete_game, get_add_game_page
from wuzzln.routes.games import get_games_page
from wuzzln.routes.leaderboard import get_leaderboard_page
from wuzzln.routes.matchmaking import get_matchmaking_page, post_matchmaking
from wuzzln.routes.player import get_player_page
from wuzzln.routes.rules import get_rules_page
from wuzzln.routes.wrapped import get_wrapped_page, is_season_start

logging_config = LoggingConfig(
    root={"level": "DEBUG"},
    formatters={"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
    log_exceptions="always",
)


def register_template_callables(engine: JinjaTemplateEngine):
    engine.register_template_callable(key="is_season_start", template_callable=is_season_start)


async def get_current_datetime():
    """Get current time."""
    return datetime.now()


async def get_database() -> sqlite3.Connection:
    """Get database connection."""
    return sqlite3.connect("database/db.sqlite", detect_types=1)


app = Litestar(
    dependencies={
        "db": Provide(get_database),
        "now": Provide(get_current_datetime),
    },
    state=State({"matchmakings": deque(maxlen=10)}),
    route_handlers=[
        get_leaderboard_page,
        get_add_game_page,
        add_game,
        delete_game,
        get_matchmaking_page,
        post_matchmaking,
        get_games_page,
        get_rules_page,
        get_player_page,
        get_wrapped_page,
    ],
    static_files_config=[
        StaticFilesConfig(directories=["assets/img"], path="img"),
        StaticFilesConfig(directories=["assets/style"], path="style"),
        StaticFilesConfig(directories=["assets/js"], path="js"),
        StaticFilesConfig(directories=["assets/font"], path="font"),
    ],
    compression_config=CompressionConfig(backend="gzip"),
    # middleware=[RateLimitConfig(("second", 20)).middleware],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
        engine_callback=register_template_callables,
    ),
    logging_config=logging_config,
)
