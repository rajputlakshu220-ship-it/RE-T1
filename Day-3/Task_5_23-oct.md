# L05 - Integration Workspace Structure

## Task Information

* **Candidate Name:** Lakshay Thakur
* **Candidate ID:** TRAIN-004
* **Assigned Role:** Systems Integration Engineer
* **Project:** RudraEdge Aerospace - UAV Software Integration
* **Assignment Type:** Technical Training Assignment
* **Task Date:** 24 October 2026
* **Task Phase:** Integration Workspace Setup & Verification
* **Document ID:** L05
* **Document Version:** 1.1 (Extended Integration Specification)
* **Document Type:** Workspace Structure and Setup Documentation
* **Status:** Proposed Structure for Local Verification

---

## 1. Introduction

The Integration Workspace is designed to provide an organized, deterministic environment for managing and integrating the software components of an Unmanned Aerial Vehicle (UAV). A modern UAV software stack contains mission-critical modules that perform independent yet tightly coupled functions, including flight stabilization, guidance and navigation, communication telemetry, and multi-sensor acquisition.

Keeping all project files in a single flat directory without structural boundaries leads to file clutter, cyclic dependencies, untracked changes, and complex merge conflicts. To mitigate these operational risks, a separated, modular workspace structure is established for the RudraEdge Aerospace UAV software integration initiative.

The workspace isolates source code, configuration registries, local testing harnesses, and systems documentation into clear, dedicated hierarchies. This arrangement ensures that integration engineers can verify local configurations, test boundaries, and prepare interface bindings systematically before code is promoted into flight-certified staging environments.

---

## 2. Objectives

The primary objective is to create a deterministic local integration workspace with decoupled module directories, centralized configuration management, and repeatable local validation routines.

### Key Detailed Objectives

1. **Modular Boundary Enforcement:** Isolate UAV software subsystems into self-contained directories.
2. **Configuration Centralization:** Establish a single point of truth for integration settings using strict JSON schemas.
3. **Test Isolation:** Decouple local integration test runners, mocks, and logs from deliverable source trees.
4. **Traceable Technical Documentation:** Maintain technical specifications, interface control documents (ICDs), and setup manuals directly alongside the codebase.
5. **IDE Uniformity:** Provide standardized settings for Visual Studio Code across candidate workstations.
6. **Automated Verification:** Enable fast syntax parsing and path resolution using lightweight built-in command-line tools without complex build tools.
7. **Deterministic Relative Paths:** Ensure all configuration paths resolve consistently across Windows systems.
8. **Git-Centric Collaboration:** Establish branch and `.gitignore` hygiene to prevent polluting source control with personal artifacts or build binaries.
9. **Zero-Trust Flight Claims:** Maintain a strict boundary between workspace setup validation and flight readiness certification.
10. **Offline Operational Capability:** Allow developers to configure, edit, and locally test workspace structure in air-gapped or network-restricted engineering labs.

---

## 3. Scope of Work

### 3.1 Within Scope
* Directory hierarchy establishment and directory permission conventions.
* Module boundary definitions for Flight Controller, Navigation, Telemetry, and Sensor Manager.
* Centralized configuration storage (`config/L06_Integration_Configuration.json`).
* Schema definition and validation procedures for configuration files.
* Test harness structuring and placeholder execution scripts.
* PowerShell command references for directory creation, verification, and inspection.
* Environment prerequisites (Visual Studio Code, Python 3 runtimes).
* Workspace verification records and sign-off checklists.

### 3.2 Outside of Scope (Out of Scope)
* Implementing production flight control algorithms or state-space matrices.
* Low-level RTOS porting, device tree configuration, or bootloader setup.
* Physical sensor calibration (e.g., IMU bias estimation, magnetometer declination).
* Hardware-in-the-Loop (HIL) test execution and RF hardware bench validation.
* DO-178C or DO-254 formal airworthiness certification documentation.
* Live RF telemetry broadcasting or ground control station (GCS) telemetry links.
* Connecting to external telemetry relays or enterprise cloud endpoints.

---

## 4. Workspace Design Principles

The workspace architecture conforms to standard safety-critical software integration practices:

| Principle | Description | Implementation in Workspace |
| :--- | :--- | :--- |
| **Separation of Concerns** | Subsystems must remain isolated to reduce side-effects during integration. | Distinct folders under `/modules/` with no cross-module file leaks. |
| **Single Point of Configuration** | Operational flags, port assignments, and paths should not be hardcoded. | Centralized in `config/L06_Integration_Configuration.json`. |
| **Independent Verification** | Verification tooling must evaluate files without executing unverified code. | Path-checking and JSON parsing run as external checks. |
| **Air-Gapped Reliability** | All baseline validation steps must function in secure test labs without internet. | Relies solely on Python's built-in standard library (`json.tool`, `pathlib`). |
| **Predictable Traceability** | File names and paths must identify their operational lifecycle and version. | Document prefixes (`L05`, `L06`) mapped directly to work orders. |
| **Defensive Validation** | Never assume existence or validity until verified programmatically. | Syntax validation precedes path existence checks. |

---

## 5. Comprehensive Directory Tree Structure

```text
Integration_Workspace/
│
├── .vscode/                                 # Editor configuration & build tasks
│   ├── settings.json                        # Tab width, line endings, formatting rules
│   └── tasks.json                           # Integrated verification task runners
│
├── modules/                                 # Subsystem source modules
│   ├── flight_controller/                   # Attitude stabilization & rate control
│   │   ├── src/                             # Module source files
│   │   ├── include/                         # Header files and public APIs
│   │   └── README.md                        # Subsystem interface summary
│   │
│   ├── navigation/                          # Waypoint following, GNSS processing, EKF
│   │   ├── src/
│   │   ├── include/
│   │   └── README.md
│   │
│   ├── telemetry/                           # Ground station uplink/downlink packets
│   │   ├── src/
│   │   ├── include/
│   │   └── README.md
│   │
│   └── sensor_manager/                      # Sensor drivers, filtering & health monitors
│       ├── src/
│       ├── include/
│       └── README.md
│
├── config/                                  # Central configuration directory
│   ├── schemas/                             # JSON validation schemas
│   │   └── integration_config.schema.json   # Structural contract for L06
│   └── L06_Integration_Configuration.json   # Primary workspace integration manifest
│
├── tests/                                   # Workspace-level test suites
│   ├── unit/                                # Mock tests for module interfaces
│   ├── integration/                         # Cross-module communication checks
│   ├── test_path_verification.py            # Automated module presence test
│   └── README.md                            # Test execution handbook
│
├── docs/                                    # Systems engineering documentation
│   ├── architecture/                        # System block diagrams and ICDs
│   ├── checklists/                          # Readiness verification forms
│   └── L05_Integration_Workspace_Structure.md # Root duplicate/reference copy
│
├── logs/                                    # Execution and validation logs (git-ignored)
│   ├── .gitkeep                             # Ensures directory presence in repo
│   └── validation_output.log                # Local verification terminal dumps
│
├── .gitignore                               # Standard exclusions for temporary files
├── L05_Integration_Workspace_Structure.md   # Primary root documentation (this file)
└── README.md                                # Quickstart guide for onboarded engineers
```

---

## 6. Detailed Subsystem Module Profiles

To avoid ambiguous component boundaries, each module is assigned explicit responsibilities and interface rules.

```
+--------------------------------------------------------------------------------+
|                             GROUND STATION / PILOT                             |
+--------------------------------------------------------------------------------+
                                        ▲
                                        │ Telemetry Data Packets
                                        ▼
+--------------------------------------------------------------------------------+
|                              TELEMETRY SUBSYSTEM                               |
|                  (Packetizer, MAVLink Handler, Radio Driver)                   |
+--------------------------------------------------------------------------------+
                                        ▲
                                        │ Waypoints & Status
                                        ▼
+--------------------------------------------------------------------------------+
|                             NAVIGATION SUBSYSTEM                               |
|               (State Estimator, EKF, Path Planner, Geofence)                   |
+--------------------------------------------------------------------------------+
                                        ▲
                                        │ Demands (Pitch, Roll, Yaw Rate)
                                        ▼
+--------------------------------------------------------------------------------+
|                          FLIGHT CONTROLLER SUBSYSTEM                           |
|                    (PID Loops, Mixer, Actuator PWM Outputs)                    |
+--------------------------------------------------------------------------------+
                                        ▲
                                        │ Calibrated Sensor Data
                                        ▼
+--------------------------------------------------------------------------------+
|                           SENSOR MANAGER SUBSYSTEM                             |
|               (IMU, Barometer, Magnetometer, GNSS Decoders)                    |
+--------------------------------------------------------------------------------+
```

### 6.1 `flight_controller`
* **Core Function:** Outer loop position control translation, inner loop angular rate control, motor mixing, failsafe motor cutoff.
* **Expected Artifacts:** C/C++ or Python source algorithms, control parameter tables, motor test harnesses.
* **Boundary Restrictions:** Must not interface directly with raw telemetry radios or read raw SPI/I2C sensor buses. Receives sanitized sensor matrices from `sensor_manager`.

### 6.2 `navigation`
* **Core Function:** Extended Kalman Filter (EKF) state estimation, waypoint parsing, trajectory generation, home-point return calculations.
* **Expected Artifacts:** Path-planning scripts, coordinate transformation helpers (ECEF, NED, Geodetic), boundary geofence polygons.
* **Boundary Restrictions:** Must not execute low-level actuator drive calls. Sends attitude targets and velocity vectors to `flight_controller`.

### 6.3 `telemetry`
* **Core Function:** Frame serialization, packet checksums (e.g., CRC-16/32), MAVLink or custom binary protocol parsing, command dispatching.
* **Expected Artifacts:** Packet schema headers, buffer managers, radio transceiver interface routines.
* **Boundary Restrictions:** Must not alter flight state directly without passing commands through safety arbiters in `flight_controller`.

### 6.4 `sensor_manager`
* **Core Function:** Hardware interface drivers (SPI/I2C/UART/CAN), sensor health monitors, bias compensation, low-pass filtering.
* **Expected Artifacts:** Driver source code for IMU, Barometer, Magnetometer, GPS receiver, battery monitor.
* **Boundary Restrictions:** Must produce normalized engineering units (SI units: $m/s^2$, $rad/s$, $hPa$, $Kelvin$) for consuming modules.

---

## 7. Integrated Configuration Manifest (`L06`)

The configuration file `config/L06_Integration_Configuration.json` serves as the declaration manifest for all integrated modules.

### 7.1 Production Configuration Template

```json
{
  "$schema": "./schemas/integration_config.schema.json",
  "project_metadata": {
    "project_name": "RudraEdge Aerospace UAV Integration",
    "configuration_version": "1.0.0",
    "document_reference": "L06",
    "environment": "local_verification",
    "last_reviewed_date": "2026-10-24",
    "engineer": {
      "name": "Lakshay Thakur",
      "id": "TRAIN-004",
      "role": "Systems Integration Engineer"
    }
  },
  "workspace_settings": {
    "base_path": ".",
    "log_directory": "logs/",
    "strict_path_checking": true,
    "allow_offline_execution": true
  },
  "modules": [
    {
      "name": "flight_controller",
      "display_name": "Flight Stabilization and Rate Controller",
      "relative_path": "modules/flight_controller",
      "enabled": true,
      "language": "cpp",
      "version": "0.1.0",
      "required_subdirectories": ["src", "include"]
    },
    {
      "name": "navigation",
      "display_name": "Waypoint Navigation and Trajectory Planner",
      "relative_path": "modules/navigation",
      "enabled": true,
      "language": "cpp",
      "version": "0.1.0",
      "required_subdirectories": ["src", "include"]
    },
    {
      "name": "telemetry",
      "display_name": "Telemetry Streamer and Command Packetizer",
      "relative_path": "modules/telemetry",
      "enabled": true,
      "language": "c",
      "version": "0.1.0",
      "required_subdirectories": ["src", "include"]
    },
    {
      "name": "sensor_manager",
      "display_name": "Inertial and Environmental Sensor Manager",
      "relative_path": "modules/sensor_manager",
      "enabled": true,
      "language": "c",
      "version": "0.1.0",
      "required_subdirectories": ["src", "include"]
    }
  ],
  "verification_settings": {
    "python_validator": "tests/test_path_verification.py",
    "max_acceptable_latency_ms": 50,
    "enforce_lowercase_paths": true
  }
}
```

---

## 8. Version Control and Source Hygiene

A properly partitioned workspace requires strict `.gitignore` rules to avoid committing machine-specific files, binaries, and temporary logs into git repositories.

### Recommended `.gitignore` File

```gitignore
# RudraEdge Aerospace Workspace .gitignore

# Operating System specific
Thumbs.db
Desktop.ini
.DS_Store

# Visual Studio Code project cache
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json

# Build outputs and binaries
bin/
build/
out/
*.o
*.obj
*.exe
*.dll
*.so

# Python cache artifacts
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
venv/
.env

# Workspace dynamic log files
logs/*
!logs/.gitkeep
*.log
```

---

## 9. Step-by-Step Setup Runbook (PowerShell)

Follow this end-to-end command sequence in Windows PowerShell to instantiate the entire workspace from scratch.

### 9.1 Step 1: Initialize Workspace Directory Tree

```powershell
# Navigate to the workspace host directory
cd C:\Projects\RudraEdge

# Create root workspace directory
New-Item -ItemType Directory -Force -Path "Integration_Workspace"
cd Integration_Workspace

# Create primary workspace branches
New-Item -ItemType Directory -Force -Path ".vscode", "config\schemas", "docs\architecture", "docs\checklists", "tests\unit", "tests\integration", "logs"

# Create module directories and standard subdirectories
$modules = @("flight_controller", "navigation", "telemetry", "sensor_manager")
foreach ($mod in $modules) {
    New-Item -ItemType Directory -Force -Path "modules\$mod\src"
    New-Item -ItemType Directory -Force -Path "modules\$mod\include"
    New-Item -ItemType File -Force -Path "modules\$mod\README.md"
}

# Add log retention placeholder
New-Item -ItemType File -Force -Path "logs\.gitkeep"
```

### 9.2 Step 2: Create Test Validation Script

Create `tests/test_path_verification.py` to automate module and folder checking:

```python
"""
RudraEdge Aerospace - Integration Workspace Verification Script
Candidate: Lakshay Thakur (TRAIN-004)
"""

import json
import sys
from pathlib import Path

def run_verification():
    root_dir = Path(__file__).resolve().parent.parent
    config_file = root_dir / "config" / "L06_Integration_Configuration.json"

    print(f"[INFO] Inspecting workspace root: {root_dir}")

    if not config_file.exists():
        print(f"[FAIL] Configuration file not found at: {config_file}")
        sys.exit(1)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("[PASS] JSON Configuration syntax is valid.")
    except Exception as e:
        print(f"[FAIL] JSON parsing error: {e}")
        sys.exit(1)

    all_modules_present = True
    for module in data.get("modules", []):
        mod_name = module.get("name")
        rel_path = module.get("relative_path")
        full_path = root_dir / rel_path

        if full_path.exists() and full_path.is_dir():
            print(f"[PASS] Module directory verified: {rel_path}")
        else:
            print(f"[FAIL] Missing module directory: {rel_path}")
            all_modules_present = False

    if not all_modules_present:
        print("[FAIL] Workspace structure verification failed.")
        sys.exit(1)

    print("[SUCCESS] All structural integration checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    run_verification()
```

---

## 10. Verification Procedures

### 10.1 Quick JSON Format Validation
Run the native Python JSON serializer tool from terminal:

```powershell
python -m json.tool config/L06_Integration_Configuration.json > $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Configuration file contains 100% valid JSON syntax." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Syntax validation failed. Check line endings and commas." -ForegroundColor Red
}
```

### 10.2 Automated Deep Workspace Audit
Execute the integration verification harness:

```powershell
python tests/test_path_verification.py
```

### 10.3 Inspecting Tree Structure in Windows PowerShell
Verify that all files are cleanly structured in accordance with Section 5:

```powershell
Get-ChildItem -Recurse | Select-Object FullName
```

---

## 11. Traceability and Sign-off Matrix

This register records the step-by-step physical and software verification status of workspace L05.

| Step ID | Verification Target | Target Condition | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **VR-01** | Root Folder Presence | Directory `Integration_Workspace/` exists | `Test-Path .\Integration_Workspace` | Completed |
| **VR-02** | Subsystem Isolation | 4 distinct module directories exist | Folder tree inspection | Completed |
| **VR-03** | Configuration Store | `config/L06_Integration_Configuration.json` exists | File existence verification | Completed |
| **VR-04** | Syntax Robustness | JSON parses without delimiter errors | `python -m json.tool` check | Completed |
| **VR-05** | Relative Path Health | Config declared paths resolve to real directories | `test_path_verification.py` | Completed |
| **VR-06** | Document Availability | L05 document present at workspace root | Markdown reader inspection | Completed |
| **VR-07** | Offline Independence | Zero internet requests during test script run | Offline mode execution | Completed |
| **VR-08** | Git Cleanliness | Exclusions defined for binaries and caches | `.gitignore` file audit | Completed |

---

## 12. Engineering Conclusion

The expanded Integration Workspace documentation provides a rigorous, standardized, and repeatable framework for the RudraEdge Aerospace UAV integration effort. By systematically separating subsystems (`flight_controller`, `navigation`, `telemetry`, `sensor_manager`), establishing strict configuration contracts under `config/L06`, and automating workspace audits via standalone offline test routines, integration engineers can maintain workspace cleanliness and eliminate configuration drift early in the lifecycle.

Future assignment phases will build upon this directory structure to inject interface contracts, mock message buses, and compile isolated component source codes.

---

**Document Identification:** L05 - Integration Workspace Structure  
**Author:** Lakshay Thakur  
**Role:** Systems Integration Engineer  
**ID:** TRAIN-004  
**Project:** RudraEdge Aerospace - UAV Software Integration  
**Date of Record:** 24 October 2026