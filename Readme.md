# ISO15118_EVCAT

**EV Charger as Battery Tester — ISO 15118-20 Communication Layer**

A working ISO 15118-20 EVCC ⇄ SECC implementation, secured with TLS 1.3 / PKI, running across two physically separate Raspberry Pi nodes over a Powerline Communication (PLC) link — extended with a Value-Added Services (VAS) framework for running battery diagnostic tests (discharge capacity, with EIS and HPPC planned) inside a standard charging session.

Student project, SS2026, Technische Hochschule Ingolstadt.
Supervisor: Vaishal Thirugnanam · Project guidance: DSc. Carlos Antônio Rufino Júnior

---

## What This Is

This repository is the communication backbone for a four-team university project converting a conventional EV charger into a battery testing platform. It implements:

1. A standards-conformant **ISO 15118-20** session between a vehicle (EVCC) and a charging station (SECC), running on two independent Raspberry Pi nodes.
2. **TLS 1.3 + PKI certificate** security for that session.
3. A **physics-corrected battery simulation** replacing the unrealistic hardcoded placeholders in the base library.
4. An extensible **diagnostic service framework** that layers battery health tests onto the session as Value-Added Services, without modifying the protocol state machines for each new test.
5. A working **end-to-end battery discharge capacity test** (charge to 100%, discharge at a configurable C-rate, full telemetry report).

This communication layer is what the project's other three work streams (grid-forming frequency regulation, square-wave EIS measurement, HPPC/ICA testing) will run their diagnostics on top of.

---

## Status at a Glance

| Component | Status |
|---|---|
| Physical hardware integration (2× Raspberry Pi 4, 2× devolo Green PHY) | ✅ Done |
| Ethernet ⇄ PLC bridge verification | ✅ Done |
| ISO 15118-2 handshake | ✅ Done |
| Security upgrade: plain TCP → TLS | ✅ Done |
| ISO 15118-20 implementation | ✅ Done |
| PKI certificates | ✅ Working |
| TLS handshake | ✅ Secure |
| Protocol session result (AC) | ✅ Session success |
| Battery physics model (SOC/voltage/limits correction) | ✅ Done |
| Diagnostic service framework (VAS-based, extensible) | ✅ Done |
| Battery discharge capacity test (VAS id 101) | ✅ Done, verified end-to-end |
| EIS diagnostic service (VAS id 102) | 🔶 Architecture ready — implementation pending (Team 2) |
| HPPC diagnostic service (VAS id 103) | 🔶 Architecture ready — implementation pending (Team 3) |
| Real battery / BMS hardware integration | 🔶 Pending — blocked on hardware availability |
| EIS signal-generation hardware integration | 🔶 Pending — blocked on hardware availability |

---

## Repository Structure

```
ISO15118_EVCAT/
├── EVCC_Client/         EVCC-side runner — launches the vehicle-side process,
│                        points at iso15118_core, loads the EVCC config
├── SECC_Master/         SECC-side runner — launches the charger-side process,
│                        points at iso15118_core, loads the SECC config/PKI
├── config/              Session and environment configuration
│                        (.env-style settings, protocol/security selection)
├── iso15118_core/       The protocol implementation — base library plus the
│                        new battery_diagnostics package (see below)
├── logs/                Captured EVCC/SECC session logs
├── Get_it_running        Setup/run instructions for bringing up both nodes
└── Readme.md             This file
```

`EVCC_Client` and `SECC_Master` are run as two **independent processes**, each on its own Raspberry Pi, communicating only through the PLC bridge. There is no shared process or shared memory between them — this mirrors a real vehicle and a real charger.

### `iso15118_core/` — diagnostic framework layout

```
iso15118_core/
└── iso15118/
    └── shared/
        └── battery_diagnostics/          (new package — this project's framework)
            ├── __init__.py
            ├── battery_simulator.py      physics: SOC integration, OCV curve, thermal model
            ├── base_service.py           DiagnosticService interface + CurrentCommand type
            ├── registry.py               ServiceRegistry — routes calls to the active service
            ├── telemetry.py              shared JSON report writer
            └── services/
                ├── health_test.py        BatteryHealthService (VAS id 101) — complete
                ├── eis_test.py            EISService (VAS id 102) — pending
                └── hppc_test.py           HPPCService (VAS id 103) — pending
```

---

## Hardware

| Component | Spec |
|---|---|
| Compute module | Raspberry Pi 4 (×2 — one SECC, one EVCC) |
| PLC modem | devolo dLAN Green PHY, Qualcomm QCA7000 chipset (×2) |
| Standard compliance | IEEE 1901 / ISO 15118-3 / DIN 70121 |
| Modulation | OFDM, 2–28 MHz carrier |
| Interface | Ethernet-to-PLC bridging |
| Data rate | Up to 10 Mbps |

**Topology:**

```
Raspberry Pi (SECC)            Raspberry Pi (EVCC)
      │ Ethernet                     │ Ethernet
      ▼                              ▼
Green PHY Eval Board I  ───wire───  Green PHY Eval Board II
```

Each Raspberry Pi connects to its local PLC evaluation board over Ethernet. The two PLC boards are interconnected by a wire path standing in for the CP/PE conductor pair of a real Type 2/CCS charging connector.

---

## Protocol & Security

- **Base library:** [EcoG-io/iso15118](https://github.com/EcoG-io/iso15118) — open-source Python implementation of ISO 15118-2, ISO 15118-20, and DIN SPEC 70121.
- **Generation used:** ISO 15118-20, selected for native Bidirectional Power Transfer (BPT) and the Value-Added Services (VAS) extensibility mechanism — both required for discharge-based diagnostics.
- **Discovery:** SECC Discovery Protocol (SDP) over UDP multicast, link-local IPv6.
- **Session transport:** TCP, upgraded to **TLS 1.3** before any V2G message is exchanged.
- **Authentication:** Certificate-based PKI (root → sub-CA → leaf), matching the standard's Plug & Charge security model. Certificates generated via the base library's `create_certs.sh` tooling.
- **Energy services used:** `DC` and `DC_BPT` (service IDs 2 and 6) — `DC_BPT` is required for the discharge phase of any diagnostic test.

---

## What Was Fixed in the Base Library

The base library's simulated controllers (`SimEVSEController`, `SimEVController`) ship with multiple hardcoded placeholder values not tied to real power flow. These were identified and corrected:

| Field | Base library behavior | Correction applied |
|---|---|---|
| State of charge (SOC) | Fixed step per charge-loop cycle, independent of power/time | Energy-integrated: `ΔSOC = (P × Δt) / capacity` |
| Terminal voltage | Fixed constant regardless of SOC | SOC-dependent open-circuit-voltage curve |
| Charging completion | Fixed loop-cycle counter | Driven by actual SOC reaching target |
| SECC/EVSE power limits | Not consistently fed back to EV-side request | EVCC reads and respects negotiated SECC limits every cycle |

---

## Diagnostic Service Framework

### Why Value-Added Services (VAS)

ISO 15118-20 defines a fixed set of energy transfer services (AC, AC_BPT, DC, DC_BPT) with dedicated state-machine paths. Extending those for every new diagnostic test would mean touching core protocol code repeatedly. VAS is the standard's built-in mechanism for advertising optional services alongside an already-running energy session — a battery test needs exactly that: a DC_BPT session already running, plus a layer of test sequencing on top. No new message types, no new protocol states.

### Architecture: Four Layers

| Layer | Responsibility |
|---|---|
| 1. ISO 15118-20 Protocol | Message encoding, state machines (base library, unmodified except two integration points) |
| 2. Controller Adapters | Thin glue holding one `ServiceRegistry`; no test-specific logic |
| 3. Diagnostic Service Framework | All test logic, phase sequencing, telemetry — the project's original contribution |
| 4. Battery Physics Model | Pure SOC/voltage/temperature simulation, no protocol or test knowledge |

A `ServiceRegistry` on the SECC side maps VAS service ID → diagnostic service implementation, and routes four lifecycle calls (parameter advertisement, selection, per-cycle execution, session-end finalization) to whichever service is active. Adding a new test = one new class implementing a four-method interface, plus one registration line.

### Service ID Allocation

| Service ID | Name | Type | Status |
|---|---|---|---|
| 2 | DC | Standard energy service | Unchanged |
| 6 | DC_BPT | Standard energy service | Unchanged |
| 101 | BatteryHealthTest | Custom VAS | ✅ Implemented |
| 102 | EISTest | Custom VAS | 🔶 Planned |
| 103 | HPPCTest | Custom VAS | 🔶 Planned |

### Implemented: Battery Discharge Capacity Test (VAS 101)

Two-phase test: charge the battery to 100%, then discharge at a configurable C-rate down to a configurable cutoff SOC, recording voltage/current/SOC/energy/internal resistance/temperature every cycle. State of Health is computed as measured discharge energy ÷ nominal capacity × 100, written to a JSON telemetry report at session end.

Default parameters: 5C discharge rate, 50 A charger current limit, 20% cutoff SOC, 3 s charge-loop interval.

A representative run completed in ≈3 minutes (≈2.5 min charge, ≈57 s discharge), with the operative discharge current always clamped to the minimum of the requested rate, the charger's hardware limit, and the vehicle's battery limit — meaning a test request can never fail to negotiate; it simply runs at the best rate all three sides agree on.

---

## Session Flow

```
EVCC (Vehicle)                                    SECC (Charger)
──────────────────────────────────────────────────────────────────────
SDP Request (UDP multicast)            →
                                        ←        SDP Response (UDP)
TCP connect + TLS 1.3 handshake        ⇄        (certificate exchange, PKI validation)
SupportedAppProtocolReq                →
                                        ←        SupportedAppProtocolRes
SessionSetupReq                        →
                                        ←        SessionSetupRes
AuthorizationSetupReq                  →
                                        ←        AuthorizationSetupRes
AuthorizationReq                       →
                                        ←        AuthorizationRes
ServiceDiscoveryReq                    →
                                        ←        ServiceDiscoveryRes
                                                  (Energy: DC=2, DC_BPT=6; VAS: diagnostic test IDs)
ServiceDetailReq (per service)         →
                                        ←        ServiceDetailRes (parameter sets)
ServiceSelectionReq                    →
                                        ←        ServiceSelectionRes
DC_ChargeParameterDiscoveryReq         →
                                        ←        DC_ChargeParameterDiscoveryRes
ScheduleExchangeReq                    →
                                        ←        ScheduleExchangeRes
PowerDeliveryReq                       →
                                        ←        PowerDeliveryRes
CableCheckReq / PreChargeReq           →
                                        ←        CableCheckRes / PreChargeRes
DC_ChargeLoopReq (repeated)            →        ← DC_ChargeLoopRes
   carries: V, I, SOC                              commands: target I, V for next cycle
PowerDeliveryReq (stop)                →
                                        ←        PowerDeliveryRes
SessionStopReq                         →
                                        ←        SessionStopRes
TCP connection closed
```

**Who controls what:**
- **SECC** advertises available energy services and VAS diagnostic tests, declares its own hardware limits, and commands the next current/voltage target each charge-loop cycle during an active diagnostic test.
- **EVCC** selects which energy service and VAS to use, declares its own battery limits, and reports actual current/voltage each cycle — always clamped within its own limits regardless of what the SECC requests.
- Neither side can force the other beyond its declared limits — the operative value for any negotiated quantity is always the minimum of both sides' declared capability.

---

## How to Run

See [`Get_it_running`](./Get_it_running) for full setup instructions.

Summary:
1. Provision PKI certificates (base library tooling under `iso15118_core/iso15118/shared/pki/`).
2. Configure `config/` with the desired protocol, security mode, and energy service.
3. Start `SECC_Master` on the charger-side Raspberry Pi.
4. Start `EVCC_Client` on the vehicle-side Raspberry Pi.
5. To run the diagnostic test instead of a normal charge session, set `diagnosticServiceId` in the EVCC config JSON (e.g. `101` for the discharge capacity test, `0` for normal charging).
6. Session logs are written to `logs/`; the diagnostic telemetry report is written to `health_telemetry.json` in the working directory at session end.

---

## Roadmap

- [ ] Implement `EISService` (VAS id 102) — swept-frequency current stimulus via the charge loop, complex impedance computed from the voltage response (Team 2)
- [ ] Implement `HPPCService` (VAS id 103) — timed pulse-discharge / rest / pulse-charge sequence, DC internal resistance from relaxation curves (Team 3)
- [ ] Incremental Capacity Analysis service — slow C/20 constant-current charge with dQ/dV computation
- [ ] Replace simulated battery physics with live BMS data once battery hardware is available
- [ ] Integrate EIS signal-generation hardware once available — connects at the existing `CurrentCommand` interface
- [ ] OCPP backend integration for forwarding diagnostic reports
- [ ] Automated multi-test reporting dashboard ("Battery Health Certificate")

---

## Project Team

Four-team student project, SS2026, THI Ingolstadt:

| Team | Focus |
|---|---|
| Team 1 | Grid-Forming (GFM) frequency regulation |
| Team 2 | Square-wave EIS measurement system |
| Team 3 | Charging station as advanced EV tester (HPPC, ICA, dashboard) |
| **This repository** | ISO 15118-20 communication layer, security, diagnostic service framework |

---

## References

- ISO 15118-20:2022 — Road vehicles — Vehicle to grid communication interface — Part 20
- ISO 15118-3 — Physical and data link layer requirements
- [EcoG-io/iso15118](https://github.com/EcoG-io/iso15118) — base protocol implementation
- devolo dLAN Green PHY / Qualcomm QCA7000 chipset documentation

---

## License

`[License to be added]`