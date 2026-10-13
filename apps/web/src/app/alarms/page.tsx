'use client';

import { useCallback, useEffect, useState } from 'react';
import { BellRing, BrainCircuit, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '@/lib/auth';
import {
  acknowledgeAlarm,
  analyzeAlarm,
  correlateAlarms,
  createAlarmWorkOrder,
  listAlarms,
  reviewAlarm,
} from '@/lib/api';
import type { AlarmAnalysis, AlarmCorrelateResult, IndustrialAlarm } from '@/lib/types';

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: 'bg-red-500/15 text-red-300',
  WARNING: 'bg-yellow-500/15 text-yellow-300',
};

export default function AlarmsPage() {
  const { user } = useAuth();
  const [alarms, setAlarms] = useState<IndustrialAlarm[]>([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('active');
  const [busy, setBusy] = useState(false);
  const [analyses, setAnalyses] = useState<Record<number, AlarmAnalysis>>({});
  const [selectedAlarmId, setSelectedAlarmId] = useState<number | null>(null);
  const [correlation, setCorrelation] = useState<AlarmCorrelateResult | null>(null);
  const canControl = user?.role === 'admin' || user?.role === 'supervisor';

  const refresh = useCallback(async () => {
    const data = await listAlarms(statusFilter ? { status: statusFilter } : undefined).catch(() => null);
    if (data) {
      setAlarms(data.items);
      setTotal(data.total);
    }
  }, [statusFilter]);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const ack = async (alarm: IndustrialAlarm) => {
    setBusy(true);
    try {
      await acknowledgeAlarm(alarm.id);
      toast.success('Alarm acknowledged');
      await refresh();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setBusy(false);
    }
  };

  const runAnalysis = async (alarm: IndustrialAlarm) => {
    setBusy(true);
    setSelectedAlarmId(alarm.id);
    try {
      const analysis = await analyzeAlarm(alarm.id);
      setAnalyses((current) => ({ ...current, [alarm.id]: analysis }));
      toast.success('Analysis complete (advisory only)');
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setBusy(false);
    }
  };

  const runCorrelation = async () => {
    setBusy(true);
    try {
      setCorrelation(await correlateAlarms());
      toast.success('Correlation analysis complete');
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setBusy(false);
    }
  };

  const review = async (action: 'approve' | 'reject' | 'request_more_evidence') => {
    if (!selectedAlarmId) return;
    setBusy(true);
    try {
      const analysis = await reviewAlarm(selectedAlarmId, action);
      setAnalyses((current) => ({ ...current, [selectedAlarmId]: analysis }));
      toast.success(action === 'approve' ? 'Analysis approved' : action === 'reject' ? 'Analysis rejected' : 'Additional evidence requested');
      await refresh();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setBusy(false);
    }
  };

  const createWorkOrder = async () => {
    if (!selectedAlarmId) return;
    setBusy(true);
    try {
      const result = await createAlarmWorkOrder(selectedAlarmId);
      setAnalyses((current) => ({
        ...current,
        [selectedAlarmId]: {
          ...current[selectedAlarmId],
          analysis_status: 'WORK_ORDER_CREATED',
          created_work_order_id: result.work_order_id,
        },
      }));
      toast.success(`${result.work_order_code} created`);
      await refresh();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6" data-testid="alarms-page">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <div className="text-xs tracking-[0.18em] uppercase text-primary-400 font-semibold mb-1">Industrial Alarm Center</div>
          <h1 className="text-2xl font-bold">Industrial Alarm Center</h1>
          <p className="text-sm text-muted mt-1">
            OPC UA Alarm Semantics (simulated subscription workflow) · Alarms derived from read-only event pipeline
          </p>
        </div>
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          className="text-sm"
          aria-label="Filter alarms"
        >
          <option value="">All</option>
          <option value="active">Active</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="cleared">Cleared</option>
        </select>
      </div>

      <div className="card overflow-x-auto">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold flex items-center gap-2"><BellRing size={16} className="text-yellow-300" />Alarm List</h2>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted">{total} records</span>
            <button disabled={busy || !canControl || !alarms.length} onClick={runCorrelation} className="btn btn-outline btn-sm">
              Correlate Alarms
            </button>
          </div>
        </div>
        {alarms.length ? (
          <table className="w-full text-sm" data-testid="alarms-table">
            <thead>
              <tr className="text-left text-xs text-muted border-b border-card-border">
                <th className="py-2 pr-3">Severity</th>
                <th className="py-2 pr-3">Risk</th>
                <th className="py-2 pr-3">Equipment</th>
                <th className="py-2 pr-3">Message</th>
                <th className="py-2 pr-3">Timestamp</th>
                <th className="py-2 pr-3">Status</th>
                <th className="py-2 pr-3">Analysis</th>
                <th className="py-2 pr-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {alarms.map((alarm) => (
                <tr key={alarm.id} className="border-b border-card-border/50 last:border-0">
                  <td className="py-2 pr-3">
                    <span className={`badge ${SEVERITY_STYLES[alarm.severity] || 'bg-gray-500/15 text-gray-300'}`}>{alarm.severity}</span>
                  </td>
                  <td className="py-2 pr-3 text-xs">{alarm.risk_level || 'Pending Analysis'}</td>
                  <td className="py-2 pr-3 font-mono text-xs">#{alarm.equipment_id}</td>
                  <td className="py-2 pr-3">{alarm.message}</td>
                  <td className="py-2 pr-3 text-xs text-muted">{formatTime(alarm.created_at)}</td>
                  <td className="py-2 pr-3 text-xs">
                    {alarm.cleared_at ? (
                      <span className="text-green-400">Cleared {formatTime(alarm.cleared_at)}</span>
                    ) : (
                      <span className="text-red-400">Active</span>
                    )}
                    {alarm.acknowledged && <span className="ml-2 badge bg-primary-500/15 text-primary-300">Acknowledged</span>}
                  </td>
                  <td className="py-2 pr-3 text-xs">
                    <div>{alarm.analysis_status || 'NEW'}</div>
                    <div className="text-muted">{alarm.correlated_alarm_count || 0} correlated</div>
                  </td>
                  <td className="py-2 pr-3 space-x-2 whitespace-nowrap">
                    {!alarm.acknowledged && (
                      <button disabled={busy || !canControl} onClick={() => ack(alarm)} className="btn btn-outline btn-sm">
                        Acknowledge
                      </button>
                    )}
                    <button
                      disabled={busy || !canControl}
                      onClick={() => runAnalysis(alarm)}
                      className="btn btn-outline btn-sm"
                      data-testid={`analyze-alarm-${alarm.id}`}
                    >
                      AI Analysis
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-muted py-6 text-center">No industrial alarm records found.</p>
        )}
      </div>

      {correlation && correlation.groups.length > 0 && (
        <div className="card" data-testid="correlation-panel">
          <h2 className="font-semibold mb-3">Correlated Event Groups ({correlation.groups.length} groups / {correlation.total_alarms} alarms)</h2>
          <div className="space-y-2 text-sm">
            {correlation.groups.map((group) => (
              <div key={group.group_id} className="rounded-lg border border-card-border p-3 flex items-center justify-between gap-3">
                <div>
                  <span className={`badge ${SEVERITY_STYLES[group.severity] || 'bg-gray-500/15 text-gray-300'}`}>{group.severity}</span>
                  <span className="ml-2 text-xs font-mono text-muted">{group.reason === 'line_cascade' ? 'Line Cascade' : 'Same Equipment'}</span>
                </div>
                <div className="text-xs text-muted">
                  Alarms: {group.alarm_ids.join(', ')} · Equipment: {group.equipment_ids.map((id) => `#${id}`).join(' ')} · {group.size} items
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedAlarmId && analyses[selectedAlarmId] && (
        <div className="card" data-testid="analysis-panel">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold flex items-center gap-2"><BrainCircuit size={16} className="text-primary-400" />Intelligent Alarm Analysis (AI-assisted, advisory only)</h2>
            <span className="text-xs text-muted">Risk: {analyses[selectedAlarmId].risk_level} · Confidence: {(analyses[selectedAlarmId].confidence * 100).toFixed(0)}% · {analyses[selectedAlarmId].analysis_status}</span>
          </div>
          <div className="space-y-3 text-sm">
            <AnalysisBlock title="Alarm Understanding" body={analyses[selectedAlarmId].summary} />
            <AnalysisBlock title="Root Cause Hypothesis" body={analyses[selectedAlarmId].root_cause_hypothesis} />
            <EvidenceDetails evidence={analyses[selectedAlarmId].evidence} />
            {analyses[selectedAlarmId].citations.length > 0 && (
              <div>
                <div className="text-xs text-muted mb-1">Knowledge Citations</div>
                <ul className="list-disc list-inside text-xs text-muted">
                  {analyses[selectedAlarmId].citations.map((citation, index) => (
                    <li key={`${citation.article_id}-${index}`}>
                      {citation.title} · {citation.source || 'Knowledge Base'} (score {citation.score})
                      {citation.snippet && <span className="block pl-4">{citation.snippet}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <div className="text-xs text-muted mb-1">Recommended Actions (requires human confirmation and work order execution)</div>
              <ol className="list-decimal list-inside space-y-1">
                {analyses[selectedAlarmId].recommended_actions.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ol>
            </div>
            {correlation && (
              <p className="text-xs text-muted">
                Correlation group: {correlation.groups.find((group) => group.group_id === analyses[selectedAlarmId].correlation_group_id)?.size ?? 1} related alarms
              </p>
            )}
            <p className="text-xs text-yellow-300 bg-yellow-500/10 rounded-lg p-3 flex items-start gap-1.5">
              <ShieldCheck size={14} className="mt-0.5 shrink-0" />
              This analysis does not automatically trigger or execute equipment controls; all actions require a work order and Human Approval workflow.
            </p>
            {canControl && analyses[selectedAlarmId].analysis_status === 'WAITING_REVIEW' && (
              <div className="flex flex-wrap gap-2" data-testid="review-actions">
                <button disabled={busy} onClick={() => review('approve')} className="btn btn-primary btn-sm">Approve Analysis</button>
                <button disabled={busy} onClick={() => review('request_more_evidence')} className="btn btn-outline btn-sm">Request Evidence</button>
                <button disabled={busy} onClick={() => review('reject')} className="btn btn-outline btn-sm">Reject Analysis</button>
              </div>
            )}
            {canControl && analyses[selectedAlarmId].analysis_status === 'APPROVED' && (
              <button disabled={busy} onClick={createWorkOrder} className="btn btn-primary btn-sm" data-testid="create-alarm-work-order">
                Create Controlled Work Order
              </button>
            )}
            {analyses[selectedAlarmId].created_work_order_id && (
              <p className="text-xs text-green-400">Created Work Order #{analyses[selectedAlarmId].created_work_order_id}</p>
            )}
          </div>
        </div>
      )}

      <p className="text-xs text-muted flex items-start gap-1.5">
        <ShieldCheck size={14} className="mt-0.5 shrink-0 text-green-400" />
        Alarms originate from read-only OPC UA subscription pipeline; acknowledgment and analysis only update platform records, never writing to equipment.
      </p>
    </div>
  );
}

function AnalysisBlock({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <div className="text-xs text-muted mb-1">{title}</div>
      <p className="rounded-lg bg-black/10 border border-card-border p-3">{body}</p>
    </div>
  );
}

function EvidenceDetails({ evidence }: { evidence: Record<string, unknown> }) {
  const telemetry = evidence.telemetry_fields as Record<string, unknown> | undefined;
  const prediction = evidence.prediction_context as Record<string, unknown> | undefined;
  const risk = evidence.risk_assessment as { reasons?: string[] } | undefined;
  return (
    <div className="grid md:grid-cols-3 gap-2 text-xs" data-testid="evidence-details">
      <div className="rounded-lg border border-card-border p-3">
        <div className="text-muted mb-1">Telemetry Evidence</div>
        <div>{telemetry ? Object.entries(telemetry).map(([key, value]) => `${key}=${value ?? '--'}`).join(' · ') : 'None'}</div>
      </div>
      <div className="rounded-lg border border-card-border p-3">
        <div className="text-muted mb-1">Failure Prediction</div>
        <div>{prediction ? `${prediction.failure_mode || 'Unknown'} · probability=${prediction.probability ?? '--'}` : 'No prediction records'}</div>
      </div>
      <div className="rounded-lg border border-card-border p-3">
        <div className="text-muted mb-1">Risk Rules</div>
        <div>{risk?.reasons?.join(' · ') || 'No escalation criteria'}</div>
      </div>
    </div>
  );
}

function formatTime(value: string | null | undefined) {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '--';
  return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
