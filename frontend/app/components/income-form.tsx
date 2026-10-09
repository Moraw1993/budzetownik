"use client";
import { useEffect, useRef, useState } from "react";
import {
  api,
  apiAllPages,
  ApiError,
  householdPath,
  messageOf,
  type Contract,
  type HouseholdMember,
} from "../lib/api";
import { confirmedIncome } from "../lib/income-response";
import { formatMoney, normalizeDecimal } from "../lib/money";
import {
  canManage,
  incomePath,
  periodPath,
  sourceOptions,
  uncertain,
  validateFiles,
  type Income,
  type IncomeValues,
  type PeriodContext,
  type SourceOption,
} from "../lib/periods-api";
import { Button, Field, Panel, SelectField } from "./ui";
import { IncomeSourceCreate } from "./income-source-create";

export type EditGuard = { dirty: boolean; busy: boolean; unknown: boolean };
const emptyGuard: EditGuard = { dirty: false, busy: false, unknown: false };
function valuesOf(income: Income): IncomeValues {
  return {
    member_id: income.member_id,
    source_id: income.source_id,
    amount: income.amount,
    currency: income.currency,
    receipt_date: income.receipt_date,
  };
}
function patchValues(before: IncomeValues, after: IncomeValues) {
  return Object.fromEntries(
    Object.entries(after).filter(([key, value]) => before[key as keyof IncomeValues] !== value),
  );
}
function ConflictValues({
  title,
  values,
  recipient,
  source,
}: {
  title: string;
  values: IncomeValues;
  recipient: string;
  source: string;
}) {
  return (
    <Panel title={title}>
      <p>
        {recipient} · {source}
      </p>
      <p className="period-amount">{formatMoney(values.amount, values.currency)}</p>
      <p>Data otrzymania: {values.receipt_date}</p>
    </Panel>
  );
}

export function IncomeForm({
  context,
  initial,
  onSaved,
  onCancel,
  onGuard,
  onRecheck,
}: {
  context: PeriodContext;
  initial: Income | null;
  onSaved: (income: Income, files: File[]) => void;
  onCancel: () => void;
  onGuard: (guard: EditGuard) => void;
  onRecheck: () => void;
}) {
  const [baseline, setBaseline] = useState(initial);
  const [values, setValues] = useState<IncomeValues>(
    initial
      ? valuesOf(initial)
      : {
          member_id: null,
          source_id: "",
          amount: "",
          currency: context.household.currency,
          receipt_date: "",
        },
  );
  const [kind, setKind] = useState(initial && !initial.member_id ? "household" : "member");
  const [members, setMembers] = useState<HouseholdMember[] | null>(null);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [options, setOptions] = useState<SourceOption[] | null>(null);
  const [prerequisiteRevision, setPrerequisiteRevision] = useState(0);
  const [sourceRevision, setSourceRevision] = useState(0);
  const [createdSource, setCreatedSource] = useState("");
  const [sourcePending, setSourcePending] = useState(false);
  const [showSource, setShowSource] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [dirty, setDirty] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [fields, setFields] = useState<Record<string, string>>({});
  const [sourceError, setSourceError] = useState("");
  const [conflict, setConflict] = useState<Income | null>(null);
  const [mergeScratch, setMergeScratch] = useState<{
    values: IncomeValues;
    recipient: string;
    source: string;
  } | null>(null);
  const [attempt, setAttempt] = useState<{ key: string; body: IncomeValues } | null>(null);
  const [unknown, setUnknown] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const lock = useRef(false);
  const lifetime = useRef<AbortController | null>(null);
  const form = useRef<HTMLFormElement>(null);
  const active = context.month.state === "active";
  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    form.current?.querySelector<HTMLSelectElement>("select")?.focus();
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    apiAllPages<HouseholdMember>(householdPath(context.household.id, "members/"), controller.signal)
      .then((reply) => {
        if (!controller.signal.aborted) setMembers(reply);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setSourceError(messageOf(cause));
      });
    apiAllPages<Contract>(householdPath(context.household.id, "contracts/"), controller.signal)
      .then((reply) => {
        if (!controller.signal.aborted) setContracts(reply);
      })
      .catch(() => {
        /* Source options remain usable when optional contract detail is unavailable. */
      });
    return () => controller.abort();
  }, [context.household.id, prerequisiteRevision]);
  const memberId = values.member_id;
  const archivedMember =
    memberId && members?.some((member) => member.id === memberId && !member.is_active);
  useEffect(() => {
    if (!members || !active || (kind === "member" && !memberId) || archivedMember) return;
    const controller = new AbortController();
    sourceOptions(context, kind === "member" ? memberId : null, controller.signal)
      .then((reply) => {
        if (controller.signal.aborted) return;
        setOptions(reply);
        setSourceError("");
        if (createdSource) {
          if (reply.some((source) => source.id === createdSource))
            setValues((current) => ({ ...current, source_id: createdSource }));
          else
            setSourceError(
              "Źródło zapisane, ale nie jest dostępne dla tego odbiorcy i okresu. Sprawdź przypisanie i daty w słowniku.",
            );
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) {
          setSourceError(messageOf(cause));
          onRecheck();
        }
      });
    return () => controller.abort();
  }, [
    context,
    kind,
    memberId,
    members,
    archivedMember,
    sourceRevision,
    createdSource,
    active,
    onRecheck,
  ]);
  useEffect(() => {
    onGuard({ dirty: dirty || showSource, busy: pending || sourcePending, unknown });
    return () => onGuard(emptyGuard);
  }, [dirty, showSource, pending, sourcePending, unknown, onGuard]);
  useEffect(() => {
    if (!dirty && !unknown) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, unknown]);
  function change<K extends keyof IncomeValues>(key: K, value: IncomeValues[K]) {
    setValues((current) => ({ ...current, [key]: value }));
    setDirty(true);
    setFields({});
    setAttempt(null);
  }
  function recipient(nextKind: string, id: string | null = null) {
    setKind(nextKind);
    setValues((current) => ({ ...current, member_id: id, source_id: "" }));
    setOptions(null);
    setCreatedSource("");
    setSourceError("");
    setDirty(true);
    setAttempt(null);
  }
  async function save(retry = false) {
    if (lock.current || blocked || (!retry && (!active || conflict))) return;
    const signal = lifetime.current?.signal;
    lock.current = true;
    setPending(true);
    setError("");
    setFields({});
    const body = {
      ...values,
      member_id: kind === "household" ? null : values.member_id,
      amount: normalizeDecimal(values.amount),
      currency: values.currency.toUpperCase(),
    };
    const currentAttempt = retry ? attempt : { key: crypto.randomUUID(), body };
    try {
      if (!baseline && !currentAttempt) return;
      if (!baseline) setAttempt(currentAttempt);
      const patch = baseline ? patchValues(valuesOf(baseline), body) : null;
      if (patch && !Object.keys(patch).length)
        throw new ApiError(400, "Nie zmieniono danych przychodu.");
      const saved = baseline
        ? await api<Income>(incomePath(context, baseline.id), {
            method: "PATCH",
            data: { ...patch, expected_version: baseline.version },
            signal,
          })
        : await api<Income>(periodPath(context, "incomes/"), {
            method: "POST",
            data: currentAttempt!.body,
            headers: { "Idempotency-Key": currentAttempt!.key },
            expectedStatus: 201,
            signal,
          });
      confirmedIncome(saved, context);
      // Replay may describe a record removed after its original creation.
      const current = await api<Income>(incomePath(context, saved.id), { signal });
      if (signal?.aborted) return;
      confirmedIncome(current, context);
      setUnknown(false);
      setDirty(false);
      onGuard(emptyGuard);
      onSaved(current, files);
    } catch (cause) {
      if (signal?.aborted) return;
      setError(messageOf(cause));
      if (cause instanceof ApiError) {
        setFields(cause.fields);
        if (retry && (cause.status === 400 || cause.code === "income_period_not_active")) {
          setUnknown(false);
          setAttempt(null);
        }
        if ([401, 403, 404].includes(cause.status)) {
          setBlocked(true);
          setUnknown(false);
        }
        if (baseline && cause.status === 409 && cause.code === "income_version_conflict") {
          try {
            const current = await api<Income>(incomePath(context, baseline.id), { signal });
            if (!signal?.aborted) setConflict(current);
          } catch (readError) {
            if (!signal?.aborted) setError(messageOf(readError));
          }
        }
      }
      if (!baseline && uncertain(cause)) setUnknown(true);
      onRecheck();
    } finally {
      lock.current = false;
      if (!signal?.aborted) setPending(false);
    }
  }
  const selected = options?.find((source) => source.id === values.source_id);
  const contract = contracts.find((item) => item.id === values.source_id);
  const disabled =
    pending ||
    sourcePending ||
    unknown ||
    blocked ||
    !active ||
    !canManage(context.household) ||
    !!conflict;
  const sameHistoricRecipient =
    baseline &&
    baseline.member_id === values.member_id &&
    kind === (baseline.member_id ? "member" : "household");
  return (
    <div className="stack">
      {unknown && (
        <Panel
          title="Nie znamy wyniku zapisu"
          description="Dane poprzedniej próby są zachowane. Sprawdź i dokończ ją przed zmianą formularza; nie powstanie drugi przychód."
        >
          <Button type="button" disabled={pending || blocked} onClick={() => void save(true)}>
            {pending ? "Sprawdzanie poprzedniego zapisu…" : "Sprawdź i dokończ poprzedni zapis"}
          </Button>
        </Panel>
      )}
      {!active && (
        <p className="notice warning">
          Miesiąc nie jest aktywny. Szkic zachowano; zmiany wymagają ponownego otwarcia okresu.
        </p>
      )}
      {conflict && (
        <Panel
          title="Przychód został zmieniony"
          description="Porównaj dane. Kontynuacja rozpocznie edycję od aktualnego zapisu, a Twój szkic pozostanie poniżej do porównania."
        >
          <div className="period-summary">
            <ConflictValues
              title="Twój szkic"
              values={values}
              recipient={
                members?.find((member) => member.id === values.member_id)?.display_name ??
                (values.member_id
                  ? (baseline?.recipient_snapshot.label ?? "Osoba")
                  : context.household.name)
              }
              source={selected?.name ?? baseline?.source_snapshot.name ?? "Źródło"}
            />
            <ConflictValues
              title="Aktualny zapis"
              values={valuesOf(conflict)}
              recipient={conflict.recipient_snapshot.label}
              source={conflict.source_snapshot.name}
            />
          </div>
          <Button
            type="button"
            disabled={!active}
            onClick={() => {
              setMergeScratch({
                values: { ...values },
                recipient:
                  members?.find((member) => member.id === values.member_id)?.display_name ??
                  baseline?.recipient_snapshot.label ??
                  context.household.name,
                source: selected?.name ?? baseline?.source_snapshot.name ?? "Źródło",
              });
              setBaseline(conflict);
              setValues(valuesOf(conflict));
              setKind(conflict.member_id ? "member" : "household");
              setConflict(null);
              setError("");
              setDirty(true);
            }}
          >
            Rozpocznij ręczne scalanie
          </Button>
        </Panel>
      )}
      {mergeScratch && (
        <ConflictValues
          title="Zachowany szkic do ręcznego porównania"
          values={mergeScratch.values}
          recipient={mergeScratch.recipient}
          source={mergeScratch.source}
        />
      )}
      <Panel
        title={initial ? "Edytuj przychód" : "Dodaj przychód"}
        description="Jedno źródło na wpis. Podaj faktycznie otrzymaną kwotę; umowa nie tworzy przychodu."
        action={
          <Button
            type="button"
            variant="secondary"
            disabled={pending || sourcePending}
            onClick={onCancel}
          >
            Anuluj
          </Button>
        }
      >
        <form
          ref={form}
          aria-busy={pending}
          onSubmit={(event) => {
            event.preventDefault();
            void save();
          }}
        >
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
          {sourceError && (
            <p className="notice error" role="alert">
              {sourceError}
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setPrerequisiteRevision((value) => value + 1);
                  setSourceRevision((value) => value + 1);
                }}
              >
                Odśwież źródła
              </Button>
            </p>
          )}
          <fieldset disabled={disabled}>
            <div className="form-grid period-form-grid">
              <SelectField
                label="Typ odbiorcy"
                value={kind}
                onChange={(event) => recipient(event.target.value)}
              >
                <option value="member">Osoba</option>
                <option value="household">Całe gospodarstwo</option>
              </SelectField>
              {kind === "member" && (
                <SelectField
                  label="Osoba"
                  required
                  value={values.member_id ?? ""}
                  error={fields.member_id}
                  onChange={(event) => recipient("member", event.target.value || null)}
                >
                  <option value="">Wybierz osobę</option>
                  {members
                    ?.filter((member) => member.is_active)
                    .map((member) => (
                      <option key={member.id} value={member.id}>
                        {member.display_name}
                      </option>
                    ))}
                  {baseline?.member_id &&
                    !members?.some(
                      (member) => member.id === baseline.member_id && member.is_active,
                    ) && (
                      <option value={baseline.member_id}>
                        {baseline.recipient_snapshot.label} (historyczna)
                      </option>
                    )}
                </SelectField>
              )}
              <SelectField
                label="Źródło dochodu"
                required
                value={values.source_id}
                error={fields.source_id}
                onChange={(event) => {
                  if (event.target.value === "__create_source__") setShowSource(true);
                  else change("source_id", event.target.value);
                }}
              >
                <option value="">
                  {kind === "member" && !values.member_id
                    ? "Najpierw wybierz osobę"
                    : options === null && !archivedMember
                      ? "Pobieranie źródeł…"
                      : "Wybierz źródło"}
                </option>
                {options?.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                    {source.contract ? " · " + source.contract.company_name : ""}
                  </option>
                ))}
                {canManage(context.household) && (
                  <option value="__create_source__">+ Dodaj nowe źródło…</option>
                )}
                {sameHistoricRecipient &&
                  !options?.some((source) => source.id === baseline.source_id) && (
                    <option value={baseline.source_id}>
                      {baseline.source_snapshot.name} (historyczne)
                    </option>
                  )}
              </SelectField>
              <Field
                label="Faktyczna kwota przychodu"
                name="amount"
                required
                inputMode="decimal"
                pattern="[0-9]+([.,][0-9]{1,2})?"
                value={values.amount}
                error={fields.amount}
                onChange={(event) => change("amount", event.target.value)}
              />
              <Field
                label="Waluta"
                required
                pattern="[A-Za-z]{3}"
                maxLength={3}
                value={values.currency}
                error={fields.currency}
                onChange={(event) => change("currency", event.target.value.toUpperCase())}
              />
              <Field
                label="Data otrzymania"
                required
                type="date"
                value={values.receipt_date}
                error={fields.receipt_date}
                onChange={(event) => change("receipt_date", event.target.value)}
              />
            </div>
            {selected?.contract && (
              <p className="notice">
                {selected.name} · {selected.contract.company_name}
                {contract
                  ? " · brutto: " + formatMoney(contract.gross_amount, contract.currency)
                  : ""}
                . To informacja o umowie, nie faktyczna kwota przychodu.
              </p>
            )}
            <p className="hint">
              Data otrzymania może być poza wybranym miesiącem lub rokiem rozliczeniowym.
            </p>
            <Field
              label="Opcjonalne załączniki (PNG, JPG, PDF)"
              type="file"
              multiple
              accept=".png,.jpg,.jpeg,.pdf"
              onChange={(event) => {
                const selectedFiles = Array.from(event.target.files ?? []);
                const issue = selectedFiles.length ? validateFiles(selectedFiles) : "";
                if (issue) {
                  setError(issue);
                  event.target.value = "";
                  return;
                }
                setFiles(selectedFiles);
                setDirty(true);
              }}
            />
            {!!files.length && (
              <ul>
                {files.map((file, index) => (
                  <li className="period-file-name" key={index}>
                    {file.name} · oczekuje na zapis
                  </li>
                ))}
              </ul>
            )}
            <p className="hint">
              Do 5 plików, 10 MiB na plik i 25 MiB na partię. Pliki dodamy po zapisaniu przychodu.
            </p>
            <Button type="submit" disabled={disabled || showSource}>
              {pending
                ? "Trwa zapisywanie…"
                : initial
                  ? "Zapisz zmiany przychodu"
                  : "Zapisz przychód"}
            </Button>
          </fieldset>
        </form>
      </Panel>
      {showSource && members && (
        <IncomeSourceCreate
          onPendingChange={setSourcePending}
          household={context.household}
          suggestedStartDate={context.month.month_start}
          refreshAccess={onRecheck}
          members={members}
          memberId={values.member_id}
          onCancel={() => setShowSource(false)}
          onSaved={(id) => {
            setShowSource(false);
            setCreatedSource(id);
            setSourceRevision((value) => value + 1);
            setDirty(true);
          }}
        />
      )}
    </div>
  );
}
