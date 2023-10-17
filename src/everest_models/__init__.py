import pathlib

from everest_models.everest_hooks import (
    get_forward_models,
    get_forward_models_schemas,
    parse_forward_model_schema,
)
from everest_models.logger import set_up_logger

__all__ = [
    "get_forward_models",
]

set_up_logger(__name__)

ROOT_DIR = pathlib.Path(__file__).parent.parent

try:
    from everest_models.version import version

    __version__ = version
except ImportError:
    __version__ = "0.0.0"
