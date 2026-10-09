"use client";
import { useEffect, useState } from "react";
import { api, ApiError, householdPath, messageOf, type Household } from "../lib/api";
import {
  canManage,
  months,
  monthNames,
  type AccountingMonth,
  type AccountingYear,
} from "../lib/periods-api";
import { Button, Panel } from "./ui";
import { ConfirmAction, LoadError, PeriodState } from "./periods-common";

export function AccountingMonths({
  household,
  year,
  onSelect,
  onRecheck,
}: {
  household: Household;
  onRecheck: () => void;
  year: AccountingYear;
  onSelect: (month: AccountingMonth) => void;
}) {
  const [data, setData] = useState<AccountingMonth[] | null>(null);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState<AccountingMonth | null>(null);
  const [pending, setPending] = useState(false);
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    months(household, year, controller.signal)
      .then((reply) => {
        if (!controller.signal.aborted) {
          setData(reply);
          setError("");
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [household, year, revision]);
  async function transition() {
    if (!selected || pending) return;
    const operation =
      selected.state === "inactive" ? "activate" : selected.state === "active" ? "close" : "reopen";
    setPending(true);
    setActionError("");
    try {
      await api(
        householdPath(
          household.id,
          `accounting-years/${year.id}/months/${selected.id}/${operation}/`,
        ),
        { method: "POST", data: {} },
      );
      setSelected(null);
      setNotice("Zapisano stan miesiąca.");
    } catch (cause) {
      setActionError(messageOf(cause));
      if (cause instanceof ApiError && [401, 403, 404, 409].includes(cause.status))
        setSelected(null);
      onRecheck();
    } finally {
      setPending(false);
      setRevision((value) => value + 1);
    }
  }
  const label =
    selected?.state === "inactive"
      ? "Aktywuj"
      : selected?.state === "active"
        ? "Zamknij"
        : "Otwórz";
  return (
    <div className="stack">
      <div>
        <h2>Miesiące roku {year.calendar_year}</h2>
        <p className="muted">Możesz aktywować wiele miesięcy w dowolnej kolejności.</p>
      </div>
      {notice && (
        <p className="notice success" role="status">
          {notice}
        </p>
      )}
      {actionError && !selected && (
        <p className="notice error" role="alert">
          {actionError} Sprawdź aktualny stan i wybierz akcję ponownie.
        </p>
      )}
      {selected && (
        <ConfirmAction
          title={`${label} miesiąc: ${monthNames[selected.month_number - 1]} ${year.calendar_year}`}
          description={
            selected.state === "active"
              ? "Zamknięcie zablokuje zmiany przychodów i załączników. Możesz później otworzyć miesiąc ponownie."
              : "Ta akcja pozwoli dodawać i zmieniać przychody oraz załączniki w tym miesiącu."
          }
          confirm={`${label} ${monthNames[selected.month_number - 1].toLowerCase()}`}
          pending={pending}
          error={actionError}
          onConfirm={() => void transition()}
          onCancel={() => setSelected(null)}
        />
      )}
      {error ? (
        <LoadError error={error} retry={() => setRevision((value) => value + 1)} />
      ) : !data ? (
        <p role="status">Pobieranie miesięcy…</p>
      ) : (
        <div className="period-grid">
          {data.map((month) => (
            <Panel key={month.id} title={monthNames[month.month_number - 1]}>
              <PeriodState month={month} />
              <div className="row-actions">
                <Button type="button" variant="secondary" onClick={() => onSelect(month)}>
                  Przychody
                </Button>
                {canManage(household) && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setSelected(month);
                      setActionError("");
                    }}
                  >
                    {month.state === "inactive"
                      ? "Aktywuj"
                      : month.state === "active"
                        ? "Zamknij"
                        : "Otwórz ponownie"}
                  </Button>
                )}
              </div>
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}
