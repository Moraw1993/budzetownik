"use client";
import { useEffect, useState } from "react";
import { api, ApiError, householdPath, messageOf, type Paginated } from "../lib/api";
import { formatMoney } from "../lib/money";
import {
  canManage,
  incomePath,
  monthNames,
  periodPath,
  type CurrencyTotal,
  type Income,
  type PeriodContext,
} from "../lib/periods-api";
import { Button, Panel, Pagination } from "./ui";
import { ConfirmAction, LoadError, PeriodState } from "./periods-common";

function Totals({ path, title, revision }: { path: string; title: string; revision: number }) {
  const [data, setData] = useState<CurrencyTotal[] | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    api<{ totals: CurrencyTotal[] }>(path, { signal: controller.signal })
      .then((reply) => {
        if (!controller.signal.aborted) {
          setData(reply.totals);
          setError("");
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [path, revision, retry]);
  return (
    <Panel title={title}>
      {error ? (
        <LoadError error={error} retry={() => setRetry((value) => value + 1)} />
      ) : data === null ? (
        <p role="status">Pobieranie podsumowania…</p>
      ) : !data.length ? (
        <p className="muted">Brak przychodów</p>
      ) : (
        <ul className="period-totals">
          {data.map((total) => (
            <li key={total.currency}>
              <span>{total.currency}</span>
              <strong className="period-amount">{formatMoney(total.amount, total.currency)}</strong>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function IncomeList({
  context,
  onAdd,
  onEdit,
  onFiles,
  onState,
  onRecheck,
}: {
  context: PeriodContext;
  onAdd: () => void;
  onEdit: (income: Income) => void;
  onFiles: (income: Income) => void;
  onState: () => void;
  onRecheck: () => void;
}) {
  const [data, setData] = useState<Paginated<Income> | null>(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [deleting, setDeleting] = useState<Income | null>(null);
  const [actionError, setActionError] = useState("");
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState("");
  const writable = canManage(context.household) && context.month.state === "active";
  const path = periodPath(context, "incomes/");
  useEffect(() => {
    const request = new AbortController();
    api<Paginated<Income>>(`${path}?page=${page}`, { signal: request.signal })
      .then((reply) => {
        if (!request.signal.aborted) {
          if (!reply.results.length && page > 1) {
            setPage(page - 1);
            return;
          }
          setData(reply);
          setError("");
        }
      })
      .catch((cause) => {
        if (!request.signal.aborted) setError(messageOf(cause));
      });
    return () => request.abort();
  }, [path, page, revision]);
  async function remove() {
    if (!deleting || pending) return;
    setPending(true);
    setActionError("");
    try {
      await api(incomePath(context, deleting.id), {
        method: "DELETE",
        data: { expected_version: deleting.version },
      });
      setDeleting(null);
      setNotice("Usunięto przychód.");
      setRevision((value) => value + 1);
    } catch (cause) {
      setActionError(messageOf(cause));
      if (cause instanceof ApiError && [401, 403, 404, 409].includes(cause.status))
        setDeleting(null);
      onRecheck();
      setRevision((value) => value + 1);
    } finally {
      setPending(false);
    }
  }
  return (
    <div className="stack">
      <div className="family-section-heading">
        <div>
          <h2>
            {monthNames[context.month.month_number - 1]} {context.year.calendar_year}
          </h2>
          <PeriodState month={context.month} />
        </div>
        {writable && (
          <Button type="button" onClick={onAdd}>
            Dodaj przychód
          </Button>
        )}
      </div>
      {!writable && (
        <p className="notice warning">
          Tylko odczyt.{" "}
          {context.month.state !== "active"
            ? "Zmiany wymagają aktywnego miesiąca."
            : "Zmiany są dostępne dla Ownera i Administratora."}
          {canManage(context.household) && (
            <Button type="button" variant="secondary" onClick={onState}>
              Zarządzaj stanem miesiąca
            </Button>
          )}
        </p>
      )}
      {notice && (
        <p className="notice success" role="status">
          {notice}
        </p>
      )}
      <div className="period-summary">
        <Totals
          path={periodPath(context, "income-totals/")}
          title="Przychody miesiąca"
          revision={revision}
        />
        <Totals
          path={householdPath(
            context.household.id,
            `accounting-years/${context.year.id}/income-totals/`,
          )}
          title={`Przychody roku ${context.year.calendar_year}`}
          revision={revision}
        />
      </div>
      {actionError && !deleting && (
        <p className="notice error" role="alert">
          {actionError} Wczytano aktualne dane. Wybierz wpis ponownie.
        </p>
      )}
      {deleting && (
        <ConfirmAction
          variant="danger"
          title="Usuń przychód"
          description={`${deleting.recipient_snapshot.label} · ${formatMoney(deleting.amount, deleting.currency)}. Wpis i jego załączniki zostaną usunięte z listy.`}
          confirm="Usuń przychód"
          pending={pending}
          error={actionError}
          onConfirm={() => void remove()}
          onCancel={() => setDeleting(null)}
        />
      )}
      <Panel
        title="Przychody"
        description="Faktyczne wpływy, oddzielnie dla każdego źródła. Data otrzymania może być poza okresem rozliczeniowym."
      >
        {error ? (
          <LoadError error={error} retry={() => setRevision((value) => value + 1)} />
        ) : !data ? (
          <p role="status">Pobieranie przychodów…</p>
        ) : !data.results.length ? (
          <p className="empty">Brak przychodów w tym miesiącu.</p>
        ) : (
          <>
            <div
              className="table-scroll"
              role="region"
              tabIndex={0}
              aria-label="Przychody miesiąca — tabela"
            >
              <table>
                <thead>
                  <tr>
                    <th scope="col">Odbiorca i źródło</th>
                    <th scope="col">Kwota</th>
                    <th scope="col">Data otrzymania</th>
                    <th scope="col">Akcje</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((income) => (
                    <tr key={income.id}>
                      <th scope="row">
                        {income.recipient_snapshot.label}
                        <span className="table-detail">{income.source_snapshot.name}</span>
                      </th>
                      <td className="period-amount">
                        {formatMoney(income.amount, income.currency)}
                      </td>
                      <td>{income.receipt_date}</td>
                      <td>
                        <div className="row-actions">
                          <Button type="button" variant="secondary" onClick={() => onFiles(income)}>
                            Załączniki
                          </Button>
                          {writable && (
                            <>
                              <Button
                                type="button"
                                variant="secondary"
                                onClick={() => onEdit(income)}
                              >
                                Edytuj
                              </Button>
                              <Button
                                type="button"
                                variant="danger"
                                onClick={() => {
                                  setDeleting(income);
                                  setActionError("");
                                }}
                              >
                                Usuń
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
      </Panel>
    </div>
  );
}
