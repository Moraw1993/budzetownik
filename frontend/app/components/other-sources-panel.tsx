"use client";

import { useEffect, useState } from "react";
import {
  api,
  ApiError,
  householdPath,
  type Household,
  type HouseholdMember,
  type IncomeFrequency,
  type IncomeSource,
  type OtherIncomeSource,
} from "../lib/api";
import { formatMoney, normalizeDecimal } from "../lib/money";
import { ActionForm, Button, Field, Panel, SelectField, TextAreaField } from "./ui";

const frequencyLabels: Record<IncomeFrequency, string> = {
  monthly: "Miesięcznie",
  weekly: "Tygodniowo",
  quarterly: "Kwartalnie",
  yearly: "Rocznie",
  one_off: "Jednorazowo",
  irregular: "Nieregularnie",
};

function OtherSourceForm({
  household,
  members,
  source,
  onSaved,
  onConflict,
  refreshAccess,
}: {
  household: Household;
  members: HouseholdMember[];
  source: OtherIncomeSource | null;
  onSaved: () => void;
  onConflict: () => void;
  refreshAccess: () => void;
}) {
  const [frequency, setFrequency] = useState<IncomeFrequency>(source?.frequency || "monthly");
  const activeMembers = members.filter((member) => member.is_active);
  const archivedOwner = members.find(
    (member) => member.id === source?.member_id && !member.is_active,
  );

  return (
    <ActionForm
      submit={source ? "Zapisz inne źródło" : "Dodaj inne źródło"}
      onDenied={refreshAccess}
      action={async (form) => {
        const amount = String(form.get("default_monthly_amount") ?? "").trim();
        const endDate = String(form.get("end_date") ?? "");
        try {
          await api(
            householdPath(
              household.id,
              source ? `income-sources/${source.id}/` : "income-sources/",
            ),
            {
              method: source ? "PATCH" : "POST",
              data: {
                ...(source ? { expected_version: source.version } : {}),
                member_id: String(form.get("member_id") ?? "") || null,
                name: String(form.get("name") ?? ""),
                category: String(form.get("category") ?? ""),
                payer: String(form.get("payer") ?? ""),
                start_date: String(form.get("start_date") ?? ""),
                end_date: endDate || null,
                default_monthly_amount: amount ? normalizeDecimal(amount) : null,
                currency: String(form.get("currency") ?? "").toUpperCase(),
                frequency,
                is_regular: frequency !== "one_off" && form.has("is_regular"),
                description: String(form.get("description") ?? ""),
              },
            },
          );
        } catch (cause) {
          if (cause instanceof ApiError && cause.status === 409) onConflict();
          throw cause;
        }
        onSaved();
      }}
    >
      {(fields) => (
        <>
          <div className="form-section">
            <h3>Informacje podstawowe</h3>
            <div className="form-grid">
              <SelectField
                label="Przypisz źródło do"
                name="member_id"
                defaultValue={source?.member_id ?? ""}
                error={fields.member_id}
              >
                <option value="">Całe gospodarstwo</option>
                {activeMembers.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.display_name}
                  </option>
                ))}
                {archivedOwner && (
                  <option value={archivedOwner.id}>
                    {archivedOwner.display_name} (archiwalna)
                  </option>
                )}
              </SelectField>
              <Field
                label="Nazwa innego źródła"
                name="name"
                required
                maxLength={180}
                defaultValue={source?.name}
                error={fields.name}
              />
              <Field
                label="Kategoria"
                name="category"
                required
                maxLength={100}
                defaultValue={source?.category}
                error={fields.category}
              />
              <Field
                label="Płatnik"
                name="payer"
                maxLength={180}
                defaultValue={source?.payer}
                error={fields.payer}
              />
            </div>
          </div>
          <div className="form-section">
            <h3>Okres</h3>
            <div className="form-grid">
              <SelectField
                label="Częstotliwość"
                name="frequency"
                required
                value={frequency}
                onChange={(event) => setFrequency(event.target.value as IncomeFrequency)}
                error={fields.frequency}
              >
                {Object.entries(frequencyLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </SelectField>
              <Field
                label="Data rozpoczęcia"
                name="start_date"
                type="date"
                required
                defaultValue={source?.start_date}
                error={fields.start_date}
              />
              <Field
                label="Data zakończenia"
                name="end_date"
                type="date"
                defaultValue={source?.end_date ?? ""}
                error={fields.end_date}
              />
            </div>
            <label className="check-field">
              <input
                type="checkbox"
                name="is_regular"
                defaultChecked={source?.is_regular ?? true}
                disabled={frequency === "one_off"}
              />
              Źródło regularne
            </label>
            {frequency === "one_off" && (
              <p className="hint">Źródło jednorazowe nie jest regularne.</p>
            )}
            {fields.is_regular && <span className="field-error">{fields.is_regular}</span>}
          </div>
          <div className="form-section">
            <h3>Kwota</h3>
            <div className="form-grid">
              <Field
                label="Opcjonalna podpowiedź miesięczna"
                name="default_monthly_amount"
                inputMode="decimal"
                pattern="[0-9]+([.,][0-9]{1,2})?"
                defaultValue={source?.default_monthly_amount ?? ""}
                error={fields.default_monthly_amount}
                placeholder="Może pozostać puste"
              />
              <Field
                label="Waluta"
                name="currency"
                required
                pattern="[A-Za-z]{3}"
                maxLength={3}
                defaultValue={source?.currency ?? household.currency}
                error={fields.currency}
              />
            </div>
          </div>
          <div className="form-section">
            <h3>Dodatkowe informacje</h3>
            <TextAreaField
              label="Opis"
              name="description"
              rows={3}
              maxLength={2000}
              defaultValue={source?.description}
              error={fields.description}
            />
          </div>
        </>
      )}
    </ActionForm>
  );
}

function SourceTable({
  title,
  sources,
  members,
  canEdit,
  onEdit,
  onConvert,
}: {
  title: string;
  sources: OtherIncomeSource[];
  members: HouseholdMember[];
  canEdit: boolean;
  onEdit: (source: OtherIncomeSource) => void;
  onConvert: (source: IncomeSource) => void;
}) {
  if (!sources.length)
    return (
      <section className="source-empty" aria-label={title}>
        <h3>{title}</h3>
        <p>Brak innych źródeł w tej części gospodarstwa.</p>
      </section>
    );

  return (
    <Panel title={title}>
      <div className="table-scroll" role="region" aria-label={`${title} — tabela`} tabIndex={0}>
        <table className="income-table">
          <thead>
            <tr>
              <th scope="col">Źródło</th>
              <th scope="col">Przypisanie</th>
              <th scope="col">Podpowiedź miesięczna</th>
              <th scope="col">Okres</th>
              <th scope="col">Status</th>
              {canEdit && <th scope="col">Akcje</th>}
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.id}>
                <th scope="row">
                  {source.name}
                  <span className="table-detail">{source.category}</span>
                </th>
                <td>
                  {members.find((member) => member.id === source.member_id)?.display_name ??
                    (source.member_id ? "Osoba niedostępna" : "Całe gospodarstwo")}
                </td>
                <td className="money">
                  {source.default_monthly_amount
                    ? formatMoney(source.default_monthly_amount, source.currency)
                    : "Brak podpowiedzi"}
                  <span className="table-detail">
                    {source.frequency ? frequencyLabels[source.frequency] : "—"}
                  </span>
                </td>
                <td>
                  {source.start_date}
                  <span className="table-detail">
                    {source.end_date ? `do ${source.end_date}` : "bez daty końcowej"}
                  </span>
                </td>
                <td>{source.is_active ? "Aktywne" : "Archiwalne"}</td>
                {canEdit && (
                  <td>
                    {source.is_active ? (
                      <div className="row-actions">
                        <Button type="button" variant="secondary" onClick={() => onEdit(source)}>
                          Edytuj
                        </Button>
                        <Button type="button" variant="secondary" onClick={() => onConvert(source)}>
                          Przekształć w umowę
                        </Button>
                      </div>
                    ) : (
                      <span className="muted">Brak dostępnych akcji</span>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

export function OtherSourcesPanel({
  household,
  members,
  sources,
  reloadSources,
  onConvert,
  refreshAccess,
}: {
  household: Household;
  members: HouseholdMember[];
  sources: IncomeSource[];
  reloadSources: () => void;
  onConvert: (source: IncomeSource) => void;
  refreshAccess: () => void;
}) {
  const [editing, setEditing] = useState<OtherIncomeSource | null>(null);
  const [formRevision, setFormRevision] = useState(0);
  const [notice, setNotice] = useState("");
  const [conflict, setConflict] = useState("");
  const [showForm, setShowForm] = useState(false);
  const canEdit = household.role === "owner" || household.role === "administrator";
  const others = sources.filter((source) => source.kind === "other");

  useEffect(() => {
    if (showForm)
      document
        .querySelector<HTMLSelectElement>('#other-source-form select[name="member_id"]')
        ?.focus();
  }, [showForm, editing]);

  function saved() {
    setEditing(null);
    setShowForm(false);
    setFormRevision((value) => value + 1);
    setNotice("Zapisano zmianę innego źródła.");
    setConflict("");
    reloadSources();
  }

  function edit(source: OtherIncomeSource) {
    setEditing(source);
    setShowForm(true);
    setNotice("");
    setConflict("");
  }

  return (
    <div className="stack">
      <div className="family-section-heading">
        <div>
          <h2>Źródła dochodu</h2>
          <p className="muted">
            Inne źródła osób i całego gospodarstwa. Podpowiedź miesięczna nie jest przychodem
            miesiąca.
          </p>
        </div>
        {canEdit && !showForm && (
          <Button
            type="button"
            aria-controls="other-source-form"
            onClick={() => {
              setEditing(null);
              setShowForm(true);
              setNotice("");
              setConflict("");
            }}
          >
            Dodaj źródło
          </Button>
        )}
      </div>
      {notice && (
        <p className="notice success" role="status">
          ✓ {notice}
        </p>
      )}
      {conflict && (
        <p className="notice error" role="alert">
          {conflict}
        </p>
      )}
      {!showForm && (
        <>
          <SourceTable
            title="Inne źródła osób"
            sources={others.filter((source) => source.member_id !== null)}
            members={members}
            canEdit={canEdit}
            onEdit={edit}
            onConvert={onConvert}
          />
          <SourceTable
            title="Źródła całego gospodarstwa"
            sources={others.filter((source) => source.member_id === null)}
            members={members}
            canEdit={canEdit}
            onEdit={edit}
            onConvert={onConvert}
          />
        </>
      )}
      {canEdit && showForm && (
        <div id="other-source-form">
          <Panel
            title={editing ? `Edycja: ${editing.name}` : "Dodaj inne źródło dochodu"}
            description="Podpowiedź miesięczna jest opcjonalna i nie tworzy przychodu miesiąca."
            className="panel-wide-form"
            action={
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setEditing(null);
                  setShowForm(false);
                }}
              >
                Anuluj
              </Button>
            }
          >
            <OtherSourceForm
              key={`${editing?.id ?? "new"}-${formRevision}`}
              household={household}
              members={members}
              source={editing}
              onSaved={saved}
              onConflict={() => {
                setEditing(null);
                setShowForm(false);
                setFormRevision((value) => value + 1);
                setConflict(
                  "Źródło zostało zmienione. Wczytano aktualne dane; wybierz je ponownie.",
                );
                reloadSources();
              }}
              refreshAccess={refreshAccess}
            />
            {editing && (
              <div className="member-danger-action">
                <ActionForm
                  submit="Archiwizuj źródło"
                  submitVariant="danger"
                  onDenied={refreshAccess}
                  action={async () => {
                    if (!window.confirm(`Archiwizować źródło ${editing.name}?`)) return;
                    await api(
                      householdPath(household.id, `income-sources/${editing.id}/deactivate/`),
                      {
                        method: "POST",
                        data: {},
                      },
                    );
                    saved();
                  }}
                >
                  {() => null}
                </ActionForm>
              </div>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
}
