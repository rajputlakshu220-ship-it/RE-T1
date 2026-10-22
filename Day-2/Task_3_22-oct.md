# L03: UAV Module Interface Specification & Data Contract Control Document

**Task Order**: TASK ORDER 3  
**Assigned Engineer**: Lakshya Thakur (`TRAIN-004`)  
**Assigned Role**: Systems Integration Engineer — UAV Training Assignment  
**Task Period**: 22–27 October 2026  
**Assigned Date**: 23 October 2026 (Day 2 — Interface Contracts)  
**Deliverable ID**: `L03_Module_Interface_Specification.md`  
**Classification**: Engineering Interface Control Document (ICD) / Technical Specification  
**System Target**: RE-T1 (SPECTRA) UAV Software Integration Framework (Modules `M01` through `M07`)  
**Parent Architecture**: [L01\_System\_Module\_Map.md](https://www.google.com/search?q=L01_System_Module_Map.md) & [L02\_Software\_Integration\_Block\_Diagram.pdf](https://www.google.com/search?q=L02_Software_Integration_Block_Diagram.pdf)

---

## 1. Scope, Purpose & Architectural Framework

### 1.1 Scope and Objective
This document defines the formal, binding interface contracts governing inter-module communication across all seven principal software modules (`M01`–`M07`) within the Unmanned Aerial Vehicle (UAV) software integration framework. These specifications formalize:
1. **Input and Output Parameters**: Explicit definitions of wire payloads, shared-memory data structures, and command messages.
2. **Data Types and Serialization**: Precise bit widths, endianness, signedness, array bounds, and structural alignments.
3. **Physical Engineering Units and Coordinate Frames**: Explicit units of measurement, reference frames (WGS84, NED, Body), and resolution scales.
4. **Protocol Framing and Envelopes**: Synchronization markers, sequence numbers, message identifiers, correlation tokens, and CRC verification.
5. **Error Conditions and Failsafe Semantics**: Rigorous exception codes, detection thresholds, fault escalation hierarchies, and autonomous vehicle safety fallbacks.

### 1.2 System Architecture and Interface Matrix Overview
The integration framework separates concerns across four distinct planes, mediated by interfaces `IF-01` through `IF-07`:

| Interface ID | Interface Name | Source Module | Target Module(s) | Operational Pattern | Primary Transport | Nominal Frequency | Latency Budget (Max) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IF-01** | Telemetry & Schema Distribution | `M01 (ICR)` | `M03`, `M04`, `M05`, `M07` | Synchronous Request-Reply / Static Cache | Local IPC / Shared Memory | On Startup & Dialect Change (1 Hz probe) | $\le 1.0\text{ ms}$ |
| **IF-02** | Flight Readiness & Pre-Arm Gate | `M02 (DSC)` | `M04`, `M05`, `M06`, `M07` | Periodic Health Beacon & State Query | Non-blocking Ring Buffer / MAVLink | 1 Hz Beacon / Event Latch | $\le 10.0\text{ ms}$ |
| **IF-03** | Synthetic Flight & Sensor Stream | `M03 (SDG)` | `M04 (IAG)` | High-Rate Asynchronous Streaming | UDP Socket / Lockless SPSC FIFO | 200 Hz (IMU), 50 Hz (Baro), 10 Hz (GPS) | $\le 2.0\text{ ms}$ |
| **IF-04** | Validated Canonical Flight Frame | `M04 (IAG)` | `M05 (CPE)` | Zero-Copy Event Dispatch | Lockless Circular FIFO / Shared Memory | 200 Hz Event-Driven Stream | $\le 0.5\text{ ms}$ |
| **IF-05** | GNC State, Actuator & ACK Stream | `M05 (CPE)` | `M06 (PSA)` | Synchronous State Dispatch | Fast Ring Buffer / POSIX Queue | 100 Hz (State), 50 Hz (Actuator) | $\le 1.5\text{ ms}$ |
| **IF-06** | Telemetry Audit & Flight Trace | `M04`, `M05`, `M06` | `M07 (IVR)` | Buffered Structured Trace Stream | Shared Memory / SQLite WAL Journal | 50 Hz Audit Snapshot / Event Stream | $\le 5.0\text{ ms}$ |
| **IF-07** | SITL Orchestration & Reset Command | `M07 (IVR)` | `M02 (DSC)`, `M03 (SDG)` | Synchronous Control & Command Dispatch | Control RPC / Function Call | Scenario-driven (Pre/Post Test Run) | $\le 50.0\text{ ms}$ |

---

## 2. Common Data Standards, Coordinate Conventions & Protocol Envelope

### 2.1 Endianness, Alignment and Packing
- **Byte Order**: Strict Little-Endian (`<`, LSB first) across all binary serialized messages and wire protocols, conforming to [MAVLink v2 specification](https://mavlink.io/en/guide/serialization.html) and ARM Cortex-M7 / x86_64 native execution.
- **Data Structure Packing**: All wire structures are strictly packed with zero internal padding (`__attribute__((packed))` or Python `struct.pack('=...')`).
- **Memory Alignment**: In-memory ring buffer representations enforce 4-byte or 8-byte natural alignment for high-speed DMA and lockless single-producer single-consumer (SPSC) pointer swaps.

### 2.2 Global Coordinate Systems and Physical Units
All sensor, state estimation, and navigation telemetry conforms strictly to the following reference frames:
- **Geodetic Coordinates**: WGS84 ellipsoid. Latitude and longitude are represented as signed 32-bit integers scaled by $10^7$ (`degE7`), where $1\text{ unit} = 10^{-7}\text{ degrees} \approx 1.11\text{ cm}$ resolution.
- **Altitude**: Expressed as signed 32-bit integer millimeters (`mm`) above Mean Sea Level (MSL) or Above Ground Level (AGL) / Relative to Home.
- **Linear Translation**: North-East-Down (NED) local tangent plane. Displacements in meters (`m`, `float32`), velocities in meters per second (`m/s`, `float32`), and linear accelerations in meters per second squared (`m/s²`, `float32`).
- **Angular Orientation**: Body-fixed frame (X-Forward, Y-Right, Z-Down). Tait-Bryan intrinsic Euler angles ($Z-Y'-X''$) for Roll ($\phi$), Pitch ($	heta$), and Yaw ($\psi$) expressed in radians (`rad`, `float32`) with canonical range $-\pi \le \phi, \psi \le \pi$ and $-\pi/2 \le \theta \le \pi/2$. Angular velocities expressed in body rates ($p, q, r$) in radians per second (`rad/s`, `float32`).
- **Electrical Metrics**: Bus voltage in millivolts (`mV`, `uint16_t`), current draw in centiamperes (`cA`, `int16_t` where $1\text{ cA} = 10\text{ mA}$), remaining battery energy in percentage points (`%`, `uint8_t`, range $0\text{--}100$).

### 2.3 Universal Telemetry Envelope (MAVLink v2 Extended Wire Header)
All binary packets traversing external transport links (`IF-03`, `IF-04`, `IF-06`) encapsulate payloads within the standardized 14-byte extended frame envelope:

```
+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
| 0xFD   | LEN    | INC_FL | CMP_FL | SEQ    | SYS_ID | CMP_ID | MSG_ID (3 Bytes)         |
+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
| <--  Payload Data (0 - 255 Bytes)  -->     | CRC-16 (2B)     | OPT: Signature (13B)    |
+--------------------------------------------+-----------------+-------------------------+
```

| Field Name | Wire Type | Byte Offset | Range / Valid Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `magic_byte` | `uint8_t` | 0 | `0xFD` (Fixed) | MAVLink v2 protocol start-of-frame synchronization marker. |
| `payload_len` | `uint8_t` | 1 | $0\text{--}255$ | Length of message payload data in bytes. |
| `incompat_flags` | `uint8_t` | 2 | `0x00` or `0x01` | Flags that require parser rejection if unsupported (bit 0 = signature present). |
| `compat_flags` | `uint8_t` | 3 | `0x00` | Flags that can be safely ignored if unrecognized. |
| `packet_seq` | `uint8_t` | 4 | $0\text{--}255$ | Monotonically incrementing rolling sequence counter for frame loss tracking. |
| `sys_id` | `uint8_t` | 5 | $1\text{--}255$ | System ID of sending node (1 = Primary Flight Controller, 255 = GCS). |
| `comp_id` | `uint8_t` | 6 | $1\text{--}255$ | Component ID (1 = Autopilot GNC, 100 = Camera Payload, 200 = SITL Engine). |
| `msg_id` | `uint24_t` | 7..9 | $0\text{--}16,777,215$ | 24-bit Message Identifier (e.g., 0 = HEARTBEAT, 30 = ATTITUDE, 33 = GLOBAL_POS). |
| `payload` | `uint8_t[N]` | 10..(10+N-1) | Dynamic | Message-specific payload serialized according to schema definition. |
| `checksum` | `uint16_t` | (10+N)..(11+N)| `0x0000`--`0xFFFF` | ITU-T CRC-16-CCITT polynomial ($x^{16} + x^{12} + x^5 + 1$, seed `0xFFFF`, CRC-EXTRA byte). |

### 2.4 Traceability and Correlation Metadata
Every data exchange between modules attaches an end-to-end lineage header:
- `x_correlation_id`: 64-bit unsigned integer (`uint64_t`) uniquely identifying the flight mission run or SITL execution session.
- `x_schema_version`: 24-bit packed unsigned integer representing SemVer (`uint8_t major`, `uint8_t minor`, `uint8_t patch`).
- `timestamp_us`: 64-bit unsigned integer (`uint64_t`) representing microseconds since Unix Epoch (`1970-01-01T00:00:00Z`).
- `time_boot_ms`: 32-bit unsigned integer (`uint32_t`) representing milliseconds since Flight Controller boot.

---

## 3. Detailed Interface Specifications

### 3.1 Interface IF-01: UAV Telemetry & Sensor Schema Distribution
- **Source**: `M01 (ICR)` — UAV Interface & Telemetry Schema Registry
- **Destination**: `M03 (SDG)`, `M04 (IAG)`, `M05 (CPE)`, `M07 (IVR)`
- **Pattern**: Synchronous In-Memory Registry Lookup / Dialect Version Manifest Query
- **Latency Budget**: $\le 1.0\text{ ms}$ (served from pre-compiled in-memory hash tables)
- **Bandwidth**: Static initialization ($pprox 64\text{ KB}$ catalog), subsequent 1 Hz polling queries ($pprox 128\text{ B/s}$).

#### 3.1.1 Interface Purpose and Data Exchange
Provides authoritative, single-source-of-truth MAVLink dialect manifests, message descriptors, CRC-EXTRA seeds, physical unit ranges, and serialization schemas. Ensures that no module ingests or deserializes data without verified schema hash synchronization.

#### 3.1.2 Input Parameters (Request Message: `SchemaLookupRequest`)
| Parameter Name | Data Type | Units | Valid Domain | Description |
| :--- | :--- | :--- | :--- | :--- |
| `client_module_id` | `uint16_t` | Enum | `0x01` (`M01`) to `0x07` (`M07`) | Identifier of requesting client module. |
| `target_msg_id` | `uint32_t` | ID | `0`--`16777215` (`0xFFFFFFFF` for all) | Specific MAVLink message ID requested, or wildcard. |
| `expected_dialect_crc` | `uint32_t` | Hex Hash | 32-bit CRC32 checksum | Expected CRC32 hash of the active dialect XML definition. |

#### 3.1.3 Output Parameters (Response Message: `SchemaDescriptorResponse`)
| Parameter Name | Data Type | Units | Valid Domain | Description |
| :--- | :--- | :--- | :--- | :--- |
| `status_code` | `uint16_t` | Code | `0x0000` (OK), `0xE101`--`0xE104` | Operation status code. |
| `dialect_version` | `uint32_t` | SemVer | `0x010200` (`v1.2.0`) | Active dialect release version. |
| `schema_hash` | `uint32_t` | Hex Hash | 32-bit CRC32 | Computed SHA256/CRC32 digest of message definitions. |
| `field_count` | `uint8_t` | Count | $1\text{--}64$ | Number of fields defined within the message schema. |
| `crc_extra_seed` | `uint8_t` | Byte | $0\text{--}255$ | MAVLink CRC-EXTRA byte required for wire integrity check. |
| `min_packet_len` | `uint16_t` | Bytes | $14\text{--}279$ | Minimum allowable wire size (header + min payload + CRC). |
| `max_packet_len` | `uint16_t` | Bytes | $14\text{--}279$ | Maximum allowable wire size including zero-truncation. |
| `field_descriptors` | `FieldDef[]` | Struct Array | Array of FieldDef | Array of field specifications (name, offset, type, units, bounds). |

#### 3.1.4 Error Conditions and Handling
| Error Code | Symbolic Name | Triggering Condition | Detection Point | Failsafe / Recovery Action |
| :--- | :--- | :--- | :--- | :--- |
| `0xE101` | `ERR_SCHEMA_NOT_FOUND` | `target_msg_id` does not exist in registry. | `M01` Lookup Handler | Returns error code; calling module drops packet and flags unrecognized message. |
| `0xE102` | `ERR_DIALECT_MISMATCH` | `expected_dialect_crc` != internal registry CRC. | `M01` Version Gate | Pre-arm interlock asserted; module initialization blocked until dialect reloaded. |
| `0xE103` | `ERR_SCHEMA_CORRUPT` | Internal schema JSON/XML failed schema validator. | `M01` Storage Loader | `M01` reverts to factory fallback dialect; raises `CRITICAL` log event. |
| `0xE104` | `ERR_REGISTRY_LOCK_TIMEOUT` | Registry read lock timeout $> 1.0\text{ ms}$. | Client Mutex Hook | Client aborts query; uses cached descriptor if within 10-second TTL. |

---

### 3.2 Interface IF-02: Flight Readiness & Pre-Arm Coordination
- **Source**: `M02 (DSC)` — Flight Readiness & Dependency Coordinator
- **Destination**: `M04 (IAG)`, `M05 (CPE)`, `M06 (PSA)`, `M07 (IVR)`
- **Pattern**: Periodic 1 Hz Telemetry Beacon & Synchronous State Query
- **Latency Budget**: $\le 10.0\text{ ms}$
- **Bandwidth**: $1\text{ Hz} \times 64\text{ B} = 64\text{ B/s}$ per channel.

#### 3.2.1 Interface Purpose and Data Exchange
Enforces the topological startup sequence (Tiers 0 through 3). Continuously broadcasts subsystem health flags, sensor calibration state, and arming permission gates. Pre-arm checks prevent throttle activation if any critical sensor (IMU, Baro, GPS, Compass) is degraded or uncalibrated.

#### 3.2.2 Input Parameters (Inbound Health Ingestion from Subsystems)
| Parameter Name | Data Type | Units | Valid Domain | Description |
| :--- | :--- | :--- | :--- | :--- |
| `subsystem_id` | `uint8_t` | Enum | `0x01`--`0x08` | Identifier of reporting subsystem (Sensors, EKF, Comms, Power). |
| `heartbeat_timestamp` | `uint64_t` | $\mu\text{s}$ | Monotonic $>0$ | Subsystem local hardware timestamp. |
| `sensor_health_mask` | `uint32_t` | Bitfield | Bitmask | Bit 0: Gyro, Bit 1: Accel, Bit 2: Mag, Bit 3: Baro, Bit 4: GPS. |
| `calibration_flags` | `uint16_t` | Bitfield | Bitmask | Bit 0: Accel Cal, Bit 1: Compass Cal, Bit 2: Level Cal. |
| `error_counter` | `uint16_t` | Count | $0\text{--}65535$ | Running tally of internal subsystem soft faults. |

#### 3.2.3 Output Parameters (Broadcast Readiness Beacon: `PreArmReadinessPacket`)
| Parameter Name | Data Type | Units | Valid Domain | Description |
| :--- | :--- | :--- | :--- | :--- |
| `time_boot_ms` | `uint32_t` | $\text{ms}$ | $>0$ | Autopilot uptime in milliseconds. |
| `readiness_state` | `uint8_t` | Enum | `0` (INIT), `1` (READY), `2` (ARMED), `3` (FAULT) | Master flight readiness state. |
| `prearm_status_flags`| `uint32_t` | Bitfield | Bitmask | Master pre-arm status (all bits set = 100% armable). |
| `active_tier_level` | `uint8_t` | Tier | $0\text{--}3$ | Highest successfully initialized topological dependency tier. |
| `arm_blocking_reason`| `uint16_t` | Enum | `0x0000` (None), `0xE201`--`0xE206` | Explicit code identifying why arming is disallowed. |
| `battery_health_pct` | `uint8_t` | $\%$ | $0\text{--}100$ | Lowest verified battery state among attached packs. |
| `active_failsafe_mode`| `uint8_t` | Enum | `0` (None), `1` (RTL), `2` (Land), `3` (Loiter) | Currently asserted failsafe fallback mode. |

#### 3.2.4 Error Conditions and Handling
| Error Code | Symbolic Name | Triggering Condition | Detection Point | Failsafe / Recovery Action |
| :--- | :--- | :--- | :--- | :--- |
| `0xE201` | `ERR_PREARM_SENSOR_DEGRADED`| Required sensor uncalibrated or health bit == 0. | `M02` Pre-Arm Poller | Locks vehicle in `DISARMED` state; emits GCS pre-arm error banner. |
| `0xE202` | `ERR_HEARTBEAT_TIMEOUT` | Subsystem heartbeat missing $> 3.0\text{ s}$. | `M02` Watchdog Loop | Asserts subsystem fault; initiates `RTL_FALLBACK` if armed. |
| `0xE203` | `ERR_TOPOLOGY_VIOLATION` | Tier 2 module started prior to Tier 1 readiness. | `M02` Startup Gate | Kills misordered process; triggers full sandbox initialization rollback. |
| `0xE204` | `ERR_CRITICAL_BATTERY_LOW` | Battery voltage $< 10.5\text{ V}$ or capacity $< 15\%$. | `M02` Power Monitor | Triggers automated `LAND_IMMEDIATELY` or blocks motor spool-up. |

---

### 3.3 Interface IF-03: Synthetic Flight & Sensor Data Stream
- **Source**: `M03 (SDG)` — Synthetic Flight & Sensor Data Generator
- **Destination**: `M04 (IAG)` — Telemetry Ingestion & MAVLink Gateway
- **Pattern**: High-Rate Asynchronous Streaming over UDP or Lockless SPSC FIFO
- **Latency Budget**: $\le 2.0\text{ ms}$
- **Bandwidth**: $200\text{ Hz (IMU)} \times 40\text{ B} + 50\text{ Hz (Baro)} \times 28\text{ B} + 10\text{ Hz (GPS)} \times 60\text{ B} \approx 10.0\text{ KB/s}$.

#### 3.3.1 Interface Purpose and Data Exchange
Injects deterministic, seeded synthetic sensor streams (IMU accelerometers/gyros, GNSS ephemeris/fix, Barometer pressure/temperature, Magnetometer flux) and pilot/GCS mission commands into the ingress gateway. Supports nominal, boundary, and negative fault injection profiles (e.g., bit flips, packet truncation, GPS loss).

#### 3.3.2 Message Payloads

##### A. Synthetic IMU Frame (`RAW_IMU` / `SCALED_IMU`) — 200 Hz
| Field Name | Data Type | Units | Resolution / Scale | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `time_usec` | `uint64_t` | $\mu\text{s}$ | $1\,\mu\text{s}$ | $>0$ | Timestamp (Unix Epoch or SITL elapsed). |
| `xacc` | `int16_t` | $\text{m/s}^2$ | $1\,\text{mG} = 9.80665\times 10^{-3}\,\text{m/s}^2$| $-16000\text{--}+16000$ | X-axis linear acceleration (Forward). |
| `yacc` | `int16_t` | $\text{m/s}^2$ | $1\,\text{mG}$ | $-16000\text{--}+16000$ | Y-axis linear acceleration (Right). |
| `zacc` | `int16_t` | $\text{m/s}^2$ | $1\,\text{mG}$ | $-16000\text{--}+16000$ | Z-axis linear acceleration (Down). |
| `xgyro` | `int16_t` | $\text{rad/s}$ | $1\,\text{mrad/s} = 10^{-3}\,\text{rad/s}$ | $-35000\text{--}+35000$ | Angular roll rate around X axis. |
| `ygyro` | `int16_t` | $\text{rad/s}$ | $1\,\text{mrad/s}$ | $-35000\text{--}+35000$ | Angular pitch rate around Y axis. |
| `zgyro` | `int16_t` | $\text{rad/s}$ | $1\,\text{mrad/s}$ | $-35000\text{--}+35000$ | Angular yaw rate around Z axis. |
| `xmag` | `int16_t` | $\text{Gauss}$ | $1\,\text{mGauss} = 10^{-7}\,\text{Tesla}$ | $-4000\text{--}+4000$ | X-axis magnetic field strength. |
| `ymag` | `int16_t` | $\text{Gauss}$ | $1\,\text{mGauss}$ | $-4000\text{--}+4000$ | Y-axis magnetic field strength. |
| `zmag` | `int16_t` | $\text{Gauss}$ | $1\,\text{mGauss}$ | $-4000\text{--}+4000$ | Z-axis magnetic field strength. |

##### B. Synthetic GNSS Frame (`GPS_RAW_INT`) — 10 Hz
| Field Name | Data Type | Units | Resolution / Scale | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `time_usec` | `uint64_t` | $\mu\text{s}$ | $1\,\mu\text{s}$ | $>0$ | GNSS receiver time tag. |
| `fix_type` | `uint8_t` | Enum | $1 = \text{No Fix}$ | $0\text{--}6$ (3 = 3D Fix, 4 = DGPS, 5 = RTK) | GNSS satellite fix quality. |
| `lat` | `int32_t` | $\text{deg}$ | $10^{-7}\,\text{deg}$ (`degE7`) | $-900,000,000\text{--}+900,000,000$ | WGS84 Latitude. |
| `lon` | `int32_t` | $\text{deg}$ | $10^{-7}\,\text{deg}$ (`degE7`) | $-1,800,000,000\text{--}+1,800,000,000$ | WGS84 Longitude. |
| `alt` | `int32_t` | $\text{m}$ | $1\,\text{mm} = 10^{-3}\,\text{m}$ | $-500,000\text{--}+50,000,000$ | Altitude above MSL. |
| `eph` | `uint16_t` | $\text{m}$ | $1\,\text{cm} = 10^{-2}\,\text{m}$ | $0\text{--}65535$ | GPS HDOP horizontal dilution of precision. |
| `epv` | `uint16_t` | $\text{m}$ | $1\,\text{cm}$ | $0\text{--}65535$ | GPS VDOP vertical dilution of precision. |
| `vel` | `uint16_t` | $\text{m/s}$ | $1\,\text{cm/s} = 10^{-2}\,\text{m/s}$ | $0\text{--}10000$ | GPS ground speed. |
| `cog` | `uint16_t` | $\text{deg}$ | $10^{-2}\,\text{deg}$ (`cdeg`) | $0\text{--}35999$ | Course over ground. |
| `satellites_visible`| `uint8_t` | Count | Integer | $0\text{--}32$ | Number of tracked SVs. |

##### C. Synthetic Barometer Frame (`SCALED_PRESSURE`) — 50 Hz
| Field Name | Data Type | Units | Resolution / Scale | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `time_boot_ms` | `uint32_t` | $\text{ms}$ | $1\,\text{ms}$ | $>0$ | Autopilot uptime. |
| `press_abs` | `float32` | $\text{hPa}$ | $0.01\,\text{hPa}$ | $300.0\text{--}1200.0$ | Static atmospheric barometric pressure. |
| `press_diff` | `float32` | $\text{hPa}$ | $0.01\,\text{hPa}$ | $-50.0\text{--}+50.0$ | Dynamic pitot-static differential pressure. |
| `temperature` | `int16_t` | $^\circ\text{C}$ | $0.01\,^\circ\text{C}$ (`cdegC`) | $-4000\text{--}+8500$ | Barometer internal die temperature. |

#### 3.3.3 Error Conditions and Handling
| Error Code | Symbolic Name | Triggering Condition | Detection Point | Failsafe / Recovery Action |
| :--- | :--- | :--- | :--- | :--- |
| `0xE301` | `ERR_SIM_TIME_REVERSAL` | Synthetic `time_usec` decreases monotonically. | `M04` Ingress Sieve | Frame discarded; `M04` asserts time warp error; logs incident to `IF-06`. |
| `0xE302` | `ERR_BURST_NOISE_TRIPPED` | BER noise exceeds physical receiver threshold. | `M04` Ingress Gateway | Frame drops incremented; if $>5$ sequential frames fail, transition to `FAIL_SAFE_STORAGE_STATE`. |
| `0xE303` | `ERR_GPS_GLITCH_INJECTED` | Synthetic GPS HDOP $> 5.0\text{ m}$ or SV count $< 4$. | `M05` EKF Estimator | EKF rejects GPS; falls back to dead-reckoning IMU/optical flow; mode reverts to `ALT_HOLD`. |
| `0xE304` | `ERR_FIFO_OVERFLOW` | SPSC queue write index overwrites read index. | `M03` FIFO Driver | Overflow flag latched; oldest unread packet dropped; increments `lost_frame_cnt`. |

---

### 3.4 Interface IF-04: Validated Canonical Flight Frame
- **Source**: `M04 (IAG)` — Telemetry Ingestion & MAVLink Gateway
- **Destination**: `M05 (CPE)` — GNC & Mission Processing Engine
- **Pattern**: Validated Zero-Copy Event Dispatch via In-Memory SPSC Circular FIFO
- **Latency Budget**: $\le 0.5\text{ ms}$ (strict deterministic hard real-time)
- **Bandwidth**: 200 Hz normalized sensor bursts ($pprox 16.0\text{ KB/s}$).

#### 3.4.1 Interface Purpose and Data Exchange
The boundary between untrusted physical/synthetic transport and core GNC execution. `M04` validates MAVLink v2 CRC-16, checks sequence counter continuity, verifies payload boundaries against `M01` schemas, strips wire framing headers, and emits normalized canonical C-structures into `M05`. Corrupted frames are rejected and never reach the flight guidance loop.

#### 3.4.2 Inbound Payload Verification Sieve
1. **Magic Byte Assertion**: Asserts `magic_byte == 0xFD`.
2. **Framing Length Assertion**: Asserts `abs(expected_wire_len - actual_received_len) == 0`.
3. **CRC-16-CCITT Verification**: Computes running polynomial over bytes $1..N$, seeds with `crc_extra_seed` from `M01`. Asserts calculated CRC matches wire CRC.
4. **Physical Sanity Clamping**: Clamps sensor inputs to valid aerodynamic envelope (e.g. Accel $\le 16\text{G}$, Roll Rate $\le 600^\circ/\text{s}$).

#### 3.4.3 Normalized Canonical Flight Structure (`CanonicalFlightSample`)
| Field Name | Wire / Mem Type | Physical Units | Precision | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sample_id` | `uint64_t` | ID | Monotonic | $1\text{--}2^{64}-1$ | Monotonically incremented canonical sequence token. |
| `timestamp_utc_us` | `uint64_t` | $\mu\text{s}$ | $1\,\mu\text{s}$ | Real-time UTC | Synchronized Unix epoch timestamp. |
| `accel_ned_m_s2[3]`| `float32[3]` | $\text{m/s}^2$ | $10^{-4}$ | $-150.0\text{--}+150.0$ | Tri-axial body accelerations $[a_x, a_y, a_z]$. |
| `gyro_body_rad_s[3]`| `float32[3]` | $\text{rad/s}$ | $10^{-5}$ | $-10.5\text{--}+10.5$ | Tri-axial body angular rates $[p, q, r]$. |
| `mag_gauss[3]` | `float32[3]` | $\text{Gauss}$ | $10^{-4}$ | $-4.0\text{--}+4.0$ | Calibrated body magnetic vector $[m_x, m_y, m_z]$. |
| `static_press_pa` | `float32` | $\text{Pa}$ | $0.1\,\text{Pa}$ | $30000.0\text{--}120000.0$ | Absolute static atmospheric pressure. |
| `dynamic_press_pa` | `float32` | $\text{Pa}$ | $0.1\,\text{Pa}$ | $0.0\text{--}5000.0$ | Differential dynamic pitot pressure (airspeed). |
| `pos_wgs84_deg[2]` | `float64[2]` | $\text{deg}$ | $10^{-9}$ | Lat: $[-90, 90]$, Lon: $[-180, 180]$ | High-precision geodetic position $[\text{Lat}, \text{Lon}]$. |
| `alt_msl_m` | `float32` | $\text{m}$ | $10^{-3}$ | $-500.0\text{--}+15000.0$ | Altitude above Mean Sea Level. |
| `ground_speed_m_s` | `float32` | $\text{m/s}$ | $10^{-2}$ | $0.0\text{--}120.0$ | True ground speed magnitude. |
| `gnss_fix_status` | `uint8_t` | Enum | Integer | $0 = \text{None}, 3 = \text{3D}, 5 = \text{RTK}$ | Verified GNSS navigation lock status. |
| `validation_mask` | `uint16_t` | Bitfield | Bitmask | `0xFFFF` = 100% valid | Bitmask indicating which sensor fields passed validation. |

#### 3.4.4 Error Conditions and Handling
| Error Code | Symbolic Name | Triggering Condition | Detection Point | Failsafe / Recovery Action |
| :--- | :--- | :--- | :--- | :--- |
| `0xE401` | `ERR_CRC_CORRUPTION` | Wire CRC-16 does not match calculated polynomial. | `M04` CRC Sieve | Packet quarantined immediately; increments error counter; never routed to `M05`. |
| `0xE402` | `ERR_FRAMING_LEN_MISMATCH`| `abs(expected_len - actual_len) != 0`. | `M04` Frame Parser | Discards corrupted frame; resynchronizes parser on next `0xFD` magic byte. |
| `0xE403` | `ERR_SEQUENCE_GAP_DETECTED`| `actual_seq != (prev_seq + 1) % 256`. | `M04` Sequence Checker| Emits gap warning event via `IF-06`; fills state via EKF prediction step. |
| `0xE404` | `ERR_RANGE_EXCEEDED` | Sensor value falls outside physical bounds. | `M04` Range Checker | Clamps value to bound; drops sample if out-of-bounds $> 3\sigma$; flags sensor anomaly. |

---

### 3.5 Interface IF-05: GNC State, Actuator & ACK Stream
- **Source**: `M05 (CPE)` — GNC & Mission Processing Engine
- **Destination**: `M06 (PSA)` — Flight Data Logger & GCS Adapter
- **Pattern**: Synchronous Dispatch to POSIX Ring Buffer / Thread-Safe Log Queue
- **Latency Budget**: $\le 1.5\text{ ms}$
- **Bandwidth**: 100 Hz State Vector + 50 Hz Actuator Outputs ($pprox 25.0\text{ KB/s}$).

#### 3.5.1 Interface Purpose and Data Exchange
Transfers the estimated vehicle navigation state, active flight mode, guidance setpoints, calculated servo/motor PWM actuator commands, and GCS mission acknowledgments (`COMMAND_ACK`) from the flight computer into the logging and telemetry downlink layer.

#### 3.5.2 Message Payloads

##### A. Navigation State Vector (`ESTIMATED_NAV_STATE`) — 100 Hz
| Field Name | Data Type | Physical Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `time_boot_ms` | `uint32_t` | $\text{ms}$ | $>0$ | Autopilot uptime. |
| `roll_rad` | `float32` | $\text{rad}$ | $-\pi\text{--}+\pi$ | Estimated roll attitude angle. |
| `pitch_rad` | `float32` | $\text{rad}$ | $-\pi/2\text{--}+\pi/2$ | Estimated pitch attitude angle. |
| `yaw_rad` | `float32` | $\text{rad}$ | $-\pi\text{--}+\pi$ | Estimated yaw (heading) angle relative to True North. |
| `vel_ned_m_s[3]` | `float32[3]` | $\text{m/s}$ | $-100.0\text{--}+100.0$ | Linear velocity vector in NED frame $[v_n, v_e, v_d]$. |
| `pos_ned_m[3]` | `float32[3]` | $\text{m}$ | Dynamic | Displacement from origin/home in NED frame $[x, y, z]$. |
| `ekf_status_flags` | `uint16_t` | Bitfield | Bitmask | EKF convergence health flags (pos, vel, hgt, mag). |
| `active_flight_mode`| `uint8_t` | Enum | `0` (MANUAL), `1` (ALT_HOLD), `2` (LOITER), `3` (AUTO), `4` (RTL) | Currently executing flight guidance mode. |

##### B. Actuator Mixing & Servo Outputs (`SERVO_OUTPUT_RAW`) — 50 Hz
| Field Name | Data Type | Physical Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `time_usec` | `uint64_t` | $\mu\text{s}$ | $>0$ | Servo command output generation timestamp. |
| `motor_pwm_us[4]` | `uint16_t[4]` | $\mu\text{s}$ Pulse | $1000\text{--}2000\,\mu\text{s}$ | Motor ESC throttle pulses ($1000 = 0\%, 2000 = 100\%$). |
| `servo_pwm_us[4]` | `uint16_t[4]` | $\mu\text{s}$ Pulse | $1000\text{--}2000\,\mu\text{s}$ | Flight control surfaces (Aileron, Elevator, Rudder, Flaps). |
| `arm_status` | `uint8_t` | Enum | `0` = Disarmed, `1` = Armed | Actuator electrical enable relay status. |

##### C. Command Acknowledgment (`COMMAND_ACK`) — Event Driven
| Field Name | Data Type | Physical Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `command_id` | `uint16_t` | MAV_CMD | $0\text{--}65535$ | ID of acknowledged mission command (e.g. 22 = TAKEOFF). |
| `result_code` | `uint8_t` | Enum | `0` (ACCEPTED), `1` (TEMPORARILY_REJECTED), `2` (DENIED), `3` (FAILED) | Execution result code. |
| `progress_pct` | `uint8_t` | $\%$ | $0\text{--}100$ | Progress percentage for multi-stage actions. |
| `target_system` | `uint8_t` | ID | $1\text{--}255$ | GCS or orchestrator system ID to receive ACK. |

#### 3.5.3 Error Conditions and Handling
| Error Code | Symbolic Name | Triggering Condition | Detection Point | Failsafe / Recovery Action |
| :--- | :--- | :--- | :--- | :--- |
| `0xE501` | `ERR_EKF_DIVERGENCE` | State estimation covariance exceeds innovation bounds.| `M05` GNC Core | Aborts AUTO mission; executes emergency autonomous `LAND` or `LOITER`. |
| `0xE502` | `ERR_ACTUATOR_SATURATION`| Actuator mixer commands $> 2000\,\mu\text{s}$ on all channels.| `M05` Mixer | Prioritizes attitude stability over altitude; clamps demand; alerts GCS. |
| `0xE503` | `ERR_LOGGER_BACKPRESSURE`| Downstream log queue fills $> 90\%$. | `M06` Log Adapter | Decimates high-rate debugging streams; preserves critical state vectors. |
| `0xE504` | `ERR_COMMAND_REJECTED` | Arm or takeoff command received while pre-arm fails.| `M05` Command Exec | Emits `COMMAND_ACK` with `DENIED`; publishes specific blocking reason. |

---

### 3.6 Interface IF-06: Telemetry Audit & Flight Trace Stream
- **Source**: `M04 (IAG)`, `M05 (CPE)`, `M06 (PSA)`
- **Destination**: `M07 (IVR)` — UAV Integration Verification & Check Runner
- **Pattern**: Buffered Structured Trace Stream via Shared Memory and SQLite WAL Journal
- **Latency Budget**: $\le 5.0\text{ ms}$
- **Bandwidth**: 50 Hz aggregated audit telemetry ($pprox 30.0\text{ KB/s}$).

#### 3.6.1 Interface Purpose and Data Exchange
Provides full observability into the UAV software integration framework during SITL test executions. Collects ingress rejection counters from `M04`, state estimation variance and failsafe transitions from `M05`, and committed SQLite WAL storage records from `M06`. Serves as the evidentiary data source for automated verification assertions (`IC-01` through `IC-04`).

#### 3.6.2 Audit Telemetry Record (`FlightAuditRecord`)
| Field Name | Data Type | Physical Units | Precision | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `audit_event_id` | `uint64_t` | ID | Monotonic | $>0$ | Unique sequential audit log key. |
| `correlation_id` | `uint64_t` | ID | Token | $>0$ | Flight check run correlation identifier. |
| `timestamp_us` | `uint64_t` | $\mu\text{s}$ | $1\,\mu\text{s}$ | Real-time UTC | Event emission timestamp. |
| `emitting_module` | `uint16_t` | Enum | `0x04`, `0x05`, `0x06` | Module generating the audit span. |
| `event_category` | `uint8_t` | Enum | `1` (INGRESS), `2` (GNC_MODE), `3` (FAILSAFE), `4` (STORAGE) | Class of integration audit event. |
| `ingress_valid_pkts`| `uint32_t` | Count | Integer | $>0$ | Cumulative tally of verified packets. |
| `ingress_quarantine_pkts`| `uint32_t`| Count | Integer | $\ge 0$ | Cumulative tally of corrupted/dropped frames. |
| `active_flight_mode`| `uint8_t` | Enum | $0\text{--}4$ | Current GNC operating mode. |
| `wal_write_index` | `uint32_t` | Index | Integer | $>0$ | Active SQLite Write-Ahead Log frame sequence. |
| `payload_audit_blob`| `uint8_t[128]`| Binary | Byte Array | Dynamic | Structured event-specific context metadata. |

#### 3.6.3 Error Conditions and Handling
| Error Code | Symbolic Name | Triggering Condition | Detection Point | Failsafe / Recovery Action |
| :--- | :--- | :--- | :--- | :--- |
| `0xE601` | `ERR_AUDIT_STREAM_STALL` | No audit frames received for $> 500\text{ ms}$ during run.| `M07` Verification Sieve| Check run fails assertion `CHECK_TIMEOUT_INCOMPLETE_FLIGHT_TRACE`. |
| `0xE602` | `ERR_STORAGE_CORRUPTION` | SQLite WAL checksum mismatch or index rollback fail.| `M06` Database Engine | Locks flash in `FAIL_SAFE_STORAGE_STATE`; isolates corrupt sector. |
| `0xE603` | `ERR_LINEAGE_GAP` | Missing `correlation_id` on incoming audit frame.| `M07` Lineage Tracer | Flags packet provenance failure; test check marks lineage verification as FAILED. |

---

### 3.7 Interface IF-07: SITL Orchestration & Scenario Command
- **Source**: `M07 (IVR)` — UAV Integration Verification & Check Runner
- **Destination**: `M02 (DSC)` — Dependency Coordinator, `M03 (SDG)` — Synthetic Generator
- **Pattern**: Synchronous Control RPC & Command Dispatch
- **Latency Budget**: $\le 50.0\text{ ms}$ (control orchestration boundary)
- **Bandwidth**: Sporadic / Scenario-driven ($pprox 512\text{ B}$ per test lifecycle event).

#### 3.7.1 Interface Purpose and Data Exchange
Enables automated, unattended execution of repeatable SITL integration test suites. `M07` commands `M02` to reset all simulated flight state, wipe transient sandbox files, and re-initialize EKF origin coordinates. It simultaneously configures `M03` with deterministic PRNG seeds, flight scenario profiles (e.g. nominal mission, GPS loss at Waypoint 3, battery drain fault), and noise parameters.

#### 3.7.2 Command Parameters (`ScenarioOrchestrationCommand`)
| Parameter Name | Data Type | Physical Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `command_token` | `uint32_t` | Token | $>0$ | Unique command sequence identifier. |
| `scenario_id` | `uint16_t` | Scenario ID | `101` (Nominal), `201` (GPS Glitch), `301` (Power Loss) | Target flight test scenario to execute. |
| `action_code` | `uint8_t` | Enum | `1` (RESET_STATE), `2` (LOAD_PROFILE), `3` (START), `4` (ABORT) | Orchestration action request. |
| `prng_seed` | `uint32_t` | Seed Value | Any 32-bit uint (e.g. `12345`, `42`) | Deterministic seed for reproducible noise and trajectory generation. |
| `ber_noise_rate` | `float32` | Probability | $0.0\text{--}0.10$ ($10\%$) | Physical layer bit-error-rate to inject into `IF-03`. |
| `home_lat_degE7` | `int32_t` | $\text{deg}$ | $-900,000,000\text{--}+900,000,000$ | Virtual launch latitude coordinate. |
| `home_lon_degE7` | `int32_t` | $\text{deg}$ | $-1,800,000,000\text{--}+1,800,000,000$ | Virtual launch longitude coordinate. |
| `home_alt_mm` | `int32_t` | $\text{mm}$ | $-500,000\text{--}+10,000,000$ | Virtual launch ground altitude above MSL. |

#### 3.7.3 Response Parameters (`ScenarioOrchestrationResponse`)
| Parameter Name | Data Type | Physical Units | Valid Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `command_token_ack`| `uint32_t`| Token | Matches request | Echo of acknowledged command token. |
| `execution_status` | `uint8_t` | Enum | `0` (SUCCESS), `1` (REJECTED), `2` (BUSY), `3` (FAILED) | Outcome of command execution. |
| `reset_duration_ms`| `uint16_t` | $\text{ms}$ | $0\text{--}5000$ | Time taken to reset sandbox and EKF state. |
| `error_detail` | `uint16_t` | Error Code | `0x0000` (None), `0xE701`--`0xE703` | Error condition details if status != SUCCESS. |

#### 3.7.4 Error Conditions and Handling
| Error Code | Symbolic Name | Triggering Condition | Detection Point | Failsafe / Recovery Action |
| :--- | :--- | :--- | :--- | :--- |
| `0xE701` | `ERR_RESET_FAILED` | Sandbox file cleanup or EKF home reset fails. | `M02` Orchestrator | Aborts test scenario immediately; reports setup failure to check runner. |
| `0xE702` | `ERR_PROFILE_INVALID` | Requested scenario ID or PRNG seed unrecognized. | `M03` Scenario Loader | Rejects command; halts test execution; logs bad parameter to console. |
| `0xE703` | `ERR_STATE_STILL_ARMED`| Reset requested while flight engine state is ARMED. | `M02` Safety Gate | Forces immediate disarm; cuts motor PWM outputs to 1000 µs; executes reset. |

---

## 4. Master Cross-Subsystem Error Dictionary & Failsafe State Machine

### 4.1 Master Error Code Allocation Table
All integration framework error codes adhere to a structured 16-bit hexadecimal hierarchy: `0xEXYY`, where `E` indicates an integration error, `X` denotes the originating interface number (`1` through `7`), and `YY` denotes the specific error condition index.

| Error Code | Symbolic Identifier | Originating Interface | Primary Detecting Subsystem | Severity Level | System-Wide Failsafe / Interlock Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0xE101` | `ERR_SCHEMA_NOT_FOUND` | `IF-01` | `M01 (ICR)` | `MAJOR` | Calling module drops incoming frame; increments unmapped packet count. |
| `0xE102` | `ERR_DIALECT_MISMATCH` | `IF-01` | `M01 (ICR)` | `CRITICAL` | Pre-arm interlock asserted; locks flight controller in `DISARMED` state. |
| `0xE103` | `ERR_SCHEMA_CORRUPT` | `IF-01` | `M01 (ICR)` | `CRITICAL` | Reverts to factory default XML dialect; flags system configuration fault. |
| `0xE104` | `ERR_REGISTRY_LOCK_TIMEOUT` | `IF-01` | Client Mutex | `WARNING` | Client falls back to cached descriptor if within 10-second TTL. |
| `0xE201` | `ERR_PREARM_SENSOR_DEGRADED`| `IF-02` | `M02 (DSC)` | `CRITICAL` | Denies arming authorization; publishes pre-arm failure reason to GCS. |
| `0xE202` | `ERR_HEARTBEAT_TIMEOUT` | `IF-02` | `M02 (DSC)` | `CRITICAL` | Triggers autonomous `RTL_FALLBACK` if armed; flags missing node. |
| `0xE203` | `ERR_TOPOLOGY_VIOLATION` | `IF-02` | `M02 (DSC)` | `CRITICAL` | Blocks subsequent module launch; initiates full state rollback. |
| `0xE204` | `ERR_CRITICAL_BATTERY_LOW` | `IF-02` | `M02 (DSC)` | `CRITICAL` | Triggers immediate autonomous `LAND` failsafe or disarm. |
| `0xE301` | `ERR_SIM_TIME_REVERSAL` | `IF-03` | `M04 (IAG)` | `MAJOR` | Quarantines packet; halts synthetic stream until timestamp restored. |
| `0xE302` | `ERR_BURST_NOISE_TRIPPED` | `IF-03` | `M04 (IAG)` | `CRITICAL` | If $\ge 5$ consecutive corrupt frames, latches `FAIL_SAFE_STORAGE_STATE`. |
| `0xE303` | `ERR_GPS_GLITCH_INJECTED` | `IF-03` | `M05 (CPE)` | `MAJOR` | EKF rejects GPS; reverts flight mode to `ALT_HOLD` dead-reckoning. |
| `0xE304` | `ERR_FIFO_OVERFLOW` | `IF-03` | `M03 (SDG)` | `WARNING` | Overwrites oldest unread frame; increments frame drop telemetry counter. |
| `0xE401` | `ERR_CRC_CORRUPTION` | `IF-04` | `M04 (IAG)` | `MAJOR` | Packet discarded at ingress; quarantine event logged via `IF-06`. |
| `0xE402` | `ERR_FRAMING_LEN_MISMATCH`| `IF-04` | `M04 (IAG)` | `MAJOR` | Drops packet; re-syncs byte parser on subsequent `0xFD` marker. |
| `0xE403` | `ERR_SEQUENCE_GAP_DETECTED`| `IF-04` | `M04 (IAG)` | `WARNING` | Logs gap span; GNC EKF propagates state via inertial dead reckoning. |
| `0xE404` | `ERR_RANGE_EXCEEDED` | `IF-04` | `M04 (IAG)` | `MAJOR` | Clamps sensor value to dynamic envelope; rejects $>3\sigma$ outliers. |
| `0xE501` | `ERR_EKF_DIVERGENCE` | `IF-05` | `M05 (CPE)` | `CRITICAL` | Failsafe transition to autonomous `EMERGENCY_LAND` or parachute release. |
| `0xE502` | `ERR_ACTUATOR_SATURATION`| `IF-05` | `M05 (CPE)` | `WARNING` | Prioritizes attitude stability; clamps servo pulses to $1000\text{--}2000\,\mu\text{s}$. |
| `0xE503` | `ERR_LOGGER_BACKPRESSURE`| `IF-05` | `M06 (PSA)` | `WARNING` | Drops high-rate debugging telemetry; preserves state vectors and ACKs. |
| `0xE504` | `ERR_COMMAND_REJECTED` | `IF-05` | `M05 (CPE)` | `WARNING` | Emits `COMMAND_ACK` with `DENIED` code; vehicle maintains current mode. |
| `0xE601` | `ERR_AUDIT_STREAM_STALL` | `IF-06` | `M07 (IVR)` | `CRITICAL` | SITL check runner terminates test run with assertion timeout failure. |
| `0xE602` | `ERR_STORAGE_CORRUPTION` | `IF-06` | `M06 (PSA)` | `CRITICAL` | Halts flash write index; locks flash in read-only forensic mode. |
| `0xE603` | `ERR_LINEAGE_GAP` | `IF-06` | `M07 (IVR)` | `MAJOR` | Flags test assertion failure due to unverified packet provenance. |
| `0xE701` | `ERR_RESET_FAILED` | `IF-07` | `M07 (IVR)` | `CRITICAL` | Aborts scenario execution immediately; reports test harness fault. |
| `0xE702` | `ERR_PROFILE_INVALID` | `IF-07` | `M03 (SDG)` | `MAJOR` | Rejects orchestration command; logs invalid profile identifier. |
| `0xE703` | `ERR_STATE_STILL_ARMED`| `IF-07` | `M02 (DSC)` | `CRITICAL` | Forces immediate hardware disarm; kills motor throttle; executes reset. |

### 4.2 Failsafe State Machine Transitions
When integration anomalies occur, the framework executes deterministic, rule-based state transitions:

```
[ INIT / BOOT ]
       │
       ▼ (All Tiers Ready & Pre-Arm Passed)
[ DISARMED / READY ] ─────────────(Arm Command)─────────────► [ ARMED / FLIGHT ]
       │                                                             │
       │ (Pre-Arm Fault: 0xE201)                                     │ (EKF Fault: 0xE501 / Battery: 0xE204)
       ▼                                                             ▼
[ PREARM_LOCKED ]                                            [ EMERGENCY_LAND ]
       │                                                             ▲
       │ (5 Consecutive Corrupt Packets: 0xE302)                     │ (Comms Loss > 3s: 0xE202)
       ▼                                                             │
[ FAIL_SAFE_STORAGE_STATE ] ◄─────────────────────────────────[ RTL_FALLBACK ]
```

1. **`PREARM_LOCKED` State**: Entered if `0xE201` (sensor uncalibrated), `0xE102` (dialect mismatch), or `0xE204` (low battery) is detected during pre-flight checks. Completely disables motor arming lines.
2. **`RTL_FALLBACK` State**: Entered if `0xE202` (telemetry/heartbeat loss $> 3.0\text{ s}$) occurs while in airborne flight. The vehicle climbs to clearance altitude ($50\text{ m}$ AGL), navigates autonomously to the recorded home coordinates, and loiters.
3. **`EMERGENCY_LAND` State**: Entered if `0xE501` (EKF attitude divergence) or `0xE204` (critical battery $< 10.5\text{ V}$) occurs. Vehicle initiates controlled vertical descent at $1.5\text{ m/s}$ until ground touchdown is confirmed via barometer/accelerometer impact sensing.
4. **`FAIL_SAFE_STORAGE_STATE` State**: Entered if `0xE302` (burst line noise corruption exceeding 5 consecutive packets) or `0xE602` (flash index corruption) is detected. Immediately suspends all flash write operations, isolates the active write buffer, and transitions storage hardware to read-only mode to preserve forensic flight telemetry.

---

## 5. Verification & Compliance Sign-Off

This interface specification has been reviewed and baseline-locked for the 23 October 2026 Interface Contracts milestone. All module implementations (`M01` through `M07`) must satisfy the data types, physical units, framing bounds, and error handling behaviors defined herein.

- **Author**: Lakshya Thakur, Systems Integration Engineer (`TRAIN-004`)
- **Review Authority**: RudraEdge Aerospace UAV Systems Integration Division
- **Document Status**: APPROVED & LOCKED (Baseline v1.0.0)
- **Cross-Reference**: Checklist verification delivered in companion workbook [L04\_Interface\_Compatibility\_Checklist.xlsx](https://www.google.com/search?q=L04_Interface_Compatibility_Checklist.xlsx).
