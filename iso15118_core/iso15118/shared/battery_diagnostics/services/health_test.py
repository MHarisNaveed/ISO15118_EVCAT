# iso15118/shared/battery_diagnostics/services/health_test.py
"""
BatteryHealthService — 5C discharge health test (service_id = 101)

SECC role (this class):
  - Advertises the test via get_parameter_list()
  - Commands charge then discharge via on_cycle() → CurrentCommand
  - Receives raw V, I, SOC from ev_data_context each cycle
  - Computes SOH, R_int, energy delivered — the diagnostic IP
  - Writes health_telemetry.json on session end

EVCC role (RealBatterySimulator):
  - Follows current commands within battery limits
  - Reports raw V, I, SOC each cycle — nothing more

All test logic, phase management, and health algorithms live here.
SimEVSEController has zero health-test knowledge.
"""

import logging
import time
from typing import List, Optional

from iso15118.shared.battery_diagnostics.base_service import (
    CurrentCommand,
    DiagnosticService,
)
from iso15118.shared.battery_diagnostics.battery_simulator import BatterySimulator
from iso15118.shared.battery_diagnostics.telemetry import TelemetryLogger
from iso15118.shared.messages.iso15118_20.common_messages import (
    Parameter,
    ParameterSet,
    ServiceParameterList,
)

logger = logging.getLogger(__name__)

# ── Service identity ──────────────────────────────────────────────────────────
_SERVICE_ID   = 101
_SERVICE_NAME = "BatteryHealthTest"

# ── Default test parameters (overridden by EVCC via ParameterSet) ─────────────
_DEFAULT_C_RATE    = 50.0   # C
_DEFAULT_CUTOFF    = 20    # % SOC
_DEFAULT_MAX_I_A   = 500.0  # A  — max discharge current this charger can sink
_CHARGE_TARGET_SOC = 100.0 # % — always charge to full before discharge
_CYCLE_DT_S        = 3.0   # s  — charge loop interval (matches chargeLoopDelayTime)


class BatteryHealthService(DiagnosticService):

    SERVICE_ID = _SERVICE_ID
    NAME       = _SERVICE_NAME

    def __init__(self):
        # ── Test configuration (set in on_selected) ───────────────────────────
        self._c_rate:    float = _DEFAULT_C_RATE
        self._cutoff:    int   = _DEFAULT_CUTOFF
        self._max_i_a:   float = _DEFAULT_MAX_I_A

        # ── Runtime state (reset in on_selected) ──────────────────────────────
        self._phase:     str   = "CHARGE"   # "CHARGE" | "DISCHARGE"
        self._battery:   Optional[BatterySimulator] = None

        # ── Telemetry accumulation ─────────────────────────────────────────────
        self._cycles:    List[dict] = []
        self._energy_wh: float = 0.0
        self._t_start:   float = 0.0

    # ── DiagnosticService interface ───────────────────────────────────────────

    def get_parameter_list(self) -> ServiceParameterList:
        """
        Advertised in ServiceDetailRes when EVCC requests service_id=101.
        One ParameterSet — Scheduled DC, the test parameters.
        """
        params = [
            Parameter(name="Connector",        int_value=2),
            Parameter(name="ControlMode",      int_value=1),   # 1 = Scheduled
            Parameter(name="MobilityNeedsMode",int_value=1),
            Parameter(name="RequestedCRate",   int_value=int(_DEFAULT_C_RATE)),
            Parameter(name="MaxTestCurrentA",  int_value=int(_DEFAULT_MAX_I_A)),
            Parameter(name="CutoffSOC",        int_value=_DEFAULT_CUTOFF),
        ]
        return ServiceParameterList(
            parameter_sets=[ParameterSet(id=1, parameters=params)]
        )

    def on_selected(
        self, parameter_set: Optional[ParameterSet], battery: BatterySimulator
    ) -> None:
        """Parse parameters, store battery reference, reset state."""
        self._battery = battery

        if parameter_set:
            for p in parameter_set.parameters:
                if p.name == "RequestedCRate" and p.int_value is not None:
                    self._c_rate = float(p.int_value)
                elif p.name == "MaxTestCurrentA" and p.int_value is not None:
                    self._max_i_a = float(p.int_value)
                elif p.name == "CutoffSOC" and p.int_value is not None:
                    self._cutoff = int(p.int_value)

        # Reset state
        self._phase     = "CHARGE"
        self._cycles    = []
        self._energy_wh = 0.0
        self._t_start   = time.time()

        logger.info(
            f"[{self.NAME}] Selected — C-rate={self._c_rate}C "
            f"MaxI={self._max_i_a}A CutoffSOC={self._cutoff}%"
        )

    def on_cycle(
        self, ev_data_context, battery: BatterySimulator
    ) -> CurrentCommand:
        """
        Called every DC_ChargeLoop cycle.

        1. Read raw data from ev_data_context (courier from EVCC)
        2. Run diagnostic algorithms (SOH computation, R_int, energy)
        3. Determine next command (phase logic)
        4. Return CurrentCommand
        """
        # ── 1. Read raw data ──────────────────────────────────────────────────
        voltage = float(getattr(ev_data_context, "present_voltage", None)
                        or battery.ocv())
        current = float(getattr(ev_data_context, "target_current", None) or 0.0)
        soc     = float(getattr(ev_data_context, "present_soc", None)
                        or battery.soc)

        # ── 2. Diagnostic algorithms (CARISSMA IP) ────────────────────────────
        power_w = abs(voltage * current)

        # Energy integration — only during discharge
        if self._phase == "DISCHARGE" and current < 0:
            self._energy_wh += power_w * (_CYCLE_DT_S / 3600.0)

        # R_int from voltage sag — raw measurement, not a decision
        r_int_ohm = battery.estimate_r_int(voltage, current)

        # Log cycle
        cycle = {
            "index":         len(self._cycles),
            "phase":         self._phase,
            "soc_pct":       round(soc, 1),
            "voltage_v":     round(voltage, 3),
            "current_a":     round(current, 3),
            "power_w":       round(power_w, 1),
            "energy_wh":     round(self._energy_wh, 4),
            "r_int_mohm":    round(r_int_ohm * 1000, 2),
            "temperature_c": battery.temperature_c,
        }
        self._cycles.append(cycle)
        logger.info(
            f"[{self.NAME} #{cycle['index']}] {self._phase} | "
            f"SOC={soc:.1f}% V={voltage:.1f}V I={current:.1f}A "
            f"P={power_w:.0f}W E={self._energy_wh:.3f}Wh "
            f"R={r_int_ohm*1000:.1f}mΩ T={battery.temperature_c:.1f}°C"
        )

        # ── 3. Phase logic and next command ───────────────────────────────────
        return self._next_command(soc, battery)

    def on_end(self) -> None:
        """Compute final SOH and write report."""
        if not self._cycles:
            logger.warning(f"[{self.NAME}] on_end() called with no cycles recorded")
            return

        nominal_wh = self._battery.capacity_wh if self._battery else 50.0
        soh = round(
            100.0 * self._energy_wh / nominal_wh, 2
        ) if nominal_wh > 0 else 0.0

        discharge_cycles = [c for c in self._cycles if c["phase"] == "DISCHARGE"]
        r_int_final = (
            discharge_cycles[-1]["r_int_mohm"] if discharge_cycles else 0.0
        )
        peak_temp = max(c["temperature_c"] for c in self._cycles)

        report = {
            "service":              self.NAME,
            "service_id":           self.SERVICE_ID,
            "test_start_epoch":     self._t_start,
            "test_duration_s":      round(time.time() - self._t_start, 1),
            "requested_c_rate":     self._c_rate,
            "cutoff_soc_pct":       self._cutoff,
            "nominal_capacity_wh":  nominal_wh,
            "measured_capacity_wh": round(self._energy_wh, 3),
            "soh_pct":              soh,
            "r_int_final_mohm":     r_int_final,
            "peak_temperature_c":   round(peak_temp, 2),
            "total_cycles":         len(self._cycles),
            "discharge_cycles":     len(discharge_cycles),
            "cycles":               self._cycles,
        }

        TelemetryLogger.write(report, "health_telemetry.json")
        logger.info(
            f"[{self.NAME}] Complete — SOH={soh}% "
            f"Capacity={self._energy_wh:.1f}/{nominal_wh}Wh "
            f"R_int={r_int_final}mΩ T_peak={peak_temp:.1f}°C"
        )

    # ── Internal phase state machine ──────────────────────────────────────────

    def _next_command(self, soc: float, battery: BatterySimulator) -> CurrentCommand:
        """
        Determine what the charger should command next cycle.

        Phase 1 CHARGE:
          Command normal charge until SOC = 100%
          Then transition to DISCHARGE

        Phase 2 DISCHARGE:
          Command 5C discharge (clamped to max_i_a)
          Stop when SOC ≤ cutoff_soc
        """
        if self._phase == "CHARGE":
            if soc >= _CHARGE_TARGET_SOC:
                logger.info(
                    f"[{self.NAME}] Phase 1 complete — SOC={soc:.1f}%. "
                    "Switching to DISCHARGE."
                )
                self._phase = "DISCHARGE"
                return self._discharge_command(battery)
            else:
                # Normal charge command — let SECC session limits handle power
                v = battery.ocv()
                return CurrentCommand(
                    target_current_a = battery.capacity_wh / max(v, 1.0),
                    target_voltage_v = v,
                    phase_label      = "CHARGE",
                    test_complete    = False,
                )

        else:  # DISCHARGE
            if soc <= self._cutoff:
                logger.info(
                    f"[{self.NAME}] Phase 2 complete — "
                    f"SOC={soc:.1f}% ≤ cutoff={self._cutoff}%"
                )
                return CurrentCommand(
                    target_current_a = 0.0,
                    target_voltage_v = battery.ocv(),
                    phase_label      = "DISCHARGE_COMPLETE",
                    test_complete    = True,
                )
            return self._discharge_command(battery)

    def _discharge_command(self, battery: BatterySimulator) -> CurrentCommand:
        """
        Compute operative discharge current.
        Operative = min(requested 5C, charger hardware limit)
        The EVCC will further clamp to its own battery limits.
        """
        capacity_ah = battery.capacity_wh / max(battery.ocv(), 1.0)
        requested_i = self._c_rate * capacity_ah
        operative_i = min(requested_i, self._max_i_a)  # charger hardware limit
        v           = battery.ocv()

        return CurrentCommand(
            target_current_a = -operative_i,    # negative = discharge
            target_voltage_v = v,
            phase_label      = f"DISCHARGE_{self._c_rate}C",
            test_complete    = False,
        )
