'use client';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import {
  copilotAsk,
  listEquipmentTypes,
  listFaultCodes,
  listRecentESPEvents,
  diagnoseESPEvent,
  ESPEventSummary,
} from '@/lib/api';
import { AskResult } from '@/lib/types';
import { AnswerPanel } from '@/components/copilot/citation-card';
import { Send, Trash2, AlertTriangle, Zap, Database, Activity, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';

const EXAMPLE_QUESTIONS = [
  'Diagnose event EV-20261012-103435-FNW-001-878',
  'What caused well FNW-001 to trip with high vibration?',
  'Analyze well FS-017 motor overload trip',
  'What are the common causes of E102 faults?',
  'How to resolve frequent loose proximity switches on packaging machines?',
  'What safety checks are required before replacing a servo drive?',
];

export default function CopilotPage() {
  const { user } = useAuth();
  const sp = useSearchParams();
  const [question, setQuestion] = useState('');
  const [equipmentTypeId, setEquipmentTypeId] = useState<number | undefined>(undefined);
  const [faultCode, setFaultCode] = useState<string | undefined>(undefined);
  const [types, setTypes] = useState<any[]>([]);
  const [faultCodes, setFaultCodes] = useState<any[]>([]);
  const [result, setResult] = useState<AskResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Array<{ role: string; content: string }>>([]);

  // ESP APM Live Events from Server 184
  const [espEvents, setEspEvents] = useState<ESPEventSummary[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [loadingEsp, setLoadingEsp] = useState(false);

  useEffect(() => {
    listEquipmentTypes().then(setTypes).catch(() => {});
    listFaultCodes().then(setFaultCodes).catch(() => {});
    listRecentESPEvents(15)
      .then(events => {
        setEspEvents(events);
        if (events.length > 0) {
          setSelectedEventId(events[0].event_id);
        }
      })
      .catch(() => {});
  }, []);

  const handleAsk = async (q?: string) => {
    const query = q || question.trim();
    if (!query) return;
    setLoading(true);
    try {
      const res = await copilotAsk(query, equipmentTypeId, faultCode, history);
      setResult(res);
      setHistory(prev => [
        ...prev,
        { role: 'user', content: query },
        { role: 'assistant', content: res.answer },
      ]);
    } catch (e: any) {
      toast.error(e.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDiagnoseEspEvent = async (evId?: string) => {
    const targetId = evId || selectedEventId;
    if (!targetId) return;
    setLoading(true);
    setLoadingEsp(true);
    try {
      const diag = await diagnoseESPEvent({ event_id: targetId });
      setResult({
        answer: diag.markdown_report,
        confidence: diag.mathematical_confidence_pct / 100.0,
        citations: [
          {
            source_type: 'esp_fault_taxonomy',
            source_id: 1,
            title: `Taxonomy: ${diag.structured_data?.signature?.fault_name || diag.trip_cause}`,
            excerpt: diag.structured_data?.signature?.citation || 'Authoritative Petroleum Standards',
            relevance_score: 0.95,
          },
        ],
        warnings: [
          `Active Telemetry Diagnosis: Well ${diag.well_id} tripped with ${diag.trip_cause}. Mandatory LOTO required before physical inspection.`,
        ],
        is_mock: false,
        disclaimer: diag.disclaimer,
      });
      toast.success(`Diagnosis complete for ${diag.well_id}`);
    } catch (e: any) {
      toast.error(e.message || 'ESP event diagnosis failed');
    } finally {
      setLoading(false);
      setLoadingEsp(false);
    }
  };

  const handleClear = () => {
    setQuestion('');
    setResult(null);
    setHistory([]);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">AI Maintenance Copilot</h1>
          <p className="text-xs text-muted mt-0.5">
            Petroleum Engineering XAI Diagnostics & Operational Decision Support
          </p>
        </div>
        {/* Status badges */}
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Database size={12} />
            ESP APM (Server 184 Read-Only)
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Zap size={12} />
            Qwen 2.5 Coder 3B
          </span>
        </div>
      </div>

      {/* Safety notice - always visible */}
      <div className="flex items-start gap-2 text-sm text-yellow-400 bg-yellow-500/10 rounded-lg p-4 border border-yellow-500/20">
        <AlertTriangle size={16} className="shrink-0 mt-0.5" />
        <span>
          AI suggestions are advisory only. Technicians and production engineers must exercise judgment based on on-site conditions, manuals, and safety rules. Mandatory LOTO required prior to wellhead intervention.
        </span>
      </div>

      {/* Real-time ESP APM Event Quick Diagnosis Card */}
      <div className="card space-y-3 bg-gradient-to-r from-card to-white/5 border border-primary/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-primary" />
            <span className="text-sm font-semibold">Live ESP Trip Event Diagnostics</span>
            <span className="text-xs text-muted font-mono">(Direct from PostgreSQL Server 184)</span>
          </div>
          <span className="text-xs text-muted">
            {espEvents.length} Recent Events Loaded
          </span>
        </div>

        <div className="flex gap-2 flex-wrap sm:flex-nowrap">
          <select
            value={selectedEventId}
            onChange={e => setSelectedEventId(e.target.value)}
            className="flex-1 text-sm bg-background border border-border rounded-md px-3 py-2 text-foreground font-mono"
            disabled={loading || espEvents.length === 0}
          >
            {espEvents.map(ev => (
              <option key={ev.event_id} value={ev.event_id}>
                {ev.well_id} — {ev.trip_cause} ({ev.severity}) [{ev.event_id}]
              </option>
            ))}
          </select>
          <button
            onClick={() => handleDiagnoseEspEvent()}
            disabled={loading || !selectedEventId}
            className="btn btn-primary shrink-0 gap-2 font-medium"
          >
            <ShieldCheck size={16} />
            {loadingEsp ? 'Diagnosing...' : 'Run XAI Diagnosis'}
          </button>
        </div>
      </div>

      {/* Natural Language Input area */}
      <div className="card space-y-4">
        <div className="flex gap-2">
          <input
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
            placeholder="Ask a maintenance question or enter Event ID / Well ID (e.g. EV-20261012-103435-FNW-001-878)..."
            className="flex-1"
            data-testid="copilot-question-input"
          />
          <button
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="btn btn-primary"
            data-testid="copilot-submit-button"
          >
            <Send size={16} /> {loading ? 'Analyzing...' : 'Ask'}
          </button>
          {result && (
            <button onClick={handleClear} className="btn btn-outline" title="Clear result">
              <Trash2 size={16} />
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          <select
            value={equipmentTypeId || ''}
            onChange={e => setEquipmentTypeId(e.target.value ? Number(e.target.value) : undefined)}
            className="text-sm"
          >
            <option value="">All Equipment Types</option>
            {types.map(t => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <select
            value={faultCode || ''}
            onChange={e => setFaultCode(e.target.value || undefined)}
            className="text-sm"
          >
            <option value="">All Fault Codes</option>
            {faultCodes.map(f => (
              <option key={f.code} value={f.code}>
                {f.code} - {f.name}
              </option>
            ))}
          </select>
        </div>

        {/* Example questions */}
        {!result && (
          <div className="space-y-1">
            <div className="text-xs text-muted mb-2">Example Diagnostic & Knowledge Questions</div>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setQuestion(q);
                    handleAsk(q);
                  }}
                  className="btn btn-sm btn-outline text-xs"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Answer panel */}
      <AnswerPanel
        result={result}
        loading={loading}
        onSelectOption={(opt) => {
          setQuestion(opt);
          handleAsk(opt);
        }}
      />
    </div>
  );
}

