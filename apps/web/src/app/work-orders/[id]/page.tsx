'use client';
import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import {
  getWorkOrder, acceptWorkOrder, startWorkOrder, pauseWorkOrder, resumeWorkOrder,
  submitWorkOrder, approveWorkOrder, rejectWorkOrder,
  addMaintenanceLog, addLaborEntry, addSparePartUsage, copilotDiagnose,
  copilotRewriteLog, addAttachment, cancelWorkOrder
} from '@/lib/api';
import { STATUS_LABELS, PRIORITY_LABELS, LOG_TYPE_LABELS, CompletionValidationError } from '@/lib/types';
import { Wrench, Clock, CheckCircle, AlertTriangle, Play, Pause, Send, XCircle, RefreshCw, Bot, Shield, Camera } from 'lucide-react';
import SafetyChecklist from '@/components/work-orders/safety-checklist';
import CompletionValidationDisplay from '@/components/work-orders/completion-validation';
import MaintenanceReport from '@/components/work-orders/maintenance-report';
import toast from 'react-hot-toast';

export default function WorkOrderDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const router = useRouter();
  const [wo, setWo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [diag, setDiag] = useState<any>(null);
  const [diagLoading, setDiagLoading] = useState(false);
  // Maintenance log form
  const [newLog, setNewLog] = useState({ log_type: 'note', content: '', photos: [] as string[] });
  const [polishedText, setPolishedText] = useState('');
  // Labor hours
  const [laborForm, setLaborForm] = useState({ started_at: '', ended_at: '', hours: 0, is_downtime: false, remark: '' });
  // Spare parts
  const [spForm, setSpForm] = useState({ spare_part_name: '', quantity: 1, unit: 'pcs', remark: '' });
  // Completion
  const [submitForm, setSubmitForm] = useState({ root_cause: '', action_taken: '', replaced_parts: '', test_result: '', equipment_status_after: 'running', follow_up_advice: '', needs_observation: false, completion_photos: [] as string[] });
  // Rejection reason
  const [rejectReason, setRejectReason] = useState('');
  // Completion validation error
  const [validationError, setValidationError] = useState<CompletionValidationError | null>(null);
  // High-risk work safety confirmation (atomic submission with start/resume)
  const [safetyAction, setSafetyAction] = useState<'start' | 'resume' | null>(null);
  const [safetyConfirmed, setSafetyConfirmed] = useState(false);
  const [safetyNote, setSafetyNote] = useState('');
  // Uploading
  const [uploading, setUploading] = useState(false);

  // Request sequence guard: this page has multiple concurrent refresh triggers (accept/start, checklist toggle, log addition, etc.).
  // In slow environments, an earlier GET may return later; without a guard, a stale response could overwrite and roll back persisted state.
  const fetchSeqRef = useRef(0);
  const fetch = useCallback(async () => {
    const seq = ++fetchSeqRef.current;
    try {
      const d = await getWorkOrder(Number(id));
      if (seq === fetchSeqRef.current) setWo(d);
    } catch (e: any) { toast.error(e.message); } finally {
      if (seq === fetchSeqRef.current) setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetch(); }, [fetch]);

  useEffect(() => { setValidationError(null); }, [wo?.status]);

  const handleAction = async (action: string, data?: any) => {
    try {
      const actions: any = { accept: acceptWorkOrder, pause: pauseWorkOrder, cancel: cancelWorkOrder };
      if (action === 'submit') {
        setValidationError(null);
        const result = await submitWorkOrder(Number(id), data || submitForm);
        // submitWorkOrder either returns WorkOrderDetail on success or throws
      } else if (action === 'approve') await approveWorkOrder(Number(id));
      else if (action === 'reject') {
        if (!rejectReason || !rejectReason.trim()) { toast.error('Please enter a rejection reason'); return; }
        await rejectWorkOrder(Number(id), rejectReason);
        setRejectReason('');
      } else if (action === 'start') await startWorkOrder(Number(id), data);
      else if (action === 'resume') await resumeWorkOrder(Number(id), data);
      else if (actions[action]) await actions[action](Number(id));
      if (action === 'start' || action === 'resume') {
        setSafetyAction(null);
        setSafetyConfirmed(false);
        setSafetyNote('');
      }
      toast.success('Operation succeeded');
      fetch();
    } catch (e: any) {
      // Handle completion validation error (422)
      if (action === 'submit' && e.status === 422) {
        setValidationError({
          code: 'WORK_ORDER_COMPLETION_VALIDATION_FAILED',
          message: e.message || 'Work order does not meet completion criteria yet',
          missing_requirements: (e as any).response?.data?.missing_requirements || [],
        });
        return;
      }
      toast.error(e.message);
    }
  };

  const addLog = async () => {
    if (!newLog.content) return toast.error('Please enter content');
    try {
      await addMaintenanceLog(Number(id), { ...newLog, logged_at: new Date().toISOString() });
      setNewLog({ log_type: 'note', content: '', photos: [] });
      setPolishedText('');
      fetch();
      toast.success('Log added');
    } catch (e: any) { toast.error(e.message); }
  };

  const addLabor = async () => {
    if (!laborForm.hours || laborForm.hours <= 0) return toast.error('Please enter valid labor hours');
    try {
      await addLaborEntry(Number(id), {
        ...laborForm,
        started_at: laborForm.started_at || null,
        ended_at: laborForm.ended_at || null,
      });
      setLaborForm({ started_at: '', ended_at: '', hours: 0, is_downtime: false, remark: '' });
      fetch();
      toast.success('Labor logged');
    } catch (e: any) { toast.error(e.message); }
  };

  const addSpare = async () => {
    if (!spForm.spare_part_name) return toast.error('Please enter spare part name');
    if (spForm.quantity <= 0) return toast.error('Quantity must be greater than 0');
    try {
      await addSparePartUsage(Number(id), spForm);
      setSpForm({ spare_part_name: '', quantity: 1, unit: 'pcs', remark: '' });
      fetch();
      toast.success('Spare part recorded');
    } catch (e: any) { toast.error(e.message); }
  };

  const doUploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await addAttachment(Number(id), file);
      setSubmitForm(prev => ({
        ...prev,
        completion_photos: [...(prev.completion_photos || []), result.url],
      }));
      toast.success('Photo uploaded');
    } catch (ex: any) { toast.error(ex.message); }
    finally { setUploading(false); }
  };

  const runDiagnosis = async () => {
    setDiagLoading(true);
    try {
      const result = await copilotDiagnose({ work_order_id: Number(id), fault_description: wo.fault_description || wo.title, equipment_id: wo.equipment_id, fault_code: wo.fault_code });
      setDiag(result);
    } catch (e: any) { toast.error(e.message); } finally { setDiagLoading(false); }
  };

  const runRewrite = async () => {
    if (!newLog.content) return;
    try { const r = await copilotRewriteLog(newLog.content); setPolishedText(r.polished); } catch {}
  };

  const doSubmit = () => {
    if (!submitForm.root_cause || !submitForm.action_taken || !submitForm.test_result) {
      toast.error('Please fill in root cause, corrective actions, and test results');
      return;
    }
    handleAction('submit', submitForm);
  };

  const requestExecution = (action: 'start' | 'resume') => {
    if (!wo.requires_safety_confirmation) {
      handleAction(action);
      return;
    }
    setSafetyAction(action);
    setSafetyConfirmed(false);
    setSafetyNote('');
  };

  const confirmHighRiskExecution = () => {
    if (!safetyAction) return;
    handleAction(safetyAction, { confirmed: safetyConfirmed, note: safetyNote.trim() });
  };

  const getStatusClass = (s: string) => {
    const m: any = { pending_dispatch: 'text-gray-400', assigned: 'text-blue-400', accepted: 'text-purple-400', in_progress: 'text-yellow-400', pending_acceptance: 'text-green-400', completed: 'text-green-500', returned: 'text-red-400', paused: 'text-gray-400' };
    return m[s] || '';
  };

  if (loading) return <div className="text-muted p-6">Loading...</div>;
  if (!wo) return <div className="text-muted p-6">Work order not found</div>;

  const isTech = user?.role === 'technician';
  const isSupervisor = user?.role === 'supervisor' || user?.role === 'admin';
  const isAssignee = wo.assignee_id === user?.id;
  const canEdit = isAssignee && ['accepted', 'in_progress', 'paused', 'returned'].includes(wo.status);
  const canSubmit = isAssignee && wo.status === 'in_progress';
  const canApprove = isSupervisor && wo.status === 'pending_acceptance';
  const isReadonly = wo.status === 'completed' || wo.status === 'cancelled';
  const requiredSafetyItems = (wo.checklist_items || []).filter((item: any) => item.category === 'safety' && item.is_required);
  const safetyChecklistComplete = requiredSafetyItems.length > 0 && requiredSafetyItems.every((item: any) => item.is_completed);

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-lg font-bold">{wo.title}</h1>
          <p className="text-sm text-muted">{wo.code} - {wo.equipment_name || 'Unknown Equipment'}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${getStatusClass(wo.status)}`}>{STATUS_LABELS[wo.status]}</span>
          <PriorityBadge priority={wo.priority} />
        </div>
      </div>

      {/* Action Buttons */}
      {!isReadonly && (canEdit || canSubmit || canApprove || (isSupervisor && ['pending_dispatch', 'assigned'].includes(wo.status)) || (isAssignee && wo.status === 'assigned')) && (
        <div className="card flex flex-wrap gap-2" data-testid="action-buttons">
          {isAssignee && wo.status === 'assigned' && <button onClick={() => handleAction('accept')} className="btn btn-primary" data-testid="accept-work-order-button"><Play size={16} /> Accept Work Order</button>}
          {isAssignee && wo.status === 'accepted' && <button onClick={() => requestExecution('start')} className="btn btn-success"><Play size={16} /> Start Repair</button>}
          {isAssignee && wo.status === 'in_progress' && <button onClick={() => handleAction('pause')} className="btn btn-outline"><Pause size={16} /> Pause</button>}
          {isAssignee && wo.status === 'paused' && <button onClick={() => requestExecution('resume')} className="btn btn-success"><Play size={16} /> Resume</button>}
          {isAssignee && wo.status === 'returned' && <button onClick={() => requestExecution('start')} className="btn btn-primary"><RefreshCw size={16} /> Rework</button>}
          {canSubmit && <button onClick={doSubmit} className="btn btn-primary"><Send size={16} /> Submit Completion</button>}
          {canApprove && <><button onClick={() => handleAction('approve')} className="btn btn-success"><CheckCircle size={16} /> Approve</button></>}
          {isSupervisor && ['pending_dispatch', 'assigned'].includes(wo.status) && <button onClick={() => handleAction('cancel')} className="btn btn-outline"><XCircle size={16} /> Cancel Work Order</button>}
        </div>
      )}

      {safetyAction && (
        <div className="card border-red-500/40 bg-red-500/10 space-y-3" data-testid="high-risk-safety-confirmation">
          <div className="flex items-start gap-2">
            <Shield size={18} className="text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <h2 className="font-semibold text-red-300">High-Risk Work Safety Confirmation</h2>
              <p className="text-xs text-red-200 mt-1">All mandatory safety checklist items must be completed first; this confirmation will be recorded with the start action. Resuming after pause requires re-confirmation.</p>
            </div>
          </div>
          {!safetyChecklistComplete && (
            <p className="text-sm text-yellow-300">Please complete all mandatory safety items in the maintenance checklist first.</p>
          )}
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={safetyConfirmed}
              onChange={e => setSafetyConfirmed(e.target.checked)}
              className="mt-1"
            />
            <span>I have verified machine shutdown, energy isolation, LOTO, residual energy dissipation, and PPE on-site</span>
          </label>
          <textarea
            value={safetyNote}
            onChange={e => setSafetyNote(e.target.value)}
            rows={2}
            maxLength={500}
            className="w-full text-sm"
            placeholder="Enter on-site safety confirmation notes (at least 8 characters)"
          />
          <div className="flex gap-2">
            <button
              onClick={confirmHighRiskExecution}
              disabled={!safetyChecklistComplete || !safetyConfirmed || safetyNote.trim().length < 8}
              className="btn btn-danger"
            >
              Confirm safety measures and {wo.status === 'paused' ? 'resume repair' : 'start repair'}
            </button>
            <button onClick={() => setSafetyAction(null)} className="btn btn-outline">Cancel</button>
          </div>
        </div>
      )}

      {/* Rejection Reason Display */}
      {wo.status === 'returned' && wo.rejection_reason && (
        <div className="card border-red-500/30 bg-red-500/10" data-testid="rejection-reason">
          <div className="flex items-start gap-2">
            <XCircle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-400">Work Order Returned</p>
              <p className="text-sm text-red-300 mt-1">{wo.rejection_reason}</p>
            </div>
          </div>
        </div>
      )}

      {/* Completion Validation Error */}
      {validationError && <CompletionValidationDisplay error={validationError} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Info */}
          <div className="card">
            <h2 className="font-semibold mb-3">Basic Information</h2>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Info label="Equipment" value={wo.equipment_name} />
              <Info label="Priority" value={<PriorityBadge priority={wo.priority} />} />
              <Info label="Type" value={wo.order_type === 'fault_repair' ? 'Fault Repair' : wo.order_type} />
              <Info label="Assignee" value={wo.assignee_name || 'Unassigned'} />
              <Info label="Fault Code" value={wo.fault_code || '-'} />
              <Info label="Planned Completion" value={wo.planned_end_at?.split('T')[0] || '-'} />
            </div>
            {wo.fault_description && (
              <div className="mt-3 text-sm">
                <div className="text-muted mb-1">Fault Description</div>
                <div className="p-2 rounded bg-white/5">{wo.fault_description}</div>
              </div>
            )}
            {/* Source Reference */}
            {wo.fault_report_id && !wo.fault_description && (
              <div className="mt-2 text-xs text-muted">
                Source: <button className="underline hover:text-white" onClick={() => router.push(`/fault-reports/${wo.fault_report_id}`)}>Fault Report #{wo.fault_report_id}</button>
              </div>
            )}
            {wo.safety_risk && (
              <div className="mt-3 p-3 rounded border border-red-500/30 bg-red-500/10 text-sm" data-testid="safety-risk-warning">
                <div className="flex items-start gap-2">
                  <Shield size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-red-400">Safety Risk</p>
                    <p className="text-red-300 mt-0.5">{wo.safety_risk}</p>
                    {(wo.safety_risk || '').toLowerCase().includes('live') && (
                      <p className="text-red-500 mt-1 text-xs font-bold">Live electrical work strictly prohibited! Ensure power is disconnected before repair.</p>
                    )}
                    {['bypass', 'interlock', 'short'].some(k => (wo.safety_risk || '').toLowerCase().includes(k)) && (
                      <p className="text-red-500 mt-1 text-xs font-bold">Strictly prohibited to bypass protective devices or safety interlocks!</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* AI Diagnosis */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold flex items-center gap-2"><Bot size={16} /> AI Diagnostic Suggestions</h2>
              <button onClick={runDiagnosis} disabled={diagLoading} className="btn btn-sm btn-outline">{diagLoading ? 'Analyzing...' : diag ? 'Re-analyze' : 'Get Suggestions'}</button>
            </div>
            {diag ? (
              <div className="space-y-3 text-sm">
                {diag.possible_causes?.length > 0 && <div><div className="text-muted mb-1">Possible Causes</div>{diag.possible_causes.map((c: any, i: number) => <div key={i} className="flex items-center gap-2 p-1.5"><span className={`badge ${c.confidence > 0.6 ? 'badge-p1' : 'badge-p3'}`}>{Math.round(c.confidence * 100)}%</span> {c.cause}</div>)}</div>}
                {diag.inspection_order?.length > 0 && <div><div className="text-muted mb-1">Recommended Inspection Order</div><ol className="list-decimal pl-5 space-y-0.5">{diag.inspection_order.map((s: string, i: number) => <li key={i}>{s}</li>)}</ol></div>}
                {diag.safety_notes?.length > 0 && <div className="p-2 rounded bg-red-500/10 border border-red-500/20"><div className="text-muted mb-1">Safety Precautions</div>{diag.safety_notes.map((s: string, i: number) => <div key={i} className="flex items-start gap-1"><AlertTriangle size={12} className="mt-1 text-red-400 flex-shrink-0" /> {s}</div>)}</div>}
                {diag.similar_cases?.length > 0 && <div><div className="text-muted mb-1">Similar Cases</div>{diag.similar_cases.map((c: any) => <div key={c.work_order_id} className="flex items-center gap-2 p-1.5"><span className="badge badge-p3">{Math.round(c.similarity * 100)}%</span> {c.code} - {c.root_cause || c.title}</div>)}</div>}
                <div className="text-xs text-muted border-t border-card-border pt-2">{diag.disclaimer}</div>
              </div>
            ) : <p className="text-sm text-muted">{'Click "Get Suggestions" to let AI assist in fault diagnosis'}</p>}
          </div>

          {/* Checklist — uses SafetyChecklist component */}
          <div className="card">
            <h2 className="font-semibold mb-3">Maintenance Checklist</h2>
            <SafetyChecklist
              workOrderId={Number(id)}
              items={wo.checklist_items || []}
              canEdit={canEdit}
              onRefresh={fetch}
            />
          </div>

          {/* Maintenance Logs */}
          <div className="card">
            <h2 className="font-semibold mb-3">Maintenance Logs</h2>
            <div className="space-y-3 mb-4 max-h-80 overflow-y-auto">
              {wo.logs?.length > 0 ? wo.logs.map((log: any) => (
                <div key={log.id} className="p-2 rounded bg-white/5 text-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="badge badge-p3">{LOG_TYPE_LABELS[log.log_type] || log.log_type}</span>
                    <span className="text-xs text-muted">{log.operator_name} - {log.logged_at?.split('T')[0]} {log.logged_at?.split('T')[1]?.split('.')[0]}</span>
                  </div>
                  <div>{log.content}</div>
                  {log.ai_polished && <div className="mt-1 p-1.5 rounded bg-primary/10 text-xs"><span className="text-primary-300 font-medium">AI Polished:</span> {log.ai_polished}</div>}
                </div>
              )) : <p className="text-sm text-muted">No records yet</p>}
            </div>
            {canEdit && (
              <div className="space-y-2 border-t border-card-border pt-3" data-testid="add-log-form">
                <div className="flex gap-2">
                  <select value={newLog.log_type} onChange={e => setNewLog({ ...newLog, log_type: e.target.value })} className="text-sm" data-testid="log-type-select">
                    {Object.entries(LOG_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                  <button onClick={runRewrite} className="btn btn-sm btn-outline" title="AI Polish"><Bot size={14} /></button>
                </div>
                <textarea value={newLog.content} onChange={e => setNewLog({ ...newLog, content: e.target.value })} rows={3} className="w-full text-sm" placeholder="Record maintenance process..." data-testid="log-content-input" />
                {polishedText && (
                  <div className="p-2 rounded bg-primary/10 text-xs text-primary-300" data-testid="polished-suggestion">
                    Suggested Version: {polishedText}
                    <button onClick={() => setNewLog({ ...newLog, content: polishedText })} className="ml-2 underline">Apply</button>
                  </div>
                )}
                <button onClick={addLog} className="btn btn-primary btn-sm" data-testid="add-log-button">Add Log</button>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Labor */}
          <div className="card" data-testid="labor-section">
            <h3 className="font-semibold text-sm mb-2">Labor Records</h3>
            {wo.labor_entries?.length > 0 ? wo.labor_entries.map((e: any) => (
              <div key={e.id} className="text-xs py-1 flex justify-between border-b border-card-border last:border-0">
                <span>{e.hours}h {e.is_downtime && <span className="text-red-400 ml-1">(Downtime)</span>}</span>
                <span className="text-muted">{e.operator_name}</span>
              </div>
            )) : <p className="text-xs text-muted">None</p>}
            {canEdit && (
              <div className="space-y-1.5 mt-2 pt-2 border-t border-card-border" data-testid="add-labor-form">
                <input type="number" value={laborForm.hours || ''} onChange={e => setLaborForm({ ...laborForm, hours: Number(e.target.value) })} placeholder="Hours" className="w-full text-sm" step="0.5" min="0.5" data-testid="labor-hours-input" />
                <div className="flex gap-2">
                  <label className="flex items-center gap-1 text-xs cursor-pointer">
                    <input type="checkbox" checked={laborForm.is_downtime} onChange={e => setLaborForm({ ...laborForm, is_downtime: e.target.checked })} data-testid="labor-downtime-checkbox" /> Downtime Hours
                  </label>
                </div>
                <input value={laborForm.remark} onChange={e => setLaborForm({ ...laborForm, remark: e.target.value })} placeholder="Remarks" className="w-full text-sm" />
                <button onClick={addLabor} className="btn btn-primary btn-sm btn-block" data-testid="add-labor-button">Log Labor</button>
              </div>
            )}
          </div>

          {/* Spare Parts */}
          <div className="card" data-testid="spare-parts-section">
            <h3 className="font-semibold text-sm mb-2">Spare Parts Used</h3>
            {wo.spare_parts?.length > 0 ? wo.spare_parts.map((s: any) => (
              <div key={s.id} className="text-xs py-1 flex justify-between border-b border-card-border last:border-0">
                <span>{s.spare_part_name} x{s.quantity}{s.unit}</span>
                {s.remark && <span className="text-muted">{s.remark}</span>}
              </div>
            )) : <p className="text-xs text-muted">None</p>}
            {canEdit && (
              <div className="space-y-1.5 mt-2 pt-2 border-t border-card-border" data-testid="add-spare-form">
                <input value={spForm.spare_part_name} onChange={e => setSpForm({ ...spForm, spare_part_name: e.target.value })} placeholder="Spare Part Name" className="w-full text-sm" data-testid="spare-name-input" />
                <div className="flex gap-2">
                  <input type="number" value={spForm.quantity} onChange={e => setSpForm({ ...spForm, quantity: Number(e.target.value) })} placeholder="Quantity" className="w-20 text-sm" min="0.1" step="0.1" />
                  <input value={spForm.unit} onChange={e => setSpForm({ ...spForm, unit: e.target.value })} placeholder="Unit" className="w-16 text-sm" />
                </div>
                <button onClick={addSpare} className="btn btn-primary btn-sm btn-block" data-testid="add-spare-button">Add Spare Part</button>
              </div>
            )}
          </div>

          {/* Status History */}
          <div className="card">
            <h3 className="font-semibold text-sm mb-2">Status History</h3>
            <div className="space-y-1 text-xs">
              {wo.status_history?.length > 0 ? wo.status_history.map((h: any, i: number) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-muted w-20">{h.changed_at?.split('T')[0]}</span>
                  <span className="font-mono">{h.from_status || '-'} → {h.to_status}</span>
                </div>
              )) : <p className="text-xs text-muted">None</p>}
            </div>
          </div>
        </div>
      </div>

      {/* Submit Section (when in_progress) */}
      {canSubmit && (
        <div className="card" data-testid="submit-section">
          <h2 className="font-semibold mb-3">Completion Details</h2>
          <div className="space-y-3">
            <div><label className="block text-sm mb-1">Root Cause *</label><textarea value={submitForm.root_cause} onChange={e => setSubmitForm({ ...submitForm, root_cause: e.target.value })} rows={2} className="w-full" placeholder="Root cause of the fault" data-testid="root-cause-input" /></div>
            <div><label className="block text-sm mb-1">Corrective Actions *</label><textarea value={submitForm.action_taken} onChange={e => setSubmitForm({ ...submitForm, action_taken: e.target.value })} rows={2} className="w-full" placeholder="Corrective actions taken" data-testid="action-taken-input" /></div>
            <div><label className="block text-sm mb-1">Replaced Parts</label><input value={submitForm.replaced_parts} onChange={e => setSubmitForm({ ...submitForm, replaced_parts: e.target.value })} className="w-full" placeholder="Replaced parts (comma-separated)" /></div>
            <div><label className="block text-sm mb-1">Test Results *</label><textarea value={submitForm.test_result} onChange={e => setSubmitForm({ ...submitForm, test_result: e.target.value })} rows={2} className="w-full" placeholder="Test results" data-testid="test-result-input" /></div>
            <div><label className="block text-sm mb-1">Post-Repair Equipment Status</label>
              <select value={submitForm.equipment_status_after} onChange={e => setSubmitForm({ ...submitForm, equipment_status_after: e.target.value })} className="text-sm" data-testid="equipment-status-select">
                <option value="running">Running</option>
                <option value="fault">Faulted</option>
                <option value="stopped">Stopped</option>
              </select>
            </div>
            <div><label className="block text-sm mb-1">Follow-up Recommendations</label><textarea value={submitForm.follow_up_advice} onChange={e => setSubmitForm({ ...submitForm, follow_up_advice: e.target.value })} rows={2} className="w-full" placeholder="Follow-up maintenance recommendations" /></div>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={submitForm.needs_observation} onChange={e => setSubmitForm({ ...submitForm, needs_observation: e.target.checked })} />
              Requires further observation
            </label>

            {/* Photo upload for high-risk */}
            {wo.safety_risk && (
              <div className="pt-2 border-t border-card-border">
                <label className="block text-sm mb-1">Completion Photos (Mandatory for high-risk work orders)</label>
                <div className="flex items-center gap-2">
                  <label className="btn btn-sm btn-outline cursor-pointer">
                    <Camera size={14} /> {uploading ? 'Uploading...' : 'Upload Photo'}
                    <input
                      type="file"
                      accept="image/*"
                      onChange={doUploadPhoto}
                      className="hidden"
                      disabled={uploading}
                      data-testid="completion-photo-input"
                    />
                  </label>
                  {submitForm.completion_photos?.length > 0 && (
                    <span className="text-xs text-green-400">{submitForm.completion_photos.length} uploaded</span>
                  )}
                </div>
              </div>
            )}

            <button onClick={doSubmit} className="btn btn-primary btn-block" data-testid="submit-completion-button">
              <Send size={16} /> Submit Completion
            </button>
          </div>
        </div>
      )}

      {/* Approval Section (supervisor) */}
      {canApprove && (
        <div className="card space-y-4" data-testid="approval-section">
          <h2 className="font-semibold">Supervisor Sign-off</h2>

          {/* Completion summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div><div className="text-muted text-xs">Root Cause</div><div className="mt-0.5">{wo.root_cause}</div></div>
            <div><div className="text-muted text-xs">Corrective Actions</div><div className="mt-0.5">{wo.action_taken}</div></div>
            <div><div className="text-muted text-xs">Test Results</div><div className="mt-0.5">{wo.test_result}</div></div>
            <div><div className="text-muted text-xs">Replaced Parts</div><div className="mt-0.5">{wo.replaced_parts || 'None'}</div></div>
          </div>

          {/* Labor summary */}
          {wo.labor_entries?.length > 0 && (
            <div className="text-sm pt-2 border-t border-card-border">
              <div className="text-muted text-xs mb-1">Labor Summary</div>
              <div className="flex gap-4">
                <span>Total Hours: {wo.labor_entries.reduce((sum: number, e: any) => sum + e.hours, 0).toFixed(1)}h</span>
                <span className="text-red-400">Downtime Hours: {wo.labor_entries.filter((e: any) => e.is_downtime).reduce((sum: number, e: any) => sum + e.hours, 0).toFixed(1)}h</span>
              </div>
            </div>
          )}

          {/* Spare parts summary */}
          {wo.spare_parts?.length > 0 && (
            <div className="text-sm pt-2 border-t border-card-border">
              <div className="text-muted text-xs mb-1">Spare Parts Summary</div>
              {wo.spare_parts.map((s: any) => (
                <div key={s.id} className="text-xs">{s.spare_part_name} x{s.quantity}{s.unit}</div>
              ))}
            </div>
          )}

          {/* Follow-up */}
          {wo.follow_up_advice && (
            <div className="text-sm pt-2 border-t border-card-border">
              <div className="text-muted text-xs">Follow-up Recommendations</div>
              <div className="mt-0.5">{wo.follow_up_advice}</div>
            </div>
          )}

          {wo.needs_observation && <div className="badge badge-p2">Requires Observation</div>}

          {/* Action buttons */}
          <div className="flex gap-2 pt-2 border-t border-card-border">
            <button onClick={() => handleAction('approve')} className="btn btn-success flex-1" data-testid="approve-button">
              <CheckCircle size={16} /> Approve
            </button>
            <div className="flex-1 flex flex-col gap-2">
              <textarea
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                rows={2}
                className="w-full text-sm"
                placeholder="Rejection reason (required)"
                data-testid="reject-reason-input"
              />
              <button
                onClick={() => handleAction('reject')}
                className="btn btn-danger btn-sm"
                disabled={!rejectReason.trim()}
                data-testid="reject-button"
              >
                <XCircle size={16} /> Reject & Return
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Maintenance Report for completed orders */}
      {wo.status === 'completed' && (
        <MaintenanceReport workOrderId={Number(id)} />
      )}

      {/* Readonly info for cancelled */}
      {wo.status === 'cancelled' && (
        <div className="card">
          <div className="flex items-center gap-2 text-muted">
            <XCircle size={16} />
            <span>This work order has been cancelled</span>
          </div>
        </div>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: any }) {
  return <div><span className="text-muted text-xs">{label}</span><div className="text-sm">{value}</div></div>;
}

function PriorityBadge({ priority }: { priority: string }) {
  const cls: any = { P1: 'badge-p1', P2: 'badge-p2', P3: 'badge-p3', P4: 'badge-p4' };
  return <span className={`badge ${cls[priority] || ''}`}>{PRIORITY_LABELS[priority] || priority}</span>;
}
