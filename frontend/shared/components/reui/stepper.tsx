"use client";

import {
  Children,
  createContext,
  isValidElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type HTMLAttributes,
  type ReactElement,
} from "react";

import { cn } from "@/shared/lib/utils";

type StepperOrientation = "horizontal" | "vertical";
type StepState = "active" | "completed" | "inactive" | "loading";
type StepIndicators = {
  active?: React.ReactNode;
  completed?: React.ReactNode;
  inactive?: React.ReactNode;
  loading?: React.ReactNode;
};

interface StepperContextValue {
  activeStep: number;
  setActiveStep: (step: number) => void;
  stepsCount: number;
  orientation: StepperOrientation;
  registerTrigger: (node: HTMLButtonElement | null) => void;
  triggerNodes: HTMLButtonElement[];
  focusNext: (currentIdx: number) => void;
  focusPrev: (currentIdx: number) => void;
  focusFirst: () => void;
  focusLast: () => void;
  indicators: StepIndicators;
}

interface StepItemContextValue {
  step: number;
  state: StepState;
  isDisabled: boolean;
  isLoading: boolean;
}

const StepperContext = createContext<StepperContextValue | undefined>(undefined);
const StepItemContext = createContext<StepItemContextValue | undefined>(undefined);

function useStepper() {
  const context = useContext(StepperContext);
  if (!context) {
    throw new Error("useStepper must be used within a Stepper");
  }
  return context;
}

function useStepItem() {
  const context = useContext(StepItemContext);
  if (!context) {
    throw new Error("useStepItem must be used within a StepperItem");
  }
  return context;
}

interface StepperProps extends HTMLAttributes<HTMLDivElement> {
  defaultValue?: number;
  value?: number;
  onValueChange?: (value: number) => void;
  orientation?: StepperOrientation;
  indicators?: StepIndicators;
}

function Stepper({
  defaultValue = 1,
  value,
  onValueChange,
  orientation = "horizontal",
  className,
  children,
  indicators = {},
  ...props
}: StepperProps) {
  const [activeStep, setActiveStep] = useState(defaultValue);
  const [triggerNodes, setTriggerNodes] = useState<HTMLButtonElement[]>([]);

  const registerTrigger = useCallback((node: HTMLButtonElement | null) => {
    setTriggerNodes((previous) => {
      if (node && !previous.includes(node)) {
        return [...previous, node];
      }
      return previous.filter((item) => item !== null);
    });
  }, []);

  const handleSetActiveStep = useCallback(
    (step: number) => {
      if (value === undefined) {
        setActiveStep(step);
      }
      onValueChange?.(step);
    },
    [onValueChange, value]
  );

  const currentStep = value ?? activeStep;

  const focusTrigger = (index: number) => {
    if (triggerNodes[index]) {
      triggerNodes[index].focus();
    }
  };

  const contextValue = useMemo<StepperContextValue>(
    () => ({
      activeStep: currentStep,
      setActiveStep: handleSetActiveStep,
      stepsCount: Children.toArray(children).filter(
        (child): child is ReactElement =>
          isValidElement(child) &&
          (child.type as { displayName?: string }).displayName === "StepperItem"
      ).length,
      orientation,
      registerTrigger,
      focusNext: (currentIdx) => focusTrigger((currentIdx + 1) % triggerNodes.length),
      focusPrev: (currentIdx) => focusTrigger((currentIdx - 1 + triggerNodes.length) % triggerNodes.length),
      focusFirst: () => focusTrigger(0),
      focusLast: () => focusTrigger(triggerNodes.length - 1),
      triggerNodes,
      indicators,
    }),
    [children, currentStep, handleSetActiveStep, indicators, orientation, registerTrigger, triggerNodes]
  );

  return (
    <StepperContext.Provider value={contextValue}>
      <div
        role="tablist"
        aria-orientation={orientation}
        data-orientation={orientation}
        data-slot="stepper"
        className={cn("w-full", className)}
        {...props}
      >
        {children}
      </div>
    </StepperContext.Provider>
  );
}

interface StepperItemProps extends React.HTMLAttributes<HTMLDivElement> {
  step: number;
  completed?: boolean;
  disabled?: boolean;
  loading?: boolean;
}

function StepperItem({
  step,
  completed = false,
  disabled = false,
  loading = false,
  className,
  children,
  ...props
}: StepperItemProps) {
  const { activeStep } = useStepper();

  const state: StepState =
    completed || step < activeStep ? "completed" : activeStep === step ? "active" : "inactive";
  const isLoading = loading && step === activeStep;

  return (
    <StepItemContext.Provider value={{ step, state, isDisabled: disabled, isLoading }}>
      <div
        data-slot="stepper-item"
        data-state={state}
        data-loading={isLoading || undefined}
        className={cn(
          "group/step flex items-center justify-center not-last:flex-1 group-data-[orientation=horizontal]/stepper-nav:flex-row group-data-[orientation=vertical]/stepper-nav:flex-col",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </StepItemContext.Provider>
  );
}

interface StepperTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

function StepperTrigger({ asChild = false, className, children, tabIndex, ...props }: StepperTriggerProps) {
  const { state, isLoading, step, isDisabled } = useStepItem();
  const { setActiveStep, activeStep, registerTrigger, triggerNodes, focusNext, focusPrev, focusFirst, focusLast } =
    useStepper();
  const isSelected = activeStep === step;
  const id = `stepper-tab-${step}`;
  const panelId = `stepper-panel-${step}`;
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (buttonRef.current) {
      registerTrigger(buttonRef.current);
    }
  }, [registerTrigger]);

  const triggerIndex = useMemo(
    () => triggerNodes.findIndex((node) => node === buttonRef.current),
    [triggerNodes]
  );

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
        event.preventDefault();
        if (triggerIndex !== -1) {
          focusNext(triggerIndex);
        }
        break;
      case "ArrowLeft":
      case "ArrowUp":
        event.preventDefault();
        if (triggerIndex !== -1) {
          focusPrev(triggerIndex);
        }
        break;
      case "Home":
        event.preventDefault();
        focusFirst();
        break;
      case "End":
        event.preventDefault();
        focusLast();
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        setActiveStep(step);
        break;
    }
  };

  if (asChild) {
    return (
      <span data-slot="stepper-trigger" data-state={state} className={className}>
        {children}
      </span>
    );
  }

  return (
    <button
      ref={buttonRef}
      role="tab"
      id={id}
      aria-selected={isSelected}
      aria-controls={panelId}
      tabIndex={typeof tabIndex === "number" ? tabIndex : isSelected ? 0 : -1}
      data-slot="stepper-trigger"
      data-state={state}
      data-loading={isLoading}
      className={cn(
        "inline-flex cursor-pointer items-center gap-2.5 rounded-full outline-none transition focus-visible:z-10 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40 disabled:pointer-events-none disabled:opacity-60",
        className
      )}
      onClick={() => setActiveStep(step)}
      onKeyDown={handleKeyDown}
      disabled={isDisabled}
      {...props}
    >
      {children}
    </button>
  );
}

function StepperIndicator({ children, className }: React.ComponentProps<"div">) {
  const { state, isLoading } = useStepItem();
  const { indicators } = useStepper();

  const indicator =
    (isLoading && indicators.loading) ||
    (state === "completed" && indicators.completed) ||
    (state === "active" && indicators.active) ||
    (state === "inactive" && indicators.inactive) ||
    children;

  return (
    <div
      data-slot="stepper-indicator"
      data-state={state}
      className={cn(
        "relative flex size-7 shrink-0 items-center justify-center overflow-hidden rounded-full border border-border/40 bg-muted/40 text-xs font-semibold text-muted-foreground transition data-[state=active]:border-sky-500/60 data-[state=active]:bg-sky-500 data-[state=active]:text-white data-[state=completed]:border-emerald-500/50 data-[state=completed]:bg-emerald-500 data-[state=completed]:text-white",
        className
      )}
    >
      <div className="absolute">{indicator}</div>
    </div>
  );
}

function StepperSeparator({ className }: React.ComponentProps<"div">) {
  const { state } = useStepItem();

  return (
    <div
      data-slot="stepper-separator"
      data-state={state}
      className={cn(
        "m-0.5 rounded-sm bg-border/50 group-data-[orientation=horizontal]/stepper-nav:h-0.5 group-data-[orientation=horizontal]/stepper-nav:flex-1 group-data-[orientation=vertical]/stepper-nav:h-12 group-data-[orientation=vertical]/stepper-nav:w-0.5",
        className
      )}
    />
  );
}

function StepperTitle({ children, className }: React.ComponentProps<"h3">) {
  const { state } = useStepItem();

  return (
    <h3
      data-slot="stepper-title"
      data-state={state}
      className={cn("text-sm font-medium leading-none transition", className)}
    >
      {children}
    </h3>
  );
}

function StepperDescription({ children, className }: React.ComponentProps<"div">) {
  const { state } = useStepItem();

  return (
    <div
      data-slot="stepper-description"
      data-state={state}
      className={cn("text-sm text-muted-foreground transition", className)}
    >
      {children}
    </div>
  );
}

function StepperNav({ children, className }: React.ComponentProps<"nav">) {
  const { activeStep, orientation } = useStepper();

  return (
    <nav
      data-slot="stepper-nav"
      data-state={activeStep}
      data-orientation={orientation}
      className={cn(
        "group/stepper-nav inline-flex data-[orientation=horizontal]:w-full data-[orientation=horizontal]:flex-row data-[orientation=vertical]:flex-col",
        className
      )}
    >
      {children}
    </nav>
  );
}

function StepperPanel({ children, className }: React.ComponentProps<"div">) {
  const { activeStep } = useStepper();

  return (
    <div data-slot="stepper-panel" data-state={activeStep} className={cn("w-full", className)}>
      {children}
    </div>
  );
}

interface StepperContentProps extends React.ComponentProps<"div"> {
  value: number;
  forceMount?: boolean;
}

function StepperContent({ value, forceMount, children, className }: StepperContentProps) {
  const { activeStep } = useStepper();
  const isActive = value === activeStep;

  if (!forceMount && !isActive) {
    return null;
  }

  return (
    <div
      data-slot="stepper-content"
      data-state={activeStep}
      className={cn("w-full", className, !isActive && forceMount && "hidden")}
      hidden={!isActive && forceMount}
    >
      {children}
    </div>
  );
}

StepperItem.displayName = "StepperItem";

export {
  Stepper,
  StepperContent,
  StepperDescription,
  StepperIndicator,
  StepperItem,
  StepperNav,
  StepperPanel,
  StepperSeparator,
  StepperTitle,
  StepperTrigger,
  useStepItem,
  useStepper,
  type StepperContentProps,
  type StepperItemProps,
  type StepperProps,
  type StepperTriggerProps,
};
