'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getTrace } from '@/lib/api';
import type { TraceDetail, TraceTimelineEntry } from '@/lib/types';

const STAGE_LABELS: Record<string, string> = {
  telemetry: 'Telemetry',
  anomaly: 'Anomaly Detection',
  prediction: 'Fault Prediction',
  recommendation: 'Recommendation',
  alarm: 'Alarm',
  analysis: 'Alarm RCA',
  rag: 'RAG Evidence',
  tool: 'Tool Invocation',
  agent: 'Agent Execution',
  work_order: 'Work Order',
  approval: 'Approval',
};

const STAGE_STYLES: Record<string, string> = {
  telemetry: 'text-sky-300 border-sky-400/30',
  anomaly: 'text-yellow-300 border-yellow-400/30',
  prediction: 'text-purple-300 border-purple-400/30',
  alarm: 'text-red-300 border-red-400/30',
  analysis: 'text-orange-300 border-orange-400/30',
  rag: 'text-emerald-300 border-emerald-400/30',
  agent: 'text-blue-300 border-blue-400/30',
  work_order: 'text-green-300 border-green-400/30',
  approval: 'text-pink-300 border-pink-400/30',
};

export default function TraceDetailPage() {
  const params = useParams<{ traceId: string }>();
  const traceId = decodeURIComponent(params.traceId);
  const [detail, setDetail] = useState<TraceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getTrace(traceId);
      setDetail(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load trace');
    }
  }, [traceId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-3" data-testid="trace-error">
        <p className="text-sm text-yellow-300">{error}</p>
        <Link href="/observability" className="btn btn-outline !py-1 !px-2 text-xs">
          Back to Observability Center
        </Link>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="max-w-4xl mx-auto p-6 text-sm text-muted">Loading...</div>
    );
  }

  const keyFacts = (entry: TraceTimelineEntry) => {
    switch (entry.stage) {
      case 'prediction':
        return [
          `Model: ${entry['model_name'] ?? '-'}`,
          `Version: ${entry['model_version'] ?? '-'}`,
          `Probability: ${entry['probability'] ?? '-'}`,
        ];
      case 'analysis':
        return [
          `Confidence: ${entry['confidence'] ?? '-'}`,
          `Risk: ${entry['risk_level'] ?? '-'}`,
          `Citations: ${entry['citations_count'] ?? 0}`,
        ];
      case 'rag':
        return [
          `Source: ${entry['source'] ?? '-'}`,
          `Score: ${entry['score'] ?? '-'}`,
          `Snippet: ${(entry['snippet'] as string) ?? ''}`.slice(0, 80),
        ];
      case 'agent':
        return [`Latency: ${entry['latency_ms'] ?? '-'}ms`];
      case 'tool':
        return [`Duration: ${entry['duration_ms'] ?? '-'}ms`];
      default:
        return [];
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-5 pb-12" data-testid="trace-detail">
      <div>
        <Link href="/observability" className="text-xs text-muted hover:underline">
          ← Back to Observability Center
        </Link>
        <h1 className="text-lg font-bold mt-2 font-mono break-all" data-testid="trace-title">
          {detail.trace_id}
        </h1>
        <p className="text-xs text-muted mt-1">
          Final Status: {detail.final_status} · Stages: {detail.stage_count} · Events:{' '}
          {detail.event_count} · Total Duration: {detail.duration_ms}ms
        </p>
      </div>

      <ol className="space-y-2" data-testid="trace-timeline">
        {detail.timeline.map((entry, index) => (
          <li
            key={`${entry.stage}-${entry.entity_type}-${entry.entity_id}-${index}`}
            className={`card border-l-2 p-3 text-xs ${
              STAGE_STYLES[entry.stage] ?? 'border-white/10'
            }`}
            data-testid={`timeline-${entry.stage}`}
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold">{STAGE_LABELS[entry.stage] ?? entry.stage}</span>
              <span className="text-muted">#{entry.entity_id}</span>
              <span className="ml-auto text-muted">
                {entry.timestamp ?? '-'}
              </span>
            </div>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 opacity-90">
              {entry.status && <span>Status: {entry.status}</span>}
              {keyFacts(entry).map((fact) => (
                <span key={fact}>{fact}</span>
              ))}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
