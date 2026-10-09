"use client";

import { useEffect, useState } from "react";
import {
  api,
  householdPath,
  type Household,
  type HouseholdMember,
  type IncomeSource,
  type OtherIncomeSource,
} from "../lib/api";
import { formatMoney } from "../lib/money";
import { ActionForm, Button, Panel } from "./ui";

import { OtherSourceForm, frequencyLabels } from "./other-source-form";

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
