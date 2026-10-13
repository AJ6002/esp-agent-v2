'use client';

import { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, LockKeyhole, SearchCheck, ShieldAlert, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { approveOperation, listOperationApprovals, reconcileOperation, rejectOperation } from '@/lib/api';
import { useAuth } from '@/lib/auth';

const COMMAND_LABELS: Record<string, string> = {
  shutdown: 'Controlled Shutdown',
  emergency_stop: 'Emergency Stop',
  restart: 'Device Restart',
  start: 'Device Start',
  reset_alarm: 'Reset Alarm',
  set_speed: 'Adjust Speed',
};

export default function ApprovalsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<any[]>([]);
  const [filter, setFilter] = useState('action_required');
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [outcomes, setOutcomes] = useState<Record<number, 'confirmed_executed' | 'confirmed_not_executed' | 'confirmed_failed'>>({});
  const [deviceStates, setDeviceStates] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const canReview = user?.role === 'admin' || user?.role === 'supervisor';

  const load = useCallback(() => {
    setLoading(true);
    const apiStatus = filter === 'all' ? undefined : filter;
    listOperationApprovals(apiStatus)
      .then(setItems)
      .catch((error) => toast.error(error.message))
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const review = async (item: any, action: 'approve' | 'reject') => {
    const note = notes[item.id]?.trim();
    if (!note) {
      toast.error('Please enter review notes and on-site safety confirmation first');
      return;
    }
    setBusyId(item.id);
    try {
      if (action === 'approve') {
        await approveOperation(item.id, note);
        toast.success('Approval granted; command has been dispatched by the equipment gateway');
      } else {
        await rejectOperation(item.id, note);
        toast.success('High-risk operation rejected; no equipment command executed');
      }
      await load();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setBusyId(null);
    }
  };

  const reconcile = async (item: any) => {
    const outcome = outcomes[item.id];
    const note = notes[item.id]?.trim();
    const observedDeviceState = deviceStates[item.id]?.trim();
    if (!outcome || !note || !observedDeviceState) {
      toast.error('Please select a verification outcome and enter the on-site device state and verification notes');
      return;
    }
    setBusyId(item.id);
    try {
      await reconcileOperation(item.id, {
        outcome,
        note,
        observed_device_state: observedDeviceState,
      });
      toast.success(outcome === 'confirmed_not_executed' ? 'Confirmed not executed; operation has returned to pending approval with a new idempotency key' : 'Manual verification completed and logged to audit records');
      await load();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs tracking-[0.18em] uppercase text-red-300 font-semibold mb-1"><LockKeyhole size={14} /> Human-in-the-loop</div>
          <h1 className="text-2xl font-bold">High-Risk Operations Approval Center</h1>
          <p className="text-sm text-muted mt-1">AI Agent can only propose operations; Equipment Gateway executes no commands without supervisor approval</p>
        </div>
        <select value={filter} onChange={(event) => setFilter(event.target.value)} className="text-sm">
          <option value="action_required">Action Required</option><option value="pending">Pending Approval</option><option value="execution_unknown">Pending Manual Verification</option><option value="executing">Executing</option><option value="approved">Approved</option><option value="execution_failed">Execution Failed</option><option value="rejected">Rejected</option><option value="all">All</option>
        </select>
      </div>

      <div className="rounded-xl border border-yellow-500/25 bg-yellow-500/[0.07] p-4 flex items-start gap-3 text-sm">
        <ShieldAlert className="text-yellow-300 shrink-0 mt-0.5" size={18} />
        <div><strong className="text-yellow-200">Safety Boundary</strong><p className="text-muted mt-1">Before approval, verify maintenance window, downtime impact, on-site personnel, energy isolation, and LOTO. Approval triggers simulated device commands; do not treat demo results as actual PLC state.</p></div>
      </div>

      {loading ? <div className="text-muted p-6">Loading...</div> : (
        <div className="space-y-4">
          {items.map((item) => (
            <article key={item.id} className="card">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                <div className="space-y-3 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={item.status} />
                    <span className="badge bg-red-500/15 text-red-300">{item.risk_level}</span>
                    <span className="text-xs text-muted font-mono">Approval #{item.id}</span>
                  </div>
                  <div>
                    <h2 className="font-semibold">{COMMAND_LABELS[item.command_type] || item.command_type} · {item.equipment_name}</h2>
                    <p className="text-xs text-muted mt-1">{item.equipment_code} · Work Order {item.work_order_id ? `#${item.work_order_id}` : 'Unlinked'} · Requester: {item.requested_by_name}</p>
                  </div>
                  <div className="rounded-lg border border-red-500/15 bg-red-500/5 p-3">
                    <div className="text-xs text-red-300 mb-1">Risk Description</div>
                    <p className="text-sm leading-6">{item.risk_reason}</p>
                  </div>
                  {item.command_payload && <div className="text-xs text-muted">Command Parameters: <code className="font-mono text-slate-300">{JSON.stringify(item.command_payload)}</code></div>}
                  {item.status !== 'pending' && (
                    <div className="text-sm">
                      <div><span className="text-muted">Reviewer: </span>{item.reviewed_by_name || '-'}</div>
                      <div className="mt-1"><span className="text-muted">Review Notes: </span>{item.review_note || '-'}</div>
                      <div className="mt-1"><span className="text-muted">Command Execution: </span>{item.command_executed ? 'Executed' : 'Not Executed'}</div>
                    </div>
                  )}
                  {item.reconciliation_outcome && (
                    <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3 text-sm">
                      <div><span className="text-muted">Verification Outcome: </span>{reconciliationLabel(item.reconciliation_outcome)}</div>
                      <div className="mt-1"><span className="text-muted">On-site State: </span>{item.observed_device_state}</div>
                      <div className="mt-1"><span className="text-muted">Verifier: </span>{item.reconciled_by_name || '-'}</div>
                      <div className="mt-1"><span className="text-muted">Verification Notes: </span>{item.reconciliation_note}</div>
                    </div>
                  )}
                </div>
                {item.status === 'pending' && (
                  <div className="lg:w-80 space-y-3">
                    <label className="block text-xs text-muted">Review Notes & Safety Confirmation
                      <textarea
                        rows={4}
                        value={notes[item.id] || ''}
                        onChange={(event) => setNotes((current) => ({ ...current, [item.id]: event.target.value }))}
                        placeholder="e.g. Confirmed 14:00 maintenance window, LOTO assigned, line supervisor notified"
                        className="w-full mt-1.5 resize-none"
                        disabled={!canReview}
                      />
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button disabled={!canReview || busyId === item.id} onClick={() => review(item, 'reject')} className="btn btn-outline text-red-300 border-red-500/30"><XCircle size={15} />Reject</button>
                      <button disabled={!canReview || busyId === item.id} onClick={() => review(item, 'approve')} className="btn btn-danger"><CheckCircle2 size={15} />Approve & Execute</button>
                    </div>
                    {!canReview && <p className="text-xs text-muted">Read-only for current role; approval requires supervisor or admin.</p>}
                  </div>
                )}
                {item.status === 'execution_unknown' && (
                  <div className="lg:w-80 space-y-3">
                    <div className="rounded-lg border border-orange-500/25 bg-orange-500/[0.08] p-3 text-xs text-orange-200">
                      Direct retry prohibited. Please inspect actual status on-site or via equipment platform first.
                    </div>
                    <label className="block text-xs text-muted">Verification Outcome
                      <select
                        value={outcomes[item.id] || ''}
                        onChange={(event) => setOutcomes((current) => ({ ...current, [item.id]: event.target.value as typeof outcomes[number] }))}
                        className="w-full mt-1.5"
                        disabled={!canReview}
                      >
                        <option value="">Select...</option>
                        <option value="confirmed_executed">Confirmed Executed</option>
                        <option value="confirmed_not_executed">Confirmed Not Executed, Re-approve</option>
                        <option value="confirmed_failed">Confirmed Execution Failed</option>
                      </select>
                    </label>
                    <label className="block text-xs text-muted">On-site Device State
                      <textarea rows={3} value={deviceStates[item.id] || ''} onChange={(event) => setDeviceStates((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="e.g. Equipment is currently stopped, PLC run bit is 0" className="w-full mt-1.5 resize-none" disabled={!canReview} />
                    </label>
                    <label className="block text-xs text-muted">Verification Notes
                      <textarea rows={3} value={notes[item.id] || ''} onChange={(event) => setNotes((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Describe verification method, time, and on-site supervisor" className="w-full mt-1.5 resize-none" disabled={!canReview} />
                    </label>
                    <button disabled={!canReview || busyId === item.id} onClick={() => reconcile(item)} className="btn btn-primary w-full"><SearchCheck size={15} />Submit Manual Verification</button>
                    {!canReview && <p className="text-xs text-muted">Read-only for current role; verification requires supervisor or admin.</p>}
                  </div>
                )}
                {item.status === 'executing' && (
                  <div className="lg:w-80 rounded-lg border border-blue-500/20 bg-blue-500/5 p-4 text-sm text-blue-200">
                    Command claimed; awaiting equipment gateway result. Will transition to manual verification upon timeout.
                  </div>
                )}
              </div>
            </article>
          ))}
          {!items.length && <div className="card text-center text-muted py-12">No {filter === 'pending' ? 'pending ' : ''}operations at this time</div>}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = { pending: 'Pending Approval', executing: 'Executing', execution_unknown: 'Pending Verification', approved: 'Approved', rejected: 'Rejected', execution_failed: 'Execution Failed' };
  const styles: Record<string, string> = { pending: 'bg-yellow-500/15 text-yellow-300', executing: 'bg-blue-500/15 text-blue-300', execution_unknown: 'bg-orange-500/15 text-orange-300', approved: 'bg-green-500/15 text-green-300', rejected: 'bg-gray-500/15 text-gray-300', execution_failed: 'bg-red-500/15 text-red-300' };
  return <span className={`badge ${styles[status] || styles.pending}`}>{labels[status] || status}</span>;
}

function reconciliationLabel(outcome: string) {
  const labels: Record<string, string> = { confirmed_executed: 'Confirmed Executed', confirmed_not_executed: 'Confirmed Not Executed', confirmed_failed: 'Confirmed Failed' };
  return labels[outcome] || outcome;
}
