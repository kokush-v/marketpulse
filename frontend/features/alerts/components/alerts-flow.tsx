"use client";

import * as React from "react";
import { Handle, type NodeProps, Position } from "reactflow";

import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/lib/utils";

export type FlowStage = "coin" | "scenario" | "timing" | "review";
export type FlowStageStatus = "locked" | "ready" | "active" | "complete" | "error";

export type StageNodeData = {
	stage: FlowStage;
	title: string;
	status: FlowStageStatus;
	body: React.ReactNode;
	badge?: string;
	footer?: React.ReactNode;
	onSelect?: () => void;
};

export const FLOW_STAGE_ORDER: FlowStage[] = ["coin", "scenario", "timing", "review"];

export function getStageLabel(stage: FlowStage): string {
	switch (stage) {
		case "coin":
			return "Coin";
		case "scenario":
			return "Scenario";
		case "timing":
			return "Timing";
		case "review":
			return "Review";
	}
}

export function getStepFromStage(stage: FlowStage): number {
	switch (stage) {
		case "coin":
			return 1;
		case "scenario":
			return 2;
		case "timing":
			return 3;
		case "review":
			return 4;
	}
}

export function getStageFromStep(step: number): FlowStage {
	if (step <= 1) {
		return "coin";
	}
	if (step === 2) {
		return "scenario";
	}
	if (step === 3) {
		return "timing";
	}
	return "review";
}

function StageNode({ data }: NodeProps<StageNodeData>) {
	const statusTone = {
		locked: "border-border/30 bg-background/70 opacity-85",
		ready: "border-border/45 bg-card/90 shadow-[0_18px_45px_rgba(15,23,42,0.08)]",
		active: "border-sky-500/45 bg-card shadow-[0_24px_55px_rgba(14,165,233,0.14)]",
		complete: "border-emerald-500/25 bg-card/90 shadow-[0_18px_45px_rgba(16,185,129,0.08)]",
		error: "border-destructive/40 bg-card shadow-[0_18px_45px_rgba(220,38,38,0.08)]",
	} satisfies Record<FlowStageStatus, string>;

	const statusLabel = {
		locked: "Locked",
		ready: "Ready",
		active: "Active",
		complete: "Complete",
		error: "Needs attention",
	} satisfies Record<FlowStageStatus, string>;

	const frameSize = {
		coin: "w-[20rem] h-[16.5rem]",
		scenario: "w-[42rem] h-[39rem]",
		timing: "w-[20rem] h-[17.5rem]",
		review: "w-[20rem] h-[17rem]",
	} satisfies Record<FlowStage, string>;

	const sourcePositionByStage = {
		coin: Position.Right,
		scenario: Position.Right,
		timing: Position.Right,
		review: Position.Bottom,
	} satisfies Record<FlowStage, Position>;

	const targetPositionByStage = {
		coin: Position.Left,
		scenario: Position.Left,
		timing: Position.Left,
		review: Position.Left,
	} satisfies Record<FlowStage, Position>;

	return (
		<div
			role={data.onSelect ? "button" : undefined}
			tabIndex={data.onSelect ? 0 : undefined}
			onClick={data.onSelect}
			onKeyDown={
				data.onSelect
					? (event) => {
							if (event.key === "Enter" || event.key === " ") {
								event.preventDefault();
								data.onSelect?.();
							}
						}
					: undefined
			}
			className={cn(
				"relative rounded-[28px] border transition-shadow duration-200",
				data.onSelect && "cursor-pointer",
				frameSize[data.stage],
				statusTone[data.status],
			)}>
			<Handle
				type="target"
				position={targetPositionByStage[data.stage]}
				isConnectable={false}
				className="!h-0 !w-0 !border-0 !bg-transparent !opacity-0"
			/>
			<div className="flex h-full flex-col gap-3 p-4">
				<div className="flex items-start justify-between gap-3">
					<div className="min-w-0">
						<p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
							{getStageLabel(data.stage)}
						</p>
						<h3 className="mt-1 text-[15px] font-semibold leading-5 text-foreground">{data.title}</h3>
					</div>
					<Badge
						variant="outline"
						className={cn(
							"shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em]",
							data.status === "active" && "border-sky-500/35 text-sky-700",
							data.status === "complete" && "border-emerald-500/30 text-emerald-700",
							data.status === "error" && "border-destructive/30 text-destructive",
						)}>
						{statusLabel[data.status]}
					</Badge>
				</div>
				<div className="flex-1 overflow-hidden">{data.body}</div>
				{data.footer ? <div className="border-t border-border/30 pt-3">{data.footer}</div> : null}
				<div className="flex items-center justify-between gap-2">
					{data.badge ? (
						<Badge variant="secondary" className="max-w-[11rem] truncate rounded-full px-2.5 py-0.5 text-[11px]">
							{data.badge}
						</Badge>
					) : (
						<span />
					)}
				</div>
			</div>
			{data.stage !== "review" ? (
				<Handle
					type="source"
					position={sourcePositionByStage[data.stage]}
					isConnectable={false}
					className="!h-0 !w-0 !border-0 !bg-transparent !opacity-0"
				/>
			) : null}
		</div>
	);
}

export const stageNodeTypes = {
	stage: StageNode,
} as const;
