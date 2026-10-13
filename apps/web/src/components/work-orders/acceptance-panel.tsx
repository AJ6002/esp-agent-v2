'use client';

import { useState } from 'react';
import { approveWorkOrder, rejectWorkOrder } from '@/lib/api';

interface Props {
  workOrderId: number;
  onRefresh: () => void;
}

export default function AcceptancePanel({ workOrderId, onRefresh }: Props) {
  const [loading, setLoading] = useState('');
  const [error, setError] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [showReject, setShowReject] = useState(false);

  async function handleApprove() {
    setLoading('approve');
    setError('');
    try {
      await approveWorkOrder(workOrderId);
      onRefresh();
    } catch (e: any) {
      if (e.message?.includes('already accepted') || e.message?.toLowerCase().includes('accepted')) {
        setError('This work order has already been accepted');
        onRefresh();
      } else {
        setError(e.message || 'Acceptance failed');
      }
    } finally {
      setLoading('');
    }
  }

  async function handleReject() {
    if (!rejectReason.trim()) {
      setError('Please provide a rejection reason');
      return;
    }
    setLoading('reject');
    setError('');
    try {
      await rejectWorkOrder(workOrderId, rejectReason.trim());
      onRefresh();
    } catch (e: any) {
      setError(e.message || 'Rejection failed');
    } finally {
      setLoading('');
    }
  }

  return (
    <div className="card p-4 space-y-3" data-testid="acceptance-panel">
      <h3 className="text-lg font-semibold">Acceptance Review</h3>

      {error && <p className="text-red-400 text-xs">{error}</p>}

      <div className="flex gap-2">
        <button
          onClick={handleApprove}
          disabled={loading !== ''}
          className="btn btn-primary btn-sm"
          data-testid="approve-work-order-button"
        >
          {loading === 'approve' ? 'Processing...' : 'Approve & Accept'}
        </button>
        <button
          onClick={() => setShowReject(!showReject)}
          disabled={loading !== ''}
          className="btn btn-sm btn-outline border-red-500/30 text-red-400"
          data-testid="reject-work-order-toggle"
        >
          Return for Rework
        </button>
      </div>

      {showReject && (
        <div className="space-y-2 pt-2 border-t border-white/5">
          <textarea
            placeholder="Enter rejection reason..."
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            className="input w-full h-20 text-sm"
            data-testid="reject-reason-input"
          />
          <div className="flex gap-2">
            <button
              onClick={handleReject}
              disabled={loading !== ''}
              className="btn btn-sm btn-outline border-red-500/30 text-red-400"
              data-testid="confirm-reject-button"
            >
              {loading === 'reject' ? 'Processing...' : 'Confirm Return'}
            </button>
            <button
              onClick={() => setShowReject(false)}
              disabled={loading !== ''}
              className="btn btn-sm btn-ghost"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
