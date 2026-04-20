// ============================================
// DASHBOARD LAYOUT
// ============================================

import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  className?: string;
}

export function DashboardLayout({ className }: DashboardLayoutProps) {
  return (
    <div className={cn('flex min-h-screen bg-background', className)}>
      <Sidebar className="hidden lg:flex fixed h-screen" />
      <div className="flex-1 flex flex-col lg:ml-60">
        <Header className="sticky top-0 z-30" />
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
