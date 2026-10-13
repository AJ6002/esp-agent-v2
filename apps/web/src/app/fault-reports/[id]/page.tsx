'use client';
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { getFaultReport, convertFaultReportToWorkOrder } from '@/lib/api';
import { ApiError, URGENCY_LABELS, FAULT_REPORT_STATUS_LABELS } from '@/lib/types';
import { ArrowLeft, AlertTriangle, Wrench, Loader2, Clock, User, CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';

export default function FaultReportDetail() {
  const { id } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const frId = Number(id);

  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [converting, setConverting] = useState(false);

  const isSupervisorOrAdmin = user?.role === 'supervisor' || user?.role === 'admin';
  const canConvert = report && report.status === 'pending' && isSupervisorOrAdmin;

  useEffect(() => {
    if (!frId || isNaN(frId)) { setError('Invalid fault report ID'); setLoading(false); return; }
    setLoading(true);
    setError(null);
    getFaultReport(frId)
      .then(setReport)
      .catch((e: any) => setError(e.message || 'Failed to load'))
      .finally(() => setLoading(false));
  }, [frId]);

  const handleConvert = async () => {
    if (!report) return;
    const confirmed = window.confirm('Are you sure you want to convert this fault report to a work order?');
    if (!confirmed) return;
    setConverting(true);
    try {
      const result = await convertFaultReportToWorkOrder(frId);
      toast.success('Work order created successfully');
      router.push(`/work-orders/${result.work_order_id}`);
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 409 && e.workOrderId) {
        toast.error('A work order already exists for this fault report, redirecting...');
        router.push(`/work-orders/${e.workOrderId}`);
      } else {
        toast.error(e.message || 'Failed to create work order');
      }
      setConverting(false);
    }
  };

  const urgencyClass: Record<string, string> = {
    low: 'badge-p4', medium: 'badge-p3', high: 'badge-p2', critical: 'badge-p1',
  };
  const statusClass: Record<string, string> = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    converted: 'bg-blue-500/20 text-blue-400',
    closed: 'bg-gray-500/20 text-gray-400',
  };

  // Loading state
  if (loading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push('/fault-reports')} className="btn btn-outline btn-sm p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-xl font-bold">Fault Report Details</h1>
        </div>
        <div className="card text-center py-12 text-muted text-sm">Loading...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push('/fault-reports')} className="btn btn-outline btn-sm p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-xl font-bold">Fault Report Details</h1>
        </div>
        <div className="card text-center py-12">
          <AlertTriangle size={40} className="mx-auto mb-3 text-red-400" />
          <p className="text-red-400 text-sm mb-4">{error}</p>
          <button onClick={() => router.push('/fault-reports')} className="btn btn-outline btn-sm">Back to List</button>
        </div>
      </div>
    );
  }

  // Not found state
  if (!report) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push('/fault-reports')} className="btn btn-outline btn-sm p-2"><ArrowLeft size={16} /></button>
          <h1 className="text-xl font-bold">Fault Report Details</h1>
        </div>
        <div className="card text-center py-12">
          <AlertTriangle size={40} className="mx-auto mb-3 text-muted opacity-40" />
          <p className="text-muted text-sm mb-4">Fault report does not exist</p>
          <button onClick={() => router.push('/fault-reports')} className="btn btn-outline btn-sm">Back to List</button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push('/fault-reports')} className="btn btn-outline btn-sm p-2"><ArrowLeft size={16} /></button>
          <div>
            <h1 className="text-xl font-bold">Fault Report Details</h1>
            <p className="text-xs text-muted">ID #{report.id} · Created at {report.created_at?.split('T')[0]}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${urgencyClass[report.urgency] || ''}`}>{URGENCY_LABELS[report.urgency] || report.urgency}</span>
          <span className={`badge text-xs ${statusClass[report.status] || 'bg-gray-500/20 text-gray-400'}`}>{FAULT_REPORT_STATUS_LABELS[report.status] || report.status}</span>
        </div>
      </div>

      {/* Related Work Order Card */}
      {report.related_work_order_id && (
        <div className="card border-blue-500/30 bg-blue-500/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Wrench size={18} className="text-blue-400" />
              <div>
                <div className="text-sm font-medium">Linked Work Order</div>
                <div className="text-xs text-muted">
                  {report.related_work_order_code}
                  {report.related_work_order_status && <span className="ml-2">{report.related_work_order_status}</span>}
                </div>
              </div>
            </div>
            <button
              onClick={() => router.push(`/work-orders/${report.related_work_order_id}`)}
              className="btn btn-primary btn-sm text-xs"
            >
              <ExternalLink size={12} /> View Order
            </button>
          </div>
        </div>
      )}

      {/* Safety Risk Warning */}
      {report.has_safety_risk && (
        <div className="card border-red-500/30 bg-red-500/10">
          <div className="flex items-center gap-2 text-sm text-red-400">
            <AlertTriangle size={16} />
            <span className="font-medium">Safety Risk Warning</span>
          </div>
          <p className="text-xs text-red-400/70 mt-1">This fault involves safety risks. Follow strict safety operating procedures.</p>
        </div>
      )}

      {/* Main Info */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-sm">Basic Information</h2>

        {/* Title */}
        <div>
          <label className="text-xs text-muted">Fault Title</label>
          <p className="text-sm mt-0.5">{report.title}</p>
        </div>

        {/* Equipment */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted">Linked Equipment</label>
            <p className="text-sm mt-0.5">
              {report.equipment_code && report.equipment_name
                ? `${report.equipment_code} - ${report.equipment_name}`
                : 'Not linked'}
            </p>
          </div>
          <div>
            <label className="text-xs text-muted">Fault Code</label>
            <p className="text-sm mt-0.5">{report.fault_code_id ? `#${report.fault_code_id}` : 'Not specified'}</p>
          </div>
        </div>

        {/* Phenomenon + Urgency */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted">Phenomenon</label>
            <p className="text-sm mt-0.5">{report.phenomenon || 'None entered'}</p>
          </div>
          <div>
            <label className="text-xs text-muted">Urgency</label>
            <p className={`text-sm mt-0.5 font-medium ${report.urgency === 'critical' ? 'text-red-400' : report.urgency === 'high' ? 'text-yellow-400' : ''}`}>
              {URGENCY_LABELS[report.urgency] || report.urgency}
            </p>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="text-xs text-muted">Detailed Description</label>
          <p className="text-sm mt-0.5 whitespace-pre-wrap">{report.description}</p>
        </div>

        {/* Impact Flags */}
        <div>
          <label className="text-xs text-muted block mb-1.5">Impact Flags</label>
          <div className="flex gap-2 flex-wrap">
            <ImpactBadge label="Downtime" active={report.is_downtime} icon="●" color="red" />
            <ImpactBadge label="Production Affected" active={report.affects_production} icon="●" color="yellow" />
            <ImpactBadge label="Safety Risk" active={report.has_safety_risk} icon="▲" color="red" />
          </div>
        </div>

        {/* Time + Reporter */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted">Occurred At</label>
            <p className="text-sm mt-0.5 flex items-center gap-1">
              <Clock size={12} /> {report.occurred_at ? new Date(report.occurred_at).toLocaleString('en-US') : 'Not specified'}
            </p>
          </div>
          <div>
            <label className="text-xs text-muted">Reporter</label>
            <p className="text-sm mt-0.5 flex items-center gap-1">
              <User size={12} /> {report.reporter_name || 'Unknown'}
              {report.contact && <span className="text-xs text-muted ml-2">({report.contact})</span>}
            </p>
          </div>
        </div>
      </div>

      {/* AI Parsed Data */}
      {report.raw_text && (
        <div className="card space-y-3">
          <h2 className="font-semibold text-sm">AI Parsed Information</h2>
          <div>
            <label className="text-xs text-muted">Original Input</label>
            <p className="text-sm mt-0.5 text-muted bg-background rounded p-2">{report.raw_text}</p>
          </div>
          {report.parsed_fields && (
            <div>
              <label className="text-xs text-muted">Parsed Fields</label>
              <pre className="text-xs mt-0.5 text-muted bg-background rounded p-2 overflow-x-auto">
                {JSON.stringify(report.parsed_fields, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Photos */}
      {report.photos && report.photos.length > 0 && (
        <div className="card space-y-3">
          <h2 className="font-semibold text-sm">On-site Photos ({report.photos.length})</h2>
          <div className="grid grid-cols-3 gap-2">
            {report.photos.map((photo: string, i: number) => (
              <div key={i} className="aspect-square bg-background rounded-lg flex items-center justify-center text-xs text-muted">
                Photo {i + 1}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Related Work Order State */}
      {!report.related_work_order_id && report.status === 'pending' && (
        <div className="card border-card-border bg-card space-y-3">
          <div className="flex items-center gap-2 text-sm text-muted">
            <Wrench size={16} />
            <span>No work order created yet</span>
          </div>
          {canConvert ? (
            <button onClick={handleConvert} disabled={converting} className="btn btn-primary w-full" data-testid="create-work-order-button">
              {converting ? <><Loader2 size={14} className="animate-spin" /> Creating...</> : <><Wrench size={14} /> Create Work Order</>}
            </button>
          ) : !isSupervisorOrAdmin && (
            <p className="text-xs text-muted">Only supervisors and admins can create work orders</p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button onClick={() => router.push('/fault-reports')} className="btn btn-outline flex-1">
          <ArrowLeft size={14} /> Back to List
        </button>
        {canConvert && (
          <button onClick={handleConvert} disabled={converting} className="btn btn-primary flex-1" data-testid="create-work-order-button-bottom">
            {converting ? <><Loader2 size={14} className="animate-spin" /> Creating...</> : <><Wrench size={14} /> Create Work Order</>}
          </button>
        )}
        {report.related_work_order_id && (
          <button
            onClick={() => router.push(`/work-orders/${report.related_work_order_id}`)}
            className="btn btn-outline flex-1"
          >
            <ExternalLink size={14} /> View Linked Work Order
          </button>
        )}
      </div>
    </div>
  );
}

function ImpactBadge({ label, active, icon, color }: { label: string; active: boolean; icon: string; color: string }) {
  const colorClasses: Record<string, string> = {
    red: 'border-red-500/30 bg-red-500/10 text-red-400',
    yellow: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-400',
  };
  const inactiveClasses = active ? colorClasses[color] : 'border-card-border bg-card-border/5 text-muted line-through';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs ${inactiveClasses}`}>
      <span className="text-[10px]">{icon}</span> {label}
    </span>
  );
}
