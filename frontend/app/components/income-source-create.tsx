"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  apiAllPages,
  householdPath,
  messageOf,
  type Company,
  type HouseholdMember,
} from "../lib/api";
import { type PeriodContext } from "../lib/periods-api";
import { ContractForm } from "./contract-form";
import { OtherSourceForm } from "./other-source-form";
import { CompanyDialog } from "./company-dialog";
import { ConfirmAction } from "./periods-common";
import { Button, Panel, SelectField } from "./ui";

export function IncomeSourceCreate({
  context,
  members,
  onSaved,
  onCancel,
  onPendingChange,
}: {
  context: PeriodContext;
  members: HouseholdMember[];
  onSaved: (id: string) => void;
  onCancel: () => void;
  onPendingChange: (pending: boolean) => void;
}) {
  const [pending, setPending] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [discard, setDiscard] = useState<{ run: () => void } | null>(null);
  const updatePending = useCallback(
    (value: boolean) => {
      setPending(value);
      onPendingChange(value);
    },
    [onPendingChange],
  );
  const [kind, setKind] = useState("other");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [company, setCompany] = useState("");
  const [dialog, setDialog] = useState(false);
  const [error, setError] = useState("");
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLElement | null>(null);
  useEffect(() => {
    trigger.current = document.activeElement as HTMLElement | null;
    root.current?.querySelector<HTMLSelectElement>("select")?.focus();
    root.current?.scrollIntoView({ block: "nearest" });
    return () => {
      if (trigger.current?.isConnected) trigger.current.focus();
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    apiAllPages<Company>(householdPath(context.household.id, "companies/"), controller.signal)
      .then((reply) => {
        if (!controller.signal.aborted) setCompanies(reply);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [context.household.id]);
  function leave(run: () => void) {
    if (pending) return;
    if (dirty) setDiscard({ run });
    else run();
  }
  return (
    <div
      ref={root}
      onChangeCapture={() => setDirty(true)}
      onKeyDown={(event) => {
        if (event.key === "Escape" && !dialog && !discard) {
          event.stopPropagation();
          leave(onCancel);
        }
      }}
    >
      {discard && (
        <ConfirmAction
          variant="danger"
          title="Odrzucić szkic źródła?"
          description="Niezapisane dane źródła zostaną usunięte. Szkic przychodu pozostanie."
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
      <Panel
        title="Dodaj źródło do słownika"
        description="Zapis źródła nie dodaje przychodu. Dane przychodu pozostają w formularzu."
        action={
          <Button
            type="button"
            variant="secondary"
            disabled={pending}
            onClick={() => leave(onCancel)}
          >
            Anuluj dodawanie źródła
          </Button>
        }
      >
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
            leave(() => setKind(next));
          }}
        >
          <option value="other">Inne źródło</option>
          <option value="contract">Umowa</option>
        </SelectField>
        {kind === "other" ? (
          <OtherSourceForm
            onPendingChange={updatePending}
            household={context.household}
            members={members}
            source={null}
            onSaved={(source) => onSaved(source.id)}
            onConflict={() => setError("Źródło zmieniło się. Sprawdź słownik.")}
            refreshAccess={() => setError("Dostęp zmienił się. Odśwież aplikację.")}
          />
        ) : (
          <div id="contract-form">
            <ContractForm
              onPendingChange={updatePending}
              household={context.household}
              members={members}
              companies={companies}
              contract={null}
              converting={null}
              suggestedCompanyId={company}
              onSaved={(saved) => onSaved(saved.id)}
              onAddCompany={() => setDialog(true)}
              onConflict={() => setError("Umowa zmieniła się. Sprawdź słownik.")}
              refreshAccess={() => setError("Dostęp zmienił się. Odśwież aplikację.")}
            />
          </div>
        )}
        {dialog && (
          <CompanyDialog
            onPendingChange={updatePending}
            household={context.household}
            refreshAccess={() => setError("Dostęp zmienił się. Odśwież aplikację.")}
            onClose={() => setDialog(false)}
            onCreated={(created) => {
              setCompanies((current) => [...current, created]);
              setCompany(created.id);
            }}
          />
        )}
      </Panel>
    </div>
  );
}
