import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarInset,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuSub,
    SidebarMenuSubButton,
    SidebarMenuSubItem,
    SidebarProvider,
    SidebarRail,
    SidebarTrigger,
} from '@/components/ui/sidebar';
import { NavUser } from '@/components/nav-user';
import { type BreadcrumbItem } from '@/types';
import { type PropsWithChildren } from 'react';
import { Link } from '@inertiajs/react';
import {
    BoxIcon,
    FileIcon,
    HomeIcon,
    Settings2Icon,
    UploadIcon,
} from 'lucide-react';

interface AppLayoutProps extends PropsWithChildren {
    breadcrumbs?: BreadcrumbItem[];
}

export default function AppSidebarLayout({ children, breadcrumbs }: AppLayoutProps) {
    return (
        <SidebarProvider defaultOpen={true}>
            <Sidebar collapsible="icon">
                <SidebarHeader>
                    <div className="flex items-center gap-2 p-2">
                        <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                            <BoxIcon className="size-4" />
                        </div>
                        <div className="flex flex-col gap-0.5 leading-none">
                            <span className="font-semibold">PolluxWeb</span>
                            <span className="text-xs text-muted-foreground">v1.0.0</span>
                        </div>
                    </div>
                </SidebarHeader>
                <SidebarContent>
                    <SidebarGroup>
                        <SidebarGroupLabel>Menu</SidebarGroupLabel>
                        <SidebarGroupContent>
                            <SidebarMenu>
                                <SidebarMenuItem>
                                    <SidebarMenuButton asChild>
                                        <Link href="/dashboard">
                                            <HomeIcon />
                                            <span>Dashboard</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>

                                {/* 3D Models section */}
                                <SidebarMenuItem>
                                    <SidebarMenuButton asChild>
                                        <Link href="/3d">
                                            <BoxIcon />
                                            <span>Modelos 3D</span>
                                        </Link>
                                    </SidebarMenuButton>
                                    <SidebarMenuSub>
                                        <SidebarMenuSubItem>
                                            <SidebarMenuSubButton asChild>
                                                <Link href="/3d">
                                                    <FileIcon className="h-4 w-4" />
                                                    <span>Ver archivos</span>
                                                </Link>
                                            </SidebarMenuSubButton>
                                        </SidebarMenuSubItem>
                                        <SidebarMenuSubItem>
                                            <SidebarMenuSubButton asChild>
                                                <Link href="/3d/upload">
                                                    <UploadIcon className="h-4 w-4" />
                                                    <span>Subir archivo</span>
                                                </Link>
                                            </SidebarMenuSubButton>
                                        </SidebarMenuSubItem>
                                    </SidebarMenuSub>
                                </SidebarMenuItem>

                                <SidebarMenuItem>
                                    <SidebarMenuButton asChild>
                                        <Link href="/settings">
                                            <Settings2Icon />
                                            <span>Settings</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            </SidebarMenu>
                        </SidebarGroupContent>
                    </SidebarGroup>
                </SidebarContent>
                <SidebarFooter>
                    <NavUser />
                </SidebarFooter>
                <SidebarRail />
            </Sidebar>
            <SidebarInset>
                <header className="border-b p-4">
                    <div className="flex items-center gap-2">
                        <SidebarTrigger />
                        {breadcrumbs && (
                            <nav className="flex items-center space-x-2 text-sm">
                                {breadcrumbs.map((item, index) => (
                                    <div key={item.href} className="flex items-center">
                                        {index > 0 && <span className="mx-2 text-muted-foreground">/</span>}
                                        {index === breadcrumbs.length - 1 ? (
                                            <span className="text-muted-foreground">{item.title}</span>
                                        ) : (
                                            <Link href={item.href} className="text-foreground hover:underline">
                                                {item.title}
                                            </Link>
                                        )}
                                    </div>
                                ))}
                            </nav>
                        )}
                    </div>
                </header>
                <main className="flex-1">{children}</main>
            </SidebarInset>
        </SidebarProvider>
    );
}
