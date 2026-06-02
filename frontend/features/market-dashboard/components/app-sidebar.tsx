"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
	Activity,
	BadgeCheck,
	BellRing,
	Bot,
	ChevronsUpDown,
	LayoutGrid,
	LineChart,
	LogOut,
	Settings,
	Star,
	WalletCards,
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
	useSidebar,
} from "@/shared/components/ui/sidebar";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuGroup,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { SupabaseBrowserClient } from "@/shared/lib/supabase";

const navGroups = [
		{
			label: "General",
			items: [
				{ title: "Overview", icon: LayoutGrid, href: "/dashboard" },
				{ title: "Market", icon: LineChart, href: "/dashboard/market", active: false, soon: true },
				{ title: "Signals", icon: Activity, href: "/dashboard/signals", active: false, soon: true },
			],
		},
		{
			label: "Workspace",
			items: [
				{ title: "Watchlist", icon: Star, href: "/watchlist" },
				{ title: "Alerts", icon: BellRing, href: "/alerts" },
				{ title: "Integrations", icon: Bot, href: "/integrations" },
				{ title: "Portfolio", icon: WalletCards, href: "/dashboard/portfolio", active: false, soon: true },
				{ title: "Settings", icon: Settings, href: "/dashboard/settings", active: false, soon: true },
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
								<div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
									<Activity className="size-4" />
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
												<Icon />
												<span>{item.title}</span>
												{item.soon && (
													<Badge variant="secondary" className="ml-auto text-[10px]">
														Soon
													</Badge>
												)}
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
	const { isMobile } = useSidebar();
	const [user, setUser] = React.useState<{ email?: string; id?: string; initials?: string } | null>(null);
	const [isLoading, setIsLoading] = React.useState(true);

	React.useEffect(() => {
		async function fetchUser() {
			try {
				const supabase = SupabaseBrowserClient.getInstance();
				const {
					data: { user: authUser },
				} = await supabase.auth.getUser();

				if (authUser) {
					const email = authUser.email || "";
					const initials = email
						.split("@")[0]
						.split(".")
						.map((p) => p[0])
						.join("")
						.toUpperCase()
						.slice(0, 2);

					setUser({
						email,
						id: authUser.id,
						initials: initials || "U",
					});
				}
			} catch (error) {
				console.error("Failed to fetch user:", error);
			} finally {
				setIsLoading(false);
			}
		}

		fetchUser();
	}, []);

	const handleLogout = async () => {
		try {
			const supabase = SupabaseBrowserClient.getInstance();
			await supabase.auth.signOut();
			localStorage.removeItem("mp_access_token");
			localStorage.removeItem("mp_refresh_token");
			window.location.href = "/sign-in";
		} catch (error) {
			console.error("Failed to logout:", error);
		}
	};

	if (isLoading || !user) {
		return (
			<SidebarMenu>
				<SidebarMenuItem>
					<div className="px-2 py-1.5 text-xs text-muted-foreground">
						{isLoading ? "Loading..." : "Not authenticated"}
					</div>
				</SidebarMenuItem>
			</SidebarMenu>
		);
	}

	return (
		<SidebarMenu>
			<SidebarMenuItem>
				<DropdownMenu>
					<DropdownMenuTrigger asChild>
						<SidebarMenuButton
							size="lg"
							className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground">
							<Avatar className="h-8 w-8 rounded-lg">
								<AvatarFallback className="rounded-lg text-xs font-semibold">{user.initials}</AvatarFallback>
							</Avatar>
							<div className="grid flex-1 text-start text-sm leading-tight">
								<span className="truncate font-semibold text-foreground">{user.email?.split("@")[0]}</span>
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
									<AvatarFallback className="rounded-lg text-xs font-semibold">{user.initials}</AvatarFallback>
								</Avatar>
								<div className="grid flex-1 text-start text-sm leading-tight">
									<span className="truncate font-semibold">{user.email?.split("@")[0]}</span>
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
