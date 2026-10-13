'use client';
import { Settings, Construction } from 'lucide-react';

export default function AdminPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold mb-4">System Administration</h1>
      <div className="card text-center py-16">
        <Construction size={48} className="mx-auto mb-4 text-yellow-400" />
        <h2 className="text-lg font-medium mb-2">Under Construction</h2>
        <p className="text-sm text-muted max-w-md mx-auto">
          System administration features are under development, including user management, role configuration, and system settings.
        </p>
      </div>
    </div>
  );
}
