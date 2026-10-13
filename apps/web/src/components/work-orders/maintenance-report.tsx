'use client';

import { useCallback, useEffect, useState } from 'react';
import { getWorkOrderReport, regenerateWorkOrderReport } from '@/lib/api';
import { WorkOrderReport } from '@/lib/types';

export default function MaintenanceReport({ workOrderId }: { workOrderId: number }) {
  const [report, setReport] = useState<WorkOrderReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState('');

  const loadReport = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getWorkOrderReport(workOrderId);
      setReport(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }, [workOrderId]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  async function handleRegenerate() {
    setRegenerating(true);
    try {
      const data = await regenerateWorkOrderReport(workOrderId);
      setReport(data);
    } catch (e: any) {
      setError(e.message || 'Failed to regenerate report');
    } finally {
      setRegenerating(false);
    }
  }

  if (loading) {
    return <div className="text-center py-8 text-muted">Loading maintenance report...</div>;
  }

  if (error) {
    return (
      <div className="card p-4 border-red-500/30">
        <p className="text-red-400 mb-2">{error}</p>
        <button onClick={loadReport} className="btn btn-sm btn-outline">Retry</button>
      </div>
    );
  }

  if (!report) {
    return <div className="text-center py-4 text-muted">No maintenance report available</div>;
  }

  return (
    <div className="card p-4 space-y-4" data-testid="maintenance-report">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Maintenance Report</h3>
          <p className="text-xs text-muted mt-1">
            Method: {report.generation_method === 'ai' ? 'AI Generated' : 'Template Generated'}
            {' · '}Version {report.version}
            {report.is_mock && ' · Smart Fallback'}
          </p>
        </div>
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="btn btn-sm btn-outline"
          data-testid="regenerate-report-button"
        >
          {regenerating ? 'Generating...' : 'Regenerate'}
        </button>
      </div>

      <div className="bg-white/5 rounded-lg p-4">
        <p className="text-sm font-medium text-primary-300 mb-1">Summary</p>
        <p className="text-sm text-muted leading-relaxed">{report.summary}</p>
      </div>

      {report.sections && report.sections.length > 0 && (
        <div className="space-y-3">
          {report.sections.map((section, i) => (
            <div key={i} className="border-t border-white/5 pt-3 first:border-0 first:pt-0">
              <p className="text-sm font-medium mb-1">{section.title}</p>
              <p className="text-sm text-muted leading-relaxed">{section.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
