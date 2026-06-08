# iso15118/shared/battery_diagnostics/base_service.py
"""
Abstract base class for all battery diagnostic services.

Every test (BatteryHealthTest, EISTest, HPPCTest, ...) implements this
interface.  The ServiceRegistry calls these four methods — nothing else.

Design rule:
  - DiagnosticService has NO knowledge of ISO 15118 state machines.
  - It receives raw data (EVDataContext) and returns a command (CurrentCommand).
  - All SOH/impedance/health computation lives here, not in simulators.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from iso15118.shared.messages.iso15118_20.common_messages import (
    ParameterSet,
    ServiceParameterList,
)

# EVDataContext is imported lazily inside methods to avoid circular imports.
# Type hint kept as string.


@dataclass
class CurrentCommand:
    """
    What the charger (SECC) should command in the next DCChargeLoopRes.

    The ServiceRegistry writes these values into evse_data_context so the
    existing send_charging_command() path picks them up without modification.

    positive current → charging
    negative current → discharging (BPT)
    """
    target_current_a: float
    target_voltage_v: float
    phase_label: str        = "IDLE"   # human-readable, logged only
    test_complete: bool     = False     # True → EVCC should stop session


class DiagnosticService(ABC):
    """
    Abstract base for one battery diagnostic test.

    Subclass this for every new test type.  Register one instance in
    ServiceRegistry.  That is all.
    """

    # ── Must be set as class attributes in every subclass ────────────────────
    SERVICE_ID:  int  = 0
    NAME:        str  = "UnnamedService"

    # ── ServiceRegistry calls these four methods only ─────────────────────────

    @abstractmethod
    def get_parameter_list(self) -> ServiceParameterList:
        """
        Return the ISO 15118-20 ServiceParameterList for this service.
        Advertised in ServiceDetailRes when the EVCC asks for this service_id.
        """
        raise NotImplementedError

    @abstractmethod
    def on_selected(self, parameter_set: ParameterSet,
                    battery: "BatterySimulator") -> None:  # noqa: F821
        """
        Called once when the EVCC selects this VAS in ServiceSelectionReq.
        Parse your parameters, reset internal state, store battery reference.
        """
        raise NotImplementedError

    @abstractmethod
    def on_cycle(self, ev_data_context: "EVDataContext",  # noqa: F821
                 battery: "BatterySimulator") -> CurrentCommand:  # noqa: F821
        """
        Called every DC_ChargeLoop cycle.

        Receives:
          ev_data_context  — raw V, I, SOC reported by the EVCC this cycle
          battery          — physics model (for R_int estimation, OCV lookup)

        Returns:
          CurrentCommand   — what to command next cycle
                             (written into evse_data_context by ServiceRegistry)
        """
        raise NotImplementedError

    @abstractmethod
    def on_end(self) -> None:
        """
        Called when the ISO 15118-20 session ends (session_ended()).
        Write your report here.
        """
        raise NotImplementedError
