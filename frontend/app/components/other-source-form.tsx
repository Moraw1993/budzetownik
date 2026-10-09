"use client";
import { useState } from "react";
import {
  api,
  ApiError,
  householdPath,
  type Household,
  type HouseholdMember,
  type IncomeFrequency,
  type OtherIncomeSource,
} from "../lib/api";
import { normalizeDecimal } from "../lib/money";
import { ActionForm, Field, SelectField, TextAreaField } from "./ui";
export const frequencyLabels: Record<IncomeFrequency, string> = {
  monthly: "Miesięcznie",
  weekly: "Tygodniowo",
  quarterly: "Kwartalnie",
  yearly: "Rocznie",
  one_off: "Jednorazowo",
  irregular: "Nieregularnie",
};
export function OtherSourceForm({
  household,
  members,
  source,
  onSaved,
  onConflict,
  refreshAccess,
  onPendingChange,
}: {
  household: Household;
  members: HouseholdMember[];
  source: OtherIncomeSource | null;
  onSaved: (source: OtherIncomeSource) => void;
  onConflict: () => void;
  refreshAccess: () => void;
  onPendingChange?: (pending: boolean) => void;
}) {
  const [frequency, setFrequency] = useState<IncomeFrequency>(source?.frequency || "monthly");
  const activeMembers = members.filter((member) => member.is_active);
  const archivedOwner = members.find(
    (member) => member.id === source?.member_id && !member.is_active,
  );

  return (
    <ActionForm
      submit={source ? "Zapisz inne źródło" : "Dodaj inne źródło"}
      onPendingChange={onPendingChange}
      onDenied={refreshAccess}
      action={async (form) => {
        const amount = String(form.get("default_monthly_amount") ?? "").trim();
        const endDate = String(form.get("end_date") ?? "");
        let saved: OtherIncomeSource;
        try {
          saved = await api<OtherIncomeSource>(
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
        onSaved(saved);
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
