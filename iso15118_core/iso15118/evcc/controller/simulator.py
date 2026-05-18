"""
iso15118/evcc/controller/simulator.py

Replaces the dummy SimEVController with a physics-based RealBatterySimulator.
The simulator integrates power over real wall-clock time to move SOC and derive
a SOC-dependent terminal voltage, giving realistic terminal-log output during
both ISO 15118-2 and ISO 15118-20 (AC / DC / BPT) sessions.

DIN SPEC 70121 methods raise NotImplementedError — they are out of scope for
this project.
"""

import logging
import random
import time
from typing import List, Optional, Tuple, Union

from iso15118.evcc import EVCCConfig
from iso15118.evcc.controller.interface import ChargeParamsV2, EVControllerInterface
from iso15118.shared.exceptions import InvalidProtocolError, MACAddressNotFound
from iso15118.shared.messages.datatypes import (
    DCEVChargeParams,
    PVEAmount,
    PVEVEnergyCapacity,
    PVEVEnergyRequest,
    PVEVMaxCurrent,
    PVEVMaxCurrentLimit,
    PVEVMaxPowerLimit,
    PVEVMaxVoltage,
    PVEVMaxVoltageLimit,
    PVEVMinCurrent,
    PVEVSEPresentVoltage,
    PVEVTargetCurrent,
    PVEVTargetVoltage,
    PVPMax,
    PVRemainingTimeToBulkSOC,
    PVRemainingTimeToFullSOC,
)
from iso15118.shared.messages.din_spec.datatypes import (
    DCEVPowerDeliveryParameter as DCEVPowerDeliveryParameterDINSPEC,
)
from iso15118.shared.messages.din_spec.datatypes import DCEVStatus as DCEVStatusDINSPEC
from iso15118.shared.messages.din_spec.datatypes import (
    SAScheduleTupleEntry as SAScheduleTupleEntryDINSPEC,
)
from iso15118.shared.messages.enums import (
    ControlMode,
    DCEVErrorCode,
    EnergyTransferModeEnum,
    Namespace,
    PriceAlgorithm,
    Protocol,
    ServiceV20,
    UnitSymbol,
)
from iso15118.shared.messages.iso15118_2.datatypes import (
    ACEVChargeParameter,
)
from iso15118.shared.messages.iso15118_2.datatypes import (
    ChargeProgress as ChargeProgressV2,
)
from iso15118.shared.messages.iso15118_2.datatypes import (
    ChargingProfile,
    DCEVChargeParameter,
    DCEVPowerDeliveryParameter,
    DCEVStatus,
    ProfileEntryDetails,
    SAScheduleTuple,
)
from iso15118.shared.messages.iso15118_20.ac import (
    ACChargeParameterDiscoveryReqParams,
    BPTACChargeParameterDiscoveryReqParams,
    BPTDynamicACChargeLoopReqParams,
    BPTScheduledACChargeLoopReqParams,
    DynamicACChargeLoopReqParams,
    ScheduledACChargeLoopReqParams,
)
from iso15118.shared.messages.iso15118_20.common_messages import (
    ChargeProgress as ChargeProgressV20,
)
from iso15118.shared.messages.iso15118_20.common_messages import (
    DynamicEVPowerProfile,
    DynamicScheduleExchangeReqParams,
    DynamicScheduleExchangeResParams,
    EMAIDList,
    EVAbsolutePriceSchedule,
    EVEnergyOffer,
    EVPowerProfile,
    EVPowerSchedule,
    EVPowerScheduleEntry,
    EVPowerScheduleEntryList,
    EVPriceRule,
    EVPriceRuleStack,
    EVPriceRuleStackList,
    MatchedService,
    PowerToleranceAcceptance,
    ScheduledEVPowerProfile,
    ScheduledScheduleExchangeReqParams,
    ScheduledScheduleExchangeResParams,
    SelectedEnergyService,
    SelectedVAS,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    DisplayParameters,
    RationalNumber,
)
from iso15118.shared.messages.iso15118_20.dc import (
    BPTDCChargeParameterDiscoveryReqParams,
    BPTDynamicDCChargeLoopReqParams,
    BPTScheduledDCChargeLoopReqParams,
    DCChargeParameterDiscoveryReqParams,
    DynamicDCChargeLoopReqParams,
    ScheduledDCChargeLoopReqParams,
)
from iso15118.shared.network import get_nic_mac_address

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper — encode a plain float voltage as a RationalNumber (integer watts /
# volts with exponent=0).  Rounds to the nearest integer so the XSD type is
# always satisfied.
# ---------------------------------------------------------------------------
def _rational(value_float: float, exponent: int = 0) -> RationalNumber:
    """Return a RationalNumber whose decimal value equals value_float * 10^exponent."""
    scaled = round(value_float / (10 ** exponent))
    return RationalNumber(exponent=exponent, value=int(scaled))


class RealBatterySimulator(EVControllerInterface):
    """
    Physics-based EV battery simulator.

    Replaces the static-increment dummy with a real energy-integration model:

        ΔE_Wh  = P_W × Δt_s / 3600
        SOC_new = SOC_old + (ΔE_Wh / capacity_Wh) × 100          (clamped 0–100)
        V       = V_min + (V_max − V_min) × SOC / 100

    Power is signed: positive = charging, negative = discharging (BPT).

    The small 2 kWh default capacity makes SOC changes visible in a short
    lab session without waiting for a real 60–100 kWh pack to budge.
    """

    # -----------------------------------------------------------------------
    # Construction
    # -----------------------------------------------------------------------
    def __init__(self, evcc_config: EVCCConfig):
        # ── Config (unchanged from SimEVController) ─────────────────────────
        self.config = evcc_config
        self.charge_loop_delay_time: int = min(evcc_config.charge_loop_delay_time, 50)

        # ── Battery parameters (tunable) ─────────────────────────────────────
        self.total_battery_capacity_wh: float = 2_00.0   # 0.2 kWh  → rapid SOC swing
        self.max_voltage: float = 450.0                    # V at 100 % SOC
        self.min_voltage: float = 300.0                    # V at   0 % SOC
        self.max_charge_current: float = 32.0              # A
        self.max_charge_power_w: float = 11_000.0          # W  (11 kW AC)

        # ── Live battery state ───────────────────────────────────────────────
        self._soc: float = 50.0                            # % — starting at 50 %
        self._current_power_w: float = self.max_charge_power_w  # W — default assumed
        self._last_update_time: float = time.time()

        # ── Session bookkeeping (preserved from SimEVController) ─────────────
        self._charging_is_completed: bool = False
        self.precharge_loop_cycles: int = 0
        self.welding_detection_cycles: int = 0


        #---
        self.target_soc: float = 80.0   # stop charging here
        self.bulk_soc: float = 70.0     # bulk complete threshold


        # ── ISO 15118-2 DC charge params (kept for protocol compatibility) ───
        self.dc_ev_charge_params: DCEVChargeParams = DCEVChargeParams(
            dc_max_current_limit=PVEVMaxCurrentLimit(
                multiplier=-3, value=32_000, unit=UnitSymbol.AMPERE
            ),
            dc_max_power_limit=PVEVMaxPowerLimit(
                multiplier=3, value=11, unit=UnitSymbol.WATT
            ),
            dc_max_voltage_limit=PVEVMaxVoltageLimit(
                multiplier=0, value=int(self.max_voltage), unit=UnitSymbol.VOLTAGE
            ),
            dc_energy_capacity=PVEVEnergyCapacity(
                multiplier=3, value=2, unit=UnitSymbol.WATT_HOURS
            ),
            dc_target_current=PVEVTargetCurrent(
                multiplier=0, value=20, unit=UnitSymbol.AMPERE
            ),
            dc_target_voltage=PVEVTargetVoltage(
                multiplier=0, value=400, unit=UnitSymbol.VOLTAGE
            ),
        )

        logger.info(
            "RealBatterySimulator initialised — "
            f"capacity={self.total_battery_capacity_wh:.0f} Wh, "
            f"SOC={self._soc:.1f} %, "
            f"V={self._compute_voltage():.1f} V"
        )

    # -----------------------------------------------------------------------
    # Physics engine
    # -----------------------------------------------------------------------
    def _compute_voltage(self) -> float:
        """Linear OCV approximation: V = V_min + (V_max − V_min) × SOC/100."""
        return self.min_voltage + (self.max_voltage - self.min_voltage) * (
            self._soc / 100.0
        )

    def update_battery_state(self, power_watts: float) -> None:
        """
        Integrate energy flow since the last call and update SOC + voltage.

        Call this from the EVCC state machine whenever the SECC delivers a new
        EVSEPresentActivePower value, or from continue_charging() for a
        cycle-by-cycle approximation.

        Args:
            power_watts: Signed power in watts.
                         Positive  → charging  (SOC rises).
                         Negative  → discharging / V2G (SOC falls).
        """
        now = time.time()
        delta_t_s: float = now - self._last_update_time
        self._last_update_time = now
        self._current_power_w = power_watts

        # Guard: skip tiny time steps that would cause numerical noise
        if delta_t_s < 0.01:
            return

        energy_wh: float = (power_watts * delta_t_s) / 3600.0
        delta_soc: float = (energy_wh / self.total_battery_capacity_wh) * 100.0

        old_soc = self._soc
        self._soc = max(0.0, min(100.0, self._soc + delta_soc))

        logger.info(
            f"[Battery] P={power_watts:+.0f} W  Δt={delta_t_s:.2f} s  "
            f"ΔE={energy_wh:+.4f} Wh  "
            f"SOC {old_soc:.2f}% → {self._soc:.2f}%  "
            f"V={self._compute_voltage():.1f} V"
        )

    def get_present_soc(self) -> float:
        """Return the current physics-integrated SOC percentage (0–100)."""
        return round(self._soc, 2)

    # -----------------------------------------------------------------------
    # EVControllerInterface — COMMON methods
    # -----------------------------------------------------------------------

    async def charge_loop_delay(self) -> int:
        """Overrides EVControllerInterface.charge_loop_delay()."""
        return self.charge_loop_delay_time

    async def get_evcc_id(self, protocol: Protocol, iface: str) -> str:
        """Overrides EVControllerInterface.get_evcc_id(). (Unchanged from SimEVController.)"""
        if protocol in (Protocol.ISO_15118_2, Protocol.DIN_SPEC_70121):
            try:
                hex_str = get_nic_mac_address(iface)
                return hex_str.replace(":", "").upper()
            except MACAddressNotFound as exc:
                logger.warning(
                    "Couldn't determine EVCCID (ISO 15118-2) — "
                    f"Reason: {exc}. Falling back to '000000000000'."
                )
                return "000000000000"
        elif protocol.ns.startswith(Namespace.ISO_V20_BASE):
            return "WMIV1234567890ABCDEX"
        else:
            logger.error(f"Invalid protocol '{protocol}', cannot determine EVCCID")
            raise InvalidProtocolError

    async def get_energy_transfer_mode(
        self, protocol: Protocol
    ) -> EnergyTransferModeEnum:
        """Overrides EVControllerInterface.get_energy_transfer_mode()."""
        return self.config.energy_transfer_mode

    async def get_supported_energy_services(self) -> List[ServiceV20]:
        """Overrides EVControllerInterface.get_supported_energy_services()."""
        return self.config.supported_energy_services

    async def select_energy_service_v20(
        self, services: List[MatchedService]
    ) -> SelectedEnergyService:
        """Overrides EVControllerInterface.select_energy_service_v20()."""
        top = services[0]
        return SelectedEnergyService(
            service=top.service,
            is_free=top.is_free,
            parameter_set=top.parameter_sets[0],
        )

    async def select_vas_services_v20(
        self, services: List[MatchedService]
    ) -> Optional[List[SelectedVAS]]:
        """Overrides EVControllerInterface.select_vas_services_v20()."""
        vas_only = [s for s in services if not s.is_energy_service]
        return [
            SelectedVAS(
                service=s.service,
                is_free=s.is_free,
                parameter_set=s.parameter_sets[0],
            )
            for s in vas_only
        ]

    async def get_scheduled_se_params(
        self, selected_energy_service: SelectedEnergyService
    ) -> ScheduledScheduleExchangeReqParams:
        """Overrides EVControllerInterface.get_scheduled_se_params()."""
        ev_price_rule = EVPriceRule(
            energy_fee=RationalNumber(exponent=0, value=0),
            power_range_start=RationalNumber(exponent=0, value=0),
        )
        ev_price_rule_stack = EVPriceRuleStack(
            duration=0, ev_price_rules=[ev_price_rule]
        )
        ev_price_rule_stack_list = EVPriceRuleStackList(
            ev_price_rule_stacks=[ev_price_rule_stack]
        )
        ev_absolute_price_schedule = EVAbsolutePriceSchedule(
            time_anchor=0,
            currency="EUR",
            price_algorithm=PriceAlgorithm.POWER,
            ev_price_rule_stacks=ev_price_rule_stack_list,
        )
        ev_power_schedule_entry = EVPowerScheduleEntry(
            duration=3600, power=RationalNumber(exponent=3, value=-10)
        )
        ev_power_schedule = EVPowerSchedule(
            time_anchor=0,
            ev_power_schedule_entries=EVPowerScheduleEntryList(
                entries=[ev_power_schedule_entry]
            ),
        )
        energy_offer = EVEnergyOffer(
            ev_power_schedule=ev_power_schedule,
            ev_absolute_price_schedule=ev_absolute_price_schedule,
        )
        return ScheduledScheduleExchangeReqParams(
            departure_time=7200,
            ev_target_energy_request=RationalNumber(exponent=3, value=10),
            ev_max_energy_request=RationalNumber(exponent=3, value=20),
            ev_min_energy_request=RationalNumber(exponent=-2, value=5),
            ev_energy_offer=energy_offer,
        )

    async def get_dynamic_se_params(
        self, selected_energy_service: SelectedEnergyService
    ) -> DynamicScheduleExchangeReqParams:
        """Overrides EVControllerInterface.get_dynamic_se_params()."""
        return DynamicScheduleExchangeReqParams(
            departure_time=7200,
            self.bulk_soc,
            self.target_soc,
            ev_target_energy_request=RationalNumber(exponent=3, value=40),
            ev_max_energy_request=RationalNumber(exponent=1, value=6000),
            ev_min_energy_request=RationalNumber(exponent=0, value=-20000),
            ev_max_v2x_energy_request=RationalNumber(exponent=0, value=5000),
            ev_min_v2x_energy_request=RationalNumber(exponent=0, value=0),
        )

    async def process_scheduled_se_params(
        self, scheduled_params: ScheduledScheduleExchangeResParams, pause: bool
    ) -> Tuple[Optional[EVPowerProfile], ChargeProgressV20]:
        """Overrides EVControllerInterface.process_scheduled_se_params()."""
        is_ready = bool(random.getrandbits(1))
        if not is_ready:
            logger.debug("Scheduled SE params not yet ready — signalling ONGOING")
            return None, ChargeProgressV20.START

        charge_progress = ChargeProgressV20.STOP if pause else ChargeProgressV20.START

        selected_schedule = scheduled_params.schedule_tuples[0]
        charging_entries = (
            selected_schedule.charging_schedule.power_schedule.schedule_entry_list.entries
        )

        ev_entries = [
            EVPowerScheduleEntry(duration=e.duration, power=e.power)
            for e in charging_entries
        ]

        scheduled_profile = ScheduledEVPowerProfile(
            selected_schedule_tuple_id=selected_schedule.schedule_tuple_id,
            power_tolerance_acceptance=PowerToleranceAcceptance.CONFIRMED,
        )
        ev_power_profile = EVPowerProfile(
            time_anchor=0,
            entry_list=EVPowerScheduleEntryList(entries=ev_entries),
            scheduled_profile=scheduled_profile,
        )
        return ev_power_profile, charge_progress

    async def process_dynamic_se_params(
        self, dynamic_params: DynamicScheduleExchangeResParams, pause: bool
    ) -> Tuple[Optional[EVPowerProfile], ChargeProgressV20]:
        """Overrides EVControllerInterface.process_dynamic_se_params()."""
        is_ready = bool(random.getrandbits(1))
        if not is_ready:
            logger.debug("Dynamic SE params not yet ready — signalling ONGOING")
            return None, ChargeProgressV20.START

        charge_progress = ChargeProgressV20.STOP if pause else ChargeProgressV20.START

        ev_power_profile = EVPowerProfile(
            time_anchor=0,
            entry_list=EVPowerScheduleEntryList(
                entries=[
                    EVPowerScheduleEntry(
                        duration=3600,
                        power=RationalNumber(exponent=3, value=11),
                    )
                ]
            ),
            dynamic_profile=DynamicEVPowerProfile(),
        )
        return ev_power_profile, charge_progress

    async def is_cert_install_needed(self) -> bool:
        """Overrides EVControllerInterface.is_cert_install_needed()."""
        return self.config.is_cert_install_needed

    # DIN SPEC — out of scope for this project
    async def process_sa_schedules_dinspec(
        self, sa_schedules: List[SAScheduleTupleEntryDINSPEC]
    ) -> int:
        raise NotImplementedError(
            "DIN SPEC 70121 is not supported by RealBatterySimulator"
        )

    async def process_sa_schedules_v2(
        self, sa_schedules: List[SAScheduleTuple]
    ) -> Tuple[ChargeProgressV2, int, ChargingProfile]:
        """Overrides EVControllerInterface.process_sa_schedules_v2()."""
        secc_schedule = sa_schedules.pop()
        evcc_profile_entry_list: List[ProfileEntryDetails] = []

        for entry in secc_schedule.p_max_schedule.schedule_entries:
            evcc_profile_entry_list.append(
                ProfileEntryDetails(
                    start=entry.time_interval.start,
                    max_power=entry.p_max,
                )
            )
            if entry.time_interval.duration:
                evcc_profile_entry_list.append(
                    ProfileEntryDetails(
                        start=entry.time_interval.start + entry.time_interval.duration,
                        max_power=PVPMax(multiplier=0, value=0, unit=UnitSymbol.WATT),
                    )
                )

        return (
            ChargeProgressV2.START,
            secc_schedule.sa_schedule_tuple_id,
            ChargingProfile(profile_entries=evcc_profile_entry_list),
        )

    async def continue_charging(self) -> bool:
        """
        Overrides EVControllerInterface.continue_charging().

        Integrates energy using the last known SECC power setpoint and returns
        False when SOC hits 100 % or stop_charging() has been called.
        """
        if self._charging_is_completed or await self.is_charging_complete():
            return False

        # Advance the battery state with whatever power is currently flowing.
        # The state machine may also call update_battery_state() directly with
        # EVSEPresentActivePower from the SECC response for higher accuracy.
        self.update_battery_state(self._current_power_w)
        return True

    async def store_contract_cert_and_priv_key(
        self, contract_cert: bytes, priv_key: bytes
    ) -> None:
        """Overrides EVControllerInterface.store_contract_cert_and_priv_key()."""
        # In production: push to HSM.  No-op here.
        pass

    async def get_prioritised_emaids(self) -> Optional[EMAIDList]:
        """Overrides EVControllerInterface.get_prioritised_emaids()."""
        return None

    async def ready_to_charge(self) -> bool:
        """Overrides EVControllerInterface.ready_to_charge()."""
        return await self.continue_charging()

    async def is_precharged(
        self, present_voltage_evse: Union[PVEVSEPresentVoltage, RationalNumber]
    ) -> bool:
        """Overrides EVControllerInterface.is_precharged()."""
        ev_voltage = (await self.get_present_voltage()).get_decimal_value()
        evse_voltage = present_voltage_evse.get_decimal_value()
        if self.precharge_loop_cycles >= 5 or evse_voltage == ev_voltage:
            logger.info(
                f"Precharge complete — EVSE={evse_voltage:.1f} V / EV={ev_voltage:.1f} V"
            )
            return True
        self.precharge_loop_cycles += 1
        return False

    async def is_charging_complete(self) -> bool:
        """Overrides EVControllerInterface.is_charging_complete()."""
        return self._soc >= self.target_soc or self._charging_is_completed

    async def is_bulk_charging_complete(self) -> bool:
        """Overrides EVControllerInterface.is_bulk_charging_complete()."""
        return self._soc >= self.bulk_soc

    async def get_remaining_time_to_full_soc(self) -> PVRemainingTimeToFullSOC:
        """
        Overrides EVControllerInterface.get_remaining_time_to_full_soc().

        Derived from current power and remaining energy gap:
            t_s = ((100 - SOC) / 100 × capacity_Wh) / P_W × 3600
        """
        remaining_energy_wh = (
            (100.0 - self._soc) / 100.0
        ) * self.total_battery_capacity_wh
        power = max(self._current_power_w, 1.0)          # avoid div/0
        remaining_s = int((remaining_energy_wh / power) * 3600.0)
        return PVRemainingTimeToFullSOC(multiplier=0, value=remaining_s, unit="s")

    async def get_remaining_time_to_bulk_soc(self) -> PVRemainingTimeToBulkSOC:
        """Overrides EVControllerInterface.get_remaining_time_to_bulk_soc()."""
        bulk_target = self.bulk_soc
        gap = max(0.0, bulk_target - self._soc)
        remaining_energy_wh = (gap / 100.0) * self.total_battery_capacity_wh
        power = max(self._current_power_w, 1.0)
        remaining_s = int((remaining_energy_wh / power) * 3600.0)
        return PVRemainingTimeToBulkSOC(multiplier=0, value=remaining_s, unit="s")

    async def welding_detection_has_finished(self) -> bool:
        """Overrides EVControllerInterface.welding_detection_has_finished()."""
        if self.welding_detection_cycles >= 3:
            return True
        self.welding_detection_cycles += 1
        return False

    async def stop_charging(self) -> None:
        """Overrides EVControllerInterface.stop_charging()."""
        logger.info(
            f"[Battery] stop_charging() called — final SOC={self._soc:.2f} %"
        )
        self._charging_is_completed = True

    async def enable_charging(self, enabled: bool) -> None:
        """Overrides EVControllerInterface.enable_charging()."""
        logger.debug(f"enable_charging({enabled})")

    async def get_display_params(self) -> DisplayParameters:
        """
        Overrides EVControllerInterface.get_display_params().

        Returns the live physics-calculated SOC and voltage so they appear in
        ISO 15118-20 DisplayParameters messages and terminal logs.
        """
        present_soc = int(round(self._soc))
        return DisplayParameters(
            present_soc=present_soc,
            min_soc=10,
            target_soc=int(self.target_soc),   # was hardcoded 80
            charging_complete=await self.is_charging_complete(),
        )

    # -----------------------------------------------------------------------
    # EVControllerInterface — CHARGE PARAMETER DISCOVERY
    # -----------------------------------------------------------------------

    async def get_charge_params_v2(self, protocol: Protocol) -> ChargeParamsV2:
        """Overrides EVControllerInterface.get_charge_params_v2()."""
        ac_charge_params = None
        dc_charge_params = None
        mode = await self.get_energy_transfer_mode(protocol)

        if str(mode).startswith("AC"):
            ac_charge_params = ACEVChargeParameter(
                departure_time=0,
                e_amount=PVEAmount(multiplier=0, value=60, unit=UnitSymbol.WATT_HOURS),
                ev_max_voltage=PVEVMaxVoltage(
                    multiplier=0, value=int(self.max_voltage), unit=UnitSymbol.VOLTAGE
                ),
                ev_max_current=PVEVMaxCurrent(
                    multiplier=-3,
                    value=int(self.max_charge_current * 1000),
                    unit=UnitSymbol.AMPERE,
                ),
                ev_min_current=PVEVMinCurrent(
                    multiplier=0, value=6, unit=UnitSymbol.AMPERE
                ),
            )
        else:
            ev_energy_request = PVEVEnergyRequest(
                multiplier=0,
                value=int(self.total_battery_capacity_wh),
                unit=UnitSymbol.WATT_HOURS,
            )
            dc_charge_params = DCEVChargeParameter(
                departure_time=0,
                dc_ev_status=await self.get_dc_ev_status(),
                ev_maximum_current_limit=self.dc_ev_charge_params.dc_max_current_limit,
                ev_maximum_power_limit=self.dc_ev_charge_params.dc_max_power_limit,
                ev_maximum_voltage_limit=self.dc_ev_charge_params.dc_max_voltage_limit,
                ev_energy_capacity=self.dc_ev_charge_params.dc_energy_capacity,
                ev_energy_request=ev_energy_request,
                self.target_soc,
                self.bulk_soc,
            )

        return ChargeParamsV2(mode, ac_charge_params, dc_charge_params)

    async def get_charge_params_v20(
        self, selected_service: SelectedEnergyService
    ) -> Union[
        ACChargeParameterDiscoveryReqParams,
        BPTACChargeParameterDiscoveryReqParams,
        DCChargeParameterDiscoveryReqParams,
        BPTDCChargeParameterDiscoveryReqParams,
    ]:
        """Overrides EVControllerInterface.get_charge_params_v20()."""
        ac_cpd = ACChargeParameterDiscoveryReqParams(
            ev_max_charge_power=RationalNumber(exponent=3, value=11),
            ev_min_charge_power=RationalNumber(exponent=0, value=100),
        )
        dc_cpd = DCChargeParameterDiscoveryReqParams(
            ev_max_charge_power=RationalNumber(exponent=3, value=11),
            ev_min_charge_power=RationalNumber(exponent=0, value=100),
            ev_max_charge_current=_rational(self.max_charge_current),
            ev_min_charge_current=RationalNumber(exponent=0, value=1),
            ev_max_voltage=_rational(self.max_voltage),
            ev_min_voltage=_rational(self.min_voltage),
        )

        if selected_service.service == ServiceV20.AC:
            return ac_cpd
        elif selected_service.service == ServiceV20.AC_BPT:
            return BPTACChargeParameterDiscoveryReqParams(
                **(ac_cpd.dict()),
                ev_max_discharge_power=RationalNumber(exponent=3, value=11),
                ev_min_discharge_power=RationalNumber(exponent=0, value=100),
            )
        elif selected_service.service == ServiceV20.DC:
            return dc_cpd
        elif selected_service.service == ServiceV20.DC_BPT:
            return BPTDCChargeParameterDiscoveryReqParams(
                **(dc_cpd.dict()),
                ev_max_discharge_power=RationalNumber(exponent=3, value=11),
                ev_min_discharge_power=RationalNumber(exponent=3, value=1),
                ev_max_discharge_current=RationalNumber(exponent=0, value=32),
                ev_min_discharge_current=RationalNumber(exponent=0, value=0),
            )
        else:
            logger.error(
                f"Energy transfer service {selected_service.service} not supported"
            )
            raise NotImplementedError

    # -----------------------------------------------------------------------
    # EVControllerInterface — AC CHARGE LOOP (ISO 15118-20)
    # -----------------------------------------------------------------------

    async def get_ac_charge_loop_params_v20(
        self, control_mode: ControlMode, selected_service: ServiceV20
    ) -> Union[
        ScheduledACChargeLoopReqParams,
        BPTScheduledACChargeLoopReqParams,
        DynamicACChargeLoopReqParams,
        BPTDynamicACChargeLoopReqParams,
    ]:
        """
        Overrides EVControllerInterface.get_ac_charge_loop_params_v20().

        Integrates the battery state on every charge loop tick so the
        ev_present_active_power field reflects the running physics.
        """
        # Each call to this method represents one charge-loop iteration,
        # so we advance the battery state with the current power.
        self.update_battery_state(self._current_power_w)

        present_power = _rational(self._current_power_w, exponent=3)

        if control_mode == ControlMode.SCHEDULED:
            scheduled_params = ScheduledACChargeLoopReqParams(
                ev_present_active_power=present_power,
            )
            if selected_service == ServiceV20.AC_BPT:
                return BPTScheduledACChargeLoopReqParams(**(scheduled_params.dict()))
            return scheduled_params
        else:
            # Dynamic mode
            remaining_energy_wh = (
                (100.0 - self._soc) / 100.0
            ) * self.total_battery_capacity_wh
            dynamic_params = DynamicACChargeLoopReqParams(
                departure_time=2000,
                ev_target_energy_request=_rational(remaining_energy_wh * 0.9, exponent=3),
                ev_max_energy_request=_rational(remaining_energy_wh, exponent=3),
                ev_min_energy_request=RationalNumber(exponent=0, value=0),
                ev_max_charge_power=_rational(self.max_charge_power_w, exponent=3),
                ev_min_charge_power=RationalNumber(exponent=0, value=100),
                ev_present_active_power=present_power,
                ev_present_reactive_power=RationalNumber(exponent=0, value=0),
            )
            if selected_service == ServiceV20.AC_BPT:
                return BPTDynamicACChargeLoopReqParams(
                    **(dynamic_params.dict()),
                    ev_max_discharge_power=_rational(self.max_charge_power_w, exponent=3),
                    ev_min_discharge_power=RationalNumber(exponent=0, value=100),
                )
            return dynamic_params

    # -----------------------------------------------------------------------
    # EVControllerInterface — DC CHARGE LOOP (ISO 15118-20)
    # -----------------------------------------------------------------------

    async def get_scheduled_dc_charge_loop_params(
        self,
    ) -> ScheduledDCChargeLoopReqParams:
        """Overrides EVControllerInterface.get_scheduled_dc_charge_loop_params()."""
        self.update_battery_state(self._current_power_w)
        voltage = self._compute_voltage()
        current = self._current_power_w / max(voltage, 1.0)
        return ScheduledDCChargeLoopReqParams(
            ev_target_current=_rational(current),
            ev_target_voltage=_rational(voltage),
        )

    async def get_dynamic_dc_charge_loop_params(self) -> DynamicDCChargeLoopReqParams:
        """Overrides EVControllerInterface.get_dynamic_dc_charge_loop_params()."""
        self.update_battery_state(self._current_power_w)
        voltage = self._compute_voltage()
        remaining_energy_wh = (
            (100.0 - self._soc) / 100.0
        ) * self.total_battery_capacity_wh
        return DynamicDCChargeLoopReqParams(
            ev_target_energy_request=_rational(remaining_energy_wh * 0.9, exponent=3),
            ev_max_energy_request=_rational(remaining_energy_wh, exponent=3),
            ev_min_energy_request=RationalNumber(exponent=0, value=0),
            ev_max_charge_power=_rational(self.max_charge_power_w, exponent=3),
            ev_min_charge_power=RationalNumber(exponent=0, value=100),
            ev_max_charge_current=_rational(self.max_charge_current),
            ev_max_voltage=_rational(self.max_voltage),
            ev_min_voltage=_rational(self.min_voltage),
        )

    async def get_bpt_scheduled_dc_charge_loop_params(
        self,
    ) -> BPTScheduledDCChargeLoopReqParams:
        """Overrides EVControllerInterface.get_bpt_scheduled_dc_charge_loop_params()."""
        base = (await self.get_scheduled_dc_charge_loop_params()).dict()
        return BPTScheduledDCChargeLoopReqParams(**base)

    async def get_bpt_dynamic_dc_charge_loop_params(
        self,
    ) -> BPTDynamicDCChargeLoopReqParams:
        """Overrides EVControllerInterface.get_bpt_dynamic_dc_charge_loop_params()."""
        base = (await self.get_dynamic_dc_charge_loop_params()).dict()
        return BPTDynamicDCChargeLoopReqParams(
            **base,
            ev_max_discharge_power=_rational(self.max_charge_power_w, exponent=3),
            ev_min_discharge_power=RationalNumber(exponent=0, value=100),
            ev_max_discharge_current=_rational(self.max_charge_current),
        )

    # -----------------------------------------------------------------------
    # EVControllerInterface — VOLTAGE / CURRENT
    # -----------------------------------------------------------------------

    async def get_present_voltage(self) -> RationalNumber:
        """
        Overrides EVControllerInterface.get_present_voltage().

        Returns the SOC-dependent OCV as a RationalNumber (exponent=0, integer volts).
        """
        voltage = self._compute_voltage()
        logger.debug(f"[Battery] present_voltage={voltage:.1f} V  SOC={self._soc:.2f}%")
        return _rational(voltage)

    async def get_target_voltage(self) -> RationalNumber:
        """Overrides EVControllerInterface.get_target_voltage()."""
        return _rational(self.max_voltage)

    # -----------------------------------------------------------------------
    # EVControllerInterface — DC STATUS (ISO 15118-2)
    # -----------------------------------------------------------------------

    async def get_dc_ev_status(self) -> DCEVStatus:
        """Overrides EVControllerInterface.get_dc_ev_status()."""
        return DCEVStatus(
            ev_ready=True,
            ev_error_code=DCEVErrorCode.NO_ERROR,
            ev_ress_soc=int(round(self._soc)),
        )

    async def get_dc_ev_power_delivery_parameter(self) -> DCEVPowerDeliveryParameter:
        """Overrides EVControllerInterface.get_dc_ev_power_delivery_parameter()."""
        return DCEVPowerDeliveryParameter(
            dc_ev_status=await self.get_dc_ev_status(),
            bulk_charging_complete=await self.is_bulk_charging_complete(),
            charging_complete=await self.is_charging_complete(),
        )

    async def get_dc_charge_params(self) -> DCEVChargeParams:
        """Overrides EVControllerInterface.get_dc_charge_params()."""
        return self.dc_ev_charge_params

    # -----------------------------------------------------------------------
    # EVControllerInterface — DIN SPEC (NOT SUPPORTED)
    # -----------------------------------------------------------------------

    async def get_dc_ev_status_dinspec(self) -> DCEVStatusDINSPEC:
        raise NotImplementedError(
            "DIN SPEC 70121 is not supported by RealBatterySimulator"
        )

    async def get_dc_ev_power_delivery_parameter_dinspec(
        self,
    ) -> DCEVPowerDeliveryParameterDINSPEC:
        raise NotImplementedError(
            "DIN SPEC 70121 is not supported by RealBatterySimulator"
        )
    
    # Backwards-compatibility alias
SimEVController = RealBatterySimulator