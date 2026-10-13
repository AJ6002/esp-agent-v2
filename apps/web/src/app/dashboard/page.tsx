'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { getSupervisorDashboard, getTechnicianDashboard, getIntelligenceOverview } from '@/lib/api';
import { Wrench, Clock, CheckCircle, AlertTriangle, TrendingUp, ArrowRight, Activity, HeartPulse, ShieldAlert, Sparkles } from 'lucide-react';
import { STATUS_LABELS, PRIORITY_LABELS } from '@/lib/types';

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [intelligence, setIntelligence] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    if (user.role === 'technician') {
      getTechnicianDashboard().then(setData).catch(console.error).finally(() => setLoading(false));
      return;
    }
    const intelligenceRequest = typeof getIntelligenceOverview === 'function'
      ? getIntelligenceOverview().catch(() => null)
      : Promise.resolve(null);
    Promise.all([getSupervisorDashboard(), intelligenceRequest])
      .then(([dashboardData, intelligenceData]) => {
        setData(dashboardData);
        setIntelligence(intelligenceData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div className="text-muted p-6">Loading...</div>;
  if (!data) return <div className="text-muted p-6">No data available</div>;

  if (user?.role === 'technician') {
    const d = data;
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-xl font-bold">Maintenance Workbench</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon={<Wrench />} label="Assigned to Me" value={d.assigned_to_me} color="blue" />
          <StatCard icon={<Clock />} label="Due Today" value={d.today_todo} color="yellow" />
          <StatCard icon={<AlertTriangle />} label="High Priority" value={d.high_priority} color="red" />
          <StatCard icon={<TrendingUp />} label="Overdue" value={d.overdue} color="red" />
        </div>
        <div className="flex gap-3">
          <button onClick={() => router.push('/fault-reports/new')} className="btn btn-primary btn-lg flex-1">Report Fault</button>
          <button onClick={() => router.push('/work-orders?mine=true')} className="btn btn-outline btn-lg flex-1">My Work Orders</button>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Pending Work Orders</h2>
            <button onClick={() => router.push('/work-orders?mine=true')} className="text-sm text-primary-400 flex items-center gap-1">All <ArrowRight size={14} /></button>
          </div>
          {d.my_work_orders?.length ? (
            <div className="space-y-2">
              {d.my_work_orders.slice(0, 5).map((wo: any) => (
                <div key={wo.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 cursor-pointer hover:bg-white/10" onClick={() => router.push(`/work-orders/${wo.id}`)}>
                  <div>
                    <div className="text-sm font-medium">{wo.title}</div>
                    <div className="text-xs text-muted">{wo.code} - {wo.equipment_name}</div>
                  </div>
                  <StatusBadge status={wo.status} />
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted">No pending work orders</p>}
        </div>
      </div>
    );
  }

  // Supervisor / Admin Dashboard
  const d = data;
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-primary-400 text-xs font-semibold tracking-[0.18em] uppercase mb-1">
            <Sparkles size={13} /> AI-Powered Maintenance
          </div>
          <h1 className="text-2xl font-bold">Smart Maintenance Cockpit</h1>
          <p className="text-sm text-muted mt-1">Operations & Maintenance Dashboard</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          Mock Gateway Online · AI Recommendations Require Verification
        </div>
      </div>
      {intelligence && (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
          <PlatformMetric icon={<CpuIcon />} label="Equipment Assets" value={intelligence.total_equipment} suffix="units" tone="blue" onClick={() => router.push('/equipment')} />
          <PlatformMetric icon={<HeartPulse size={18} />} label="Avg Health Score" value={intelligence.average_health_score} suffix="/100" tone="green" />
          <PlatformMetric icon={<Activity size={18} />} label="Active Anomalies" value={intelligence.active_anomalies} suffix="items" tone="orange" onClick={() => router.push('/monitoring')} />
          <PlatformMetric icon={<ShieldAlert size={18} />} label="High Risk Assets" value={intelligence.high_risk_equipment} suffix="units" tone="red" onClick={() => router.push('/predictive-maintenance')} />
          <PlatformMetric icon={<Clock size={18} />} label="Pending Approvals" value={intelligence.pending_approvals} suffix="items" tone="yellow" onClick={() => router.push('/approvals')} />
          <PlatformMetric icon={<TrendingUp size={18} />} label="Telemetry Points" value={intelligence.simulator?.generated_points || 0} suffix="pts" tone="purple" />
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard icon={<Clock />} label="Pending Dispatch" value={d.pending_dispatch} color="yellow" onClick={() => router.push('/work-orders?status=pending_dispatch')} />
        <StatCard icon={<Wrench />} label="In Progress" value={d.in_progress} color="blue" onClick={() => router.push('/work-orders?status=in_progress')} />
        <StatCard icon={<CheckCircle />} label="Pending Acceptance" value={d.pending_acceptance} color="green" onClick={() => router.push('/work-orders?status=pending_acceptance')} />
        <StatCard icon={<AlertTriangle />} label="Overdue" value={d.overdue} color="red" onClick={() => router.push('/work-orders?status=overdue')} />
        <StatCard icon={<AlertTriangle />} label="Today New" value={d.today_new_faults} color="orange" />
        <StatCard icon={<CheckCircle />} label="Today Completed" value={d.today_completed} color="green" />
      </div>
      {d.avg_repair_hours != null && (
        <p className="text-sm text-muted">Average Repair Time: {d.avg_repair_hours} hours</p>
      )}
      {intelligence && (
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          <div className="card xl:col-span-3">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-semibold">Real-time Equipment Status</h2>
                <p className="text-xs text-muted mt-1">Latest snapshot of motor and bearing telemetry</p>
              </div>
              <button className="text-sm text-primary-400 flex items-center gap-1" onClick={() => router.push('/monitoring')}>View Monitoring <ArrowRight size={14} /></button>
            </div>
            {intelligence.latest_telemetry?.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-xs text-muted border-b border-card-border">
                    <tr><th className="text-left py-2">Equipment</th><th className="text-right">Vibration</th><th className="text-right">Temperature</th><th className="text-right">Current</th><th className="text-right">Load</th><th className="text-right">Status</th></tr>
                  </thead>
                  <tbody>
                    {intelligence.latest_telemetry.slice(0, 6).map((item: any) => (
                      <tr key={item.id} className="border-b border-card-border/50 hover:bg-white/[0.03]">
                        <td className="py-3"><div className="font-medium">{item.equipment_name}</div><div className="text-xs text-muted font-mono">{item.equipment_code}</div></td>
                        <td className="text-right font-mono">{formatMetric(item.vibration_rms, 'mm/s')}</td>
                        <td className="text-right font-mono">{formatMetric(item.bearing_temperature, '°C')}</td>
                        <td className="text-right font-mono">{formatMetric(item.motor_current, 'A')}</td>
                        <td className="text-right font-mono">{formatMetric(item.load_ratio, '%')}</td>
                        <td className="text-right"><span className={`badge ${item.is_anomaly ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'}`}>{item.is_anomaly ? 'Anomaly' : 'Normal'}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="text-sm text-muted py-8 text-center">Real-time telemetry will appear here once simulator is running</p>}
          </div>
          <div className="card xl:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div><h2 className="font-semibold">Risk Predictions</h2><p className="text-xs text-muted mt-1">Deterministic Rule Model · Mock</p></div>
              <button className="text-sm text-primary-400" onClick={() => router.push('/predictive-maintenance')}>View All</button>
            </div>
            <div className="space-y-3">
              {intelligence.risk_predictions?.slice(0, 4).map((prediction: any) => (
                <div key={prediction.id} className="rounded-lg border border-card-border bg-black/10 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div><div className="text-sm font-medium">{prediction.equipment_name}</div><div className="text-xs text-muted mt-1">{failureModeLabel(prediction.failure_mode)}</div></div>
                    <RiskBadge level={prediction.risk_level} />
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-muted">Failure Probability</span><span className="font-mono">{Math.round(prediction.probability * 100)}%</span>
                    <span className="text-muted">RUL</span><span className="font-mono">{prediction.remaining_useful_life_hours}h</span>
                  </div>
                </div>
              ))}
              {!intelligence.risk_predictions?.length && <p className="text-sm text-muted py-6 text-center">No risk predictions available</p>}
            </div>
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-3">Distribution by Priority</h2>
          <div className="space-y-2">
            {d.by_priority?.map((p: any) => (
              <div key={p.priority} className="flex items-center justify-between">
                <span><PriorityBadge priority={p.priority} /></span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 rounded-full bg-white/10">
                    <div className={`h-full rounded-full ${p.priority === 'P1' ? 'bg-red-500' : p.priority === 'P2' ? 'bg-yellow-500' : p.priority === 'P3' ? 'bg-blue-500' : 'bg-gray-500'}`} style={{ width: `${Math.min((p.count / Math.max(...d.by_priority.map((x: any) => x.count || 1))) * 100, 100)}%` }} />
                  </div>
                  <span className="text-sm font-mono">{p.count}</span>
                </div>
              </div>
            )) || <p className="text-sm text-muted">No data</p>}
          </div>
        </div>
        <div className="card">
          <h2 className="font-semibold mb-3">By Equipment Type</h2>
          <div className="space-y-2">
            {d.by_equipment_type?.map((t: any) => (
              <div key={t.equipment_type} className="flex items-center justify-between text-sm">
                <span>{t.equipment_type}</span>
                <span className="font-mono">{t.count}</span>
              </div>
            )) || <p className="text-sm text-muted">No data</p>}
          </div>
        </div>
      </div>
      <div className="card">
        <h2 className="font-semibold mb-3">Recent Work Orders</h2>
        <div className="space-y-1">
          {d.recent_work_orders?.map((wo: any) => (
            <div key={wo.id} className="flex items-center justify-between p-2 rounded hover:bg-white/5 cursor-pointer text-sm" onClick={() => router.push(`/work-orders/${wo.id}`)}>
              <span className="text-muted w-20">{wo.code}</span>
              <span className="flex-1 truncate">{wo.title}</span>
              <StatusBadge status={wo.status} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CpuIcon() {
  return <Wrench size={18} />;
}

function PlatformMetric({ icon, label, value, suffix, tone, onClick }: any) {
  const tones: Record<string, string> = {
    blue: 'text-blue-300 bg-blue-500/10 border-blue-500/20',
    green: 'text-green-300 bg-green-500/10 border-green-500/20',
    orange: 'text-orange-300 bg-orange-500/10 border-orange-500/20',
    red: 'text-red-300 bg-red-500/10 border-red-500/20',
    yellow: 'text-yellow-300 bg-yellow-500/10 border-yellow-500/20',
    purple: 'text-purple-300 bg-purple-500/10 border-purple-500/20',
  };
  return (
    <button type="button" onClick={onClick} className={`text-left rounded-xl border p-3 transition-transform hover:-translate-y-0.5 ${tones[tone] || tones.blue}`}>
      <div className="flex items-center gap-2 text-xs opacity-80">{icon}{label}</div>
      <div className="mt-2 text-xl font-bold text-white">{value}<span className="text-xs font-normal text-muted ml-1">{suffix}</span></div>
    </button>
  );
}

function RiskBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    low: 'bg-green-500/15 text-green-300',
    medium: 'bg-yellow-500/15 text-yellow-300',
    high: 'bg-orange-500/15 text-orange-300',
    critical: 'bg-red-500/15 text-red-300',
  };
  const labels: Record<string, string> = { low: 'Low Risk', medium: 'Medium Risk', high: 'High Risk', critical: 'Critical' };
  return <span className={`badge ${styles[level] || styles.medium}`}>{labels[level] || level}</span>;
}

function failureModeLabel(mode: string) {
  const labels: Record<string, string> = {
    bearing_wear: 'Bearing Wear',
    bearing_overheat: 'Bearing Overheat',
    motor_overload: 'Motor Overload',
    rotor_unbalance: 'Rotor Unbalance',
    shaft_misalignment: 'Shaft Misalignment',
    insufficient_lubrication: 'Insufficient Lubrication',
    voltage_abnormal: 'Voltage Abnormal',
    sensor_abnormal: 'Sensor Anomaly',
    unknown_anomaly: 'Unknown Compound Anomaly',
  };
  return labels[mode] || mode;
}

function formatMetric(value: number | null | undefined, unit: string) {
  return value == null ? '--' : `${value} ${unit}`;
}

function StatCard({ icon, label, value, color, onClick }: any) {
  const colors: any = { blue: 'border-primary/30', yellow: 'border-warning/30', red: 'border-red-500/30', green: 'border-green-500/30', orange: 'border-orange-500/30' };
  return (
    <div className={`card cursor-pointer hover:bg-white/5 transition-colors border-l-4 ${colors[color] || 'border-card-border'}`} onClick={onClick}>
      <div className="text-sm text-muted mb-1">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: any = {
    pending_dispatch: 'bg-gray-500/20 text-gray-400',
    assigned: 'bg-blue-500/20 text-blue-400',
    accepted: 'bg-purple-500/20 text-purple-400',
    in_progress: 'bg-yellow-500/20 text-yellow-400',
    pending_acceptance: 'bg-green-500/20 text-green-400',
    completed: 'bg-green-600/20 text-green-500',
    cancelled: 'bg-gray-500/20 text-gray-500',
    returned: 'bg-red-500/20 text-red-400',
    paused: 'bg-gray-500/20 text-gray-400',
  };
  const labels: any = {
    pending_dispatch: 'Pending Dispatch', assigned: 'Assigned', accepted: 'Accepted', in_progress: 'In Progress',
    pending_acceptance: 'Pending Acceptance', completed: 'Completed', cancelled: 'Cancelled', returned: 'Returned', paused: 'Paused',
  };
  return <span className={`badge ${colors[status] || ''}`}>{labels[status] || status}</span>;
}

function PriorityBadge({ priority }: { priority: string }) {
  const cls: any = { P1: 'badge-p1', P2: 'badge-p2', P3: 'badge-p3', P4: 'badge-p4' };
  return <span className={`badge ${cls[priority] || ''}`}>{PRIORITY_LABELS[priority] || priority}</span>;
}
