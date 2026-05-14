// ============================================
// HEADER COMPONENT
// ============================================

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Search, User, Settings, LogOut, ChevronDown, Menu, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useUserStore } from '@/stores';
import {
  apiGetNotifications,
  apiGetUnreadNotificationCount,
  apiMarkNotificationRead,
  type ApiNotification,
} from '@/lib/api';
import { cn } from '@/lib/utils';

interface HeaderProps {
  className?: string;
  onMenuClick?: () => void;
}

export function Header({ className, onMenuClick }: HeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState<ApiNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);

  const loadNotificationCount = async () => {
    try {
      const data = await apiGetUnreadNotificationCount();
      setUnreadCount(data.unread_count);
    } catch {
      setUnreadCount(0);
    }
  };

  const loadNotifications = async () => {
    setIsLoadingNotifications(true);
    try {
      const data = await apiGetNotifications();
      setNotifications(data.results);
      setUnreadCount(data.results.filter((item) => !item.read).length);
    } catch {
      setNotifications([]);
    } finally {
      setIsLoadingNotifications(false);
    }
  };

  useEffect(() => {
    if (!user) return;
    loadNotificationCount();
    const timer = window.setInterval(loadNotificationCount, 45000);
    return () => window.clearInterval(timer);
  }, [user?.id]);

  const handleLogout = () => {
    logout();
  };

  const handleNotificationClick = async (notification: ApiNotification) => {
    if (!notification.read) {
      try {
        await apiMarkNotificationRead(notification.id);
        setNotifications((prev) =>
          prev.map((item) =>
            item.id === notification.id ? { ...item, read: true } : item
          )
        );
        setUnreadCount((count) => Math.max(0, count - 1));
      } catch {
        return;
      }
    }
    if (notification.action_url) navigate(notification.action_url);
  };

  const formatNotificationTime = (value: string) => {
    const date = new Date(value);
    const diffMinutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
    if (diffMinutes < 1) return 'Agora';
    if (diffMinutes < 60) return `${diffMinutes} min`;
    const diffHours = Math.round(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours} h`;
    return date.toLocaleDateString('pt-PT');
  };

  return (
    <header
      className={cn(
        'h-16 bg-card border-b border-border flex items-center justify-between px-4 lg:px-6',
        className
      )}
    >
      {onMenuClick && (
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden mr-2"
          onClick={onMenuClick}
          aria-label="Menu"
        >
          <Menu className="h-5 w-5" />
        </Button>
      )}

      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Pesquisar oportunidades, propostas..."
            className="pl-10 h-10 bg-muted border-0"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Pesquisar"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 lg:gap-4">
        <DropdownMenu onOpenChange={(open) => { if (open) loadNotifications(); }}>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="relative"
              aria-label="Notificacoes"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 min-h-4 min-w-4 px-1 bg-error text-error-foreground text-[10px] rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notificacoes</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <div className="max-h-64 overflow-auto">
              {isLoadingNotifications ? (
                <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  A carregar...
                </div>
              ) : notifications.length === 0 ? (
                <div className="p-4 text-sm text-muted-foreground">
                  Sem notificacoes.
                </div>
              ) : notifications.map((notification) => (
                <DropdownMenuItem
                  key={notification.id}
                  className={cn(
                    'flex flex-col items-start gap-1 p-3',
                    !notification.read && 'bg-primary/5'
                  )}
                  onSelect={() => handleNotificationClick(notification)}
                >
                  <span className="flex w-full items-center justify-between gap-2">
                    <span className="text-sm font-medium truncate">{notification.title}</span>
                    {!notification.read && <span className="h-2 w-2 rounded-full bg-primary" />}
                  </span>
                  <span className="line-clamp-2 text-xs text-muted-foreground">
                    {notification.message}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatNotificationTime(notification.created_at)}
                  </span>
                </DropdownMenuItem>
              ))}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-2">
              <Avatar className="h-8 w-8">
                <AvatarImage src={user?.avatar} alt={user?.name} />
                <AvatarFallback>{user?.name?.charAt(0) || 'U'}</AvatarFallback>
              </Avatar>
              <span className="hidden md:inline text-sm font-medium">{user?.name}</span>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Minha Conta</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => navigate('/settings')}>
              <User className="mr-2 h-4 w-4" />
              Perfil
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => navigate('/settings')}>
              <Settings className="mr-2 h-4 w-4" />
              Definicoes
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-error">
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
