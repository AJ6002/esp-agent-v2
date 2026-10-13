'use client';

import { CompletionValidationError } from '@/lib/types';

const MISSING_LABELS: Record<string, string> = {
  root_cause: 'Root cause',
  action_taken: 'Action taken',
  test_result: 'Test result',
  required_checklist_items: 'Mandatory checklist items not all completed',
  maintenance_log: 'At least one maintenance log entry required',
  labor_entry: 'At least one labor entry required',
  test_step: 'At least one test verification required',
  completion_photo: 'High-risk orders require completion/test photo',
};

export default function CompletionValidationDisplay({ error }: { error: CompletionValidationError }) {
  if (!error.missing_requirements || error.missing_requirements.length === 0) {
    return null;
  }

  return (
    <div className="card p-4 border-red-500/30 bg-red-500/5" data-testid="completion-validation">
      <p className="text-sm font-medium text-red-400 mb-2">{error.message}</p>
      <p className="text-xs text-muted mb-2">The following requirements are not yet satisfied:</p>
      <ul className="space-y-1">
        {error.missing_requirements.map((item, i) => (
          <li key={i} className="text-sm text-red-300 flex items-start gap-2">
            <span className="text-red-400 mt-1">&#x2716;</span>
            <span>{MISSING_LABELS[item] || item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
