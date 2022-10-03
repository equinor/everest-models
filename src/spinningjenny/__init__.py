import pathlib

from lib.logger import set_up_logger
from spinningjenny.everest_hooks import get_forward_models

__all__ = [
    "get_forward_models",
]

set_up_logger(__name__)

ROOT_DIR = pathlib.Path(__file__).parent.parent

try:
    from spinningjenny.version import version

    __version__ = version
except ImportError:
    __version__ = "0.0.0"
