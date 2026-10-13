'use client';
import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getEquipment, getEquipmentWorkOrders, copilotEquipmentHistory, getEquipmentIntelligence } from '@/lib/api';
import { Activity, AlertTriangle, CalendarClock, HeartPulse, Radio, Wrench } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import toast from 'react-hot-toast';

export default function EquipmentDetail() {
  const { id } = useParams();
  const router = useRouter();
  const [eq, setEq] = useState<any>(null);
  const [wos, setWos] = useState<any[]>([]);
  const [history, setHistory] = useState<any>(null);
  const [intelligence, setIntelligence] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const intelligenceRequest = typeof getEquipmentIntelligence === 'function'
        ? getEquipmentIntelligence(Number(id), 60).catch(() => null)
        : Promise.resolve(null);
      const [d, w, h, i] = await Promise.all([getEquipment(Number(id)), getEquipmentWorkOrders(Number(id)), copilotEquipmentHistory(Number(id)).catch(() => null), intelligenceRequest]);
      setEq(d);
      setWos(w);
      setHistory(h);
      setIntelligence(i);
    } catch (e: any) { toast.error(e.message); } finally { setLoading(false); }
  }, [id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div className="text-muted p-6">Loading...</div>;
  if (!eq) return <div className="text-muted p-6">Equipment does not exist</div>;

  const statusLabel: any = { running: 'Running', idle: 'Idle', warning: 'Warning', fault: 'Fault', maintenance: 'Maintenance', offline: 'Offline', under_repair: 'Under Repair', stopped: 'Stopped', scrapped: 'Scrapped' };
  const riskLabel: any = { low: 'Low', medium: 'Medium', high: 'High', critical: 'Critical' };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <div className="text-xs text-muted font-mono mb-1">{eq.code} · {eq.equipment_type_name || 'Uncategorized Equipment'}</div>
          <h1 className="text-2xl font-bold">{eq.name}</h1>
          <p className="text-sm text-muted mt-1">{eq.production_line || '-'} · {eq.location || '-'}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="badge bg-blue-500/15 text-blue-300">{statusLabel[eq.status] || eq.status}</span>
          <div className="rounded-xl border border-card-border bg-card px-4 py-2">
            <div className="text-[11px] text-muted flex items-center gap-1"><HeartPulse size={12} />Health Score</div>
            <div className={`text-2xl font-bold font-mono ${healthColor(eq.health_score)}`}>{eq.health_score == null ? '--' : Math.round(eq.health_score)}<span className="text-xs text-muted font-normal">/100</span></div>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-3">Basic Properties</h2>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <Info label="Equipment Code" value={eq.code} />
            <Info label="Equipment Type" value={eq.equipment_type_name} />
            <Info label="Risk Level" value={riskLabel[eq.risk_level]} />
            <Info label="Plant" value={eq.plant} />
            <Info label="Production Line" value={eq.production_line} />
            <Info label="Location" value={eq.location} />
            <Info label="Manufacturer" value={eq.manufacturer} />
            <Info label="Model" value={eq.model} />
            <Info label="Serial Number" value={eq.serial_number} />
            <Info label="Commissioning Date" value={eq.commissioning_date} />
            <Info label="Responsible Person" value={eq.responsible_person_name} />
            <Info label="Last Maintenance" value={eq.last_maintenance_at} />
            <Info label="Recommended Maintenance" value={eq.next_maintenance_at} />
            <Info label="Runtime Hours" value={eq.cumulative_runtime_hours ? `${Math.round(eq.cumulative_runtime_hours).toLocaleString()} h` : '-'} />
          </div>
          {eq.remarks && <div className="mt-2 text-sm text-muted">Remarks: {eq.remarks}</div>}
        </div>
        <div className="card">
          <h2 className="font-semibold mb-3">Equipment History Summary</h2>
          {history ? (
            <div className="space-y-3 text-sm">
              <div><span className="text-muted">Total Work Orders:</span> <span className="font-bold">{history.total_work_orders}</span> {history.avg_repair_hours && <span className="text-muted ml-2">Avg Repair Time: {history.avg_repair_hours}h</span>}</div>
              {history.frequent_faults?.length > 0 && <div><div className="text-muted mb-1">Frequent Faults</div>{history.frequent_faults.map((f: any, i: number) => <div key={i} className="flex justify-between text-xs py-0.5"><span>{f.fault?.substring(0, 40)}</span><span className="font-mono text-muted">{f.count} times</span></div>)}</div>}
              {history.repeated_faults?.length > 0 && <div><div className="text-muted mb-1">Repeated Faults</div>{history.repeated_faults.map((f: any, i: number) => <div key={i} className="text-xs">{f.fault?.substring(0, 40)} <span className="font-mono text-muted">({f.count} times)</span></div>)}</div>}
              {history.common_parts?.length > 0 && <div><div className="text-muted mb-1">Commonly Replaced Parts</div>{history.common_parts.map((p: any, i: number) => <div key={i} className="text-xs">{p.part} <span className="font-mono text-muted">({p.count} times)</span></div>)}</div>}
            </div>
          ) : <p className="text-sm text-muted">No history summary available</p>}
        </div>
      </div>
      {intelligence && (
        <>
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="card xl:col-span-2 min-h-[360px]">
              <div className="flex items-center justify-between mb-4">
                <div><h2 className="font-semibold flex items-center gap-2"><Activity size={16} className="text-primary-400" />Key Telemetry Trends</h2><p className="text-xs text-muted mt-1">Last {intelligence.telemetry?.length || 0} sample points</p></div>
                <button className="btn btn-outline btn-sm" onClick={() => router.push('/monitoring')}>Live Monitoring</button>
              </div>
              {intelligence.telemetry?.length ? (
                <div className="h-[275px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={intelligence.telemetry.map((item: any) => ({ ...item, time: new Date(item.collected_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) }))}>
                      <CartesianGrid stroke="#334155" strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
                      <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
                      <Line type="monotone" dataKey="vibration_rms" name="Vibration RMS" stroke="#38bdf8" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="bearing_temperature" name="Bearing Temp" stroke="#fb923c" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="motor_current" name="Motor Current" stroke="#a78bfa" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : <div className="h-[260px] flex items-center justify-center text-muted">No telemetry data available</div>}
            </div>
            <div className="card">
              <h2 className="font-semibold flex items-center gap-2 mb-4"><Radio size={16} className="text-green-400" />Associated Sensors</h2>
              <div className="space-y-2 max-h-[290px] overflow-y-auto">
                {intelligence.sensors?.map((sensor: any) => (
                  <div key={sensor.id} className="rounded-lg border border-card-border bg-black/10 p-3 flex items-center justify-between">
                    <div><div className="text-sm">{sensor.name}</div><div className="text-[11px] text-muted font-mono">{sensor.code}</div></div>
                    <div className="text-right"><div className="text-sm font-mono">{sensor.latest_value == null ? '--' : sensor.latest_value} {sensor.unit}</div><div className={`text-[11px] ${sensor.status === 'online' ? 'text-green-400' : 'text-red-400'}`}>{sensor.status === 'online' ? 'Online' : 'Offline'}</div></div>
                  </div>
                ))}
                {!intelligence.sensors?.length && <p className="text-sm text-muted">No associated sensors</p>}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="font-semibold flex items-center gap-2 mb-4"><AlertTriangle size={16} className="text-orange-400" />Anomalies & Diagnosis</h2>
              <div className="space-y-3">
                {intelligence.anomalies?.slice(0, 5).map((event: any) => (
                  <div key={event.id} className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-3">
                    <div className="flex items-center justify-between"><span className="text-sm font-medium">{event.title}</span><span className="badge bg-orange-500/15 text-orange-300">{riskLabel[event.severity] || event.severity}</span></div>
                    <p className="text-xs text-muted leading-5 mt-2">{event.diagnosis_summary}</p>
                    <div className="text-[11px] text-muted mt-2">Confidence {Math.round(event.confidence * 100)}% · {event.status}</div>
                  </div>
                ))}
                {!intelligence.anomalies?.length && <p className="text-sm text-muted">No active anomaly events</p>}
              </div>
            </div>
            <div className="card">
              <h2 className="font-semibold flex items-center gap-2 mb-4"><CalendarClock size={16} className="text-purple-400" />Maintenance Strategies</h2>
              <div className="space-y-3">
                {intelligence.recommendations?.slice(0, 4).map((item: any) => (
                  <div key={item.id} className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">
                    <div className="flex items-center justify-between"><span className="text-sm font-medium">{item.title}</span><span className="badge bg-purple-500/15 text-purple-300">{item.priority}</span></div>
                    <p className="text-xs text-muted leading-5 mt-2">{item.strategy}</p>
                    <div className="flex items-center justify-between mt-3">
                      <span className="text-[11px] text-muted">{(item.required_skills || []).join(' · ')}</span>
                      {item.auto_work_order_id && <button onClick={() => router.push(`/work-orders/${item.auto_work_order_id}`)} className="text-xs text-primary-400 flex items-center gap-1"><Wrench size={12} />Smart Work Order</button>}
                    </div>
                  </div>
                ))}
                {!intelligence.recommendations?.length && <p className="text-sm text-muted">No maintenance strategies</p>}
              </div>
            </div>
          </div>
        </>
      )}
      <div className="card">
        <h2 className="font-semibold mb-3">Work Order History ({wos.length})</h2>
        {wos.length === 0 ? <p className="text-sm text-muted">No work order records</p> : (
          <div className="space-y-1">
            {wos.map(w => (
              <div key={w.id} className="flex items-center justify-between p-2 rounded hover:bg-white/5 cursor-pointer text-sm" onClick={() => router.push(`/work-orders/${w.id}`)}>
                <div>
                  <span className="font-mono text-xs text-muted mr-2">{w.code}</span>
                  <span>{w.title}</span>
                  {w.root_cause && <span className="text-xs text-muted ml-2">({w.root_cause.substring(0, 30)})</span>}
                </div>
                <span className={`badge ${w.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{w.status === 'completed' ? 'Completed' : w.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: any }) {
  return <div><span className="text-muted text-xs">{label}</span><div className="text-sm">{value || '-'}</div></div>;
}

function healthColor(score?: number) {
  if (score == null) return 'text-muted';
  return score >= 85 ? 'text-green-300' : score >= 70 ? 'text-yellow-300' : 'text-red-300';
}
