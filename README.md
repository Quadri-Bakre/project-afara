# Project Afara

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Status](https://img.shields.io/badge/Status-Phase%204%3A%20Modular%20Beta-green)
![Domain](https://img.shields.io/badge/Domain-Systems%20Commissioning-orange)

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

### Current Implementation (Phase 4: Modular Architecture)
* **`main.py` (The Engine):**
    The central coordinator. It reads configuration, loads the correct drivers, and executes monitoring loops. It is designed to run 24/7 in a container.

* **`drivers/generic.py` (Universal Driver):**
    The fallback driver for 90% of devices (Apple TV, Sky Q, Cameras). Handles Ping and Port Scanning.

* **`drivers/loxone.py` (IoT Driver):**
    A REST API driver connecting Python to Loxone Miniservers. It translates network states into physical actions using persistent state control.

* **`tests/` (The Archive):**
    Contains utility scripts, mock servers, and unit tests used during development (e.g., `mock_loxone_server.py`, `vlan_provisioner.py`).

## Getting Started

### Prerequisites
* Python 3.9+
* Docker (Optional, for production)

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

### Workflow A: Run the Commissioning Engine
To start the continuous monitoring service (Watchdog Mode):

```bash
python main.py

```

**What happens?**

1. The system loads the `GenericDevice` driver to monitor your `DEVICE_IP`.
2. It loads the `LoxoneManager` driver to connect to your automation controller.
3. If the device goes offline, it triggers the Loxone Alarm automatically.

### Workflow B: Run Unit Tests

To test specific components without running the main engine:

```bash
# Test the Loxone connection specifically
python tests/test_loxone.py

```

### Workflow C: Fully Virtualized Commissioning

To test the entire "Watchdog -> Alarm" logic chain without physical hardware:

1. **Configure `.env` for Simulation:**
```ini
# Point the driver to the Mock Server
LOXONE_IP=127.0.0.1:5001
LOXONE_USER=test
LOXONE_PASS=test

```


2. **Start the Mock Server:**
```bash
python tests/mock_loxone_server.py

```


3. **Run the Engine (New Terminal):**
```bash
python main.py

```



## Deployment (Docker)

To run the engine as a background service on a Headless Server (Ubuntu/Linux).

1. **Build the Image:**
```bash
docker build -t project-afara:v1 .

```


2. **Run in Background:**
We use `--restart unless-stopped` to ensure the service auto-reboots if the server crashes.
```bash
docker run -d \
  --name afara-engine \
  --restart unless-stopped \
  --net=host \
  --env-file .env \
  project-afara:v1

```


3. **View Live Logs:**
```bash
docker logs -f afara-engine

```



## Security & Compliance

* **Credential Abstraction:** All sensitive keys and environmental configurations are managed via `.env` abstraction layers.
* **Operational Safety:** Automation modules operate in read-only telemetry mode by default to ensure non-destructive testing on live infrastructure.

## Connect

* **LinkedIn:** [Quadri Bakre](https://www.linkedin.com/in/quadri-bakre) - *Professional updates & Engineering insights*
* **X:** [@Quadri_Bakre](https://x.com/Quadri_Bakre) - *Real-time R&D updates*

---

*Maintained by Quadri | Systems Commissioning, Testing & QA Engineer*

```

```