# Graph Report - industrial-maintenance-copilot-master  (2026-10-12)

## Corpus Check
- 387 files · ~231,081 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 6, .example 1, .ini 1)

## Summary
- 2866 nodes · 9027 edges · 115 communities (87 shown, 28 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 966 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Work Orders & Scheduling Endpoints
- Intelligence & Simulation Endpoints
- Web Observability & Traces UI
- Module Group 3 (apps/api/app)
- API Endpoints (app)
- Web UI Testing & Specs
- Intelligence & Simulation Endpoints
- Module Group 7 (apps/api/app)
- Web Observability & Traces UI
- Web Observability & Traces UI
- API Endpoints (app)
- Intelligence & Simulation Endpoints
- Intelligence & Simulation Endpoints
- Intelligence & Simulation Endpoints
- Module Group 14 (apps/api/app)
- Module Group 15 (apps/api/app)
- Module Group 16 (apps/api/app)
- Web Observability & Traces UI
- Dataset Preparation & ML Research Scripts
- Module Group 19 (apps/api/tests)
- Module Group 20 (apps/api/app)
- Dataset Preparation & ML Research Scripts
- API Endpoints (app)
- Module Group 23 (apps/api/tests)
- Module Group 24 (apps/api/app)
- Web UI Testing & Specs
- Module Group 26 (apps/api/app)
- Web Work Orders & Dispatch UI
- Module Group 28 (apps/api/tests)
- API Endpoints (app)
- Module Group 30 (apps/api/tests)
- Dataset Preparation & ML Research Scripts
- Equipment & Spare Parts Endpoints
- Module Group 33 (apps/api/app)
- Module Group 34 (apps/api/app)
- Module Group 35 (apps/api/app)
- API Endpoints (app)
- Module Group 37 (apps/api/app)
- Module Group 38 (apps/api/app)
- Module Group 39 (apps/api/app)
- Module Group 40 (apps/api/app)
- Web Frontend Components (41)
- Web Interactive Demo Console
- Module Group 43 (apps/api/tests)
- Web Telemetry & Realtime Monitoring
- Web UI Testing & Specs
- Dataset Preparation & ML Research Scripts
- Module Group 47 (apps/api/tests)
- API Endpoints (app)
- Module Group 49 (apps/api/tests)
- Module Group 50 (apps/api/app)
- Dataset Preparation & ML Research Scripts
- Dataset Preparation & ML Research Scripts
- Web Frontend Components (53)
- Module Group 54 (apps/api/app)
- Module Group 55 (apps/api/tests)
- Module Group 56 (apps/api/tests)
- Web UI Testing & Specs
- Web Frontend Components (58)
- Dataset Preparation & ML Research Scripts
- Dataset Preparation & ML Research Scripts
- Module Group 61 (apps/api/app)
- Module Group 62 (apps/api/tests)
- Module Group 63 (apps/api/app)
- Module Group 64 (apps/api/tests)
- Module Group 65 (apps/api/tests)
- Web Frontend Components (66)
- API Endpoints (app)
- API Endpoints (app)
- Module Group 69 (apps/api/app)
- Web Work Orders & Dispatch UI
- Dataset Preparation & ML Research Scripts
- Module Group 72 (apps/api/app)
- Dataset Preparation & ML Research Scripts
- Module Group 74 (apps/api/app)
- Web Frontend Components (75)
- Module Group 76 (apps/api/app)
- Module Group 77 (apps/api/app)
- Module Group 78 (apps/api/app)
- Web UI Testing & Specs
- Module Group 80 (apps/api/app)
- Web Frontend Components (81)
- Web Human Approval Center
- Module Group 83 (apps/api/alembic)
- Module Group 84 (apps/api/alembic)
- Module Group 85 (apps/api/alembic)
- API Endpoints (tests)
- Module Group 87 (apps/api/alembic)
- Module Group 88 (apps/api/alembic)
- Module Group 89 (apps/api/alembic)
- Web Frontend Components (90)
- Module Group 91 (apps/api/alembic)
- Module Group 92 (apps/api/app)
- Module Group 94 (apps/api/tests)
- Web Frontend Components (96)
- Web Frontend Components (97)
- Module Group 98 (apps/api/app)

## God Nodes (most connected - your core abstractions)
1. `WorkOrder` - 132 edges
2. `Equipment` - 108 edges
3. `request()` - 97 edges
4. `User` - 81 edges
5. `OpcUaGatewayService` - 75 edges
6. `WorkOrderStatusEnum` - 68 edges
7. `Base` - 64 edges
8. `RiskLevelEnum` - 55 edges
9. `TelemetryRecord` - 55 edges
10. `NodeRead` - 46 edges

## Surprising Connections (you probably didn't know these)
- `reset_demo_data()` --uses--> `Base`  [INFERRED]
  scripts/reset_demo_data.py → apps/api/app/db/session.py
- `prepare_paderborn()` --uses--> `TelemetryWindow`  [INFERRED]
  scripts/prepare_bearing_dataset.py → apps/api/app/ml/types.py
- `prepare_xjtu()` --uses--> `TelemetryWindow`  [INFERRED]
  scripts/prepare_bearing_dataset.py → apps/api/app/ml/types.py
- `prepare_paderborn_bearing()` --uses--> `TelemetryWindow`  [INFERRED]
  scripts/prepare_bearing_v2.py → apps/api/app/ml/types.py
- `prepare_xjtu_bearing()` --uses--> `TelemetryWindow`  [INFERRED]
  scripts/prepare_bearing_v2.py → apps/api/app/ml/types.py

## Import Cycles
- None detected.

## Communities (115 total, 28 thin omitted)

### Community 0 - "Work Orders & Scheduling Endpoints"
Cohesion: 0.07
Nodes (72): accept(), add_labor(), add_log(), add_spare_part(), approve(), assign(), cancel(), _create_knowledge_candidate() (+64 more)

### Community 1 - "Intelligence & Simulation Endpoints"
Cohesion: 0.05
Nodes (49): _agent_run_dict(), _anomaly_dict(), _approval_dict(), approve_operation(), configure_simulator(), create_verification(), _diagnosis_dict(), equipment_intelligence() (+41 more)

### Community 2 - "Web Observability & Traces UI"
Cohesion: 0.03
Nodes (66): ResizeObserverMock, AdminPage(), alarmPayload, mockAcknowledgeAlarm, mockAnalyzeAlarm, mockCorrelateAlarms, mockCreateAlarmWorkOrder, mockListAlarms (+58 more)

### Community 3 - "Module Group 3 (apps/api/app)"
Cohesion: 0.06
Nodes (6): get_metrics(), NodeSnapshotEntry, _event_reject_reason(), GatewaySyncResult, OpcUaGatewayService, NodeDataChange

### Community 4 - "API Endpoints (app)"
Cohesion: 0.06
Nodes (40): gateway_nodes(), gateway_status(), gateway_sync(), reload_mappings(), start_subscriptions(), stop_subscriptions(), subscription_status(), test_connect() (+32 more)

### Community 5 - "Web UI Testing & Specs"
Cohesion: 0.07
Nodes (54): config, createJestConfig, nextJest, ALL_NAV_ITEMS, AppLayout(), NavItem, ROLE_LABELS, CopilotPage() (+46 more)

### Community 6 - "Intelligence & Simulation Endpoints"
Cohesion: 0.08
Nodes (29): get_trace_detail(), metrics_summary(), observability_health(), search_trace_list(), IndustrialAlarm, AgentRun, AnomalyEvent, MaintenanceRecommendation (+21 more)

### Community 7 - "Module Group 7 (apps/api/app)"
Cohesion: 0.05
Nodes (24): _clamp(), MotorSimulator, main(), OpcUaSimulatorServer, parse_args(), _publish_all(), test_changed_nodes_tracks_discrete_transitions(), test_fault_event_sequence_is_reproducible() (+16 more)

### Community 8 - "Web Observability & Traces UI"
Cohesion: 0.07
Nodes (62): formatTime(), GatewayPage(), InfoRow(), QUALITY_LABELS, SyncStat(), MetricBox(), ObservabilityPage(), STATUS_STYLES (+54 more)

### Community 9 - "Web Observability & Traces UI"
Cohesion: 0.04
Nodes (60): STAGE_LABELS, STAGE_STYLES, TraceDetailPage(), CATEGORY_COLORS, CATEGORY_ORDER, Props, SafetyChecklist(), handleToggle() (+52 more)

### Community 10 - "API Endpoints (app)"
Cohesion: 0.08
Nodes (37): record_ai_interaction(), ask(), _build_diagnose_prompt(), _build_parse_prompt(), _build_report_prompt(), _build_safety_warnings(), _coerce_parse(), diagnose() (+29 more)

### Community 11 - "Intelligence & Simulation Endpoints"
Cohesion: 0.13
Nodes (28): Base, GatewayConnection, AIInteractionTypeEnum, AIStatusEnum, AuditMixin, KnowledgeCategoryEnum, MaintenanceLogTypeEnum, TimestampMixin (+20 more)

### Community 12 - "Intelligence & Simulation Endpoints"
Cohesion: 0.08
Nodes (31): supervisor_dashboard(), technician_dashboard(), EquipmentStatusEnum, PriorityEnum, RiskLevelEnum, WorkOrderStatusEnum, WorkOrderTypeEnum, Equipment (+23 more)

### Community 13 - "Intelligence & Simulation Endpoints"
Cohesion: 0.09
Nodes (31): acknowledge_alarm(), _alarm_out(), analyze_alarm(), correlate_active_alarms(), create_alarm_work_order(), get_alarm_analysis(), get_alarm_event(), _get_alarm_or_404() (+23 more)

### Community 14 - "Module Group 14 (apps/api/app)"
Cohesion: 0.06
Nodes (10): quality_from_status_code(), _as_utc(), _AsyncuaHandler, AsyncuaSubscriptionClient, _coerce_value(), MockSubscriptionClient, _node_id_string(), OpcUaSubscriptionClient (+2 more)

### Community 15 - "Module Group 15 (apps/api/app)"
Cohesion: 0.10
Nodes (30): find_similar_work_orders(), search_articles(), _tokenize(), TelemetrySnapshot, MaintenanceVerification, anomaly_reason(), assess_snapshot(), _create_diagnosis() (+22 more)

### Community 16 - "Module Group 16 (apps/api/app)"
Cohesion: 0.11
Nodes (26): assert_disjoint_groups(), group_split_audit(), grouped_split_from_manifest(), grouped_train_validation_test_split(), GroupedSplit, LeakageAudit, main(), main() (+18 more)

### Community 17 - "Web Observability & Traces UI"
Cohesion: 0.08
Nodes (18): alarm, waitingAnalysis, SUFFIX, DEFAULT_CREDENTIALS, loginAs(), navigateTo(), Role, switchLogin() (+10 more)

### Community 18 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.10
Nodes (16): _archive_records(), create_snapshot(), _git_sha(), main(), _read_json(), _sha256(), main(), sha256() (+8 more)

### Community 19 - "Module Group 19 (apps/api/tests)"
Cohesion: 0.09
Nodes (28): require_role(), _dep(), hash_password(), RoleEnum, require_roles(), _check(), admin_user(), another_technician() (+20 more)

### Community 20 - "Module Group 20 (apps/api/app)"
Cohesion: 0.09
Nodes (22): causal_multiscale_context(), causal_ewma(), ExperimentRun, fault_promotion(), hierarchical_fault_targets(), PaderbornAccessPolicy, _read_json(), rul_promotion() (+14 more)

### Community 21 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.14
Nodes (29): _append_bounded_history(), _channel_matches(), _consolidate_chunks(), _load_mat5_named_y_channel(), _load_paderborn_channel(), _load_split_map(), _load_xjtu_csv(), main() (+21 more)

### Community 22 - "API Endpoints (app)"
Cohesion: 0.12
Nodes (22): change_model_status(), _extract_online_features(), list_ml_predictions(), list_models(), online_inference(), _risk_level(), rollback(), active_model() (+14 more)

### Community 23 - "Module Group 23 (apps/api/tests)"
Cohesion: 0.08
Nodes (6): _make_wo(), TestChecklistItems, TestLaborEntries, TestMaintenanceLogs, TestSpareParts, TestWorkOrderStartRepair

### Community 24 - "Module Group 24 (apps/api/app)"
Cohesion: 0.10
Nodes (15): NodeRead, RejectedRead, convert_value(), DataQualityLayer, normalize_unit(), QualityReport, UnitConversionError, initial_provider() (+7 more)

### Community 25 - "Web UI Testing & Specs"
Cohesion: 0.07
Nodes (32): FaultReportDetail(), ImpactBadge(), FlagToggle(), NewFaultReport(), FaultReportList(), convertFaultReportToWorkOrder(), createFaultReport(), getFaultReport() (+24 more)

### Community 26 - "Module Group 26 (apps/api/app)"
Cohesion: 0.08
Nodes (9): _as_utc(), AsyncuaOpcUaClient, _coerce_value(), MockOpcUaClient, _BadQualityClient, test_asyncua_client_is_lazy_and_read_only(), test_mock_client_rejects_write_operations(), test_mock_opcua_client_connect_and_read() (+1 more)

### Community 27 - "Web Work Orders & Dispatch UI"
Cohesion: 0.11
Nodes (31): Info(), PriorityBadge(), WorkOrderDetail(), AcceptancePanel(), handleApprove(), handleReject(), Props, CompletionValidationDisplay() (+23 more)

### Community 28 - "Module Group 28 (apps/api/tests)"
Cohesion: 0.12
Nodes (22): client(), _sha256(), test_paderborn_audit_accepts_complete_traceable_fixture(), test_paderborn_channel_falls_back_to_strict_mat5_reader(), fail_general_decode(), test_paderborn_download_rejects_an_existing_checksum_mismatch(), test_paderborn_download_resumes_to_an_atomic_destination(), test_paderborn_fallback_returns_an_early_named_channel() (+14 more)

### Community 29 - "API Endpoints (app)"
Cohesion: 0.10
Nodes (7): login(), me(), is_demo_account(), get_current_user(), decode_access_token(), verify_password(), get_db()

### Community 30 - "Module Group 30 (apps/api/tests)"
Cohesion: 0.13
Nodes (20): bind_trace(), current_context(), current_trace_id(), new_trace_id(), start_trace(), trace_attributes(), TraceContext, test_asyncio_child_bind_does_not_leak_to_parent() (+12 more)

### Community 31 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.14
Nodes (19): main(), _aggregate_importance(), Candidate, _candidates(), _complexity(), _evaluate_family(), _git_sha(), _is_ancestor() (+11 more)

### Community 32 - "Equipment & Spare Parts Endpoints"
Cohesion: 0.16
Nodes (24): by_qr(), create_equipment(), create_fault_code(), create_spare_part(), create_type(), equipment_qrcode(), equipment_work_orders(), get_equipment() (+16 more)

### Community 33 - "Module Group 33 (apps/api/app)"
Cohesion: 0.11
Nodes (16): build_alarm_message(), evaluate_alarm_state(), load_all_mappings(), load_mappings(), MappingSeedResult, NodeMapping, seed_mappings_from_config(), snapshot_field_for() (+8 more)

### Community 34 - "Module Group 34 (apps/api/app)"
Cohesion: 0.14
Nodes (18): feature_definitions(), main(), _optional_datetime(), _optional_string(), _read_json(), _register_feature_definitions(), _sha256(), _immutable_prediction() (+10 more)

### Community 35 - "Module Group 35 (apps/api/app)"
Cohesion: 0.17
Nodes (15): condition_normalized_matrices(), degradation_matrices(), fault_family_feature_names(), fault_fold_matrices(), grouped_condition_folds(), _median_iqr(), PaderbornFaultV2Preprocessor, rul_family_feature_names() (+7 more)

### Community 36 - "API Endpoints (app)"
Cohesion: 0.17
Nodes (21): convert_to_work_order(), create_report(), _enforce_minimum_priority(), get_report(), list_reports(), parse_fault(), _to_detail(), _to_out() (+13 more)

### Community 37 - "Module Group 37 (apps/api/app)"
Cohesion: 0.11
Nodes (14): Settings, build_client(), build_subscription_client(), GatewayConfig, test_gateway_config_defaults_and_factory(), test_development_keeps_local_demo_defaults(), test_explicit_sqlalchemy_driver_is_preserved(), test_legacy_postgres_url_uses_installed_psycopg_driver() (+6 more)

### Community 38 - "Module Group 38 (apps/api/app)"
Cohesion: 0.14
Nodes (18): _alarm_type_from_message(), AlarmSnapshot, correlate_alarm_snapshots(), correlate_alarms(), CorrelationGroup, _group_id_for(), _merge_line_cascades(), _severity_rank() (+10 more)

### Community 39 - "Module Group 39 (apps/api/app)"
Cohesion: 0.12
Nodes (15): LoadedArtifact, _band_energy(), extract_features(), _finite(), _frequency_features(), _slope(), _trend_features(), predict() (+7 more)

### Community 40 - "Module Group 40 (apps/api/app)"
Cohesion: 0.19
Nodes (17): group_kfold_indices(), _band_mask(), _baseline_stats(), _channel_features(), ConditionBaseline, extract_dual_channel_features(), extract_envelope_features(), extract_spectral_features_v2() (+9 more)

### Community 41 - "Web Frontend Components (41)"
Cohesion: 0.07
Nodes (28): license, name, private, version, autoprefixer, axios, class-variance-authority, clsx (+20 more)

### Community 42 - "Web Interactive Demo Console"
Cohesion: 0.14
Nodes (26): AlarmsPage(), AnalysisBlock(), EvidenceDetails(), formatTime(), SEVERITY_STYLES, AnalysisChip(), EquipmentDigitalView(), HealthChip() (+18 more)

### Community 43 - "Module Group 43 (apps/api/tests)"
Cohesion: 0.18
Nodes (10): LaborEntry, MaintenanceLog, WorkOrder, WorkOrderChecklistItem, TestWorkOrderCompletion, test_checklist_items_ordered_by_business_order(), test_maintenance_logs_ordered_by_created_then_id(), test_status_history_append_only_order() (+2 more)

### Community 44 - "Web Telemetry & Realtime Monitoring"
Cohesion: 0.14
Nodes (24): EquipmentDetail(), healthColor(), Info(), EquipmentList(), healthBar(), healthColor(), riskLabel(), format() (+16 more)

### Community 45 - "Web UI Testing & Specs"
Cohesion: 0.07
Nodes (26): acceptedHighRiskWo, assignedWo, completedWo, inProgressWo, mockAcceptWorkOrder, mockAddAttachment, mockAddLaborEntry, mockAddMaintenanceLog (+18 more)

### Community 46 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.21
Nodes (18): _binary_metrics(), Candidate, _candidates(), _classifier(), _complexity(), _evaluate_candidate(), _fold_indices(), _git_sha() (+10 more)

### Community 47 - "Module Group 47 (apps/api/tests)"
Cohesion: 0.10
Nodes (11): build_metrics(), IndustrialMetrics, _auth(), test_build_metrics_registries_are_isolated(), test_full_workflow_via_http_shows_review_and_work_order(), test_health_reports_honest_statuses(), test_metrics_endpoint_lists_core_families(), test_rag_empty_result_metric_on_empty_knowledge() (+3 more)

### Community 48 - "API Endpoints (app)"
Cohesion: 0.14
Nodes (15): create_knowledge(), delete_knowledge(), get_knowledge(), list_knowledge(), search_knowledge(), update_knowledge(), ErrorResponse, forbidden() (+7 more)

### Community 50 - "Module Group 50 (apps/api/app)"
Cohesion: 0.11
Nodes (10): render_metrics(), reset_request_id(), set_request_id(), health(), lifespan(), metrics(), ready(), RequestContextMiddleware (+2 more)

### Community 51 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.21
Nodes (14): _consolidate_cache(), _git_sha(), _json_sha256(), main(), _prepare_cached_group(), prepare_paderborn_bearing(), prepare_xjtu_bearing(), _read_json() (+6 more)

### Community 52 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.26
Nodes (15): _audit_csv(), audit_paderborn(), _audit_paderborn_archives(), audit_xjtu(), _audit_xjtu_archive(), _bearing_from_parent(), _expected_xjtu_condition(), _load_manifest() (+7 more)

### Community 53 - "Web Frontend Components (53)"
Cohesion: 0.10
Nodes (21): devDependencies, autoprefixer, eslint, eslint-config-next, identity-obj-proxy, jest, jest-environment-jsdom, @netlify/plugin-nextjs (+13 more)

### Community 54 - "Module Group 54 (apps/api/app)"
Cohesion: 0.12
Nodes (9): downgrade(), upgrade(), downgrade_intelligent_schema(), schema_is_ready(), upgrade_schema(), test_upgrade_adds_checklist_category_without_losing_data(), test_upgrade_adds_intelligent_equipment_fields_and_backfills_uuid(), test_upgrade_backfills_operation_approval_execution_keys() (+1 more)

### Community 55 - "Module Group 55 (apps/api/tests)"
Cohesion: 0.17
Nodes (10): reset_gateway_runtime(), _auth_headers(), _reset_runtime_after_test(), _setup_mock_gateway(), test_demo_state_aggregates_real_records(), test_invalid_scenario_rejected_400(), test_normal_and_warning_scenarios_are_supported(), test_scenario_permissions() (+2 more)

### Community 56 - "Module Group 56 (apps/api/tests)"
Cohesion: 0.16
Nodes (8): _make_equipment(), _make_service(), _ScriptedClock, test_bad_quality_and_missing_data_never_reach_business(), test_gateway_failure_fallback_then_recovery(), test_opcua_telemetry_conversion_ingests_into_ai_chain(), test_partial_mapping_produces_no_snapshot(), test_unit_conversion_applied_before_ingestion()

### Community 57 - "Web UI Testing & Specs"
Cohesion: 0.16
Nodes (18): CpuIcon(), Dashboard(), failureModeLabel(), formatMetric(), PlatformMetric(), PriorityBadge(), RiskBadge(), StatCard() (+10 more)

### Community 58 - "Web Frontend Components (58)"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 59 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.23
Nodes (11): analyze(), _audit_channels(), _bearing_distribution(), _eta_squared(), _git_sha(), _labels(), main(), _markdown() (+3 more)

### Community 60 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.26
Nodes (11): _write_mapping_config(), audit_processed_dataset(), _audit_rul_time(), _audit_training_policy(), _failed_result(), main(), _markdown(), _read_json() (+3 more)

### Community 62 - "Module Group 62 (apps/api/tests)"
Cohesion: 0.24
Nodes (12): CandidateMetrics, _metric(), select_failure_model(), select_rul_model(), synthetic_window(), test_artifact_integrity_and_deterministic_inference(), test_group_split_never_leaks_bearings(), test_locked_group_manifest_is_materialized_without_overlap() (+4 more)

### Community 63 - "Module Group 63 (apps/api/app)"
Cohesion: 0.15
Nodes (3): LLMClient, LLMProvider, test_ai_provider_failure_degrades_to_mock()

### Community 64 - "Module Group 64 (apps/api/tests)"
Cohesion: 0.26
Nodes (12): create_access_token(), _setup(), test_analyze_endpoint_persists_full_intelligence(), test_analyze_forbidden_for_technician(), test_correlate_groups_active_alarms(), test_decision_support_links_open_work_order(), test_get_analysis_requires_existing_record(), test_no_device_control_endpoints_added() (+4 more)

### Community 65 - "Module Group 65 (apps/api/tests)"
Cohesion: 0.13
Nodes (4): gateway_runtime(), _seed_runtime(), test_gateway_exposes_no_write_endpoints(), test_gateway_sync_ingests_telemetry()

### Community 66 - "Web Frontend Components (66)"
Cohesion: 0.12
Nodes (16): dependencies, axios, class-variance-authority, clsx, date-fns, @hookform/resolvers, lucide-react, next (+8 more)

### Community 67 - "API Endpoints (app)"
Cohesion: 0.16
Nodes (6): _default_ticks(), demo_state(), DemoScenarioRequest, _require_mock_gateway(), set_demo_scenario(), get_mock_simulator()

### Community 68 - "API Endpoints (app)"
Cohesion: 0.30
Nodes (9): create_user(), list_technicians(), list_users(), LoginRequest, SkillOut, TechnicianOut, UserBase, UserCreate (+1 more)

### Community 69 - "Module Group 69 (apps/api/app)"
Cohesion: 0.30
Nodes (8): alembic_config(), current_revision(), database_is_at_head(), ensure_database_at_head(), upgrade_database(), test_alembic_adopts_unversioned_legacy_database_without_losing_data(), test_alembic_upgrade_creates_and_versions_new_database(), test_production_startup_refuses_unmigrated_database()

### Community 70 - "Web Work Orders & Dispatch UI"
Cohesion: 0.20
Nodes (12): PriorityBadge(), WorkOrderList(), assignWorkOrder(), listTechnicians(), listWorkOrders(), mockAssignWorkOrder, mockCancelWorkOrder, mockListTechnicians (+4 more)

### Community 71 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.30
Nodes (9): build_manifest(), _distribution(), main(), _read_json(), _read_labels(), _seeded_digest(), _sha256(), _string_list() (+1 more)

### Community 72 - "Module Group 72 (apps/api/app)"
Cohesion: 0.37
Nodes (6): _calibration_curve(), _curve_points(), evaluate_binary_classification(), evaluate_multiclass_classification(), evaluate_rul(), _safe_auc()

### Community 73 - "Dataset Preparation & ML Research Scripts"
Cohesion: 0.35
Nodes (8): _combined_dataset(), _labels(), main(), _read_json(), _read_yaml(), _sha256(), _validate_committed_config(), _write_json()

### Community 74 - "Module Group 74 (apps/api/app)"
Cohesion: 0.33
Nodes (6): check(), _dependencies_ready(), _heartbeat_key(), main(), _redis_client(), run()

### Community 75 - "Web Frontend Components (75)"
Cohesion: 0.17
Nodes (12): scripts, build, dev, lint, start, test, test:coverage, test:e2e (+4 more)

### Community 76 - "Module Group 76 (apps/api/app)"
Cohesion: 0.22
Nodes (4): industrial_span(), _initialise(), decorator(), wrapper()

### Community 77 - "Module Group 77 (apps/api/app)"
Cohesion: 0.20
Nodes (3): current_request_id(), TraceLogFilter, TraceLogFilter

### Community 78 - "Module Group 78 (apps/api/app)"
Cohesion: 0.47
Nodes (5): bundle_sha256(), load_artifact_bundle(), _read_json(), save_artifact_bundle(), _write_json()

### Community 79 - "Web UI Testing & Specs"
Cohesion: 0.33
Nodes (7): DemoAccount, DemoLoginConfig, LoginForm(), LoginFormProps, LoginPage(), mockLogin, mockPush

### Community 80 - "Module Group 80 (apps/api/app)"
Cohesion: 0.31
Nodes (3): DatabaseNotificationGateway, NotificationGateway, Notification

### Community 81 - "Web Frontend Components (81)"
Cohesion: 0.22
Nodes (8): compilerOptions, jsx, noEmit, types, exclude, extends, include, ../tsconfig.json

### Community 82 - "Web Human Approval Center"
Cohesion: 0.39
Nodes (8): ApprovalsPage(), COMMAND_LABELS, reconciliationLabel(), StatusBadge(), approveOperation(), listOperationApprovals(), reconcileOperation(), rejectOperation()

### Community 84 - "Module Group 84 (apps/api/alembic)"
Cohesion: 0.43
Nodes (5): _column_exists(), downgrade(), _index_exists(), _table_exists(), upgrade()

### Community 85 - "Module Group 85 (apps/api/alembic)"
Cohesion: 0.43
Nodes (4): downgrade(), _index_exists(), _table_exists(), upgrade()

### Community 86 - "API Endpoints (tests)"
Cohesion: 0.29
Nodes (5): _resolve_storage_path(), serve_file(), test_storage_path_accepts_real_child(), test_storage_path_rejects_parent_traversal(), test_storage_path_rejects_sibling_with_same_prefix()

### Community 87 - "Module Group 87 (apps/api/alembic)"
Cohesion: 0.40
Nodes (3): downgrade(), _table_exists(), upgrade()

### Community 88 - "Module Group 88 (apps/api/alembic)"
Cohesion: 0.40
Nodes (3): downgrade(), _table_exists(), upgrade()

### Community 89 - "Module Group 89 (apps/api/alembic)"
Cohesion: 0.40
Nodes (3): downgrade(), _table_exists(), upgrade()

## Knowledge Gaps
- **25 isolated node(s):** `../tsconfig.json`, `@hookform/resolvers`, `@tanstack/react-query`, `axios`, `class-variance-authority` (+20 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 872 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkOrder` connect `Module Group 43 (apps/api/tests)` to `Equipment & Spare Parts Endpoints`, `Intelligence & Simulation Endpoints`, `Work Orders & Scheduling Endpoints`, `Module Group 64 (apps/api/tests)`, `API Endpoints (app)`, `API Endpoints (app)`, `Intelligence & Simulation Endpoints`, `Module Group 34 (apps/api/app)`, `API Endpoints (app)`, `Intelligence & Simulation Endpoints`, `Intelligence & Simulation Endpoints`, `Intelligence & Simulation Endpoints`, `Module Group 15 (apps/api/app)`, `Module Group 49 (apps/api/tests)`, `Module Group 19 (apps/api/tests)`, `Module Group 23 (apps/api/tests)`, `Module Group 55 (apps/api/tests)`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `WorkOrder` (e.g. with `diagnose()` and `generate_report()`) actually correct?**
  _`WorkOrder` has 79 INFERRED edges - model-reasoned connections that need verification._
- **What connects `../tsconfig.json`, `@hookform/resolvers`, `@tanstack/react-query` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Work Orders & Scheduling Endpoints` be split into smaller, more focused modules?**
  _Cohesion score 0.06964022722491059 - nodes in this community are weakly interconnected._
- **Why does `Equipment` connect `Intelligence & Simulation Endpoints` to `Work Orders & Scheduling Endpoints`, `Intelligence & Simulation Endpoints`, `Module Group 3 (apps/api/app)`, `API Endpoints (app)`, `Intelligence & Simulation Endpoints`, `Module Group 7 (apps/api/app)`, `API Endpoints (app)`, `Intelligence & Simulation Endpoints`, `Intelligence & Simulation Endpoints`, `Module Group 15 (apps/api/app)`, `Module Group 19 (apps/api/tests)`, `API Endpoints (app)`, `Module Group 24 (apps/api/app)`, `Equipment & Spare Parts Endpoints`, `Module Group 33 (apps/api/app)`, `API Endpoints (app)`, `Module Group 43 (apps/api/tests)`, `Module Group 55 (apps/api/tests)`, `Module Group 56 (apps/api/tests)`, `Module Group 64 (apps/api/tests)`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 58 inferred relationships involving `Equipment` (e.g. with `_build_diagnose_prompt()` and `generate_report()`) actually correct?**
  _`Equipment` has 58 INFERRED edges - model-reasoned connections that need verification._
- **Should `Intelligence & Simulation Endpoints` be split into smaller, more focused modules?**
  _Cohesion score 0.050645007166746296 - nodes in this community are weakly interconnected._