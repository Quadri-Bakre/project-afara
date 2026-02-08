# Project Afara

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Status-Active%20Prototype-yellow)
![Docker](https://img.shields.io/badge/Container-Native-blueviolet)
![Domain](https://img.shields.io/badge/Domain-Automated%20Commissioning-orange)

> **Engineering Note:** This project is an active R&D initiative introducing DevOps methodologies to the Cyber-Physical, Audio-Visual (AV), and NetSec sectors.

## The Mission: DevOps for the Physical Layer
**Project Afara** (Yoruba for *"The Bridge"*) is a **Virtual Commissioning & Automated QA Framework** designed to bridge the gap between static design documentation and dynamic physical infrastructure.

In traditional Systems Integration, commissioning is often a manual, "Waterfall" process. Engineers rely on clipboards and disjointed spreadsheets to verify complex networks. This leads to human error, security gaps, and costly site revisits.

**Afara modernizes this workflow.** It treats the **Project Schedule (Excel)** as a "Source of Truth" and uses automated drivers to validate the physical reality against the design specification. Whether you are building a rack in a warehouse, commissioning a new site, or auditing an existing 5-year-old system, Afara provides instant, programmatic verification.

## Key Objectives

1.  **Full Lifecycle Validation:**
    * **Pre-Deployment:** Validate a rack is "Site Ready" (firmware, VLANs, config) before it leaves the warehouse.
    * **On-Site Commissioning:** Instantly verify 100+ devices are online and configured correctly during the install phase.
    * **Post-Occupancy Maintenance:** Audit existing sites to detect "Configuration Drift," failed power supplies, or security lapses years after deployment.

2.  **Infrastructure as Code (IaC):** Move away from manual CLI inspection. Define the desired state in your documentation, and let code enforce it.

3.  **Cybersecurity & Network Compliance:** Automate the auditing of security baselines. Afara verifies that devices are hardened (e.g., default credentials removed, SSH enabled/Telnet disabled, Port Security active) and conform to network policies.

4.  **Offline-First Development:** Enable control logic to be tested against "Mock" virtual devices (Digital Twins) when physical hardware is unavailable.

## Current Capabilities: The Audit Engine

The current build is a fully functional **Automated Auditing & Monitoring Engine** designed for scale and portability.

### 1. Universal Hardware Abstraction
Afara utilizes a modular, protocol-agnostic driver layer that standardizes communication across heterogeneous vendors. Whether checking a **Cisco Switch** (SSH), a **Windows Server** (PowerShell), a **Crestron Processor** (CIP/SSH), or a **Gude PDU** (HTTP), the engine treats all hardware as unified "Nodes." This abstraction allows for seamless switching between physical hardware and virtual lab simulations.


### 2. Automated PDF Reporting
The engine generates client-ready commissioning documentation automatically:
* **Compliance Check:** Flags devices that fail to meet the spec (e.g., "Firmware Mismatch" or "Offline").
* **Inventory Capture:** Auto-populates Serial Numbers and MAC addresses from live equipment into the report.
* **Health Diagnostics:** Includes specialized checks like PoE Usage vs. Budget, WAN Throughput, and OS Uptime.

### 3. Live CLI Dashboard
After the initial audit, Afara enters **Live Monitoring Mode**. It displays a real-time, refreshable dashboard in the terminal, giving engineers instant visibility into network health, active protocols, and device status.

## The Workflow

Afara transforms the commissioning process into a streamlined pipeline:

1.  **Define:** Populate the **Project Schedule (Excel)** with IP addresses, credentials, and device drivers.
2.  **Audit:** The `CommissioningOrchestrator` scans the network, probing every device to verify it matches the design.
3.  **Report:** The system generates a timestamped **PDF Report** summarizing the health and security status of the entire project.
4.  **Monitor:** The system stays active, looping through devices to provide real-time status updates via the CLI.

## Technical Architecture

The framework is built on a modular Python architecture designed for extensibility:

* **`main.py`**: The entry point. Loads the topology and starts the engine.
* **`core/`**: Orchestration logic, PDF reporting (`reporter.py`), and threading.
* **`drivers/`**: Hardware abstraction layers (HAL) utilizing Netmiko, Paramiko, and Requests.
* **`tools/`**: Helper scripts for generating project templates and mock data.

## Getting Started

### Prerequisites
* Python 3.10+
* Docker (Optional, for containerized deployment)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Quadri-Bakre/project-afara.git](https://github.com/Quadri-Bakre/project-afara.git)
    cd project-afara
    ```

2.  **Set up the environment:**
    ```bash
    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Generate Project Schedule:**
    Create a fresh Excel template with correct headers and driver keys.
    ```bash
    python tools/make_template.py
    ```

## Usage

### Option A: Local Run (Development)
Runs the engine directly on your machine, auto-converting Excel schedules to internal topology.

```bash
python main.py

```

### Option B: Containerized Simulation (Production)

Run the engine as an isolated background service, ideal for permanent site monitoring or cloud simulation.

```bash
# Build the image
docker build -t afara-engine .

# Run the container (background mode)
docker run -d --name afara-service --restart unless-stopped afara-engine

```

## Roadmap: The Future of Afara

Project Afara is evolving from a monitoring tool into a **Self-Healing Automation Platform**.

* **CI/CD Integration (In Progress):** Triggering automated network validation tests via GitHub Actions whenever the project schedule is updated.
* **Self-Healing Networks:** Moving beyond monitoring to active remediation (e.g., automatically rebooting a specific PoE port when a Wireless Access Point goes offline).
* **Digital Twin Emulation:** Enhanced simulation capabilities to spin up virtual "Mock Devices" for logic testing without physical hardware.

## Connect & Follow the Journey

This project is part of a broader initiative to modernize Systems Integration.

* **Medium:** [Read the Engineering Logs](https://www.google.com/search?q=https://medium.com/%40quadri.bakre)
* **LinkedIn:** [Quadri Bakre](https://www.linkedin.com/in/quadri-bakre)
* **X:** [@Quadri_Bakre](https://x.com/Quadri_Bakre)

---

*Maintained by Quadri | Systems Commissioning, Testing & QA Engineer*

```

```