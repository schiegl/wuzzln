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
from wuzzln.routes.robots import get_robots_txt
from wuzzln.routes.rules import get_rules_page
from wuzzln.routes.wrapped import get_wrapped_page
from wuzzln.utils import is_season_start, pretty_timestamp

logging_config = LoggingConfig(
    root={"level": "DEBUG"},
    formatters={"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
    log_exceptions="always",
)


async def get_database() -> sqlite3.Connection:
    """Get database connection."""
    return sqlite3.connect("database/db.sqlite", detect_types=1)


def get_current_datetime():
    """Get current time."""
    return datetime.now()


def register_template_callables(tmpl_engine: JinjaTemplateEngine):
    tmpl_engine.register_template_callable(
        key="now", template_callable=lambda ctx: get_current_datetime()
    )
    tmpl_engine.engine.tests["season_start"] = is_season_start
    tmpl_engine.engine.filters["pretty_timestamp"] = pretty_timestamp


app = Litestar(
    dependencies={
        "db": Provide(get_database),
        "now": Provide(get_current_datetime, sync_to_thread=True),
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
        get_robots_txt,
    ],
    static_files_config=[
        StaticFilesConfig(directories=["assets/img"], path="img"),
        StaticFilesConfig(directories=["assets/style"], path="style"),
        StaticFilesConfig(directories=["assets/js"], path="js"),
        StaticFilesConfig(directories=["assets/font"], path="font"),
    ],
    compression_config=CompressionConfig(backend="gzip"),
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
        engine_callback=register_template_callables,
    ),
    logging_config=logging_config,
)
