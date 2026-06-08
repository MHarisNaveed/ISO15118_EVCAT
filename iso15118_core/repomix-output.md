This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: iso15118/evcc/controller/simulator.py, iso15118/secc/controller/simulator.py, iso15118/secc/states/iso15118_20_states.py, iso15118/evcc/states/iso15118_20_states.py, iso15118/secc/controller/interface.py, iso15118/evcc/controller/interface.py, iso15118/shared/messages/iso15118_20/dc.py, iso15118/shared/messages/iso15118_20/common_messages.py
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
iso15118/evcc/controller/interface.py
iso15118/evcc/controller/simulator.py
iso15118/evcc/states/iso15118_20_states.py
iso15118/secc/controller/interface.py
iso15118/secc/controller/simulator.py
iso15118/secc/states/iso15118_20_states.py
iso15118/shared/messages/iso15118_20/common_messages.py
iso15118/shared/messages/iso15118_20/dc.py
```

# Files

## File: iso15118/evcc/controller/interface.py
```python
"""
This module contains the abstract class for an EVCC to retrieve data from the EV.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from iso15118.shared.messages.datatypes import (
    DCEVChargeParams,
    PVEVSEPresentVoltage,
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
from iso15118.shared.messages.enums import ControlMode, Protocol, ServiceV20
from iso15118.shared.messages.iso15118_2.datatypes import (
    ACEVChargeParameter,
    ChargeProgress,
    ChargingProfile,
    DCEVChargeParameter,
    DCEVPowerDeliveryParameter,
    DCEVStatus,
    EnergyTransferModeEnum,
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
    DynamicScheduleExchangeReqParams,
    DynamicScheduleExchangeResParams,
    EMAIDList,
    EVPowerProfile,
    MatchedService,
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


@dataclass
class ChargeParamsV2:
    energy_mode: EnergyTransferModeEnum
    ac_parameters: Optional[ACEVChargeParameter]
    dc_parameters: Optional[DCEVChargeParameter]


class EVControllerInterface(ABC):
    # ============================================================================
    # |             COMMON FUNCTIONS (FOR ALL ENERGY TRANSFER MODES)             |
    # ============================================================================
    @abstractmethod
    async def charge_loop_delay(self) -> int:
        """
        Delays the charging loop for a certain amount of time. This could be used
        for example to simulate a delay in the charging process, e.g. due to a
        temporary lack of power.

        Returns:
            The amount of time the charging loop was delayed in seconds

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_evcc_id(self, protocol: Protocol, iface: str) -> str:
        """
        Retrieves the EVCCID, which is a field of the SessionSetupReq. The structure of
        the EVCCID depends on the protocol version. In DIN SPEC 70121 and ISO 15118-2,
        the EVCCID is the MAC address (given as hexadecimal bytes), in ISO 15118-20 it's
        similar to a VIN (Vehicle Identification Number, given as str).

        Args:
            protocol: The communication protocol, a member of the Protocol enum
            iface (str): The network interface selected

        Raises:
            InvalidProtocolError

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_energy_transfer_mode(
        self, protocol: Protocol
    ) -> EnergyTransferModeEnum:
        """
        Gets the energy transfer mode requested for the current charging session.
        This depends on the charging cable being plugged in, which could be a
        Type 2 AC or Combo 2 plug, for example.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        """
        raise NotImplementedError

    async def get_supported_energy_services(self) -> List[ServiceV20]:
        """
        Gets the energy transfer service requested for the current charging session.
        This must be one of the energy related services (services with ID 1 through 7)

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def select_energy_service_v20(
        self, services: List[MatchedService]
    ) -> SelectedEnergyService:
        """
        Selects the energy service and associated parameter set from a given set of
        parameters per energy service ID.

        Args:
            services: List of compatible energy services offered by EVSE

        Returns:
            An instance of SelectedEnergyService, containing the service, whether it's
            free or paid, and its chosen parameter set.

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def select_vas_services_v20(
        self, services: List[MatchedService]
    ) -> Optional[List[SelectedVAS]]:
        """
        Selects a value-added service (VAS) and associated parameter set from a given
        set of parameters for that value-added energy. If you don't want to select
        the offered VAS, return None.

        Args:
            services: List of matched services

        Returns:
            A list of SelectedVAS, containing the service, whether it's free or
            paid, and its chosen parameter set.

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_scheduled_se_params(
        self, selected_energy_service: SelectedEnergyService
    ) -> ScheduledScheduleExchangeReqParams:
        """
        Gets the parameters for a ScheduleExchangeRequest, which correspond to the
        Scheduled control mode.

        Args:
            selected_energy_service: The energy services, which the EVCC selected.
                                     The selected parameter set, that is associated
                                     with that energy service, influences the
                                     parameters for the ScheduleExchangeReq

        Returns:
            Parameters for the ScheduleExchangeReq in Scheduled control mode

        Relevant for:
        - ISO 15118-20
        """

    @abstractmethod
    async def get_dynamic_se_params(
        self, selected_energy_service: SelectedEnergyService
    ) -> DynamicScheduleExchangeReqParams:
        """
        Gets the parameters for a ScheduleExchangeRequest, which correspond to the
        Dynamic control mode.

        Args:
            selected_energy_service: The energy services, which the EVCC selected.
                                     The selected parameter set, that is associated
                                     with that energy service, influences the
                                     parameters for the ScheduleExchangeReq

        Returns:
            Parameters for the ScheduleExchangeReq in Dynamic control mode

        Relevant for:
        - ISO 15118-20
        """

    @abstractmethod
    async def process_scheduled_se_params(
        self, scheduled_params: ScheduledScheduleExchangeResParams, pause: bool
    ) -> Tuple[Optional[EVPowerProfile], ChargeProgressV20]:
        """
        Processes the ScheduleExchangeRes parameters for the Scheduled mode.

        Args:
            scheduled_params: The list of offered schedule tuples for Scheduled mode
            pause: When set to True, this indicates that the EVSE doesn’t have any power
                   available and the EV should set ChargeProgress to PAUSE

        Returns:
            A tuple consisting of
            1. the resulting charging profile of the EV (or None, if not yet ready)
            1. the ChargeProgress status
            needed to create the PowerDeliveryReq message

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def process_dynamic_se_params(
        self, dynamic_params: DynamicScheduleExchangeResParams, pause: bool
    ) -> Tuple[Optional[EVPowerProfile], ChargeProgressV20]:
        """
        Processes the ScheduleExchangeRes parameters for the Dynamic mode.

        Args:
            dynamic_params: The parameters relevant for the Dynamic mode
            pause: When set to True, this indicates that the EVSE doesn’t have any power
                   available and the EV should set ChargeProgress to PAUSE

        Returns:
            A tuple consisting of
            1. the resulting charging profile of the EV (or None, if not yet ready)
            1. the ChargeProgress status
            needed to create the PowerDeliveryReq message

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def is_cert_install_needed(self) -> bool:
        """
        Returns True if the installation of a contract certificate is needed, False
        otherwise. A certificate installation is needed if the authorization option
        'Contract' (Plug & Charge) is chosen but no valid contract certificate is
        currently installed. An EV manufacturer might also choose to use the
        certificate installation process instead of a certificate update process
        available in ISO 15118-2 as there's no benefit of using the
        CertificateUpdateReq instead of the CertificateInstallationReq message.
        For example, you might want to choose to do a contract certificate
        installation if a certificate is about to expire (e.g. in two weeks).

        Relevant for:
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def process_sa_schedules_dinspec(
        self, sa_schedules: List[SAScheduleTupleEntryDINSPEC]
    ) -> int:
        """
        Processes the SAScheduleList provided with the ChargeParameterDiscoveryRes
        to decide which of the offered schedules to choose and whether or not to
        start charging instantly (ChargeProgress=Start) or to delay the charging
        process (ChargeProgress=Stop), including information on how the EV's
        charging profile will look like.

        Args:
            sa_schedules: The list of offered charging profiles (SAScheduleTuple
                          elements), each of which contains a mandatory PMaxSchedule
                          and an optional SalesTariff

        Returns the ID of the chosen charging schedule

        Relevant for:
        - DIN SPEC 70121
        """
        raise NotImplementedError

    @abstractmethod
    async def process_sa_schedules_v2(
        self, sa_schedules: List[SAScheduleTuple]
    ) -> Tuple[ChargeProgress, int, ChargingProfile]:
        """
        Processes the SAScheduleList provided with the ChargeParameterDiscoveryRes
        to decide which of the offered schedules to choose and whether or not to
        start charging instantly (ChargeProgress=Start) or to delay the charging
        process (ChargeProgress=Stop), including information on how the EV's
        charging profile will look like.

        Args:
            sa_schedules: The list of offered charging profiles (SAScheduleTuple
                          elements), each of which contains a mandatory PMaxSchedule
                          and an optional SalesTariff

        Returns:
            A tuple consisting of
            1. the ChargeProgress status,
            2. the ID of the chosen charging schedule (SAScheduleTuple), and
            3. the resulting charging profile of the EV, which may follow the
               suggestion of the offered charging schedule exactly or deviate
               (consume less power, but never more than the max limit provided by
               the SECC).

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def continue_charging(self) -> bool:
        """
        Whether or not to continue the energy flow during the charging loop. This
        depends on factors like SOC or user interaction with the vehicle (e.g. opened
        doors). If True, the charging loop continues.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def store_contract_cert_and_priv_key(
        self, contract_cert: bytes, priv_key: bytes
    ):
        """
        Stores the contract certificate and associated private key, both needed
        for Plug & Charge and received via a CertificateInstallationRes.
        This is a mockup, but a real EV should interact with a hardware security
        module (HSM) on a productive environment.

        Relevant for:
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_prioritised_emaids(self) -> Optional[EMAIDList]:
        """
        Indicates the list of EMAIDs (E-Mobility Account IDs) referencing contract
        certificates that shall be installed into the EV. The EMAIDs are given in
        the order of priority from highest priority to lowest priority.
        The secondary actor (e.g. Contract Certificate Pool operator, see the spec
        VDE-AR-E 2802-100-1, implemented by e.g. Hubject) will use this parameter to
        filter the list of contract certificates to be installed in case
        MaximumContractCertificateChains (a parameter the EVCC sends in
        CertificateInstallationReq) is smaller than the number of contract
        certificates available and ensures that the EV gets the highest priority
        contract certificates it desires.

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dc_ev_status_dinspec(self) -> DCEVStatusDINSPEC:
        """
        Gets the DC-specific EV Status information.

        Relevant for:
        - DIN SPEC 70121
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dc_ev_status(self) -> DCEVStatus:
        """
        Gets the DC-specific EV Status information.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def is_precharged(
        self, present_voltage_evse: Union[PVEVSEPresentVoltage, RationalNumber]
    ) -> bool:
        """
        Return True if the output voltage of the EVSE has reached
        the requested precharge voltage. Otherwise return False.
        According 61851-23

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_charge_params_v2(self, protocol: Protocol) -> ChargeParamsV2:
        """
        Gets the charge parameter needed for ChargeParameterDiscoveryReq (ISO 15118-2),
        including the energy transfer mode and the energy mode-specific parameters,
        which is an instance of either ACEVChargeParameter.

        Returns:
            A tuple of ChargeParamsV2, including EnergyTransferMode and
            ACEVChargeParameter

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_charge_params_v20(
        self, selected_service: SelectedEnergyService
    ) -> Union[
        ACChargeParameterDiscoveryReqParams,
        BPTACChargeParameterDiscoveryReqParams,
        DCChargeParameterDiscoveryReqParams,
        BPTDCChargeParameterDiscoveryReqParams,
    ]:
        """
        Gets the charge parameter needed for
        ACChargeParameterDiscovery/DCChargeParameterDiscovery (ISO 15118-20).
        Returns:
            One of [ACChargeParameterDiscoveryReqParams,
            BPTACChargeParameterDiscoveryReqParams,
            DCChargeParameterDiscoveryReqParams,
            BPTDCChargeParameterDiscoveryReqParams]
            based on the currently selected service.

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def ready_to_charge(self) -> bool:
        """
        Used by PowerDeliveryReq message (DIN SPEC) to indicate if we are
        ready to start/stop charging.
        """
        raise NotImplementedError

    @abstractmethod
    async def is_charging_complete(self) -> bool:
        """
        If set to True, the EV indicates that full charge (100% SOC) is complete.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20

        """
        raise NotImplementedError

    @abstractmethod
    async def is_bulk_charging_complete(self) -> bool:
        """
        Returns True if the soc for bulk charging is reached

        Relevant for:
        - DIN SPEC 70121 ??
        - ISO 15118-2
        - ISO 15118-20 ??
        """
        raise NotImplementedError

    @abstractmethod
    async def get_remaining_time_to_full_soc(self) -> PVRemainingTimeToFullSOC:
        """
        Gets the remaining time until full soc is reached.

        Relevant for:
        - DIN SPEC 70121 ??
        - ISO 15118-2
        - ISO 15118-20 ??
        """
        raise NotImplementedError

    @abstractmethod
    async def get_ac_charge_loop_params_v20(
        self, control_mode: ControlMode, selected_service: ServiceV20
    ) -> Union[
        ScheduledACChargeLoopReqParams,
        BPTScheduledACChargeLoopReqParams,
        DynamicACChargeLoopReqParams,
        BPTDynamicACChargeLoopReqParams,
    ]:
        """
        Gets the parameters for the ACChargeLoopReq for the currently set control mode
         and service.
        Args:
            control_mode: Control mode for this session - Scheduled/Dynamic
            selected_service: Enum for this Service - AC/AC_BPT
        Returns:
            ChargeLoop params depending on the selected mode. Return object could be
            one of the following types:
            [
                ScheduledACChargeLoopReqParams,
                BPTScheduledACChargeLoopReqParams,
                DynamicACChargeLoopReqParams,
                BPTDynamicACChargeLoopReqParams,
            ]
        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    # ============================================================================
    # |                          DC-SPECIFIC FUNCTIONS                           |
    # ============================================================================

    @abstractmethod
    async def get_scheduled_dc_charge_loop_params(
        self,
    ) -> ScheduledDCChargeLoopReqParams:
        """
        Gets the parameters for the DCChargeLoopReq in the Scheduled control mode

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dynamic_dc_charge_loop_params(self) -> DynamicDCChargeLoopReqParams:
        """
        Gets the parameters for the DCChargeLoopReq in the Dynamic control mode

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_bpt_scheduled_dc_charge_loop_params(
        self,
    ) -> BPTScheduledDCChargeLoopReqParams:
        """
        Gets the parameters for the DCChargeLoopReq in the Scheduled control mode for
        bi-directional power transfer (BPT)

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_bpt_dynamic_dc_charge_loop_params(
        self,
    ) -> BPTDynamicDCChargeLoopReqParams:
        """
        Gets the parameters for the DCChargeLoopReq in the Dynamic control mode for
        bi-directional power transfer (BPT)

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_present_voltage(self) -> RationalNumber:
        """
        Gets current voltage required for DCChargeLoop for
        DC charging.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_target_voltage(self) -> RationalNumber:
        """
        Gets current voltage required for DCChargeLoop for
        DC charging.
        """
        raise NotImplementedError

    async def get_remaining_time_to_bulk_soc(self) -> PVRemainingTimeToBulkSOC:
        """
        Gets the remaining time until bulk soc is reached.

        Relevant for:
        - DIN SPEC 70121 ??
        - ISO 15118-2
        - ISO 15118-20 ??
        """
        raise NotImplementedError

    @abstractmethod
    async def welding_detection_has_finished(self):
        """
        Returns true as soon as the process of welding
        detection has finished successfully.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20 ??
        """
        raise NotImplementedError

    @abstractmethod
    async def stop_charging(self) -> None:
        """
        Used by CurrentDemand to indicate to EV to stop charging.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dc_ev_power_delivery_parameter_dinspec(
        self,
    ) -> DCEVPowerDeliveryParameterDINSPEC:
        """
        gets the Power Delivery Parameter of the EV

        Relevant for:
        - DIN SPEC 70121
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dc_ev_power_delivery_parameter(self) -> DCEVPowerDeliveryParameter:
        """
        gets the Power Delivery Parameter of the EV

        Relevant for:
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dc_charge_params(self) -> DCEVChargeParams:
        """
        This would return an encapsulation of the following parameters:
        DC Max Current Limit
        DC Max Voltage Limit
        DC Target Current
        DC Target Voltage

        Relevant for
        - DIN SPEC 70121
        """
        raise NotImplementedError

    @abstractmethod
    async def enable_charging(self, enabled: bool) -> None:
        """
        Enables charging for the EVCC.
        Can be used as an indication to go to state C
        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """

    @abstractmethod
    async def get_display_params(self) -> DisplayParameters:
        """
        Enables charging for the EVCC.
        Can be used as an indication to go to state C
        Relevant for:
        - ISO 15118-20
        """
```

## File: iso15118/evcc/controller/simulator.py
```python
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
        self.total_battery_capacity_wh: float = 50.0   # 0.2 kWh  → rapid SOC swing
        self.max_voltage: float = 450.0                    # V at 100 % SOC
        self.min_voltage: float = 300.0                    # V at   0 % SOC
        self.max_charge_current: float = 32.0              # A
        self.max_charge_power_w: float = 11_000.0          # W  (11 kW AC)

        # ── Live battery state ───────────────────────────────────────────────
        self._soc: float = 90.0                            # % — starting at 50 %
        self._current_power_w: float = self.max_charge_power_w  # W — default assumed
        self._last_update_time: float = time.time()

        # ── Session bookkeeping (preserved from SimEVController) ─────────────
        self._charging_is_completed: bool = False
        # ── Battery Health Test state ──────────────────────────────────────
        self._health_test_active: bool = False
        self._health_phase: str = "CHARGE"   # "CHARGE" | "DISCHARGE"
        self._health_c_rate: float = 5.0
        self._health_cutoff_soc: int = 20
        self._health_discharge_current_a: float = 0.0
        # ──────────────────────────────────────────────────────────────────
        self.precharge_loop_cycles: int = 0
        self.welding_detection_cycles: int = 0


        #---
        self.target_soc: float = 100.0   # stop charging here
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
        """Overrides EVControllerInterface.select_energy_service_v20().

        If DC_BPT is offered with a ParameterSet containing TestMode=1
        (HealthDischarge), select that set and activate the health test.
        Otherwise pick the first available service as before.
        """
        # Look for a health test parameter set in DC_BPT services
        for matched in services:
            if matched.service == ServiceV20.DC_BPT:
                for ps in matched.parameter_sets:
                    for param in ps.parameters:
                        if param.name == "TestMode" and param.int_value == 1:
                            # Found health test parameter set — activate
                            c_rate = 5.0
                            cutoff_soc = 20
                            for p2 in ps.parameters:
                                if p2.name == "TestCRate" and p2.int_value:
                                    c_rate = float(p2.int_value)
                                if p2.name == "CutoffSOC" and p2.int_value:
                                    cutoff_soc = p2.int_value
                            # Capacity_Ah = capacity_Wh / nominal_V
                            capacity_ah = self.total_battery_capacity_wh / 400.0
                            self._health_discharge_current_a = -(c_rate * capacity_ah)
                            self._health_cutoff_soc = cutoff_soc
                            self._health_c_rate = c_rate
                            self._health_test_active = True
                            self._health_phase = "CHARGE"   # always charge first
                            logger.info(
                                f"[HealthTest] Activated — C-rate={c_rate}C, "
                                f"I_discharge={self._health_discharge_current_a:.1f}A, "
                                f"cutoff_soc={cutoff_soc}%"
                            )
                            return SelectedEnergyService(
                                service=matched.service,
                                is_free=matched.is_free,
                                parameter_set=ps,
                            )
        # Default: pick first offered service
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
            bulk_soc=self.bulk_soc,
            target_soc=self.target_soc,
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
        """Overrides EVControllerInterface.is_charging_complete().

        During a health test:
          CHARGE phase: complete when SOC reaches 100% → switch to DISCHARGE
          DISCHARGE phase: complete when SOC falls to cutoff_soc
        Normal session: complete when SOC reaches target_soc.
        """
        if self._health_test_active:
            if self._health_phase == "CHARGE":
                if self._soc >= 100.0:
                    # Phase transition — switch to discharge
                    logger.info(
                        "[HealthTest] Phase 1 CHARGE complete — SOC=100%. "
                        "Switching to DISCHARGE phase."
                    )
                    self._health_phase = "DISCHARGE"
                    # Reset power to discharge value so battery physics work
                    capacity_ah = self.total_battery_capacity_wh / 400.0
                    self._current_power_w = -(self._health_c_rate * capacity_ah * 400.0)
                return False   # keep session alive for discharge phase
            elif self._health_phase == "DISCHARGE":
                if self._soc <= self._health_cutoff_soc:
                    logger.info(
                        f"[HealthTest] Phase 2 DISCHARGE complete — "
                        f"SOC={self._soc:.1f}% reached cutoff={self._health_cutoff_soc}%"
                    )
                    self._charging_is_completed = True
                    return True
                return False
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


    def update_secc_limits(self, max_current: float, max_voltage: float, max_power: float):
        """Called when DC_ChargeParameterDiscoveryRes arrives to store SECC limits."""
        self._secc_max_current = min(max_current, self.max_charge_current)
        self._secc_max_voltage = min(max_voltage, self.max_voltage)
        self._secc_max_power_w = min(max_power, self.max_charge_power_w)
        self._current_power_w = self._secc_max_power_w
        logger.info(
            f"[Battery] SECC limits accepted: "
            f"P={self._secc_max_power_w:.0f}W, "
            f"I={self._secc_max_current:.0f}A, "
            f"V={self._secc_max_voltage:.0f}V"
        )

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
                target_soc=self.target_soc,
                bulk_soc=self.bulk_soc,
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
        """Overrides EVControllerInterface.get_bpt_scheduled_dc_charge_loop_params().

        During a health test DISCHARGE phase, sends negative target_current so
        the SECC knows the battery is discharging. During CHARGE phase (or normal
        sessions) behaves identically to before.
        """
        if self._health_test_active and self._health_phase == "DISCHARGE":
            voltage = self._compute_voltage()
            i_discharge = self._health_discharge_current_a  # already negative

            # Update battery physics with discharge power
            discharge_power_w = abs(i_discharge * voltage)
            self._current_power_w = -discharge_power_w   # negative = discharging

            logger.info(
                f"[HealthTest] DISCHARGE | SOC={self._soc:.1f}% "
                f"V={voltage:.1f}V I={i_discharge:.1f}A P={discharge_power_w:.0f}W"
            )
            return BPTScheduledDCChargeLoopReqParams(
                ev_target_current=RationalNumber.get_rational_repr(int(i_discharge)),
                ev_target_voltage=RationalNumber.get_rational_repr(int(voltage)),
                ev_max_discharge_power=RationalNumber.get_rational_repr(
                    int(discharge_power_w)
                ),
                ev_min_discharge_power=RationalNumber.get_rational_repr(0),
                ev_max_discharge_current=RationalNumber.get_rational_repr(
                    int(abs(i_discharge))
                ),
            )

        # Normal charge or health test CHARGE phase — use base scheduled params
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
```

## File: iso15118/evcc/states/iso15118_20_states.py
```python
"""
This module contains the EVCC's States used to process the SECC's incoming
V2GMessage objects of the ISO 15118-20 protocol, from SessionSetupRes to
SessionStopRes.
"""

import asyncio
import logging
import time
from typing import Any, List, Union, cast

from iso15118.evcc.comm_session_handler import EVCCCommunicationSession
from iso15118.evcc.states.evcc_state import StateEVCC
from iso15118.shared.exceptions import PrivateKeyReadError
from iso15118.shared.exi_codec import EXI
from iso15118.shared.messages.app_protocol import (
    SupportedAppProtocolReq,
    SupportedAppProtocolRes,
)
from iso15118.shared.messages.din_spec.msgdef import V2GMessage as V2GMessageDINSPEC
from iso15118.shared.messages.enums import (
    AuthEnum,
    ControlMode,
    ISOV20PayloadTypes,
    Namespace,
    ParameterName,
    ServiceV20,
    SessionStopAction,
)
from iso15118.shared.messages.iso15118_2.msgdef import V2GMessage as V2GMessageV2
from iso15118.shared.messages.iso15118_20.ac import (
    ACChargeLoopReq,
    ACChargeLoopRes,
    ACChargeParameterDiscoveryReq,
    ACChargeParameterDiscoveryRes,
)
from iso15118.shared.messages.iso15118_20.common_messages import (
    AuthorizationReq,
    AuthorizationRes,
    AuthorizationSetupReq,
    AuthorizationSetupRes,
    CertificateInstallationReq,
    ChannelSelection,
    ChargingSession,
    EIMAuthReqParams,
    MatchedService,
    PnCAuthReqParams,
    PowerDeliveryReq,
    PowerDeliveryRes,
    ScheduleExchangeReq,
    ScheduleExchangeRes,
    SelectedService,
    ServiceDetailReq,
    ServiceDetailRes,
    ServiceDiscoveryReq,
    ServiceDiscoveryRes,
    ServiceSelectionReq,
    ServiceSelectionRes,
    SessionSetupRes,
    SessionStopReq,
    SessionStopRes,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    EVSENotification,
    MessageHeader,
    Processing,
    RationalNumber,
    RootCertificateIDList,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    V2GMessage as V2GMessageV20,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    V2GRequest,
)
from iso15118.shared.messages.iso15118_20.dc import (
    BPTDynamicDCChargeLoopReqParams,
    BPTScheduledDCChargeLoopReqParams,
    DCCableCheckReq,
    DCCableCheckRes,
    DCChargeLoopReq,
    DCChargeLoopRes,
    DCChargeParameterDiscoveryReq,
    DCChargeParameterDiscoveryRes,
    DCPreChargeReq,
    DCPreChargeRes,
    DCWeldingDetectionReq,
    DynamicDCChargeLoopReqParams,
    ScheduledDCChargeLoopReqParams,
)
from iso15118.shared.messages.iso15118_20.timeouts import Timeouts
from iso15118.shared.messages.timeouts import Timeouts as TimeoutsShared
from iso15118.shared.messages.xmldsig import X509IssuerSerial
from iso15118.shared.notifications import StopNotification
from iso15118.shared.security import (
    CertPath,
    KeyEncoding,
    KeyPasswordPath,
    KeyPath,
    create_signature,
    get_cert_issuer_serial,
    load_cert_chain,
    load_priv_key,
)
from iso15118.shared.states import Terminate

logger = logging.getLogger(__name__)


# ============================================================================
# |    COMMON EVCC STATES (FOR ALL ENERGY TRANSFER MODES) - ISO 15118-20     |
# ============================================================================


class SessionSetup(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a SessionSetupRes from
    the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        # TODO: less the time used for waiting for and processing the
        #       SDPResponse and SupportedAppProtocolRes
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, SessionSetupRes)
        if not msg:
            return

        session_setup_res: SessionSetupRes = cast(SessionSetupRes, msg)

        self.comm_session.session_id = msg.header.session_id
        self.comm_session.evse_id = session_setup_res.evse_id

        auth_setup_req = AuthorizationSetupReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            )
        )

        self.create_next_message(
            AuthorizationSetup,
            auth_setup_req,
            Timeouts.AUTHORIZATION_SETUP_REQ,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )


class AuthorizationSetup(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes an AuthorizationSetupRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.AUTHORIZATION_SETUP_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, AuthorizationSetupRes)
        if not msg:
            return

        auth_setup_res: AuthorizationSetupRes = cast(AuthorizationSetupRes, msg)
        signature = None

        if (
            auth_setup_res.cert_install_service
            and await self.comm_session.ev_controller.is_cert_install_needed()
        ):
            # TODO: Find a more generic way to search for all available
            #       V2GRootCA certificates
            issuer, serial = get_cert_issuer_serial(CertPath.V2G_ROOT_DER)

            oem_prov_cert_chain = load_cert_chain(
                protocol=self.comm_session.protocol,
                leaf_path=CertPath.OEM_LEAF_DER,
                sub_ca2_path=CertPath.OEM_SUB_CA2_DER,
                sub_ca1_path=CertPath.OEM_SUB_CA1_DER,
                id="id1",
            )

            # TODO: Check how a signature in ISO 15118-20 differs from an
            #       ISO 15118-2 signature
            try:
                signature = create_signature(
                    [
                        (
                            "id1",
                            EXI().to_exi(
                                oem_prov_cert_chain, Namespace.ISO_V20_COMMON_MSG
                            ),
                        )
                    ],
                    load_priv_key(
                        KeyPath.OEM_LEAF_PEM,
                        KeyEncoding.PEM,
                        KeyPasswordPath.OEM_LEAF_KEY_PASSWORD,
                    ),
                )

                cert_install_req = CertificateInstallationReq(
                    header=MessageHeader(
                        session_id=self.comm_session.session_id,
                        timestamp=time.time(),
                        signature=signature,
                    ),
                    oem_prov_cert_chain=oem_prov_cert_chain,
                    root_cert_id_list=RootCertificateIDList(
                        root_cert_ids=[
                            X509IssuerSerial(
                                x509_issuer_name=issuer, x509_serial_number=serial
                            )
                        ]
                    ),
                    max_contract_cert_chains=self.comm_session.config.max_contract_certs,  # noqa: E501
                    prioritized_emaids=await self.comm_session.ev_controller.get_prioritised_emaids(),  # noqa: E501
                )

                self.create_next_message(
                    CertificateInstallation,
                    cert_install_req,
                    Timeouts.CERTIFICATE_INSTALLATION_REQ,
                    Namespace.ISO_V20_COMMON_MSG,
                )
                return
            except PrivateKeyReadError as exc:
                logger.warning(
                    "PrivateKeyReadError occurred while trying to create "
                    "signature for CertificateInstallationReq. Falling back to sending "
                    f"AuthorizationReq instead.\n{exc}"
                )

        eim_params, pnc_params = None, None
        if AuthEnum.PNC in auth_setup_res.auth_services:
            # TODO: Check if several contract certificates are in place and
            #      if the SECC sent a list of supported providers to pre-
            #      select the contract certificate(s) that work at this SECC
            pnc_params = PnCAuthReqParams(
                gen_challenge=auth_setup_res.pnc_as_res.gen_challenge,
                contract_cert_chain=load_cert_chain(
                    protocol=self.comm_session.protocol,
                    leaf_path=CertPath.CONTRACT_LEAF_DER,
                    sub_ca2_path=CertPath.MO_SUB_CA2_DER,
                    sub_ca1_path=CertPath.MO_SUB_CA1_DER,
                ),
                id="id1",
            )

            # TODO: Need a signature for ISO 15118-20, not ISO 15118-2
            pnc_params_tuple = (
                pnc_params.id,
                EXI().to_exi(pnc_params, Namespace.ISO_V20_COMMON_MSG),
            )
            elements_to_sign = [pnc_params_tuple]
            try:
                # The private key to be used for the signature
                signature_key = load_priv_key(
                    KeyPath.CONTRACT_LEAF_PEM,
                    KeyEncoding.PEM,
                    KeyPasswordPath.CONTRACT_LEAF_KEY_PASSWORD,
                )
                signature = create_signature(elements_to_sign, signature_key)
            except PrivateKeyReadError as exc:
                logger.warning(
                    "PrivateKeyReadError occurred while trying to create "
                    "signature for PnC_AReqAuthorizationMode. Falling back to EIM "
                    f"identification mode.\n{exc}"
                )
                pnc_params = None
                eim_params = EIMAuthReqParams()
        else:
            eim_params = EIMAuthReqParams()

        auth_req = AuthorizationReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
                signature=signature,
            ),
            selected_auth_service=AuthEnum.PNC if pnc_params else AuthEnum.EIM,
            pnc_params=pnc_params,
            eim_params=eim_params,
        )

        # Caching this in case, we need to loop AuthorizationReq/Res
        # [V2G20-1582] If EVSEProcessing is set to Ongoing, EVCC shall send another
        # unaltered AuthorizationReq (with the exception of timestamp)
        self.comm_session.authorization_req_message = auth_req
        self.create_next_message(
            Authorization,
            auth_req,
            Timeouts.AUTHORIZATION_REQ,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )


class CertificateInstallation(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a
    CertificateInstallationRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.CERTIFICATE_INSTALLATION_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        raise NotImplementedError("CertificateInstallation not yet implemented")


class Authorization(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes an AuthorizationRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.AUTHORIZATION_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, AuthorizationRes)
        if not msg:
            return

        auth_res: AuthorizationRes = cast(AuthorizationRes, msg)
        # TODO Act upon the response codes and evse_processing value of auth_res
        #      (and delete the # noqa: F841)
        # TODO: V2G20-2221 demands to send CertificateInstallationReq if necessary

        if auth_res.evse_processing == Processing.FINISHED:
            # Reset the Ongoing timer
            self.comm_session.ongoing_timer = -1

            service_discovery_req = ServiceDiscoveryReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                )
                # To limit the list of requested VAS services, set supported_service_ids
            )

            self.create_next_message(
                ServiceDiscovery,
                service_discovery_req,
                Timeouts.SERVICE_DISCOVERY_REQ,
                Namespace.ISO_V20_COMMON_MSG,
                ISOV20PayloadTypes.MAINSTREAM,
            )
        else:
            logger.debug("SECC is still processing the Authorization")
            elapsed_time: float = 0
            if self.comm_session.ongoing_timer >= 0:
                elapsed_time = time.time() - self.comm_session.ongoing_timer
                if elapsed_time > TimeoutsShared.V2G_EVCC_ONGOING_TIMEOUT:
                    self.stop_state_machine(
                        "Ongoing timer timed out for " "AuthorizationRes"
                    )
                    return
            else:
                self.comm_session.ongoing_timer = time.time()

            auth_req = AuthorizationReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                    signature=(
                        self.comm_session.authorization_req_message.header.signature
                    ),
                ),
                selected_auth_service=(
                    self.comm_session.authorization_req_message.selected_auth_service
                ),
                pnc_params=self.comm_session.authorization_req_message.pnc_params,
                eim_params=self.comm_session.authorization_req_message.eim_params,
            )

            self.create_next_message(
                Authorization,
                auth_req,
                min(
                    Timeouts.AUTHORIZATION_REQ,
                    TimeoutsShared.V2G_EVCC_ONGOING_TIMEOUT - elapsed_time,
                ),
                Namespace.ISO_V20_COMMON_MSG,
                ISOV20PayloadTypes.MAINSTREAM,
            )


class ServiceDiscovery(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a ServiceDiscoveryRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.SERVICE_DISCOVERY_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, ServiceDiscoveryRes)
        if not msg:
            return

        service_discovery_res: ServiceDiscoveryRes = cast(ServiceDiscoveryRes, msg)

        self.comm_session.service_renegotiation_supported = (
            service_discovery_res.service_renegotiation_supported
        )

        req_energy_services: List[ServiceV20] = (
            await self.comm_session.ev_controller.get_supported_energy_services()
        )

        for energy_service in service_discovery_res.energy_service_list.services:
            for requested_energy_service in req_energy_services:
                if requested_energy_service.id == energy_service.service_id:
                    self.comm_session.matched_services_v20.append(
                        MatchedService(
                            service=ServiceV20.get_by_id(energy_service.service_id),
                            is_energy_service=True,
                            is_free=energy_service.free_service,
                            # Parameter sets are available with ServiceDetailRes
                            parameter_sets=[],
                        )
                    )
                    self.comm_session.service_details_to_request.append(
                        energy_service.service_id
                    )

        if not self.comm_session.matched_services_v20:
            self.comm_session.charging_session_stop_v20 = ChargingSession.TERMINATE
            termination_reason: str = "WrongServiceID"
            logger.info(f"Requesting SessionStop. Reason: {termination_reason} ")
            session_stop_req = SessionStopReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                charging_session=ChargingSession.TERMINATE,
                # See "3.5.2. Error handling" in CharIN Implementation Guide for DC BPT
                ev_termination_code=1,
                ev_termination_explanation=termination_reason,
            )

            self.create_next_message(
                SessionStop,
                session_stop_req,
                Timeouts.SESSION_STOP_REQ,
                Namespace.ISO_V20_COMMON_MSG,
                ISOV20PayloadTypes.MAINSTREAM,
            )
            return

        if service_discovery_res.vas_list:
            for vas_service in service_discovery_res.vas_list.services:
                self.comm_session.matched_services_v20.append(
                    MatchedService(
                        service=ServiceV20.get_by_id(vas_service.service_id),
                        is_energy_service=False,
                        is_free=vas_service.free_service,
                        # Parameter sets are available with ServiceDetailRes
                        parameter_sets=[],
                    )
                )

                # If you want to request service details for a specific value-added
                # service, then use these lines of code:
                # self.comm_session.service_details_to_request.append(
                #     vas_service.service_id
                # )

        service_detail_req = ServiceDetailReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            service_id=self.comm_session.service_details_to_request.pop(),
        )

        self.create_next_message(
            ServiceDetail,
            service_detail_req,
            Timeouts.SERVICE_DETAIL_REQ,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )


class ServiceDetail(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a ServiceDetailRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.SERVICE_DETAIL_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, ServiceDetailRes)
        if not msg:
            return

        service_detail_res: ServiceDetailRes = cast(ServiceDetailRes, msg)

        self.store_parameter_sets(service_detail_res)

        # Each ServiceDetailReq returns ParameterSet for a specified service.
        # Send ServiceDetailReq to EVSE if there are more parameter sets
        # to be requested
        if self.comm_session.service_details_to_request:
            service_detail_req = ServiceDetailReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                service_id=self.comm_session.service_details_to_request.pop(),
            )

            self.create_next_message(
                ServiceDetail,
                service_detail_req,
                Timeouts.SERVICE_DETAIL_REQ,
                Namespace.ISO_V20_COMMON_MSG,
                ISOV20PayloadTypes.MAINSTREAM,
            )
            return

        self.comm_session.selected_energy_service = (
            await self.comm_session.ev_controller.select_energy_service_v20(
                self.comm_session.matched_services_v20
            )
        )

        if not self.is_control_mode_set():
            session_stop_req = SessionStopReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                charging_session=ChargingSession.TERMINATE,
                ev_termination_explanation="Control mode parameter missing",
            )

            self.create_next_message(
                SessionStop,
                session_stop_req,
                Timeouts.SESSION_STOP_REQ,
                Namespace.ISO_V20_COMMON_MSG,
                ISOV20PayloadTypes.MAINSTREAM,
            )
            return

        service_selection_req: ServiceSelectionReq = (
            await self.build_service_selection_req()
        )

        self.create_next_message(
            ServiceSelection,
            service_selection_req,
            Timeouts.SERVICE_SELECTION_REQ,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

    async def build_service_selection_req(self) -> ServiceSelectionReq:
        selected_energy_service = SelectedService(
            service_id=self.comm_session.selected_energy_service.service_id,
            parameter_set_id=self.comm_session.selected_energy_service.parameter_set_id,
        )

        self.comm_session.selected_vas_list_v20 = (
            await self.comm_session.ev_controller.select_vas_services_v20(
                self.comm_session.matched_services_v20
            )
        )

        selected_vas_list: List[SelectedService] = []
        for vas in self.comm_session.selected_vas_list_v20:
            selected_vas_list.append(
                SelectedService(
                    service_id=vas.service.id, parameter_set_id=vas.parameter_set.id
                )
            )

        service_selection_req = ServiceSelectionReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            selected_energy_service=selected_energy_service,
            selected_vas_list=selected_vas_list if selected_vas_list else None,
        )

        return service_selection_req

    def is_control_mode_set(self) -> bool:
        control_mode_set = False
        if self.comm_session.selected_energy_service:
            parameter_set = self.comm_session.selected_energy_service.parameter_set
            for param in parameter_set.parameters:
                if param.name == ParameterName.CONTROL_MODE:
                    self.comm_session.control_mode = ControlMode(param.int_value)
                    logger.info(
                        f"Selected Control Mode: {self.comm_session.control_mode}"
                    )
                    control_mode_set = True
        return control_mode_set

    def store_parameter_sets(self, service_detail_res: ServiceDetailRes):
        """
        Saves the parameter sets associated with the service id requested
        Args:
            service_detail_res: Service Detail Response for the service requested

        Returns:

        """
        for service in self.comm_session.matched_services_v20:
            # Save the parameter sets for a particular service
            if service.service.id == service_detail_res.service_id:
                service.parameter_sets = (
                    service_detail_res.service_parameter_list.parameter_sets
                )


class ServiceSelection(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a ServiceSelectionRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.SERVICE_SELECTION_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, ServiceSelectionRes)
        if not msg:
            return

        # TODO Act upon the possible negative response codes in service_selection_res

        next_req: Any = None
        if self.comm_session.selected_energy_service.service in (
            ServiceV20.AC,
            ServiceV20.AC_BPT,
        ):
            ac_params, bpt_ac_params = None, None
            self.comm_session.selected_charging_type_is_ac = True
            if self.comm_session.selected_energy_service.service == ServiceV20.AC:
                ac_params = await self.comm_session.ev_controller.get_charge_params_v20(
                    self.comm_session.selected_energy_service
                )
            else:
                bpt_ac_params = (
                    await self.comm_session.ev_controller.get_charge_params_v20(
                        self.comm_session.selected_energy_service
                    )
                )

            next_req = ACChargeParameterDiscoveryReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                ac_params=ac_params,
                bpt_ac_params=bpt_ac_params,
            )

            self.create_next_message(
                ACChargeParameterDiscovery,
                next_req,
                Timeouts.CHARGE_PARAMETER_DISCOVERY_REQ,
                Namespace.ISO_V20_AC,
                ISOV20PayloadTypes.AC_MAINSTREAM,
            )
        elif self.comm_session.selected_energy_service.service in (
            ServiceV20.DC,
            ServiceV20.DC_BPT,
        ):
            dc_params, bpt_dc_params = None, None
            self.comm_session.selected_charging_type_is_ac = False
            if self.comm_session.selected_energy_service.service == ServiceV20.DC:
                dc_params = await self.comm_session.ev_controller.get_charge_params_v20(
                    self.comm_session.selected_energy_service
                )
            else:
                bpt_dc_params = (
                    await self.comm_session.ev_controller.get_charge_params_v20(
                        self.comm_session.selected_energy_service
                    )
                )

            next_req = DCChargeParameterDiscoveryReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                dc_params=dc_params,
                bpt_dc_params=bpt_dc_params,
            )

            self.create_next_message(
                DCChargeParameterDiscovery,
                next_req,
                Timeouts.CHARGE_PARAMETER_DISCOVERY_REQ,
                Namespace.ISO_V20_DC,
                ISOV20PayloadTypes.DC_MAINSTREAM,
            )
        else:
            # TODO Implement support for other energy transfer services
            logger.error(
                "Energy transfer mode for service "
                f"{self.comm_session.selected_energy_service.service} "
                "not supported in ServiceSelection"
            )


class ScheduleExchange(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a ScheduleExchangeRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.SCHEDULE_EXCHANGE_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, ScheduleExchangeRes)
        if not msg:
            return

        schedule_exchange_res: ScheduleExchangeRes = cast(ScheduleExchangeRes, msg)

        if schedule_exchange_res.evse_processing == Processing.ONGOING:
            self.create_next_message(
                ScheduleExchange,
                self.comm_session.ongoing_schedule_exchange_req,
                Timeouts.SCHEDULE_EXCHANGE_REQ,
                Namespace.ISO_V20_COMMON_MSG,
                ISOV20PayloadTypes.MAINSTREAM,
            )
        else:
            if self.comm_session.control_mode == ControlMode.SCHEDULED:
                (
                    ev_power_profile,
                    charge_progress,
                ) = await self.comm_session.ev_controller.process_scheduled_se_params(
                    schedule_exchange_res.scheduled_params,
                    schedule_exchange_res.go_to_pause,
                )
            else:
                (
                    ev_power_profile,
                    charge_progress,
                ) = await self.comm_session.ev_controller.process_dynamic_se_params(
                    schedule_exchange_res.dynamic_params,
                    schedule_exchange_res.go_to_pause,
                )

            ev_processing = Processing.FINISHED
            bpt_channel_selection = None
            self.comm_session.schedule_exchange_res = schedule_exchange_res

            if not ev_power_profile:
                ev_processing = Processing.ONGOING
                self.comm_session.ev_processing = Processing.ONGOING
            else:
                # Information from EV to show if charging or discharging is planned
                if self.comm_session.selected_energy_service.service in (
                    ServiceV20.AC_BPT,
                    ServiceV20.DC_BPT,
                ):
                    power_value = ev_power_profile.entry_list.entries[-1].power.value
                    if power_value < 0:
                        bpt_channel_selection = ChannelSelection.DISCHARGE
                    else:
                        bpt_channel_selection = ChannelSelection.CHARGE

            await self.comm_session.ev_controller.enable_charging(True)
            if self.comm_session.selected_charging_type_is_ac:
                power_delivery_req = PowerDeliveryReq(
                    header=MessageHeader(
                        session_id=self.comm_session.session_id,
                        timestamp=time.time(),
                    ),
                    ev_processing=ev_processing,
                    charge_progress=charge_progress,
                    ev_power_profile=ev_power_profile,
                    bpt_channel_selection=bpt_channel_selection,
                )

                self.create_next_message(
                    PowerDelivery,
                    power_delivery_req,
                    Timeouts.POWER_DELIVERY_REQ,
                    Namespace.ISO_V20_COMMON_MSG,
                    ISOV20PayloadTypes.MAINSTREAM,
                )
            else:
                cable_check_req = DCCableCheckReq(
                    header=MessageHeader(
                        session_id=self.comm_session.session_id,
                        timestamp=time.time(),
                    )
                )
                self.create_next_message(
                    DCCableCheck,
                    cable_check_req,
                    Timeouts.DC_CABLE_CHECK_REQ,
                    Namespace.ISO_V20_DC,
                    ISOV20PayloadTypes.DC_MAINSTREAM,
                )


class PowerDelivery(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a PowerDeliveryRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.POWER_DELIVERY_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, PowerDeliveryRes)
        if not msg:
            return

        if self.comm_session.ev_processing == Processing.ONGOING:
            await self.create_new_power_delivery_req(
                self.comm_session.schedule_exchange_res
            )
            return

        if self.comm_session.charging_session_stop_v20 in (
            ChargingSession.SERVICE_RENEGOTIATION,
            ChargingSession.TERMINATE,
        ):
            await self.comm_session.ev_controller.enable_charging(False)
            if self.comm_session.selected_energy_service.service in [
                ServiceV20.DC,
                ServiceV20.DC_BPT,
            ]:
                welding_detection_req = DCWeldingDetectionReq(
                    header=MessageHeader(
                        session_id=self.comm_session.session_id,
                        timestamp=time.time(),
                    ),
                    ev_processing=Processing.ONGOING,
                )
                self.create_next_message(
                    DCWeldingDetection,
                    welding_detection_req,
                    Timeouts.DC_WELDING_DETECTION_REQ,
                    Namespace.ISO_V20_DC,
                    ISOV20PayloadTypes.DC_MAINSTREAM,
                )
            else:
                session_stop_req = SessionStopReq(
                    header=MessageHeader(
                        session_id=self.comm_session.session_id,
                        timestamp=time.time(),
                    ),
                    charging_session=self.comm_session.charging_session_stop_v20,
                )
                self.create_next_message(
                    SessionStop,
                    session_stop_req,
                    Timeouts.SESSION_STOP_REQ,
                    Namespace.ISO_V20_COMMON_MSG,
                    ISOV20PayloadTypes.MAINSTREAM,
                )

            return

        scheduled_params: ScheduledDCChargeLoopReqParams = None
        dynamic_params: DynamicDCChargeLoopReqParams = None
        bpt_scheduled_params: BPTScheduledDCChargeLoopReqParams = None
        bpt_dynamic_params: BPTDynamicDCChargeLoopReqParams = None
        selected_energy_service = self.comm_session.selected_energy_service
        control_mode = self.comm_session.control_mode
        ev_controller = self.comm_session.ev_controller

        if selected_energy_service.service in [ServiceV20.AC, ServiceV20.AC_BPT]:
            charging_loop_params = await ev_controller.get_ac_charge_loop_params_v20(
                control_mode, selected_energy_service.service
            )
            if selected_energy_service.service == ServiceV20.AC:
                if control_mode == ControlMode.SCHEDULED:
                    scheduled_params = cast(
                        ScheduledDCChargeLoopReqParams, charging_loop_params
                    )
                else:
                    # Dynamic
                    dynamic_params = cast(
                        DynamicDCChargeLoopReqParams, charging_loop_params
                    )
            else:
                # AC_BPT
                if control_mode == ControlMode.SCHEDULED:
                    bpt_scheduled_params = cast(
                        BPTScheduledDCChargeLoopReqParams, charging_loop_params
                    )
                else:
                    # Dynamic
                    bpt_dynamic_params = cast(
                        BPTDynamicDCChargeLoopReqParams, charging_loop_params
                    )

            ac_charge_loop_req = ACChargeLoopReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                display_parameters=await self.comm_session.ev_controller.get_display_params(),  # noqa
                scheduled_params=scheduled_params,
                dynamic_params=dynamic_params,
                bpt_scheduled_params=bpt_scheduled_params,
                bpt_dynamic_params=bpt_dynamic_params,
                meter_info_requested=False,
            )

            self.create_next_message(
                ACChargeLoop,
                ac_charge_loop_req,
                Timeouts.AC_CHARGE_LOOP_REQ,
                Namespace.ISO_V20_AC,
                ISOV20PayloadTypes.AC_MAINSTREAM,
            )

        elif selected_energy_service.service in [ServiceV20.DC, ServiceV20.DC_BPT]:
            if selected_energy_service.service == ServiceV20.DC:
                if control_mode == ControlMode.SCHEDULED:
                    scheduled_params = (
                        await ev_controller.get_scheduled_dc_charge_loop_params()
                    )
                else:
                    dynamic_params = (
                        await ev_controller.get_dynamic_dc_charge_loop_params()
                    )
            elif selected_energy_service.service == ServiceV20.DC_BPT:
                if control_mode == ControlMode.SCHEDULED:
                    bpt_scheduled_params = (
                        await ev_controller.get_bpt_scheduled_dc_charge_loop_params()
                    )
                else:
                    bpt_dynamic_params = (
                        await ev_controller.get_bpt_dynamic_dc_charge_loop_params()
                    )

            dc_charge_loop_req = DCChargeLoopReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                display_parameters=await ev_controller.get_display_params(),
                ev_present_voltage=await ev_controller.get_present_voltage(),
                scheduled_params=scheduled_params,
                dynamic_params=dynamic_params,
                bpt_scheduled_params=bpt_scheduled_params,
                bpt_dynamic_params=bpt_dynamic_params,
                meter_info_requested=False,
            )

            self.create_next_message(
                DCChargeLoop,
                dc_charge_loop_req,
                Timeouts.DC_CHARGE_LOOP_REQ,
                Namespace.ISO_V20_DC,
                ISOV20PayloadTypes.DC_MAINSTREAM,
            )
        else:
            logger.error(f"Energy service unknown: {selected_energy_service.service}")
            return

    async def create_new_power_delivery_req(
        self, schedule_exchange_res: ScheduleExchangeRes
    ):
        if self.comm_session.control_mode == ControlMode.SCHEDULED:
            (
                ev_power_profile,
                charge_progress,
            ) = await self.comm_session.ev_controller.process_scheduled_se_params(
                schedule_exchange_res.scheduled_params,
                schedule_exchange_res.go_to_pause,
            )
        else:
            (
                ev_power_profile,
                charge_progress,
            ) = await self.comm_session.ev_controller.process_dynamic_se_params(
                schedule_exchange_res.dynamic_params, schedule_exchange_res.go_to_pause
            )

        ev_processing = Processing.FINISHED
        self.comm_session.ev_processing = Processing.FINISHED
        if not ev_power_profile:
            ev_processing = Processing.ONGOING
            self.comm_session.ev_processing = Processing.ONGOING

        # Information from EV to show if charging or discharging is planned
        bpt_channel_selection = None
        if self.comm_session.selected_energy_service.service in (
            ServiceV20.AC_BPT,
            ServiceV20.DC_BPT,
        ):
            bpt_channel_selection = ChannelSelection.CHARGE
            if ev_power_profile is not None:
                power_value = ev_power_profile.entry_list.entries[-1].power.value
                if power_value < 0:
                    bpt_channel_selection = ChannelSelection.DISCHARGE

        power_delivery_req = PowerDeliveryReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            ev_processing=ev_processing,
            charge_progress=charge_progress,
            ev_power_profile=ev_power_profile,
            bpt_channel_selection=bpt_channel_selection,
        )

        self.create_next_message(
            PowerDelivery,
            power_delivery_req,
            Timeouts.POWER_DELIVERY_REQ,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )


class SessionStop(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a SessionStopRes
    from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.SESSION_STOP_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, SessionStopRes)
        if not msg:
            return

        session_stop_reason = self.comm_session.charging_session_stop_v20.lower()
        if session_stop_reason == "pause":
            session_stop_action = SessionStopAction.PAUSE
        else:
            session_stop_action = SessionStopAction.TERMINATE
        self.comm_session.stop_reason = StopNotification(
            True,
            f"Communication session " f"{session_stop_reason}d",
            self.comm_session.writer.get_extra_info("peername"),
            session_stop_action,
        )

        if (
            self.comm_session.service_renegotiation_supported
            and self.comm_session.renegotiation_requested
        ):
            self.comm_session.renegotiation_requested = False
            self.next_state = ServiceDiscovery
        else:
            self.next_state = Terminate

        return


# ============================================================================
# |                AC-SPECIFIC EVCC STATES - ISO 15118-20                    |
# ============================================================================


class ACChargeParameterDiscovery(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes an
    ACChargeParameterDiscoveryRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.CHARGE_PARAMETER_DISCOVERY_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, ACChargeParameterDiscoveryRes)
        if not msg:
            return

        # TODO Act upon the possible negative response codes in ac_cpd_res

        self.comm_session.ongoing_schedule_exchange_req = (
            await self.build_schedule_exchange_request()
        )

        self.create_next_message(
            ScheduleExchange,
            self.comm_session.ongoing_schedule_exchange_req,
            Timeouts.SCHEDULE_EXCHANGE_REQ,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

    async def build_schedule_exchange_request(self) -> ScheduleExchangeReq:
        scheduled_params, dynamic_params = None, None
        if self.comm_session.control_mode == ControlMode.SCHEDULED:
            scheduled_params = (
                await self.comm_session.ev_controller.get_scheduled_se_params(
                    self.comm_session.selected_energy_service
                )
            )

        if self.comm_session.control_mode == ControlMode.DYNAMIC:
            dynamic_params = (
                await self.comm_session.ev_controller.get_dynamic_se_params(
                    self.comm_session.selected_energy_service
                )
            )

        return ScheduleExchangeReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            max_supporting_points=self.comm_session.config.max_supporting_points,
            scheduled_params=scheduled_params,
            dynamic_params=dynamic_params,
        )


class ACChargeLoop(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes an
    ACChargeLoopRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.AC_CHARGE_LOOP_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, ACChargeLoopRes)
        if not msg:
            return

        ac_charge_loop_res: ACChargeLoopRes = cast(ACChargeLoopRes, msg)

        # Before checking if we should continue charging,
        # check if SECC requested a renegotiation.
        # evse_status field in ACChargeLoopRes is optional
        if ac_charge_loop_res.evse_status:
            renegotiation = False
            evse_notification = ac_charge_loop_res.evse_status.evse_notification
            if evse_notification not in [
                EVSENotification.SERVICE_RENEGOTIATION,
                EVSENotification.TERMINATE,
            ]:
                raise NotImplementedError(
                    f"Processing for EVSE Notification "
                    f"{evse_notification} is not "
                    f"supported at the moment"
                )
            if evse_notification == EVSENotification.SERVICE_RENEGOTIATION:
                renegotiation = True
            self.stop_v20_charging(
                next_state=PowerDelivery, renegotiate_requested=renegotiation
            )

        elif await self.comm_session.ev_controller.continue_charging():
            try:
                delay: int = (
                    await self.comm_session.ev_controller.charge_loop_delay()
                )  # noqa
                logger.info(f"Next ChargeLoop Req in {delay} seconds")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.info(f"No delay for the next ChargeLoop Req. Reason {e}")
            scheduled_params, dynamic_params = None, None
            bpt_scheduled_params, bpt_dynamic_params = None, None
            selected_energy_service = self.comm_session.selected_energy_service
            control_mode = self.comm_session.control_mode
            ev_controller = self.comm_session.ev_controller

            # TODO You might want to change certain request params based on the values
            #      in the response

            if selected_energy_service.service in [ServiceV20.AC, ServiceV20.AC_BPT]:
                charging_loop_params = (
                    await ev_controller.get_ac_charge_loop_params_v20(  # noqa
                        control_mode, selected_energy_service.service
                    )
                )
                if selected_energy_service.service == ServiceV20.AC:
                    if control_mode == ControlMode.SCHEDULED:
                        scheduled_params = charging_loop_params
                    else:
                        # Dynamic
                        dynamic_params = charging_loop_params
                else:
                    # AC_BPT
                    if control_mode == ControlMode.SCHEDULED:
                        bpt_scheduled_params = charging_loop_params
                    else:
                        # Dynamic
                        bpt_dynamic_params = charging_loop_params
            else:
                logger.error(
                    f"This shouldn't happen. {selected_energy_service.service} "
                    f"not expected here."
                )
                return

            ac_charge_loop_req = ACChargeLoopReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                display_parameters=await self.comm_session.ev_controller.get_display_params(),  # noqa
                scheduled_params=scheduled_params,
                dynamic_params=dynamic_params,
                bpt_scheduled_params=bpt_scheduled_params,
                bpt_dynamic_params=bpt_dynamic_params,
                meter_info_requested=False,
            )

            self.create_next_message(
                ACChargeLoop,
                ac_charge_loop_req,
                Timeouts.AC_CHARGE_LOOP_REQ,
                Namespace.ISO_V20_AC,
                ISOV20PayloadTypes.AC_MAINSTREAM,
            )
        else:
            self.stop_v20_charging(next_state=PowerDelivery)


# ============================================================================
# |                DC-SPECIFIC EVCC STATES - ISO 15118-20                    |
# ============================================================================


class DCChargeParameterDiscovery(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a
    DCChargeParameterDiscoveryRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.CHARGE_PARAMETER_DISCOVERY_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, DCChargeParameterDiscoveryRes)
        if not msg:
            return

        # ── Feed SECC limits into EV controller ───────────────────────────
        cp = msg.dc_params or msg.bpt_dc_params
        self.comm_session.ev_controller.update_secc_limits(
            max_current=cp.evse_max_charge_current.value * (10 ** cp.evse_max_charge_current.exponent),
            max_voltage=cp.evse_max_voltage.value * (10 ** cp.evse_max_voltage.exponent),
            max_power=cp.evse_max_charge_power.value * (10 ** cp.evse_max_charge_power.exponent),
        )
        # ──────────────────────────────────────────────────────────────────



        # TODO Act upon the possible negative response codes in dc_cpd_res

        self.comm_session.ongoing_schedule_exchange_req = (
            await self.build_schedule_exchange_request()
        )

        self.create_next_message(
            ScheduleExchange,
            self.comm_session.ongoing_schedule_exchange_req,
            Timeouts.SCHEDULE_EXCHANGE_REQ,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

    async def build_schedule_exchange_request(self) -> ScheduleExchangeReq:
        scheduled_params, dynamic_params = None, None
        if self.comm_session.control_mode == ControlMode.SCHEDULED:
            scheduled_params = (
                await self.comm_session.ev_controller.get_scheduled_se_params(
                    self.comm_session.selected_energy_service
                )
            )

        if self.comm_session.control_mode == ControlMode.DYNAMIC:
            dynamic_params = (
                await self.comm_session.ev_controller.get_dynamic_se_params(
                    self.comm_session.selected_energy_service
                )
            )

        return ScheduleExchangeReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            max_supporting_points=self.comm_session.config.max_supporting_points,
            scheduled_params=scheduled_params,
            dynamic_params=dynamic_params,
        )


class DCCableCheck(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a
    DCCableCheckRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.DC_CABLE_CHECK_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, DCCableCheckRes)
        if not msg:
            return

        cable_check_res: DCCableCheckRes = cast(DCCableCheckRes, msg)

        if cable_check_res.evse_processing == Processing.FINISHED:
            # Reset the Ongoing timer
            self.comm_session.ongoing_timer = -1
            precharge_req = await self.build_pre_charge_message()
            self.create_next_message(
                DCPreCharge,
                precharge_req,
                Timeouts.DC_PRE_CHARGE_REQ,
                Namespace.ISO_V20_DC,
                ISOV20PayloadTypes.DC_MAINSTREAM,
            )
        else:
            elapsed_time: float = 0
            if self.comm_session.ongoing_timer >= 0:
                elapsed_time = time.time() - self.comm_session.ongoing_timer
                if elapsed_time > Timeouts.V2G_EVCC_CABLE_CHECK_TIMEOUT:
                    self.stop_state_machine("Ongoing timer timed out for CableCheck")
                    return
            else:
                self.comm_session.ongoing_timer = time.time()

            cable_check_req = DCCableCheckReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                )
            )
            self.create_next_message(
                None,
                cable_check_req,
                Timeouts.DC_CABLE_CHECK_REQ,
                Namespace.ISO_V20_DC,
                ISOV20PayloadTypes.DC_MAINSTREAM,
            )

    async def build_pre_charge_message(self):
        present_voltage = await self.comm_session.ev_controller.get_present_voltage()
        processing = Processing.ONGOING
        dc_pre_charge_req = DCPreChargeReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            ev_processing=processing,
            ev_present_voltage=present_voltage,
            ev_target_voltage=await self.comm_session.ev_controller.get_target_voltage(),  # noqa
        )
        return dc_pre_charge_req


class DCPreCharge(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a
    DCPreChargeRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.DC_PRE_CHARGE_REQ)
        self.pre_charge_finished_message_built_once = False

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, DCPreChargeRes)
        if not msg:
            return

        precharge_res: DCPreChargeRes = cast(DCPreChargeRes, msg)
        next_state = None
        if (
            await self.comm_session.ev_controller.is_precharged(
                precharge_res.evse_present_voltage
            )
            and self.pre_charge_finished_message_built_once
        ):
            next_state = PowerDelivery
            next_request = await self.build_power_delivery_req()
            payload_type = ISOV20PayloadTypes.MAINSTREAM
            namespace = Namespace.ISO_V20_COMMON_MSG
            timeout = Timeouts.POWER_DELIVERY_REQ
        else:
            next_request = await self.build_pre_charge_message(
                precharge_res.evse_present_voltage
            )
            payload_type = ISOV20PayloadTypes.DC_MAINSTREAM
            timeout = Timeouts.DC_PRE_CHARGE_REQ
            namespace = Namespace.ISO_V20_DC
            self.pre_charge_finished_message_built_once = True

        self.create_next_message(
            next_state,
            next_request,
            timeout,
            namespace,
            payload_type,
        )

    async def build_power_delivery_req(self):
        if self.comm_session.control_mode == ControlMode.SCHEDULED:
            (
                ev_power_profile,
                charge_progress,
            ) = await self.comm_session.ev_controller.process_scheduled_se_params(
                self.comm_session.schedule_exchange_res.scheduled_params,
                self.comm_session.schedule_exchange_res.go_to_pause,
            )
        else:
            (
                ev_power_profile,
                charge_progress,
            ) = await self.comm_session.ev_controller.process_dynamic_se_params(
                self.comm_session.schedule_exchange_res.dynamic_params,
                self.comm_session.schedule_exchange_res.go_to_pause,
            )

        ev_processing = Processing.FINISHED
        self.comm_session.ev_processing = Processing.FINISHED
        if not ev_power_profile:
            ev_processing = Processing.ONGOING
            self.comm_session.ev_processing = Processing.ONGOING

        # Information from EV to show if charging or discharging is planned
        bpt_channel_selection = None
        if self.comm_session.selected_energy_service.service in (
            ServiceV20.AC_BPT,
            ServiceV20.DC_BPT,
        ):
            bpt_channel_selection = ChannelSelection.CHARGE
            if ev_power_profile is not None:
                power_value = ev_power_profile.entry_list.entries[-1].power.value
                if power_value < 0:
                    bpt_channel_selection = ChannelSelection.DISCHARGE
        power_delivery_req = PowerDeliveryReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            ev_processing=ev_processing,
            charge_progress=charge_progress,
            ev_power_profile=ev_power_profile,
            bpt_channel_selection=bpt_channel_selection,
        )
        return power_delivery_req

    async def build_pre_charge_message(self, evse_voltage: RationalNumber):
        present_voltage = await self.comm_session.ev_controller.get_present_voltage()
        is_precharged = await self.comm_session.ev_controller.is_precharged(
            evse_voltage
        )
        processing = Processing.ONGOING
        if is_precharged:
            processing = Processing.FINISHED
        dc_pre_charge_req = DCPreChargeReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            ev_processing=processing,
            ev_present_voltage=present_voltage,
            ev_target_voltage=await self.comm_session.ev_controller.get_target_voltage(),  # noqa
        )
        return dc_pre_charge_req


class DCChargeLoop(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a
    DCChargeLoopRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.DC_CHARGE_LOOP_REQ)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, DCChargeLoopRes)
        if not msg:
            return

        charge_loop_res: DCChargeLoopRes = cast(DCChargeLoopRes, msg)

        # if charge_loop_res.evse_power_limit_achieved:
        #     self.stop_v20_charging(False)

        if charge_loop_res.evse_status:
            renegotiation = False
            evse_notification = charge_loop_res.evse_status.evse_notification
            if evse_notification not in [
                EVSENotification.SERVICE_RENEGOTIATION,
                EVSENotification.TERMINATE,
            ]:
                raise NotImplementedError(
                    f"Processing for EVSE Notification "
                    f"{evse_notification} is not "
                    f"supported at the moment"
                )
            if evse_notification == EVSENotification.SERVICE_RENEGOTIATION:
                renegotiation = True
            self.stop_v20_charging(
                next_state=PowerDelivery, renegotiate_requested=renegotiation
            )

        elif await self.comm_session.ev_controller.continue_charging():
            try:
                delay: int = (
                    await self.comm_session.ev_controller.charge_loop_delay()
                )  # noqa
                logger.info(f"Next ChargeLoop Req in {delay} seconds")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.info(f"No delay for the next ChargeLoop Req. Reason {e}")
            current_demand_req = await self.build_current_demand_data()

            self.create_next_message(
                None,
                current_demand_req,
                Timeouts.DC_CHARGE_LOOP_REQ,
                Namespace.ISO_V20_DC,
                ISOV20PayloadTypes.DC_MAINSTREAM,
            )
        else:
            self.stop_v20_charging(next_state=PowerDelivery)

    async def build_current_demand_data(self):
        scheduled_params, dynamic_params = None, None
        bpt_scheduled_params, bpt_dynamic_params = None, None
        if self.comm_session.selected_energy_service.service == ServiceV20.DC:
            if self.comm_session.control_mode == ControlMode.SCHEDULED:
                scheduled_params = (
                    await self.comm_session.ev_controller.get_scheduled_dc_charge_loop_params()  # noqa
                )
            else:
                dynamic_params = (
                    await self.comm_session.ev_controller.get_dynamic_dc_charge_loop_params()  # noqa
                )
        elif self.comm_session.selected_energy_service.service == ServiceV20.DC_BPT:
            if self.comm_session.control_mode == ControlMode.SCHEDULED:
                bpt_scheduled_params = (
                    await self.comm_session.ev_controller.get_bpt_scheduled_dc_charge_loop_params()  # noqa
                )
            else:
                bpt_dynamic_params = (
                    await self.comm_session.ev_controller.get_bpt_dynamic_dc_charge_loop_params()  # noqa
                )

        dc_charge_loop_req = DCChargeLoopReq(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            display_parameters=await self.comm_session.ev_controller.get_display_params(),  # noqa
            ev_present_voltage=await self.comm_session.ev_controller.get_present_voltage(),  # noqa
            scheduled_params=scheduled_params,
            dynamic_params=dynamic_params,
            bpt_scheduled_params=bpt_scheduled_params,
            bpt_dynamic_params=bpt_dynamic_params,
            meter_info_requested=False,
        )
        return dc_charge_loop_req


class DCWeldingDetection(StateEVCC):
    """
    The ISO 15118-20 state in which the EVCC processes a
    DCWeldingDetectionRes from the SECC.
    """

    def __init__(self, comm_session: EVCCCommunicationSession):
        super().__init__(comm_session, Timeouts.DC_WELDING_DETECTION_REQ)
        self.welding_detection_complete = False

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        if self.comm_session.ongoing_timer > 0:
            elapsed_time = time.time() - self.comm_session.ongoing_timer
            logger.debug(f"EVCC timeout : {Timeouts.V2G_EVCC_ONGOING_TIMEOUT}")
            if elapsed_time > Timeouts.V2G_EVCC_ONGOING_TIMEOUT:
                self.stop_state_machine(
                    "Ongoing timer timed out for " "WeldingDetectionRes"
                )
                return
        elif self.comm_session.ongoing_timer == -1:
            self.comm_session.ongoing_timer = time.time()

        if self.welding_detection_complete:
            session_stop_req = SessionStopReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                charging_session=ChargingSession.TERMINATE,
            )
            next_state = SessionStop
            next_request: V2GRequest = session_stop_req
            next_timeout = Timeouts.SESSION_STOP_REQ
            namespace = Namespace.ISO_V20_COMMON_MSG
            next_payload_type = ISOV20PayloadTypes.MAINSTREAM
        else:
            processing = Processing.ONGOING
            if await self.comm_session.ev_controller.welding_detection_has_finished():
                processing = Processing.FINISHED
                self.welding_detection_complete = True
            next_request = DCWeldingDetectionReq(
                header=MessageHeader(
                    session_id=self.comm_session.session_id,
                    timestamp=time.time(),
                ),
                ev_processing=processing,
            )
            next_state = None
            next_timeout = Timeouts.DC_WELDING_DETECTION_REQ
            namespace = Namespace.ISO_V20_DC
            next_payload_type = ISOV20PayloadTypes.DC_MAINSTREAM

        self.create_next_message(
            next_state, next_request, next_timeout, namespace, next_payload_type
        )
```

## File: iso15118/secc/controller/interface.py
```python
"""
This module contains the abstract class for an SECC to retrieve data from the EVSE
(Electric Vehicle Supply Equipment).
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, cast

from iso15118.secc.controller.ev_data import EVDataContext
from iso15118.secc.controller.evse_data import CurrentType, EVSEDataContext
from iso15118.shared.messages.datatypes import (
    DCEVSEChargeParameter,
    DCEVSEStatus,
    PhysicalValue,
    PVEVSEMaxCurrent,
    PVEVSEMaxCurrentLimit,
    PVEVSEMaxPowerLimit,
    PVEVSEMaxVoltageLimit,
    PVEVSEPresentCurrent,
    PVEVSEPresentVoltage,
)
from iso15118.shared.messages.din_spec.datatypes import (
    ResponseCode as ResponseCodeDINSPEC,
)
from iso15118.shared.messages.din_spec.datatypes import (
    SAScheduleTupleEntry as SAScheduleTupleEntryDINSPEC,
)
from iso15118.shared.messages.enums import (
    AuthorizationStatus,
    AuthorizationTokenType,
    ControlMode,
    CpState,
    EnergyTransferModeEnum,
    IsolationLevel,
    Protocol,
    ServiceV20,
    SessionStopAction,
    UnitSymbol,
)
from iso15118.shared.messages.iso15118_2.datatypes import (
    ACEVSEChargeParameter,
    ACEVSEStatus,
)
from iso15118.shared.messages.iso15118_2.datatypes import MeterInfo as MeterInfoV2
from iso15118.shared.messages.iso15118_2.datatypes import ResponseCode as ResponseCodeV2
from iso15118.shared.messages.iso15118_2.datatypes import (
    SAScheduleTuple,
)
from iso15118.shared.messages.iso15118_20.ac import (
    ACChargeParameterDiscoveryResParams,
    BPTACChargeParameterDiscoveryResParams,
    BPTDynamicACChargeLoopResParams,
    BPTScheduledACChargeLoopResParams,
    DynamicACChargeLoopResParams,
    ScheduledACChargeLoopResParams,
)
from iso15118.shared.messages.iso15118_20.common_messages import (
    DynamicScheduleExchangeResParams,
    ProviderID,
    ScheduledScheduleExchangeResParams,
    ScheduleExchangeReq,
    SelectedEnergyService,
    ServiceList,
    ServiceParameterList,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    EVSEStatus,
)
from iso15118.shared.messages.iso15118_20.common_types import MeterInfo as MeterInfoV20
from iso15118.shared.messages.iso15118_20.common_types import (
    RationalNumber,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    ResponseCode as ResponseCodeV20,
)
from iso15118.shared.messages.iso15118_20.dc import (
    BPTDCChargeParameterDiscoveryResParams,
    BPTDynamicDCChargeLoopRes,
    BPTScheduledDCChargeLoopResParams,
    DCChargeParameterDiscoveryResParams,
    DynamicDCChargeLoopRes,
    ScheduledDCChargeLoopResParams,
)
from iso15118.shared.states import State

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationResponse:
    authorization_status: AuthorizationStatus
    certificate_response_status: Optional[
        Union[ResponseCodeV2, ResponseCodeV20, ResponseCodeDINSPEC]
    ] = None


class ServiceStatus(str, Enum):
    READY = "ready"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    BUSY = "busy"


class EVSEControllerInterface(ABC):
    def __init__(self):
        self.ev_data_context = EVDataContext()
        self.evse_data_context = EVSEDataContext()

        self._selected_protocol: Optional[Protocol] = None

    def reset_ev_data_context(self):
        self.ev_data_context = EVDataContext()

    def get_ev_data_context(self) -> EVDataContext:
        return self.ev_data_context

    def set_evse_data_context(self, evse_data_context: EVSEDataContext) -> None:
        self.evse_data_context = evse_data_context

    def get_evse_data_context(self) -> EVSEDataContext:
        return self.evse_data_context

    # ============================================================================
    # |             COMMON FUNCTIONS (FOR ALL ENERGY TRANSFER MODES)             |
    # ============================================================================

    @abstractmethod
    async def set_status(self, status: ServiceStatus) -> None:
        """
        Sets the new status for the EVSE Controller
        """
        raise NotImplementedError

    @abstractmethod
    async def get_evse_id(self, protocol: Protocol) -> str:
        """
        Gets the ID of the EVSE (Electric Vehicle Supply Equipment), which is
        controlling the energy flow to the connector the EV is plugged into.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_supported_energy_transfer_modes(
        self, protocol: Protocol
    ) -> List[EnergyTransferModeEnum]:
        """
        The available energy transfer modes, which depends on the socket the EV is
        connected to.

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_schedule_exchange_params(
        self,
        selected_energy_service: SelectedEnergyService,
        control_mode: ControlMode,
        schedule_exchange_req: ScheduleExchangeReq,
    ) -> Union[ScheduledScheduleExchangeResParams, DynamicScheduleExchangeResParams]:
        """
        Gets the parameters for a ScheduleExchangeResponse.
        If the parameters are not yet ready when requested,
        return None.

        Args:
            selected_energy_service: The energy services, which the EVCC selected.
                                     The selected parameter set, that is associated
                                     with that energy service, influences the
                                     parameters for the ScheduleExchangeRes
            control_mode: Control mode for this session - Scheduled/Dynamic
            schedule_exchange_req: The ScheduleExchangeReq, whose parameters influence
                                   the parameters for the ScheduleExchangeRes

        Returns:
            Parameters for the ScheduleExchangeRes, if
            readily available. If you're still waiting for all parameters, return None.

        Relevant for:
        - ISO 15118-20
        """

    @abstractmethod
    async def get_energy_service_list(self) -> ServiceList:
        """
        The available energy transfer services

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    def is_eim_authorized(self) -> bool:
        """
        it returns true when an rfid authentication before plugging in.
        Relevant for:
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def is_authorized(
        self,
        id_token: Optional[str] = None,
        id_token_type: Optional[AuthorizationTokenType] = None,
        certificate_chain: Optional[bytes] = None,
        hash_data: Optional[List[Dict[str, str]]] = None,
    ) -> AuthorizationResponse:
        """
        Provides the information on whether or not the user is authorized to charge at
        this EVSE. The auth token could be an RFID card, a whitelisted MAC address
        of the EV (Autocharge), a contract certificate (Plug & Charge), or a payment
        authorization via NFC or credit card.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_sa_schedule_list(
        self,
        ev_data_context: EVDataContext,
        is_free_charging_service: bool,
        max_schedule_entries: Optional[int],
        departure_time: int = 0,
    ) -> Optional[List[SAScheduleTuple]]:
        """
        Requests the charging schedule from a secondary actor (SA) like a
        charge point operator, if available. If no backend information is given
        regarding the restrictions imposed on an EV charging profile, then the
        charging schedule is solely influenced by the max rating of the charger
        and the ampacity of the charging cable.

        Args:
            ev_data_context: contains all the limits of the EV for AC and DC
            is_free_charging_service: Indicates if free sa schedules are to be returned.
            max_schedule_entries: The maximum amount of schedule entries the EVCC
                                  can handle, or None if not provided
            departure_time: The departure time given in seconds from the time of
                            sending the ChargeParameterDiscoveryReq. If the
                            request doesn't provide a departure time, then this
                            implies the need to start charging immediately.

        Returns:
            A list of SAScheduleTupleEntry values to influence the EV's charging profile
            if the backend/charger can provide the information already, or None if
            the calculation is still ongoing.

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_sa_schedule_list_dinspec(
        self, max_schedule_entries: Optional[int], departure_time: int = 0
    ) -> Optional[List[SAScheduleTupleEntryDINSPEC]]:
        """
        Requests the charging schedule from a secondary actor (SA) like a
        charge point operator, if available. If no backend information is given
        regarding the restrictions imposed on an EV charging profile, then the
        charging schedule is solely influenced by the max rating of the charger
        and the ampacity of the charging cable.

        Args:
            max_schedule_entries: The maximum amount of schedule entries the EVCC
                                  can handle, or None if not provided
            departure_time: The departure time given in seconds from the time of
                            sending the ChargeParameterDiscoveryReq. If the
                            request doesn't provide a departure time, then this
                            implies the need to start charging immediately.

        Returns:
            A list of SAScheduleTupleEntry values to influence the EV's charging profile
            if the backend/charger can provide the information already, or None if
            the calculation is still ongoing.

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_meter_info_v2(self) -> MeterInfoV2:
        """
        Provides the MeterInfo from the EVSE's smart meter

        Returns:
            A MeterInfo instance, which contains the meter reading

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_meter_info_v20(self) -> MeterInfoV20:
        """
        Provides the MeterInfo from the EVSE's smart meter

        Returns:
            A MeterInfo instance, which contains the meter reading

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_supported_providers(self) -> Optional[List[ProviderID]]:
        """
        Provides a list of eMSPs (E-Mobility Service Providers) supported by the SECC.
        This allows EVCC to filter the list of contract certificates to be utilized
        during the authorization.

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def set_hlc_charging(self, is_ongoing: bool) -> None:
        """
        Notify that high level communication is ongoing or not.
        Args:
            is_ongoing (bool): whether hlc charging is ongoing or not.
        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_cp_state(self) -> CpState:
        """
        Returns current cp state

        Relevant for:
        - IEC 61851-1
        """
        raise NotImplementedError

    @abstractmethod
    async def service_renegotiation_supported(self) -> bool:
        """
        Whether or not service renegotiation is supported

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_service_parameter_list(
        self, service_id: int
    ) -> Optional[ServiceParameterList]:
        """
        Provides a list of parameters for a specific service ID for which the EVCC
        requests additional information.

        Args:
            service_id: The service ID, according to Table 204 (ISO 15118-20)

        Returns:
            A ServiceParameterList instance for the requested service ID, or None if
            that service is not supported.

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def stop_charger(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def is_contactor_opened(self) -> bool:
        """
        This method is used to check if the contactor is open.
        Used in PowerDelivery when the EV requests to
        stop energy transfer.

        Relevant for:
        - all protocols
        """
        raise NotImplementedError

    @abstractmethod
    async def is_contactor_closed(self) -> Optional[bool]:
        """
        This method is used to check if the contactor is closed.
        In AC, this method is called in PowerDelivery when the EV requests to
        start energy transfer.
        In DC, this method is called during CableCheck.

        Relevant for:
        - all protocols
        """
        raise NotImplementedError

    @abstractmethod
    async def get_evse_status(self) -> Optional[EVSEStatus]:
        """
        Gets the status of the EVSE

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def set_present_protocol_state(self, state: State):
        """
        This method sets the present state of the charging protocol.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        """
        raise NotImplementedError

    def set_selected_protocol(self, protocol: Protocol) -> None:
        """Set the selected Protocol.

        Args:
            protocol: An EV communication protocol supported by Josev.
        """
        self._selected_protocol = protocol

    def get_selected_protocol(self) -> Optional[Protocol]:
        """Get the selected Protocol."""
        return self._selected_protocol

    # ============================================================================
    # |                          AC-SPECIFIC FUNCTIONS                           |
    # ============================================================================

    @abstractmethod
    async def get_ac_evse_status(self) -> ACEVSEStatus:
        """
        Gets the AC-specific EVSE status information

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_ac_charge_params_v2(self) -> ACEVSEChargeParameter:
        """
        Gets the AC-specific EVSE charge parameter (for ChargeParameterDiscoveryRes)

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_ac_charge_params_v20(
        self, energy_service: ServiceV20
    ) -> Optional[
        Union[
            ACChargeParameterDiscoveryResParams, BPTACChargeParameterDiscoveryResParams
        ]
    ]:
        """
        Gets the charge parameters needed for a ChargeParameterDiscoveryRes for
        AC/AC_BPT charging.

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    async def get_ac_charge_loop_params_v20(
        self, control_mode: ControlMode, selected_service: ServiceV20
    ) -> Union[
        ScheduledACChargeLoopResParams,
        BPTScheduledACChargeLoopResParams,
        DynamicACChargeLoopResParams,
        BPTDynamicACChargeLoopResParams,
    ]:
        """
        Gets the parameters for the ACChargeLoopRes for the currently set control mode
         and service.
        Args:
            control_mode: Control mode for this session - Scheduled/Dynamic
            selected_service: Enum for this Service - AC/AC_BPT
        Returns:
            ChargeLoop params depending on the selected mode. Return object could be
            one of the following types:
            [
                ScheduledACChargeLoopResParams,
                BPTScheduledACChargeLoopResParams,
                DynamicACChargeLoopResParams,
                BPTDynamicACChargeLoopResParams,
            ]
        Relevant for:
        - ISO 15118-20
        """
        evse_session_limits = self.evse_data_context.session_limits.ac_limits

        def get_target_power_limits():
            active_discharge_mode = False
            reactive_discharge_mode = False

            if (evse_session_limits.max_charge_power or 0) > 0 and (
                evse_session_limits.max_discharge_power or 0
            ) > 0:
                logger.error(
                    "Both Max Charge and Discharge power are set, "
                    "Just one is allowed at a time. Ignoring Discharge setpoint."
                )
                target_active_power = evse_session_limits.max_charge_power
            elif evse_session_limits.max_charge_power > 0:
                target_active_power = evse_session_limits.max_charge_power
            elif evse_session_limits.max_discharge_power > 0:
                active_discharge_mode = True
                target_active_power = (-1) * evse_session_limits.max_discharge_power
            else:
                logger.warning("No Active Power setpoint is provided. Setting to 0.")
                target_active_power = 0

            if (evse_session_limits.max_charge_reactive_power or 0) > 0 and (
                evse_session_limits.max_discharge_reactive_power or 0
            ) > 0:
                logger.error(
                    "Both Max Reactive Charge and Discharge power are set, "
                    "Just one is allowed at a time. "
                    "Ignoring Reactive Discharge setpoint."
                )
                target_reactive_power = evse_session_limits.max_charge_reactive_power
            elif evse_session_limits.max_charge_reactive_power or 0 > 0:
                target_reactive_power = evse_session_limits.max_charge_reactive_power
            elif evse_session_limits.max_discharge_reactive_power or 0 > 0:
                reactive_discharge_mode = True
                target_reactive_power = (
                    -1
                ) * evse_session_limits.max_discharge_reactive_power
            else:
                logger.warning("No Reactive Power setpoint is provided. Setting to 0.")
                target_reactive_power = 0

            # Conversion to RationalNumber
            target_active_power = RationalNumber.get_rational_repr(target_active_power)
            target_reactive_power = RationalNumber.get_rational_repr(
                target_reactive_power
            )
            return (
                target_active_power,
                active_discharge_mode,
                target_reactive_power,
                reactive_discharge_mode,
            )

        def get_phase_power_limits(active_discharge_mode, reactive_discharge_mode):
            target_active_power_l2 = target_active_power_l3 = None
            target_reactive_power_l2 = target_reactive_power_l3 = None

            if active_discharge_mode:
                if evse_session_limits.max_discharge_power_l2:
                    target_active_power_l2 = (
                        -1
                    ) * evse_session_limits.max_discharge_power_l2
                    target_active_power_l2 = RationalNumber.get_rational_repr(
                        target_active_power_l2
                    )
                if evse_session_limits.max_discharge_power_l3:
                    target_active_power_l3 = (
                        -1
                    ) * evse_session_limits.max_discharge_power_l3
                    target_active_power_l3 = RationalNumber.get_rational_repr(
                        target_active_power_l3
                    )
            else:
                if evse_session_limits.max_charge_power_l2:
                    target_active_power_l2 = evse_session_limits.max_charge_power_l2
                    target_active_power_l2 = RationalNumber.get_rational_repr(
                        target_active_power_l2
                    )
                if evse_session_limits.max_charge_power_l3:
                    target_active_power_l3 = evse_session_limits.max_charge_power_l3
                    target_active_power_l3 = RationalNumber.get_rational_repr(
                        target_active_power_l3
                    )

            if reactive_discharge_mode:
                if evse_session_limits.max_discharge_reactive_power_l2:
                    target_reactive_power_l2 = (
                        -1
                    ) * evse_session_limits.max_discharge_reactive_power_l2
                    target_reactive_power_l2 = RationalNumber.get_rational_repr(
                        target_reactive_power_l2
                    )
                if evse_session_limits.max_discharge_reactive_power_l3:
                    target_reactive_power_l3 = (
                        -1
                    ) * evse_session_limits.max_discharge_reactive_power_l3
                    target_reactive_power_l3 = RationalNumber.get_rational_repr(
                        target_reactive_power_l3
                    )
            else:
                if evse_session_limits.max_charge_reactive_power_l2:
                    target_reactive_power_l2 = (
                        evse_session_limits.max_charge_reactive_power_l2
                    )
                    target_reactive_power_l2 = RationalNumber.get_rational_repr(
                        target_reactive_power_l2
                    )
                if evse_session_limits.max_charge_reactive_power_l3:
                    target_reactive_power_l3 = (
                        evse_session_limits.max_charge_reactive_power_l3
                    )
                    target_reactive_power_l3 = RationalNumber.get_rational_repr(
                        target_reactive_power_l3
                    )

            return (
                target_active_power_l2,
                target_active_power_l3,
                target_reactive_power_l2,
                target_reactive_power_l3,
            )

        # Targets derivation based on the session limits
        (
            target_active_power,
            active_discharge_mode,
            target_reactive_power,
            reactive_discharge_mode,
        ) = get_target_power_limits()
        (
            target_active_power_l2,
            target_active_power_l3,
            target_reactive_power_l2,
            target_reactive_power_l3,
        ) = get_phase_power_limits(active_discharge_mode, reactive_discharge_mode)

        present_active_power = RationalNumber.get_rational_repr(
            self.evse_data_context.present_active_power
        )
        present_active_power_l2 = RationalNumber.get_rational_repr(
            self.evse_data_context.present_active_power_l2
        )
        present_active_power_l3 = RationalNumber.get_rational_repr(
            self.evse_data_context.present_active_power_l3
        )

        if (
            control_mode == ControlMode.DYNAMIC
            and selected_service == ServiceV20.AC_BPT
        ):
            return BPTDynamicACChargeLoopResParams(
                evse_target_active_power=target_active_power,
                evse_target_active_power_l2=target_active_power_l2,
                evse_target_active_power_l3=target_active_power_l3,
                evse_target_reactive_power=target_reactive_power,
                evse_target_reactive_power_l2=target_reactive_power_l2,
                evse_target_reactive_power_l3=target_reactive_power_l3,
                evse_present_active_power=present_active_power,
                evse_present_active_power_l2=present_active_power_l2,
                evse_present_active_power_l3=present_active_power_l3,
            )
        elif (
            control_mode == ControlMode.SCHEDULED
            and selected_service == ServiceV20.AC_BPT
        ):
            return BPTScheduledACChargeLoopResParams(
                evse_target_active_power=target_active_power,
                evse_target_active_power_l2=target_active_power_l2,
                evse_target_active_power_l3=target_active_power_l3,
                evse_target_reactive_power=target_reactive_power,
                evse_target_reactive_power_l2=target_reactive_power_l2,
                evse_target_reactive_power_l3=target_reactive_power_l3,
                evse_present_active_power=present_active_power,
                evse_present_active_power_l2=present_active_power_l2,
                evse_present_active_power_l3=present_active_power_l3,
            )
        elif control_mode == ControlMode.DYNAMIC and selected_service == ServiceV20.AC:
            return DynamicACChargeLoopResParams(
                evse_target_active_power=target_active_power,
                evse_target_active_power_l2=target_active_power_l2,
                evse_target_active_power_l3=target_active_power_l3,
                evse_target_reactive_power=target_reactive_power,
                evse_target_reactive_power_l2=target_reactive_power_l2,
                evse_target_reactive_power_l3=target_reactive_power_l3,
                evse_present_active_power=present_active_power,
                evse_present_active_power_l2=present_active_power_l2,
                evse_present_active_power_l3=present_active_power_l3,
            )
        else:
            return ScheduledACChargeLoopResParams(
                evse_target_active_power=target_active_power,
                evse_target_active_power_l2=target_active_power_l2,
                evse_target_active_power_l3=target_active_power_l3,
                evse_target_reactive_power=target_reactive_power,
                evse_target_reactive_power_l2=target_reactive_power_l2,
                evse_target_reactive_power_l3=target_reactive_power_l3,
                evse_present_active_power=present_active_power,
                evse_present_active_power_l2=present_active_power_l2,
                evse_present_active_power_l3=present_active_power_l3,
            )

    # ============================================================================
    # |                          DC-SPECIFIC FUNCTIONS                           |
    # ============================================================================

    @abstractmethod
    async def get_dc_evse_status(self) -> DCEVSEStatus:
        """
        Gets the DC-specific EVSE status information

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def get_dc_charge_parameters(self) -> DCEVSEChargeParameter:
        """
        Gets the DC-specific EVSE charge parameter (for ChargeParameterDiscoveryRes)

        Relevant for:
        - ISO 15118-2
        """
        raise NotImplementedError

    async def get_dc_charge_parameters_dinspec(self) -> DCEVSEChargeParameter:
        """
        Gets the DC-specific EVSE charge parameter (for ChargeParameterDiscoveryRes)

        Relevant for:
        - ISO 15118-2
        """
        return await self.get_dc_charge_parameters()

    async def get_dc_charge_parameters_v2(self) -> DCEVSEChargeParameter:
        """
        Gets the DC-specific EVSE charge parameter (for ChargeParameterDiscoveryRes)

        Relevant for:
        - ISO 15118-2
        """
        return await self.get_dc_charge_parameters()

    async def get_evse_present_voltage(
        self, protocol: Protocol
    ) -> Union[PVEVSEPresentVoltage, RationalNumber]:
        """
        Gets the presently available voltage at the EVSE

        Relevant for:
        - ISO 15118-2
        - ISO 15118-20
        - DINSPEC
        """
        if protocol in [Protocol.DIN_SPEC_70121, Protocol.ISO_15118_2]:
            exponent, value = PhysicalValue.get_exponent_value_repr(
                cast(int, self.evse_data_context.present_voltage)
            )
            return PVEVSEPresentVoltage(multiplier=exponent, value=value, unit="V")
        else:
            return RationalNumber.get_rational_repr(
                self.evse_data_context.present_voltage
            )

    async def get_evse_present_current(
        self, protocol: Protocol
    ) -> Union[PVEVSEPresentCurrent, RationalNumber]:
        """
        Gets the presently available current at the EVSE

        Relevant for:
        - ISO 15118-2
        - ISO 15118-20
        - DINSPEC
        """
        if protocol in [Protocol.DIN_SPEC_70121, Protocol.ISO_15118_2]:
            exponent, value = PhysicalValue.get_exponent_value_repr(
                cast(int, self.evse_data_context.present_current)
            )
            return PVEVSEPresentCurrent(multiplier=exponent, value=value, unit="A")
        else:
            return RationalNumber.get_rational_repr(
                self.evse_data_context.present_current
            )

    @abstractmethod
    async def start_cable_check(self):
        """
        This method is called at the beginning of the state CableCheck.
        It requests the charger to perform a CableCheck

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def get_cable_check_status(self) -> Union[IsolationLevel, None]:
        """
        This method is called at the beginning of the state CableCheck.
        Gets's the status of a previously started CableCheck

        Relevant for:
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def send_charging_command(
        self,
        ev_target_voltage: Optional[float],
        ev_target_current: Optional[float],
        is_precharge: bool = False,
        is_session_bpt: bool = False,
    ):
        """
        This method is called in the state CurrentDemand/DCChargeLoop.
        The values target current and target voltage from the EV are passed.
        The fields discharge_current and discharge_power are relevant during discharge
        in 15118-20. This information must be provided to the charger's
         power electronics.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError

    @abstractmethod
    async def is_evse_current_limit_achieved(self):
        """
        Returns true if the current limit of the charger has achieved

        Relevant for:
        - ISO 15118-2
        """
        # TODO retrieve from evse data context
        raise NotImplementedError

    @abstractmethod
    async def is_evse_voltage_limit_achieved(self):
        """
        Returns true if the current limit of the charger has achieved

        Relevant for:
        - ISO 15118-2
        """
        # TODO retrieve from evse data context
        return NotImplementedError

    @abstractmethod
    async def is_evse_power_limit_achieved(self) -> bool:
        """
        Returns true if the current limit of the charger has achieved

        Relevant for:
        - ISO 15118-2
        """
        # TODO retrieve from evse data context
        return False

    async def get_evse_max_voltage_limit(self) -> PVEVSEMaxVoltageLimit:
        """
        Gets the max voltage that can be provided by the charger

        Relevant for:
        - ISO 15118-2
        """
        session_limits = self.evse_data_context.session_limits
        if self.evse_data_context.current_type == CurrentType.AC:
            voltage_limit = self.evse_data_context.nominal_voltage
        else:
            voltage_limit = session_limits.dc_limits.max_voltage
        exponent, value = PhysicalValue.get_exponent_value_repr(voltage_limit)
        return PVEVSEMaxVoltageLimit(
            multiplier=exponent,
            value=value,
            unit=UnitSymbol.VOLTAGE,
        )

    async def get_evse_max_current_limit(
        self,
    ) -> Union[PVEVSEMaxCurrentLimit, PVEVSEMaxCurrent]:
        """
        Gets the max current that can be provided by the charger

        Relevant for:
        - ISO 15118-2
        """
        # This is currently being used by -2 only.
        logger.info(
            "Extracting the Session Current Limit " "based on Session Limits with. "
        )
        logger.debug("This method is used both in CPD and " "ChargeLoop in -2")
        session_limits = self.evse_data_context.session_limits
        rated_limits = self.evse_data_context.rated_limits
        if self.evse_data_context.current_type == CurrentType.AC:
            logger.debug("Gettint EVSE Max Current for AC...")
            logger.debug(f"Active Rated Limits: {rated_limits.ac_limits}")
            logger.debug(f"Active Session Limits: {session_limits.ac_limits}")
            ac_limits = session_limits.ac_limits
            if ac_limits.max_charge_power > 0:
                logger.info("Applying a Charging limit")
                total_power_limit: float = ac_limits.max_charge_power
                if ac_limits.max_charge_power_l2:
                    total_power_limit += ac_limits.max_charge_power_l2
                if ac_limits.max_charge_power_l3:
                    total_power_limit += ac_limits.max_charge_power_l3
            elif ac_limits.max_discharge_power and ac_limits.max_discharge_power > 0:
                logger.info("Applying a Discharging limit")
                total_power_limit = (-1) * ac_limits.max_discharge_power
                if ac_limits.max_discharge_power_l2:
                    total_power_limit -= ac_limits.max_discharge_power_l2
                if ac_limits.max_discharge_power_l3:
                    total_power_limit -= ac_limits.max_discharge_power_l3
            present_voltage = self.evse_data_context.present_voltage
            if present_voltage == 0:
                logger.warning(
                    "Present voltage and nominal voltage are 0,"
                    "using Nominal voltage as default"
                )
                present_voltage = self.evse_data_context.nominal_voltage
                if not present_voltage:
                    logger.error("Present voltage and nominal voltage are 0")
                    raise ValueError("Present voltage and nominal voltage are 0")
            logger.debug(f"Total Power Limit to Set: {total_power_limit}")
            current_limit_phase = total_power_limit / present_voltage
            logger.debug(f"Active EVSEMaxCurrent limit: {current_limit_phase}")
            exponent, value = PhysicalValue.get_exponent_value_repr(current_limit_phase)
            return PVEVSEMaxCurrent(
                multiplier=exponent,
                value=value,
                unit=UnitSymbol.AMPERE,
            )
        elif self.evse_data_context.current_type == CurrentType.DC:
            logger.debug("Getting EVSE Max Current for DC...")
            logger.debug(f"Active Rated Limits: {rated_limits.dc_limits}")
            logger.debug(f"Active Session Limits: {session_limits.dc_limits}")
            max_discharge_current = session_limits.dc_limits.max_discharge_current
            if max_discharge_current and max_discharge_current > 0:
                logger.info("Applying a Discharging limit")
                current_limit = (-1) * session_limits.dc_limits.max_discharge_current
            else:
                logger.info("Applying a Charging limit")
                current_limit = session_limits.dc_limits.max_charge_current
            logger.debug(f"Active EVSEMaxCurrentLimit: {current_limit}")
            exponent, value = PhysicalValue.get_exponent_value_repr(current_limit)
            return PVEVSEMaxCurrentLimit(
                multiplier=exponent,
                value=value,
                unit=UnitSymbol.AMPERE,
            )

    @abstractmethod
    async def get_dc_charge_params_v20(
        self, energy_service: ServiceV20
    ) -> Optional[
        Union[
            DCChargeParameterDiscoveryResParams, BPTDCChargeParameterDiscoveryResParams
        ]
    ]:
        """
        Gets the charge parameters needed for a ChargeParameterDiscoveryRes for
        DC charging.
        """
        raise NotImplementedError

    async def get_evse_max_power_limit(self) -> PVEVSEMaxPowerLimit:
        """
        Gets the max power that can be provided by the charger

        Relevant for:
        - ISO 15118-2
        """
        session_limits = self.evse_data_context.session_limits
        max_discharge_power = 0.0
        max_charge_power = 0.0
        if session_limits.dc_limits.max_discharge_power:
            max_discharge_power = session_limits.dc_limits.max_discharge_power
        else:
            max_charge_power = session_limits.dc_limits.max_charge_power
        # Update of the power limit based on the session limits
        if max_discharge_power > 0:
            power_limit = (-1) * max_discharge_power
        else:
            power_limit = max_charge_power
        exponent, value = PhysicalValue.get_exponent_value_repr(power_limit)
        return PVEVSEMaxPowerLimit(
            multiplier=exponent,
            value=value,
            unit=UnitSymbol.WATT,
        )

    async def get_dc_charge_loop_params_v20(
        self, control_mode: ControlMode, selected_service: ServiceV20
    ) -> Optional[
        Union[
            ScheduledDCChargeLoopResParams,
            BPTScheduledDCChargeLoopResParams,
            DynamicDCChargeLoopRes,
            BPTDynamicDCChargeLoopRes,
        ]
    ]:
        """
        Gets the parameters for the DCChargeLoopRes for the currently set control mode
         and service.
        Args:
            control_mode: Control mode for this session - Scheduled/Dynamic
            selected_service: Enum for this Service - DC/DC_BPT
        Returns:
            ChargeLoop params depending on the selected mode. Return object could be
            one of the following types:
            [
                ScheduledDCChargeLoopResParams,
                BPTScheduledDCChargeLoopResParams,
                DynamicDCChargeLoopRes,
                BPTDynamicDCChargeLoopRes,
            ]
        Relevant for:
        - ISO 15118-20
        """
        evse_session_limits = self.evse_data_context.session_limits.dc_limits
        evse_max_charge_power = evse_session_limits.max_charge_power
        evse_min_charge_power = evse_session_limits.min_charge_power
        evse_max_charge_current = evse_session_limits.max_charge_current
        evse_max_voltage = evse_session_limits.max_voltage
        if selected_service == ServiceV20.DC:
            if control_mode == ControlMode.SCHEDULED:
                scheduled_params = ScheduledDCChargeLoopResParams(
                    evse_maximum_charge_power=RationalNumber.get_rational_repr(
                        evse_max_charge_power
                    ),
                    evse_minimum_charge_power=RationalNumber.get_rational_repr(
                        evse_min_charge_power
                    ),
                    evse_maximum_charge_current=RationalNumber.get_rational_repr(
                        evse_max_charge_current
                    ),
                    evse_maximum_voltage=RationalNumber.get_rational_repr(
                        evse_max_voltage
                    ),
                )
                return scheduled_params
            elif control_mode == ControlMode.DYNAMIC:
                dynamic_params = DynamicDCChargeLoopRes(
                    departure_time=self.evse_data_context.departure_time,  # noqa
                    min_soc=self.evse_data_context.min_soc,
                    target_soc=self.evse_data_context.target_soc,
                    ack_max_delay=self.evse_data_context.ack_max_delay,
                    evse_maximum_charge_power=RationalNumber.get_rational_repr(
                        evse_max_charge_power
                    ),
                    evse_minimum_charge_power=RationalNumber.get_rational_repr(
                        evse_min_charge_power
                    ),
                    evse_maximum_charge_current=RationalNumber.get_rational_repr(
                        evse_max_charge_current
                    ),
                    evse_maximum_voltage=RationalNumber.get_rational_repr(
                        evse_max_voltage
                    ),
                )
                return dynamic_params
            return None
        elif selected_service == ServiceV20.DC_BPT:
            evse_max_discharge_power = evse_session_limits.max_discharge_power
            evse_min_discharge_power = evse_session_limits.min_discharge_power
            evse_max_discharge_current = evse_session_limits.max_discharge_current
            evse_min_voltage = evse_session_limits.min_voltage
            if control_mode == ControlMode.SCHEDULED:
                bpt_scheduled_params = BPTScheduledDCChargeLoopResParams(
                    evse_maximum_charge_power=RationalNumber.get_rational_repr(
                        evse_max_charge_power
                    ),
                    evse_minimum_charge_power=RationalNumber.get_rational_repr(
                        evse_min_charge_power
                    ),
                    evse_maximum_charge_current=RationalNumber.get_rational_repr(
                        evse_max_charge_current
                    ),
                    evse_maximum_voltage=RationalNumber.get_rational_repr(
                        evse_max_voltage
                    ),
                    evse_max_discharge_power=RationalNumber.get_rational_repr(
                        evse_max_discharge_power
                    ),
                    evse_min_discharge_power=RationalNumber.get_rational_repr(
                        evse_min_discharge_power
                    ),
                    evse_max_discharge_current=RationalNumber.get_rational_repr(
                        evse_max_discharge_current
                    ),
                    evse_min_voltage=RationalNumber.get_rational_repr(evse_min_voltage),
                )
                return bpt_scheduled_params
            else:
                bpt_dynamic_params = BPTDynamicDCChargeLoopRes(
                    departure_time=self.evse_data_context.departure_time,  # noqa
                    min_soc=self.evse_data_context.min_soc,
                    target_soc=self.evse_data_context.target_soc,
                    ack_max_delay=self.evse_data_context.ack_max_delay,
                    evse_maximum_charge_power=RationalNumber.get_rational_repr(
                        evse_max_charge_power
                    ),
                    evse_minimum_charge_power=RationalNumber.get_rational_repr(
                        evse_min_charge_power
                    ),
                    evse_maximum_charge_current=RationalNumber.get_rational_repr(
                        evse_max_charge_current
                    ),
                    evse_maximum_voltage=RationalNumber.get_rational_repr(
                        evse_max_voltage
                    ),
                    evse_max_discharge_power=RationalNumber.get_rational_repr(
                        evse_max_discharge_power
                    ),
                    evse_min_discharge_power=RationalNumber.get_rational_repr(
                        evse_min_discharge_power
                    ),
                    evse_max_discharge_current=RationalNumber.get_rational_repr(
                        evse_max_discharge_current
                    ),
                    evse_min_voltage=RationalNumber.get_rational_repr(evse_min_voltage),
                )
                return bpt_dynamic_params
        else:
            logger.error(f"Energy service {selected_service.name} not yet supported")
            return None

    @abstractmethod
    async def get_15118_ev_certificate(
        self, base64_encoded_cert_installation_req: str, namespace: str
    ) -> str:
        """
        Used to fetch base64 encoded CertificateInstallationRes from CPO backend.
        Args:
         base64_encoded_cert_installation_req : This is the CertificateInstallationReq
         from the EV in base64 encoded form.
         namespace: This would be the namespace to be passed to the backend and depends
          on the protocol.
         15118-2:  "urn:iso:15118:2:2013:MsgDef"
         15118-20: "urn:iso:std:iso:15118:-20:CommonMessages"
        Returns:
         CertificateInstallationRes EXI stream in base64 encoded form.

        Relevant for:
        - ISO 15118-20 and ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    async def update_data_link(self, action: SessionStopAction) -> None:
        """
        Called when EV requires termination or pausing of the charging session.
        Args:
            action : SessionStopAction
        Relevant for:
        - ISO 15118-20 and ISO 15118-2
        """
        raise NotImplementedError

    @abstractmethod
    def ready_to_charge(self) -> bool:
        """
        Used by Authorization state to indicate if we are
        ready to start charging.
        """
        raise NotImplementedError

    @abstractmethod
    async def session_ended(self, current_state: str, reason: str):
        """
        Indicate the reason for stopping charging.
        """
        raise NotImplementedError

    @abstractmethod
    async def send_display_params(self):
        """
        Share display params with CS.
        """
        raise NotImplementedError

    @abstractmethod
    async def send_rated_limits(self):
        """
        This method is called in the state ChargeParameterDiscovery state for all
        protocols.
        The message is used to share the physical limitations of the EV (perhaps
        for this session alone) with the charging station.

        Relevant for:
        - DIN SPEC 70121
        - ISO 15118-2
        - ISO 15118-20
        """
        raise NotImplementedError
```

## File: iso15118/secc/controller/simulator.py
```python
"""
This module contains the code to retrieve (hardware-related) data from the EVSE
(Electric Vehicle Supply Equipment).
"""

import base64
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from iso15118.secc.controller.common import UnknownEnergyService
from iso15118.secc.controller.evse_data import (
    EVSEACCLLimits,
    EVSEACCPDLimits,
    EVSEDataContext,
    EVSEDCCLLimits,
    EVSEDCCPDLimits,
    EVSERatedLimits,
    EVSESessionLimits,
)
from iso15118.secc.controller.interface import (
    AuthorizationResponse,
    EVDataContext,
    EVSEControllerInterface,
    ServiceStatus,
)
from iso15118.shared.exceptions import EncryptionError, PrivateKeyReadError
from iso15118.shared.exi_codec import EXI
from iso15118.shared.messages.datatypes import (
    DCEVSEChargeParameter,
    DCEVSEStatus,
    DCEVSEStatusCode,
)
from iso15118.shared.messages.datatypes import EVSENotification as EVSENotificationV2
from iso15118.shared.messages.datatypes import (
    PVEVSEMaxCurrentLimit,
    PVEVSEMaxPowerLimit,
    PVEVSEMaxVoltageLimit,
    PVEVSEMinCurrentLimit,
    PVEVSEMinVoltageLimit,
    PVEVSEPeakCurrentRipple,
)
from iso15118.shared.messages.din_spec.datatypes import (
    PMaxScheduleEntry as PMaxScheduleEntryDINSPEC,
)
from iso15118.shared.messages.din_spec.datatypes import (
    PMaxScheduleEntryDetails as PMaxScheduleEntryDetailsDINSPEC,
)
from iso15118.shared.messages.din_spec.datatypes import (
    RelativeTimeInterval as RelativeTimeIntervalDINSPEC,
)
from iso15118.shared.messages.din_spec.datatypes import (
    ResponseCode as ResponseCodeDINSPEC,
)
from iso15118.shared.messages.din_spec.datatypes import (
    SAScheduleTupleEntry as SAScheduleTupleEntryDINSPEC,
)
from iso15118.shared.messages.enums import (
    AuthorizationStatus,
    AuthorizationTokenType,
    ControlMode,
    CpState,
    EnergyTransferModeEnum,
    IsolationLevel,
    Namespace,
    PriceAlgorithm,
    Protocol,
    ServiceV20,
    SessionStopAction,
    UnitSymbol,
)
from iso15118.shared.messages.iso15118_2.body import (
    Body,
    CertificateInstallationReq,
    CertificateInstallationRes,
)
from iso15118.shared.messages.iso15118_2.datatypes import (
    EMAID,
    ACEVSEChargeParameter,
    ACEVSEStatus,
    CertificateChain,
    DHPublicKey,
    EncryptedPrivateKey,
)
from iso15118.shared.messages.iso15118_2.datatypes import MeterInfo as MeterInfoV2
from iso15118.shared.messages.iso15118_2.datatypes import (
    PMaxSchedule,
    PMaxScheduleEntry,
    PVEVSEMaxCurrent,
    PVEVSENominalVoltage,
    PVPMax,
    RelativeTimeInterval,
)
from iso15118.shared.messages.iso15118_2.datatypes import ResponseCode as ResponseCodeV2
from iso15118.shared.messages.iso15118_2.datatypes import (
    SalesTariff,
    SalesTariffEntry,
    SAScheduleTuple,
    SubCertificates,
)
from iso15118.shared.messages.iso15118_2.header import MessageHeader as MessageHeaderV2
from iso15118.shared.messages.iso15118_2.msgdef import V2GMessage as V2GMessageV2
from iso15118.shared.messages.iso15118_20.ac import (
    ACChargeParameterDiscoveryResParams,
    BPTACChargeParameterDiscoveryResParams,
)
from iso15118.shared.messages.iso15118_20.common_messages import (
    AbsolutePriceSchedule,
    AdditionalService,
    AdditionalServiceList,
    ChargingSchedule,
    DynamicScheduleExchangeResParams,
    OverstayRule,
    OverstayRuleList,
    Parameter,
    ParameterSet,
    PowerSchedule,
    PowerScheduleEntry,
    PowerScheduleEntryList,
    PriceLevelSchedule,
    PriceLevelScheduleEntry,
    PriceLevelScheduleEntryList,
    PriceRule,
    PriceRuleStack,
    PriceRuleStackList,
    ProviderID,
    ScheduledScheduleExchangeResParams,
    ScheduleExchangeReq,
    ScheduleTuple,
    SelectedEnergyService,
    Service,
    ServiceList,
    ServiceParameterList,
    TaxRule,
    TaxRuleList,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    EVSEStatus,
)
from iso15118.shared.messages.iso15118_20.common_types import MeterInfo as MeterInfoV20
from iso15118.shared.messages.iso15118_20.common_types import (
    RationalNumber,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    ResponseCode as ResponseCodeV20,
)
from iso15118.shared.messages.iso15118_20.dc import (
    BPTDCChargeParameterDiscoveryResParams,
    DCChargeParameterDiscoveryResParams,
)
from iso15118.shared.security import (
    CertPath,
    KeyEncoding,
    KeyPasswordPath,
    KeyPath,
    create_signature,
    encrypt_priv_key,
    get_cert_cn,
    load_cert,
    load_priv_key,
)
from iso15118.shared.states import State

logger = logging.getLogger(__name__)


def get_evse_context():
    ac_limits = EVSEACCPDLimits(
        max_current=10,
        max_charge_power=10,
        min_charge_power=10,
        max_charge_power_l2=10,
        max_charge_power_l3=10,
        min_charge_power_l2=10,
        min_charge_power_l3=10,
        max_discharge_power=10,
        min_discharge_power=10,
        max_discharge_power_l2=10,
        max_discharge_power_l3=10,
        min_discharge_power_l2=10,
        min_discharge_power_l3=10,
    )
    dc_limits = EVSEDCCPDLimits(
        max_charge_power=10,
        min_charge_power=10,
        max_charge_current=10,
        min_charge_current=10,
        max_voltage=10,
        min_voltage=10,
        # 15118-20 DC BPT
        max_discharge_power=10,
        min_discharge_power=10,
        max_discharge_current=10,
        min_discharge_current=10,
    )
    ac_cl_limits = EVSEACCLLimits(
        max_charge_power=10,
        max_charge_power_l2=10,
        max_charge_power_l3=10,
        max_charge_reactive_power=10,
        max_charge_reactive_power_l2=10,
        max_charge_reactive_power_l3=10,
        # BPT attributes
        max_discharge_power=10,
        max_discharge_power_l2=10,
        max_discharge_power_l3=10,
        max_discharge_reactive_power=10,
        max_discharge_reactive_power_l2=10,
        max_discharge_reactive_power_l3=10,
    )
    dc_cl_limits = EVSEDCCLLimits(
        # Optional in 15118-20 DC CL (Scheduled)
        max_charge_power=10,
        min_charge_power=10,
        max_charge_current=10,
        max_voltage=10,
        # Optional and present in 15118-20 DC BPT CL (Scheduled)
        max_discharge_power=10,
        min_discharge_power=10,
        max_discharge_current=10,
        min_voltage=10,
    )
    rated_limits: EVSERatedLimits = EVSERatedLimits(
        ac_limits=ac_limits,
        dc_limits=dc_limits,
    )

    session_limits: EVSESessionLimits = EVSESessionLimits(
        ac_limits=ac_cl_limits,
        dc_limits=dc_cl_limits,
    )
    evse_data_context = EVSEDataContext(
        rated_limits=rated_limits, session_limits=session_limits
    )
    evse_data_context.nominal_voltage = 10
    evse_data_context.nominal_frequency = 10
    evse_data_context.max_power_asymmetry = 10
    evse_data_context.power_ramp_limit = 10
    evse_data_context.present_active_power = 10
    evse_data_context.present_active_power_l2 = 10
    evse_data_context.present_active_power_l3 = 10
    evse_data_context.current_regulation_tolerance = 10
    evse_data_context.energy_to_be_delivered = 10
    evse_data_context.present_current = 1
    evse_data_context.present_voltage = 1
    return evse_data_context


class SimEVSEController(EVSEControllerInterface):
    """
    A simulated version of an EVSE controller
    """

    def __init__(self):
        super().__init__()
        self.ev_data_context = EVDataContext()
        # ── Battery Health Test state ──────────────────────────────────────
        self._health_test_active: bool = False
        self._health_phase: str = "CHARGE"   # "CHARGE" | "DISCHARGE"
        self._health_cycles: list = []
        self._health_energy_wh: float = 0.0
        self._health_temperature_c: float = 25.0
        self._health_c_rate: float = 5.0
        self._health_cutoff_soc: int = 20
        # ──────────────────────────────────────────────────────────────────
        self.evse_data_context = get_evse_context()

    def reset_ev_data_context(self):
        self.ev_data_context = EVDataContext()

    # ============================================================================
    # |             COMMON FUNCTIONS (FOR ALL ENERGY TRANSFER MODES)             |
    # ============================================================================
    async def set_status(self, status: ServiceStatus) -> None:
        logger.debug(f"New Status: {status}")

    async def get_evse_id(self, protocol: Protocol) -> str:
        if protocol == Protocol.DIN_SPEC_70121:
            #  To transform a string-based DIN SPEC 91286 EVSE ID to hexBinary
            #  representation and vice versa, the following conversion rules shall
            #  be used for each character and hex digit: '0' <--> 0x0, '1' <--> 0x1,
            #  '2' <--> 0x2, '3' <--> 0x3, '4' <--> 0x4, '5' <--> 0x5, '6' <--> 0x6,
            #  '7' <--> 0x7, '8' <--> 0x8, '9' <--> 0x9, '*' <--> 0xA,
            #  Unused <--> 0xB .. 0xF.
            # Example: The DIN SPEC 91286 EVSE ID “49*89*6360” is represented
            # as “0x49 0xA8 0x9A 0x63 0x60”.
            return "49A89A6360"
        """Overrides EVSEControllerInterface.get_evse_id()."""
        return "UK123E1234"

    async def get_supported_energy_transfer_modes(
        self, protocol: Protocol
    ) -> List[EnergyTransferModeEnum]:
        """Overrides EVSEControllerInterface.get_supported_energy_transfer_modes()."""
        if protocol == Protocol.DIN_SPEC_70121:
            """
            For DIN SPEC, only DC_CORE and DC_EXTENDED are supported.
            The other DC modes DC_COMBO_CORE and DC_DUAL are out of scope for DIN SPEC
            """
            dc_extended = EnergyTransferModeEnum.DC_EXTENDED
            return [dc_extended]

        # It's not valid to have mixed energy transfer modes associated with
        # a single EVSE. Providing this here only for simulation purposes.
        # ac_single_phase = EnergyTransferModeEnum.AC_SINGLE_PHASE_CORE
        ac_three_phase = EnergyTransferModeEnum.AC_THREE_PHASE_CORE
        dc_extended = EnergyTransferModeEnum.DC_EXTENDED
        return [dc_extended, ac_three_phase]

    async def get_schedule_exchange_params(
        self,
        selected_energy_service: SelectedEnergyService,
        control_mode: ControlMode,
        schedule_exchange_req: ScheduleExchangeReq,
    ) -> Union[ScheduledScheduleExchangeResParams, DynamicScheduleExchangeResParams]:
        if control_mode == ControlMode.SCHEDULED:
            return await self.get_scheduled_se_params(
                selected_energy_service, schedule_exchange_req
            )
        else:
            return await self.get_dynamic_se_params(
                selected_energy_service, schedule_exchange_req
            )

    async def get_scheduled_se_params(
        self,
        selected_energy_service: SelectedEnergyService,
        schedule_exchange_req: ScheduleExchangeReq,
    ) -> ScheduledScheduleExchangeResParams:
        """Overrides EVSEControllerInterface.get_scheduled_se_params()."""
        charging_power_schedule_entry = PowerScheduleEntry(
            duration=3600,
            power=RationalNumber(exponent=3, value=10),
            # Check if AC ThreePhase applies (Connector parameter within parameter set
            # of SelectedEnergyService) if you want to add power_l2 and power_l3 values
        )

        charging_power_schedule = PowerSchedule(
            time_anchor=0,
            available_energy=RationalNumber(exponent=3, value=300),
            power_tolerance=RationalNumber(exponent=0, value=2000),
            schedule_entry_list=PowerScheduleEntryList(
                entries=[charging_power_schedule_entry]
            ),
        )

        tax_rule = TaxRule(
            tax_rule_id=1,
            tax_rule_name="What a great tax rule",
            tax_rate=RationalNumber(exponent=0, value=10),
            tax_included_in_price=False,
            applies_to_energy_fee=True,
            applies_to_parking_fee=True,
            applies_to_overstay_fee=True,
            applies_to_min_max_cost=True,
        )

        tax_rules = TaxRuleList(tax_rule=[tax_rule])

        price_rule = PriceRule(
            energy_fee=RationalNumber(exponent=0, value=20),
            parking_fee=RationalNumber(exponent=0, value=0),
            parking_fee_period=0,
            carbon_dioxide_emission=0,
            renewable_energy_percentage=0,
            power_range_start=RationalNumber(exponent=0, value=0),
        )

        price_rule_stack = PriceRuleStack(duration=3600, price_rules=[price_rule])

        price_rule_stacks = PriceRuleStackList(price_rule_stacks=[price_rule_stack])

        overstay_rule = OverstayRule(
            description="What a great description",
            start_time=0,
            fee=RationalNumber(exponent=0, value=50),
            fee_period=3600,
        )

        overstay_rules = OverstayRuleList(
            time_threshold=3600,
            power_threshold=RationalNumber(exponent=3, value=30),
            rules=[overstay_rule],
        )

        additional_service = AdditionalService(
            service_name="What a great service name",
            service_fee=RationalNumber(exponent=0, value=0),
        )

        additional_services = AdditionalServiceList(
            additional_services=[additional_service]
        )

        charging_absolute_price_schedule = AbsolutePriceSchedule(
            time_anchor=0,
            schedule_id=1,
            currency="EUR",
            language="ENG",
            price_algorithm=PriceAlgorithm.POWER,
            min_cost=RationalNumber(exponent=0, value=1),
            max_cost=RationalNumber(exponent=0, value=10),
            tax_rules=tax_rules,
            price_rule_stacks=price_rule_stacks,
            overstay_rules=overstay_rules,
            additional_services=additional_services,
        )

        discharging_power_schedule_entry = PowerScheduleEntry(
            duration=3600,
            power=RationalNumber(exponent=3, value=10),
            # Check if AC ThreePhase applies (Connector parameter within parameter set
            # of SelectedEnergyService) if you want to add power_l2 and power_l3 values
        )

        discharging_power_schedule = PowerSchedule(
            time_anchor=0,
            schedule_entry_list=PowerScheduleEntryList(
                entries=[discharging_power_schedule_entry]
            ),
        )

        discharging_absolute_price_schedule = charging_absolute_price_schedule

        charging_schedule = ChargingSchedule(
            power_schedule=charging_power_schedule,
            absolute_price_schedule=charging_absolute_price_schedule,
        )

        discharging_schedule = ChargingSchedule(
            power_schedule=discharging_power_schedule,
            absolute_price_schedule=discharging_absolute_price_schedule,
        )

        schedule_tuple = ScheduleTuple(
            schedule_tuple_id=1,
            charging_schedule=charging_schedule,
            discharging_schedule=discharging_schedule,
        )

        scheduled_params = ScheduledScheduleExchangeResParams(
            schedule_tuples=[schedule_tuple]
        )

        return scheduled_params

    async def get_service_parameter_list(
        self, service_id: int
    ) -> Optional[ServiceParameterList]:
        """Overrides EVSEControllerInterface.get_service_parameter_list()."""
        parameter_sets_list: List[ParameterSet] = []

        try:
            connector_parameter = Parameter(name="Connector", int_value=2)

            nominal_voltage = 400

            nominal_voltage_parameter = Parameter(
                name="EVSENominalVoltage", int_value=nominal_voltage
            )
            # TODO: map the pricing type
            pricing_parameter = Parameter(name="Pricing", int_value=0)

            parameter_set_id: int = 1
            # According to the spec, both EVSE and EV must offer Scheduled = 1 and
            # Dynamic = 2 control modes
            # As the EVCC Simulator will choose the first parameter set by default,
            # we first advertise the one with Dynamic control mode 2
            # The env variable 15118_20_PRIORITIZE_DYNAMIC_CONTROL_MODE is provided
            # if this is to be inverted. When set, the first parameter set will be for
            # scheduled control mode. This will be removed soon. For testing purposes
            # only.
            control_modes = [1, 2]

            for control_mode in control_modes:
                control_mode_parameter = Parameter(
                    name="ControlMode", int_value=control_mode
                )
                mobility_needs_parameter = Parameter(
                    name="MobilityNeedsMode", int_value=control_mode
                )
                parameters_list: list = [
                    connector_parameter,
                    nominal_voltage_parameter,
                    pricing_parameter,
                    control_mode_parameter,
                    mobility_needs_parameter,
                ]
                parameter_set = ParameterSet(
                    id=parameter_set_id, parameters=parameters_list
                )
                parameter_sets_list.append(parameter_set)
                # increment the parameter set id for the next set of them
                parameter_set_id += 1
                if control_mode == 2:
                    # [V2G20-2663]:The SECC shall only offer MobilityNeedsMode equal
                    # to ‘2’ when ControlMode is set to ‘2’ (Dynamic).
                    # So, for Dynamic mode the MobilityNeeds can have the value
                    # of 1 or 2 so in this if clause we insert another parameter set
                    # for Dynamic mode but for MobilityNeedsMode = 1 (MobilityNeeds
                    # provided by the EVCC).
                    parameters_list.remove(mobility_needs_parameter)
                    mobility_needs_parameter = Parameter(
                        name="MobilityNeedsMode", int_value=1
                    )
                    parameters_list.append(mobility_needs_parameter)
                    parameter_set = ParameterSet(
                        id=parameter_set_id, parameters=parameters_list
                    )
                    parameter_sets_list.append(parameter_set)
                    # increment the parameter set id for the next set
                    parameter_set_id += 1
        except AttributeError as e:
            logger.error(
                f"No ServiceParameterList available for service ID {service_id}"
            )
            raise e

        # ── Battery Health Test parameter set (DC_BPT only) ──────────────────
        # When the EVCC requests ServiceDetail for DC_BPT (service_id=6),
        # advertise an extra ParameterSet with TestMode=HealthDischarge.
        # The EVCC reads this and activates the two-phase health test flow.
        if service_id == 6:
            health_test_params = [
                Parameter(name="Connector", int_value=2),
                Parameter(name="EVSENominalVoltage", int_value=400),
                Parameter(name="Pricing", int_value=0),
                Parameter(name="ControlMode", int_value=1),   # Scheduled
                Parameter(name="MobilityNeedsMode", int_value=1),
                Parameter(name="TestMode", int_value=1),       # 1 = HealthDischarge
                Parameter(name="TestCRate", int_value=50),      # 5C discharge
                Parameter(name="CutoffSOC", int_value=20),     # stop at 20%
            ]
            parameter_sets_list.append(
                ParameterSet(id=parameter_set_id, parameters=health_test_params)
            )
        # ──────────────────────────────────────────────────────────────────────

        return ServiceParameterList(parameter_sets=parameter_sets_list)

    async def get_dynamic_se_params(
        self,
        selected_energy_service: SelectedEnergyService,
        schedule_exchange_req: ScheduleExchangeReq,
    ) -> DynamicScheduleExchangeResParams:
        """Overrides EVSEControllerInterface.get_dynamic_se_params()."""
        price_level_schedule_entry = PriceLevelScheduleEntry(
            duration=3600, price_level=1
        )

        schedule_entries = PriceLevelScheduleEntryList(
            entries=[price_level_schedule_entry]
        )

        price_level_schedule = PriceLevelSchedule(
            id="id1",
            time_anchor=0,
            schedule_id=1,
            schedule_description="What a great description",
            num_price_levels=1,
            schedule_entries=schedule_entries,
        )

        dynamic_params = DynamicScheduleExchangeResParams(
            departure_time=7200,
            min_soc=30,
            target_soc=80,
            price_level_schedule=price_level_schedule,
        )

        return dynamic_params

    async def get_energy_service_list(self) -> ServiceList:
        """Overrides EVSEControllerInterface.get_energy_service_list()."""
        # AC = 1, DC = 2, AC_BPT = 5, DC_BPT = 6;
        # DC_ACDP = 4 and DC_ADCP_BPT NOT supported

        current_protocol = self.get_selected_protocol()
        if current_protocol == Protocol.ISO_15118_20_DC:
            service_ids = [2, 6]
        elif current_protocol == Protocol.ISO_15118_20_AC:
            service_ids = [1, 5]

        service_list: ServiceList = ServiceList(services=[])
        for service_id in service_ids:
            service_list.services.append(
                Service(service_id=service_id, free_service=False)
            )

        return service_list

    def is_eim_authorized(self) -> bool:
        """Overrides EVSEControllerInterface.is_eim_authorized()."""
        return False

    async def is_authorized(
        self,
        id_token: Optional[str] = None,
        id_token_type: Optional[AuthorizationTokenType] = None,
        certificate_chain: Optional[bytes] = None,
        hash_data: Optional[List[Dict[str, str]]] = None,
    ) -> AuthorizationResponse:
        """Overrides EVSEControllerInterface.is_authorized()."""
        protocol = self.get_selected_protocol()
        response_code: Optional[
            Union[ResponseCodeDINSPEC, ResponseCodeV2, ResponseCodeV20]
        ] = None
        if protocol == Protocol.DIN_SPEC_70121:
            response_code = ResponseCodeDINSPEC.OK
        elif protocol == Protocol.ISO_15118_20_COMMON_MESSAGES:
            response_code = ResponseCodeV20.OK
        else:
            response_code = ResponseCodeV2.OK

        return AuthorizationResponse(
            authorization_status=AuthorizationStatus.ACCEPTED,
            certificate_response_status=response_code,
        )

    async def get_sa_schedule_list_dinspec(
        self, max_schedule_entries: Optional[int], departure_time: int = 0
    ) -> Optional[List[SAScheduleTupleEntryDINSPEC]]:
        """Overrides EVSEControllerInterface.get_sa_schedule_list_dinspec()."""
        sa_schedule_list: List[SAScheduleTupleEntryDINSPEC] = []
        entry_details = PMaxScheduleEntryDetailsDINSPEC(
            p_max=200, time_interval=RelativeTimeIntervalDINSPEC(start=0, duration=3600)
        )
        p_max_schedule_entries = [entry_details]
        pmax_schedule_entry = PMaxScheduleEntryDINSPEC(
            p_max_schedule_id=0, entry_details=p_max_schedule_entries
        )

        sa_schedule_tuple_entry = SAScheduleTupleEntryDINSPEC(
            sa_schedule_tuple_id=1,
            p_max_schedule=pmax_schedule_entry,
            sales_tariff=None,
        )
        sa_schedule_list.append(sa_schedule_tuple_entry)
        return sa_schedule_list

    async def get_sa_schedule_list(
        self,
        ev_data_context: EVDataContext,
        is_free_charging_service: bool,
        max_schedule_entries: Optional[int],
        departure_time: int = 0,
    ) -> Optional[List[SAScheduleTuple]]:
        """Overrides EVSEControllerInterface.get_sa_schedule_list()."""
        sa_schedule_list: List[SAScheduleTuple] = []

        if departure_time == 0:
            # [V2G2-304] If no departure_time is provided, the sum of the individual
            # time intervals shall be greater than or equal to 24 hours.
            departure_time = 86400

        # PMaxSchedule entries
        schedule_entries = []
        # SalesTariff
        sales_tariff_entries: List[SalesTariffEntry] = []
        remaining_charge_duration = departure_time
        counter = 1
        start = 0
        current_pmax_val = 7000
        while remaining_charge_duration > 0:
            if current_pmax_val == 7000:
                p_max = PVPMax(multiplier=0, value=11000, unit=UnitSymbol.WATT)
                current_pmax_val = 11000
            else:
                p_max = PVPMax(multiplier=0, value=7000, unit=UnitSymbol.WATT)
                current_pmax_val = 7000

            p_max_schedule_entry = PMaxScheduleEntry(
                p_max=p_max, time_interval=RelativeTimeInterval(start=start)
            )

            sales_tariff_entry = SalesTariffEntry(
                e_price_level=counter,
                time_interval=RelativeTimeInterval(start=start),
            )

            if remaining_charge_duration <= 86400:
                p_max_schedule_entry = PMaxScheduleEntry(
                    p_max=p_max,
                    time_interval=RelativeTimeInterval(
                        start=start, duration=remaining_charge_duration
                    ),
                )

                sales_tariff_entry = SalesTariffEntry(
                    e_price_level=counter,
                    time_interval=RelativeTimeInterval(
                        start=start, duration=remaining_charge_duration
                    ),
                )

            remaining_charge_duration -= 86400
            start += 86400
            counter += 1
            schedule_entries.append(p_max_schedule_entry)
            sales_tariff_entries.append(sales_tariff_entry)

        p_max_schedule = PMaxSchedule(schedule_entries=schedule_entries)

        sales_tariff = SalesTariff(
            id="id1",
            sales_tariff_id=10,  # a random id
            sales_tariff_entry=sales_tariff_entries,
            num_e_price_levels=len(sales_tariff_entries),
        )

        # Putting the list of SAScheduleTuple entries together
        sa_schedule_tuple = SAScheduleTuple(
            sa_schedule_tuple_id=1,
            p_max_schedule=p_max_schedule,
            sales_tariff=None if is_free_charging_service else sales_tariff,
        )

        # TODO We could also implement an optional SalesTariff, but for the sake of
        #      time we'll do that later (after the basics are implemented).
        #      When implementing the SalesTariff, we also need to apply a digital
        #      signature to it.
        sa_schedule_list.append(sa_schedule_tuple)

        # TODO We need to take care of [V2G2-741], which says that the SECC needs to
        #      resend a previously agreed SAScheduleTuple and the "period of time
        #      this SAScheduleTuple applies for shall be reduced by the time already
        #      elapsed".

        return sa_schedule_list

    async def get_meter_info_v2(self) -> MeterInfoV2:
        """Overrides EVSEControllerInterface.get_meter_info_v2()."""
        return MeterInfoV2(
            meter_id="Switch-Meter-123", meter_reading=12345, t_meter=time.time()
        )

    async def get_meter_info_v20(self) -> MeterInfoV20:
        """Overrides EVSEControllerInterface.get_meter_info_v20()."""
        return MeterInfoV20(
            meter_id="Switch-Meter-123",
            charged_energy_reading_wh=10,
            meter_timestamp=time.time(),
        )

    async def get_supported_providers(self) -> Optional[List[ProviderID]]:
        """Overrides EVSEControllerInterface.get_supported_providers()."""
        return None

    async def set_hlc_charging(self, is_ongoing: bool) -> None:
        """Overrides EVSEControllerInterface.set_hlc_charging()."""
        pass

    async def stop_charger(self) -> None:
        pass

    async def get_cp_state(self) -> CpState:
        """Overrides EVSEControllerInterface.set_cp_state()."""
        return CpState.C2

    async def service_renegotiation_supported(self) -> bool:
        """Overrides EVSEControllerInterface.service_renegotiation_supported()."""
        return False

    async def is_contactor_closed(self) -> Optional[bool]:
        """Overrides EVSEControllerInterface.is_contactor_closed()."""
        return True

    async def is_contactor_opened(self) -> bool:
        """Overrides EVSEControllerInterface.is_contactor_opened()."""
        return True

    async def get_evse_status(self) -> Optional[EVSEStatus]:
        """Overrides EVSEControllerInterface.get_evse_status()."""
        # TODO: this function can be generic to all protocols.
        #       We can make use of the method `get_evse_id`
        #       or other way to get the evse_id to request
        #       status of a specific evse_id. We can also use the
        #       `self.comm_session.protocol` obtained during SAP,
        #       and inject its value into the `get_evse_status`
        #       to decide on providing the -2ß EVSEStatus or the
        #       -2 AC or DC one and the `selected_charging_type_is_ac` in -2
        #       to decide on returning the ACEVSEStatus or the DCEVSEStatus
        #
        # Just as an example, here is how the return could look like
        # from iso15118.shared.messages.iso15118_20.common_types import (
        #    EVSENotification as EVSENotificationV20,
        # )
        # return EVSEStatus(
        #        notification_max_delay=0,
        #        evse_notification=EVSENotificationV20.TERMINATE
        #    )
        return None

    async def set_present_protocol_state(self, state: State):
        logger.info(f"iso15118 state: {str(state)}")

    # ============================================================================
    # |                          AC-SPECIFIC FUNCTIONS                           |
    # ============================================================================

    async def get_ac_evse_status(self) -> ACEVSEStatus:
        """Overrides EVSEControllerInterface.get_ac_evse_status()."""
        return ACEVSEStatus(
            notification_max_delay=0,
            evse_notification=EVSENotificationV2.NONE,
            rcd=False,
        )

    async def get_ac_charge_params_v2(self) -> ACEVSEChargeParameter:
        """Overrides EVSEControllerInterface.get_ac_evse_charge_parameter()."""
        evse_nominal_voltage = PVEVSENominalVoltage(
            multiplier=0, value=400, unit=UnitSymbol.VOLTAGE
        )
        evse_max_current = PVEVSEMaxCurrent(
            multiplier=0, value=32, unit=UnitSymbol.AMPERE
        )
        return ACEVSEChargeParameter(
            ac_evse_status=await self.get_ac_evse_status(),
            evse_nominal_voltage=evse_nominal_voltage,
            evse_max_current=evse_max_current,
        )

    async def get_ac_charge_params_v20(
        self, energy_service: ServiceV20
    ) -> Optional[
        Union[
            ACChargeParameterDiscoveryResParams, BPTACChargeParameterDiscoveryResParams
        ]
    ]:
        """Overrides EVSEControllerInterface.get_ac_charge_params_v20()."""
        ac_charge_parameter_discovery_res_params = ACChargeParameterDiscoveryResParams(
            evse_max_charge_power=RationalNumber.get_rational_repr(30000),
            evse_max_charge_power_l2=RationalNumber.get_rational_repr(30000),
            evse_max_charge_power_l3=RationalNumber.get_rational_repr(30000),
            evse_min_charge_power=RationalNumber.get_rational_repr(100),
            evse_min_charge_power_l2=RationalNumber.get_rational_repr(100),
            evse_min_charge_power_l3=RationalNumber.get_rational_repr(100),
            evse_nominal_frequency=RationalNumber.get_rational_repr(50),
            max_power_asymmetry=RationalNumber.get_rational_repr(0),
            evse_power_ramp_limit=RationalNumber.get_rational_repr(100),
            evse_present_active_power=RationalNumber.get_rational_repr(0),
            evse_present_active_power_l2=RationalNumber.get_rational_repr(0),
            evse_present_active_power_l3=RationalNumber.get_rational_repr(0),
        )
        if energy_service == ServiceV20.AC:
            return ac_charge_parameter_discovery_res_params
        elif energy_service == ServiceV20.AC_BPT:
            return BPTACChargeParameterDiscoveryResParams(
                **(ac_charge_parameter_discovery_res_params.dict()),
                evse_max_discharge_power=RationalNumber.get_rational_repr(30000),
                evse_max_discharge_power_l2=RationalNumber.get_rational_repr(30000),
                evse_max_discharge_power_l3=RationalNumber.get_rational_repr(30000),
                evse_min_discharge_power=RationalNumber.get_rational_repr(100),
                evse_min_discharge_power_l2=RationalNumber.get_rational_repr(100),
                evse_min_discharge_power_l3=RationalNumber.get_rational_repr(100),
            )
        else:
            raise UnknownEnergyService(f"Unknown Service {energy_service}")

    # ============================================================================
    # |                          DC-SPECIFIC FUNCTIONS                           |
    # ============================================================================

    async def get_dc_evse_status(self) -> DCEVSEStatus:
        """Overrides EVSEControllerInterface.get_dc_evse_status()."""
        return DCEVSEStatus(
            evse_notification=EVSENotificationV2.NONE,
            notification_max_delay=0,
            evse_isolation_status=IsolationLevel.VALID,
            evse_status_code=DCEVSEStatusCode.EVSE_READY,
        )

    async def get_dc_charge_parameters(self) -> DCEVSEChargeParameter:
        """Overrides EVSEControllerInterface.get_dc_evse_charge_parameter()."""
        return DCEVSEChargeParameter(
            dc_evse_status=DCEVSEStatus(
                notification_max_delay=100,
                evse_notification=EVSENotificationV2.NONE,
                evse_isolation_status=IsolationLevel.VALID,
                evse_status_code=DCEVSEStatusCode.EVSE_READY,
            ),
            evse_maximum_power_limit=PVEVSEMaxPowerLimit(
                multiplier=1, value=230, unit="W"
            ),
            evse_maximum_current_limit=PVEVSEMaxCurrentLimit(
                multiplier=1, value=4, unit="A"
            ),
            evse_maximum_voltage_limit=PVEVSEMaxVoltageLimit(
                multiplier=1, value=4, unit="V"
            ),
            evse_minimum_current_limit=PVEVSEMinCurrentLimit(
                multiplier=1, value=2, unit="A"
            ),
            evse_minimum_voltage_limit=PVEVSEMinVoltageLimit(
                multiplier=1, value=4, unit="V"
            ),
            evse_peak_current_ripple=PVEVSEPeakCurrentRipple(
                multiplier=1, value=4, unit="A"
            ),
        )

    async def start_cable_check(self):
        """Overrides EVSEControllerInterface.start_cable_check()."""
        pass

    async def get_cable_check_status(self) -> Union[IsolationLevel, None]:
        """Overrides EVSEControllerInterface.get_cable_check_status()."""
        return IsolationLevel.VALID

    async def send_charging_command(
        self,
        ev_target_voltage: Optional[float],
        ev_target_current: Optional[float],
        is_precharge: bool = False,
        is_session_bpt: bool = False,
    ):
        pass

    async def is_evse_current_limit_achieved(self) -> bool:
        return False

    async def is_evse_voltage_limit_achieved(self) -> bool:
        return False

    async def is_evse_power_limit_achieved(self) -> bool:
        return False

    async def get_evse_max_voltage_limit(self) -> PVEVSEMaxVoltageLimit:
        return PVEVSEMaxVoltageLimit(multiplier=0, value=600, unit="V")

    async def get_evse_max_current_limit(self) -> PVEVSEMaxCurrentLimit:
        return PVEVSEMaxCurrentLimit(multiplier=0, value=300, unit="A")

    async def get_evse_max_power_limit(self) -> PVEVSEMaxPowerLimit:
        return PVEVSEMaxPowerLimit(multiplier=1, value=1000, unit="W")

    async def get_dc_charge_params_v20(
        self, energy_service: ServiceV20
    ) -> Union[
        DCChargeParameterDiscoveryResParams, BPTDCChargeParameterDiscoveryResParams
    ]:
        """Override EVSEControllerInterface.get_dc_charge_params_v20()."""
        dc_charge_parameter_discovery_res = DCChargeParameterDiscoveryResParams(
            evse_max_charge_power=RationalNumber.get_rational_repr(1000),
            evse_min_charge_power=RationalNumber.get_rational_repr(100),
            evse_max_charge_current=RationalNumber.get_rational_repr(100),
            evse_min_charge_current=RationalNumber.get_rational_repr(10),
            evse_max_voltage=RationalNumber.get_rational_repr(500),
            evse_min_voltage=RationalNumber.get_rational_repr(10),
            evse_power_ramp_limit=RationalNumber.get_rational_repr(10),
        )
        if energy_service == ServiceV20.DC:
            return dc_charge_parameter_discovery_res
        elif energy_service == ServiceV20.DC_BPT:
            return BPTDCChargeParameterDiscoveryResParams(
                **(dc_charge_parameter_discovery_res.dict()),
                evse_max_discharge_power=RationalNumber.get_rational_repr(1000),
                evse_min_discharge_power=RationalNumber.get_rational_repr(100),
                evse_max_discharge_current=RationalNumber.get_rational_repr(100),
                evse_min_discharge_current=RationalNumber.get_rational_repr(10),
            )
        else:
            raise UnknownEnergyService(f"Unknown Service {energy_service}")

    async def get_15118_ev_certificate(
        self, base64_encoded_cert_installation_req: str, namespace: str
    ) -> str:
        """
        Overrides EVSEControllerInterface.get_15118_ev_certificate().

        Here we simply mock the actions of the backend.
        The code here is almost the same as what is done if USE_CPO_BACKEND
        is set to False. Except that both the request and response is base64 encoded.
        """
        cert_install_req_exi = base64.b64decode(base64_encoded_cert_installation_req)
        cert_install_req = EXI().from_exi(cert_install_req_exi, namespace)
        try:
            dh_pub_key, encrypted_priv_key_bytes = encrypt_priv_key(
                oem_prov_cert=load_cert(CertPath.OEM_LEAF_DER),
                priv_key_to_encrypt=load_priv_key(
                    KeyPath.CONTRACT_LEAF_PEM,
                    KeyEncoding.PEM,
                    KeyPasswordPath.CONTRACT_LEAF_KEY_PASSWORD,
                ),
            )
        except EncryptionError:
            raise EncryptionError(
                "EncryptionError while trying to encrypt the private key for the "
                "contract certificate"
            )
        except PrivateKeyReadError as exc:
            raise PrivateKeyReadError(
                f"Can't read private key to encrypt for CertificateInstallationRes:"
                f" {exc}"
            )

        # The elements that need to be part of the signature
        contract_cert_chain = CertificateChain(
            id="id1",
            certificate=load_cert(CertPath.CONTRACT_LEAF_DER),
            sub_certificates=SubCertificates(
                certificates=[
                    load_cert(CertPath.MO_SUB_CA2_DER),
                    load_cert(CertPath.MO_SUB_CA1_DER),
                ]
            ),
        )
        encrypted_priv_key = EncryptedPrivateKey(
            id="id2", value=encrypted_priv_key_bytes
        )
        dh_public_key = DHPublicKey(id="id3", value=dh_pub_key)
        emaid = EMAID(
            id="id4", value=get_cert_cn(load_cert(CertPath.CONTRACT_LEAF_DER))
        )
        cps_certificate_chain = CertificateChain(
            certificate=load_cert(CertPath.CPS_LEAF_DER),
            sub_certificates=SubCertificates(
                certificates=[
                    load_cert(CertPath.CPS_SUB_CA2_DER),
                    load_cert(CertPath.CPS_SUB_CA1_DER),
                ]
            ),
        )

        cert_install_res = CertificateInstallationRes(
            response_code=ResponseCodeV2.OK,
            cps_cert_chain=cps_certificate_chain,
            contract_cert_chain=contract_cert_chain,
            encrypted_private_key=encrypted_priv_key,
            dh_public_key=dh_public_key,
            emaid=emaid,
        )

        try:
            # Elements to sign, containing its id and the exi encoded stream
            contract_cert_tuple = (
                cert_install_res.contract_cert_chain.id,
                EXI().to_exi(
                    cert_install_res.contract_cert_chain, Namespace.ISO_V2_MSG_DEF
                ),
            )
            encrypted_priv_key_tuple = (
                cert_install_res.encrypted_private_key.id,
                EXI().to_exi(
                    cert_install_res.encrypted_private_key, Namespace.ISO_V2_MSG_DEF
                ),
            )
            dh_public_key_tuple = (
                cert_install_res.dh_public_key.id,
                EXI().to_exi(cert_install_res.dh_public_key, Namespace.ISO_V2_MSG_DEF),
            )
            emaid_tuple = (
                cert_install_res.emaid.id,
                EXI().to_exi(cert_install_res.emaid, Namespace.ISO_V2_MSG_DEF),
            )

            elements_to_sign = [
                contract_cert_tuple,
                encrypted_priv_key_tuple,
                dh_public_key_tuple,
                emaid_tuple,
            ]
            # The private key to be used for the signature
            signature_key = load_priv_key(
                KeyPath.CPS_LEAF_PEM,
                KeyEncoding.PEM,
                KeyPasswordPath.CPS_LEAF_KEY_PASSWORD,
            )

            signature = create_signature(elements_to_sign, signature_key)

        except PrivateKeyReadError as exc:
            raise Exception(
                "Can't read private key needed to create signature "
                f"for CertificateInstallationRes: {exc}",
            )
        except Exception as exc:
            raise Exception(f"Error creating signature {exc}")

        if isinstance(cert_install_req, CertificateInstallationReq):
            header = MessageHeaderV2(
                session_id=cert_install_req.header.session_id,
                signature=signature,
            )
            body = Body.parse_obj(
                {"CertificateInstallationRes": cert_install_res.dict()}
            )
            to_be_exi_encoded = V2GMessageV2(header=header, body=body)
            exi_encoded_cert_installation_res = EXI().to_exi(
                to_be_exi_encoded, Namespace.ISO_V2_MSG_DEF
            )

            # base64.b64encode in Python is a binary transform
            # so the return value is byte[]
            # But the CPO expects exi_encoded_cert_installation_res
            # as a string, hence the added .decode("utf-8")
            base64_encode_cert_install_res = base64.b64encode(
                exi_encoded_cert_installation_res
            ).decode("utf-8")

            return base64_encode_cert_install_res
        else:
            logger.info(f"Ignoring EXI decoding of a {type(cert_install_req)} message.")
            return ""

    async def update_data_link(self, action: SessionStopAction) -> None:
        """
        Overrides EVSEControllerInterface.update_data_link().
        """
        pass

    def ready_to_charge(self) -> bool:
        """
        Overrides EVSEControllerInterface.ready_to_charge().
        """
        return True

    # ── Battery Health Test methods ───────────────────────────────────────────

    def activate_health_test(self, c_rate: float = 5.0, cutoff_soc: int = 20) -> None:
        """Called when EVCC selects the DC_BPT health test parameter set."""
        self._health_test_active = True
        self._health_phase = "CHARGE"
        self._health_cycles = []
        self._health_energy_wh = 0.0
        self._health_temperature_c = 25.0
        self._health_c_rate = c_rate
        self._health_cutoff_soc = cutoff_soc
        logger.info(
            f"[HealthTest] Activated — C-rate={c_rate}C, cutoff_soc={cutoff_soc}%"
        )

    def record_health_cycle(self) -> None:
        """
        Called once per DC_ChargeLoopReq cycle when health test is active.
        Reads present values from ev_data_context and logs telemetry.
        Phase is determined by the sign of ev_data_context.target_current:
          negative = DISCHARGE, positive or zero = CHARGE
        """
        ctx = self.ev_data_context
        voltage = float(getattr(ctx, "present_voltage", 400) or 400)
        current = float(getattr(ctx, "target_current", 0) or 0)
        soc     = int(getattr(ctx, "present_soc", 50) or 50)
        dt      = 3.0   # charge loop interval in seconds

        # Determine phase from current sign
        phase = "DISCHARGE" if current < 0 else "CHARGE"
        self._health_phase = phase

        power_w = abs(voltage * current)

        # Accumulate energy only during discharge
        if phase == "DISCHARGE" and current < 0:
            self._health_energy_wh += power_w * (dt / 3600.0)

        # Internal resistance estimate: R = (V_oc - V_measured) / |I|
        v_oc = 400.0 * (0.80 + 0.20 * soc / 100.0)
        i_abs = max(abs(current), 0.1)
        r_int = max(0.005, min((v_oc - voltage) / i_abs, 0.5))

        # Simple thermal model
        heat_j = (current ** 2) * r_int * dt
        self._health_temperature_c += heat_j / 15000.0
        self._health_temperature_c += (25.0 - self._health_temperature_c) * 0.001

        cycle = {
            "index":        len(self._health_cycles),
            "phase":        phase,
            "soc_pct":      soc,
            "voltage_v":    round(voltage, 2),
            "current_a":    round(current, 2),
            "power_w":      round(power_w, 1),
            "energy_wh":    round(self._health_energy_wh, 3),
            "r_int_mohm":   round(r_int * 1000, 2),
            "temperature_c": round(self._health_temperature_c, 2),
        }
        self._health_cycles.append(cycle)
        logger.info(
            f"[HealthTest #{cycle['index']}] {phase} | "
            f"SOC={soc}% V={voltage:.1f}V I={current:.1f}A "
            f"P={power_w:.0f}W E={self._health_energy_wh:.2f}Wh "
            f"R={r_int*1000:.1f}mΩ T={self._health_temperature_c:.1f}°C"
        )

    def finish_health_test(self) -> None:
        """Write JSON report when the session ends."""
        if not self._health_cycles:
            return
        nominal_wh = 500.0   # must match simulator.py total_battery_capacity_wh
        soh = round(100.0 * self._health_energy_wh / nominal_wh, 2) if nominal_wh else 0
        report = {
            "c_rate":               self._health_c_rate,
            "cutoff_soc":           self._health_cutoff_soc,
            "nominal_capacity_wh":  nominal_wh,
            "measured_capacity_wh": round(self._health_energy_wh, 3),
            "soh_pct":              soh,
            "peak_temperature_c":   round(
                max(c["temperature_c"] for c in self._health_cycles), 2
            ),
            "r_int_final_mohm":     self._health_cycles[-1]["r_int_mohm"],
            "total_cycles":         len(self._health_cycles),
            "cycles":               self._health_cycles,
        }
        out = Path("health_telemetry.json")
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info(
            f"[HealthTest] Report saved → {out} | "
            f"SOH={soh}% | "
            f"Capacity={self._health_energy_wh:.1f}/{nominal_wh}Wh | "
            f"R_int={report['r_int_final_mohm']}mΩ | "
            f"T_peak={report['peak_temperature_c']}°C"
        )
        self._health_test_active = False

    # ─────────────────────────────────────────────────────────────────────────

    async def session_ended(self, current_state: str, reason: str):
        """
        Reports the state and reason where the session ended.

        @param current_state: The current SDP/SAP/DIN/ISO15118-2/ISO15118-20 state.
        @param reason: Reason for ending the session.
        @param last_message: The last message that was either sent/received.
        """
        logger.info(f"Session ended in {current_state} ({reason}).")
        if self._health_test_active:
            self.finish_health_test()

    async def send_display_params(self):
        """
        Share display params with CS.
        """
        logger.info("Send display params to CS.")

    async def send_rated_limits(self):
        """
        Overrides EVSEControllerInterface.send_rated_limits
        """
        logger.info("Send rated limits to CS.")
```

## File: iso15118/secc/states/iso15118_20_states.py
```python
"""
This module contains the SECC's States used to process the EVCC's incoming
V2GMessage objects of the ISO 15118-20 protocol, from SessionSetupReq to
SessionStopReq.
"""

import asyncio
import logging
import time
from typing import List, Optional, Tuple, Type, Union, cast

from iso15118.secc.comm_session_handler import SECCCommunicationSession
from iso15118.secc.controller.common import UnknownEnergyService
from iso15118.secc.controller.evse_data import CurrentType
from iso15118.secc.states.secc_state import StateSECC
from iso15118.shared.exi_codec import EXI
from iso15118.shared.messages.app_protocol import (
    SupportedAppProtocolReq,
    SupportedAppProtocolRes,
)
from iso15118.shared.messages.din_spec.datatypes import (
    ResponseCode as ResponseCodeDINSPEC,
)
from iso15118.shared.messages.din_spec.msgdef import V2GMessage as V2GMessageDINSPEC
from iso15118.shared.messages.enums import (
    AuthEnum,
    AuthorizationStatus,
    ControlMode,
    CpState,
    EVSEProcessing,
    IsolationLevel,
    ISOV20PayloadTypes,
    Namespace,
    ParameterName,
    Protocol,
    ServiceV20,
    SessionStopAction,
)
from iso15118.shared.messages.iso15118_2.datatypes import ResponseCode as ResponseCodeV2
from iso15118.shared.messages.iso15118_2.msgdef import V2GMessage as V2GMessageV2
from iso15118.shared.messages.iso15118_20.ac import (
    ACChargeLoopReq,
    ACChargeLoopRes,
    ACChargeParameterDiscoveryReq,
    ACChargeParameterDiscoveryReqParams,
    ACChargeParameterDiscoveryRes,
    BPTACChargeParameterDiscoveryReqParams,
)
from iso15118.shared.messages.iso15118_20.common_messages import (
    AuthorizationReq,
    AuthorizationRes,
    AuthorizationSetupReq,
    AuthorizationSetupRes,
    CertificateInstallationReq,
    ChargeProgress,
    ChargingSession,
    DynamicScheduleExchangeResParams,
    EIMAuthSetupResParams,
    EVPowerProfile,
    MatchedService,
    PnCAuthSetupResParams,
    PowerDeliveryReq,
    PowerDeliveryRes,
    ScheduledScheduleExchangeResParams,
    ScheduleExchangeReq,
    ScheduleExchangeRes,
    SelectedEnergyService,
    SelectedService,
    SelectedServiceList,
    SelectedVAS,
    ServiceDetailReq,
    ServiceDetailRes,
    ServiceDiscoveryReq,
    ServiceDiscoveryRes,
    ServiceIDList,
    ServiceList,
    ServiceSelectionReq,
    ServiceSelectionRes,
    SessionSetupReq,
    SessionSetupRes,
    SessionStopReq,
    SessionStopRes,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    EVSEStatus,
    MessageHeader,
    MeterInfo,
    Processing,
)
from iso15118.shared.messages.iso15118_20.common_types import ResponseCode
from iso15118.shared.messages.iso15118_20.common_types import (
    ResponseCode as ResponseCodeV20,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    V2GMessage as V2GMessageV20,
)
from iso15118.shared.messages.iso15118_20.dc import (
    DCCableCheckReq,
    DCCableCheckRes,
    DCChargeLoopReq,
    DCChargeLoopRes,
    DCChargeParameterDiscoveryReq,
    DCChargeParameterDiscoveryRes,
    DCPreChargeReq,
    DCPreChargeRes,
    DCWeldingDetectionReq,
    DCWeldingDetectionRes,
)
from iso15118.shared.messages.iso15118_20.timeouts import Timeouts
from iso15118.shared.notifications import StopNotification
from iso15118.shared.security import get_random_bytes, verify_signature
from iso15118.shared.states import State, Terminate

logger = logging.getLogger(__name__)


# ============================================================================
# |    COMMON SECC STATES (FOR ALL ENERGY TRANSFER MODES) - ISO 15118-20     |
# ============================================================================


class SessionSetup(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a SessionSetupReq from
    the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        # TODO: less the time used for waiting for and processing the
        #       SDPRequest and SupportedAppProtocolReq
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, [SessionSetupReq])
        if not msg:
            return

        session_setup_req: SessionSetupReq = cast(SessionSetupReq, msg)

        # Check session ID. Most likely, we need to create a new one
        session_id: str = get_random_bytes(8).hex().upper()
        if session_setup_req.header.session_id == bytes(1).hex():
            # A new charging session is established
            self.response_code = ResponseCode.OK_NEW_SESSION_ESTABLISHED
        elif session_setup_req.header.session_id == self.comm_session.session_id:
            # The EV wants to resume the previously paused charging session
            session_id = self.comm_session.session_id
            self.response_code = ResponseCode.OK_OLD_SESSION_JOINED
        else:
            # False session ID from EV, gracefully assigning new session ID
            logger.warning(
                f"EVCC's session ID {msg.header.session_id} "
                f"does not match {self.comm_session.session_id}. "
                f"New session ID {session_id} assigned"
            )
            self.response_code = ResponseCode.OK_NEW_SESSION_ESTABLISHED

        session_setup_res = SessionSetupRes(
            header=MessageHeader(session_id=session_id, timestamp=time.time()),
            response_code=self.response_code,
            evse_id=await self.comm_session.evse_controller.get_evse_id(
                Protocol.ISO_15118_20_COMMON_MESSAGES
            ),
        )

        self.comm_session.evcc_id = session_setup_req.evcc_id
        self.comm_session.session_id = session_id

        self.create_next_message(
            AuthorizationSetup,
            session_setup_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )


class AuthorizationSetup(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes an AuthorizationSetupReq
    from the EVCC.

    The EVCC may send one of the following requests in this state:
    1. an AuthorizationSetupReq
    2. an AuthorizationReq
    3. a CertificateInstallationReq
    4. a SessionStopReq

    Upon first initialisation of this state, we expect an
    AuthorizationSetupReq, but after that, the next possible request could
    be one of the others listed above. So we remain in this state until we know
    which is the following request from the EVCC and then transition to the
    appropriate state (or terminate if the incoming message doesn't fit any of
    the expected requests).

    As a result, the create_next_message() method is called with
    next_state = None.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.expecting_auth_setup_req = True

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message,
            [
                AuthorizationSetupReq,
                AuthorizationReq,
                CertificateInstallationReq,
                SessionStopReq,
            ],
            self.expecting_auth_setup_req,
        )
        if not msg:
            return

        if isinstance(msg, CertificateInstallationReq):
            await CertificateInstallation(self.comm_session).process_message(
                message, message_exi
            )
            return

        if isinstance(msg, AuthorizationReq):
            await Authorization(self.comm_session).process_message(message, message_exi)
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        auth_options: List[AuthEnum] = []
        eim_as_res, pnc_as_res = None, None
        supported_auth_options = []
        if self.comm_session.evse_controller.is_eim_authorized():
            supported_auth_options.append(AuthEnum.EIM)
        else:
            supported_auth_options = self.comm_session.config.supported_auth_options

        if AuthEnum.PNC in supported_auth_options:
            auth_options.append(AuthEnum.PNC)
            self.comm_session.gen_challenge = get_random_bytes(16)
            pnc_as_res = PnCAuthSetupResParams(
                gen_challenge=self.comm_session.gen_challenge,
                supported_providers=await self.comm_session.evse_controller.get_supported_providers(),  # noqa: E501
            )

        if AuthEnum.EIM in supported_auth_options:
            auth_options.append(AuthEnum.EIM)
            if not pnc_as_res:
                # Only if Plug & Charge is not offered as an authorization option, then
                # we offer EIM (according to [V2G20-2567] and [V2G20-2568]). Also, the
                # XSD makes clear that either the EIM_ASResAuthorizationMode or the
                # PnC_ASResAuthorizationMode should be used, not both at the same time.
                eim_as_res = EIMAuthSetupResParams()

        # TODO [V2G20-2570]

        self.comm_session.offered_auth_options = auth_options

        auth_setup_res = AuthorizationSetupRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
            auth_services=auth_options,
            cert_install_service=self.comm_session.config.allow_cert_install_service,
            eim_as_res=eim_as_res,
            pnc_as_res=pnc_as_res,
        )

        self.create_next_message(
            None,
            auth_setup_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

        self.expecting_auth_setup_req = False


class CertificateInstallation(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    CertificateInstallationReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        raise NotImplementedError("CertificateInstallation not yet implemented")


class Authorization(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes an AuthorizationReq
    from the EVCC.

    The EVCC may send one of the following requests in this state:
    1. an AuthorizationReq
    2. a CertificateInstallationReq
    3. a ServiceDiscoveryReq
    4. a SessionStopReq

    Upon first initialisation of this state, we expect an
    AuthorizationReq, but after that, the next possible request could
    be one of the others listed above. So we remain in this state until we know
    which is the following request from the EVCC and then transition to the
    appropriate state (or terminate if the incoming message doesn't fit any of
    the expected requests).

    As a result, the create_next_message() method is called with
    next_state = None.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.expecting_authorization_req = True

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message,
            [
                AuthorizationReq,
                CertificateInstallationReq,
                ServiceDiscoveryReq,
                SessionStopReq,
            ],
            self.expecting_authorization_req,
        )
        if not msg:
            return

        if isinstance(msg, CertificateInstallationReq):
            await CertificateInstallation(self.comm_session).process_message(
                message, message_exi
            )
            return

        if isinstance(msg, ServiceDiscoveryReq):
            await ServiceDiscovery(self.comm_session).process_message(
                message, message_exi
            )
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        auth_req: AuthorizationReq = cast(AuthorizationReq, msg)
        response_code: Optional[
            Union[ResponseCodeV2, ResponseCodeV20, ResponseCodeDINSPEC]
        ] = ResponseCode.OK
        self.comm_session.selected_auth_option = AuthEnum(
            auth_req.selected_auth_service.value
        )
        if auth_req.pnc_params:
            if not verify_signature(
                auth_req.header.signature,
                [
                    (
                        auth_req.pnc_params.id,
                        EXI().to_exi(auth_req.pnc_params, Namespace.ISO_V20_COMMON_MSG),
                    )
                ],
                auth_req.pnc_params.contract_cert_chain.certificate,
            ):
                # TODO: There are more fine-grained WARNING response codes available
                self.stop_state_machine(
                    "Unable to verify signature for AuthorizationReq",
                    message,
                    ResponseCode.FAILED_SIGNATURE_ERROR,
                )
                return

            if auth_req.pnc_params.gen_challenge != self.comm_session.gen_challenge:
                response_code = ResponseCode.WARN_CHALLENGE_INVALID

        current_authorization_status = (
            await self.comm_session.evse_controller.is_authorized()
        )
        evse_processing = Processing.ONGOING

        if resp_status := current_authorization_status.certificate_response_status:
            # Based on table 224 in ISO 15118-20 the response code should be
            # one of the following:
            # OK, OK_CERT_EXPIRES_SOON,
            # WARN_CERT_EXPIRED, WARN_CERT_NOT_YET_VALID,
            # WARN_CERT_REVOKED, WARN_CERT_VALIDATION_ERROR,
            # WARN_EMSP_UNKNOWN, WARN_GENERAL_PNC_AUTH_ERROR,
            # WARN_CHALLENGE_INVALID, WARN_AUTH_SELECTION_INVALID,
            # WARN_EIM_AUTH_FAILED, FAILED,
            # FAILED_SEQUENCE_ERROR or FAILED_UNKNOWN_SESSION

            response_code = (
                resp_status
                if resp_status
                in [
                    ResponseCode.OK,
                    ResponseCode.OK_CERT_EXPIRES_SOON,
                    ResponseCode.WARN_CERT_EXPIRED,
                    ResponseCode.WARN_CERT_NOT_YET_VALID,
                    ResponseCode.WARN_CERT_REVOKED,
                    ResponseCode.WARN_CERT_VALIDATION_ERROR,
                    ResponseCode.WARN_EMSP_UNKNOWN,
                    ResponseCode.WARN_GENERAL_PNC_AUTH_ERROR,
                    ResponseCode.WARN_CHALLENGE_INVALID,
                    ResponseCode.WARN_AUTH_SELECTION_INVALID,
                    ResponseCode.WARN_EIM_AUTH_FAILED,
                    ResponseCode.FAILED,
                    ResponseCode.FAILED_SEQUENCE_ERROR,
                    ResponseCode.FAILED_UNKNOWN_SESSION,
                ]
                else ResponseCode.FAILED
            )

        if (
            current_authorization_status.authorization_status
            == AuthorizationStatus.ACCEPTED
        ):
            evse_processing = Processing.FINISHED
        elif (
            current_authorization_status.authorization_status
            == AuthorizationStatus.ONGOING
        ):
            if self.comm_session.selected_auth_option == AuthEnum.EIM:
                evse_processing = Processing.WAITING_FOR_CUSTOMER
            else:
                evse_processing = Processing.ONGOING
        else:
            evse_processing = Processing.FINISHED

        auth_res = AuthorizationRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=response_code,
            evse_processing=evse_processing,
        )

        self.create_next_message(
            None,
            auth_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

        if evse_processing == Processing.FINISHED:
            self.expecting_authorization_req = False
        else:
            self.expecting_authorization_req = True


class ServiceDiscovery(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    ServiceDiscoveryReq from the EVCC.

    The EVCC may send one of the following requests in this state:
    1. ServiceDiscoveryReq
    2. ServiceDetailReq
    3. SessionStopReq

    Upon first initialisation of this state, we expect a ServiceDiscoveryReq
    but after that, the next possible request could be a ServiceDetailReq or a
    SessionStopReq. This means that we need to remain in this state until we receive
    the next message in the sequence.

    As a result, the create_next_message() method is called with next_state = None.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.expecting_service_discovery_req = True

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg = self.check_msg_v20(
            message,
            [ServiceDiscoveryReq, ServiceDetailReq, SessionStopReq],
            self.expecting_service_discovery_req,
        )
        if not msg:
            return

        if isinstance(msg, ServiceDetailReq):
            await ServiceDetail(self.comm_session).process_message(message, message_exi)
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        service_discovery_req: ServiceDiscoveryReq = cast(ServiceDiscoveryReq, msg)
        # TODO: Filter services based on
        #  SupportedServiceIDs field in ServiceDiscoveryReq
        offered_energy_services = (
            await self.comm_session.evse_controller.get_energy_service_list()
        )
        for energy_service in offered_energy_services.services:
            self.comm_session.matched_services_v20.append(
                MatchedService(
                    service=ServiceV20.get_by_id(energy_service.service_id),
                    is_energy_service=True,
                    is_free=energy_service.free_service,
                    # Parameter sets are available with ServiceDetailRes
                    parameter_sets=[],
                )
            )

        offered_vas = self.get_vas_list(service_discovery_req.supported_service_ids)
        if offered_vas:
            for vas in offered_vas.services:
                self.comm_session.matched_services_v20.append(
                    MatchedService(
                        service=ServiceV20.get_by_id(vas.service_id),
                        is_energy_service=False,
                        is_free=vas.free_service,
                        # Parameter sets are available with ServiceDetailRes
                        parameter_sets=[],
                    )
                )

        service_discovery_res = ServiceDiscoveryRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
            service_renegotiation_supported=await self.comm_session.evse_controller.service_renegotiation_supported(),  # noqa: E501
            energy_service_list=offered_energy_services,
            vas_list=offered_vas,
        )

        self.create_next_message(
            None,
            service_discovery_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

        self.expecting_service_discovery_req = False

    def get_vas_list(
        self, supported_service_ids: ServiceIDList = None
    ) -> Optional[ServiceList]:
        """
        Provides a list of value-added services (VAS) offered by the SECC. If the EVCC
        provided a SupportedServiceIDs parameter with ServiceDiscoveryReq, then the
        offered VAS list must not contain more services than the ones whose IDs are in
        this list.

        Args:
            supported_service_ids: A list that contains all ServiceIDs that the EV
                                   supports.

        Returns:
            A list of offered value-added services, or None, if none are offered.
        """
        return None


class ServiceDetail(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    ServiceDetailReq from the EVCC.

    The EVCC may send one of the following requests in this state:
    1. ServiceDetailReq
    2. ServiceSelectionReq
    3. SessionStopReq

    Upon first initialisation of this state, we expect a ServiceDetailReq
    but after that, the next possible request could be a ServiceSelectionReq or a
    SessionStopReq. This means that we need to remain in this state until we receive
    the next message in the sequence.

    As a result, the create_next_message() method is called with next_state = None.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.expecting_service_detail_req = True

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg = self.check_msg_v20(
            message,
            [ServiceDetailReq, ServiceSelectionReq, SessionStopReq],
            # TODO Need to rethink this as we may also always expect a SessionStopReq,
            #      but not always a ServiceSelectionReq. The expect_first parameter
            #      doesn't work here as good as it does for ISO 15118-2
            self.expecting_service_detail_req,
        )
        if not msg:
            return

        if isinstance(msg, ServiceSelectionReq):
            await ServiceSelection(self.comm_session).process_message(
                message, message_exi
            )
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        service_detail_req: ServiceDetailReq = cast(ServiceDetailReq, msg)

        service_parameter_list = (
            await self.comm_session.evse_controller.get_service_parameter_list(
                service_detail_req.service_id
            )
        )

        is_found = False
        for offered_service in self.comm_session.matched_services_v20:
            if offered_service.service.id == service_detail_req.service_id:
                offered_service.parameter_sets = service_parameter_list.parameter_sets
                is_found = True
                break
        if is_found:
            response_code = ResponseCode.OK
        else:
            # [V2G20-464] The message "ServiceDetailRes" shall contain the
            # ResponseCode "FAILED_ServiceIDInvalid" if the ServiceID contained
            # in the ServiceDetailReq message was not part of the offered
            # EnergyTransferServiceList or VASList during ServiceDiscovery.
            response_code = ResponseCode.FAILED_SERVICE_ID_INVALID
            logger.error(f"Service Id is invalid for {message}")
        service_detail_res = ServiceDetailRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=response_code,
            service_id=service_detail_req.service_id,
            service_parameter_list=service_parameter_list,
        )

        self.create_next_message(
            None,
            service_detail_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

        self.expecting_service_detail_req = False


class ServiceSelection(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    ServiceSelectionReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg = self.check_msg_v20(message, [ServiceSelectionReq, SessionStopReq], False)
        if not msg:
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        service_selection_req: ServiceSelectionReq = cast(ServiceSelectionReq, msg)

        valid, reason, res_code = self.check_selected_services(service_selection_req)
        if not valid:
            self.stop_state_machine(reason, message, res_code)
            return

        energy_service_id = service_selection_req.selected_energy_service.service_id
        next_state: Type[State] = None
        if energy_service_id in (ServiceV20.AC.id, ServiceV20.AC_BPT.id):
            next_state = ACChargeParameterDiscovery
        elif energy_service_id in (ServiceV20.DC.id, ServiceV20.DC_BPT.id):
            next_state = DCChargeParameterDiscovery
        else:
            # TODO Implement WPT and ACDP classes to create corresponding elif-branches
            # TODO Check if the SECC offered the selected combination of service ID and
            #      parameter set ID
            self.stop_state_machine(
                f"Selected energy transfer service ID '{energy_service_id}' invalid",
                message,
                ResponseCode.FAILED_SERVICE_SELECTION_INVALID,
            )
            return

        service_selection_res = ServiceSelectionRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
        )

        self.create_next_message(
            next_state,
            service_selection_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

    def check_selected_services(
        self, service_req: ServiceSelectionReq
    ) -> Tuple[bool, str, Optional[ResponseCode]]:
        """
        Checks whether the energy transfer service and value-added services, which the
        EVCC selected, were offered by the SECC in the previous ServiceDiscoveryRes.

        Args:
            service_req: The EVCC's ServiceSelectionReq message

        Returns:
            A tuple containing the following information:
            1. True, if check passed, False otherwise
            2. If False, the reason for not passing (empty if passed)
            3. The corresponding negative response code
        """
        req_energy_service: SelectedService = service_req.selected_energy_service
        req_vas_list: SelectedServiceList = service_req.selected_vas_list

        # Create a list of tuples, with each tuple containing the service ID and the
        # associated parameter set IDs of an offered service.
        offered_id_pairs = []
        for offered_service in self.comm_session.matched_services_v20:
            offered_id_pairs.extend(offered_service.service_parameter_set_ids())

        # Let's first check if the (service ID, parameter set ID)-pair of the selected
        # energy service is valid
        if (
            req_energy_service.service_id,
            req_energy_service.parameter_set_id,
        ) not in offered_id_pairs:
            return (
                False,
                "Invalid selected pair of energy transfer service ID "
                f"'{req_energy_service.service_id}' and parameter set ID "
                f"'{req_energy_service.parameter_set_id}' (not offered by SECC)",
                ResponseCode.FAILED_NO_ENERGY_TRANSFER_SERVICE_SELECTED,
            )

        # Let's check if the (service ID, parameter set ID)-pair of all selected
        # value-added services (VAS) are valid (if the EVCC selected any VAS)
        if req_vas_list:
            for vas in req_vas_list.selected_services:
                if (vas.service_id, vas.parameter_set_id) not in offered_id_pairs:
                    return (
                        False,
                        "Invalid selected pair of value-added service ID "
                        f"'{vas.service_id}' and parameter set ID "
                        f"'{vas.parameter_set_id}' (not offered by SECC)",
                        ResponseCode.FAILED_SERVICE_SELECTION_INVALID,
                    )

        # TODO: Refactor to a separate method.
        # If all selected services are valid, let's add the information about the
        # parameter set (not just the ID) to each selected service
        for offered_service in self.comm_session.matched_services_v20:
            if req_energy_service.service_id == offered_service.service.id:
                for parameter_set in offered_service.parameter_sets:
                    if req_energy_service.parameter_set_id == parameter_set.id:
                        self.comm_session.selected_energy_service = (
                            SelectedEnergyService(
                                service=ServiceV20.get_by_id(
                                    req_energy_service.service_id
                                ),
                                is_free=offered_service.is_free,
                                parameter_set=parameter_set,
                            )
                        )

                        # Set the control mode for the comm_session object
                        for param in parameter_set.parameters:
                            if param.name == ParameterName.CONTROL_MODE:
                                self.comm_session.control_mode = ControlMode(
                                    param.int_value
                                )

                        break
                continue

            if req_vas_list:
                for vas in req_vas_list.selected_services:
                    if req_energy_service.service_id == offered_service.service.id:
                        for parameter_set in offered_service.parameter_sets:
                            if req_energy_service.parameter_set_id == parameter_set.id:
                                self.comm_session.selected_vas_list_v20.append(
                                    SelectedVAS(
                                        service=ServiceV20.get_by_id(vas.service_id),
                                        is_free=offered_service.is_free,
                                        parameter_set=parameter_set,
                                    )
                                )
                                break

        # TODO Implement [V2G20-1956] and [V2G20-1644] (ServiceRenegotiationSupported)
        # TODO Check for [V2G20-1985]

        # ── Battery Health Test activation ────────────────────────────────────
        selected_service = self.comm_session.selected_energy_service
        if selected_service and selected_service.service == ServiceV20.DC_BPT:
            ps = selected_service.parameter_set
            if ps and any(
                p.name == "TestMode" and p.int_value == 1
                for p in ps.parameters
            ):
                c_rate = 5.0
                cutoff_soc = 20
                for p in ps.parameters:
                    if p.name == "TestCRate" and p.int_value:
                        c_rate = float(p.int_value)
                    if p.name == "CutoffSOC" and p.int_value:
                        cutoff_soc = p.int_value
                self.comm_session.evse_controller.activate_health_test(
                    c_rate=c_rate, cutoff_soc=cutoff_soc
                )
        # ──────────────────────────────────────────────────────────────────────


        return True, "", None


class ScheduleExchange(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    ScheduleExchangeReq from the EVCC.

    The EVCC may send one of the following requests in this state:
    1. ScheduleExchangeReq
    2. DCCableCheckReq
    3. PowerDeliveryReq
    3. SessionStopReq

    Upon first initialisation of this state, we expect a ScheduleExchangeReq
    but after that, the next possible request could be another ScheduleExchangeReq,
    a DCCableCheckReq, a PowerDeliveryReq or a SessionStopReq. This means that we need
    to remain in this state until we receive the next message in the sequence.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message,
            [ScheduleExchangeReq, DCCableCheckReq, PowerDeliveryReq, SessionStopReq],
            False,
        )
        if not msg:
            return

        if isinstance(msg, DCCableCheckReq):
            await DCCableCheck(self.comm_session).process_message(message, message_exi)
            return

        if isinstance(msg, PowerDeliveryReq):
            await PowerDelivery(self.comm_session).process_message(message, message_exi)
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        schedule_exchange_req: ScheduleExchangeReq = cast(ScheduleExchangeReq, msg)
        control_mode = self.comm_session.control_mode
        ev_data_context = self.comm_session.evse_controller.ev_data_context
        ev_data_context.update_schedule_exchange_parameters(
            control_mode, schedule_exchange_req
        )

        # As per Table 49 of ISO15118-20 spec: one of scheduled_params/dynamic_params is
        # required even if EVSEProcessing is ongoing. The SECC shall only omit the
        # parameter 'ScheduleList' in case EVSEProcessing is set to 'Ongoing'.
        # However, the schema file doesn't permit this as minOccurs = 0 is not set in
        # schema here: https://github.com/SwitchEV/iso15118/blob/769eddb0cb780db629b4c736de270d381516abd1/iso15118/shared/schemas/iso15118_20/V2G_CI_CommonMessages.xsd#L467-L466  # noqa
        params = await self.comm_session.evse_controller.get_schedule_exchange_params(
            self.comm_session.selected_energy_service,
            control_mode,
            schedule_exchange_req,
        )

        if (
            control_mode == ControlMode.SCHEDULED
            and type(params) is not ScheduledScheduleExchangeResParams
        ) or (
            control_mode == ControlMode.DYNAMIC
            and type(params) is not DynamicScheduleExchangeResParams
        ):
            self.stop_state_machine(
                f"Unexpected control_mode {control_mode},"
                f" for params type {type(params)}",
                message,
                ResponseCode.FAILED,
            )
            return

        if self.comm_session.evse_controller.ready_to_charge():
            evse_processing = Processing.FINISHED
            if type(params) is ScheduledScheduleExchangeResParams:
                self.comm_session.offered_schedules_V20 = params.schedule_tuples
        else:
            evse_processing = Processing.ONGOING

        schedule_exchange_res = ScheduleExchangeRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
            evse_processing=evse_processing,
            scheduled_params=params if control_mode == ControlMode.SCHEDULED else None,
            dynamic_params=params if control_mode == ControlMode.DYNAMIC else None,
        )

        if evse_processing == Processing.FINISHED:
            evse_data_context = self.comm_session.evse_controller.evse_data_context
            evse_data_context.update_schedule_exchange_parameters(
                control_mode, schedule_exchange_res
            )

        # We don't know what request will come next (which state to transition to),
        # unless the schedule parameters are ready and we're in AC charging.
        # Even in DC charging the sequence is not 100% clear as the EVCC could skip
        # DCCableCheck and DCPreCharge and go straight to PowerDelivery (Pause, Standby)
        # [V2G20-2122]
        next_state = None
        if (
            evse_processing == Processing.FINISHED
            and self.comm_session.selected_energy_service.service
            in (ServiceV20.AC, ServiceV20.AC_BPT)
        ):
            next_state = PowerDelivery

        self.create_next_message(
            next_state,
            schedule_exchange_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )


class PowerDelivery(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    PowerDeliveryReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message, [PowerDeliveryReq, DCWeldingDetectionReq, SessionStopReq], False
        )
        if not msg:
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        if isinstance(msg, DCWeldingDetectionReq):
            await DCWeldingDetection(self.comm_session).process_message(
                message, message_exi
            )
            return

        power_delivery_req: PowerDeliveryReq = cast(PowerDeliveryReq, msg)

        next_state: Optional[Type[State]] = None
        header = MessageHeader(
            session_id=self.comm_session.session_id, timestamp=time.time()
        )
        response_code = ResponseCode.OK

        if power_delivery_req.ev_processing == Processing.ONGOING:
            # Initial values for next_state and response_code apply. The EVCC will send
            # another PowerDeliveryReq
            logger.debug("EV is still processing the EVPowerProfile")
        else:
            response_code = self.check_power_profile(
                power_delivery_req.ev_power_profile
            )
            if response_code in (
                ResponseCode.FAILED_EV_POWER_PROFILE_INVALID,
                ResponseCode.FAILED_EV_POWER_PROFILE_VIOLATION,
            ):
                self.stop_state_machine(
                    "EVPowerProfile invalid/violation",
                    message,
                    response_code,
                )
                return

            if (
                power_delivery_req.charge_progress == ChargeProgress.STANDBY
                and not self.comm_session.config.standby_allowed
            ):
                self.stop_state_machine(
                    "Standby not allowed",
                    message,
                    ResponseCode.WARN_STANDBY_NOT_ALLOWED,
                )
                return
            elif power_delivery_req.charge_progress == ChargeProgress.STOP:
                # According to section 8.5.6 in ISO 15118-20, the EV is out of the
                # HLC-C (High Level Controlled Charging) once
                # PowerDeliveryRes(ResponseCode=OK) is sent with a ChargeProgress=Stop
                await self.comm_session.evse_controller.set_hlc_charging(False)

                # 1st a controlled stop is performed (specially important for
                # DC charging)
                # later on we may also need here some feedback on stopping the charger
                await self.comm_session.evse_controller.stop_charger()
                # 2nd once the energy transfer is properly interrupted,
                # the contactor(s) may open

                if not await self.comm_session.evse_controller.is_contactor_opened():
                    self.stop_state_machine(
                        "Contactor didnt open",
                        message,
                        ResponseCode.FAILED_CONTACTOR_ERROR,
                    )
                    return
            else:
                # The only ChargeProgress options left are START and
                # SCHEDULE_RENEGOTIATION, although the latter is only allowed after we
                # entered the charge loop
                # TODO Check how to handle a misplaced SCHEDULE_RENEGOTIATION

                if self.comm_session.control_mode == ControlMode.SCHEDULED:
                    offered_schedules = self.comm_session.offered_schedules_V20
                    selected_schedule = (
                        power_delivery_req.ev_power_profile.scheduled_profile
                    )

                    if selected_schedule.selected_schedule_tuple_id not in [
                        schedule.schedule_tuple_id for schedule in offered_schedules
                    ]:
                        self.stop_state_machine(
                            f"Schedule with ID "
                            f"{selected_schedule.selected_schedule_tuple_id} was not "
                            f"offered",
                            message,
                            ResponseCode.FAILED_SCHEDULE_SELECTION_INVALID,
                        )
                        return
                # According to section 8.5.6 in ISO 15118-20, the EV enters into HLC-C
                # (High Level Controlled Charging) once
                # PowerDeliveryRes(ResponseCode=OK) is sent with a ChargeProgress=Start
                # To facilitate testing, we will set the HLC-C flag to True here
                # but if the contactor wont close as expected, we set
                # the HLC-C flag to False and stop the state machine immediately
                await self.comm_session.evse_controller.set_hlc_charging(True)

                # [V2G20-1617] The EVCC shall signal CP State B before sending the
                # first PowerDeliveryReq with ChargeProgress equals "Start" within V2G
                # communication session.
                # [V2G20 - 847] The EVCC shall signal CP State C or D no later than 250
                # ms after sending the first PowerDeliveryReq with ChargeProgress
                # equals "Start" within V2G communication session.
                if not await self.wait_for_state_c_or_d():
                    logger.warning(
                        "[V2G20-847]: C2/D2 CP state not detected after "
                        "250ms in PowerDelivery"
                    )

                if not await self.comm_session.evse_controller.is_contactor_closed():
                    await self.comm_session.evse_controller.set_hlc_charging(False)
                    self.stop_state_machine(
                        "Contactor didn't close",
                        message,
                        ResponseCode.FAILED_CONTACTOR_ERROR,
                    )
                    return

                if self.comm_session.selected_energy_service.service in (
                    ServiceV20.AC,
                    ServiceV20.AC_BPT,
                ):
                    next_state = ACChargeLoop
                elif self.comm_session.selected_energy_service.service in (
                    ServiceV20.DC,
                    ServiceV20.DC_BPT,
                ):
                    next_state = DCChargeLoop
                else:
                    # TODO Add support for WPT and ACDP
                    logger.error(
                        "Selected energy service not supported: "
                        f"{self.comm_session.selected_energy_service.service}"
                    )

                # TODO: Look into FAILED_PowerToleranceNotConfirmed
                #       OK_PowerToleranceConfirmed, WARNING_PowerToleranceNotConfirmed,
                #       and FAILED_PowerDeliveryNotApplied

        power_delivery_res = PowerDeliveryRes(
            header=header, response_code=response_code
        )

        self.create_next_message(
            next_state,
            power_delivery_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )

    async def wait_for_state_c_or_d(self) -> bool:
        # [V2G2 - 847] The EV shall signal CP State C or D no later than 250ms
        # after sending the first PowerDeliveryReq with ChargeProgress equals
        # "Start" within V2G Communication SessionPowerDeliveryReq.
        STATE_C_TIMEOUT = 0.25

        async def check_state():
            while await self.comm_session.evse_controller.get_cp_state() not in [
                CpState.C2,
                CpState.D2,
            ]:
                await asyncio.sleep(0.05)
            logger.debug(
                f"State is " f"{await self.comm_session.evse_controller.get_cp_state()}"
            )
            return True

        try:
            return await asyncio.wait_for(
                check_state(),
                timeout=STATE_C_TIMEOUT,
            )
        except asyncio.TimeoutError:
            # try one more time to get the latest state
            return await self.comm_session.evse_controller.get_cp_state() in [
                CpState.C2,
                CpState.D2,
            ]

    def check_power_profile(self, power_profile: EVPowerProfile) -> ResponseCode:
        # TODO Check the power profile for any violation
        return ResponseCode.OK


class SessionStop(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    SessionStopReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(message, [SessionStopReq], False)
        if not msg:
            return

        session_stop_req: SessionStopReq = cast(SessionStopReq, msg)

        evse_controller = self.comm_session.evse_controller
        # [V2G20-1477] : If EVSE supports ServiceRegotiation and EVCC requests
        # it in the SessionStopReq, the next state should be set to ServiceDiscoveryReq
        next_state: Type[State] = Terminate
        if (
            session_stop_req.charging_session == ChargingSession.SERVICE_RENEGOTIATION
            and await evse_controller.service_renegotiation_supported()
        ):
            next_state = ServiceDiscovery
            session_stop_state = SessionStopAction.PAUSE
        elif session_stop_req.charging_session == ChargingSession.TERMINATE:
            session_stop_state = SessionStopAction.TERMINATE
        else:
            session_stop_state = SessionStopAction.PAUSE

        termination_info = ""
        if (
            session_stop_req.ev_termination_code
            or session_stop_req.ev_termination_explanation
        ):
            termination_info = (
                f"EV termination code: '{session_stop_req.ev_termination_code}'; "
                f"EV termination explanation: '"
                f"{session_stop_req.ev_termination_explanation}'"
            )

        self.comm_session.stop_reason = StopNotification(
            True,
            f"Communication session {session_stop_state.value}d. "
            f"EV Info: {termination_info}",
            self.comm_session.writer.get_extra_info("peername"),
            session_stop_state,
        )

        session_stop_res = SessionStopRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
        )

        self.create_next_message(
            next_state,
            session_stop_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_COMMON_MSG,
            ISOV20PayloadTypes.MAINSTREAM,
        )


# ============================================================================
# |                AC-SPECIFIC EVCC STATES - ISO 15118-20                    |
# ============================================================================


class ACChargeParameterDiscovery(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes an
    ACChargeParameterDiscoveryReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message, [ACChargeParameterDiscoveryReq, SessionStopReq], False
        )
        if not msg:
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        ac_cpd_req: ACChargeParameterDiscoveryReq = cast(
            ACChargeParameterDiscoveryReq, msg
        )

        energy_service = self.comm_session.selected_energy_service.service
        params = None
        try:
            params = await self.comm_session.evse_controller.get_ac_charge_params_v20(
                energy_service
            )
            ac_cpd_res = ACChargeParameterDiscoveryRes(
                header=MessageHeader(
                    session_id=self.comm_session.session_id, timestamp=time.time()
                ),
                response_code=ResponseCode.OK,
                ac_params=params if energy_service == ServiceV20.AC else None,
                bpt_ac_params=params if energy_service == ServiceV20.AC_BPT else None,
            )
            # Update EVSE Data Context not needed as comes from cs config
            evse_data_context = self.comm_session.evse_controller.evse_data_context
            evse_data_context.current_type = CurrentType.AC
            # Update EV Data Context
            ev_data_context = self.comm_session.evse_controller.ev_data_context
            ev_data_context.update_ac_charge_parameters_v20(energy_service, ac_cpd_req)
            await self.comm_session.evse_controller.send_rated_limits()
        except UnknownEnergyService:
            self.stop_state_machine(
                f"Invalid charge parameter for service {energy_service}",
                message,
                ResponseCode.FAILED_WRONG_CHARGE_PARAMETER,
            )
            return
        self.create_next_message(
            ScheduleExchange,
            ac_cpd_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_AC,
            ISOV20PayloadTypes.AC_MAINSTREAM,
        )

    def charge_parameter_valid(
        self,
        ac_charge_params: Union[
            ACChargeParameterDiscoveryReqParams, BPTACChargeParameterDiscoveryReqParams
        ],
    ) -> bool:
        # TODO Implement [V2G20-1619] (FAILED_WrongChargeParameter)
        # raise an error if the charge parameter is not valid
        return True


class ACChargeLoop(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes an
    ACChargeLoopReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            # TODO A MeteringConfirmationReq can come in using the multiplexed side
            #      stream. Need to figure out how to enable multiplexed communication
            message,
            [ACChargeLoopReq, PowerDeliveryReq, SessionStopReq],
            False,
        )
        if not msg:
            return

        if isinstance(msg, PowerDeliveryReq):
            await PowerDelivery(self.comm_session).process_message(message, message_exi)
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        ac_charge_loop_req: ACChargeLoopReq = cast(ACChargeLoopReq, msg)
        service = self.comm_session.selected_energy_service.service
        control_mode = self.comm_session.control_mode

        self.comm_session.evse_controller.ev_data_context.update_ac_charge_loop_v20(
            ac_charge_loop_req, service, control_mode
        )

        meter_info = None
        if ac_charge_loop_req.meter_info_requested:
            meter_info = await self.comm_session.evse_controller.get_meter_info_v20()

        evse_status: Optional[EVSEStatus] = (
            await self.comm_session.evse_controller.get_evse_status()
        )

        response_code = ResponseCode.OK
        params = None
        if service not in [ServiceV20.AC, ServiceV20.AC_BPT]:
            logger.error(f"Energy service {service} not yet supported")
            response_code = ResponseCode.FAILED_SERVICE_SELECTION_INVALID
        else:
            params = (
                await self.comm_session.evse_controller.get_ac_charge_loop_params_v20(
                    control_mode, service
                )
            )  # noqa

        ac_charge_loop_res = ACChargeLoopRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id,
                timestamp=time.time(),
            ),
            evse_status=evse_status,
            # TODO Check for other failed or warning response codes
            response_code=response_code,
            scheduled_params=(
                params
                if control_mode == ControlMode.SCHEDULED and service == ServiceV20.AC
                else None
            ),
            dynamic_params=(
                params
                if control_mode == ControlMode.DYNAMIC and service == ServiceV20.AC
                else None
            ),
            bpt_scheduled_params=(
                params
                if control_mode == ControlMode.SCHEDULED
                and service == ServiceV20.AC_BPT
                else None
            ),
            bpt_dynamic_params=(
                params
                if control_mode == ControlMode.DYNAMIC and service == ServiceV20.AC_BPT
                else None
            ),
            meter_info=meter_info,
        )
        await self.comm_session.evse_controller.send_display_params()
        self.create_next_message(
            None,
            ac_charge_loop_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_AC,
            ISOV20PayloadTypes.AC_MAINSTREAM,
        )

    def check_power_profile(self) -> ResponseCode:
        # TODO Check the power profile for any violation
        return ResponseCode.OK


# ============================================================================
# |                DC-SPECIFIC EVCC STATES - ISO 15118-20                    |
# ============================================================================


class DCChargeParameterDiscovery(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    DCChargeParameterDiscoveryReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message, [DCChargeParameterDiscoveryReq, SessionStopReq], False
        )
        if not msg:
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        dc_cpd_req: DCChargeParameterDiscoveryReq = cast(
            DCChargeParameterDiscoveryReq, msg
        )

        energy_service = self.comm_session.selected_energy_service.service
        params = None
        try:
            params = await self.comm_session.evse_controller.get_dc_charge_params_v20(
                energy_service
            )  # noqa
            dc_cpd_res = DCChargeParameterDiscoveryRes(
                header=MessageHeader(
                    session_id=self.comm_session.session_id, timestamp=time.time()
                ),
                response_code=ResponseCode.OK,
                dc_params=params if energy_service == ServiceV20.DC else None,
                bpt_dc_params=params if energy_service == ServiceV20.DC_BPT else None,
            )
            # Update EVSE Data Context
            evse_data_context = self.comm_session.evse_controller.evse_data_context
            evse_data_context.current_type = CurrentType.DC
            evse_data_context.update_dc_charge_parameters_v20(
                energy_service, dc_cpd_res
            )
            # Update EV Data Context
            ev_data_context = self.comm_session.evse_controller.ev_data_context
            ev_data_context.update_dc_charge_parameters_v20(energy_service, dc_cpd_req)
            await self.comm_session.evse_controller.send_rated_limits()
        except UnknownEnergyService:
            self.stop_state_machine(
                f"Invalid charge parameter for service {energy_service}",
                message,
                ResponseCode.FAILED_WRONG_CHARGE_PARAMETER,
            )
            return
        self.create_next_message(
            ScheduleExchange,
            dc_cpd_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_DC,
            ISOV20PayloadTypes.DC_MAINSTREAM,
        )

    def charge_parameter_valid(
        self,
        energy_service: ServiceV20,
        dc_cpd_req: DCChargeParameterDiscoveryReq,
    ) -> bool:
        # TODO Implement [V2G20-2272] (FAILED_WrongChargeParameter)
        if energy_service == ServiceV20.DC:
            pass
            # params = dc_cpd_req.dc_params
        elif energy_service == ServiceV20.DC_BPT:
            pass
            # params = dc_cpd_req.bpt_dc_params
        return True


class DCCableCheck(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    DCCableCheckReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.contactors_closed = False
        self.cable_check_started = False

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message, [DCCableCheckReq, SessionStopReq], False
        )
        if not msg:
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        next_state = None
        processing = EVSEProcessing.ONGOING

        if not self.cable_check_started:
            # Start cable check as contactors are now closed.
            await self.comm_session.evse_controller.start_cable_check()
            self.cable_check_started = True

        if self.contactors_closed:
            isolation_level = (
                await self.comm_session.evse_controller.get_cable_check_status()
            )

            if isolation_level in [IsolationLevel.VALID, IsolationLevel.WARNING]:
                if isolation_level == IsolationLevel.WARNING:
                    logger.warning(
                        "Isolation resistance measured by EVSE is in Warning range"
                    )
                next_state = DCPreCharge
                processing = EVSEProcessing.FINISHED
            elif isolation_level in [IsolationLevel.INVALID, IsolationLevel.FAULT]:
                self.stop_state_machine(
                    f"Isolation Failure: {isolation_level}",
                    message,
                    ResponseCode.FAILED,
                )
                return
        else:
            if not self.contactors_closed:
                # Requirement in 6.4.3.106 of the IEC 61851-23
                # Any relays in the DC output circuit of the DC station shall
                # be closed during the insulation test
                # If None is returned, then contactor close operation is ongoing.
                contactors_closed_for_cable_check: Optional[bool] = (
                    await self.comm_session.evse_controller.is_contactor_closed()
                )

                if contactors_closed_for_cable_check is not None:
                    if contactors_closed_for_cable_check:
                        self.contactors_closed = True
                    else:
                        self.stop_state_machine(
                            "Contactor didnt close for Cable Check",
                            message,
                            ResponseCode.FAILED,
                        )
                        return

        dc_cable_check_res = DCCableCheckRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
            evse_processing=processing,
        )

        self.create_next_message(
            next_state,
            dc_cable_check_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_DC,
            ISOV20PayloadTypes.DC_MAINSTREAM,
        )


class DCPreCharge(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    DCPreChargeReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.expecting_precharge_req = True

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message,
            [DCPreChargeReq, PowerDeliveryReq],
            self.expecting_precharge_req,
        )
        if not msg:
            return

        if isinstance(msg, PowerDeliveryReq):
            await PowerDelivery(self.comm_session).process_message(message, message_exi)
            return

        precharge_req: DCPreChargeReq = cast(DCPreChargeReq, msg)
        self.expecting_precharge_req = False

        ev_data_context = self.comm_session.evse_controller.ev_data_context
        ev_data_context.update_pre_charge_parameters_v20(precharge_req)

        next_state: Type[StateSECC] = None
        if precharge_req.ev_processing == Processing.FINISHED:
            next_state = PowerDelivery
        else:
            try:
                # Current is set to 0 as that is not used for PreCharge
                await self.comm_session.evse_controller.send_charging_command(
                    ev_data_context.target_voltage, 0, is_precharge=True
                )
            except asyncio.TimeoutError:
                self.stop_state_machine(
                    "Error sending targets to charging station in charging loop.",
                    message,
                    ResponseCode.FAILED,
                )
                return
        dc_precharge_res = DCPreChargeRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
            evse_present_voltage=await self.comm_session.evse_controller.get_evse_present_voltage(  # noqa
                Protocol.ISO_15118_20_DC
            ),
        )
        self.create_next_message(
            next_state,
            dc_precharge_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_DC,
            ISOV20PayloadTypes.DC_MAINSTREAM,
        )


class DCChargeLoop(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    DCChargeLoopReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.expecting_charge_loop_req = True

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message, [DCChargeLoopReq, PowerDeliveryReq], self.expecting_charge_loop_req
        )
        if not msg:
            return

        if isinstance(msg, PowerDeliveryReq):
            await PowerDelivery(self.comm_session).process_message(message, message_exi)
            return

        self.expecting_charge_loop_req = False

        selected_energy_service = self.comm_session.selected_energy_service
        control_mode = self.comm_session.control_mode

        dc_charge_loop_req: DCChargeLoopReq = cast(DCChargeLoopReq, msg)

        ev_data_context = self.comm_session.evse_controller.ev_data_context
        ev_data_context.update_dc_charge_loop_parameters_v20(
            dc_charge_loop_req, selected_energy_service, control_mode
        )

        # ── Battery Health Test: per-cycle telemetry recording ────────────────
        evse_ctrl = self.comm_session.evse_controller
        if getattr(evse_ctrl, "_health_test_active", False):
            evse_ctrl.record_health_cycle()
        # ──────────────────────────────────────────────────────────────────────

        
        try:
            ev_target_voltage = None
            ev_target_current = None
            is_session_bpt = False
            if control_mode == ControlMode.SCHEDULED:
                # If the control is scheduled, then we check
                # what are the EV targets, otherwise,
                # the charging command requested
                # will only depend on the EVSE/EV maximum capabilities
                ev_target_voltage = ev_data_context.target_voltage
                ev_target_current = ev_data_context.target_current
            if selected_energy_service.service == ServiceV20.DC_BPT:
                is_session_bpt = True
            await self.comm_session.evse_controller.send_charging_command(
                ev_target_voltage, ev_target_current, is_session_bpt
            )
        except (asyncio.TimeoutError, Exception) as e:
            self.stop_state_machine(
                f"Error sending targets to charging station in charging loop." f": {e}",
                message,
                ResponseCode.FAILED,
            )
            return
        await self.comm_session.evse_controller.send_display_params()
        dc_charge_loop_res = await self._build_dc_charge_loop_res(
            dc_charge_loop_req.meter_info_requested
        )
        self.create_next_message(
            None,
            dc_charge_loop_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_DC,
            ISOV20PayloadTypes.DC_MAINSTREAM,
        )

    async def _build_dc_charge_loop_res(
        self, meter_info_requested: bool
    ) -> DCChargeLoopRes:
        selected_energy_service = self.comm_session.selected_energy_service
        control_mode = self.comm_session.control_mode
        service = selected_energy_service.service
        response_code = ResponseCode.OK
        params = None
        if service not in [ServiceV20.DC, ServiceV20.DC_BPT]:
            logger.error(f"Energy service {service} not yet supported")
            response_code = ResponseCode.FAILED_SERVICE_SELECTION_INVALID
        else:
            params = (
                await self.comm_session.evse_controller.get_dc_charge_loop_params_v20(
                    control_mode, service
                )
            )  # noqa

        evse_status: Optional[EVSEStatus] = (
            await self.comm_session.evse_controller.get_evse_status()
        )

        meter_info: Optional[MeterInfo] = None
        if meter_info_requested:
            meter_info = await self.comm_session.evse_controller.get_meter_info_v20()

        dc_charge_loop_res = DCChargeLoopRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            meter_info=meter_info,
            evse_status=evse_status,
            response_code=response_code,
            evse_present_current=await self.comm_session.evse_controller.get_evse_present_current(  # noqa
                Protocol.ISO_15118_20_DC
            ),  # noqa
            evse_present_voltage=await self.comm_session.evse_controller.get_evse_present_voltage(  # noqa
                Protocol.ISO_15118_20_DC
            ),  # noqa
            evse_power_limit_achieved=await self.comm_session.evse_controller.is_evse_power_limit_achieved(),  # noqa
            evse_current_limit_achieved=await self.comm_session.evse_controller.is_evse_current_limit_achieved(),  # noqa
            evse_voltage_limit_achieved=await self.comm_session.evse_controller.is_evse_voltage_limit_achieved(),  # noqa
            scheduled_dc_charge_loop_res=(
                params
                if control_mode == ControlMode.SCHEDULED and service == ServiceV20.DC
                else None
            ),
            dynamic_dc_charge_loop_res=(
                params
                if control_mode == ControlMode.DYNAMIC and service == ServiceV20.DC
                else None
            ),
            bpt_scheduled_dc_charge_loop_res=(
                params
                if control_mode == ControlMode.SCHEDULED
                and service == ServiceV20.DC_BPT
                else None
            ),
            bpt_dynamic_dc_charge_loop_res=(
                params
                if control_mode == ControlMode.DYNAMIC and service == ServiceV20.DC_BPT
                else None
            ),
        )
        return dc_charge_loop_res


class DCWeldingDetection(StateSECC):
    """
    The ISO 15118-20 state in which the SECC processes a
    DCWeldingDetectionReq from the EVCC.
    """

    def __init__(self, comm_session: SECCCommunicationSession):
        super().__init__(comm_session, Timeouts.V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT)
        self.expecting_welding_detection_req = True

    async def process_message(
        self,
        message: Union[
            SupportedAppProtocolReq,
            SupportedAppProtocolRes,
            V2GMessageV2,
            V2GMessageV20,
            V2GMessageDINSPEC,
        ],
        message_exi: bytes = None,
    ):
        msg: V2GMessageV20 = self.check_msg_v20(
            message,
            [DCWeldingDetectionReq, SessionStopReq],
            self.expecting_welding_detection_req,
        )
        if not msg:
            return

        if isinstance(msg, SessionStopReq):
            await SessionStop(self.comm_session).process_message(message, message_exi)
            return

        self.expecting_welding_detection_req = False
        welding_detection_res = DCWeldingDetectionRes(
            header=MessageHeader(
                session_id=self.comm_session.session_id, timestamp=time.time()
            ),
            response_code=ResponseCode.OK,
            evse_present_voltage=await self.comm_session.evse_controller.get_evse_present_voltage(  # noqa
                Protocol.ISO_15118_20_DC
            ),  # noqa
        )

        self.create_next_message(
            None,
            welding_detection_res,
            Timeouts.V2G_SECC_SEQUENCE_TIMEOUT,
            Namespace.ISO_V20_DC,
            ISOV20PayloadTypes.DC_MAINSTREAM,
        )
```

## File: iso15118/shared/messages/iso15118_20/common_messages.py
```python
"""
This modules contains classes which implement all the elements of the
ISO 15118-20 XSD file V2G_CI_CommonMessages.xsd (see folder 'schemas').
These are the V2GMessages exchanged between the EVCC and the SECC specifically
for AC charging.

All classes are ultimately subclassed from pydantic's BaseModel to ease
validation when instantiating a class and to reduce boilerplate code.
Pydantic's Field class is used to be able to create a json schema of each model
(or class) that matches the definitions in the XSD schema, including the XSD
element names by using the 'alias' attribute.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

from pydantic import Field, root_validator, validator

from iso15118.shared.messages import BaseModel
from iso15118.shared.messages.enums import (
    INT_8_MAX,
    INT_8_MIN,
    INT_16_MAX,
    INT_16_MIN,
    UINT_8_MAX,
    UINT_16_MAX,
    AuthEnum,
    ServiceV20,
)
from iso15118.shared.messages.iso15118_20.common_types import (
    UINT_32_MAX,
    Certificate,
    Description,
    EVSEStatus,
    Identifier,
    MeterInfo,
    Name,
    NumericID,
    Processing,
    RationalNumber,
    Receipt,
    RootCertificateIDList,
    V2GRequest,
    V2GResponse,
)
from iso15118.shared.validators import one_field_must_be_set


class ECDHCurve(str, Enum):
    """
    See section 8.3.5.3.39 in ISO 15118-20.
    Elliptic curves used for the Elliptic Curve Diffie Hellman (ECDH) key
    agreement protocol."""

    secp_521 = "SECP521"
    x448 = "X448"


class EMAIDList(BaseModel):
    """See Annex C.1 in ISO 15118-20"""

    emaids: List[Identifier] = Field(..., max_items=8, alias="EMAID")


class SubCertificates(BaseModel):
    """A list of DER encoded X.509 certificates"""

    certificates: List[Certificate] = Field(..., max_items=3, alias="Certificate")


class CertificateChain(BaseModel):
    """See section 8.3.5.3.3 in ISO 15118-20"""

    # Note that the type here must be bytes and not Certificate, otherwise we
    # end up with a json structure that does not match the XSD schema
    certificate: bytes = Field(..., max_length=800, alias="Certificate")
    sub_certificates: SubCertificates = Field(None, alias="SubCertificates")


class SignedCertificateChain(BaseModel):
    """See section 8.3.5.3.4 in ISO 15118-20"""

    # 'Id' is actually an XML attribute, but JSON (our serialisation method)
    # doesn't have attributes. The EXI codec has to en-/decode accordingly.
    id: str = Field(..., max_length=255, alias="Id")
    # Note that the type here must be bytes and not Certificate, otherwise we
    # end up with a json structure that does not match the XSD schema
    certificate: bytes = Field(..., max_length=800, alias="Certificate")
    sub_certificates: SubCertificates = Field(None, alias="SubCertificates")

    def __str__(self):
        return type(self).__name__


class ContractCertificateChain(BaseModel):
    """See section 8.3.5.3.5 in ISO 15118-20"""

    # Note that the type here must be bytes and not Certificate, otherwise we
    # end up with a json structure that does not match the XSD schema
    certificate: bytes = Field(..., max_length=800, alias="Certificate")
    sub_certificates: SubCertificates = Field(..., alias="SubCertificates")


class SessionSetupReq(V2GRequest):
    """See section 8.3.4.3.1.1 in ISO 15118-20"""

    evcc_id: str = Field(..., max_length=255, alias="EVCCID")


class SessionSetupRes(V2GResponse):
    """See section 8.3.4.3.1.2 in ISO 15118-20"""

    evse_id: str = Field(..., max_length=255, alias="EVSEID")


class AuthorizationSetupReq(V2GRequest):
    """See section 8.3.4.3.2.1 in ISO 15118-20"""


class ProviderID(BaseModel):
    provider_id: Name = Field(..., alias="ProviderID")


class PnCAuthSetupResParams(BaseModel):
    """See section 8.3.4.3.2.1 in ISO 15118-20"""

    gen_challenge: bytes = Field(
        ..., min_length=16, max_length=16, alias="GenChallenge"
    )
    supported_providers: List[ProviderID] = Field(
        None, max_items=128, alias="SupportedProviders"
    )


class EIMAuthSetupResParams(BaseModel):
    """See section 8.3.5.3.33 in ISO 15118-20"""


class AuthorizationSetupRes(V2GResponse):
    """See section 8.3.4.3.2.2 in ISO 15118-20"""

    auth_services: List[AuthEnum] = Field(
        ..., max_items=2, alias="AuthorizationServices"
    )
    cert_install_service: bool = Field(..., alias="CertificateInstallationService")
    pnc_as_res: PnCAuthSetupResParams = Field(None, alias="PnC_ASResAuthorizationMode")
    eim_as_res: EIMAuthSetupResParams = Field(None, alias="EIM_ASResAuthorizationMode")

    @root_validator(pre=True)
    def exactly_one_authorization_mode(cls, values):
        """
        Either pnc_as_res orand eim_as_res must be set, depending on
        whether both Plug & Charge is offered or not. In the latter case, only
        eim_as_res modes is offered.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "pnc_as_res",
                "PnC_ASResAuthorizationMode",
                "eim_as_res",
                "EIM_ASResAuthorizationMode",
            ],
            values,
            True,
        ):
            return values


class PnCAuthReqParams(BaseModel):
    """
    See section 8.3.5.3.32 in ISO 15118-20
    PnCAuthReq = Plug and Charge Authorization Request
    """

    # 'Id' is actually an XML attribute, but JSON (our serialisation method)
    # doesn't have attributes. The EXI codec has to en-/decode accordingly.
    id: str = Field(None, max_length=255, alias="Id")
    gen_challenge: bytes = Field(
        ..., min_length=16, max_length=16, alias="GenChallenge"
    )
    contract_cert_chain: ContractCertificateChain = Field(
        ..., alias="ContractCertificateChain"
    )

    def __str__(self):
        # We need to sign this element, which means it will be EXI encoded and we need
        # its XSD-conform name
        return "PnC_AReqAuthorizationMode"


class EIMAuthReqParams(BaseModel):
    """
    See section 8.3.5.3.31 in ISO 15118-20
    EIMAuthReq = External Identification Means Authorization Request
    """


class AuthorizationReq(V2GRequest):
    """See section 8.3.4.3.3.1 in ISO 15118-20"""

    selected_auth_service: AuthEnum = Field(..., alias="SelectedAuthorizationService")
    pnc_params: PnCAuthReqParams = Field(None, alias="PnC_AReqAuthorizationMode")
    eim_params: EIMAuthReqParams = Field(None, alias="EIM_AReqAuthorizationMode")

    @root_validator(pre=True)
    def at_least_one_authorization_mode(cls, values):
        """
        At least one of pnc_params and eim_params must be set, depending on
        whether both Plug & Charge and EIM or just one of these authorization
        modes is offered.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "pnc_params",
                "PnC_AReqAuthorizationMode",
                "eim_params",
                "EIM_AReqAuthorizationMode",
            ],
            values,
            False,
        ):
            return values


class AuthorizationRes(V2GResponse):
    """See section 8.3.4.3.3.2 in ISO 15118-20"""

    evse_processing: Processing = Field(..., alias="EVSEProcessing")


class ServiceIDList(BaseModel):
    """See section 8.3.5.3.29 in ISO 15118-20"""

    service_ids: List[int] = Field(..., max_items=16, alias="ServiceID")


class ServiceDiscoveryReq(V2GRequest):
    """See section 8.3.4.3.4.2 in ISO 15118-20"""

    supported_service_ids: ServiceIDList = Field(None, alias="SupportedServiceIDs")


class Service(BaseModel):
    """See section 8.3.5.3.1 in ISO 15118-20"""

    service_id: int = Field(..., alias="ServiceID")
    free_service: bool = Field(..., alias="FreeService")


class ServiceList(BaseModel):
    """See section 8.3.5.3.2 in ISO 15118-20"""

    services: List[Service] = Field(..., max_items=8, alias="Service")


class ServiceDiscoveryRes(V2GResponse):
    """See section 8.3.4.3.4.3 in ISO 15118-20"""

    service_renegotiation_supported: bool = Field(
        ..., alias="ServiceRenegotiationSupported"
    )
    energy_service_list: ServiceList = Field(..., alias="EnergyTransferServiceList")
    vas_list: ServiceList = Field(None, alias="VASList")


class ServiceDetailReq(V2GRequest):
    """See section 8.3.4.3.5.1 in ISO 15118-20"""

    service_id: int = Field(..., alias="ServiceID")


class Parameter(BaseModel):
    """See section 8.3.5.3.23 in ISO 15118-20"""

    # 'Name' is actually an XML attribute, but JSON (our serialisation method)
    # doesn't have attributes. The EXI codec has to en-/decode accordingly.
    name: Name = Field(..., alias="Name")
    bool_value: bool = Field(None, alias="boolValue")
    # XSD type byte with value range [-128..127]
    byte_value: int = Field(None, ge=INT_8_MIN, le=INT_8_MAX, alias="byteValue")
    # XSD type short (16 bit integer) with value range [-32768..32767]
    short_value: int = Field(None, ge=INT_16_MIN, le=INT_16_MAX, alias="shortValue")
    int_value: int = Field(None, alias="intValue")
    rational_number: RationalNumber = Field(None, alias="rationalNumber")
    finite_str: Name = Field(None, alias="finiteString")

    @root_validator(pre=True)
    def at_least_one_parameter_value(cls, values):
        """
        Either bool_value, byte_value, short_value, int_value, rational_number,
        or finite_str must be set, depending on the datatype of the parameter.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "bool_value",
                "boolValue",
                "byte_value",
                "byteValue",
                "short_value",
                "shortValue",
                "int_value",
                "intValue",
                "rational_number",
                "rationalNumber",
                "finite_str",
                "finiteString",
            ],
            values,
            True,
        ):
            return values


class ParameterSet(BaseModel):
    """See section 8.3.5.3.22 in ISO 15118-20"""

    id: int = Field(..., alias="ParameterSetID")
    parameters: List[Parameter] = Field(..., max_items=32, alias="Parameter")


class ServiceParameterList(BaseModel):
    """See section 8.3.5.3.21 in ISO 15118-20"""

    parameter_sets: List[ParameterSet] = Field(..., max_items=32, alias="ParameterSet")


class ServiceDetailRes(V2GResponse):
    """See section 8.3.4.3.5.2 in ISO 15118-20"""

    service_id: int = Field(..., alias="ServiceID")
    service_parameter_list: ServiceParameterList = Field(
        ..., alias="ServiceParameterList"
    )


class SelectedService(BaseModel):
    """See section 8.3.5.3.25 in ISO 15118-20"""

    service_id: int = Field(..., alias="ServiceID")
    parameter_set_id: int = Field(..., alias="ParameterSetID")


class SelectedServiceList(BaseModel):
    """See section 8.3.5.3.24 in ISO 15118-20"""

    selected_services: List[SelectedService] = Field(
        ..., max_items=16, alias="SelectedService"
    )


class ServiceSelectionReq(V2GRequest):
    """See section 8.3.4.3.6.2 in ISO 15118-20"""

    selected_energy_service: SelectedService = Field(
        ..., alias="SelectedEnergyTransferService"
    )
    selected_vas_list: SelectedServiceList = Field(None, alias="SelectedVASList")


class ServiceSelectionRes(V2GResponse):
    """See section 8.3.4.3.6.3 in ISO 15118-20"""


class EVPowerScheduleEntry(BaseModel):
    """See section 8.3.5.3.44 in ISO 15118-20"""

    duration: int = Field(..., alias="Duration")
    power: RationalNumber = Field(..., alias="Power")


class EVPowerScheduleEntryList(BaseModel):
    """See section 8.3.5.3.43 in ISO 15118-20"""

    entries: List[EVPowerScheduleEntry] = Field(
        ..., max_items=1024, alias="EVPowerScheduleEntry"
    )


class EVPowerSchedule(BaseModel):
    """See section 8.3.5.3.42 in ISO 15118-20"""

    time_anchor: int = Field(..., alias="TimeAnchor")
    ev_power_schedule_entries: EVPowerScheduleEntryList = Field(
        ..., alias="EVPowerScheduleEntries"
    )


class EVPriceRule(BaseModel):
    """See section 8.3.5.3.48 in ISO 15118-20"""

    energy_fee: RationalNumber = Field(..., alias="EnergyFee")
    power_range_start: RationalNumber = Field(..., alias="PowerRangeStart")


class EVPriceRuleStack(BaseModel):
    """See section 8.3.5.3.47 in ISO 15118-20"""

    duration: int = Field(..., alias="Duration")
    ev_price_rules: List[EVPriceRule] = Field(..., max_items=8, alias="EVPriceRule")


class EVPriceRuleStackList(BaseModel):
    """See section 8.3.5.3.46 in ISO 15118-20"""

    ev_price_rule_stacks: List[EVPriceRuleStack] = Field(
        ..., max_items=1024, alias="EVPriceRuleStack"
    )


class EVAbsolutePriceSchedule(BaseModel):
    """See section 8.3.5.3.45 in ISO 15118-20"""

    time_anchor: int = Field(..., alias="TimeAnchor")
    currency: str = Field(..., max_length=3, alias="Currency")
    price_algorithm: str = Field(..., max_length=255, alias="PriceAlgorithm")
    ev_price_rule_stacks: EVPriceRuleStackList = Field(..., alias="EVPriceRuleStacks")


class EVEnergyOffer(BaseModel):
    """See section 8.3.5.3.41 in ISO 15118-20"""

    ev_power_schedule: EVPowerSchedule = Field(..., alias="EVPowerSchedule")
    ev_absolute_price_schedule: EVAbsolutePriceSchedule = Field(
        ..., alias="EVAbsolutePriceSchedule"
    )


class ScheduledScheduleExchangeReqParams(BaseModel):
    """See section 8.3.5.3.14 in ISO 15118-20"""

    departure_time: int = Field(None, ge=0, le=UINT_32_MAX, alias="DepartureTime")
    ev_target_energy_request: RationalNumber = Field(
        None, alias="EVTargetEnergyRequest"
    )
    ev_max_energy_request: RationalNumber = Field(None, alias="EVMaximumEnergyRequest")
    ev_min_energy_request: RationalNumber = Field(None, alias="EVMinimumEnergyRequest")
    ev_energy_offer: EVEnergyOffer = Field(None, alias="EVEnergyOffer")


class DynamicScheduleExchangeReqParams(BaseModel):
    """See section 8.3.5.3.13 in ISO 15118-20"""

    departure_time: int = Field(..., ge=0, le=UINT_32_MAX, alias="DepartureTime")
    # XSD type byte with value range [0..100]
    min_soc: int = Field(None, ge=0, le=100, alias="MinimumSOC")
    # XSD type byte with value range [0..100]
    target_soc: int = Field(None, ge=0, le=100, alias="TargetSOC")
    ev_target_energy_request: RationalNumber = Field(..., alias="EVTargetEnergyRequest")
    ev_max_energy_request: RationalNumber = Field(..., alias="EVMaximumEnergyRequest")
    ev_min_energy_request: RationalNumber = Field(..., alias="EVMinimumEnergyRequest")
    ev_max_v2x_energy_request: RationalNumber = Field(
        None, alias="EVMaximumV2XEnergyRequest"
    )
    ev_min_v2x_energy_request: RationalNumber = Field(
        None, alias="EVMinimumV2XEnergyRequest"
    )

    @root_validator(pre=True)
    def both_v2x_fields_must_be_set(cls, values):
        max_v2x, min_v2x = (
            values.get("ev_max_v2x_energy_request"),
            values.get("ev_min_v2x_energy_request"),
        )

        if max_v2x is None and min_v2x is None:
            # When decoding from EXI to JSON dict
            max_v2x, min_v2x = (
                values.get("EVMaximumV2XEnergyRequest"),
                values.get("EVMinimumV2XEnergyRequest"),
            )

        if (max_v2x and not min_v2x) or (min_v2x and not max_v2x):
            raise ValueError(
                "EVMaximumV2XEnergyRequest and EVMinimumV2XEnergyRequest of type "
                "Dynamic_SEReqControlModeType must either be both set or both omitted. "
                "Only one of them was set ([V2G20-2681])"
            )

        return values


class ScheduleExchangeReq(V2GRequest):
    """See section 8.3.4.3.7.2 in ISO 15118-20"""

    max_supporting_points: int = Field(
        ..., ge=12, le=1024, alias="MaximumSupportingPoints"
    )
    scheduled_params: ScheduledScheduleExchangeReqParams = Field(
        None, alias="Scheduled_SEReqControlMode"
    )
    dynamic_params: DynamicScheduleExchangeReqParams = Field(
        None, alias="Dynamic_SEReqControlMode"
    )

    @root_validator(pre=True)
    def either_scheduled_or_dynamic(cls, values):
        """
        Either scheduled_params or dynamic_params must be set, depending on
        whether the charging process is governed by charging schedules or
        dynamic charging settings from the SECC.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "scheduled_params",
                "Scheduled_SEReqControlMode",
                "dynamic_params",
                "Dynamic_SEReqControlMode",
            ],
            values,
            True,
        ):
            return values


class PowerScheduleEntry(BaseModel):
    """See section 8.3.5.3.20 in ISO 15118-20"""

    duration: int = Field(..., alias="Duration")
    power: RationalNumber = Field(..., alias="Power")
    power_l2: RationalNumber = Field(None, alias="Power_L2")
    power_l3: RationalNumber = Field(None, alias="Power_L3")


class PowerScheduleEntryList(BaseModel):
    """See section 8.3.5.3.19 in ISO 15118-20"""

    entries: List[PowerScheduleEntry] = Field(
        ..., max_items=1024, alias="PowerScheduleEntry"
    )


class PowerSchedule(BaseModel):
    """See section 8.3.5.3.18 in ISO 15118-20"""

    time_anchor: int = Field(..., alias="TimeAnchor")
    available_energy: RationalNumber = Field(None, alias="AvailableEnergy")
    power_tolerance: RationalNumber = Field(None, alias="PowerTolerance")
    schedule_entry_list: PowerScheduleEntryList = Field(
        ..., alias="PowerScheduleEntries"
    )


class PriceSchedule(BaseModel):
    """See sections 8.3.5.3.49 and 8.3.5.3.62 in ISO 15118-20"""

    time_anchor: int = Field(..., alias="TimeAnchor")
    schedule_id: NumericID = Field(..., alias="PriceScheduleID")
    schedule_description: Description = Field(None, alias="PriceScheduleDescription")


class PriceLevelScheduleEntry(BaseModel):
    """See section 8.3.5.3.64 in ISO 15118-20"""

    duration: int = Field(..., ge=0, le=UINT_32_MAX, alias="Duration")
    # XSD type unsignedByte with value range [0..255]
    price_level: int = Field(..., ge=0, le=UINT_8_MAX, alias="PriceLevel")


class PriceLevelScheduleEntryList(BaseModel):
    """See section 8.3.5.3.63 in ISO 15118-20"""

    entries: List[PriceLevelScheduleEntry] = Field(
        ..., max_items=1024, alias="PriceLevelScheduleEntry"
    )


class PriceLevelSchedule(PriceSchedule):
    """See section 8.3.5.3.62 in ISO 15118-20"""

    # 'Id' is actually an XML attribute, but JSON (our serialisation method)
    # doesn't have attributes. The EXI codec has to en-/decode accordingly.
    id: str = Field(None, max_length=255, alias="Id")
    # XSD type unsignedByte with value range [0..255]
    num_price_levels: int = Field(..., ge=0, le=UINT_8_MAX, alias="NumberOfPriceLevels")
    schedule_entries: PriceLevelScheduleEntryList = Field(
        ..., alias="PriceLevelScheduleEntries"
    )


class TaxRule(BaseModel):
    """See section 8.3.5.3.51 in ISO 15118-20"""

    tax_rule_id: NumericID = Field(..., alias="TaxRuleID")
    tax_rule_name: Name = Field(None, alias="TaxRuleName")
    tax_rate: RationalNumber = Field(..., alias="TaxRate")
    tax_included_in_price: bool = Field(None, alias="TaxIncludedInPrice")
    applies_to_energy_fee: bool = Field(..., alias="AppliesToEnergyFee")
    applies_to_parking_fee: bool = Field(..., alias="AppliesToParkingFee")
    applies_to_overstay_fee: bool = Field(..., alias="AppliesToOverstayFee")
    applies_to_min_max_cost: bool = Field(..., alias="AppliesMinimumMaximumCost")


class TaxRuleList(BaseModel):
    """See section 8.3.5.3.50 in ISO 15118-20"""

    tax_rule: List[TaxRule] = Field(..., max_items=10, alias="TaxRule")


class PriceRule(BaseModel):
    """See section 8.3.5.3.54 in ISO 15118-20"""

    energy_fee: RationalNumber = Field(..., alias="EnergyFee")
    parking_fee: RationalNumber = Field(None, alias="ParkingFee")
    parking_fee_period: int = Field(None, le=UINT_32_MAX, alias="ParkingFeePeriod")
    carbon_dioxide_emission: int = Field(
        None, le=UINT_16_MAX, alias="CarbonDioxideEmission"
    )
    # XSD type unsignedByte with value range [0..255]
    renewable_energy_percentage: int = Field(
        None, ge=0, le=255, alias="RenewableGenerationPercentage"
    )
    power_range_start: RationalNumber = Field(..., alias="PowerRangeStart")


class PriceRuleStack(BaseModel):
    """See section 8.3.5.3.53 in ISO 15118-20"""

    duration: int = Field(..., ge=0, le=UINT_32_MAX, alias="Duration")
    price_rules: List[PriceRule] = Field(..., max_items=8, alias="PriceRule")


class PriceRuleStackList(BaseModel):
    """See section 8.3.5.3.52 in ISO 15118-20"""

    price_rule_stacks: List[PriceRuleStack] = Field(
        ..., max_items=1024, alias="PriceRuleStack"
    )


class OverstayRule(BaseModel):
    """See section 8.3.5.3.56 in ISO 15118-20"""

    description: Description = Field(None, alias="OverstayRuleDescription")
    start_time: int = Field(..., ge=0, le=UINT_32_MAX, alias="StartTime")
    fee: RationalNumber = Field(..., alias="OverstayFee")
    fee_period: int = Field(..., ge=0, le=UINT_32_MAX, alias="OverstayFeePeriod")


class OverstayRuleList(BaseModel):
    """See section 8.3.5.3.55 in ISO 15118-20"""

    time_threshold: int = Field(
        None, ge=0, le=UINT_32_MAX, alias="OverstayTimeThreshold"
    )
    power_threshold: RationalNumber = Field(None, alias="OverstayPowerThreshold")
    rules: List[OverstayRule] = Field(..., max_items=5, alias="OverstayRule")


class AdditionalService(BaseModel):
    """See section 8.3.5.3.58 in ISO 15118-20"""

    service_name: Name = Field(..., alias="ServiceName")
    service_fee: RationalNumber = Field(..., alias="ServiceFee")


class AdditionalServiceList(BaseModel):
    """See section 8.3.5.3.57 in ISO 15118-20"""

    additional_services: List[AdditionalService] = Field(
        ..., max_items=5, alias="AdditionalService"
    )


class AbsolutePriceSchedule(PriceSchedule):
    """See section 8.3.5.3.45 in ISO 15118-20"""

    # 'Id' is actually an XML attribute, but JSON (our serialisation method)
    # doesn't have attributes. The EXI codec has to en-/decode accordingly.
    id: str = Field(None, alias="Id")
    currency: str = Field(..., max_length=3, alias="Currency")
    language: str = Field(..., max_length=3, alias="Language")
    price_algorithm: str = Field(..., max_length=255, alias="PriceAlgorithm")
    min_cost: RationalNumber = Field(None, alias="MinimumCost")
    max_cost: RationalNumber = Field(None, alias="MaximumCost")
    tax_rules: TaxRuleList = Field(None, alias="TaxRules")
    price_rule_stacks: PriceRuleStackList = Field(..., alias="PriceRuleStacks")
    overstay_rules: OverstayRuleList = Field(None, alias="OverstayRules")
    additional_services: AdditionalServiceList = Field(
        None, alias="AdditionalSelectedServices"
    )


class ChargingSchedule(BaseModel):
    """See section 8.3.5.3.40 in ISO 15118-20"""

    power_schedule: PowerSchedule = Field(..., alias="PowerSchedule")
    price_level_schedule: PriceLevelSchedule = Field(None, alias="PriceLevelSchedule")
    absolute_price_schedule: AbsolutePriceSchedule = Field(
        None, alias="AbsolutePriceSchedule"
    )

    @root_validator(pre=True)
    def either_price_levels_or_absolute_prices(cls, values):
        """
        Either price_level_schedule or absolute_price_schedule must be set,
        depending on whether abstract price levels or absolute prices are used
        to indicate costs for the charging session.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "price_level_schedule",
                "PriceLevelSchedule",
                "absolute_price_schedule",
                "AbsolutePriceSchedule",
            ],
            values,
            True,
        ):
            return values


class DischargingSchedule(BaseModel):
    """See section 8.3.5.3.40 in ISO 15118-20"""

    power_schedule: PowerSchedule = Field(..., alias="PowerSchedule")
    price_level_schedule: PriceLevelSchedule = Field(None, alias="PriceLevelSchedule")
    absolute_price_schedule: AbsolutePriceSchedule = Field(
        None, alias="AbsolutePriceSchedule"
    )

    # TODO Need to add a root validator to check if power schedule entries are negative
    #      for discharging (also heck other discharging fields in other types)

    @root_validator(pre=True)
    def either_price_levels_or_absolute_prices(cls, values):
        """
        Either price_level_schedule or absolute_price_schedule must be set,
        depending on abstract price levels or absolute prices are used to
        indicate costs for the charging session.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "price_level_schedule",
                "PriceLevelSchedule",
                "absolute_price_schedule",
                "AbsolutePriceSchedule",
            ],
            values,
            True,
        ):
            return values


class ScheduleTuple(BaseModel):
    """See section 8.3.5.3.17 in ISO 15118-20"""

    schedule_tuple_id: NumericID = Field(..., alias="ScheduleTupleID")
    charging_schedule: ChargingSchedule = Field(..., alias="ChargingSchedule")
    discharging_schedule: DischargingSchedule = Field(None, alias="DischargingSchedule")


class ScheduledScheduleExchangeResParams(BaseModel):
    """See section 8.3.5.3.16 in ISO 15118-20"""

    schedule_tuples: List[ScheduleTuple] = Field(
        ..., max_items=3, alias="ScheduleTuple"
    )


class DynamicScheduleExchangeResParams(BaseModel):
    """See section 8.3.5.3.15 in ISO 15118-20"""

    departure_time: int = Field(None, ge=0, le=UINT_32_MAX, alias="DepartureTime")
    # XSD type byte with value range [0..100]
    min_soc: int = Field(None, ge=0, le=100, alias="MinimumSOC")
    # XSD type byte with value range [0..100]
    target_soc: int = Field(None, ge=0, le=100, alias="TargetSOC")
    price_level_schedule: PriceLevelSchedule = Field(None, alias="PriceLevelSchedule")
    absolute_price_schedule: AbsolutePriceSchedule = Field(
        None, alias="AbsolutePriceSchedule"
    )

    @root_validator(pre=True)
    def min_soc_less_than_or_equal_to_target_soc(cls, values):
        """
        The min_soc value must be smaller or equal to target_soc ([V2G20-1640]).

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        # TODO Also check other classes that contain min_soc and target_soc
        min_soc, target_soc = values.get("min_soc"), values.get("target_soc")
        if min_soc is None and target_soc is None:
            # When decoding from EXI to JSON dict
            min_soc, target_soc = values.get("MinimumSOC"), values.get("TargetSOC")

        if (min_soc and target_soc) and min_soc > target_soc:
            raise ValueError(
                "MinimumSOC must be less than or equal to TargetSOC.\n"
                f"MinimumSOC: {min_soc}, TargetSOC: {target_soc}"
            )

        return values


class ScheduleExchangeRes(V2GResponse):
    """See section 8.3.4.3.7.3 in ISO 15118-20"""

    evse_processing: Processing = Field(..., alias="EVSEProcessing")
    scheduled_params: ScheduledScheduleExchangeResParams = Field(
        None, alias="Scheduled_SEResControlMode"
    )
    dynamic_params: DynamicScheduleExchangeResParams = Field(
        None, alias="Dynamic_SEResControlMode"
    )
    go_to_pause: bool = Field(None, alias="GoToPause")

    @root_validator(pre=True)
    def either_scheduled_or_dynamic(cls, values):
        """
        Either scheduled_params or dynamic_params must be set, depending on
        whether the charging process is governed by charging schedules or
        dynamic charging settings from the SECC.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        evse_processing = values.get("evse_processing")
        if evse_processing is None:
            # When decoding from EXI to JSON dict
            evse_processing = values.get("EVSEProcessing")
        if evse_processing == Processing.ONGOING:
            return values

        # Check if either the dynamic or scheduled parameters are set, but only in case
        # evse_processing is set to FINISHED
        if one_field_must_be_set(
            [
                "scheduled_params",
                "Scheduled_SEResControlMode",
                "dynamic_params",
                "Dynamic_SEResControlMode",
            ],
            values,
            True,
        ):
            return values


class EVPowerProfileEntryList(BaseModel):
    """See section 8.3.5.3.10 in ISO 15118-20"""

    entries: List[PowerScheduleEntry] = Field(
        ..., max_items=2048, alias="EVPowerProfileEntry"
    )


class PowerToleranceAcceptance(str, Enum):
    """See section 8.3.5.3.12 in ISO 15118-20"""

    NOT_CONFIRMED = "PowerToleranceNotConfirmed"
    CONFIRMED = "PowerToleranceConfirmed"


class ScheduledEVPowerProfile(BaseModel):
    """See section 8.3.5.3.12 in ISO 15118-20"""

    selected_schedule_tuple_id: NumericID = Field(..., alias="SelectedScheduleTupleID")
    power_tolerance_acceptance: PowerToleranceAcceptance = Field(
        ..., alias="PowerToleranceAcceptance"
    )


class DynamicEVPowerProfile(BaseModel):
    """See section 8.3.5.3.11 in ISO 15118-20"""


class EVPowerProfile(BaseModel):
    """See section 8.3.5.3.9 in ISO 15118-20"""

    time_anchor: int = Field(..., alias="TimeAnchor")
    entry_list: EVPowerProfileEntryList = Field(..., alias="EVPowerProfileEntries")
    scheduled_profile: ScheduledEVPowerProfile = Field(
        None, alias="Scheduled_EVPPTControlMode"
    )
    dynamic_profile: DynamicEVPowerProfile = Field(
        None, alias="Dynamic_EVPPTControlMode"
    )

    @root_validator(pre=True)
    def either_scheduled_or_dynamic(cls, values):
        """
        Either scheduled_profile or dynamic_profile must be set, depending on whether
        the charging process is governed by charging schedules or dynamic charging
        settings from the SECC.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "scheduled_profile",
                "Scheduled_EVPPTControlMode",
                "dynamic_profile",
                "Dynamic_EVPPTControlMode",
            ],
            values,
            True,
        ):
            return values


class ChannelSelection(str, Enum):
    """See section 8.3.4.3.8.2 in ISO 15118-20"""

    CHARGE = "Charge"
    DISCHARGE = "Discharge"


class ChargeProgress(str, Enum):
    """See section 8.3.4.3.8.2 in ISO 15118-20"""

    START = "Start"
    STOP = "Stop"
    STANDBY = "Standby"
    SCHEDULE_RENEGOTIATION = "ScheduleRenegotiation"


class PowerDeliveryReq(V2GRequest):
    """See section 8.3.4.3.8.2 in ISO 15118-20"""

    ev_processing: Processing = Field(..., alias="EVProcessing")
    charge_progress: ChargeProgress = Field(..., alias="ChargeProgress")
    ev_power_profile: EVPowerProfile = Field(None, alias="EVPowerProfile")
    bpt_channel_selection: ChannelSelection = Field(None, alias="BPT_ChannelSelection")

    @root_validator(pre=True)
    def set_ev_power_profile_if_processing_finished_and_start_charging(cls, values):
        """
        The optional ev_power_profile field must be set once the EVCC finishes
        processing, thereby setting the field ev_processing to FINISHED, and if the
        charge_progress is set to START.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use

        ev_processing = values.get("ev_processing")
        charge_progress = values.get("charge_progress")
        if ev_processing is None:
            # When decoding from EXI to JSON dict
            ev_processing = values.get("EVProcessing")
        if charge_progress is None:
            # When decoding from EXI to JSON dict
            charge_progress = values.get("ChargeProgress")
        if (
            ev_processing == Processing.ONGOING
            or charge_progress == ChargeProgress.STOP
        ):
            return values

        ev_power_profile = values.get("ev_power_profile")
        if ev_power_profile is None:
            # When decoding from EXI to JSON dict
            ev_power_profile = values.get("EVPowerProfile")

        if ev_power_profile is None:
            raise ValueError(
                "EVPowerProfile is not set although EVProcessing is set to FINISHED"
            )

        return values


class PowerDeliveryRes(V2GResponse):
    """See section 8.3.4.3.8.3 in ISO 15118-20"""

    evse_status: EVSEStatus = Field(None, alias="EVSEStatus")


class ScheduledSignedMeterData(BaseModel):
    """See section 8.3.5.3.38 in ISO 15118-20"""

    selected_schedule_tuple_id: NumericID = Field(..., alias="SelectedScheduleTupleID")


class DynamicSignedMeterData(BaseModel):
    """See section 8.3.5.3.37 in ISO 15118-20"""


class SignedMeteringData(BaseModel):
    """See section 8.3.5.3.36 in ISO 15118-20"""

    # 'Id' is actually an XML attribute, but JSON (our serialisation method)
    # doesn't have attributes. The EXI codec has to en-/decode accordingly.
    id: str = Field(..., max_length=255, alias="Id")
    session_id: str = Field(..., max_length=16, alias="SessionID")
    meter_info: MeterInfo = Field(..., alias="MeterInfo")
    receipt: Receipt = Field(None, alias="Receipt")
    scheduled_smart_meter_data: ScheduledSignedMeterData = Field(
        None, alias="Scheduled_SMDTControlMode"
    )
    dynamic_smart_meter_data: DynamicSignedMeterData = Field(
        None, alias="Dynamic_SMDTControlMode"
    )

    @root_validator(pre=True)
    def either_scheduled_or_dynamic(cls, values):
        """
        Either scheduled_smart_meter_data or dynamic_smart_meter_data must be
        set, depending on whether the charging process is governed by charging s
        chedules or dynamic charging settings from the SECC.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "scheduled_smart_meter_data",
                "Scheduled_SMDTControlMode",
                "dynamic_smart_meter_data",
                "Dynamic_SMDTControlMode",
            ],
            values,
            True,
        ):
            return values

        @validator("session_id")
        def check_sessionid_is_hexbinary(cls, value):
            """
            Checks whether the session_id field is a hexadecimal representation of
            8 bytes.

            Pydantic validators are "class methods",
            see https://pydantic-docs.helpmanual.io/usage/validators/
            """
            # pylint: disable=no-self-argument
            # pylint: disable=no-self-use
            try:
                int(value, 16)
                return value
            except ValueError as exc:
                raise ValueError(
                    f"Invalid value '{value}' for SessionID (must be "
                    f"hexadecimal representation of max 8 bytes)"
                ) from exc


class MeteringConfirmationReq(V2GRequest):
    """See section 8.3.4.3.11.2 in ISO 15118-20"""

    signed_metering_data: SignedMeteringData = Field(..., alias="SignedMeteringData")


class MeteringConfirmationRes(V2GResponse):
    """See section 8.3.4.3.11.3 in ISO 15118-20"""


class ChargingSession(str, Enum):
    """See section 8.3.4.3.10.2 in ISO 15118-20"""

    PAUSE = "Pause"
    TERMINATE = "Terminate"
    SERVICE_RENEGOTIATION = "ServiceRenegotiation"


class SessionStopReq(V2GRequest):
    """See section 8.3.4.3.10.2 in ISO 15118-20"""

    charging_session: ChargingSession = Field(..., alias="ChargingSession")
    ev_termination_code: Name = Field(None, alias="EVTerminationCode")
    ev_termination_explanation: str = Field(
        None, max_length=160, alias="EVTerminationExplanation"
    )


class SessionStopRes(V2GResponse):
    """See section 8.3.4.3.10.3 in ISO 15118-20"""


class CertificateInstallationReq(V2GRequest):
    """See section 8.3.4.3.9.2 in ISO 15118-20"""

    oem_prov_cert_chain: SignedCertificateChain = Field(
        ..., alias="OEMProvisioningCertificateChain"
    )
    root_cert_id_list: RootCertificateIDList = Field(
        ..., alias="ListOfRootCertificateIDs"
    )
    # XSD type unsignedShort (16 bit integer) with value range [0..65535]
    max_contract_cert_chains: int = Field(
        ..., ge=0, le=UINT_16_MAX, alias="MaximumContractCertificateChains"
    )
    prioritized_emaids: EMAIDList = Field(None, alias="PrioritizedEMAIDs")


class SignedInstallationData(BaseModel):
    """See section 8.3.5.3.39 in ISO 15118-20"""

    # 'Id' is actually an XML attribute, but JSON (our serialisation method)
    # doesn't have attributes. The EXI codec has to en-/decode accordingly.
    id: str = Field(..., max_length=255, alias="Id")
    contract_cert_chain: ContractCertificateChain = Field(
        ..., alias="ContractCertificateChain"
    )
    ecdh_curve: ECDHCurve = Field(..., alias="ECDHCurve")
    dh_public_key: bytes = Field(..., max_length=133, alias="DHPublicKey")
    secp521_encrypted_private_key: bytes = Field(
        None, min_length=94, max_length=94, alias="SECP521_EncryptedPrivateKey"
    )
    x448_encrypted_private_key: bytes = Field(
        None, min_length=84, max_length=84, alias="X448_EncryptedPrivateKey"
    )
    tpm_encrypted_private_key: bytes = Field(
        None, min_length=209, max_length=209, alias="TPM_EncryptedPrivateKey"
    )

    @root_validator(pre=True)
    def one_encryption_mode(cls, values):
        """
        Either secp521_encrypted_private_key or x448_encrypted_private_key or
        tpm_encrypted_private_key must be set, depending on which encryption
        algorithm is used to encrypt the private key associated with the
        contract certificate.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "secp521_encrypted_private_key",
                "SECP521_EncryptedPrivateKey",
                "x448_encrypted_private_key",
                "X448_EncryptedPrivateKey",
                "tpm_encrypted_private_key",
                "TPM_EncryptedPrivateKey",
            ],
            values,
            True,
        ):
            return values


class CertificateInstallationRes(V2GResponse):
    """See section 8.3.4.3.9.3 in ISO 15118-20"""

    evse_processing: Processing = Field(..., alias="EVSEProcessing")
    cps_certificate_chain: CertificateChain = Field(..., alias="CPSCertificateChain")
    signed_installation_data: SignedInstallationData = Field(
        ..., alias="SignedInstallationData"
    )
    # XSD type unsignedByte with value range [0..255]
    remaining_contract_cert_chains: int = Field(
        ..., ge=0, le=255, alias="RemainingContractCertificateChains"
    )


class EVCheckInStatus(str, Enum):
    """See section 8.3.4.8.1.1.2 in ISO 15118-20"""

    check_in = "CheckIn"
    processing = "Processing"
    completed = "Completed"


class EVCheckOutStatus(str, Enum):
    """See section 8.3.4.8.1.2.2 in ISO 15118-20"""

    check_out = "CheckOut"
    processing = "Processing"
    completed = "Completed"


class EVSECheckOutStatus(str, Enum):
    """See section 8.3.4.8.1.2.3 in ISO 15118-20"""

    scheduled = "Scheduled"
    completed = "Completed"


class ParkingMethod(str, Enum):
    """See section 8.3.4.8.1.1.2 in ISO 15118-20"""

    auto_parking = "AutoParking"
    mv_guided_manual = "MVGuideManual"
    manual = "Manual"


class TargetPosition(BaseModel):
    """Defined in XSD schema but not used in any message"""

    target_offset_x: int = Field(..., alias="TargetOffsetX")
    target_offset_y: int = Field(..., alias="TargetOffsetY")


class VehicleCheckInReq(V2GRequest):
    """See section 8.3.4.8.1.1.2 in ISO 15118-20"""

    ev_check_in_status: EVCheckInStatus = Field(..., alias="EVCheckInStatus")
    parking_method: ParkingMethod = Field(None, alias="ParkingMethod")


class VehicleCheckInRes(V2GResponse):
    """See section 8.3.4.8.1.1.3 in ISO 15118-20"""

    vehicle_space: int = Field(..., alias="VehicleSpace")
    target_offset: TargetPosition = Field(None, alias="TargetOffset")


class VehicleCheckOutReq(V2GRequest):
    """See section 8.3.4.8.1.2.2 in ISO 15118-20"""

    ev_check_out_status: EVCheckOutStatus = Field(..., alias="EVCheckOutStatus")
    check_out_time: int = Field(..., alias="CheckOutTime")


class VehicleCheckOutRes(V2GResponse):
    """See section 8.3.4.8.1.3.2 in ISO 15118-20"""

    evse_check_out_status: EVSECheckOutStatus = Field(..., alias="EVSECheckOutStatus")


# ============================================================================
# |            HELPFUL CUSTOM CLASSES FOR A COMMUNICATION SESSION            |
# ============================================================================


@dataclass
class MatchedService:
    """
    This class puts all service-related information into one place. ISO 15118-20
    messages and data types scatter information about service ID, typeo of service
    (energy or value-added service) parameter sets, and whether a service is free.
    This custom class provides easier access to all this information, which comes in
    handy throughout the various states.
    """

    service: ServiceV20
    # If it's not an energy transfer service, then it's a value-added service (VAS)
    is_energy_service: bool
    is_free: bool
    parameter_sets: List[ParameterSet]

    def service_parameter_set_ids(self) -> List[Tuple[int, int]]:
        service_param_set_ids: List[Tuple[int, int]] = []
        for parameter_set in self.parameter_sets:
            service_param_set_ids.append((self.service.id, parameter_set.id))
        return service_param_set_ids


@dataclass
class SelectedEnergyService:
    """
    This class puts all necessary information about the energy service, which the EVCC
    selects for a charging session, in one place. A SelectedService instance (datatype
    used in ISO 15118-20) only contains a ServiceID and a ParameterSetID, but not the
    actual parameter sets, for which we'd have to look elsewhere and loop through a
    list of offered parameter sets. The parameter sets describe important service
    details, which we need throughout the state machine.
    """

    service: ServiceV20
    is_free: bool
    parameter_set: ParameterSet

    @property
    def service_id(self) -> int:
        return self.service.id

    @property
    def parameter_set_id(self) -> int:
        return self.parameter_set.id


@dataclass
class SelectedVAS:
    """
    Similar to the custom class SelectedEnergyService, but for the value-added services
    (VAS), which the EVCC selects for a charging session.
    """

    service: ServiceV20
    is_free: bool
    parameter_set: ParameterSet
```

## File: iso15118/shared/messages/iso15118_20/dc.py
```python
"""
This modules contains classes which implement all the elements of the
ISO 15118-20 XSD file V2G_CI_DC.xsd (see folder 'schemas').
These are the V2GMessages exchanged between the EVCC and the SECC specifically
for DC charging.

All classes are ultimately subclassed from pydantic's BaseModel to ease
validation when instantiating a class and to reduce boilerplate code.
Pydantic's Field class is used to be able to create a json schema of each model
(or class) that matches the definitions in the XSD schema, including the XSD
element names by using the 'alias' attribute.
"""

from pydantic import Field, root_validator

from iso15118.shared.messages import BaseModel
from iso15118.shared.messages.iso15118_20.common_types import (
    ChargeLoopReq,
    ChargeLoopRes,
    ChargeParameterDiscoveryReq,
    ChargeParameterDiscoveryRes,
    DynamicChargeLoopReqParams,
    DynamicChargeLoopResParams,
    Processing,
    RationalNumber,
    ScheduledChargeLoopReqParams,
    ScheduledChargeLoopResParams,
    V2GRequest,
    V2GResponse,
)
from iso15118.shared.validators import one_field_must_be_set


class DCChargeParameterDiscoveryReqParams(BaseModel):
    """See section 8.3.5.5.1 in ISO 15118-20"""

    ev_max_charge_power: RationalNumber = Field(..., alias="EVMaximumChargePower")
    ev_min_charge_power: RationalNumber = Field(..., alias="EVMinimumChargePower")
    ev_max_charge_current: RationalNumber = Field(..., alias="EVMaximumChargeCurrent")
    ev_min_charge_current: RationalNumber = Field(..., alias="EVMinimumChargeCurrent")
    ev_max_voltage: RationalNumber = Field(..., alias="EVMaximumVoltage")
    ev_min_voltage: RationalNumber = Field(..., alias="EVMinimumVoltage")
    target_soc: int = Field(None, ge=0, le=100, alias="TargetSOC")


class DCChargeParameterDiscoveryResParams(BaseModel):
    """See section 8.3.5.5.2 in ISO 15118-20"""

    evse_max_charge_power: RationalNumber = Field(..., alias="EVSEMaximumChargePower")
    evse_min_charge_power: RationalNumber = Field(..., alias="EVSEMinimumChargePower")
    evse_max_charge_current: RationalNumber = Field(
        ..., alias="EVSEMaximumChargeCurrent"
    )
    evse_min_charge_current: RationalNumber = Field(
        ..., alias="EVSEMinimumChargeCurrent"
    )
    evse_max_voltage: RationalNumber = Field(..., alias="EVSEMaximumVoltage")
    evse_min_voltage: RationalNumber = Field(..., alias="EVSEMinimumVoltage")
    evse_power_ramp_limit: RationalNumber = Field(None, alias="EVSEPowerRampLimitation")


class BPTDCChargeParameterDiscoveryReqParams(DCChargeParameterDiscoveryReqParams):
    """
    See section 8.3.5.5.7.1 in ISO 15118-20
    BPT = Bidirectional Power Transfer
    """

    ev_max_discharge_power: RationalNumber = Field(..., alias="EVMaximumDischargePower")
    ev_min_discharge_power: RationalNumber = Field(..., alias="EVMinimumDischargePower")
    ev_max_discharge_current: RationalNumber = Field(
        ..., alias="EVMaximumDischargeCurrent"
    )
    ev_min_discharge_current: RationalNumber = Field(
        ..., alias="EVMinimumDischargeCurrent"
    )


class BPTDCChargeParameterDiscoveryResParams(DCChargeParameterDiscoveryResParams):
    """
    See section 8.3.5.5.7.2 in ISO 15118-20
    BPT = Bidirectional Power Transfer
    """

    evse_max_discharge_power: RationalNumber = Field(
        ..., alias="EVSEMaximumDischargePower"
    )
    evse_min_discharge_power: RationalNumber = Field(
        ..., alias="EVSEMinimumDischargePower"
    )
    evse_max_discharge_current: RationalNumber = Field(
        ..., alias="EVSEMaximumDischargeCurrent"
    )
    evse_min_discharge_current: RationalNumber = Field(
        ..., alias="EVSEMinimumDischargeCurrent"
    )


class ScheduledDCChargeLoopReqParams(ScheduledChargeLoopReqParams):
    """See section 8.3.5.5.4 in ISO 15118-20"""

    ev_target_current: RationalNumber = Field(..., alias="EVTargetCurrent")
    ev_target_voltage: RationalNumber = Field(..., alias="EVTargetVoltage")
    ev_max_charge_power: RationalNumber = Field(None, alias="EVMaximumChargePower")
    ev_min_charge_power: RationalNumber = Field(None, alias="EVMinimumChargePower")
    ev_max_charge_current: RationalNumber = Field(None, alias="EVMaximumChargeCurrent")
    ev_max_voltage: RationalNumber = Field(None, alias="EVMaximumVoltage")
    ev_min_voltage: RationalNumber = Field(None, alias="EVMinimumVoltage")

    # TODO: Validator for ensuring only one of target current and target voltage
    #  is provided V2G20-2183


class ScheduledDCChargeLoopResParams(ScheduledChargeLoopResParams):
    """See section 8.3.5.5.6 in ISO 15118-20"""

    evse_maximum_charge_power: RationalNumber = Field(
        None, alias="EVSEMaximumChargePower"
    )
    evse_minimum_charge_power: RationalNumber = Field(
        None, alias="EVSEMinimumChargePower"
    )
    evse_maximum_charge_current: RationalNumber = Field(
        None, alias="EVSEMaximumChargeCurrent"
    )
    evse_maximum_voltage: RationalNumber = Field(None, alias="EVSEMaximumVoltage")


class BPTScheduledDCChargeLoopReqParams(ScheduledDCChargeLoopReqParams):
    """See section 8.3.5.5.7.4 in ISO 15118-20"""

    ev_max_discharge_power: RationalNumber = Field(
        None, alias="EVMaximumDischargePower"
    )
    ev_min_discharge_power: RationalNumber = Field(
        None, alias="EVMinimumDischargePower"
    )
    ev_max_discharge_current: RationalNumber = Field(
        None, alias="EVMaximumDischargeCurrent"
    )


class BPTScheduledDCChargeLoopResParams(ScheduledDCChargeLoopResParams):
    """See section 8.3.5.5.7.4 in ISO 15118-20"""

    evse_max_discharge_power: RationalNumber = Field(
        None, alias="EVSEMaximumDischargePower"
    )
    evse_min_discharge_power: RationalNumber = Field(
        None, alias="EVSEMinimumDischargePower"
    )
    evse_max_discharge_current: RationalNumber = Field(
        None, alias="EVSEMaximumDischargeCurrent"
    )
    evse_min_voltage: RationalNumber = Field(None, alias="EVSEMinimumVoltage")


class DynamicDCChargeLoopReqParams(DynamicChargeLoopReqParams):
    """See section 8.3.5.5.3 in ISO 15118-20"""

    ev_max_charge_power: RationalNumber = Field(..., alias="EVMaximumChargePower")
    ev_min_charge_power: RationalNumber = Field(..., alias="EVMinimumChargePower")
    ev_max_charge_current: RationalNumber = Field(..., alias="EVMaximumChargeCurrent")
    ev_max_voltage: RationalNumber = Field(..., alias="EVMaximumVoltage")
    ev_min_voltage: RationalNumber = Field(..., alias="EVMinimumVoltage")


class DynamicDCChargeLoopRes(DynamicChargeLoopResParams):
    """See section 8.3.5.5.5 in ISO 15118-20"""

    evse_maximum_charge_power: RationalNumber = Field(
        ..., alias="EVSEMaximumChargePower"
    )
    evse_minimum_charge_power: RationalNumber = Field(
        ..., alias="EVSEMinimumChargePower"
    )
    evse_maximum_charge_current: RationalNumber = Field(
        ..., alias="EVSEMaximumChargeCurrent"
    )
    evse_maximum_voltage: RationalNumber = Field(..., alias="EVSEMaximumVoltage")


class BPTDynamicDCChargeLoopReqParams(DynamicDCChargeLoopReqParams):
    """See section 8.3.5.5.7.3 in ISO 15118-20"""

    ev_max_discharge_power: RationalNumber = Field(..., alias="EVMaximumDischargePower")
    ev_min_discharge_power: RationalNumber = Field(..., alias="EVMinimumDischargePower")
    ev_max_discharge_current: RationalNumber = Field(
        ..., alias="EVMaximumDischargeCurrent"
    )
    ev_max_v2x_energy_request: RationalNumber = Field(
        None, alias="EVMaximumV2XEnergyRequest"
    )
    ev_min_v2x_energy_request: RationalNumber = Field(
        None, alias="EVMinimumV2XEnergyRequest"
    )


class BPTDynamicDCChargeLoopRes(DynamicDCChargeLoopRes):
    """See section 8.3.5.5.7.5 in ISO 15118-20"""

    evse_max_discharge_power: RationalNumber = Field(
        ..., alias="EVSEMaximumDischargePower"
    )
    evse_min_discharge_power: RationalNumber = Field(
        ..., alias="EVSEMinimumDischargePower"
    )
    evse_max_discharge_current: RationalNumber = Field(
        ..., alias="EVSEMaximumDischargeCurrent"
    )
    evse_min_voltage: RationalNumber = Field(..., alias="EVSEMinimumVoltage")


class DCChargeParameterDiscoveryReq(ChargeParameterDiscoveryReq):
    """See section 8.3.4.5.2.2 in ISO 15118-20"""

    dc_params: DCChargeParameterDiscoveryReqParams = Field(
        None, alias="DC_CPDReqEnergyTransferMode"
    )
    bpt_dc_params: BPTDCChargeParameterDiscoveryReqParams = Field(
        None, alias="BPT_DC_CPDReqEnergyTransferMode"
    )

    @root_validator(pre=True)
    def either_dc_or_dc_bpt_params(cls, values):
        """
        Either dc_params or bpt_dc_params must be set, depending on whether
        unidirectional or bidirectional power transfer was chosen.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "dc_params",
                "DC_CPDReqEnergyTransferMode",
                "bpt_dc_params",
                "BPT_DC_CPDReqEnergyTransferMode",
            ],
            values,
            True,
        ):
            return values

    def __str__(self):
        # The XSD-conform name
        return "DC_ChargeParameterDiscoveryReq"


class DCChargeParameterDiscoveryRes(ChargeParameterDiscoveryRes):
    """See section 8.3.4.5.2.3 in ISO 15118-20"""

    dc_params: DCChargeParameterDiscoveryResParams = Field(
        None, alias="DC_CPDResEnergyTransferMode"
    )
    bpt_dc_params: BPTDCChargeParameterDiscoveryResParams = Field(
        None, alias="BPT_DC_CPDResEnergyTransferMode"
    )

    @root_validator(pre=True)
    def either_dc_or_bpt_dc_params(cls, values):
        """
        Either dc_params or bpt_dc_params must be set, depending on whether
        unidirectional or bidirectional power transfer was chosen.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "dc_params",
                "DC_CPDResEnergyTransferMode",
                "bpt_dc_params",
                "BPT_DC_CPDResEnergyTransferMode",
            ],
            values,
            True,
        ):
            return values

    def __str__(self):
        # The XSD-conform name
        return "DC_ChargeParameterDiscoveryRes"


class DCChargeLoopReq(ChargeLoopReq):
    """See section 8.3.4.5.5.2 in ISO 15118-20"""

    ev_present_voltage: RationalNumber = Field(..., alias="EVPresentVoltage")
    scheduled_params: ScheduledDCChargeLoopReqParams = Field(
        None, alias="Scheduled_DC_CLReqControlMode"
    )
    dynamic_params: DynamicDCChargeLoopReqParams = Field(
        None, alias="Dynamic_DC_CLReqControlMode"
    )
    bpt_scheduled_params: BPTScheduledDCChargeLoopReqParams = Field(
        None, alias="BPT_Scheduled_DC_CLReqControlMode"
    )
    bpt_dynamic_params: BPTDynamicDCChargeLoopReqParams = Field(
        None, alias="BPT_Dynamic_DC_CLReqControlMode"
    )

    @root_validator(pre=True)
    def either_scheduled_or_dynamic_bpt(cls, values):
        """
        Either scheduled_params or dynamic_params or bpt_scheduled_params or
        bpt_dynamic_params must be set, depending on whether unidirectional or
        bidirectional power transfer and whether scheduled or dynamic mode was chosen.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "scheduled_params",
                "Scheduled_DC_CLReqControlMode",
                "dynamic_params",
                "Dynamic_DC_CLReqControlMode",
                "bpt_scheduled_params",
                "BPT_Scheduled_DC_CLReqControlMode",
                "bpt_dynamic_params",
                "BPT_Dynamic_DC_CLReqControlMode",
            ],
            values,
            True,
        ):
            return values

    def __str__(self):
        # The XSD-conform name
        return "DC_ChargeLoopReq"


class DCChargeLoopRes(ChargeLoopRes):
    """See section 8.3.4.5.5.3 in ISO 15118-20"""

    evse_present_current: RationalNumber = Field(..., alias="EVSEPresentCurrent")
    evse_present_voltage: RationalNumber = Field(..., alias="EVSEPresentVoltage")
    evse_power_limit_achieved: bool = Field(..., alias="EVSEPowerLimitAchieved")
    evse_current_limit_achieved: bool = Field(..., alias="EVSECurrentLimitAchieved")
    evse_voltage_limit_achieved: bool = Field(..., alias="EVSEVoltageLimitAchieved")
    scheduled_dc_charge_loop_res: ScheduledDCChargeLoopResParams = Field(
        None, alias="Scheduled_DC_CLResControlMode"
    )
    dynamic_dc_charge_loop_res: DynamicDCChargeLoopRes = Field(
        None, alias="Dynamic_DC_CLResControlMode"
    )
    bpt_scheduled_dc_charge_loop_res: BPTScheduledDCChargeLoopResParams = Field(
        None, alias="BPT_Scheduled_DC_CLResControlMode"
    )
    bpt_dynamic_dc_charge_loop_res: BPTDynamicDCChargeLoopRes = Field(
        None, alias="BPT_Dynamic_DC_CLResControlMode"
    )

    @root_validator(pre=True)
    def either_scheduled_or_dynamic_bpt(cls, values):
        """
        Either scheduled_dc_charge_loop_res or scheduled_dc_charge_loop_res or
        bpt_scheduled_dc_charge_loop_res or bpt_dynamic_dc_charge_loop_res
        must be set, depending on whether unidirectional or bidirectional power
        transfer and whether scheduled or dynamic mode was chosen.

        Pydantic validators are "class methods",
        see https://pydantic-docs.helpmanual.io/usage/validators/
        """
        # pylint: disable=no-self-argument
        # pylint: disable=no-self-use
        if one_field_must_be_set(
            [
                "scheduled_dc_charge_loop_res",
                "Scheduled_DC_CLResControlMode",
                "dynamic_dc_charge_loop_res",
                "Dynamic_DC_CLResControlMode",
                "bpt_scheduled_dc_charge_loop_res",
                "BPT_Scheduled_DC_CLResControlMode",
                "bpt_dynamic_dc_charge_loop_res",
                "BPT_Dynamic_DC_CLResControlMode",
            ],
            values,
            True,
        ):
            return values

    def __str__(self):
        # The XSD-conform name
        return "DC_ChargeLoopRes"


class DCCableCheckReq(V2GRequest):
    """See section 8.3.4.5.3.2 in ISO 15118-20"""

    def __str__(self):
        # The XSD-conform name
        return "DC_CableCheckReq"


class DCCableCheckRes(V2GResponse):
    """See section 8.3.4.5.3.3 in ISO 15118-20"""

    evse_processing: Processing = Field(..., alias="EVSEProcessing")

    def __str__(self):
        # The XSD-conform name
        return "DC_CableCheckRes"


class DCPreChargeReq(V2GRequest):
    """See section 8.3.4.5.4.1 in ISO 15118-20"""

    ev_processing: Processing = Field(..., alias="EVProcessing")
    ev_present_voltage: RationalNumber = Field(..., alias="EVPresentVoltage")
    ev_target_voltage: RationalNumber = Field(..., alias="EVTargetVoltage")

    def __str__(self):
        # The XSD-conform name
        return "DC_PreChargeReq"


class DCPreChargeRes(V2GResponse):
    """See section 8.3.4.5.4.3 in ISO 15118-20"""

    evse_present_voltage: RationalNumber = Field(..., alias="EVSEPresentVoltage")

    def __str__(self):
        # The XSD-conform name
        return "DC_PreChargeRes"


class DCWeldingDetectionReq(V2GRequest):
    """See section 8.3.4.5.6.2 in ISO 15118-20"""

    ev_processing: Processing = Field(..., alias="EVProcessing")

    def __str__(self):
        # The XSD-conform name
        return "DC_WeldingDetectionReq"


class DCWeldingDetectionRes(V2GResponse):
    """See section 8.3.4.5.6.3 in ISO 15118-20"""

    evse_present_voltage: RationalNumber = Field(..., alias="EVSEPresentVoltage")

    def __str__(self):
        # The XSD-conform name
        return "DC_WeldingDetectionRes"
```
