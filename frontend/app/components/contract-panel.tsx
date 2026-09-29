"use client";

import { useEffect, useRef, useState } from "react";
import {
  api,
  apiAllPages,
  householdPath,
  messageOf,
  type Company,
  type Contract,
  type ContractType,
  type GrossBasis,
  type Household,
  type HouseholdMember,
  type IncomeSource,
} from "../lib/api";
import { formatMoney } from "../lib/money";
import { CompanyCreateForm, CompanyPanel } from "./company-panel";
import { ContractForm } from "./contract-form";
import { ActionForm, Button, Panel } from "./ui";

const typeLabels: Record<ContractType, string> = {
  employment: "Umowa o pracę",
  mandate: "Umowa zlecenie",
  specific_work: "Umowa o dzieło",
  other: "Inna umowa",
};
const basisLabels: Record<GrossBasis, string> = {
  monthly: "miesięcznie",
  hourly: "za godzinę",
  total: "za całość",
};

export function ContractPanel({
  household,
  members,
  converting,
  onCancelConversion,
  reloadSources,
  refreshAccess,
}: {
  household: Household;
  members: HouseholdMember[];
  converting: IncomeSource | null;
  onCancelConversion: () => void;
  reloadSources: () => void;
  refreshAccess: () => void;
}) {
  const [data, setData] = useState<{ companies: Company[]; contracts: Contract[] } | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [conflict, setConflict] = useState("");
  const [revision, setRevision] = useState(0);
  const [formRevision, setFormRevision] = useState(0);
  const [editing, setEditing] = useState<Contract | null>(null);
  const [creating, setCreating] = useState(false);
  const [showCompanies, setShowCompanies] = useState(false);
  const [companyDialogOpen, setCompanyDialogOpen] = useState(false);
  const [suggestedCompanyId, setSuggestedCompanyId] = useState("");
  const companyDialogRef = useRef<HTMLDialogElement>(null);
  const canEdit = household.role === "owner" || household.role === "administrator";
  const formTarget = converting?.id ?? editing?.id ?? (creating ? "new" : "");
  const formReady = data !== null;

  useEffect(() => {
    const controller = new AbortController();
    const base = householdPath(household.id);
    Promise.all([
      apiAllPages<Company>(`${base}companies/`, controller.signal),
      apiAllPages<Contract>(`${base}contracts/`, controller.signal),
    ])
      .then(([companies, contracts]) => {
        if (!controller.signal.aborted) {
          setData({ companies, contracts });
          setError("");
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [household.id, revision]);

  useEffect(() => {
    if (formTarget && formReady)
      document.querySelector<HTMLSelectElement>('#contract-form select[name="member_id"]')?.focus();
  }, [formTarget, formReady]);

  useEffect(() => {
    if (companyDialogOpen) {
      companyDialogRef.current?.showModal();
      companyDialogRef.current?.querySelector<HTMLInputElement>('input[name="name"]')?.focus();
    }
  }, [companyDialogOpen]);

  useEffect(() => {
    if (suggestedCompanyId)
      document
        .querySelector<HTMLSelectElement>('#contract-form select[name="company_id"]')
        ?.focus();
  }, [suggestedCompanyId]);

  function reload(message: string) {
    setEditing(null);
    setCreating(false);
    onCancelConversion();
    setSuggestedCompanyId("");
    setFormRevision((value) => value + 1);
    setNotice(message);
    setConflict("");
    setRevision((value) => value + 1);
    reloadSources();
  }

  function handleConflict() {
    setConflict(
      "Dane zmieniły się od ostatniego odczytu. Wczytano aktualną listę; wybierz rekord ponownie.",
    );
    setEditing(null);
    setCreating(false);
    onCancelConversion();
    setSuggestedCompanyId("");
    setFormRevision((value) => value + 1);
    setRevision((value) => value + 1);
    reloadSources();
  }

  if (error)
    return (
      <Panel title="Umowy i firmy">
        <p className="notice error" role="alert">
          {error}
        </p>
        <Button type="button" onClick={() => setRevision((value) => value + 1)}>
          Spróbuj ponownie
        </Button>
      </Panel>
    );
  if (!data) return <p role="status">Pobieranie umów i firm…</p>;

  const contract = converting ? null : editing;
  const showForm = creating || !!contract || !!converting;
  return (
    <div className="stack">
      <div className="family-section-heading">
        <div>
          <h2>{showCompanies ? "Firmy" : "Umowy"}</h2>
          <p className="muted">
            {showCompanies
              ? "Firmy powiązane z umowami członków gospodarstwa."
              : "Umowy członków rodziny, kwoty brutto i powiązane firmy."}
          </p>
        </div>
        <div className="family-heading-actions">
          {showCompanies ? (
            <Button type="button" variant="secondary" onClick={() => setShowCompanies(false)}>
              Wróć do umów
            </Button>
          ) : !showForm ? (
            <Button type="button" variant="secondary" onClick={() => setShowCompanies(true)}>
              Zarządzaj firmami
            </Button>
          ) : null}
          {canEdit && !showForm && !showCompanies && (
            <Button
              type="button"
              aria-controls="contract-form"
              onClick={() => {
                setEditing(null);
                setCreating(true);
                onCancelConversion();
                setNotice("");
                setConflict("");
              }}
            >
              Dodaj umowę
            </Button>
          )}
        </div>
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
      {!showCompanies && !showForm && (
        <Panel
          title="Lista umów"
          description="Kwota brutto i jej podstawa pochodzą z umowy; nie są przychodem miesiąca."
        >
          {!data.contracts.length ? (
            <p className="empty">Brak umów w tym gospodarstwie.</p>
          ) : (
            <div className="table-scroll" role="region" aria-label="Umowy — tabela" tabIndex={0}>
              <table className="income-table">
                <thead>
                  <tr>
                    <th scope="col">Umowa</th>
                    <th scope="col">Osoba</th>
                    <th scope="col">Firma i typ</th>
                    <th scope="col">Brutto</th>
                    <th scope="col">Okres</th>
                    <th scope="col">Status</th>
                    {canEdit && <th scope="col">Akcje</th>}
                  </tr>
                </thead>
                <tbody>
                  {data.contracts.map((item) => (
                    <tr key={item.id}>
                      <th scope="row">{item.name}</th>
                      <td>
                        {members.find((member) => member.id === item.member_id)?.display_name ??
                          "Osoba archiwalna"}
                      </td>
                      <td>
                        {item.company.name}
                        <span className="table-detail">
                          {item.contract_type === "other"
                            ? item.other_type_name
                            : typeLabels[item.contract_type]}
                        </span>
                        {item.position && <span className="table-detail">{item.position}</span>}
                      </td>
                      <td className="money">
                        {formatMoney(item.gross_amount, item.currency)}
                        <span className="table-detail">{basisLabels[item.gross_basis]}</span>
                      </td>
                      <td>
                        {item.start_date}
                        <span className="table-detail">
                          {item.end_date ? `do ${item.end_date}` : "bez daty końcowej"}
                        </span>
                      </td>
                      <td>{item.is_active ? "Aktywna" : "Archiwalna"}</td>
                      {canEdit && (
                        <td>
                          {item.is_active ? (
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() => {
                                onCancelConversion();
                                setEditing(item);
                                setCreating(false);
                                setSuggestedCompanyId("");
                                setNotice("");
                                setConflict("");
                              }}
                            >
                              Edytuj
                            </Button>
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
      )}
      {canEdit && showForm && (
        <div id="contract-form">
          <Panel
            title={
              converting
                ? `Przekształć źródło: ${converting.name}`
                : contract
                  ? `Edycja umowy: ${contract.name}`
                  : "Dodaj umowę"
            }
            description="Podaj kwotę brutto i podstawę umowy. Zapis nie dodaje przychodu za miesiąc."
            className="panel-wide-form"
            action={
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setEditing(null);
                  setCreating(false);
                  onCancelConversion();
                  setSuggestedCompanyId("");
                }}
              >
                Anuluj
              </Button>
            }
          >
            <ContractForm
              key={`${converting?.id ?? contract?.id ?? "new"}-${formRevision}`}
              household={household}
              members={members}
              companies={data.companies}
              contract={contract}
              converting={converting}
              suggestedCompanyId={suggestedCompanyId}
              onAddCompany={() => setCompanyDialogOpen(true)}
              onSaved={() =>
                reload(converting ? "Źródło przekształcono w umowę." : "Zapisano umowę.")
              }
              onConflict={handleConflict}
              refreshAccess={refreshAccess}
            />
            {contract && (
              <div className="member-danger-action">
                <ActionForm
                  submit="Archiwizuj umowę"
                  submitVariant="danger"
                  onDenied={refreshAccess}
                  action={async () => {
                    if (!window.confirm(`Archiwizować umowę ${contract.name}?`)) return;
                    await api(householdPath(household.id, `contracts/${contract.id}/archive/`), {
                      method: "POST",
                      data: {},
                    });
                    reload("Umowa została zarchiwizowana.");
                  }}
                >
                  {() => null}
                </ActionForm>
              </div>
            )}
          </Panel>
        </div>
      )}
      {showCompanies && (
        <CompanyPanel
          household={household}
          companies={data.companies}
          onCreated={(company) => {
            setData((current) =>
              current ? { ...current, companies: [...current.companies, company] } : current,
            );
          }}
          onChanged={() => setRevision((value) => value + 1)}
          refreshAccess={refreshAccess}
        />
      )}
      {companyDialogOpen && (
        <dialog
          ref={companyDialogRef}
          className="company-dialog"
          aria-labelledby="company-dialog-title"
          onClose={() => {
            setCompanyDialogOpen(false);
            requestAnimationFrame(() => {
              document
                .querySelector<HTMLSelectElement>('#contract-form select[name="company_id"]')
                ?.focus();
            });
          }}
        >
          <div className="dialog-heading">
            <div>
              <h2 id="company-dialog-title">Nowa firma</h2>
              <p className="muted">Podaj nazwę firmy. Po zapisaniu wybierzemy ją w umowie.</p>
            </div>
            <Button
              type="button"
              variant="secondary"
              onClick={() => companyDialogRef.current?.close()}
            >
              Anuluj
            </Button>
          </div>
          <CompanyCreateForm
            household={household}
            refreshAccess={refreshAccess}
            onCreated={(company) => {
              setData((current) =>
                current ? { ...current, companies: [...current.companies, company] } : current,
              );
              setSuggestedCompanyId(company.id);
              companyDialogRef.current?.close();
            }}
          />
        </dialog>
      )}
    </div>
  );
}
