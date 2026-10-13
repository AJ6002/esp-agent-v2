'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { parseFaultText, createFaultReport, convertFaultReportToWorkOrder, listEquipment, listFaultCodes } from '@/lib/api';
import { ApiError } from '@/lib/types';
import { Sparkles, AlertTriangle, Loader2, ArrowLeft, Check, Edit3, Send } from 'lucide-react';
import toast from 'react-hot-toast';

export default function NewFaultReport() {
  const router = useRouter();

  // AI parse state
  const [rawText, setRawText] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parsed, setParsed] = useState<any>(null);

  // Form state
  const [equipmentId, setEquipmentId] = useState<number | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [phenomenon, setPhenomenon] = useState('');
  const [urgency, setUrgency] = useState('medium');
  const [isDowntime, setIsDowntime] = useState(false);
  const [affectsProduction, setAffectsProduction] = useState(false);
  const [hasSafetyRisk, setHasSafetyRisk] = useState(false);
  const [faultCode, setFaultCode] = useState('');
  const [reporterName, setReporterName] = useState('');
  const [contact, setContact] = useState('');
  const [occurredAt, setOccurredAt] = useState('');

  // Equipment list
  const [equipment, setEquipment] = useState<any[]>([]);
  const [equipSearch, setEquipSearch] = useState('');
  const [faultCodes, setFaultCodes] = useState<any[]>([]);

  // Submit state
  const [submitting, setSubmitting] = useState(false);
  const [createWO, setCreateWO] = useState(false);

  useEffect(() => {
    listEquipment({ page_size: '200' }).then(d => setEquipment(d.items)).catch(() => {});
    listFaultCodes().then(setFaultCodes).catch(() => {});
    setOccurredAt(new Date().toISOString().slice(0, 16));
  }, []);

  const handleParse = async () => {
    if (!rawText.trim()) { toast.error('Please enter fault description'); return; }
    setParsing(true);
    try {
      const result = await parseFaultText(rawText);
      setParsed(result);
      setTitle(result.title || '');
      setDescription(result.description || '');
      setPhenomenon(result.phenomenon || '');
      setUrgency(result.urgency || 'medium');
      setIsDowntime(result.is_downtime || false);
      setAffectsProduction(result.affects_production || false);
      setHasSafetyRisk(result.has_safety_risk || false);
      setFaultCode(result.fault_code || '');
      if (result.equipment_id) {
        setEquipmentId(result.equipment_id);
        const eq = equipment.find(e => e.id === result.equipment_id);
        if (eq) setEquipSearch(`${eq.code} ${eq.name}`);
      } else if (result.equipment_keyword) {
        setEquipSearch(result.equipment_keyword);
      }
      toast.success(result.confidence > 0.5 ? 'AI parsing complete. Please review and edit.' : 'AI parsing complete with low confidence. Please verify carefully.');
    } catch (e: any) {
      toast.error(e.message || 'Parsing failed. Please fill in manually.');
    } finally {
      setParsing(false);
    }
  };

  const resolveFaultCodeId = (): number | undefined => {
    if (!faultCode.trim()) return undefined;
    const match = faultCodes.find(fc => fc.code === faultCode.trim());
    return match?.id;
  };

  const handleSubmit = async () => {
    if (!title.trim()) { toast.error('Please enter fault title'); return; }
    if (!description.trim()) { toast.error('Please enter fault description'); return; }
    setSubmitting(true);
    try {
      const payload: any = {
        title: title.trim(),
        description: description.trim(),
        urgency,
        is_downtime: isDowntime,
        affects_production: affectsProduction,
        has_safety_risk: hasSafetyRisk,
        reporter_name: reporterName.trim() || undefined,
        contact: contact.trim() || undefined,
        raw_text: rawText.trim() || undefined,
        parsed_fields: parsed || undefined,
      };
      if (equipmentId) payload.equipment_id = equipmentId;
      if (phenomenon.trim()) payload.phenomenon = phenomenon.trim();
      const fcId = resolveFaultCodeId();
      if (fcId) payload.fault_code_id = fcId;
      if (occurredAt) payload.occurred_at = new Date(occurredAt).toISOString();

      const fr = await createFaultReport(payload);

      if (createWO) {
        try {
          const result = await convertFaultReportToWorkOrder(fr.id);
          toast.success('Fault reported and work order generated');
          router.push(`/work-orders/${result.work_order_id}`);
          return;
        } catch (e: any) {
          if (e instanceof ApiError && e.status === 409 && e.workOrderId) {
            toast.success('Fault reported, work order already exists, redirecting...');
            router.push(`/work-orders/${e.workOrderId}`);
            return;
          }
          toast.error('Fault reported, but work order creation failed. Please create it manually from the details page.');
          router.push(`/fault-reports/${fr.id}`);
          return;
        }
      }

      toast.success('Fault reported successfully');
      router.push(`/fault-reports/${fr.id}`);
    } catch (e: any) {
      toast.error(e.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const urgencyOptions = [
    { value: 'low', label: 'Low', desc: 'No operational impact' },
    { value: 'medium', label: 'Medium', desc: 'Scheduled maintenance' },
    { value: 'high', label: 'High', desc: 'Affects production' },
    { value: 'critical', label: 'Critical', desc: 'Downtime / safety risk' },
  ];

  const filteredEquipment = equipSearch
    ? equipment.filter(e =>
        e.name.toLowerCase().includes(equipSearch.toLowerCase()) ||
        e.code.toLowerCase().includes(equipSearch.toLowerCase()) ||
        (e.plant || '').toLowerCase().includes(equipSearch.toLowerCase())
      ).slice(0, 10)
    : equipment.slice(0, 10);

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} className="btn btn-outline btn-sm p-2">
          <ArrowLeft size={16} />
        </button>
        <div>
          <h1 className="text-xl font-bold">New Fault Report</h1>
          <p className="text-xs text-muted mt-0.5">Describe in natural language or fill out manually</p>
        </div>
      </div>

      {/* AI Parse Section */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Sparkles size={16} className="text-primary-400" />
          <span>AI Fault Parser</span>
          <span className="text-xs text-muted font-normal">Describe the issue naturally; AI will extract key parameters</span>
        </div>
        <div className="flex gap-2">
          <textarea
            value={rawText}
            onChange={e => setRawText(e.target.value)}
            placeholder='e.g. "Line 2 CNC-03 spindle has abnormal noise and 0.05mm accuracy deviation, suspect bearing wear. Running but quality sub-standard"'
            rows={3}
            className="flex-1 resize-none"
            onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleParse(); }}
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted">Ctrl+Enter to parse quickly</span>
          <button onClick={handleParse} disabled={parsing || !rawText.trim()} className="btn btn-primary btn-sm">
            {parsing ? <><Loader2 size={14} className="animate-spin" /> Parsing...</> : <><Sparkles size={14} /> Parse with AI</>}
          </button>
        </div>
      </div>

      {/* Parsed Result Preview */}
      {parsed && (
        <div className="card border-primary/30 bg-primary/5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <Check size={14} className="text-green-400" />
              <span className="text-green-400">Parsed Successfully</span>
              {parsed.confidence != null && (
                <span className={`badge text-xs ${parsed.confidence >= 0.7 ? 'bg-green-500/20 text-green-400' : parsed.confidence >= 0.5 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                  Confidence {Math.round(parsed.confidence * 100)}%
                </span>
              )}
            </div>
            <button onClick={() => setParsed(null)} className="text-xs text-muted hover:text-white">Clear</button>
          </div>
          {parsed.suggested_priority && (
            <div className="text-xs text-muted">Suggested Priority: {parsed.suggested_priority}</div>
          )}
        </div>
      )}

      {/* Manual Form */}
      <div className="card space-y-5">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Edit3 size={16} className="text-muted" />
          <span>Fault Details</span>
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm mb-1">Fault Title <span className="text-red-400">*</span></label>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Brief fault summary" className="w-full" />
        </div>

        {/* Equipment */}
        <div>
          <label className="block text-sm mb-1">Linked Equipment</label>
          <input
            value={equipSearch}
            onChange={e => { setEquipSearch(e.target.value); setEquipmentId(null); }}
            placeholder="Search equipment name or code..."
            className="w-full"
          />
          {equipSearch && !equipmentId && filteredEquipment.length > 0 && (
            <div className="mt-1 border border-card-border rounded-md max-h-40 overflow-y-auto bg-background">
              {filteredEquipment.map(eq => (
                <div
                  key={eq.id}
                  className="px-3 py-2 text-sm hover:bg-white/5 cursor-pointer flex items-center justify-between"
                  onClick={() => { setEquipmentId(eq.id); setEquipSearch(`${eq.code} ${eq.name}`); }}
                >
                  <span>{eq.code} - {eq.name}</span>
                  <span className={`badge text-xs ${eq.status === 'running' ? 'bg-green-500/20 text-green-400' : eq.status === 'fault' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}`}>
                    {eq.status === 'running' ? 'Running' : eq.status === 'fault' ? 'Fault' : eq.status === 'under_repair' ? 'Under Repair' : eq.status === 'stopped' ? 'Stopped' : eq.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Phenomenon + Fault Code */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1">Phenomenon</label>
            <input value={phenomenon} onChange={e => setPhenomenon(e.target.value)} placeholder="e.g. Abnormal noise, vibration, overheating" className="w-full" />
          </div>
          <div>
            <label className="block text-sm mb-1">Fault Code</label>
            <input value={faultCode} onChange={e => setFaultCode(e.target.value)} placeholder="e.g. E103" className="w-full" />
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm mb-1">Detailed Description <span className="text-red-400">*</span></label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Describe fault symptoms, occurrence timeline, temporary actions taken, etc."
            rows={3}
            className="w-full resize-none"
          />
        </div>

        {/* Urgency + Occurred At */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1">Urgency</label>
            <div className="grid grid-cols-2 gap-2">
              {urgencyOptions.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setUrgency(opt.value)}
                  className={`p-2 rounded-lg border text-xs text-left transition-colors ${
                    urgency === opt.value
                      ? 'border-primary/50 bg-primary/10 text-primary-300'
                      : 'border-card-border hover:bg-white/5 text-muted'
                  }`}
                >
                  <div className="font-medium">{opt.label}</div>
                  <div className="opacity-60">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm mb-1">Occurred At</label>
            <input type="datetime-local" value={occurredAt} onChange={e => setOccurredAt(e.target.value)} className="w-full" />
          </div>
        </div>

        {/* Flags */}
        <div>
          <label className="block text-sm mb-2">Impact Flags</label>
          <div className="flex gap-2 flex-wrap">
            <FlagToggle active={isDowntime} onChange={setIsDowntime} label="Downtime" color="red" />
            <FlagToggle active={affectsProduction} onChange={setAffectsProduction} label="Production Affected" color="yellow" />
            <FlagToggle active={hasSafetyRisk} onChange={setHasSafetyRisk} label="Safety Risk" color="red" />
          </div>
        </div>

        {/* Reporter Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1">Reporter</label>
            <input value={reporterName} onChange={e => setReporterName(e.target.value)} placeholder="Name" className="w-full" />
          </div>
          <div>
            <label className="block text-sm mb-1">Contact</label>
            <input value={contact} onChange={e => setContact(e.target.value)} placeholder="Phone / Extension" className="w-full" />
          </div>
        </div>

        {/* Create Work Order Toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={createWO}
            onChange={e => setCreateWO(e.target.checked)}
            className="w-4 h-4 rounded accent-primary"
          />
          <span className="text-sm">Also create work order</span>
          {createWO && (
            <span className="text-xs text-muted">Automatically generates a work order and redirects to work order details upon submission</span>
          )}
        </label>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button onClick={() => router.back()} className="btn btn-outline flex-1">Cancel</button>
        <button onClick={handleSubmit} disabled={submitting || !title.trim() || !description.trim()} className="btn btn-primary flex-1 btn-lg" data-testid="fault-report-submit-button">
          {submitting ? <><Loader2 size={16} className="animate-spin" /> Submitting...</> : <><Send size={16} /> {createWO ? 'Report & Create Order' : 'Submit Report'}</>}
        </button>
      </div>
    </div>
  );
}

function FlagToggle({ active, onChange, label, color }: { active: boolean; onChange: (v: boolean) => void; label: string; color: string }) {
  const colorClasses: any = {
    red: 'border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20',
    yellow: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20',
  };
  const activeColor: any = {
    red: 'border-red-500/50 bg-red-500/20 text-red-300',
    yellow: 'border-yellow-500/50 bg-yellow-500/20 text-yellow-300',
  };
  return (
    <button
      onClick={() => onChange(!active)}
      className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
        active ? activeColor[color] : colorClasses[color]
      }`}
    >
      {active && <Check size={12} className="inline mr-1" />}
      {label}
    </button>
  );
}
