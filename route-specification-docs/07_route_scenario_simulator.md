---
route_id: route.scenario_simulator
type: route
title: What-If Scenario Simulator
path: /custom-testing
workspace: operations
summary: What-if operational scenario simulation bench with 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins.
related:
  - route.well_detail
  - route.live_calculations
aliases:
  - scenario simulator
  - what-if simulator
  - custom testing
  - sensor testing
  - what if scenario simulator
  - custom testing bench
keywords:
  - scenario simulator
  - what-if analysis
  - fault presets
  - dynamic pump curve
  - 14-channel telemetry
  - thermal stress
authority: Advait Surveillance Engineering
last_reviewed: 2026-10-14
---

# 🧭 Route Specification: `/custom-testing` — What-If Scenario Simulator Bench

**Application Workspace:** Operations (`WORKSPACES.operations`)  
**File Location:** [`src/routes/custom-testing.tsx`](file:///x:/TAS/v2_ESP/esp-insight-suite/src/routes/custom-testing.tsx)  
**Supporting Components & Modules:**  
* [`PumpCurveChart.tsx`](file:///x:/TAS/v2_ESP/esp-insight-suite/src/components/esp/charts/PumpCurveChart.tsx)  
* [`calc.ts`](file:///x:/TAS/v2_ESP/esp-insight-suite/src/lib/esp/calc.ts) (`tdhBreakdown`, `frictionHeadFt`, `psiToFt`)  
* [`fleet.ts`](file:///x:/TAS/v2_ESP/esp-insight-suite/src/data/esp/fleet.ts) (`FLEET` dataset)  
**Backend Mathematical Provenance:** Matches `esp_routes.py` lines 572, 575, 608, 675, and 2491.  

***

## 1. Route Metadata & Header

### Route Definition
* **Route Path:** `/custom-testing`
* **Page Title:** `What-If Scenario Simulator — ADVAIT ESP-PMM`
* **Meta Description:** `What-if operational scenario simulation and sensor testing across all platform views.`

### Header Section (`PageHeader`)
* **Title:** `What-If Scenario Simulator`
* **Subtitle:** `Define an operational scenario or adjust sensor telemetry to evaluate physical lift dynamics, pump operating curves, and virtual flow rates.`
* **Header Actions & Info:** Surfaces last execution timestamp and provides instant keyboard shortcut notice (`Enter to Simulate`).

***

## 2. Component 1: Scenario Configuration Bench (`Section 1`)

Encapsulated in an elevated master panel (`Panel`):
* **Target Well Configuration Dropdown:**
  * Pulls asset specifications from the `FLEET` registry (`FS-004`, `FS-006`, `FS-010`, `FS-013`, `FS-016`, `FS-017`, `FS-023`, `FS-040`, `FS-047`, `FNW-001`, `FWS-001`).
  * Changing wells automatically updates the equipment hardware defaults: Pump Depth (ft), Number of Stages, Motor HP, and Baseline Water Cut (%).
* **Quick Scenario Presets Dropdown:**
  * One-click presets injecting pre-calibrated multi-parameter fault conditions:

| Preset Name | Tone | Badge | Physical Condition Description |
|---|:---:|---|---|
| **Normal Operating Baseline** | `normal` | `Optimal 50.0 Hz` | Stable production rate at BEP with minimal gas fraction, normal thermal & electrical balance. |
| **Gas Interference & Locking** | `warning` | `GVF 38.0%` | Free gas entering pump intake causing head reduction, current oscillation, and rate drop. |
| **Dry Well / Pump-Off Underload** | `critical` | `PIP 65 psi` | Fluid level drop below intake. Low intake pressure, underload current, and severe motor overheating. |
| **Sand Ingestion & High Load** | `warning` | `Current 66 A` | Particulate solids causing mechanical friction, motor overload current spike, and thermal rise. |
| **Bearing Degradation & Thermal Stress**| `critical` | `Vibration 3.4g` | Mechanical bearing wear downhole with elevated radial vibration and critical winding temperature. |
| **Electrical Phase Imbalance** | `warning` | `Power Factor 0.68`| Unbalanced supply voltage or surface VFD transformer phase drop causing current asymmetry. |

***

## 3. Component 2: 14-Channel Granular Telemetry Input Grid

Surfaces full interactive control over every primary downhole and surface measurement:

```mermaid
grid-flowchart
    subgraph Electrical_Group["Electrical Domain"]
        C1["1. Frequency (30 - 65 Hz)"]
        C2["4. Motor Current (10 - 100 A)"]
        C3["5. Motor Voltage (300 - 500 V)"]
        C4["6. Power Factor (0.40 - 1.00)"]
    end
    subgraph Hydraulic_Group["Hydraulic & Production Domain"]
        C5["2. Intake Pressure PIP (0 - 1500 psi)"]
        C6["3. Discharge Pressure PDP (500 - 3500 psi)"]
        C7["9. Gross Liquid Rate (0 - 5000 BPD)"]
        C8["10. Water Cut (0 - 100 %)"]
        C9["13. Wellhead Pressure WHP (0 - 1000 psi)"]
        C10["14. Surface Choke (0 - 100 %)"]
    end
    subgraph Gas_and_Mechanical["Gas & Mechanical Domain"]
        C11["7. Motor Temp (20 - 180 °C)"]
        C12["8. Radial Vibration (0.0 - 6.0 g)"]
        C13["11. Gas Rate (0 - 1000 MSCFD)"]
        C14["12. Gas Fraction GVF (0.0 - 80.0 %)"]
    end
```

### Granular Input Specifications

| # | Channel Name | State Variable | Step | Min / Max | Engineering Unit | Visual Accent |
|---|---|---|:---:|:---:|:---:|:---:|
| **1** | Drive Frequency | `freq` | $0.5$ | $30 - 65$ | $\text{Hz}$ | Emerald |
| **2** | Intake Pressure (PIP) | `pip` | $10$ | $0 - 1500$ | $\text{psi}$ | Cyan |
| **3** | Discharge Pressure (PDP) | `pdp` | $25$ | $500 - 3500$ | $\text{psi}$ | Sky Blue |
| **4** | Motor Current | `current` | $0.5$ | $10 - 100$ | $\text{A}$ | Amber |
| **5** | Motor Voltage | `voltage` | $5$ | $300 - 500$ | $\text{V}$ | Yellow |
| **6** | Power Factor | `powerFactor` | $0.01$ | $0.40 - 1.00$ | $\cos\phi$ | Amber |
| **7** | Motor Winding Temperature | `motorTemp` | $1$ | $20 - 180$ | $\text{°C}$ | Rose |
| **8** | Radial Vibration | `vibration` | $0.05$ | $0.0 - 6.0$ | $\text{g}$ | Rose |
| **9** | Gross Liquid Rate | `flowRate` | $10$ | $0 - 5000$ | $\text{BPD}$ | Emerald |
| **10**| Water Cut | `waterCut` | $1$ | $0 - 100$ | $\%$ | Blue |
| **11**| Gas Rate | `gasFlow` | $5$ | $0 - 1000$ | $\text{MSCFD}$ | Teal |
| **12**| Gas Volume Fraction (GVF)| `gvf` | $0.5$ | $0.0 - 80.0$ | $\%$ | Teal |
| **13**| Wellhead Pressure (WHP) | `whp` | $5$ | $0 - 1000$ | $\text{psi}$ | Indigo |
| **14**| Surface Choke Position | `choke` | $5$ | $0 - 100$ | $\%$ | Purple |

### Hardware Assembly Banner & Simulation Action
* **Downhole Specs Ribbon:** Displays active assembly parameters: `Pump: {pumpModel}`, `Stages: {stages}`, `Depth: {pumpDepth} ft`, `Motor HP: {motorHp} HP`.
* **Execution Button (`Simulate Scenario (Enter)`):** Triggers `handleExecute()`, re-evaluates the physics formulas, and initiates smooth scrolling to the analytical sub-pages below.

***

## 4. Component 3: Analytical Physics Engine & Derived Formulas

All calculations match the backend Single Source of Truth (`esp_routes.py`):

1. **Fluid Specific Gravity ($SG$):**
   $$SG = (WC \times 1.05) + ((1 - WC) \times 0.85)$$
2. **Pressure Differential ($\Delta P$):**
   $$\Delta P = PDP - PIP \quad [\text{psi}]$$
3. **Total Dynamic Head ($TDH$):**
   $$TDH = H_{\Delta P} + H_{\text{elevation}} + H_{\text{friction}} \quad [\text{ft}]$$
   *Calculated via `tdhBreakdown()` with Hazen-Williams friction.*
4. **Head per Stage:**
   $$\text{Head/Stage} = \frac{TDH_{\text{total}}}{\text{stages}} \quad [\text{ft/stage}]$$
5. **Active Electrical Power ($P_{kW}$):**
   $$P_{kW} = \frac{\sqrt{3} \times V \times I \times \cos\phi}{1000}$$
6. **Hydraulic Power ($HP_{hyd}$):**
   $$HP_{hyd} = \frac{Q_{BPD} \times TDH_{\text{ft}} \times SG}{135,740}$$
7. **Motor Power Utilized ($HP_{used}$):**
   $$HP_{used} = P_{kW} \times 1.341$$
8. **Wire-to-Water Overall Efficiency ($\eta$):**
   $$\eta = \left(\frac{HP_{hyd}}{HP_{used}}\right) \times 100\%$$
9. **Virtual Flow Metering (VFM Liquidation):**
   $$Q_{\text{vfm, gross}} = Q \times \left(1 - \frac{GVF}{100} \times 0.45\right)$$
   $$Q_{\text{vfm, net oil}} = Q_{\text{vfm, gross}} \times \left(1 - \frac{WC}{100}\right)$$
   $$Q_{\text{vfm, water}} = Q_{\text{vfm, gross}} \times \left(\frac{WC}{100}\right)$$
10. **Real-Time Fault Classifier & Health Score:**
    * Evaluates deterministic rules against simulated values:
      * $PIP < 100\text{ psi} \lor I < 30\text{ A} \rightarrow \text{Dry Well / Pump-Off Underload}$ ($P = 0.88$, Health: $32$).
      * $GVF > 25\% \rightarrow \text{Gas Interference & Locking}$ ($P = 0.79$, Health: $48$).
      * $\text{Vibration} > 2.5\text{g} \lor T_{\text{motor}} > 120\text{°C} \rightarrow \text{Bearing Wear & Thermal Stress}$ ($P = 0.84$, Health: $42$).
      * $I > 60\text{ A} \rightarrow \text{Sand Ingestion / Overload}$ ($P = 0.75$, Health: $52$).
      * $\cos\phi < 0.75 \rightarrow \text{Electrical Phase Imbalance}$ ($P = 0.68$).

***

## 5. Component 4: Multi-View Analytical Workspace (4 Sub-Pages)

Navigated via a dedicated pagination controller (`activeSubPage` $1 \rightarrow 4$) with next/previous buttons:

### Sub-Page 1: Downhole & Fleet Impact
* **Fleet Gross Rate Delta:** Compares simulated gross liquid rate against baseline field quota.
* **14-Channel Telemetry Grid:** Renders cards for all 14 parameters displaying current simulated values against standard normal operating envelopes. Sensor values out of range are highlighted in amber/rose.

### Sub-Page 2: Physics & VFM Breakdown
* **Fluid Dynamics Panel:** Fluid SG ($0.85 - 1.05$), Delta P ($\text{psi}$), TDH ($\text{ft}$), and Head/Stage ($\text{ft/stage}$).
* **Power & Efficiency Panel:** Active Electrical Power ($\text{kW}$), Hydraulic Power ($\text{HP}$), Motor Utilization ($\text{HP}$), Wire-to-Water Efficiency ($\%$), and Motor Slip ($\%$).
* **VFM Reconciled Production:** Reconciled Gross Liquid ($\text{BPD}$), Net Oil Output ($\text{BOPD}$), and Water Production ($\text{BWPD}$).
* **Evaluated Fault Spectrum:** Primary classified fault banner, health score index ($0 - 100$), and sorted probability spectrum.

### Sub-Page 3: Dynamic Pump Curve Analysis (`PumpCurveChart`)
* **Interactive H-Q Affinity Curve:**
  * Recalculates head and flow affinity equations dynamically based on simulated frequency:
    $$Q_2 = Q_1 \left(\frac{f_2}{f_1}\right), \quad H_2 = H_1 \left(\frac{f_2}{f_1}\right)^2$$
* **Operating Point Overlay:** Plots an active pulsating marker $(Q_{\text{sim}}, TDH_{\text{sim}})$ on top of the catalog curve.
* **Operating Zones:** Visual shading for the Continuous Operating Range (COR) and Recommended Operating Range (ROR) with BEP marker.

### Sub-Page 4: Thermal & Reliability Margins
* **Motor Thermal Headroom:** Calculated winding temperature margin before thermal trip ($140\text{°C}$ limit).
* **Vibration Fatigue Index:** Radial acceleration stress rating based on ISO 10816 vibration severity standards.
* **Remaining Useful Life (RUL) Delta:** Estimated runtime impact and mechanical stress degradation index.
