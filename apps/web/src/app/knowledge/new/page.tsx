'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { createKnowledge, listEquipmentTypes, listFaultCodes } from '@/lib/api';
import { KNOWLEDGE_CATEGORY_LABELS } from '@/lib/types';
import { ArrowLeft, Save } from 'lucide-react';
import toast from 'react-hot-toast';

export default function KnowledgeNew() {
  const { user } = useAuth();
  const router = useRouter();
  const [types, setTypes] = useState<any[]>([]);
  const [faultCodes, setFaultCodes] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '', category: 'experience', content: '', summary: '', tags: '',
    equipment_type_id: '', fault_code_id: '', source: '', status: 'published',
  });

  useEffect(() => {
    listEquipmentTypes().then(setTypes).catch(() => {});
    listFaultCodes().then(setFaultCodes).catch(() => {});
    if (user?.role !== 'admin' && user?.role !== 'supervisor') {
      toast.error('Permission denied to create knowledge articles');
      router.push('/knowledge');
    }
  }, [user, router]);

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
      const result = await createKnowledge(payload);
      toast.success('Created successfully');
      router.push(`/knowledge/${result.id}`);
    } catch (e: any) { toast.error(e.message); } finally { setSaving(false); }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => router.push('/knowledge')} className="btn btn-sm btn-outline">
          <ArrowLeft size={14} /> Back
        </button>
        <h1 className="text-xl font-bold">New Knowledge Article</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <FormField label="Title" required>
          <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Article title" className="w-full" />
        </FormField>

        <div className="grid grid-cols-2 gap-4">
          <FormField label="Category" required>
            <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="w-full">
              {Object.entries(KNOWLEDGE_CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </FormField>
          <FormField label="Status">
            <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="w-full">
              <option value="published">Published</option>
              <option value="draft">Draft</option>
            </select>
          </FormField>
        </div>

        <FormField label="Summary">
          <textarea value={form.summary} onChange={e => setForm({ ...form, summary: e.target.value })} placeholder="Brief summary of the article" className="w-full" rows={2} />
        </FormField>

        <FormField label="Content" required>
          <textarea value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} placeholder="Article body content (Markdown supported)" className="w-full min-h-[200px]" rows={10} />
        </FormField>

        <div className="grid grid-cols-2 gap-4">
          <FormField label="Equipment Type">
            <select value={form.equipment_type_id} onChange={e => setForm({ ...form, equipment_type_id: e.target.value })} className="w-full">
              <option value="">None</option>
              {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </FormField>
          <FormField label="Fault Code">
            <select value={form.fault_code_id} onChange={e => setForm({ ...form, fault_code_id: e.target.value })} className="w-full">
              <option value="">None</option>
              {faultCodes.map(f => <option key={f.id} value={f.id}>{f.code} - {f.name}</option>)}
            </select>
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField label="Source">
            <input value={form.source} onChange={e => setForm({ ...form, source: e.target.value })} placeholder="e.g. Maintenance Manual V3.2" className="w-full" />
          </FormField>
          <FormField label="Tags (comma separated)">
            <input value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} placeholder="e.g. Proximity Switch, Packaging Machine, E104" className="w-full" />
          </FormField>
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

function FormField({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}{required && <span className="text-red-400 ml-0.5">*</span>}</label>
      {children}
    </div>
  );
}
