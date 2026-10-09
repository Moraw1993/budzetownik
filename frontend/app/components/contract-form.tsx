"use client";

import { useState } from "react";
import {
  api,
  ApiError,
  householdPath,
  type Company,
  type Contract,
  type ContractType,
  type Household,
  type HouseholdMember,
  type IncomeSource,
} from "../lib/api";
import { formatMoney, normalizeDecimal } from "../lib/money";
import { ActionForm, Button, Field, SelectField } from "./ui";

const contractTypeLabels: Record<ContractType, string> = {
  employment: "Umowa o pracę",
  mandate: "Umowa zlecenie",
  specific_work: "Umowa o dzieło",
  other: "Inna umowa",
};

export function ContractForm({
  household,
  members,
  companies,
  contract,
  converting,
  suggestedCompanyId,
  onAddCompany,
  onSaved,
  onConflict,
  refreshAccess,
  onPendingChange,
}: {
  household: Household;
  members: HouseholdMember[];
  companies: Company[];
  contract: Contract | null;
  converting: IncomeSource | null;
  suggestedCompanyId: string;
  onAddCompany: () => void;
  onSaved: (contract: Contract) => void;
  onConflict: () => void;
  refreshAccess: () => void;
  onPendingChange?: (pending: boolean) => void;
}) {
  const [contractType, setContractType] = useState<ContractType>(
    contract?.contract_type ?? "employment",
  );
  const activeMembers = members.filter((member) => member.is_active);
  const selectedMember = contract?.member_id ?? converting?.member_id;
  const archivedMember = members.find(
    (member) => member.id === selectedMember && !member.is_active,
  );
  const activeCompanies = companies.filter((company) => company.is_active);
  const archivedCompany = contract?.company.is_active ? null : contract?.company;
  const companyId = suggestedCompanyId || contract?.company.id || "";
  const isConversion = !!converting;

  return (
    <div className="stack">
      {converting && (
        <p className="notice warning" role="status">
          Przekształcasz „{converting.name}” w umowę. Identyfikator źródła zostanie zachowany.
          {converting.default_monthly_amount && (
            <>
              {" "}
              Dawna podpowiedź:{" "}
              {formatMoney(converting.default_monthly_amount, converting.currency)}.
            </>
          )}{" "}
          Ta operacja nie doda przychodu za miesiąc.
        </p>
      )}
      <ActionForm
        submit={isConversion ? "Przekształć w umowę" : contract ? "Zapisz umowę" : "Dodaj umowę"}
        onPendingChange={onPendingChange}
        onDenied={refreshAccess}
        action={async (form) => {
          const endDate = String(form.get("end_date") ?? "");
          const path = converting
            ? `income-sources/${converting.id}/convert-to-contract/`
            : contract
              ? `contracts/${contract.id}/`
              : "contracts/";
          const payload = {
            member_id: String(form.get("member_id") ?? ""),
            company_id: String(form.get("company_id") ?? ""),
            name: String(form.get("name") ?? ""),
            contract_type: contractType,
            other_type_name:
              contractType === "other" ? String(form.get("other_type_name") ?? "") : "",
            position:
              contractType === "employment" || contractType === "mandate"
                ? String(form.get("position") ?? "")
                : "",
            gross_amount: normalizeDecimal(String(form.get("gross_amount") ?? "")),
            gross_basis: String(form.get("gross_basis") ?? ""),
            currency: String(form.get("currency") ?? "").toUpperCase(),
            start_date: String(form.get("start_date") ?? ""),
            end_date: endDate || null,
            ...(converting || contract
              ? { expected_version: converting?.version ?? contract?.version }
              : {}),
          };
          let saved: Contract;
          try {
            saved = await api<Contract>(householdPath(household.id, path), {
              method: contract && !converting ? "PATCH" : "POST",
              data: payload,
            });
          } catch (cause) {
            if (cause instanceof ApiError && cause.status === 409) onConflict();
            throw cause;
          }
          onSaved(saved);
        }}
      >
        {(fields) => (
          <>
            <div className="form-grid">
              <SelectField
                label="Osoba umowy"
                name="member_id"
                required
                defaultValue={selectedMember ?? ""}
                error={fields.member_id}
              >
                <option value="">Wybierz osobę</option>
                {activeMembers.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.display_name}
                  </option>
                ))}
                {archivedMember && (
                  <option value={archivedMember.id}>
                    {archivedMember.display_name} (archiwalna)
                  </option>
                )}
              </SelectField>
              <div className="company-select-field">
                <SelectField
                  key={suggestedCompanyId}
                  label="Firma"
                  name="company_id"
                  required
                  defaultValue={companyId}
                  error={fields.company_id}
                >
                  <option value="">Wybierz firmę</option>
                  {activeCompanies.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))}
                  {archivedCompany && (
                    <option value={archivedCompany.id}>{archivedCompany.name} (archiwalna)</option>
                  )}
                </SelectField>
                <Button type="button" variant="secondary" onClick={onAddCompany}>
                  + Nowa firma
                </Button>
              </div>
              <Field
                label="Nazwa umowy"
                name="name"
                required
                maxLength={180}
                defaultValue={contract?.name ?? converting?.name}
                error={fields.name}
              />
              <SelectField
                label="Typ umowy"
                name="contract_type"
                required
                value={contractType}
                onChange={(event) => setContractType(event.target.value as ContractType)}
                error={fields.contract_type}
              >
                {Object.entries(contractTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </SelectField>
              {contractType === "other" && (
                <Field
                  label="Własna nazwa typu umowy"
                  name="other_type_name"
                  required
                  maxLength={180}
                  defaultValue={contract?.other_type_name}
                  error={fields.other_type_name}
                />
              )}
              {(contractType === "employment" || contractType === "mandate") && (
                <Field
                  label="Stanowisko"
                  name="position"
                  maxLength={180}
                  defaultValue={contract?.position}
                  error={fields.position}
                />
              )}
              <Field
                label="Kwota brutto z umowy"
                name="gross_amount"
                required
                inputMode="decimal"
                pattern="[0-9]+([.,][0-9]{1,2})?"
                defaultValue={contract?.gross_amount}
                error={fields.gross_amount}
              />
              <SelectField
                label="Podstawa kwoty brutto"
                name="gross_basis"
                required
                defaultValue={contract?.gross_basis ?? "monthly"}
                error={fields.gross_basis}
              >
                <option value="monthly">Miesięcznie</option>
                <option value="hourly">Za godzinę</option>
                <option value="total">Za całość</option>
              </SelectField>
              <Field
                label="Waluta umowy"
                name="currency"
                required
                pattern="[A-Za-z]{3}"
                maxLength={3}
                defaultValue={contract?.currency ?? converting?.currency ?? household.currency}
                error={fields.currency}
              />
              <Field
                label="Data rozpoczęcia umowy"
                name="start_date"
                type="date"
                required
                defaultValue={contract?.start_date ?? converting?.start_date}
                error={fields.start_date}
              />
              <Field
                label="Data zakończenia umowy"
                name="end_date"
                type="date"
                defaultValue={contract?.end_date ?? converting?.end_date ?? ""}
                error={fields.end_date}
              />
            </div>
            {fields.expected_version && (
              <p className="notice error" role="alert">
                {fields.expected_version}
              </p>
            )}
          </>
        )}
      </ActionForm>
    </div>
  );
}
