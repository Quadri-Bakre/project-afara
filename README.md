# Project Afara

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Status](https://img.shields.io/badge/Status-Active%20Prototype-green)
![Domain](https://img.shields.io/badge/Domain-Systems%20QA-orange)

## Overview
**Project Afara** (Yoruba for *"The Bridge"*) is an automated testing framework designed to modernize the commissioning and Quality Assurance (QA) of integrated cyber-physical systems.

In the current Systems Integration landscape, validation is often manual, unscalable, and prone to inconsistency. This project addresses these inefficiencies by applying **DevOps principles**, such as Service Virtualization and Infrastructure-as-Code (IaC), to physical hardware environments.

## The Objective
To engineer a **Systems Commissioning Middleware** that delivers:
1.  **Service Virtualization:** De-coupling control logic from physical dependencies by implementing software mocks for proprietary hardware (e.g., Crestron, Control4, Cisco).
2.  **Automated Infrastructure Validation:** Programmatic verification of network state via SSH/Netconf rather than manual CLI inspection.
3.  **Cross-Protocol Interoperability:** A unified abstraction layer that enables heterogeneous systems (Industrial IoT, Enterprise Network, AV) to exchange telemetry.

## Architecture & Modules
The framework is designed as a modular micro-services architecture.

### Current Implementation (Phase 1)
* **`mock_device_server.py` (Virtual Endpoint):**
    A TCP-based service simulator that mimics hardware behavior. It enables "Offline-First" development of control drivers, allowing logic to be validated before physical deployment.

### In Development (Coming Soon)
* **`tcp_client_controller.py` (Command Dispatch):**
    The central control node responsible for dispatching payloads to edge devices and parsing protocol-specific acknowledgments.
* **`cisco_ssh_manager.py` (Network Telemetry):**
    An automated infrastructure manager utilizing `Netmiko` to securely retrieve and parse operational data from Cisco IOS environments.

## Getting Started

### Prerequisites
* Python 3.9+
* Virtual Environment (Recommended)

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

## Usage
To initialize the mock environment for protocol testing:

1.  **Launch the Virtual Endpoint:**
    ```bash
    python mock_device_server.py
    ```
    *Status: Listening on 127.0.0.1:5001 (Simulating Hardware)*

2.  **Test Connectivity (In a separate terminal):**
    *(Client Controller coming in next update)*

## Security & Compliance
* **Credential Abstraction:** All sensitive keys and environmental configurations are managed via `.env` abstraction layers.
* **Operational Safety:** Automation modules operate in read-only telemetry mode by default to ensure non-destructive testing on live infrastructure.

## Connect
* **LinkedIn:** [Quadri Bakre](https://www.linkedin.com/in/quadri-bakre) - *Professional updates & Engineering insights*
* **X:** [@Quadri_Bakre](https://x.com/Quadri_Bakre) - *Real-time R&D updates*

---
*Maintained by Quadri | Systems Commissioning, Testing & QA Engineer*
