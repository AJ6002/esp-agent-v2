'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, Database, RadioTower, Server } from 'lucide-react';
import {
  getMetricsSummary,
  getObservabilityHealth,
  searchTraces,
} from '@/lib/api';
import type {
  MetricsSummary,
  ObservabilityHealth,
  TraceSearchResult,
} from '@/lib/types';

const STATUS_STYLES: Record<string, string> = {
  healthy: 'bg-green-500/15 text-green-300',
  degraded: 'bg-yellow-500/15 text-yellow-300',
  unavailable: 'bg-red-500/15 text-red-300',
  unknown: 'bg-gray-500/15 text-gray-300',
};

export default function ObservabilityPage() {
  const [health, setHealth] = useState<ObservabilityHealth | null>(null);
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [traces, setTraces] = useState<TraceSearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [h, s, t] = await Promise.all([
      getObservabilityHealth().catch(() => null),
      getMetricsSummary().catch(() => null),
      searchTraces({ limit: 10 }).catch(() => null),
    ]);
    if (!h && !s && !t) {
      setError('Observability data temporarily unavailable, please retry later');
      return;
    }
    setError(null);
    if (h) setHealth(h);
    if (s) setSummary(s);
    if (t) setTraces(t);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (error) {
    return (
      <div className="p-6">
        <div className="card" data-testid="observability-error">
          <p className="text-sm text-yellow-300">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12" data-testid="observability-page">
      <div>
        <h1 className="text-lg font-bold">System Observability & Trace Tracking</h1>
        <p className="text-xs text-muted mt-1">
          End-to-end evidence chain from OPC UA DataChange to work order approval (simulated environment).
        </p>
      </div>

      {/* System Health */}
      <section className="card">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <Server size={16} /> System Health
        </h2>
        {!health ? (
          <p className="text-xs text-muted">Loading...</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(health.components).map(([name, component]) => (
              <div
                key={name}
                data-testid={`health-${name}`}
                className={`rounded p-2 text-xs ${STATUS_STYLES[component.status] ?? 'bg-gray-500/15 text-gray-300'}`}
              >
                <div className="font-semibold">{name}</div>
                <div className="mt-1 opacity-80">{component.status}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Core metrics summary */}
      <section className="card">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <Activity size={16} /> Core Metrics
        </h2>
        {!summary ? (
          <p className="text-xs text-muted">Loading...</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <MetricBox label="Telemetry Events" value={summary.telemetry_events} testId="metric-telemetry" />
            <MetricBox label="Active Alarms" value={summary.alarms_active} testId="metric-alarms-active" />
            <MetricBox label="Analyses Awaiting Review" value={summary.analyses_waiting_review} testId="metric-waiting-review" />
            <MetricBox
              label="Agent Avg Latency (ms)"
              value={summary.agent_avg_latency_ms ?? '-'}
              testId="metric-agent-latency"
            />
            <MetricBox label="Total Work Orders" value={summary.work_orders_total} />
            <MetricBox label="Open Work Orders" value={summary.work_orders_open} />
            <MetricBox label="Agent Runs Total" value={summary.agent_runs_total} />
            <MetricBox label="Tracked Traces" value={summary.traces_tracked} testId="metric-traces" />
          </div>
        )}
      </section>

      {/* Recent traces */}
      <section className="card">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <RadioTower size={16} /> Recent Industrial Traces
          <Database size={14} className="ml-auto text-muted" />
        </h2>
        {!traces || traces.items.length === 0 ? (
          <p className="text-xs text-muted" data-testid="traces-empty">
            No tracked traces. Trigger a simulated fault to display the complete evidence chain here.
          </p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-muted">
                <th className="py-1">Trace ID</th>
                <th>Equipment</th>
                <th>Started At</th>
                <th>Final Status</th>
                <th>Stages / Events</th>
                <th></th>
              </tr>
            </thead>
            <tbody data-testid="recent-traces">
              {traces.items.map((item) => (
                <tr key={item.trace_id} className="border-t border-white/5">
                  <td className="py-1 font-mono">{item.trace_id.slice(0, 8)}…</td>
                  <td>{item.equipment_ids.join(', ') || '-'}</td>
                  <td>{item.started_at ?? '-'}</td>
                  <td>{item.final_status}</td>
                  <td>
                    {item.stage_count}/{item.event_count}
                  </td>
                  <td className="text-right">
                    <Link
                      href={`/observability/traces/${item.trace_id}`}
                      className="btn btn-outline !py-0.5 !px-2"
                      data-testid={`open-trace-${item.trace_id}`}
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function MetricBox({
  label,
  value,
  testId,
}: {
  label: string;
  value: number | string;
  testId?: string;
}) {
  return (
    <div className="rounded bg-white/5 p-2" data-testid={testId}>
      <div className="text-muted">{label}</div>
      <div className="text-base font-bold mt-1">{value}</div>
    </div>
  );
}
