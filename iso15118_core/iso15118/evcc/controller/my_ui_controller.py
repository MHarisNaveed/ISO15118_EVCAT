"""
Custom EV Controller with UI control via JSON file
No modifications to original simulator.py needed!
"""
from iso15118.shared.messages.enums import Namespace
from iso15118.shared.messages.enums import (
    ControlMode,
    DCEVErrorCode,
    EnergyTransferModeEnum,
    Namespace,  # ADD THIS
    Protocol,
    ServiceV20,
    UnitSymbol,
)

import json
import logging
from typing import List, Optional, Tuple, Union

from iso15118.evcc import EVCCConfig
from iso15118.evcc.controller.interface import ChargeParamsV2, EVControllerInterface
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
from iso15118.shared.messages.enums import (
    ControlMode,
    DCEVErrorCode,
    EnergyTransferModeEnum,
    Protocol,
    ServiceV20,
    UnitSymbol,
)
from iso15118.shared.messages.iso15118_2.datatypes import (
    ACEVChargeParameter,
    ChargeProgress as ChargeProgressV2,
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

logger = logging.getLogger(__name__)

# File for UI values - can be changed by your web UI
UI_JSON_FILE = "/tmp/ev_ui_values.json"


class MyUIController(EVControllerInterface):
    """
    Custom EV Controller that reads values from UI JSON file.
    This completely replaces the original simulator.
    """
    
    def __init__(self, evcc_config: EVCCConfig):
        self.config = evcc_config
        self._soc = 10
        self._charging_is_completed = False
        self._load_ui_values()
        
        print("\n" + "="*60)
        print("🎮 MyUIController ACTIVE - UI control enabled!")
        print(f"📁 UI values file: {UI_JSON_FILE}")
        print("="*60 + "\n")
    
    def _load_ui_values(self):
        """Load values from UI JSON file"""
        try:
            with open(UI_JSON_FILE, 'r') as f:
                self.ui_values = json.load(f)
                new_soc = self.ui_values.get("soc", self._soc)
                if new_soc != self._soc:
                    self._soc = new_soc
                    print(f"📊 UI: SOC updated to {self._soc}%")
        except (FileNotFoundError, json.JSONDecodeError):
            # Default values
            self.ui_values = {
                "soc": 10,
                "target_soc": 80,
                "departure_time_hours": 2,
                "max_current": 200,
                "max_power": 50,
                "bpt_enabled": False
            }
    
    def _get_ui_value(self, key, default):
        """Get a value from UI or return default"""
        self._load_ui_values()
        return self.ui_values.get(key, default)
    
    # ========== REQUIRED INTERFACE METHODS ==========
    
    async def get_evcc_id(self, protocol: Protocol, iface: str) -> str:
        """Return EVCC ID - must be exactly 12 hex characters for ISO 15118-20"""
        # EVCCID must be max 12 characters (hexadecimal)
        # Here's a valid 12-character hex string
        if protocol.ns.startswith(Namespace.ISO_V20_BASE):
            return "A1B2C3D4E5F6"  # Exactly 12 hex chars
        else:
            # For older protocols, return MAC address format
            return "A1B2C3D4E5F6"
    
    async def get_energy_transfer_mode(self, protocol: Protocol) -> EnergyTransferModeEnum:
        """Return energy transfer mode"""
        return self.config.energy_transfer_mode
    
    async def get_supported_energy_services(self) -> List[ServiceV20]:
        """Return supported services"""
        return self.config.supported_energy_services
    
    async def select_energy_service_v20(self, services: List[MatchedService]) -> SelectedEnergyService:
        """Select first available service"""
        top_of_list: MatchedService = services[0]
        return SelectedEnergyService(
            service=top_of_list.service,
            is_free=top_of_list.is_free,
            parameter_set=top_of_list.parameter_sets[0],
        )
    
    async def select_vas_services_v20(self, services: List[MatchedService]) -> Optional[List[SelectedVAS]]:
        """Select VAS services"""
        matched_vas_services = [s for s in services if not s.is_energy_service]
        selected_vas_services: List[SelectedVAS] = []
        for vas_service in matched_vas_services:
            selected_vas_services.append(
                SelectedVAS(
                    service=vas_service.service,
                    is_free=vas_service.is_free,
                    parameter_set=vas_service.parameter_sets[0],
                )
            )
        return selected_vas_services
    
    async def get_charge_params_v2(self, protocol: Protocol) -> ChargeParamsV2:
        """Get charge parameters for V2"""
        # Simple implementation
        dc_charge_params = DCEVChargeParameter(
            departure_time=0,
            dc_ev_status=await self.get_dc_ev_status(),
            ev_maximum_current_limit=PVEVMaxCurrentLimit(
                multiplier=-3, value=32000, unit=UnitSymbol.AMPERE
            ),
            ev_maximum_power_limit=PVEVMaxPowerLimit(
                multiplier=1, value=8000, unit=UnitSymbol.WATT
            ),
            ev_maximum_voltage_limit=PVEVMaxVoltageLimit(
                multiplier=1, value=50, unit=UnitSymbol.VOLTAGE
            ),
            ev_energy_capacity=PVEVEnergyCapacity(
                multiplier=1, value=7000, unit=UnitSymbol.WATT_HOURS
            ),
            ev_energy_request=PVEVEnergyRequest(
                multiplier=1, value=6000, unit=UnitSymbol.WATT_HOURS
            ),
            full_soc=90,
            bulk_soc=80,
        )
        return ChargeParamsV2(
            await self.get_energy_transfer_mode(protocol),
            None,  # AC params
            dc_charge_params,
        )
    
    async def get_charge_params_v20(self, selected_service: SelectedEnergyService) -> Union[
        ACChargeParameterDiscoveryReqParams,
        BPTACChargeParameterDiscoveryReqParams,
        DCChargeParameterDiscoveryReqParams,
        BPTDCChargeParameterDiscoveryReqParams,
    ]:
        """Get charge parameters for V20"""
        return DCChargeParameterDiscoveryReqParams(
            ev_max_charge_power=RationalNumber(exponent=3, value=300),
            ev_min_charge_power=RationalNumber(exponent=0, value=100),
            ev_max_charge_current=RationalNumber(exponent=0, value=300),
            ev_min_charge_current=RationalNumber(exponent=0, value=10),
            ev_max_voltage=RationalNumber(exponent=0, value=1000),
            ev_min_voltage=RationalNumber(exponent=0, value=10),
        )
    
    async def get_scheduled_se_params(self, selected_energy_service: SelectedEnergyService) -> ScheduledScheduleExchangeReqParams:
        """Get scheduled parameters"""
        return ScheduledScheduleExchangeReqParams(
            departure_time=7200,
            ev_target_energy_request=RationalNumber(exponent=3, value=10),
            ev_max_energy_request=RationalNumber(exponent=3, value=20),
            ev_min_energy_request=RationalNumber(exponent=-2, value=5),
            ev_energy_offer=None,
        )
    
    async def get_dynamic_se_params(self, selected_energy_service: SelectedEnergyService) -> DynamicScheduleExchangeReqParams:
        """Get dynamic parameters"""
        return DynamicScheduleExchangeReqParams(
            departure_time=7200,
            min_soc=30,
            target_soc=80,
            ev_target_energy_request=RationalNumber(exponent=3, value=40),
            ev_max_energy_request=RationalNumber(exponent=1, value=6000),
            ev_min_energy_request=RationalNumber(exponent=0, value=-20000),
            ev_max_v2x_energy_request=RationalNumber(exponent=0, value=5000),
            ev_min_v2x_energy_request=RationalNumber(exponent=0, value=0),
        )
    
    async def process_scheduled_se_params(
        self, scheduled_params: ScheduledScheduleExchangeResParams, pause: bool
    ) -> Tuple[Optional[EVPowerProfile], ChargeProgressV20]:
        """Process scheduled parameters - CREATE PROPER POWER PROFILE"""
        
        # Get the selected schedule
        selected_schedule = scheduled_params.schedule_tuples[0]
        
        # Create power profile entries from the schedule
        ev_power_schedule_entries = []
        
        # Get the power schedule entries from the charging schedule
        power_schedule = selected_schedule.charging_schedule.power_schedule
        for entry in power_schedule.schedule_entry_list.entries:
            ev_power_schedule_entry = EVPowerScheduleEntry(
                duration=entry.duration,
                power=entry.power
            )
            ev_power_schedule_entries.append(ev_power_schedule_entry)
        
        # Create the entry list
        entry_list = EVPowerScheduleEntryList(entries=ev_power_schedule_entries)
        
        # Create the power profile
        ev_power_profile = EVPowerProfile(
            time_anchor=power_schedule.time_anchor,
            entry_list=entry_list,
            scheduled_profile=ScheduledEVPowerProfile(
                selected_schedule_tuple_id=selected_schedule.schedule_tuple_id,
                power_tolerance_acceptance=PowerToleranceAcceptance.CONFIRMED,
            ),
        )
        
        charge_progress = ChargeProgressV20.STOP if pause else ChargeProgressV20.START
        
        return ev_power_profile, charge_progress

    
    async def process_dynamic_se_params(
        self, dynamic_params: DynamicScheduleExchangeResParams, pause: bool
    ) -> Tuple[Optional[EVPowerProfile], ChargeProgressV20]:
        """Process dynamic parameters - CREATE PROPER POWER PROFILE"""
        
        # Create a simple power profile for dynamic mode
        ev_power_schedule_entry = EVPowerScheduleEntry(
            duration=3600,
            power=RationalNumber(exponent=3, value=10)  # 10 kW
        )
        
        entry_list = EVPowerScheduleEntryList(entries=[ev_power_schedule_entry])
        
        ev_power_profile = EVPowerProfile(
            time_anchor=0,
            entry_list=entry_list,
            dynamic_profile=DynamicEVPowerProfile(),
        )
        
        charge_progress = ChargeProgressV20.STOP if pause else ChargeProgressV20.START
        
        return ev_power_profile, charge_progress
    
    async def is_cert_install_needed(self) -> bool:
        return self.config.is_cert_install_needed
    
    async def process_sa_schedules_dinspec(self, sa_schedules) -> int:
        return 1
    
    async def process_sa_schedules_v2(self, sa_schedules: List[SAScheduleTuple]) -> Tuple[ChargeProgressV2, int, ChargingProfile]:
        secc_schedule = sa_schedules.pop()
        return ChargeProgressV2.START, secc_schedule.sa_schedule_tuple_id, ChargingProfile(profile_entries=[])
    
    async def charge_loop_delay(self) -> int:
        return 0
    
    async def continue_charging(self) -> bool:
        """Check if charging should continue"""
        self._load_ui_values()
        target_soc = self.ui_values.get("target_soc", 80)
        if self._soc >= target_soc or self._soc >= 100:
            return False
        self._soc += 10  # Increment by 10% each cycle
        if self._soc > 100:
            self._soc = 100
        return True
    
    async def store_contract_cert_and_priv_key(self, contract_cert: bytes, priv_key: bytes):
        pass
    
    async def get_prioritised_emaids(self) -> Optional[EMAIDList]:
        return None
    
    async def ready_to_charge(self) -> bool:
        return True
    
    async def is_precharged(self, present_voltage_evse) -> bool:
        return True
    
    async def get_dc_ev_power_delivery_parameter_dinspec(self):
        pass
    
    async def get_dc_ev_power_delivery_parameter(self) -> DCEVPowerDeliveryParameter:
        return DCEVPowerDeliveryParameter(
            dc_ev_status=await self.get_dc_ev_status(),
            bulk_charging_complete=False,
            charging_complete=not await self.continue_charging(),
        )
    
    async def is_bulk_charging_complete(self) -> bool:
        return False
    
    async def is_charging_complete(self) -> bool:
        return not await self.continue_charging()
    
    async def get_remaining_time_to_full_soc(self) -> PVRemainingTimeToFullSOC:
        return PVRemainingTimeToFullSOC(multiplier=0, value=100, unit="s")
    
    async def get_remaining_time_to_bulk_soc(self) -> PVRemainingTimeToBulkSOC:
        return PVRemainingTimeToBulkSOC(multiplier=0, value=80, unit="s")
    
    async def welding_detection_has_finished(self):
        return True
    
    async def stop_charging(self) -> None:
        self._charging_is_completed = True
    
    # ========== DC-SPECIFIC METHODS ==========
    
    async def get_dc_charge_params(self) -> DCEVChargeParams:
        """Get DC charge parameters with UI values"""
        max_current = self._get_ui_value("max_current", 200)
        max_power = self._get_ui_value("max_power", 50) * 1000  # kW to W
        
        return DCEVChargeParams(
            dc_max_current_limit=PVEVMaxCurrentLimit(
                multiplier=0, value=max_current, unit=UnitSymbol.AMPERE
            ),
            dc_max_power_limit=PVEVMaxPowerLimit(
                multiplier=3, value=int(max_power/1000), unit=UnitSymbol.WATT
            ),
            dc_max_voltage_limit=PVEVMaxVoltageLimit(
                multiplier=1, value=50, unit=UnitSymbol.VOLTAGE
            ),
            dc_energy_capacity=PVEVEnergyCapacity(
                multiplier=1, value=7000, unit=UnitSymbol.WATT_HOURS
            ),
            dc_target_current=PVEVTargetCurrent(
                multiplier=0, value=1, unit=UnitSymbol.AMPERE
            ),
            dc_target_voltage=PVEVTargetVoltage(
                multiplier=1, value=50, unit=UnitSymbol.VOLTAGE
            ),
        )
    
    async def get_dc_ev_status_dinspec(self) -> DCEVStatusDINSPEC:
        self._load_ui_values()
        return DCEVStatusDINSPEC(
            ev_ready=True,
            ev_error_code=DCEVErrorCode.NO_ERROR,
            ev_ress_soc=self._soc,
        )
    
    async def get_dc_ev_status(self) -> DCEVStatus:
        self._load_ui_values()
        print(f"🔋 Current SOC: {self._soc}% (Target: {self.ui_values.get('target_soc', 80)}%)")
        return DCEVStatus(
            ev_ready=True,
            ev_error_code=DCEVErrorCode.NO_ERROR,
            ev_ress_soc=self._soc,
        )
    
    async def get_display_params(self) -> DisplayParameters:
        self._load_ui_values()
        return DisplayParameters(
            present_soc=self._soc,
            charging_complete=await self.is_charging_complete(),
        )
    
    # Other required methods (simplified)
    async def get_scheduled_dc_charge_loop_params(self) -> ScheduledDCChargeLoopReqParams:
        return ScheduledDCChargeLoopReqParams(
            ev_target_current=RationalNumber(exponent=1, value=20),
            ev_target_voltage=RationalNumber(exponent=1, value=20),
        )
    
    async def get_dynamic_dc_charge_loop_params(self) -> DynamicDCChargeLoopReqParams:
        return DynamicDCChargeLoopReqParams(
            ev_target_energy_request=RationalNumber(exponent=1, value=20),
            ev_max_energy_request=RationalNumber(exponent=1, value=20),
            ev_min_energy_request=RationalNumber(exponent=0, value=20),
            ev_max_charge_power=RationalNumber(exponent=2, value=40),
            ev_min_charge_power=RationalNumber(exponent=1, value=40),
            ev_max_charge_current=RationalNumber(exponent=0, value=40),
            ev_max_voltage=RationalNumber(exponent=1, value=40),
            ev_min_voltage=RationalNumber(exponent=0, value=40),
        )
    
    async def get_bpt_scheduled_dc_charge_loop_params(self) -> BPTScheduledDCChargeLoopReqParams:
        return BPTScheduledDCChargeLoopReqParams(
            ev_target_current=RationalNumber(exponent=1, value=20),
            ev_target_voltage=RationalNumber(exponent=1, value=20),
        )
    
    async def get_bpt_dynamic_dc_charge_loop_params(self) -> BPTDynamicDCChargeLoopReqParams:
        return BPTDynamicDCChargeLoopReqParams(
            ev_target_energy_request=RationalNumber(exponent=1, value=20),
            ev_max_energy_request=RationalNumber(exponent=1, value=20),
            ev_min_energy_request=RationalNumber(exponent=0, value=20),
            ev_max_charge_power=RationalNumber(exponent=2, value=40),
            ev_min_charge_power=RationalNumber(exponent=1, value=40),
            ev_max_charge_current=RationalNumber(exponent=0, value=40),
            ev_max_voltage=RationalNumber(exponent=1, value=40),
            ev_min_voltage=RationalNumber(exponent=0, value=40),
            ev_max_discharge_power=RationalNumber(exponent=3, value=300),
            ev_min_discharge_power=RationalNumber(exponent=3, value=300),
            ev_max_discharge_current=RationalNumber(exponent=3, value=300),
        )
    
    async def get_present_voltage(self) -> RationalNumber:
        return RationalNumber(exponent=3, value=20)
    
    async def get_target_voltage(self) -> RationalNumber:
        return RationalNumber(exponent=3, value=20)
    
    async def enable_charging(self, enabled: bool) -> None:
        pass
    
    async def get_ac_charge_loop_params_v20(self, control_mode: ControlMode, selected_service: ServiceV20):
        return ScheduledACChargeLoopReqParams(
            ev_present_active_power=RationalNumber(exponent=3, value=200),
        )