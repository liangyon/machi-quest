'use client';

import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { MachiSidebar } from '@/components/machi-sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider
      defaultOpen={false}
    >
      <div className="relative z-50">
        <MachiSidebar />
      </div>
      <SidebarInset className="relative z-10">
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}
