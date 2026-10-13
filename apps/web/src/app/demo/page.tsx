'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  BookOpen,
  Eye,
  FileText,
  FlaskConical,
  GitBranch,
  Gauge,
  Info,
  Wrench,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '@/lib/auth';
import {
  analyzeAlarm,
  createAlarmWorkOrder,
  getDemoState,
  reviewAlarm,
  setDemoScenario,
} from '@/lib/api';
import type { DemoState } from '@/lib/types';
import {
  AnalysisChip,
  EquipmentDigitalView,
  HealthChip,
  ScenarioControl,
  WorkflowChip,
} from './_components/workspace';

const SIMULATION_DISCLAIMER =
  'This demo uses a deterministic software OPC UA simulator, not connected to a real plant PLC. ' +
  'AI recommendations must be reviewed by humans before entering maintenance workflows.';

function deriveSteps(state: DemoState | null): Array<{
  label: string;
  done: boolean;
}> {
  if (!state) return [];
  return [
    { label: 'Data Ingestion', done: state.telemetry != null },
    { label: 'Quality Verified', done: (state.quality?.accepted ?? 0) > 0 },
    { label: 'Anomaly Detection', done: state.anomaly != null },
    { label: 'Fault Prediction', done: state.prediction != null },
    { label: 'Industrial Alarm', done: state.alarm != null },
    { label: 'RCA Analysis Completed', done: state.analysis != null },
    {
      label: 'Human Review',
      done:
        state.analysis?.review_status === 'approve' ||
        state.analysis?.analysis_status === 'APPROVED',
    },
    { label: 'Work Order Creation', done: state.work_order != null },
    { label: 'Traceable Pipeline', done: !!state.trace_id },
  ];
}

export default function DemoPage() {
  const { user } = useAuth();
  const [state, setState] = useState<DemoState | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showArchitecture, setShowArchitecture] = useState(false);
  const canControl = user?.role === 'admin' || user?.role === 'supervisor';

  const refresh = useCallback(async () => {
    try {
      const data = await getDemoState('Motor001');
      setState(data);
      setLoadError(null);
    } catch (err: any) {
      setLoadError(err?.message || 'Failed to load demo state');
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const applyScenario = async (scenario: 'normal' | 'warning' | 'fault') => {
    setBusy(true);
    try {
      await setDemoScenario(scenario, undefined, 'Motor001');
      toast.success(`Switched to ${scenario.toUpperCase()} and completed a deterministic sampling cycle`);
      await refresh();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to switch scenario');
    } finally {
      setBusy(false);
    }
  };

  const doAnalyze = async () => {
    if (!state?.alarm) return;
    setBusy(true);
    try {
      await analyzeAlarm(state.alarm.id);
      toast.success('Alarm analysis completed (for human decision reference only)');
      await refresh();
    } catch (err: any) {
      toast.error(err?.message || 'Analysis failed');
    } finally {
      setBusy(false);
    }
  };

  const doReview = async (
    action: 'approve' | 'reject' | 'request_more_evidence'
  ) => {
    if (!state?.alarm) return;
    setBusy(true);
    try {
      await reviewAlarm(state.alarm.id, action, `Demo ${action}`);
      toast.success(`Review action submitted: ${action}`);
      await refresh();
    } catch (err: any) {
      toast.error(err?.message || 'Review failed');
    } finally {
      setBusy(false);
    }
  };

  const doCreateWorkOrder = async () => {
    if (!state?.alarm) return;
    setBusy(true);
    try {
      const result = await createAlarmWorkOrder(state.alarm.id);
      toast.success(
        result.created
          ? `Work order created: ${result.work_order_code}`
          : `Work order already exists: ${result.work_order_code}`
      );
      await refresh();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to create work order');
    } finally {
      setBusy(false);
    }
  };

  const steps = deriveSteps(state);
  const analysis = state?.analysis ?? null;

  return (
    <div className="max-w-5xl mx-auto space-y-4 pb-12" data-testid="demo-page">
      {/* Header */}
      <div className="flex items-start gap-3 flex-wrap">
        <div>
          <h1 className="text-lg font-bold">Industrial AI Maintenance Demo</h1>
          <p className="text-xs text-muted mt-1">
            Motor001 · Simulated OPC UA Equipment → AI-assisted Diagnosis →
            Human-reviewed Maintenance Workflow
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowArchitecture((v) => !v)}
          className="btn btn-outline !py-1 !px-2 text-xs ml-auto"
          data-testid="toggle-architecture"
        >
          <Info size={12} className="inline mr-1" />
          Architecture
        </button>
      </div>

      {showArchitecture && (
        <div className="card text-xs leading-6" data-testid="architecture-panel">
          <p className="font-semibold mb-1">Architecture</p>
          <p className="text-muted">
            User → Scenario → Simulator(software OPC UA) → Gateway → Data Quality
            → Telemetry → AI Pipeline(Anomaly/Prediction) → Alarm Intelligence
            (Correlation/RCA/RAG/Risk) → Human Review → Work Order → Trace
            Explorer
          </p>
        </div>
      )}

      {/* Demo Guide */}
      <div className="card" data-testid="demo-guide">
        <p className="text-xs font-semibold mb-1 flex items-center gap-1">
          <FlaskConical size={12} /> Demo Guide (5 Minutes)
        </p>
        <ol className="text-xs text-muted list-decimal list-inside space-y-0.5">
          <li>Select FAULT scenario and wait for deterministic degradation data to enter the platform</li>
          <li>Observe Health / Anomaly / Prediction / Industrial Alarm</li>
          <li>Inspect RCA and RAG evidence (evidence-bound)</li>
          <li>Manually approve analysis recommendations (human-in-the-loop)</li>
          <li>Create work order and inspect complete trace timeline</li>
        </ol>
      </div>

      {loadError && (
        <div className="card text-sm text-yellow-300" data-testid="demo-error">
          {loadError}
        </div>
      )}

      {/* Scenario controls */}
      <div className="card p-3">
        <ScenarioControl
          current={state?.simulator?.scenario ?? null}
          busy={busy}
          canControl={canControl}
          onSelect={applyScenario}
        />
      </div>

      {!state ? (
        <div className="card p-6 text-sm text-muted">Loading...</div>
      ) : (
        <>
          {/* Digital view + chips */}
          <EquipmentDigitalView state={state} />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <HealthChip state={state} />
            <AnalysisChip state={state} />
            <WorkflowChip state={state} />
          </div>

          {/* Quality */}
          <section className="card p-4" data-testid="quality-panel">
            <h2 className="font-semibold mb-2 flex items-center gap-2">
              <Gauge size={14} /> Data Quality (Latest Sync)
            </h2>
            {!state.quality ? (
              <p className="text-xs text-muted">No synchronization records yet</p>
            ) : (
              <div className="text-xs flex flex-wrap gap-x-6 gap-y-1">
                <span>Accepted: {state.quality.accepted ?? '-'}</span>
                <span>Rejected: {state.quality.rejected ?? '-'}</span>
                <span>Corrections: {state.quality.corrections ?? '-'}</span>
                {Object.entries(state.quality.reject_reasons).map(
                  ([reason, count]) => (
                    <span key={reason} className="text-red-300">
                      {reason}: {count}
                    </span>
                  )
                )}
              </div>
            )}
          </section>

          {/* Anomaly & Prediction */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <section className="card p-4" data-testid="anomaly-panel">
              <h2 className="font-semibold mb-2 text-sm">Latest Anomaly</h2>
              {state.anomaly ? (
                <ul className="text-xs space-y-1">
                  <li>Type: {state.anomaly.fault_type}</li>
                  <li>Severity: {state.anomaly.severity}</li>
                  <li>Status: {state.anomaly.status}</li>
                  <li>Detected At: {state.anomaly.detected_at}</li>
                </ul>
              ) : (
                <p className="text-xs text-muted">No active anomaly</p>
              )}
            </section>
            <section className="card p-4" data-testid="prediction-panel">
              <h2 className="font-semibold mb-2 text-sm">Fault Prediction</h2>
              {state.prediction ? (
                <ul className="text-xs space-y-1">
                  <li>Model Version: {state.prediction.model_version}</li>
                  <li>Failure Mode: {state.prediction.failure_mode}</li>
                  <li>Probability: {state.prediction.probability ?? '-'}</li>
                  <li className="text-muted">
                    Research/staging model · Non-production operating conditions
                  </li>
                </ul>
              ) : (
                <p className="text-xs text-muted">No prediction generated</p>
              )}
            </section>
          </div>

          {/* Alarm */}
          <section className="card p-4" data-testid="alarm-panel">
            <h2 className="font-semibold mb-2 text-sm">Latest Industrial Alarm</h2>
            {state.alarm ? (
              <div className="text-xs space-y-1">
                <p>
                  <span
                    className={`badge mr-2 ${
                      state.alarm.severity === 'CRITICAL'
                        ? 'bg-red-500/15 text-red-300'
                        : 'bg-yellow-500/15 text-yellow-300'
                    }`}
                  >
                    {state.alarm.severity}
                  </span>
                  {state.alarm.cleared ? 'CLEARED' : 'ACTIVE'} ·{' '}
                  {state.alarm.created_at}
                </p>
                <p>{state.alarm.message}</p>
              </div>
            ) : (
              <p className="text-xs text-muted">No industrial alarm</p>
            )}
          </section>

          {/* RCA + RAG */}
          <section className="card p-4" data-testid="diagnosis-panel">
            <h2 className="font-semibold mb-2 text-sm flex items-center gap-2">
              <GitBranch size={14} /> RCA & RAG Evidence
            </h2>
            {!analysis ? (
              !state.alarm ? (
                <p className="text-xs text-muted">Please trigger an industrial alarm first</p>
              ) : canControl ? (
                <button
                  type="button"
                  className="btn btn-primary !py-1 !px-3 text-xs"
                  disabled={busy}
                  onClick={doAnalyze}
                  data-testid="generate-analysis"
                >
                  Generate Alarm Analysis
                </button>
              ) : (
                <p className="text-xs text-muted">Awaiting supervisor analysis generation</p>
              )
            ) : (
              <div className="space-y-2 text-xs">
                <p>
                  <span className="text-muted">Root Cause Hypothesis: </span>
                  {analysis.root_cause_hypothesis}
                </p>
                <p>
                  <span className="text-muted">Confidence: </span>
                  {analysis.confidence} ·{' '}
                  {analysis.requires_human_review
                    ? 'Insufficient evidence, manual review required'
                    : ''}
                </p>
                <div>
                  <p className="text-muted mb-1">Recommended Actions (AI Recommendation)</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {analysis.recommended_actions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-muted mb-1">Knowledge Base Evidence (Up to 3 citations)</p>
                  {analysis.citations.length === 0 ? (
                    <p>No knowledge evidence retrieved</p>
                  ) : (
                    <ul className="space-y-1">
                      {analysis.citations.map((citation, index) => (
                        <li key={index} className="rounded bg-white/5 p-1.5">
                          {String(citation.title ?? '')} ·{' '}
                          {String(citation.source ?? '')} · score{' '}
                          {String(citation.score ?? '-')}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </section>

          {/* Review */}
          <section className="card p-4" data-testid="review-panel">
            <h2 className="font-semibold mb-2 text-sm">Human Review</h2>
            {!analysis ? (
              <p className="text-xs text-muted">Please generate alarm analysis first</p>
            ) : analysis.analysis_status === 'WAITING_REVIEW' ||
              analysis.analysis_status === 'DIAGNOSED' ? (
              <div className="flex gap-2 flex-wrap">
                <button
                  type="button"
                  className="btn btn-success !py-1 !px-3 text-xs"
                  disabled={busy || !canControl}
                  onClick={() => doReview('approve')}
                  data-testid="review-approve"
                >
                  Approve Recommendation
                </button>
                <button
                  type="button"
                  className="btn btn-outline !py-1 !px-3 text-xs"
                  disabled={busy || !canControl}
                  onClick={() => doReview('reject')}
                  data-testid="review-reject"
                >
                  Reject
                </button>
                <button
                  type="button"
                  className="btn btn-outline !py-1 !px-3 text-xs"
                  disabled={busy || !canControl}
                  onClick={() => doReview('request_more_evidence')}
                  data-testid="review-more-evidence"
                >
                  Request Evidence
                </button>
              </div>
            ) : (
              <p className="text-xs text-muted">
                Current Status: {analysis.analysis_status}
                {analysis.review_status ? ` (${analysis.review_status})` : ''}
              </p>
            )}
          </section>

          {/* Work Order */}
          <section className="card p-4" data-testid="workorder-panel">
            <h2 className="font-semibold mb-2 text-sm flex items-center gap-2">
              <Wrench size={14} /> Work Order
            </h2>
            {analysis &&
            analysis.analysis_status === 'APPROVED' &&
            !analysis.created_work_order_id ? (
              <button
                type="button"
                className="btn btn-primary !py-1 !px-3 text-xs"
                disabled={busy || !canControl}
                onClick={doCreateWorkOrder}
                data-testid="create-work-order"
              >
                Create Approved Work Order
              </button>
            ) : null}
            {state.work_order && (
              <div className="text-xs mt-2 space-y-1">
                <p>
                  <Link
                    href={`/work-orders/${state.work_order.id}`}
                    className="underline"
                    data-testid="work-order-link"
                  >
                    {state.work_order.code}
                  </Link>{' '}
                  · {state.work_order.status} · {state.work_order.priority}
                </p>
                {state.approval && (
                  <p className="text-yellow-300">
                    Approval required：{state.approval.command_type}（
                    {state.approval.risk_level} risk · {state.approval.status}）
                  </p>
                )}
              </div>
            )}
          </section>

          {/* Trace */}
          <section className="card p-4" data-testid="trace-panel">
            <h2 className="font-semibold mb-2 text-sm flex items-center gap-2">
              <FileText size={14} /> End-to-End Trace
            </h2>
            {state.trace_id ? (
              <div className="text-xs space-y-1">
                <p className="font-mono break-all">{state.trace_id}</p>
                <Link
                  href={`/observability/traces/${state.trace_id}`}
                  className="btn btn-outline !py-1 !px-2 inline-flex items-center gap-1"
                  data-testid="view-full-trace"
                >
                  <Eye size={12} /> View Full Trace
                </Link>
              </div>
            ) : (
              <p className="text-xs text-muted">Trace unavailable</p>
            )}
          </section>
        </>
      )}

      {/* Simulation disclaimer */}
      <div
        className="card border-yellow-400/30 bg-yellow-500/5 p-3 text-xs text-yellow-200"
        data-testid="simulation-disclaimer"
      >
        Simulation Environment：This demo uses a deterministic software OPC UA
        simulator. It is not connected to a real factory PLC. AI recommendations
        require human review before maintenance workflow progression.
      </div>

      {/* Portfolio docs link */}
      <p className="text-xs text-muted flex items-center gap-1">
        <BookOpen size={12} />
        <Link href="/observability" className="underline">
          Observability Center
        </Link>
        <span>·</span>
        <span>docs/demo-guide.md</span>
        <span>·</span>
        <span className="inline-flex items-center gap-1">
          <Eye size={12} /> Trace Explorer reused
        </span>
      </p>
    </div>
  );
}
