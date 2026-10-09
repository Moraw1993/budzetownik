"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError, type Household } from "../lib/api";
import {
  months,
  monthNames,
  type AccountingMonth,
  type AccountingYear,
  type Income,
} from "../lib/periods-api";
import { AccountingYears } from "./accounting-years";
import { AccountingMonths } from "./accounting-months";
import { IncomeList } from "./income-list";
import { IncomeForm, type EditGuard } from "./income-form";
import { IncomeAttachments } from "./income-attachments";
import { Button } from "./ui";

type View = "years" | "months" | "list" | "form" | "attachments";
export function PeriodsPanel({
  household,
  requestNavigation,
  onGuard,
}: {
  household: Household;
  requestNavigation: (action: () => void) => void;
  onGuard: (guard: EditGuard) => void;
}) {
  const [view, setView] = useState<View>("years");
  const [year, setYear] = useState<AccountingYear | null>(null);
  const [month, setMonth] = useState<AccountingMonth | null>(null);
  const [income, setIncome] = useState<Income | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [access, setAccess] = useState(household);
  const [unavailable, setUnavailable] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const read = useRef<AbortController | null>(null);
  const context = useMemo(
    () => (year && month ? { household: access, year, month } : null),
    [access, year, month],
  );
  const recheck = useCallback(() => {
    read.current?.abort();
    const controller = new AbortController();
    read.current = controller;
    const expectedMonth = month?.id;
    void Promise.allSettled([
      api<Household[]>("/households/", { signal: controller.signal }),
      year ? months(household, year, controller.signal) : Promise.resolve([]),
    ]).then(([membershipResult, periodResult]) => {
      if (controller.signal.aborted) return;
      if (membershipResult.status === "fulfilled") {
        const membership = membershipResult.value.find((item) => item.id === household.id);
        if (!membership) {
          setUnavailable(true);
          return;
        }
        setAccess((previous) => (previous.role === membership.role ? previous : membership));
      } else if (
        membershipResult.reason instanceof ApiError &&
        [401, 403, 404].includes(membershipResult.reason.status)
      ) {
        setUnavailable(true);
        return;
      }
      if (periodResult.status === "fulfilled" && expectedMonth) {
        const current = periodResult.value.find((item) => item.id === expectedMonth);
        if (!current) {
          setUnavailable(true);
          return;
        }
        setMonth((previous) =>
          previous?.id !== expectedMonth || previous.state === current.state ? previous : current,
        );
      } else if (
        periodResult.status === "rejected" &&
        periodResult.reason instanceof ApiError &&
        [401, 403, 404].includes(periodResult.reason.status)
      ) {
        setUnavailable(true);
      }
    });
  }, [household, year, month]);
  useEffect(() => {
    heading.current?.focus();
  }, [view, year?.id, month?.id, income?.id]);
  useEffect(() => () => read.current?.abort(), [year?.id, month?.id]);
  useEffect(() => {
    if (view === "list") recheck();
  }, [view, recheck]);
  const navigate = (next: View) => {
    if (next === view) return;
    requestNavigation(() => {
      setView(next);
      setFiles([]);
    });
  };
  return (
    <section className="periods-workspace" aria-label="Okresy i przychody">
      <nav className="period-breadcrumbs" aria-label="Ścieżka okresu">
        <Button
          type="button"
          variant="secondary"
          aria-current={view === "years" ? "page" : undefined}
          onClick={() => navigate("years")}
        >
          Lata
        </Button>
        {year && view !== "years" && (
          <>
            <span aria-hidden="true">/</span>
            <Button
              type="button"
              variant="secondary"
              aria-current={view === "months" ? "page" : undefined}
              onClick={() => navigate("months")}
            >
              Rok {year.calendar_year}
            </Button>
          </>
        )}
        {month && context && !["years", "months"].includes(view) && (
          <>
            <span aria-hidden="true">/</span>
            <Button
              type="button"
              variant="secondary"
              aria-current={view === "list" ? "page" : undefined}
              onClick={() => navigate("list")}
            >
              {monthNames[month.month_number - 1]}
            </Button>
          </>
        )}
      </nav>
      <h2 className="sr-only" tabIndex={-1} ref={heading}>
        {view === "years"
          ? "Lata rozliczeniowe"
          : view === "months"
            ? "Miesiące roku"
            : view === "form"
              ? "Formularz przychodu"
              : view === "attachments"
                ? "Załączniki przychodu"
                : "Przychody miesiąca"}
      </h2>
      {unavailable ? (
        <p className="notice error" role="alert">
          Dane lub dostęp do gospodarstwa są niedostępne. Odśwież aplikację.
        </p>
      ) : (
        <>
          {view === "years" && (
            <AccountingYears
              onRecheck={recheck}
              household={access}
              onSelect={(selected) => {
                setYear(selected);
                setMonth(null);
                setView("months");
              }}
            />
          )}
          {view === "months" && year && (
            <AccountingMonths
              onRecheck={recheck}
              household={access}
              year={year}
              onSelect={(selected) => {
                setMonth(selected);
                setView("list");
              }}
            />
          )}
          {view === "list" && context && (
            <IncomeList
              onRecheck={recheck}
              context={context}
              onAdd={() => {
                setIncome(null);
                setView("form");
              }}
              onEdit={(selected) => {
                setIncome(selected);
                setView("form");
              }}
              onFiles={(selected) => {
                setIncome(selected);
                setFiles([]);
                setView("attachments");
              }}
              onState={() => navigate("months")}
            />
          )}
          {view === "form" && context && (
            <IncomeForm
              context={context}
              initial={income}
              onGuard={onGuard}
              onRecheck={recheck}
              onCancel={() => navigate("list")}
              onSaved={(saved, selectedFiles) => {
                setIncome(saved);
                setFiles(selectedFiles);
                setView("attachments");
              }}
            />
          )}
          {view === "attachments" && context && income && (
            <IncomeAttachments
              key={income.id}
              context={context}
              income={income}
              initialFiles={files}
              onGuard={onGuard}
              onRecheck={recheck}
            />
          )}
        </>
      )}
    </section>
  );
}
