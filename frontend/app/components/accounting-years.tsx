"use client";
import { useEffect, useState } from "react";
import {
  api,
  ApiError,
  householdPath,
  messageOf,
  type Household,
  type Paginated,
} from "../lib/api";
import { canManage, years, type AccountingYear } from "../lib/periods-api";
import { ActionForm, Button, Field, Panel, Pagination } from "./ui";
import { LoadError } from "./periods-common";

export function AccountingYears({
  household,
  onSelect,
  onRecheck,
}: {
  household: Household;
  onRecheck: () => void;
  onSelect: (year: AccountingYear) => void;
}) {
  const [data, setData] = useState<Paginated<AccountingYear> | null>(null);
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  useEffect(() => {
    const request = new AbortController();
    years(household, page, request.signal)
      .then((reply) => {
        if (!request.signal.aborted) {
          setData(reply);
          setError("");
        }
      })
      .catch((cause) => {
        if (!request.signal.aborted) setError(messageOf(cause));
      });
    return () => request.abort();
  }, [household, page, revision]);
  useEffect(() => {
    if (adding) document.querySelector<HTMLInputElement>("#year-add input")?.focus();
  }, [adding]);
  return (
    <div className="stack">
      <div className="family-section-heading">
        <div>
          <h2>Lata rozliczeniowe</h2>
          <p className="muted">Każdy rok zawiera 12 miesięcy. Sam wybór okresu nie aktywuje go.</p>
        </div>
        {canManage(household) && !adding && (
          <Button type="button" onClick={() => setAdding(true)}>
            Dodaj rok
          </Button>
        )}
      </div>
      {adding && (
        <div id="year-add">
          <Panel
            title="Dodaj rok"
            description="Powstanie 12 nieaktywnych miesięcy. Każdy miesiąc aktywujesz osobno."
            action={
              <Button type="button" variant="secondary" onClick={() => setAdding(false)}>
                Anuluj
              </Button>
            }
          >
            <ActionForm
              onDenied={onRecheck}
              submit="Utwórz rok"
              action={async (form) => {
                try {
                  const created = await api<AccountingYear>(
                    householdPath(household.id, "accounting-years/"),
                    {
                      method: "POST",
                      data: { calendar_year: Number(form.get("calendar_year")) },
                      expectedStatus: 201,
                    },
                  );
                  onSelect(created);
                } catch (cause) {
                  setRevision((value) => value + 1);
                  if (cause instanceof ApiError && cause.status === 409)
                    throw new ApiError(409, "Ten rok już istnieje — wybierz go z listy.");
                  throw cause;
                }
              }}
            >
              {(fields) => (
                <Field
                  label="Rok"
                  name="calendar_year"
                  type="number"
                  min={1}
                  max={9999}
                  step={1}
                  defaultValue={new Date().getFullYear()}
                  required
                  error={fields.calendar_year}
                />
              )}
            </ActionForm>
          </Panel>
        </div>
      )}
      {error ? (
        <LoadError error={error} retry={() => setRevision((value) => value + 1)} />
      ) : !data ? (
        <p role="status">Pobieranie lat…</p>
      ) : (
        <>
          {!data.results.length && <p className="empty">Brak lat rozliczeniowych.</p>}
          <div className="period-grid">
            {data.results.map((year) => (
              <Panel key={year.id} title={String(year.calendar_year)} description="12 miesięcy">
                <Button type="button" variant="secondary" onClick={() => onSelect(year)}>
                  Zobacz miesiące
                </Button>
              </Panel>
            ))}
          </div>
          <Pagination
            count={data.count}
            page={page}
            onPage={(next) => {
              setData(null);
              setPage(next);
            }}
          />
        </>
      )}
    </div>
  );
}
