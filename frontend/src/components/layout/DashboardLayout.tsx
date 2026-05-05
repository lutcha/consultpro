// ============================================
// DASHBOARD LAYOUT - With mobile sidebar support
// ============================================

import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  className?: string;
}

export function DashboardLayout({ className }: DashboardLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className={cn('flex min-h-screen bg-background', className)}>
      {/* Desktop Sidebar */}
      <Sidebar className="hidden lg:flex fixed h-screen" />

      {/* Mobile Sidebar Overlay */}
      <Sidebar
        className={cn(
          'lg:hidden fixed inset-0 z-50 h-screen w-60 transition-transform duration-300',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        onClose={() => setMobileOpen(false)}
      />

      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <div className="flex-1 flex flex-col lg:ml-60">
        <Header
          className="sticky top-0 z-30"
          onMenuClick={() => setMobileOpen(true)}
        />
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
