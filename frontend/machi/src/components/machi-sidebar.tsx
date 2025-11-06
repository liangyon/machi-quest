'use client';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarTrigger,
  useSidebar,
} from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Gamepad2,
  Settings,
  Trophy,
  Target,
  Activity,
  User,
  LogOut,
} from 'lucide-react';
import type { Route } from '@/components/nav-main';
import DashboardNavigation from '@/components/nav-main';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

import Image from 'next/image';

const dashboardRoutes: Route[] = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    icon: <LayoutDashboard className="size-4" />,
    link: '/dashboard',
  },
  {
    id: 'game',
    title: 'Game',
    icon: <Gamepad2 className="size-4" />,
    link: '/dashboard/game',
  },
  {
    id: 'quests',
    title: 'Quests',
    icon: <Target className="size-4" />,
    link: '/dashboard/quests',
  },
  {
    id: 'achievements',
    title: 'Achievements',
    icon: <Trophy className="size-4" />,
    link: '/dashboard/achievements',
  },
  {
    id: 'activity',
    title: 'Activity',
    icon: <Activity className="size-4" />,
    link: '/dashboard/activity',
  },
  {
    id: 'settings',
    title: 'Settings',
    icon: <Settings className="size-4" />,
    link: '/dashboard/settings',
  },
];

export function MachiSidebar() {
  const { state } = useSidebar();
  const { user, logout } = useAuth();
  const router = useRouter();
  const isCollapsed = state === 'collapsed';

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <Sidebar variant="floating" collapsible="icon">
      <SidebarHeader
        className={cn(
          'flex md:pt-3.5',
          isCollapsed
            ? 'flex-row items-center justify-between gap-y-4 md:flex-col md:items-start md:justify-start'
            : 'flex-row items-center justify-between'
        )}
      >
        <a href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg ">
            <Image src="/Leaf.png" alt="Machi Quest" width={25} height={25} />
          </div>
          {!isCollapsed && (
            <span className="font-semibold text-black dark:text-white">
              Machi Quest
            </span>
          )}
        </a>

        <motion.div
          key={isCollapsed ? 'header-collapsed' : 'header-expanded'}
          className={cn(
            'flex items-center gap-2',
            isCollapsed ? 'flex-row md:flex-col-reverse' : 'flex-row'
          )}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <SidebarTrigger />
        </motion.div>
      </SidebarHeader>

      <SidebarContent className="gap-4 px-2 py-4">
        <DashboardNavigation routes={dashboardRoutes} />
      </SidebarContent>

      <SidebarFooter className="px-2 pb-4">
        <div className={cn(
          'flex items-center gap-2 rounded-lg border p-2',
          isCollapsed && 'flex-col'
        )}>
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <User className="size-4 shrink-0" />
                <span className="text-sm font-medium truncate">
                  {user?.display_name || user?.email || 'User'}
                </span>
              </div>
            </div>
          )}
          <Button
            variant="ghost"
            size={isCollapsed ? 'icon' : 'sm'}
            onClick={handleLogout}
            className="shrink-0"
            title="Logout"
          >
            <LogOut className="size-4" />
            {!isCollapsed && <span className="ml-2">Logout</span>}
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
