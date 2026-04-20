// ============================================
// SIDEBAR COMPONENT
// ============================================

import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Users,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface SidebarProps {
  className?: string;
}

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Oportunidades',
    href: '/opportunities',
    icon: Briefcase,
  },
  {
    name: 'Propostas',
    href: '/proposals',
    icon: FileText,
  },
  {
    name: 'Projetos',
    href: '/projects',
    icon: Briefcase,
  },
  {
    name: 'Equipas',
    href: '/teams',
    icon: Users,
  },
  {
    name: 'Definições',
    href: '/settings',
    icon: Settings,
  },
];

export function Sidebar({ className }: SidebarProps) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  
  return (
    <aside
      className={cn(
        'bg-card border-r border-border flex flex-col transition-all duration-300',
        collapsed ? 'w-16' : 'w-60',
        className
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
              <Briefcase className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-semibold text-lg">ConsultPro</span>
          </div>
        )}
        {collapsed && (
          <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center mx-auto">
            <Briefcase className="h-4 w-4 text-primary-foreground" />
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          className={cn('h-8 w-8', collapsed && 'hidden')}
          onClick={() => setCollapsed(true)}
          aria-label="Colapsar menu"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>
      
      {/* Collapse button when collapsed */}
      {collapsed && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 mx-auto mt-2"
          onClick={() => setCollapsed(false)}
          aria-label="Expandir menu"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      )}
      
      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {navigationItems.map((item) => {
          const isActive = location.pathname.startsWith(item.href);
          const Icon = item.icon;
          
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                collapsed && 'justify-center px-2'
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>
      
      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-border">
          <div className="bg-muted rounded-lg p-3">
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Plano Atual
            </p>
            <p className="text-sm font-semibold">Professional</p>
            <div className="mt-2 h-1.5 bg-muted-foreground/20 rounded-full overflow-hidden">
              <div className="h-full w-3/4 bg-primary rounded-full" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              12/15 propostas este mês
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}
