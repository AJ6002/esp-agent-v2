'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { getKnowledge, updateKnowledge, listEquipmentTypes, listFaultCodes } from '@/lib/api';
import { KNOWLEDGE_CATEGORY_LABELS } from '@/lib/types';
import { ArrowLeft, Save } from 'lucide-react';
import toast from 'react-hot-toast';

export default function KnowledgeEdit() {
  const { id } = useParams();
  const { user } = useAuth();
  const router = useRouter();
  const [types, setTypes] = useState<any[]>([]);
  const [faultCodes, setFaultCodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '', category: 'experience', content: '', summary: '', tags: '',
    equipment_type_id: '', fault_code_id: '', source: '', status: 'published',
  });

  useEffect(() => {
    listEquipmentTypes().then(setTypes).catch(() => {});
    listFaultCodes().then(setFaultCodes).catch(() => {});
    if (user?.role !== 'admin' && user?.role !== 'supervisor') {
      toast.error('Permission denied to edit knowledge articles');
      router.push('/knowledge');
      return;
    }
    getKnowledge(Number(id))
      .then(item => {
        setForm({
          title: item.title || '', category: item.category || 'experience', content: item.content || '',
          summary: item.summary || '', tags: item.tags?.join(', ') || '',
          equipment_type_id: item.equipment_type_id ? String(item.equipment_type_id) : '',
          fault_code_id: item.fault_code_id ? String(item.fault_code_id) : '',
          source: item.source || '', status: item.status || 'published',
        });
      })
      .catch((e: any) => { toast.error(e.message); router.push('/knowledge'); })
      .finally(() => setLoading(false));
  }, [id, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) {
      toast.error('Title and content cannot be empty');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        equipment_type_id: form.equipment_type_id ? Number(form.equipment_type_id) : null,
        fault_code_id: form.fault_code_id ? Number(form.fault_code_id) : null,
        tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
      };
      await updateKnowledge(Number(id), payload);
      toast.success('Saved successfully');
      router.push(`/knowledge/${id}`);
    } catch (e: any) { toast.error(e.message); } finally { setSaving(false); }
  };

  if (loading) return <div className="max-w-2xl mx-auto text-muted p-6">Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => router.push(`/knowledge/${id}`)} className="btn btn-sm btn-outline">
          <ArrowLeft size={14} /> Back
        </button>
        <h1 className="text-xl font-bold">Edit Knowledge Article</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Title <span className="text-red-400">*</span></label>
          <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="w-full" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Category <span className="text-red-400">*</span></label>
            <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="w-full">
              {Object.entries(KNOWLEDGE_CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="w-full">
              <option value="published">Published</option>
              <option value="draft">Draft</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Summary</label>
          <textarea value={form.summary} onChange={e => setForm({ ...form, summary: e.target.value })} className="w-full" rows={2} />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Content <span className="text-red-400">*</span></label>
          <textarea value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} className="w-full min-h-[200px]" rows={10} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Equipment Type</label>
            <select value={form.equipment_type_id} onChange={e => setForm({ ...form, equipment_type_id: e.target.value })} className="w-full">
              <option value="">None</option>
              {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Fault Code</label>
            <select value={form.fault_code_id} onChange={e => setForm({ ...form, fault_code_id: e.target.value })} className="w-full">
              <option value="">None</option>
              {faultCodes.map(f => <option key={f.id} value={f.id}>{f.code} - {f.name}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Source</label>
            <input value={form.source} onChange={e => setForm({ ...form, source: e.target.value })} className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Tags (comma separated)</label>
            <input value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} className="w-full" />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={() => router.back()} className="btn btn-outline">Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            <Save size={14} /> {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
}
