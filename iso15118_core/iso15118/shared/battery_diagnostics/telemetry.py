# iso15118/shared/battery_diagnostics/telemetry.py
"""
Shared telemetry writer.

Each DiagnosticService builds its own report dict and calls
TelemetryLogger.write(report, filename).  No coupling to any specific test.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TelemetryLogger:

    @staticmethod
    def write(report: dict, filename: str = "telemetry.json") -> Path:
        """
        Write report dict to JSON file in the current working directory.
        Returns the Path of the written file.
        """
        out = Path(filename)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info(f"[Telemetry] Report written → {out}")
        return out
