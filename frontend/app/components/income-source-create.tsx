"use client";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import {
  apiAllPages,
  householdPath,
  messageOf,
  type Company,
  type Household,
  type HouseholdMember,
} from "../lib/api";
import { ContractForm } from "./contract-form";
import { OtherSourceForm } from "./other-source-form";
import { CompanyDialog } from "./company-dialog";
import { ConfirmAction } from "./periods-common";
import { Button, SelectField } from "./ui";

export function IncomeSourceCreate({
  household,
  suggestedStartDate,
  refreshAccess,
  members,
  memberId,
  onSaved,
  onCancel,
  onPendingChange,
}: {
  household: Household;
  suggestedStartDate?: string;
  refreshAccess?: () => void;
  members: HouseholdMember[];
  memberId: string | null;
  onSaved: (id: string, kind: "other" | "contract") => void;
  onCancel: () => void;
  onPendingChange?: (pending: boolean) => void;
}) {
  const [pending, setPending] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [discard, setDiscard] = useState<{ run: () => void } | null>(null);
  const updatePending = useCallback(
    (value: boolean) => {
      setPending(value);
      onPendingChange?.(value);
    },
    [onPendingChange],
  );
  const [kind, setKind] = useState("other");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [company, setCompany] = useState("");
  const [dialog, setDialog] = useState(false);
  const [error, setError] = useState("");
  const root = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    root.current?.showModal();
    root.current?.querySelector<HTMLSelectElement>("select")?.focus();
    return () => {
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    apiAllPages<Company>(householdPath(household.id, "companies/"), controller.signal)
      .then((reply) => {
        if (!controller.signal.aborted) setCompanies(reply);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [household.id]);
  function accessChanged() {
    setError("Dostęp zmienił się. Odśwież aplikację.");
    refreshAccess?.();
  }
  function leave(run: () => void) {
    if (pending) return;
    if (dirty) setDiscard({ run });
    else run();
  }
  return (
    <dialog
      ref={root}
      id="income-source-dialog"
      className="income-source-dialog"
      aria-labelledby={titleId}
      onChangeCapture={(event) => {
        if ((event.target as HTMLElement).closest("form")) setDirty(true);
      }}
      onCancel={(event) => {
        if (event.target !== event.currentTarget) return;
        event.preventDefault();
        if (discard) setDiscard(null);
        else if (!dialog) leave(onCancel);
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape" && discard) {
          event.preventDefault();
          event.stopPropagation();
          setDiscard(null);
        }
      }}
    >
      {discard && (
        <ConfirmAction
          variant="danger"
          title="Odrzucić szkic źródła?"
          description="Niezapisane dane źródła zostaną usunięte. Przychody pozostaną bez zmian."
          confirm="Odrzuć szkic źródła"
          pending={pending}
          onCancel={() => setDiscard(null)}
          onConfirm={() => {
            const run = discard.run;
            setDiscard(null);
            setDirty(false);
            run();
          }}
        />
      )}
      <div className="income-source-dialog-content" inert={discard ? true : undefined}>
        <div className="dialog-heading">
          <div>
            <h2 id={titleId}>Nowe źródło dochodu</h2>
            <p className="muted">Dodaj do słownika. Przychód zapiszesz osobno.</p>
          </div>
          <Button
            type="button"
            variant="secondary"
            disabled={pending}
            onClick={() => leave(onCancel)}
          >
            Anuluj
          </Button>
        </div>
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        <SelectField
          label="Rodzaj źródła"
          disabled={pending}
          value={kind}
          onChange={(event) => {
            const next = event.target.value;
            leave(() => {
              setKind(next);
              setDirty(false);
            });
          }}
        >
          <option value="other">Inne źródło</option>
          <option value="contract">Umowa</option>
        </SelectField>
        <div className="income-source-dialog-form">
          {kind === "other" ? (
            <OtherSourceForm
              compact
              suggestedMemberId={memberId}
              suggestedStartDate={suggestedStartDate}
              onPendingChange={updatePending}
              household={household}
              members={members}
              source={null}
              onSaved={(source) => onSaved(source.id, "other")}
              onConflict={() => setError("Źródło zmieniło się. Sprawdź słownik.")}
              refreshAccess={accessChanged}
            />
          ) : (
            <div id="contract-form">
              <ContractForm
                suggestedMemberId={memberId}
                suggestedStartDate={suggestedStartDate}
                onPendingChange={updatePending}
                household={household}
                members={members}
                companies={companies}
                contract={null}
                converting={null}
                suggestedCompanyId={company}
                onSaved={(saved) => onSaved(saved.id, "contract")}
                onAddCompany={() => setDialog(true)}
                onConflict={() => setError("Umowa zmieniła się. Sprawdź słownik.")}
                refreshAccess={accessChanged}
              />
            </div>
          )}
        </div>
      </div>
      {dialog && (
        <CompanyDialog
          onPendingChange={updatePending}
          household={household}
          refreshAccess={accessChanged}
          onClose={() => setDialog(false)}
          onCreated={(created) => {
            setCompanies((current) => [...current, created]);
            setCompany(created.id);
          }}
        />
      )}
    </dialog>
  );
}
