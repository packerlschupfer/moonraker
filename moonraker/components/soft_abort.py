# Moonraker component: graceful "soft abort" over HTTP.
#
# Exposes the klippy `soft_cancel/abort` webhook (from extras/soft_cancel.py) as
# POST /machine/soft_abort, so a UI button can interrupt an IN-FLIGHT BLOCKING wait
# (M190/M109 heat, M191/TEMPERATURE_WAIT chamber soak, BED_MESH_CALIBRATE, G28 Z)
# WITHOUT an emergency stop — the printer parks to idle and stays `ready` (no
# FIRMWARE_RESTART).
#
# CRITICAL: this calls the klippy webhook endpoint OUT-OF-BAND — the SAME mechanism
# `emergency_stop` uses (`klippy_apis._send_klippy_request`, dispatched from the
# reactor, mutex-free). It is NOT a gcode script: a gcode macro would take the gcode
# mutex and hang exactly like the native cancel does (the bug this fixes).
#
# Enable with `[soft_abort]` in moonraker.conf.
from __future__ import annotations
import logging
from ..common import RequestType, WebRequest

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from .klippy_apis import KlippyAPI

KLIPPY_SOFT_ABORT = "soft_cancel/abort"


class SoftAbort:
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.server.register_endpoint(
            "/machine/soft_abort", RequestType.POST, self._handle_soft_abort
        )

    async def _handle_soft_abort(self, web_request: WebRequest) -> Any:
        kapis: KlippyAPI = self.server.lookup_component("klippy_apis")
        # Out-of-band klippy call (mutex-free) — mirrors emergency_stop's path.
        result = await kapis._send_klippy_request(KLIPPY_SOFT_ABORT, {})
        logging.info("soft_abort: klippy returned %s", result)
        return result


def load_component(config: ConfigHelper) -> SoftAbort:
    return SoftAbort(config)
