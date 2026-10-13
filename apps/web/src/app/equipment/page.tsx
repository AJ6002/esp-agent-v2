'use client';
import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { listEquipment, listEquipmentTypes, getEquipmentWorkOrders, copilotEquipmentHistory } from '@/lib/api';
import { Search, HeartPulse, MapPin, CalendarClock } from 'lucide-react';
import toast from 'react-hot-toast';

export default function EquipmentList() {
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [types, setTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchData = useCallback(async () => {
    setLoading(true);
    const params: any = { page: String(page), page_size: '20' };
    if (keyword) params.keyword = keyword;
    if (typeFilter) params.equipment_type_id = typeFilter;
    if (statusFilter) params.status = statusFilter;
    try { const d = await listEquipment(params); setItems(d.items); setTotal(d.total); } catch (e: any) { toast.error(e.message); } finally { setLoading(false); }
  }, [page, typeFilter, statusFilter, keyword]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { listEquipmentTypes().then(setTypes).catch(() => {}); }, []);

  const statusLabel: any = { running: 'Running', idle: 'Idle', warning: 'Warning', fault: 'Fault', maintenance: 'Maintenance', offline: 'Offline', under_repair: 'Under Repair', stopped: 'Stopped', scrapped: 'Scrapped' };
  const statusClass: any = { running: 'bg-green-500/15 text-green-300', idle: 'bg-blue-500/15 text-blue-300', warning: 'bg-yellow-500/15 text-yellow-300', fault: 'bg-red-500/15 text-red-300', maintenance: 'bg-purple-500/15 text-purple-300', offline: 'bg-gray-500/15 text-gray-300', under_repair: 'bg-yellow-500/15 text-yellow-300', stopped: 'bg-gray-500/15 text-gray-300', scrapped: 'bg-gray-500/15 text-gray-400' };

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <div>
        <div className="text-xs tracking-[0.18em] uppercase text-primary-400 font-semibold mb-1">Asset Intelligence</div>
        <h1 className="text-2xl font-bold">Equipment Asset Center</h1>
        <p className="text-sm text-muted mt-1">Unified management of equipment profiles, health status, telemetry, work orders, and fault history</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <input value={keyword} onChange={e => setKeyword(e.target.value)} placeholder="Search equipment code or name..." className="pl-8 w-full" onKeyDown={e => { if (e.key === 'Enter') { setPage(1); fetchData(); } }} />
          <Search size={14} className="absolute left-2.5 top-2.5 text-muted" />
        </div>
        <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(1); }} className="text-sm">
          <option value="">All Types</option>
          {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} className="text-sm">
          <option value="">All Statuses</option>
          <option value="running">Running</option>
          <option value="idle">Idle</option>
          <option value="warning">Warning</option>
          <option value="fault">Fault</option>
          <option value="maintenance">Maintenance</option>
          <option value="offline">Offline</option>
          <option value="under_repair">Under Repair</option>
          <option value="stopped">Stopped</option>
        </select>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? <div className="col-span-full text-muted">Loading...</div> : items.length === 0 ? <div className="col-span-full text-muted">No equipment found</div> : items.map(eq => (
          <div key={eq.id} className="card cursor-pointer hover:bg-white/5 hover:-translate-y-0.5 transition-all" onClick={() => router.push(`/equipment/${eq.id}`)}>
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="font-semibold text-sm">{eq.name}</div>
                <div className="text-xs text-muted font-mono">{eq.code}</div>
              </div>
              <span className={`badge ${statusClass[eq.status] || ''}`}>{statusLabel[eq.status] || eq.status}</span>
            </div>
            <div className="my-4 rounded-lg bg-black/10 border border-card-border p-3">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-muted flex items-center gap-1.5"><HeartPulse size={13} />Health Score</span>
                <span className={`font-mono font-semibold ${healthColor(eq.health_score)}`}>{eq.health_score == null ? '--' : Math.round(eq.health_score)}</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div className={`h-full rounded-full ${healthBar(eq.health_score)}`} style={{ width: `${Math.max(0, Math.min(eq.health_score || 0, 100))}%` }} />
              </div>
              <div className="flex items-center justify-between mt-2 text-[11px] text-muted">
                <span>Risk: {riskLabel(eq.risk_level)}</span>
                <span>{eq.cumulative_runtime_hours ? `${Math.round(eq.cumulative_runtime_hours).toLocaleString()} h` : 'No runtime data'}</span>
              </div>
            </div>
            <div className="text-xs text-muted space-y-0.5">
              {eq.equipment_type_name && <div>Type: {eq.equipment_type_name}</div>}
              {eq.location && <div className="flex items-center gap-1"><MapPin size={11} />Location: {eq.location}</div>}
              {eq.manufacturer && <div>Manufacturer: {eq.manufacturer} {eq.model}</div>}
              {eq.next_maintenance_at && <div className="flex items-center gap-1 pt-1 text-primary-300"><CalendarClock size={11} />Recommended Maintenance: {eq.next_maintenance_at}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function riskLabel(risk?: string) {
  return ({ low: 'Low', medium: 'Medium', high: 'High', critical: 'Critical' } as Record<string, string>)[risk || ''] || '-';
}

function healthColor(score?: number) {
  if (score == null) return 'text-muted';
  return score >= 85 ? 'text-green-300' : score >= 70 ? 'text-yellow-300' : 'text-red-300';
}

function healthBar(score?: number) {
  if (score == null) return 'bg-gray-500';
  return score >= 85 ? 'bg-green-400' : score >= 70 ? 'bg-yellow-400' : 'bg-red-400';
}
