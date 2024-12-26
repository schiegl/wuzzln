from collections import deque
from pathlib import Path

from litestar import Litestar
from litestar.config.compression import CompressionConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures.state import State
from litestar.di import Provide
from litestar.logging.config import LoggingConfig
from litestar.static_files.config import StaticFilesConfig
from litestar.template import TemplateConfig

from wuzzln.database import get_database
from wuzzln.routes.add import add_game, delete_game, get_add_game_page
from wuzzln.routes.games import get_games_page
from wuzzln.routes.leaderboard import get_leaderboard_page
from wuzzln.routes.matchmaking import get_matchmaking_page, post_matchmaking
from wuzzln.routes.player import get_player_page
from wuzzln.routes.rules import get_rules_page
from wuzzln.routes.wrapped import get_wrapped_page, get_wrapped_season

logging_config = LoggingConfig(
    root={"level": "DEBUG"},
    formatters={"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
    log_exceptions="always",
)


def register_template_callables(engine: JinjaTemplateEngine):
    engine.register_template_callable(
        key="get_wrapped_season", template_callable=get_wrapped_season
    )


app = Litestar(
    dependencies={"db": Provide(get_database, use_cache=True)},
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
