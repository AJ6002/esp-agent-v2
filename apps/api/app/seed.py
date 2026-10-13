"""Demo data initialization: roles, users, equipment, fault codes, spare parts, knowledge base, historical work orders."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.base import (
    EquipmentStatusEnum,
    FaultReportStatusEnum,
    KnowledgeCategoryEnum,
    MaintenanceLogTypeEnum,
    PriorityEnum,
    RiskLevelEnum,
    UrgencyEnum,
    WorkOrderStatusEnum,
    WorkOrderTypeEnum,
)
from app.models.equipment import Equipment, EquipmentType, FaultCode, SparePart
from app.models.fault import FaultReport
from app.models.intelligence import (
    AgentRun,
    AnomalyEvent,
    EquipmentSensor,
    FaultDiagnosis,
    MaintenanceRecommendation,
    OperationApproval,
    RiskPrediction,
    SparePartReservation,
    TelemetryRecord,
    ToolInvocation,
)
from app.models.knowledge import KnowledgeArticle
from app.models.maintenance import LaborEntry, MaintenanceLog, WorkOrderSparePart
from app.models.user import Skill, TechnicianProfile, User
from app.models.workorder import (
    WorkOrder,
    WorkOrderAssignment,
    WorkOrderChecklistItem,
    WorkOrderStatusHistory,
)

DEMO_PASSWORD = "Demo123456"

SKILLS = [
    "Electrical Maintenance",
    "Mechanical Maintenance",
    "PLC Programming",
    "Pneumatics & Hydraulics",
    "Servo Tuning",
    "Welding",
    "Robot Maintenance",
    "Instrumentation & Calibration",
]

EQUIPMENT_TYPES = [
    ("Industrial Motor", "Three-phase induction motor and bearing system"),
    ("CNC Machine Tool", "CNC machining center equipment"),
    ("Packaging Machine", "Automated packaging line equipment"),
    ("Air Compressor", "Compressed air supply equipment"),
    ("Conveyor", "Material conveyor belt and chain system"),
    ("Industrial Robot", "Six-axis and SCARA industrial robots"),
]

FAULT_CODES = [
    ("M101", "Bearing Wear", "high", "Industrial Motor"),
    ("M102", "Bearing Overheating", "high", "Industrial Motor"),
    ("M103", "Motor Overload", "high", "Industrial Motor"),
    ("M104", "Voltage Abnormality", "medium", "Industrial Motor"),
    ("E101", "Servo Drive Alarm", "high", "CNC Machine Tool"),
    ("E102", "Control Cabinet Abnormality", "high", "Packaging Machine"),
    ("E103", "Motor Overheating", "medium", "CNC Machine Tool"),
    ("E104", "Proximity Switch Signal Abnormality", "low", "Packaging Machine"),
    ("E105", "Insufficient Pneumatic Pressure", "medium", "Air Compressor"),
    ("E106", "Conveyor Belt Misalignment", "medium", "Conveyor"),
    ("E107", "Robot Positioning Deviation", "high", "Industrial Robot"),
    ("E108", "Lubrication Pressure Abnormality", "medium", "CNC Machine Tool"),
    ("E109", "Inverter Overload", "high", "Conveyor"),
    ("E110", "Pneumatic Cylinder Abnormality", "low", "Packaging Machine"),
]

SPARE_PARTS = [
    ("SP001", "Proximity Switch", "Inductive NPN NO", "pcs"),
    ("SP002", "Servo Driver", "750W 220V", "unit"),
    ("SP003", "Contactor", "AC220V 32A", "pcs"),
    ("SP004", "Air Filter Element", "Standard", "pcs"),
    ("SP005", "Conveyor Belt", "PVC 100mm", "m"),
    ("SP006", "Gearbox Oil", "ISO VG220", "L"),
    ("SP007", "Encoder", "Incremental 1024PPR", "pcs"),
    ("SP008", "Solenoid Valve", "DC24V 5/2-Way", "pcs"),
    ("SP009", "Bearing", "6204ZZ", "pcs"),
    ("SP010", "Inverter", "5.5kW", "unit"),
]

PLANTS = ["Plant 1", "Plant 2"]
LINES = ["Line A", "Line B", "Line C", "Packaging Line", "Assembly Line"]

KNOWLEDGE = [
    (
        "Industrial Motor Bearing Vibration & Temperature Diagnostics Manual",
        KnowledgeCategoryEnum.manual,
        "Bearing wear typically presents as a concurrent rise in vibration RMS and bearing temperature. Review vibration spectrum, radial clearance, raceway condition, and lubrication, and execute shutdown inspection during the maintenance window.",
        ["Industrial Motor", "Bearing", "Vibration", "Temperature Rise"],
        "Industrial Motor",
    ),
    (
        "Industrial Motor Bearing Replacement & LOTO SOP",
        KnowledgeCategoryEnum.sop,
        "Before bearing overhaul, verify maintenance window, execute shutdown, de-energization, zero-energy verification, and LOTO. Following replacement, perform alignment, lubrication, no-load test, load test, and vibration re-measurement.",
        ["Industrial Motor", "Bearing", "LOTO", "Replacement"],
        "Industrial Motor",
    ),
    (
        "E101 Servo Drive Alarm Troubleshooting Guide",
        KnowledgeCategoryEnum.fault_code,
        "When CNC machine tool triggers an E101 servo drive alarm, root causes typically involve driver overload, encoder feedback anomaly, or lost drive parameters. Steps: 1. Record drive alarm code; 2. Measure motor insulation resistance; 3. Inspect encoder cable and connectors; 4. Reset drive parameters if necessary. Safety notice: Wait 5 minutes after de-energization for capacitor discharge before servicing.",
        ["Servo", "E101", "Driver"],
        "CNC Machine Tool",
    ),
    (
        "Packaging Machine Proximity Switch Maintenance SOP",
        KnowledgeCategoryEnum.sop,
        "Clean packaging machine proximity switches weekly and inspect mechanical mounting firmness monthly. Loose mounting leads to E104 signal abnormality. When replacing, ensure exact model match with 2mm sensing distance.",
        ["Proximity Switch", "E104", "Packaging Machine"],
        "Packaging Machine",
    ),
    (
        "Control Cabinet Electrical Safety Operating Procedures",
        KnowledgeCategoryEnum.safety,
        "Before working inside control cabinets, execute Lockout/Tagout (LOTO): 1. De-energize main breaker and apply padlock; 2. Verify zero voltage with calibrated multimeter; 3. Discharge residual energy; 4. Remove lock only by the person who applied it upon completion. Never work live; never bypass safety interlocks.",
        ["Safety", "LOTO", "Electrical"],
        None,
    ),
    (
        "Air Compressor Low Pressure Troubleshooting Experience",
        KnowledgeCategoryEnum.experience,
        "Common causes for low compressed air pressure: clogged intake filter, safety valve leakage, loose pneumatic fittings. First check filter differential pressure, then listen for audible leaks around valve assemblies. Replacing the intake filter element generally restores normal pressure.",
        ["Pneumatic", "E105", "Air Compressor"],
        "Air Compressor",
    ),
    (
        "Conveyor Belt Tracking and Alignment Procedure",
        KnowledgeCategoryEnum.experience,
        "Principle for correcting conveyor belt misalignment (E106): tighten the side the belt tracks toward. Loosen tensioner bolts, make incremental adjustments to both sides, run no-load for 10 minutes to observe tracking, then verify under load.",
        ["Tracking", "E106", "Conveyor"],
        "Conveyor",
    ),
    (
        "Industrial Robot Positioning Deviation Calibration SOP",
        KnowledgeCategoryEnum.sop,
        "When an industrial robot presents positioning deviation (E107): 1. Check if mastering/zero position data is lost; 2. Execute zero-point calibration; 3. Calibrate tool center point (TCP) coordinate system; 4. Re-run test trajectory to verify repeatability.",
        ["Robot", "E107", "Positioning"],
        "Industrial Robot",
    ),
    (
        "Lubrication System Pressure Abnormality Diagnostics",
        KnowledgeCategoryEnum.case,
        "CNC machine tool lubrication pressure anomaly E108 resolved: inspection revealed oil pump strainer blockage causing insufficient delivery. Cleaned strainer and changed lubricant to restore rated pressure. Recommend quarterly lubricant replacement.",
        ["Lubrication", "E108"],
        "CNC Machine Tool",
    ),
    (
        "Variable Frequency Drive Overload Case Analysis",
        KnowledgeCategoryEnum.case,
        "Conveyor inverter frequently tripped on overload E109. Root cause was seized bearing on the driven side causing motor current spike. Replaced bearing 6204ZZ to resolve the fault permanently.",
        ["Inverter", "E109", "Overload"],
        "Conveyor",
    ),
    (
        "Preventive Maintenance Plan Template",
        KnowledgeCategoryEnum.sop,
        "Equipment preventive maintenance intervals: daily inspection, weekly cleaning, monthly lubrication, quarterly precision check, annual overhaul. Maintain equipment logs and track compliance rigorously.",
        ["Preventive Maintenance", "PM"],
        None,
    ),
    (
        "Lockout/Tagout (LOTO) Standard Procedure",
        KnowledgeCategoryEnum.safety,
        "Six-step LOTO procedure: Notify, Shut down, Isolate, Lockout/Tagout, Release stored energy, Verify zero energy. Reverse sequence upon completion. LOTO must be completed before any maintenance begins.",
        ["LOTO", "Safety"],
        None,
    ),
    (
        "E103 Motor Overheating Handling SOP",
        KnowledgeCategoryEnum.fault_code,
        "Common causes for motor overheating E103: sustained overload, cooling fan failure, bearing wear, excessive ambient temperature. Check load ratio, measure bearing vibration, and clean air cooling ducts.",
        ["E103", "Motor", "Temperature"],
        "CNC Machine Tool",
    ),
    (
        "Pneumatic Cylinder Motion Abnormality Troubleshooting",
        KnowledgeCategoryEnum.fault_code,
        "Cylinder motion abnormality E110: verify pneumatic supply pressure, solenoid valve spool switching, and cylinder rod seals. Frequently caused by internal seal aging and bypass leakage; replace seal kit to resolve.",
        ["E110", "Pneumatic Cylinder"],
        "Packaging Machine",
    ),
    (
        "Equipment QR Code Management Guidelines",
        KnowledgeCategoryEnum.experience,
        "Each physical asset is assigned a unique QR code. Scanning the code opens the equipment profile with historical work orders and maintenance records for rapid on-site asset identification.",
        ["QR Code", "Asset Management"],
        None,
    ),
    (
        "Maintenance Log Reporting Standards",
        KnowledgeCategoryEnum.sop,
        "Maintenance logs must include: findings, root cause, corrective actions, replaced parts, test results, and labor hours. Use objective, professional terminology. AI-assisted polishing may be used while preserving factual integrity.",
        ["Maintenance Log", "Standard"],
        None,
    ),
    (
        "Work Order Acceptance Criteria & Return Handling",
        KnowledgeCategoryEnum.sop,
        "Work orders are inspected by supervisors upon completion. Acceptance criteria: all mandatory fields complete, testing verified, equipment restored to operating state. Incomplete orders are rejected with specific notes for technician rework.",
        ["Acceptance", "Standard"],
        None,
    ),
]

# (Fault description template, Fault code, Equipment type)
FAULT_TEMPLATES = [
    ("{eq} servo drive alarm E101, unable to start", "E101", "CNC Machine Tool"),
    ("{eq} control cabinet abnormal noise, display shows E102", "E102", "Packaging Machine"),
    ("{eq} spindle motor overheating E103", "E103", "CNC Machine Tool"),
    ("{eq} proximity switch signal abnormal E104, unstable detection", "E104", "Packaging Machine"),
    ("{eq} insufficient air pressure E105, cannot reach operating pressure", "E105", "Air Compressor"),
    ("{eq} conveyor belt tracking misalignment E106", "E106", "Conveyor"),
    ("{eq} robot positioning deviation E107", "E107", "Industrial Robot"),
    ("{eq} lubrication system pressure abnormal E108", "E108", "CNC Machine Tool"),
    ("{eq} inverter overload E109", "E109", "Conveyor"),
    ("{eq} pneumatic cylinder motion abnormal E110", "E110", "Packaging Machine"),
]

ROOT_CAUSES = {
    "E101": "Loose encoder wiring on servo driver leading to feedback signal anomaly",
    "E102": "Contact erosion on contactor inside control cabinet generating buzzing noise",
    "E103": "Defective motor cooling fan resulting in excessive temperature rise",
    "E104": "Loose proximity switch bracket causing sensing distance drift",
    "E105": "Clogged intake filter element resulting in insufficient air intake",
    "E106": "Uneven belt tension on both sides causing belt tracking drift",
    "E107": "Lost robot mastering zero position causing coordinate positioning error",
    "E108": "Clogged lubrication pump strainer causing low oil delivery pressure",
    "E109": "Bearing seizure on driven side causing inverter current overload",
    "E110": "Aged pneumatic cylinder seals causing internal pressure bypass",
}

ACTIONS = {
    "E101": "Re-tightened encoder wiring terminals and reset servo drive parameters",
    "E102": "Replaced eroded contactor and cleaned electrical contact surfaces",
    "E103": "Replaced cooling fan assembly and cleaned motor heat sinks",
    "E104": "Re-tightened proximity switch mounting bracket and calibrated sensing gap",
    "E105": "Replaced air filter element and verified pneumatic line seals",
    "E106": "Adjusted belt tensioners on both sides and verified no-load tracking",
    "E107": "Executed robot zero-point mastering and re-calibrated TCP tool coordinate system",
    "E108": "Cleaned lubrication pump strainer and replaced ISO VG220 gear oil",
    "E109": "Replaced driven side bearing 6204ZZ and verified free rotation",
    "E110": "Replaced pneumatic cylinder seal kit and verified smooth stroke",
}

PARTS_USED = {
    "E101": "Encoder Terminal Block",
    "E102": "Contactor AC220V 32A",
    "E103": "Cooling Fan Assembly",
    "E104": "Proximity Switch",
    "E105": "Air Filter Element",
    "E106": "",
    "E107": "",
    "E108": "Gearbox Oil ISO VG220",
    "E109": "Bearing 6204ZZ",
    "E110": "Cylinder Seal Kit",
}


def _wo_code(db: Session, i: int) -> str:
    year = datetime.now(UTC).year
    return f"WO-{year}-{i:04d}"


def run_seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        _seed(db)
        db.commit()
        print("[seed] Demo data initialization complete")
    except Exception as e:
        db.rollback()
        print(f"[seed] Demo data initialization failed: {e}")
    finally:
        db.close()


def _seed(db: Session) -> None:
    random.seed(42)
    # Users
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password(DEMO_PASSWORD),
        full_name="System Administrator",
        phone="13800000001",
        role="admin",
    )  # type: ignore[arg-type]
    sup = User(
        email="supervisor@example.com",
        hashed_password=hash_password(DEMO_PASSWORD),
        full_name="Supervisor Zhang",
        phone="13800000002",
        role="supervisor",
    )  # type: ignore[arg-type]
    techs_data = [
        ("tech@example.com", "Demo Engineer", "Electrical Maintenance,PLC Programming,Servo Tuning"),
        ("tech1@example.com", "Engineer Li", "Electrical Maintenance,PLC Programming,Servo Tuning"),
        ("tech2@example.com", "Engineer Wang", "Mechanical Maintenance,Pneumatics & Hydraulics,Welding"),
        ("tech3@example.com", "Engineer Zhao", "Robot Maintenance,PLC Programming"),
        ("tech4@example.com", "Engineer Chen", "Electrical Maintenance,Instrumentation & Calibration"),
        ("tech5@example.com", "Engineer Liu", "Mechanical Maintenance,Pneumatics & Hydraulics"),
    ]
    db.add_all([admin, sup])
    db.flush()
    techs: list[User] = []
    for email, name, skills in techs_data:
        u = User(
            email=email,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name=name,
            phone=f"1380000001{len(techs) + 3}",
            role="technician",
        )  # type: ignore[arg-type]
        db.add(u)
        db.flush()
        techs.append(u)
        profile = TechnicianProfile(
            user_id=u.id,
            employee_no=f"T{len(techs):03d}",
            availability="available",
            max_concurrent=5,
        )
        db.add(profile)
        db.flush()
        for sn in skills.split(","):
            sk = db.query(Skill).filter(Skill.name == sn.strip()).first()
            if not sk:
                sk = Skill(name=sn.strip(), category="Maintenance Skills")
                db.add(sk)
                db.flush()
            profile.skills.append(sk)

    # Equipment Types
    type_map: dict[str, EquipmentType] = {}
    for name, desc in EQUIPMENT_TYPES:
        t = EquipmentType(name=name, description=desc, created_by=str(admin.id))
        db.add(t)
        db.flush()
        type_map[name] = t

    # Fault Codes
    fc_map: dict[str, FaultCode] = {}
    for code, name, sev, etype in FAULT_CODES:
        fc = FaultCode(
            code=code,
            name=name,
            severity=sev,
            equipment_type_id=type_map.get(etype).id if type_map.get(etype) else None,
        )
        db.add(fc)
        db.flush()
        fc_map[code] = fc

    # Spare Parts
    sp_map: dict[str, SparePart] = {}
    for code, name, spec, unit in SPARE_PARTS:
        sp = SparePart(
            code=code,
            name=name,
            specification=spec,
            unit=unit,
            stock_qty=random.randint(5, 50),
        )
        db.add(sp)
        db.flush()
        sp_map[code] = sp

    # Equipment 20 units
    import uuid

    PREFIX_MAP = {
        "Industrial Motor": "MTR",
        "CNC Machine Tool": "CNC",
        "Packaging Machine": "PKG",
        "Air Compressor": "AIR",
        "Conveyor": "CNV",
        "Industrial Robot": "RBT",
    }

    equipment_list: list[Equipment] = []
    eq_names = {
        "Industrial Motor": [
            "Drive Motor A1",
            "Main Spindle Motor A2",
            "Conveyor Motor B1",
            "Circulation Pump Motor B2",
            "Blower Motor C1",
        ],
        "CNC Machine Tool": [
            "CNC Machining Center",
            "CNC Lathe",
            "Vertical Machining Center",
            "Gantry Machining Center",
            "CNC Milling Machine",
        ],
        "Packaging Machine": ["Automatic Packaging Machine", "Vertical Packaging Machine", "Packaging Machine #3", "Granule Packaging Machine"],
        "Air Compressor": ["Screw Air Compressor", "Piston Air Compressor"],
        "Conveyor": ["Roller Conveyor Line", "Belt Conveyor", "Slat Conveyor"],
        "Industrial Robot": ["Welding Robot", "Handling Robot", "Assembly Robot"],
    }
    statuses_pool = (
        [EquipmentStatusEnum.running] * 14
        + [EquipmentStatusEnum.fault] * 3
        + [EquipmentStatusEnum.under_repair] * 2
        + [EquipmentStatusEnum.stopped] * 1
    )
    eq_idx = 0
    for etype, names in eq_names.items():
        for i, n in enumerate(names):
            eq = Equipment(
                code=f"EQ-{PREFIX_MAP[etype]}{i + 1:02d}",
                name=f"{n}",
                equipment_type_id=type_map[etype].id,
                plant=random.choice(PLANTS),
                production_line=random.choice(LINES),
                location=f"{random.choice(PLANTS)} Workshop {random.randint(1, 3)}",
                manufacturer=random.choice(["Siemens", "Mitsubishi", "FANUC", "ABB", "Domestic OEM"]),
                model=f"Model-{etype[:2].upper()}{i + 100}",
                serial_number=f"SN{2024000 + eq_idx}",
                commissioning_date=datetime(
                    2021, random.randint(1, 12), random.randint(1, 28)
                ).date(),
                status=statuses_pool[eq_idx % len(statuses_pool)],
                risk_level=random.choice(
                    [RiskLevelEnum.low, RiskLevelEnum.medium, RiskLevelEnum.high]
                ),
                health_score=round(random.uniform(72, 98), 1),
                rated_parameters={
                    "rated_power_kw": 18.5 if etype == "Industrial Motor" else None,
                    "rated_voltage_v": 380 if etype == "Industrial Motor" else None,
                    "rated_current_a": 36 if etype == "Industrial Motor" else None,
                    "rated_speed_rpm": 1480 if etype == "Industrial Motor" else None,
                },
                cumulative_runtime_hours=round(random.uniform(3000, 18000), 1),
                responsible_person_id=random.choice(techs).id,
                qr_token=uuid.uuid4().hex,
                last_maintenance_at=(
                    datetime.now(UTC) - timedelta(days=random.randint(5, 90))
                ).date(),
                next_maintenance_at=(
                    datetime.now(UTC) + timedelta(days=random.randint(10, 90))
                ).date(),
                created_by=str(admin.id),
            )
            db.add(eq)
            db.flush()
            equipment_list.append(eq)
            eq_idx += 1

    # Knowledge Articles
    knowledge_by_title: dict[str, KnowledgeArticle] = {}
    for title, cat, content, tags, etype in KNOWLEDGE:
        art = KnowledgeArticle(
            title=title,
            category=cat,
            content=content,
            summary=content[:60],
            tags=tags,
            equipment_type_id=type_map[etype].id if etype in type_map else None,
            source="Internal Knowledge Base",
            author_id=admin.id,
            status="published",
            created_by=str(admin.id),
        )
        db.add(art)
        knowledge_by_title[title] = art
    db.flush()

    # Historical Work Orders: 30 completed
    wo_counter = 0
    for _i in range(30):
        tpl, fcc, etype = random.choice(FAULT_TEMPLATES)
        eqs_of_type = [
            e for e in equipment_list if e.equipment_type_id == type_map[etype].id
        ]
        if not eqs_of_type:
            continue
        eq = random.choice(eqs_of_type)
        tech = random.choice(techs)
        days_ago = random.randint(10, 180)
        created = datetime.now(UTC) - timedelta(days=days_ago)
        start = created + timedelta(hours=random.randint(1, 8))
        end = start + timedelta(hours=random.randint(1, 12))
        wo_counter += 1
        wo = WorkOrder(
            code=_wo_code(db, wo_counter),
            title=f"{eq.name} {fcc} Fault Repair",
            equipment_id=eq.id,
            fault_description=tpl.format(eq=eq.name),
            fault_code_id=fc_map[fcc].id,
            order_type=WorkOrderTypeEnum.fault_repair,
            priority=random.choice(list(PriorityEnum)),
            status=WorkOrderStatusEnum.completed,
            created_by_id=sup.id,
            assignee_id=tech.id,
            actual_start_at=start,
            actual_end_at=end,
            planned_end_at=start + timedelta(hours=8),
            root_cause=ROOT_CAUSES[fcc],
            action_taken=ACTIONS[fcc],
            replaced_parts=PARTS_USED[fcc] or None,
            test_result="No-load and load tests passed; equipment returned to normal operation",
            equipment_status_after="running",
            follow_up_advice="Recommend enhanced routine inspection, monitor this component closely",
            needs_observation=random.choice([True, False]),
            safety_risk="De-energization and Lockout/Tagout (LOTO) executed",
            created_by=str(sup.id),
            created_at=created,
        )
        db.add(wo)
        db.flush()
        db.add(
            WorkOrderAssignment(
                work_order_id=wo.id,
                assignee_id=tech.id,
                assigned_by=sup.id,
                assigned_at=created,
                is_current=False,
            )
        )
        db.add(
            WorkOrderStatusHistory(
                work_order_id=wo.id,
                from_status=None,
                to_status="pending_dispatch",
                changed_by=sup.id,
                changed_at=created,
            )
        )
        # Maintenance Logs
        db.add(
            MaintenanceLog(
                work_order_id=wo.id,
                log_type=MaintenanceLogTypeEnum.inspect,
                content=f"Arrived at site, confirmed fault symptoms on {eq.name}, read fault code {fcc}",
                operator_id=tech.id,
                operator_name=tech.full_name,
                logged_at=start,
            )
        )
        db.add(
            MaintenanceLog(
                work_order_id=wo.id,
                log_type=MaintenanceLogTypeEnum.repair,
                content=ACTIONS[fcc],
                operator_id=tech.id,
                operator_name=tech.full_name,
                logged_at=start + timedelta(hours=1),
            )
        )
        db.add(
            MaintenanceLog(
                work_order_id=wo.id,
                log_type=MaintenanceLogTypeEnum.test,
                content="Completed no-load and load testing; equipment operation returned to normal",
                operator_id=tech.id,
                operator_name=tech.full_name,
                logged_at=end,
            )
        )
        # Labor
        db.add(
            LaborEntry(
                work_order_id=wo.id,
                started_at=start,
                ended_at=end,
                hours=round((end - start).total_seconds() / 3600, 1),
                is_downtime=random.choice([True, False]),
                operator_id=tech.id,
                operator_name=tech.full_name,
            )
        )
        # Spare parts
        if PARTS_USED[fcc]:
            db.add(
                WorkOrderSparePart(
                    work_order_id=wo.id,
                    spare_part_code=random.choice(list(sp_map.keys())),
                    spare_part_name=random.choice(list(sp_map.values())).name,
                    quantity=random.randint(1, 3),
                    unit="pcs",
                )
            )

    # 8 Unfinished Work Orders across statuses
    unfinished_statuses = [
        WorkOrderStatusEnum.pending_dispatch,
        WorkOrderStatusEnum.assigned,
        WorkOrderStatusEnum.accepted,
        WorkOrderStatusEnum.in_progress,
        WorkOrderStatusEnum.in_progress,
        WorkOrderStatusEnum.pending_acceptance,
        WorkOrderStatusEnum.returned,
        WorkOrderStatusEnum.paused,
    ]
    for i, st in enumerate(unfinished_statuses):
        tpl, fcc, etype = FAULT_TEMPLATES[i % len(FAULT_TEMPLATES)]
        eqs_of_type = [
            e for e in equipment_list if e.equipment_type_id == type_map[etype].id
        ]
        if not eqs_of_type:
            eq = random.choice(equipment_list)
        else:
            eq = random.choice(eqs_of_type)
        # Keep the public technician account useful after every deterministic reset.
        tech = techs[(i - 1) % len(techs)] if i else techs[0]
        created = datetime.now(UTC) - timedelta(days=random.randint(0, 5))
        wo_counter += 1
        priority = (
            PriorityEnum.P1
            if i < 2
            else random.choice([PriorityEnum.P2, PriorityEnum.P3])
        )
        wo = WorkOrder(
            code=_wo_code(db, wo_counter),
            title=f"{eq.name} {fcc} Fault Repair",
            equipment_id=eq.id,
            fault_description=tpl.format(eq=eq.name),
            fault_code_id=fc_map[fcc].id,
            order_type=WorkOrderTypeEnum.fault_repair,
            priority=priority,
            status=st,
            created_by_id=sup.id,
            assignee_id=tech.id if st != WorkOrderStatusEnum.pending_dispatch else None,
            planned_end_at=datetime.now(UTC) + timedelta(hours=random.randint(4, 48)),
            actual_start_at=datetime.now(UTC) - timedelta(hours=2)
            if st
            in [
                WorkOrderStatusEnum.in_progress,
                WorkOrderStatusEnum.pending_acceptance,
                WorkOrderStatusEnum.returned,
                WorkOrderStatusEnum.paused,
            ]
            else None,
            safety_risk="Involves electrical work; power must be disconnected and LOTO executed before maintenance"
            if "E101" in fcc or "E102" in fcc
            else None,
            created_by=str(sup.id),
            created_at=created,
            root_cause=ROOT_CAUSES[fcc]
            if st == WorkOrderStatusEnum.pending_acceptance
            else None,
            action_taken=ACTIONS[fcc]
            if st == WorkOrderStatusEnum.pending_acceptance
            else None,
            test_result="Testing passed"
            if st == WorkOrderStatusEnum.pending_acceptance
            else None,
            equipment_status_after="running"
            if st == WorkOrderStatusEnum.pending_acceptance
            else None,
            rejection_reason="Test results unclear; please provide load testing data"
            if st == WorkOrderStatusEnum.returned
            else None,
            submitted_at=datetime.now(UTC) - timedelta(hours=1)
            if st == WorkOrderStatusEnum.pending_acceptance
            else None,
        )
        db.add(wo)
        db.flush()
        # Checklist
        default_checklist = [
            "Confirm equipment is shut down",
            "Execute de-energization",
            "Execute Lockout/Tagout (LOTO)",
            "Verify residual energy dissipation",
            "Read fault codes",
            "Inspect relevant components",
            "Perform maintenance work",
            "Restore power and perform operational test",
        ]
        for j, content in enumerate(default_checklist):
            db.add(
                WorkOrderChecklistItem(
                    work_order_id=wo.id,
                    content=content,
                    order=j,
                    is_required=True,
                    is_completed=st
                    in [
                        WorkOrderStatusEnum.in_progress,
                        WorkOrderStatusEnum.pending_acceptance,
                    ]
                    and j < 4,
                )
            )
        db.add(
            WorkOrderStatusHistory(
                work_order_id=wo.id,
                from_status=None,
                to_status="pending_dispatch",
                changed_by=sup.id,
                changed_at=created,
            )
        )
        if st != WorkOrderStatusEnum.pending_dispatch:
            db.add(
                MaintenanceLog(
                    work_order_id=wo.id,
                    log_type=MaintenanceLogTypeEnum.inspect,
                    content=f"Confirmed fault symptoms, read fault code {fcc}",
                    operator_id=tech.id,
                    operator_name=tech.full_name,
                    logged_at=datetime.now(UTC) - timedelta(hours=3),
                )
            )
        # Associated fault report
        fr = FaultReport(
            equipment_id=eq.id,
            title=f"{eq.name} {fcc} Fault",
            description=tpl.format(eq=eq.name),
            occurred_at=created,
            is_downtime="stop" in tpl.lower() or "unable" in tpl.lower() or "cannot" in tpl.lower(),
            affects_production="line" in tpl.lower(),
            has_safety_risk="noise" in tpl.lower() or "abnormal" in tpl.lower(),
            urgency=UrgencyEnum.high
            if priority == PriorityEnum.P1
            else UrgencyEnum.medium,
            status=FaultReportStatusEnum.converted,
            reporter_name=random.choice(techs).full_name,
            created_by=str(sup.id),
            fault_code_id=fc_map[fcc].id,
        )
        db.add(fr)
        wo.fault_report_id = fr.id

    # Industrial motor telemetry, predictive risk, and automated work orders
    motors = [
        item
        for item in equipment_list
        if item.equipment_type_id == type_map["Industrial Motor"].id
    ]
    now = datetime.now(UTC)
    scenarios = [
        ("normal", 1.8, 56.0, 18.0, 380.0, 62.0),
        ("bearing_wear", 6.8, 78.0, 20.0, 380.0, 68.0),
        ("temperature_rise", 3.2, 84.0, 21.0, 379.0, 72.0),
        ("voltage_fluctuation", 2.0, 58.0, 19.0, 425.0, 64.0),
        ("current_overload", 2.8, 72.0, 32.0, 376.0, 109.0),
    ]
    for motor_index, motor in enumerate(motors):
        scenario, vibration, temperature, current, voltage, load = scenarios[
            motor_index
        ]
        for point in range(24):
            progress = point / 23
            db.add(
                TelemetryRecord(
                    equipment_id=motor.id,
                    collected_at=now - timedelta(minutes=(23 - point) * 5),
                    vibration_rms=round(
                        1.7
                        + progress * (vibration - 1.7)
                        + random.uniform(-0.08, 0.08),
                        2,
                    ),
                    bearing_temperature=round(
                        55 + progress * (temperature - 55) + random.uniform(-0.4, 0.4),
                        2,
                    ),
                    motor_current=round(
                        18 + progress * (current - 18) + random.uniform(-0.2, 0.2),
                        2,
                    ),
                    motor_voltage=round(
                        380 + progress * (voltage - 380) + random.uniform(-1, 1),
                        2,
                    ),
                    rotational_speed=round(1480 + random.uniform(-7, 7), 2),
                    load_ratio=round(
                        62 + progress * (load - 62) + random.uniform(-0.8, 0.8),
                        2,
                    ),
                    ambient_temperature=round(26 + random.uniform(-0.5, 0.5), 2),
                    cumulative_runtime_hours=motor.cumulative_runtime_hours
                    + point / 12,
                    scenario=scenario,
                    quality=1.0,
                    is_anomaly=motor_index > 0 and point >= 18,
                    anomaly_metrics=(
                        ["Vibration RMS", "Bearing Temperature"]
                        if motor_index in {1, 2}
                        else ["Motor Voltage"]
                        if motor_index == 3
                        else ["Motor Current", "Load Ratio"]
                        if motor_index == 4
                        else []
                    ),
                )
            )

        motor.health_score = [96.0, 58.0, 64.0, 74.0, 52.0][motor_index]
        motor.risk_level = [
            RiskLevelEnum.low,
            RiskLevelEnum.high,
            RiskLevelEnum.high,
            RiskLevelEnum.medium,
            RiskLevelEnum.critical,
        ][motor_index]
        motor.status = (
            EquipmentStatusEnum.running
            if motor_index == 0
            else EquipmentStatusEnum.warning
            if motor_index < 4
            else EquipmentStatusEnum.fault
        )
        sensor_values = {
            "vibration_rms": ("Vibration RMS", "mm/s", vibration),
            "bearing_temperature": ("Bearing Temperature", "°C", temperature),
            "motor_current": ("Motor Current", "A", current),
            "motor_voltage": ("Motor Voltage", "V", voltage),
            "load_ratio": ("Load Ratio", "%", load),
        }
        for metric, (sensor_name, unit, latest_value) in sensor_values.items():
            db.add(
                EquipmentSensor(
                    equipment_id=motor.id,
                    code=f"{motor.code}-{metric.upper()}",
                    name=sensor_name,
                    metric_type=metric,
                    unit=unit,
                    status="online",
                    latest_value=latest_value,
                    last_seen_at=now,
                )
            )

    predictive_motor = motors[1]
    anomaly = AnomalyEvent(
        equipment_id=predictive_motor.id,
        fault_type="bearing_wear",
        title="Bearing Wear Trend",
        severity=RiskLevelEnum.high,
        status="open",
        evidence={"Vibration RMS": 6.8, "Bearing Temperature": 78.0},
        diagnosis_summary="Vibration and temperature trends deteriorating simultaneously; high probability of bearing wear.",
        confidence=0.91,
        detected_at=now,
    )
    db.add(anomaly)
    db.flush()
    diagnosis = FaultDiagnosis(
        equipment_id=predictive_motor.id,
        anomaly_event_id=anomaly.id,
        fault_type="bearing_wear",
        summary=anomaly.diagnosis_summary,
        possible_causes=["Raceway or rolling element wear", "Lubrication degradation", "Bearing clearance anomaly"],
        evidence=anomaly.evidence,
        rag_citations=[
            {
                "article_id": knowledge_by_title["Industrial Motor Bearing Vibration & Temperature Diagnostics Manual"].id,
                "title": "Industrial Motor Bearing Vibration & Temperature Diagnostics Manual",
                "source": "Internal Knowledge Base",
                "score": 0.93,
            },
            {
                "article_id": knowledge_by_title["Industrial Motor Bearing Replacement & LOTO SOP"].id,
                "title": "Industrial Motor Bearing Replacement & LOTO SOP",
                "source": "Internal Knowledge Base",
                "score": 0.81,
            },
        ],
        confidence=0.91,
        requires_human_review=False,
        generated_at=now,
    )
    db.add(diagnosis)
    db.flush()
    prediction = RiskPrediction(
        equipment_id=predictive_motor.id,
        anomaly_event_id=anomaly.id,
        risk_level=RiskLevelEnum.high,
        failure_mode="bearing_wear",
        probability=0.82,
        remaining_useful_life_hours=36,
        predicted_failure_at=now + timedelta(hours=36),
        maintenance_window_start=now,
        maintenance_window_end=now + timedelta(hours=18),
        factors=["Vibration RMS", "Bearing Temperature"],
        is_mock=True,
    )
    db.add(prediction)
    db.flush()
    recommendation = MaintenanceRecommendation(
        equipment_id=predictive_motor.id,
        prediction_id=prediction.id,
        title=f"{predictive_motor.name}: Bearing Wear Trend",
        strategy="Plan downtime to inspect bearing clearance and lubrication status; replace bearing and verify alignment if necessary.",
        priority="P2",
        required_skills=["Mechanical Maintenance", "Instrumentation & Calibration"],
        required_parts=[
            {"name": "Bearing", "available": True, "stock_qty": sp_map["SP009"].stock_qty}
        ],
        risk_operations=["shutdown", "reset_alarm", "restart"],
        dispatch_suggestion={
            "recommended_technician_id": techs[1].id,
            "technicians": [
                {"user_id": techs[1].id, "name": techs[1].full_name, "score": 37}
            ],
        },
        status="work_order_created",
        generated_at=now,
    )
    db.add(recommendation)
    db.flush()
    wo_counter += 1
    predictive_wo = WorkOrder(
        code=_wo_code(db, wo_counter),
        title="[Predictive Maintenance] Bearing Wear Trend",
        equipment_id=predictive_motor.id,
        fault_description="Automatically created from telemetry trend: vibration RMS and bearing temperature increasing continuously.",
        order_type=WorkOrderTypeEnum.preventive,
        priority=PriorityEnum.P2,
        status=WorkOrderStatusEnum.assigned,
        assignee_id=techs[1].id,
        planned_start_at=now,
        planned_end_at=now + timedelta(hours=18),
        safety_risk="Involves rotating machinery and electrical energy; shutdown, de-energization, verification, and LOTO must be executed.",
        ai_diagnosis_summary=anomaly.diagnosis_summary,
        maintenance_steps=[
            "Execute LOTO",
            "Inspect bearing and lubrication",
            "Replace bearing if necessary",
            "Acquire post-maintenance telemetry",
        ],
        acceptance_criteria="Vibration RMS < 4.5 mm/s, bearing temperature < 75°C, health score >= 80.",
        created_by="maintenance-agent",
    )
    db.add(predictive_wo)
    db.flush()
    recommendation.auto_work_order_id = predictive_wo.id
    reservation = SparePartReservation(
        recommendation_id=recommendation.id,
        work_order_id=predictive_wo.id,
        spare_part_id=sp_map["SP009"].id,
        requested_name="Bearing",
        requested_qty=1,
        reserved_qty=1,
        shortage_qty=0,
        status="reserved",
        reserved_at=now,
    )
    db.add(reservation)
    recommendation.required_parts = [
        {
            "name": "Bearing",
            "spare_part_id": sp_map["SP009"].id,
            "stock_qty": sp_map["SP009"].stock_qty,
            "available": True,
            "requested_qty": 1,
            "reserved_qty": 1,
            "shortage_qty": 0,
            "reservation_status": "reserved",
        }
    ]
    agent_run = AgentRun(
        equipment_id=predictive_motor.id,
        anomaly_event_id=anomaly.id,
        goal="Diagnose equipment anomaly and generate predictive maintenance strategy",
        status="completed",
        provider="deterministic-mock",
        input={"fault_type": "bearing_wear", "evidence": anomaly.evidence},
        output={
            "diagnosis_id": diagnosis.id,
            "prediction_id": prediction.id,
            "recommendation_id": recommendation.id,
            "work_order_id": predictive_wo.id,
        },
        confidence=0.91,
        requires_human_review=False,
        started_at=now,
        finished_at=now,
    )
    db.add(agent_run)
    db.flush()
    for tool_name, response in [
        ("anomaly_detector", {"fault_type": "bearing_wear", "health_score": 58}),
        ("knowledge_search", {"citations": diagnosis.rag_citations}),
        ("risk_predictor", {"risk_level": "high", "probability": 0.82}),
        ("maintenance_strategy", {"recommendation_id": recommendation.id}),
        ("work_order_creator", {"work_order_id": predictive_wo.id}),
    ]:
        db.add(
            ToolInvocation(
                agent_run_id=agent_run.id,
                tool_name=tool_name,
                provider="local",
                status="success",
                request={"anomaly_event_id": anomaly.id},
                response=response,
                duration_ms=0,
            )
        )
    db.add(
        WorkOrderAssignment(
            work_order_id=predictive_wo.id,
            assignee_id=techs[1].id,
            assigned_by=None,
            assigned_at=now,
            is_current=True,
        )
    )
    db.add(
        WorkOrderStatusHistory(
            work_order_id=predictive_wo.id,
            from_status=None,
            to_status="assigned",
            changed_by=None,
            changed_at=now,
            remark=f"Automatically created from anomaly event #{anomaly.id}",
        )
    )
    for order, (category, content) in enumerate(
        [
            ("safety", "Equipment shut down and LOTO executed"),
            ("diagnosis", "Verify vibration and temperature trends"),
            ("repair", "Inspect bearing, lubrication, and shaft alignment"),
            ("testing", "Acquire post-maintenance telemetry and verify health score"),
        ],
        start=1,
    ):
        db.add(
            WorkOrderChecklistItem(
                work_order_id=predictive_wo.id,
                category=category,
                content=content,
                order=order,
                is_required=True,
                created_by="maintenance-agent",
            )
        )
    db.add(
        OperationApproval(
            equipment_id=predictive_motor.id,
            work_order_id=predictive_wo.id,
            recommendation_id=recommendation.id,
            command_type="shutdown",
            command_payload={"reason": "Bearing Wear Trend"},
            risk_level=RiskLevelEnum.high,
            risk_reason="Equipment shutdown affects production line and involves energy isolation; supervisor manual approval required.",
            status="pending",
            requested_by=None,
            requested_at=now,
        )
    )
