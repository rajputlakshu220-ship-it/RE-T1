# L01 - UAV System Software Module Map

## 1. Assignment Dossier

| Field | Details |
|---|---|
| **Author** | Lakshay Thakur |
| **Candidate ID** | TRAIN-004 |
| **Role** | Systems Integration Engineer |
| **Assignment Scope** | UAV Software Integration & Architecture Mapping |
| **Review Window** | 22 October 2026 – 27 October 2026 |
| **Date of Submission** | 22 October 2026 |
| **Lifecycle Phase** | Phase 1: High-Level Architecture & Inter-Module Topology |

---

## 2. Objective & Scope

This document establishes the functional breakdown of the onboard software architecture for our autonomous Unmanned Aerial Vehicle (UAV). 

The goal is three-fold:
1. **Deconstruct** the autonomy stack into modular, loosely-coupled functional blocks.
2. **Standardize** the input/output boundaries and dependency pathways across critical flight subsystems.
3. **Establish an integration baseline** to prevent data serialization bottlenecks, race conditions, and unhandled fault propagation during hardware-in-the-loop (HIL) testing.

---

## 3. High-Level Architectural Overview

The UAV software stack operates on a hybrid event-driven and cyclic architecture. Fast execution loops (attitude estimation and actuator rate control) execute synchronously at high frequencies (200–400 Hz), whereas higher-order tasks like waypoint sequencing, telemetry synchronization, and health diagnostics operate asynchronously at 10–50 Hz.

```
       +-------------------------------------------------------+
       |               Ground Control Station (GCS)            |
       +-------------------------------------------------------+
                                   ^
                                   | RF / LTE Datalink (MAVLink)
                                   v
+-------------------------------------------------------------------------+
| Onboard Software Bus                                                    |
|                                                                         |
|  +------------------+         +----------------+                        |
|  | Sensor Interface | ------> |   Navigation   |                        |
|  |  (IMU, GPS, Baro)|         | (EKF2 / State) |                        |
|  +------------------+         +----------------+                        |
|           |                           |                                 |
|           v                           v                                 |
|  +------------------+         +----------------+      +---------------+ |
|  |  Flight Control  | <------ |   Mission      | <--- | Communication | |
|  | (PID / Rates)    |         |   Management   |      | & Telemetry   | |
|  +------------------+         +----------------+      +---------------+ |
|           |                           |                       |         |
|           +-------------+-------------+-----------------------+         |
|                         |                                               |
|                         v                                               |
|             +-----------------------+      +---------------+            |
|             |   Health Monitoring   | ---> |  Data Logger  |            |
|             |  (Watchdog / Failsafe)|      | (Flash/SDcard)|            |
|             +-----------------------+      +---------------+            |
+-------------------------------------------------------------------------+
```

---

## 4. Principal Software Modules

The table below catalogs our primary onboard software modules, their operating context, and core responsibilities:

| No. | Module Name | Primary Responsibility | Execution Cadence |
|:---:|---|---|:---:|
| **01** | **Flight Control (FC)** | Computes attitude/position error vectors and translates guidance setpoints into actuator motor mixer signals (PWM/DShot). | Hard Real-Time (250–400 Hz) |
| **02** | **Sensor Interface (SI)** | Interfaces with physical buses (SPI, I2C, UART, CAN), handles device calibration matrices, and filters raw sensor data. | Real-Time (100–1000 Hz) |
| **03** | **Navigation & Estimation (NAV)** | Fuses multi-source sensor inputs (IMU, GNSS, barometer, optical flow) using Extended Kalman Filtering (EKF) to produce a 15-DOF state estimate. | Real-Time (100–250 Hz) |
| **04** | **Mission Management (MM)** | Controls autonomous flight modes, interprets geofencing constraints, manages waypoint state machines, and executes fail-safe procedures. | Cyclic (20–50 Hz) |
| **05** | **Communication & Telemetry (COMS)** | Encapsulates bidirectional datalinks, parses incoming GCS command frames, and schedules prioritized downlink packets. | Async / Cyclic (20–50 Hz) |
| **06** | **Health & Diagnostics (SYS_MON)** | Tracks subsystem heartbeats, detects thermal/voltage anomalies, monitors bus latency, and flags system degraded modes. | Cyclic (10–20 Hz) |
| **07** | **Data Logging & Blackbox (LOG)** | Writes flight telemetry, estimator innovations, fault flags, and raw IMU dumps to high-speed NV-storage (microSD/eMMC). | Background Buffered (50–200 Hz) |
| **08** | **GCS Interface Bridge (GCS_IF)** | Decouples modem hardware drivers from high-level MAVLink/custom telemetry serialization protocols. | Event-Driven (On Packet Rx/Tx) |

---

## 5. Detailed Module Interface Specifications

### 5.1 Flight Control (`fc_core`)
* **Data Ingest:** Estimated state vector $(\mathbf{p}, \mathbf{v}, \mathbf{q}, \boldsymbol{\omega})$, desired setpoints from Mission Management, RC override channels.
* **Data Egress:** Actuator mixing commands (ESC motor speeds, control surface deflection angles), inner-loop status.
* **Core Dependencies:** Low-latency IPC from `nav_estimator`, hardware timer peripherals.

### 5.2 Sensor Interface (`sensor_hal`)
* **Data Ingest:** Raw register reads across SPI/I2C/CAN buses (Accelerometers, Gyroscopes, Magnetometer, Barometric Pressure, GNSS NMEA/UBX frames).
* **Data Egress:** Calibrated SI units (temperature-compensated accelerations in $\text{m/s}^2$, angular rates in $\text{rad/s}$, static atmospheric pressure in $\text{Pa}$).
* **Core Dependencies:** Microcontroller HAL/BSP, DMA channels, interrupt service routines.

### 5.3 Navigation & Estimation (`nav_estimator`)
* **Data Ingest:** Synchronized IMU deltas, GNSS PVT (Position, Velocity, Time) solutions, barometric altitude, magnetometer heading.
* **Data Egress:** Local NED position, body-frame ground speed, attitude quaternion $\mathbf{q}_{nb}$, estimated sensor biases.
* **Core Dependencies:** Time-stamped sensor feeds from `sensor_hal`.

### 5.4 Mission Management (`mission_exec`)
* **Data Ingest:** Waypoint sequences, GCS mode switch requests, fence breach flags, battery state of charge.
* **Data Egress:** Active guidance commands (target trajectory vectors, target velocity profiles, loiter origins), mode annunciators.
* **Core Dependencies:** State estimates from `nav_estimator`, fault alerts from `sys_mon`.

### 5.5 Communication & Telemetry (`telemetry_mgr`)
* **Data Ingest:** Inbound ground station commands via RF link, internal module status updates.
* **Data Egress:** Deserialized command structs to internal message broker, compressed telemetry packets out to radio modem.
* **Core Dependencies:** Radio UART/USB hardware driver, packet serialization library.

### 5.6 Health & Safety Watchdog (`sys_mon`)
* **Data Ingest:** Task loop execution latencies, power distribution board telemetry (bus voltage, current draw), communication link RSSI/loss timers.
* **Data Egress:** System readiness flags, emergency triggers (Return to Launch, immediate motor cut, land-in-place).
* **Core Dependencies:** System-wide module heartbeat subscriptions.

### 5.7 High-Rate Flight Logging (`logger`)
* **Data Ingest:** Estimator innovation values, raw high-rate gyro samples, actuator signals, status logs, error alerts.
* **Data Egress:** Persistent binary flight log files (`.ulg` or `.bin`) committed to physical non-volatile storage.
* **Core Dependencies:** File system access, dedicated DMA write buffer to prevent thread starvation.

### 5.8 Ground Control Station Interface (`gcs_bridge`)
* **Data Ingest:** Physical serial/socket byte stream from the telemetry modem.
* **Data Egress:** Validated, CRC-verified packet frames dispatched to `telemetry_mgr`.
* **Core Dependencies:** Network/serial stack, packet framing logic.

---

## 6. Subsystem Dependency & Data Flow Graph

```
[Raw Sensors: IMU / Baro / Mag / GNSS]
                  |
                  v
          [Sensor Interface]
             |          |
  (Raw IMU)  |          | (Corrected Observables)
             v          v
    [Flight Control] <--- [Navigation (EKF)] <-----+
           |                      ^                |
           | (Actuator Demands)   | (State Vector) |
           v                      |                |
      [ESC / Motors]       [Mission Exec] <--------+
                                  ^                | (Commands / Setpoints)
                                  |                |
                          [Telemetry Mgr] <--------+
                                  ^
                                  | (RF Uplink / Downlink)
                                  v
                        [GCS Bridge / Radio]
```

### Critical Path Constraints
1. **Zero-Lag Attenuation:** The `sensor_hal` $\rightarrow$ `nav_estimator` $\rightarrow$ `fc_core` pipeline represents the critical flight stabilization path. Total loop latency must not exceed **$2.5\,\text{ms}$** to maintain robust attitude stability during gust disturbances.
2. **Deterministic Failsafe:** If the heartbeat signal from `telemetry_mgr` drops for $>3.0\,\text{s}$ during autonomous flight, `mission_exec` must deterministically trigger the pre-configured Lost-Link contingency without manual intervention.

---

## 7. Integration Guidelines & Verification Criteria

To ensure reliable bench and flight integration, the software stack must adhere to the following standards:

* **Strict Interface Serialization:** All intra-module messages must use typed structs or standardized uORB/Protobuf schemas. Raw buffer pointers across task boundaries are strictly prohibited.
* **Graceful Degradation:** Sensor loss (e.g., GNSS lock drop) must trigger an automated fallback to an altitude-hold or dead-reckoning state with clear telemetry notification, rather than an unhandled software crash.
* **Deterministic Timing & Profiling:** Every periodic task must have its worst-case execution time (WCET) profiled using hardware trace pins and bench oscilloscopes.
* **System Logging Integrity:** Log write spikes must never block primary flight control threads. Buffer drops are acceptable on debug strings, but strictly forbidden on crash-analysis sensor streams.

---

## 8. Next Milestones

1. **Interface Control Document (ICD) Generation:** Map exact struct layouts, signal names, units, and endianness for all message types.
2. **Software-in-the-Loop (SITL) Harness:** Validate the state machine transitions in a virtual flight environment (Gazebo/JSBSim).
3. **Bench Integration Sign-off:** Execute end-to-end telemetry and actuator loop latency tests using real flight hardware.