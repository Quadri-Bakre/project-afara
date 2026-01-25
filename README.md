# Project Afara

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Status](https://img.shields.io/badge/Status-Active%20Prototype-green)
![Domain](https://img.shields.io/badge/Domain-Systems%20QA-orange)

## Overview
**Project Afara** (Yoruba for *"The Bridge"*) is an automated testing framework designed to modernize the commissioning and Quality Assurance (QA) of integrated cyber-physical systems.

In the current Systems Integration landscape, validation is often manual, unscalable, and prone to inconsistency. This project addresses these inefficiencies by applying **DevOps principles**, such as Service Virtualization and Infrastructure-as-Code (IaC), to physical hardware environments.

## The Objective
To engineer a **Systems Commissioning Middleware** that delivers:
1.  **Service Virtualization:** De-coupling control logic from physical dependencies by implementing software mocks for proprietary hardware.
2.  **Automated Infrastructure Validation:** Programmatic verification of network state via SSH/Netconf rather than manual CLI inspection.
3.  **Cross-Protocol Interoperability:** A unified abstraction layer that enables heterogeneous systems (Industrial IoT, Enterprise Network, AV) to exchange telemetry.

## Architecture & Modules
The framework is designed as a hybrid micro-services architecture, bridging local Python logic with enterprise-grade network emulation.

### Current Implementation (Phase 1)
* **`cisco_ssh_manager.py` (Live Infrastructure):**
    Integrated with **Cisco CML (Modeling Labs)** to validate automation logic against real IOSv kernels. It handles SSH session management, privileged execution, and telemetry retrieval via `Netmiko`.

* **`mock_device_server.py` (Virtual Endpoint):**
    A TCP-based service simulator that mimics legacy hardware behavior. It enables "Offline-First" development of control drivers.

* **`tcp_client_controller.py` (Command Dispatch):**
    The central control node responsible for dispatching payloads to edge devices (real or virtual) and parsing protocol-specific acknowledgments.

### Implementation (Phase 2: Active Monitoring)
* **`afara_watchdog.py` (Logic Engine):**
    A cross-platform service (Windows/Linux/macOS) that polls critical network assets via OS-native ICMP. It features "State Latching" logic to prevent alert fatigue during intermittent network flapping.

* **`loxone_controller.py` (IoT Driver):**
    A REST API driver connecting Python to Loxone Miniservers. It translates network states into physical actions (e.g., triggering alarms, switching relays, Sending Messages or App notifications to admin or users) using persistent state control (`/On` vs `/Off` logic).

* **`mock_loxone_server.py` (Virtual Controller):**
    A lightweight HTTP server that emulates the Loxone REST API. It allows developers to validate the Watchdog logic and alarm triggers entirely on localhost, without requiring physical automation hardware.

## Getting Started

### Prerequisites
* Python 3.9+
* Cisco CML (Optional for live switch testing)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Quadri-Bakre/project-afara.git](https://github.com/Quadri-Bakre/project-afara.git)
    cd project-afara
    ```

2.  **Set up the environment:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    To protect sensitive credentials, this project uses a `.env` file.
    * Duplicate the template: `cp example.env .env`
    * Edit `.env` with your local lab credentials (IP, Username, Password).

## Usage

### Workflow A: Mock Protocol Testing
To test control logic without physical hardware:

1.  **Launch the Virtual Endpoint:**
    ```bash
    python mock_device_server.py
    ```
    *Status: Listening on 127.0.0.1:5001*

2.  **Launch the Controller (New Terminal):**
    ```bash
    python tcp_client_controller.py
    ```
    *Command: Type `POWER_ON` to test the handshake.*

### Workflow B: Live Infrastructure Validation
To validate network state against Cisco CML or physical switches:

1.  **Ensure `.env` is configured correctly.**
2.  **Execute the Manager:**
    ```bash
    python cisco_ssh_manager.py
    ```
    *Output: Verifies SSH reachability and retrieves the device hostname.*

### Workflow C: Network Watchdog Service (Hardware)
To monitor a critical asset and trigger a **physical** Loxone alarm on failure:

1.  **Verify Configuration:** Ensure `.env` contains the IP of your **real** Loxone Miniserver (e.g., `192.168.1.100`) and the correct Virtual Input name.
2.  **Launch the Watchdog:**
    ```bash
    python afara_watchdog.py
    ```
    * *Status: Polling Target...*
    * *Action: If the target goes offline, the script sends a command to the physical Miniserver to turn the Alarm State ON.*

### Workflow D: Fully Virtualized Commissioning (No Hardware)
To test the entire "Watchdog -> Alarm" logic chain **without** physical hardware:

1.  **Configure `.env` for Simulation:**
    ```ini
    # Point the driver to the Mock Server
    LOXONE_IP=127.0.0.1:5001
    LOXONE_USER=test
    LOXONE_PASS=test
    ```
2.  **Start the Mock Server:**
    ```bash
    python mock_loxone_server.py
    ```
3.  **Run the Watchdog (New Terminal):**
    ```bash
    python afara_watchdog.py
    ```
    *Result: When the Watchdog triggers an alarm, you will see the "On/Off" command appear in the Mock Server terminal window instead of on a real device.*

## Security & Compliance
* **Credential Abstraction:** All sensitive keys and environmental configurations are managed via `.env` abstraction layers.
* **Operational Safety:** Automation modules operate in read-only telemetry mode by default to ensure non-destructive testing on live infrastructure.

## Deployment (Docker)
To run the application in a containerized environment (ensuring consistent behavior across Windows/Linux/macOS):

1.  **Build the Image:**
    ```bash
    docker build -t project-afara:v1 .
    ```

2.  **Run the Container:**
    Injects your local configuration `.env` into the container to allow access to physical hardware.
    ```bash
    docker run -it --rm --env-file .env project-afara:v1
    ```

## Connect
* **LinkedIn:** [Quadri Bakre](https://www.linkedin.com/in/quadri-bakre) - *Professional updates & Engineering insights*
* **X:** [@Quadri_Bakre](https://x.com/Quadri_Bakre) - *Real-time R&D updates*

---
*Maintained by Quadri | Systems Commissioning, Testing & QA Engineer*
