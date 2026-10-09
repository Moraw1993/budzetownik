"use client";
import { useEffect, useId, useRef, useState, useCallback } from "react";
import { type Company, type Household } from "../lib/api";
import { CompanyCreateForm } from "./company-panel";
import { Button } from "./ui";

export function CompanyDialog({
  household,
  onCreated,
  onClose,
  refreshAccess,
  onPendingChange,
}: {
  household: Household;
  onCreated: (company: Company) => void;
  onClose: () => void;
  refreshAccess: () => void;
  onPendingChange?: (pending: boolean) => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [pending, setPending] = useState(false);
  const updatePending = useCallback(
    (value: boolean) => {
      setPending(value);
      onPendingChange?.(value);
    },
    [onPendingChange],
  );
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.showModal();
    ref.current?.querySelector<HTMLInputElement>('input[name="name"]')?.focus();
    return () => {
      const company = previous
        ?.closest("#contract-form")
        ?.querySelector<HTMLSelectElement>("select[name=company_id]");
      if (company?.isConnected) company.focus();
      else if (previous?.isConnected) previous.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="company-dialog"
      aria-labelledby={titleId}
      onClose={onClose}
      onCancel={(event) => {
        if (pending) event.preventDefault();
      }}
    >
      <div className="dialog-heading">
        <div>
          <h2 id={titleId}>Nowa firma</h2>
          <p className="muted">Podaj nazwę firmy. Po zapisaniu wybierzemy ją w umowie.</p>
        </div>
        <Button
          type="button"
          variant="secondary"
          disabled={pending}
          onClick={() => ref.current?.close()}
        >
          Anuluj
        </Button>
      </div>
      <CompanyCreateForm
        household={household}
        refreshAccess={refreshAccess}
        onPendingChange={updatePending}
        onCreated={(company) => {
          onCreated(company);
          ref.current?.close();
        }}
      />
    </dialog>
  );
}
