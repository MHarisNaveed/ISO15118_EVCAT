# iso15118/shared/battery_diagnostics/battery_simulator.py
"""
Pure physics model of a battery pack.

This class has ZERO knowledge of ISO 15118, test procedures, or telemetry.
It only answers two questions:
  - Given this power flow for this duration, what is the new SOC and voltage?
  - What is the current terminal voltage at this SOC?

Used by:
  - RealBatterySimulator (EVCC side) as its physics engine
  - DiagnosticService subclasses (SECC side) for R_int estimation
"""

import logging

logger = logging.getLogger(__name__)

# ── Default pack constants (override via constructor) ─────────────────────────
_DEFAULT_CAPACITY_WH   = 50.0    # Wh  — small so SOC moves fast in lab
_DEFAULT_MAX_VOLTAGE   = 450.0   # V   — at 100% SOC
_DEFAULT_MIN_VOLTAGE   = 300.0   # V   — at   0% SOC
_DEFAULT_R_INT_OHM     = 0.050   # Ω   — internal resistance seed
_DEFAULT_THERMAL_MASS  = 15_000  # J/K — pack thermal mass
_AMBIENT_TEMP_C        = 25.0


class BatterySimulator:
    """
    Physics-based battery model.

    SOC integration:
        ΔE_Wh  = P_W × Δt_s / 3600
        SOC    = clamp(SOC + ΔE_Wh / capacity_Wh × 100,  0, 100)

    OCV (linear approximation):
        V_oc   = V_min + (V_max − V_min) × SOC / 100

    Terminal voltage under load:
        V_term = V_oc − I × R_int          (charge: I > 0, discharge: I < 0)

    Thermal model (Newton cooling):
        dT = (I² × R_int × Δt) / thermal_mass
        T  = T + dT + (T_ambient − T) × 0.001   (slow cooling)
    """

    def __init__(
        self,
        capacity_wh: float = _DEFAULT_CAPACITY_WH,
        max_voltage: float = _DEFAULT_MAX_VOLTAGE,
        min_voltage: float = _DEFAULT_MIN_VOLTAGE,
        r_int_ohm: float   = _DEFAULT_R_INT_OHM,
        initial_soc: float = 90.0,
    ):
        self.capacity_wh   = capacity_wh
        self.max_voltage   = max_voltage
        self.min_voltage   = min_voltage
        self.r_int_ohm     = r_int_ohm

        self._soc          = float(initial_soc)
        self._temperature  = _AMBIENT_TEMP_C

    # ── Read-only properties ──────────────────────────────────────────────────

    @property
    def soc(self) -> float:
        """State of charge, 0–100 %."""
        return round(self._soc, 3)

    @property
    def temperature_c(self) -> float:
        return round(self._temperature, 2)

    # ── Physics ───────────────────────────────────────────────────────────────

    def ocv(self) -> float:
        """Open-circuit voltage from SOC (linear model)."""
        return self.min_voltage + (self.max_voltage - self.min_voltage) * (
            self._soc / 100.0
        )

    def terminal_voltage(self, current_a: float) -> float:
        """
        Terminal voltage under load.
        current_a > 0 = charging (voltage rises above OCV)
        current_a < 0 = discharging (voltage sags below OCV)
        """
        return self.ocv() - current_a * self.r_int_ohm

    def update(self, power_w: float, dt_s: float) -> None:
        """
        Integrate energy flow and update SOC + temperature.

        Args:
            power_w:  Signed power in watts.
                      Positive → charging  (SOC rises).
                      Negative → discharging (SOC falls).
            dt_s:     Time step in seconds.
        """
        if dt_s < 0.001:
            return

        energy_wh   = (power_w * dt_s) / 3600.0
        delta_soc   = (energy_wh / self.capacity_wh) * 100.0
        old_soc     = self._soc
        self._soc   = max(0.0, min(100.0, self._soc + delta_soc))

        # Thermal update — use approximate current from power / ocv
        v   = max(self.ocv(), 1.0)
        i   = power_w / v
        heat_j = (i ** 2) * self.r_int_ohm * dt_s
        self._temperature += heat_j / _DEFAULT_THERMAL_MASS
        self._temperature += (_AMBIENT_TEMP_C - self._temperature) * 0.001

        logger.debug(
            f"[BatterySimulator] P={power_w:+.0f}W Δt={dt_s:.2f}s "
            f"SOC {old_soc:.2f}%→{self._soc:.2f}% "
            f"V={self.ocv():.1f}V T={self._temperature:.1f}°C"
        )

    def estimate_r_int(self, v_measured: float, current_a: float) -> float:
        """
        Estimate internal resistance from measured terminal voltage sag.
        R_int = (V_oc − V_measured) / |I|

        Returns a clamped value in Ohms.
        Raw data only — interpretation is the DiagnosticService's job.
        """
        i_abs = max(abs(current_a), 0.1)
        r = (self.ocv() - v_measured) / i_abs
        return max(0.001, min(r, 1.0))   # clamp 1 mΩ – 1 Ω
