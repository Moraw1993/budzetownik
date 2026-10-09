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
  compact = false,
  suggestedMemberId,
  suggestedStartDate,
}: {
  household: Household;
  members: HouseholdMember[];
  source: OtherIncomeSource | null;
  onSaved: (source: OtherIncomeSource) => void;
  onConflict: () => void;
  refreshAccess: () => void;
  onPendingChange?: (pending: boolean) => void;
  compact?: boolean;
  suggestedMemberId?: string | null;
  suggestedStartDate?: string;
}) {
  const [frequency, setFrequency] = useState<IncomeFrequency>(source?.frequency || "monthly");

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
        <OtherSourceFields
          fields={fields}
          household={household}
          members={members}
          source={source}
          compact={compact}
          suggestedMemberId={suggestedMemberId}
          suggestedStartDate={suggestedStartDate}
          frequency={frequency}
          onFrequencyChange={setFrequency}
        />
      )}
    </ActionForm>
  );
}
function OtherSourceFields({
  fields,
  household,
  members,
  source,
  compact,
  suggestedMemberId,
  suggestedStartDate,
  frequency,
  onFrequencyChange,
}: {
  fields: Record<string, string>;
  household: Household;
  members: HouseholdMember[];
  source: OtherIncomeSource | null;
  compact: boolean;
  suggestedMemberId?: string | null;
  suggestedStartDate?: string;
  frequency: IncomeFrequency;
  onFrequencyChange: (value: IncomeFrequency) => void;
}) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const activeMembers = members.filter((member) => member.is_active);
  const archivedOwner = members.find(
    (member) => member.id === source?.member_id && !member.is_active,
  );
  const hiddenError = [
    "payer",
    "end_date",
    "default_monthly_amount",
    "description",
    "is_regular",
  ].some((name) => !!fields[name]);
  const member_idField = (
    <SelectField
      label="Przypisz źródło do"
      name="member_id"
      defaultValue={source?.member_id ?? suggestedMemberId ?? ""}
      error={fields.member_id}
    >
      <option value="">Całe gospodarstwo</option>
      {activeMembers.map((member) => (
        <option key={member.id} value={member.id}>
          {member.display_name}
        </option>
      ))}
      {archivedOwner && (
        <option value={archivedOwner.id}>{archivedOwner.display_name} (archiwalna)</option>
      )}
    </SelectField>
  );
  const nameField = (
    <Field
      label="Nazwa innego źródła"
      name="name"
      required
      maxLength={180}
      defaultValue={source?.name}
      error={fields.name}
    />
  );
  const categoryField = (
    <Field
      label="Kategoria"
      name="category"
      required
      maxLength={100}
      defaultValue={source?.category}
      error={fields.category}
    />
  );
  const payerField = (
    <Field
      label="Płatnik"
      name="payer"
      maxLength={180}
      defaultValue={source?.payer}
      error={fields.payer}
    />
  );
  const frequencyField = (
    <SelectField
      label="Częstotliwość"
      name="frequency"
      required
      value={frequency}
      onChange={(event) => onFrequencyChange(event.target.value as IncomeFrequency)}
      error={fields.frequency}
    >
      {Object.entries(frequencyLabels).map(([value, label]) => (
        <option key={value} value={value}>
          {label}
        </option>
      ))}
    </SelectField>
  );
  const start_dateField = (
    <Field
      label="Data rozpoczęcia"
      name="start_date"
      type="date"
      required
      defaultValue={source?.start_date ?? suggestedStartDate}
      error={fields.start_date}
    />
  );
  const end_dateField = (
    <Field
      label="Data zakończenia"
      name="end_date"
      type="date"
      defaultValue={source?.end_date ?? ""}
      error={fields.end_date}
    />
  );
  const default_monthly_amountField = (
    <Field
      label="Opcjonalna podpowiedź miesięczna"
      name="default_monthly_amount"
      inputMode="decimal"
      pattern="[0-9]+([.,][0-9]{1,2})?"
      defaultValue={source?.default_monthly_amount ?? ""}
      error={fields.default_monthly_amount}
      placeholder="Może pozostać puste"
    />
  );
  const currencyField = (
    <Field
      label="Waluta"
      name="currency"
      required
      pattern="[A-Za-z]{3}"
      maxLength={3}
      defaultValue={source?.currency ?? household.currency}
      error={fields.currency}
    />
  );
  const descriptionField = (
    <TextAreaField
      label="Opis"
      name="description"
      rows={3}
      maxLength={2000}
      defaultValue={source?.description}
      error={fields.description}
    />
  );
  const regularField = (
    <>
      <label className="check-field">
        <input
          type="checkbox"
          name="is_regular"
          defaultChecked={source?.is_regular ?? true}
          disabled={frequency === "one_off"}
        />
        Źródło regularne
      </label>
      {frequency === "one_off" && <p className="hint">Źródło jednorazowe nie jest regularne.</p>}
      {fields.is_regular && <span className="field-error">{fields.is_regular}</span>}
    </>
  );
  return compact ? (
    <div
      onInvalidCapture={(event) => {
        if ((event.target as HTMLElement).closest("details")) setDetailsOpen(true);
      }}
    >
      <div className="form-grid">
        {member_idField}
        {nameField}
        {categoryField}
        {frequencyField}
        {start_dateField}
        {currencyField}
      </div>
      <details
        open={detailsOpen || hiddenError}
        onToggle={(event) => setDetailsOpen(event.currentTarget.open)}
      >
        <summary>Dodatkowe informacje</summary>
        <div className="form-grid">
          {payerField}
          {end_dateField}
          {default_monthly_amountField}
        </div>
        {regularField}
        {descriptionField}
      </details>
    </div>
  ) : (
    <>
      <div className="form-section">
        <h3>Informacje podstawowe</h3>
        <div className="form-grid">
          {member_idField}
          {nameField}
          {categoryField}
          {payerField}
        </div>
      </div>
      <div className="form-section">
        <h3>Okres</h3>
        <div className="form-grid">
          {frequencyField}
          {start_dateField}
          {end_dateField}
        </div>
        {regularField}
      </div>
      <div className="form-section">
        <h3>Kwota</h3>
        <div className="form-grid">
          {default_monthly_amountField}
          {currencyField}
        </div>
      </div>
      <div className="form-section">
        <h3>Dodatkowe informacje</h3>
        {descriptionField}
      </div>
    </>
  );
}
