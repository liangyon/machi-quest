'use client';

import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { MachiSidebar } from '@/components/machi-sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <MachiSidebar />
      <SidebarInset>
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}
