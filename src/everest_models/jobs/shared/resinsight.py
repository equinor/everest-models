import logging
import signal
import sys
from typing import Any

try:
    import rips as _rips
except ImportError:
    _rips = None

rips: Any = _rips
_HAVE_RIPS = rips is not None
_RIPS_LAUNCH_ERROR = getattr(rips, "RipsError", ())

logger = logging.getLogger(__name__)


class ResInsight:
    def __init__(self, executable: str = "") -> None:
        self._executable = executable
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

    def __enter__(self) -> Any:
        if not _HAVE_RIPS:
            msg = "Failed to launch ResInsight: module `rips` not found"
            raise ImportError(msg)
        logger.info("Launching ResInsight...")
        try:
            instance = rips.Instance.launch(
                self._executable, console=True, launch_port=0
            )
        except _RIPS_LAUNCH_ERROR as exc:
            raise ConnectionError(self._launch_error_message()) from exc
        if instance is None:
            raise ConnectionError(self._launch_error_message())

        self._instance = instance
        return instance

    def _launch_error_message(self) -> str:
        if self._executable == "":
            return "Failed to launch ResInsight: no executable found"
        return f"Failed to launch ResInsight executable: {self._executable}"

    def __exit__(self, *_) -> None:
        self._instance.exit()
