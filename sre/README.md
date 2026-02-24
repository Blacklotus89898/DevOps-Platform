# Local SRE Agent

A **local-first Site Reliability Engineering (SRE) agent** for process monitoring, crash detection, log aggregation, and incident forensics — designed for **developer machines, homelabs, edge systems, and pre-production environments**.

This tool emphasizes **observability before automation**, providing strong forensic guarantees today while laying a clean foundation for **self-healing and automation** tomorrow.

---

## Why This Exists

Most SRE tooling assumes:

* Kubernetes
* Cloud-native infrastructure
* Heavy dependencies

This agent is intentionally:

* **Local-first**
* **Dependency-light**
* **Readable**
* **Fail-safe**
* **Operator-driven**

It ensures that **every failure leaves evidence**, even outside large platforms.

---

## Core Principles

* **Never lose failure context**
* **Do not automate blindly**
* **Prefer explicit operator control**
* **Fail safely**
* **Remain usable without root or cloud access**

---

## Current Capabilities

### Process Monitoring

* Watches a target process by name
* Detects:

  * Process crashes
  * Memory pressure
  * Thread count changes
* Low overhead polling via `psutil`

---

### Crash Detection

* Detects process disappearance within seconds
* Generates immediate crash reports
* Continues running and waits for recovery

---

### Forensic Report Generation

* Plain-text reports (no UI dependencies)
* Timestamped and immutable
* Designed for:

  * Post-mortems
  * Trend analysis
  * Offline inspection

Each report includes:

* Process state (PID, CPU, memory, threads)
* Application log tail
* Host health (RAM, disk)
* Kernel OOM signals (when permitted)
* Docker context
* Kubernetes context
* Available SRE tools on the host

---

### Local Log Aggregation

* Centralized report directory
* Grep-friendly, human-readable artifacts
* Safe for long-term archival

---

### Integrated Operator Tooling

The agent **detects and integrates with**:

* `htop` / `btop` → system-level inspection
* `lazydocker` → container debugging
* `k9s` → Kubernetes debugging

These tools are:

* Detected automatically
* Referenced in reports
* Optionally launched interactively on incidents

No TUI embedding. No coupling. No fragility.

---

## What This Is *Not* (By Design)

* Not a full observability platform
* Not a replacement for Prometheus/Grafana
* Not a Kubernetes-only tool
* Not an intrusive agent
* Not auto-remediating (yet)

---

## Typical Use Cases

* Monitoring long-running local services
* Debugging memory leaks
* Watching AI / ML training jobs
* Homelab reliability
* Pre-production incident simulation
* Learning SRE fundamentals hands-on
* Edge / air-gapped environments

---

## Architecture Overview

```
┌───────────────────┐
│   Local SRE Agent │
│  (Python Loop)    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│   psutil          │
│   OS Metrics      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Report Generator  │
│ - Snapshots       │
│ - Crash Reports   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Local Artifacts   │
│ sre_reports/      │
└───────────────────┘
```

---

## Roadmap & Priority Order

The roadmap follows **real SRE maturity progression**, not feature hype.

### Phase 1 — Reliability First (Next)

**Goal:** Reduce manual intervention without losing control

1. **Self-Healing Rules Engine**

   * Declarative recovery rules
   * Triggered by crashes or thresholds
   * Dry-run capable

2. **Auto-Restart (Local Process)**

   * Restart on crash
   * Backoff and retry limits
   * Failure escalation after N attempts

---

### Phase 2 — Container & Platform Awareness

**Goal:** Extend reliability into modern runtimes

3. **Docker Restart Hooks**

   * Restart failing containers
   * Capture container logs pre-restart

4. **Kubernetes Pod Recovery**

   * Restart pods
   * Scale deployments (controlled)
   * Namespace-aware actions

---

### Phase 3 — Operationalization

**Goal:** Make it production-operable

5. **systemd Service Mode**

   * Proper daemonization
   * Automatic startup
   * Journald integration

6. **JSON Event Stream**

   * Structured events alongside text reports
   * Enables ingestion into ELK / Loki
   * Backward-compatible with current reports

---

### Phase 4 — Observability & Intelligence

**Goal:** Move from reaction to insight

7. **Prometheus Exporter**

   * Crash counters
   * Memory trend metrics
   * MTBF signals

8. **Crash Frequency Scoring**

   * Rolling failure windows
   * Stability score (0–100)
   * Alert thresholds

---

### Phase 5 — Operator UX

**Goal:** Visibility without control risk

9. **Read-Only Web Dashboard**

   * Timeline view
   * Incident history
   * Trend graphs
   * No mutation endpoints

---

## Future Self-Healing Philosophy

Self-healing will be:

* **Explicit**
* **Policy-driven**
* **Auditable**
* **Reversible**

Example rule (future):

```yaml
on: crash
action: restart_process
max_retries: 3
cooldown_seconds: 60
```

Automation will **never run without artifacts**.

---

## Security Considerations

* No privileged operations by default
* No remote network exposure
* No auto-exec without explicit enablement
* Safe to run as non-root

---

## Status

**Current state:**
✔ Stable
✔ Production-safe for local usage
✔ Extensible
✔ Actively evolving

---

## Philosophy

> *“You can’t fix what you didn’t observe,
> and you shouldn’t automate what you don’t understand.”*

This project exists to enforce that discipline.
