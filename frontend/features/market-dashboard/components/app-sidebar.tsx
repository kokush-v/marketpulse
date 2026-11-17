"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
	BadgeCheck,
	BellRing,
	ChevronsUpDown,
	LayoutDashboard,
	LogOut,
	MessageCircle,
	Star,
} from "lucide-react";

import {
	Sidebar,
	SidebarContent,
	SidebarFooter,
	SidebarGroup,
	SidebarGroupLabel,
	SidebarHeader,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
	SidebarRail,
} from "@/shared/components/ui/sidebar";
import { Avatar, AvatarFallback, AvatarImage } from "@/shared/components/ui/avatar";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuGroup,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { BrandMark } from "@/shared/components/brand-mark";
import { useMeAuthMeGet } from "@/src/api/generated/auth/auth";
import { clearSession } from "@/shared/lib/auth";

const navGroups = [
		{
			label: "General",
			items: [
				{ title: "Overview", icon: LayoutDashboard, href: "/dashboard", color: "text-sky-400" },
			],
		},
		{
			label: "Workspace",
			items: [
				{ title: "Watchlist", icon: Star, href: "/watchlist", color: "text-amber-400" },
				{ title: "Alerts", icon: BellRing, href: "/alerts", color: "text-rose-400" },
				{ title: "Assistant", icon: MessageCircle, href: "/assistant", color: "text-violet-400" },
			],
		},
	];

export function AppSidebar() {
	const pathname = usePathname();

	return (
		<Sidebar collapsible="icon">
			<SidebarHeader>
				<SidebarMenu>
					<SidebarMenuItem>
						<SidebarMenuButton size="lg" asChild>
							<Link href="/dashboard">
								<div className="flex size-8 shrink-0 items-center justify-center">
									<BrandMark />
								</div>
								<div className="grid flex-1 text-left text-sm leading-tight">
									<span className="truncate font-semibold">MarketPulse</span>
									<span className="truncate text-xs text-muted-foreground">Public dashboard</span>
								</div>
							</Link>
						</SidebarMenuButton>
					</SidebarMenuItem>
				</SidebarMenu>
			</SidebarHeader>

			<SidebarContent>
				{navGroups.map((group) => (
					<SidebarGroup key={group.label}>
						<SidebarGroupLabel>{group.label}</SidebarGroupLabel>
						<SidebarMenu>
							{group.items.map((item) => {
								const Icon = item.icon;
								return (
									<SidebarMenuItem key={item.title}>
										<SidebarMenuButton
											asChild
											isActive={pathname === item.href}
										tooltip={item.title}>
											<Link href={item.href} className="flex items-center gap-2">
												<Icon className={item.color} />
												<span>{item.title}</span>
											</Link>
										</SidebarMenuButton>
									</SidebarMenuItem>
								);
							})}
						</SidebarMenu>
					</SidebarGroup>
				))}
			</SidebarContent>

			<SidebarFooter>
				<UserPanel />
			</SidebarFooter>

			<SidebarRail />
		</Sidebar>
	);
}

function UserPanel() {
	const meQuery = useMeAuthMeGet({
		query: {
			staleTime: 60_000,
			retry: 1,
		},
	});

	const handleLogout = async () => {
		try {
			await clearSession();
			window.location.href = "/sign-in";
		} catch (error) {
			console.error("Failed to logout:", error);
		}
	};

	if (meQuery.isLoading) {
		return (
			<SidebarMenu>
				<SidebarMenuItem>
					<div className="px-2 py-1.5 text-xs text-muted-foreground">Loading...</div>
				</SidebarMenuItem>
			</SidebarMenu>
		);
	}

	if (meQuery.isError || !meQuery.data) {
		return (
			<SidebarMenu>
				<SidebarMenuItem>
					<div className="px-2 py-1.5 text-xs text-muted-foreground">Profile unavailable</div>
				</SidebarMenuItem>
			</SidebarMenu>
		);
	}

	const user = meQuery.data;
	const primaryLabel = user.display_name?.trim() || user.email?.split("@")[0] || "User";
	const initialsSource = user.display_name?.trim() || user.email || "";
	const initials = initialsSource
		.split(/[\s.@_-]+/)
		.filter(Boolean)
		.map((part) => part[0])
		.join("")
		.toUpperCase()
		.slice(0, 2) || "U";

	return (
		<SidebarMenu>
			<SidebarMenuItem>
				<DropdownMenu>
					<DropdownMenuTrigger asChild>
						<SidebarMenuButton
							size="lg"
							className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground">
							<Avatar className="h-8 w-8 rounded-lg">
								<AvatarImage
									src={user.avatar_url ?? undefined}
									alt={primaryLabel}
									referrerPolicy="no-referrer"
									crossOrigin="anonymous"
								/>
								<AvatarFallback className="rounded-lg text-xs font-semibold">{initials}</AvatarFallback>
							</Avatar>
							<div className="grid flex-1 text-start text-sm leading-tight">
								<span className="truncate font-semibold text-foreground">{primaryLabel}</span>
								<span className="truncate text-xs text-muted-foreground">{user.email}</span>
							</div>
							<ChevronsUpDown className="ms-auto size-4 text-muted-foreground" />
						</SidebarMenuButton>
					</DropdownMenuTrigger>
					<DropdownMenuContent
						className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg border border-border/30"
						side="top"
						align="end"
						sideOffset={4}>
						<DropdownMenuLabel className="p-0 font-normal">
							<div className="flex items-center gap-2 px-1 py-1.5 text-start text-sm">
								<Avatar className="h-8 w-8 rounded-lg">
									<AvatarImage
										src={user.avatar_url ?? undefined}
										alt={primaryLabel}
										referrerPolicy="no-referrer"
										crossOrigin="anonymous"
									/>
									<AvatarFallback className="rounded-lg text-xs font-semibold">{initials}</AvatarFallback>
								</Avatar>
								<div className="grid flex-1 text-start text-sm leading-tight">
									<span className="truncate font-semibold">{primaryLabel}</span>
									<span className="truncate text-xs text-muted-foreground">{user.email}</span>
								</div>
							</div>
						</DropdownMenuLabel>
						<DropdownMenuSeparator />
						<DropdownMenuGroup>
							<DropdownMenuItem asChild>
								<Link href="/settings" className="cursor-pointer">
									<BadgeCheck className="mr-2 size-4" />
									Settings
								</Link>
							</DropdownMenuItem>
						</DropdownMenuGroup>
						<DropdownMenuSeparator />
						<DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
							<LogOut className="mr-2 size-4" />
							Sign out
						</DropdownMenuItem>
					</DropdownMenuContent>
				</DropdownMenu>
			</SidebarMenuItem>
		</SidebarMenu>
	);
}
