"""Direct Raw SQL Verification Script against PostgreSQL Server 184 (esp_apm_db).

Compares reported comparison table values for FS-017 and FS-040 (and FNW-001)
directly against the actual database rows in asset_registry, opg_well_telemetry, and events.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from app.db.esp_db import get_esp_cursor

def verify():
    print("=" * 80)
    print("DIRECT RAW SQL VERIFICATION AGAINST POSTGRESQL SERVER 184 (esp_apm_db)")
    print("=" * 80)

    with get_esp_cursor() as cur:
        # ----------------------------------------------------
        # 1. ASSET REGISTRY CHECK
        # ----------------------------------------------------
        print("\n--- 1. ASSET_REGISTRY AUDIT (FS-017 vs FS-040) ---")
        cur.execute("""
            SELECT well_id, cluster, pump_type, motor_hp, rated_amp_a, max_vibration_g,
                   ref_intake_pressure_psi, ref_discharge_pressure_psi
            FROM asset_registry
            WHERE well_id IN ('FS-017', 'FS-040')
            ORDER BY well_id;
        """)
        asset_rows = cur.fetchall()
        for r in asset_rows:
            print(f"Well: {r[0]}")
            print(f"  Cluster: {r[1]}")
            print(f"  Pump Type: {r[2]}")
            print(f"  Motor HP: {r[3]}")
            print(f"  Rated Current (A): {r[4]}")
            print(f"  Max Vibration (g): {r[5]}")
            print(f"  P50 PIP Baseline: {r[6]}")
            print(f"  P50 PDP Baseline: {r[7]}")

        # ----------------------------------------------------
        # 2. LATEST TELEMETRY IN OPG_WELL_TELEMETRY
        # ----------------------------------------------------
        print("\n--- 2. LATEST OPG_WELL_TELEMETRY AUDIT (FS-017 vs FS-040) ---")
        for w in ['FS-017', 'FS-040']:
            cur.execute("""
                SELECT timestamp, operating_state, motor_current_a, vibration_g,
                       intake_pressure_psi, discharge_pressure_psi, motor_temperature_c,
                       flow_rate_bpd, water_cut_pct, frequency_hz
                FROM opg_well_telemetry
                WHERE well_id = %s
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (w,))
            t_row = cur.fetchone()
            print(f"Well {w} Latest Telemetry:")
            print(f"  Timestamp: {t_row[0]}")
            print(f"  Operating State: {t_row[1]}")
            print(f"  Motor Current: {t_row[2]} A")
            print(f"  Vibration: {t_row[3]} g")
            print(f"  Intake Pressure (PIP): {t_row[4]} PSI")
            print(f"  Discharge Pressure (PDP): {t_row[5]} PSI")
            print(f"  Motor Temperature: {t_row[6]} °C")
            print(f"  Flow Rate (Liquid): {t_row[7]} BPD")
            print(f"  Water Cut: {t_row[8]} %")
            print(f"  Frequency: {t_row[9]} Hz")

        # ----------------------------------------------------
        # 3. LIFETIME TRIP COUNT & DOMINANT TRIP MODE
        # ----------------------------------------------------
        print("\n--- 3. LIFETIME TRIPS & DOMINANT TRIP MODES IN EVENTS ---")
        for w in ['FS-017', 'FS-040']:
            cur.execute("""
                SELECT count(*)
                FROM events
                WHERE well_id = %s;
            """, (w,))
            total_events = cur.fetchone()[0]

            cur.execute("""
                SELECT trip_cause, count(*) as cnt
                FROM events
                WHERE well_id = %s AND (operating_state = 'tripped' OR trip_cause IS NOT NULL)
                GROUP BY trip_cause
                ORDER BY cnt DESC;
            """, (w,))
            cause_rows = cur.fetchall()
            dominant_cause = cause_rows[0][0] if cause_rows else "NONE"
            dominant_count = cause_rows[0][1] if cause_rows else 0
            total_trips = sum(c[1] for c in cause_rows)

            print(f"Well {w} Event Statistics:")
            print(f"  Total Event Records: {total_events}")
            print(f"  Confirmed Tripped Events: {total_trips}")
            print(f"  Dominant Trip Cause: {dominant_cause} ({dominant_count} trips)")
            print(f"  All Trip Causes: {dict(cause_rows)}")

        # ----------------------------------------------------
        # 4. FNW-001 EVENT & 120s TELEMETRY WAVEFORM CHECK
        # ----------------------------------------------------
        print("\n--- 4. FNW-001 TRIP EVENT & TELEMETRY WINDOW AUDIT ---")
        cur.execute("""
            SELECT event_id, well_id, timestamp, trip_cause, severity, scenario
            FROM events
            WHERE well_id = 'FNW-001'
            ORDER BY timestamp DESC
            LIMIT 1;
        """)
        fnw_ev = cur.fetchone()
        print(f"FNW-001 Event:")
        print(f"  Event ID: {fnw_ev[0]}")
        print(f"  Timestamp: {fnw_ev[2]}")
        print(f"  Trip Cause: {fnw_ev[3]}")
        print(f"  Severity: {fnw_ev[4]}")
        print(f"  Scenario: {fnw_ev[5]}")

        # Check telemetry min/max around that event (-120s to +30s)
        ev_ts = fnw_ev[2]
        from datetime import timedelta
        t_start = ev_ts - timedelta(seconds=120)
        t_end = ev_ts + timedelta(seconds=30)
        cur.execute("""
            SELECT 
                count(*),
                min(vibration_g), max(vibration_g),
                min(motor_current_a), max(motor_current_a),
                min(intake_pressure_psi), max(intake_pressure_psi),
                min(discharge_pressure_psi), max(discharge_pressure_psi),
                min(motor_temperature_c), max(motor_temperature_c)
            FROM opg_well_telemetry
            WHERE well_id = 'FNW-001' AND timestamp BETWEEN %s AND %s;
        """, (t_start, t_end))
        wave_stats = cur.fetchone()
        print(f"FNW-001 Telemetry Window (T-120s to T+30s):")
        print(f"  Total Data Points in Window: {wave_stats[0]}")
        print(f"  Vibration (min -> peak): {wave_stats[1]:.4f}g -> {wave_stats[2]:.4f}g")
        print(f"  Motor Current (min -> peak): {wave_stats[3]:.4f}A -> {wave_stats[4]:.4f}A")
        print(f"  PIP (min -> max): {wave_stats[5]:.2f} PSI -> {wave_stats[6]:.2f} PSI")
        print(f"  PDP (min -> max): {wave_stats[7]:.2f} PSI -> {wave_stats[8]:.2f} PSI")
        print(f"  Motor Temp (min -> peak): {wave_stats[9]:.2f} °C -> {wave_stats[10]:.2f} °C")

if __name__ == "__main__":
    verify()
