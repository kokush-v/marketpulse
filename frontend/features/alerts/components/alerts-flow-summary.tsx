"use client";

import type { ReactNode } from "react";

import { Button } from "@/shared/components/ui/button";

function PreviewRow({ label, value }: { label: string; value: string }) {
	return (
		<div className="rounded-2xl border border-border/40 bg-background/45 px-3 py-2.5">
			<p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
			<p className="mt-1 text-[13px] font-semibold leading-5">{value}</p>
		</div>
	);
}

type SharedSummaryProps = {
	coinValue: string;
	scenarioValue: string;
	timingValue: string;
	triggerValue: string;
};

export function AlertFlowStageSummary({
	stage,
	coinName,
	coinMeta,
	coinValue,
	scenarioValue,
	timingValue,
	windowValue,
	triggerValue,
	scenarioSummary,
}: SharedSummaryProps & {
	stage: "coin" | "scenario" | "timing" | "review";
	coinName?: string;
	coinMeta?: string;
	windowValue?: string;
	scenarioSummary?: ReactNode;
}) {
	switch (stage) {
		case "coin":
			return (
				<div className="rounded-2xl border border-border/40 bg-background/45 px-3 py-3">
					<p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Coin</p>
					<p className="mt-1 text-[13px] font-semibold leading-5">{coinName ?? "Choose coin"}</p>
					<p className="text-[11px] text-muted-foreground">{coinMeta}</p>
				</div>
			);
		case "scenario":
			return scenarioSummary ?? (
				<div className="space-y-3">
					<PreviewRow label="Scenario" value={scenarioValue} />
					<PreviewRow label="Trigger" value={triggerValue} />
				</div>
			);
		case "timing":
			return (
				<div className="space-y-3">
					<PreviewRow label="Timing" value={timingValue} />
					{windowValue ? <PreviewRow label="Window" value={windowValue} /> : null}
				</div>
			);
		case "review":
			return (
				<div className="grid gap-2 md:grid-cols-2">
					<PreviewRow label="Coin" value={coinValue} />
					<PreviewRow label="Scenario" value={scenarioValue} />
					<PreviewRow label="Timing" value={timingValue} />
					<PreviewRow label="Trigger" value={triggerValue} />
				</div>
			);
	}
}

export function AlertFlowReview({
	coinValue,
	scenarioValue,
	timingValue,
	triggerValue,
	onBack,
	onSave,
	isSaving,
	saveLabel,
	saveDisabled,
}: SharedSummaryProps & {
	onBack: () => void;
	onSave: () => void;
	isSaving: boolean;
	saveLabel: string;
	saveDisabled: boolean;
}) {
	return (
		<div className="space-y-4">
			<div className="grid gap-2 md:grid-cols-2">
				<PreviewRow label="Coin" value={coinValue} />
				<PreviewRow label="Scenario" value={scenarioValue} />
				<PreviewRow label="Timing" value={timingValue} />
				<PreviewRow label="Trigger" value={triggerValue} />
			</div>
			<div className="flex flex-col gap-3 sm:flex-row">
				<Button type="button" variant="outline" className="h-9 rounded-full px-4" onClick={onBack} disabled={isSaving}>
					Back
				</Button>
				<Button type="button" className="h-9 rounded-full px-5" onClick={onSave} disabled={saveDisabled}>
					{isSaving ? "Saving..." : saveLabel}
				</Button>
			</div>
		</div>
	);
}
