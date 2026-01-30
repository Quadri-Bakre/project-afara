# Project Afara

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Status-Active%20Prototype-yellow)
![Docker](https://img.shields.io/badge/Container-Native-blueviolet)
![Domain](https://img.shields.io/badge/Domain-Virtual%20Commissioning-orange)

> **Engineering Note:** This project is an active R&D initiative. Architectures and APIs are subject to rapid iteration as the methodology for automated physical QA is refined.

## The Mission: DevOps for the Physical Layer
**Project Afara** (Yoruba for *"The Bridge"*) is a **Virtual Commissioning Framework** designed to bring Continuous Integration (CI) and Automated QA to the world of Audio-Visual (AV) and Cyber-Physical Systems.

In traditional systems integration, software validation is paralyzed by **Hardware Dependency**. Engineers cannot test control logic until physical gear (Crestron processors, Cisco switches) arrives on-site, creating a "Waterfall" bottleneck.

**Afara breaks this dependency.** It decouples control logic from physical hardware, enabling an **"Offline-First"** development workflow where infrastructure is simulated, tested, and validated before deployment.

## The Key Objective: "Offline" Commissioning
The primary goal of Project Afara is to decouple project delivery from hardware logistics.

In traditional integration, software validation is paralyzed until equipment arrives on site. Afara eliminates this bottleneck, allowing engineers to **fully commission and validate control logic** even when the physical equipment is:
* In a Warehouse
* In a Shipping Container
* In Transit
* Not yet manufactured

By simulating these devices or connecting to lab equivalents, Afara ensures the system is "Site Ready" before the hardware ever leaves the dock.

## Current State: The Virtual Engine
**The current build represents the Virtual Commissioning Layer.**

This engine focuses on the **Pre-Deployment Phase**, where equipment is assumed to be off-site or virtual. It connects Excel design documentation to:
1.  **Virtual Labs:** (Cisco CML, Mock Servers) to prove the network topology works.
2.  **Staging Environments:** To validate configurations on the bench before shipping.

## The Problem vs. The Solution

| The Traditional Way (Waterfall) | The Afara Way (Agile/DevOps) |
| :--- | :--- |
| **Manual Verification:** Engineers type commands into terminals one by one. | **Automated Auditing:** Scripts run thousands of tests against the infrastructure in seconds. |
| **Hardware Blocked:** Software waits for shipping containers and site readiness. | **Service Virtualization:** Code is tested against Python-based "Mock" servers (Digital Twins). |
| **Reactive:** Bugs are found on-site, causing costly delays. | **Proactive:** Logic is validated in CI pipelines weeks before site access. |

## Core Capabilities

### 1. Service Virtualization & Mock Environments
At its core, Afara is a dual-node architecture designed to simulate the physical world:
* **The Virtual Device (Server):** Python-based listeners (TCP/HTTP) that mimic the behavior of AV processors (e.g., simulating a Loxone Miniserver or Crestron Controller).
* **The Controller (Client):** A dynamic dispatcher that injects payloads to verify signal integrity without needing the actual device present.

### 2. Data-Driven "Digital Twin" Auditing
The engine uses standard project documentation as code.
* **Excel-to-Reality:** Ingests the **Project Schedule (Excel)** as the single source of truth.
* **Automated Compliance:** Automatically verifies that the live device (MAC Address, Serial Number, Firmware) matches the exact design spec, flagging discrepancies instantly.

### 3. Universal Hardware Abstraction
A unified driver layer that treats virtual and physical devices identically.
* **Hybrid Network Support:** Seamlessly switches between controlling virtual labs (Cisco CML) and physical hardware (Cisco Catalyst/SMB) without code changes.
* **Protocol Agnosticism:** Currently supports SSH (Netmiko), REST APIs, and raw TCP sockets, with an architecture designed to wrap proprietary dialects (e.g., Crestron/Control4 delimiters).

### 4. Enterprise Portability
* **Dockerized Runtime:** The entire engine runs as a containerized microservice, allowing it to be deployed on a laptop for local testing or a Raspberry Pi/Server for permanent site monitoring.
* **Forensic Logging:** Generates granular session logs (`logs/`) to provide an audit trail of every connection attempt, failure, and recovery.

## Future Roadmap & Possibilities
Project Afara is evolving into a full-stack commissioning suite. The current roadmap includes:

* **Protocol Drivers:** Building specific wrappers for vendor dialects (Crestron, Lutron, Q-SYS) to ensure vendor-agnostic control.
* **CI/CD Integration:** Triggering automated network validation tests via GitHub Actions whenever the project schedule is updated.
* **Cross-Platform Signaling:** Moving beyond simple chat alerts to industrial standards—using **MQTT and REST** to trigger physical rack indicators, update AV Touch Panels, or log faults directly into facility management software.
* **Self-Healing Networks:** Moving beyond monitoring to active remediation (e.g., automatically rebooting a PoE port when a WAP goes offline).

## Technical Architecture

The framework is built on a modular Python architecture:

* **`core/`**: The orchestration logic (Loaders, Loggers, Watchdogs).
* **`drivers/`**: Hardware abstraction layers (Cisco Netmiko, Generic Ping, Mock TCP).
* **`tools/`**: ETL scripts for converting Excel Data into System Topology.
* **`integrations/`**: Third-party driver code (e.g., Lua for Control4).

## Getting Started

### Prerequisites
* Python 3.10+
* Docker (Recommended for simulation)

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

4.  **Configuration:**
    * **Credentials:** Create a `.env` file (copy `example.env`) for secure credential management.
    * **Topology:** Open `project_schedule.xlsx` to define your Virtual or Physical devices.

## Usage

### Option A: Local Run (Development)
Runs the engine directly on your machine, auto-converting Excel schedules to YAML topology.

```bash
python main.py

```

### Option B: Containerized Simulation (Production)

Run the engine as an isolated background service.

```bash
docker build -t afara-engine .
docker run -d --name afara-service --restart unless-stopped afara-engine

```

## Connect & Follow the Journey

This project is part of a broader initiative to modernize Systems Integration.

* **Medium:** [Read the Engineering Logs](https://www.google.com/search?q=https://medium.com/%40quadri.bakre)
* **LinkedIn:** [Quadri Bakre](https://www.linkedin.com/in/quadri-bakre)
* **X:** [@Quadri_Bakre](https://x.com/Quadri_Bakre)

---

*Maintained by Quadri | Systems Commissioning, Testing & QA Engineer*

```

```