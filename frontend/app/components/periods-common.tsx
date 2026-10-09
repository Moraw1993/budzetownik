"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { Button, Panel } from "./ui";
import { stateLabels, type AccountingMonth } from "../lib/periods-api";

export function PeriodState({ month }: { month: AccountingMonth }) {
  return (
    <span className={`badge period-state period-${month.state}`}>{stateLabels[month.state]}</span>
  );
}
export function ConfirmAction({
  title,
  description,
  confirm,
  pending,
  error,
  onConfirm,
  onCancel,
  variant = "primary",
}: {
  variant?: "primary" | "danger";
  title: string;
  description: string;
  confirm: string;
  pending: boolean;
  error?: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.querySelector<HTMLButtonElement>("button")?.focus();
    return () => {
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  return (
    <div
      ref={ref}
      onKeyDown={(event) => {
        if (event.key === "Escape" && !pending) onCancel();
      }}
    >
      <Panel title={title} description={description}>
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        <div className="row-actions" aria-busy={pending}>
          <Button type="button" variant="secondary" disabled={pending} onClick={onCancel}>
            Anuluj
          </Button>
          <Button type="button" variant={variant} disabled={pending} onClick={onConfirm}>
            {pending ? "Trwa zapisywanie…" : confirm}
          </Button>
        </div>
      </Panel>
    </div>
  );
}
export function LoadError({
  error,
  retry,
  children,
}: {
  error: string;
  retry: () => void;
  children?: ReactNode;
}) {
  return (
    <div>
      <p className="notice error" role="alert">
        {error}
      </p>
      <Button type="button" variant="secondary" onClick={retry}>
        Spróbuj ponownie
      </Button>
      {children}
    </div>
  );
}
