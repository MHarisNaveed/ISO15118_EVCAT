# iso15118/shared/battery_diagnostics/registry.py
"""
ServiceRegistry

The one object SimEVSEController holds.  It:
  - Stores all registered DiagnosticService instances
  - Advertises their VAS service IDs to the ISO 15118-20 ServiceDiscovery
  - Routes on_selected / on_cycle / on_end to whichever service is active
  - Writes the CurrentCommand back into evse_data_context so the existing
    send_charging_command() path works without modification

SimEVSEController never imports from services/ directly.
"""

import logging
from typing import Dict, Optional

from iso15118.shared.battery_diagnostics.base_service import (
    CurrentCommand,
    DiagnosticService,
)
from iso15118.shared.battery_diagnostics.battery_simulator import BatterySimulator
from iso15118.shared.messages.iso15118_20.common_messages import (
    ParameterSet,
    Service,
    ServiceList,
    ServiceParameterList,
)

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Holds all registered DiagnosticService instances and routes calls.

    Usage in SimEVSEController.__init__():

        from iso15118.shared.battery_diagnostics import ServiceRegistry, BatterySimulator
        from iso15118.shared.battery_diagnostics.services.health_test import BatteryHealthService

        self.service_registry = ServiceRegistry(
            battery=BatterySimulator()
        )
        self.service_registry.register(BatteryHealthService())
        # Add more: self.service_registry.register(EISService())
    """

    def __init__(self, battery: BatterySimulator):
        self._battery: BatterySimulator = battery
        self._services: Dict[int, DiagnosticService] = {}
        self._active: Optional[DiagnosticService] = None

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, service: DiagnosticService) -> None:
        """Register a DiagnosticService. Call once at startup per service."""
        self._services[service.SERVICE_ID] = service
        logger.info(
            f"[ServiceRegistry] Registered: {service.NAME} (id={service.SERVICE_ID})"
        )

    # ── Called by SimEVSEController ───────────────────────────────────────────

    def get_vas_list(self) -> Optional[ServiceList]:
        """
        Returns a ServiceList of all registered diagnostic VAS services.
        Called by SimEVSEController to include in ServiceDiscoveryRes.
        Returns None if no services are registered.
        """
        if not self._services:
            return None
        return ServiceList(
            services=[
                Service(service_id=sid, free_service=True)
                for sid in self._services
            ]
        )

    def get_parameter_list(self, service_id: int) -> Optional[ServiceParameterList]:
        """
        Returns ServiceParameterList for a given service_id.
        Called by SimEVSEController.get_service_parameter_list().
        Returns None if service_id is not a diagnostic service (energy service).
        """
        service = self._services.get(service_id)
        if service is None:
            return None
        return service.get_parameter_list()

    def on_service_selected(
        self, service_id: int, parameter_set: Optional[ParameterSet]
    ) -> None:
        """
        Called by check_selected_services() in iso15118_20_states.py
        when the EVCC selects a VAS.
        """
        service = self._services.get(service_id)
        if service is None:
            logger.warning(
                f"[ServiceRegistry] Unknown service_id={service_id} selected — ignored"
            )
            return
        self._active = service
        service.on_selected(parameter_set, self._battery)
        logger.info(
            f"[ServiceRegistry] Active service: {service.NAME} (id={service_id})"
        )

    def on_cycle(self, ev_data_context, evse_data_context) -> None:
        """
        Called every DC_ChargeLoop cycle from DCChargeLoop.process_message().

        1. Passes raw ev_data_context to active service → gets CurrentCommand
        2. Writes CurrentCommand into evse_data_context DC session limits so
           the existing send_charging_command() path picks it up unchanged.

        If no diagnostic service is active, does nothing.
        """
        if self._active is None:
            return

        cmd: CurrentCommand = self._active.on_cycle(ev_data_context, self._battery)

        # Write command into SECC session limits — existing infrastructure
        # reads these in get_dc_charge_loop_params_v20() / send_charging_command()
        dc_limits = evse_data_context.session_limits.dc_limits
        if cmd.target_current_a < 0:
            # Discharge — write into discharge current limit
            dc_limits.max_discharge_current = abs(cmd.target_current_a)
            dc_limits.max_discharge_power   = abs(
                cmd.target_current_a * cmd.target_voltage_v
            )
        else:
            # Charge
            dc_limits.max_charge_current = cmd.target_current_a
            dc_limits.max_charge_power   = cmd.target_current_a * cmd.target_voltage_v

        dc_limits.max_voltage = cmd.target_voltage_v

        logger.debug(
            f"[ServiceRegistry] Cycle cmd: {cmd.phase_label} "
            f"I={cmd.target_current_a:.1f}A V={cmd.target_voltage_v:.1f}V "
            f"complete={cmd.test_complete}"
        )

        # Signal test completion via evse_data_context flag so EVCC can read it
        evse_data_context.test_complete = cmd.test_complete

    def on_end(self) -> None:
        """
        Called by SimEVSEController.session_ended().
        Delegates to active service, then clears active.
        """
        if self._active is None:
            return
        logger.info(
            f"[ServiceRegistry] Session ended — finalising {self._active.NAME}"
        )
        self._active.on_end()
        self._active = None

    @property
    def is_active(self) -> bool:
        return self._active is not None
