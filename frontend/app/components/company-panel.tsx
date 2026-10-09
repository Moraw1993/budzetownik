"use client";

import { useEffect, useState } from "react";
import { api, householdPath, type Company, type Household } from "../lib/api";
import { ActionForm, Button, Field, Panel } from "./ui";

export function CompanyCreateForm({
  onPendingChange,
  household,
  onCreated,
  refreshAccess,
}: {
  onPendingChange?: (pending: boolean) => void;
  household: Household;
  onCreated: (company: Company) => void;
  refreshAccess: () => void;
}) {
  return (
    <ActionForm
      onPendingChange={onPendingChange}
      submit="Dodaj firmę"
      onDenied={refreshAccess}
      action={async (form) => {
        const company = await api<Company>(householdPath(household.id, "companies/"), {
          method: "POST",
          data: { name: form.get("name") },
        });
        onCreated(company);
      }}
    >
      {(fields) => (
        <Field label="Nazwa firmy" name="name" required maxLength={180} error={fields.name} />
      )}
    </ActionForm>
  );
}

export function CompanyPanel({
  household,
  companies,
  onCreated,
  onChanged,
  refreshAccess,
}: {
  household: Household;
  companies: Company[];
  onCreated: (company: Company) => void;
  onChanged: () => void;
  refreshAccess: () => void;
}) {
  const [editing, setEditing] = useState<Company | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formRevision, setFormRevision] = useState(0);
  const [notice, setNotice] = useState("");
  const canEdit = household.role === "owner" || household.role === "administrator";

  useEffect(() => {
    if (showForm)
      document.querySelector<HTMLInputElement>('#company-dictionary input[name="name"]')?.focus();
  }, [showForm, editing]);

  function saved(message: string) {
    setEditing(null);
    setShowForm(false);
    setFormRevision((value) => value + 1);
    setNotice(message);
    onChanged();
  }

  return (
    <div id="company-dictionary" className="stack">
      {notice && (
        <p className="notice success" role="status">
          ✓ {notice}
        </p>
      )}
      <Panel
        title="Lista firm"
        description="Słownik firm wybranego gospodarstwa."
        action={
          canEdit && !showForm ? (
            <Button
              type="button"
              onClick={() => {
                setEditing(null);
                setShowForm(true);
              }}
            >
              Dodaj firmę
            </Button>
          ) : undefined
        }
      >
        {!companies.length ? (
          <p className="empty">Brak firm. Dodaj pierwszą firmę, aby utworzyć umowę.</p>
        ) : (
          <div className="table-scroll" role="region" aria-label="Firmy — tabela" tabIndex={0}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Firma</th>
                  <th scope="col">Status</th>
                  {canEdit && <th scope="col">Akcje</th>}
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={company.id}>
                    <th scope="row">{company.name}</th>
                    <td>{company.is_active ? "Aktywna" : "Archiwalna"}</td>
                    {canEdit && (
                      <td>
                        {company.is_active ? (
                          <div className="row-actions">
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() => {
                                setEditing(company);
                                setShowForm(true);
                                setNotice("");
                              }}
                            >
                              Edytuj
                            </Button>
                            <ActionForm
                              submit="Archiwizuj"
                              submitVariant="danger"
                              onDenied={refreshAccess}
                              action={async () => {
                                if (!window.confirm(`Archiwizować firmę ${company.name}?`)) return;
                                await api(
                                  householdPath(household.id, `companies/${company.id}/archive/`),
                                  { method: "POST", data: {} },
                                );
                                saved("Firma została zarchiwizowana.");
                              }}
                            >
                              {() => null}
                            </ActionForm>
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
        )}
      </Panel>
      {canEdit && showForm && (
        <Panel
          title={editing ? `Edycja firmy: ${editing.name}` : "Dodaj firmę"}
          description="Wymagana jest tylko nazwa."
          className="panel-compact-form"
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
          {editing ? (
            <ActionForm
              key={`${editing.id}-${formRevision}`}
              submit="Zapisz firmę"
              onDenied={refreshAccess}
              action={async (form) => {
                await api<Company>(householdPath(household.id, `companies/${editing.id}/`), {
                  method: "PATCH",
                  data: { name: form.get("name") },
                });
                saved("Zapisano nazwę firmy.");
              }}
            >
              {(fields) => (
                <Field
                  label="Nazwa firmy"
                  name="name"
                  required
                  maxLength={180}
                  defaultValue={editing.name}
                  error={fields.name}
                />
              )}
            </ActionForm>
          ) : (
            <CompanyCreateForm
              key={`new-${formRevision}`}
              household={household}
              refreshAccess={refreshAccess}
              onCreated={(company) => {
                onCreated(company);
                saved("Dodano firmę.");
              }}
            />
          )}
        </Panel>
      )}
    </div>
  );
}
