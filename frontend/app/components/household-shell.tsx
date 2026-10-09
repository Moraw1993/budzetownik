"use client";
import Link from "next/link";

import { useRef, useEffect, useState, useCallback } from "react";
import {
  CalendarDays,
  ChevronDown,
  House,
  ShieldCheck,
  LogOut,
  Settings2,
  Users,
} from "lucide-react";
import { api, messageOf, roleLabels, type Household, type User } from "../lib/api";
import { AccessPanel } from "./access-panel";
import { PeriodsPanel } from "./periods-panel";
import { ConfirmAction } from "./periods-common";
import { type EditGuard } from "./income-form";
import { FamilyPanel } from "./family-panel";
import { ActionForm, Button, Field, Panel } from "./ui";

export type HouseholdSection = "family" | "settings" | "periods";

const sectionLabels: Record<HouseholdSection, string> = {
  family: "Zarządzanie rodziną",
  settings: "Ustawienia gospodarstwa / Dostępy",
  periods: "Okresy i przychody",
};

export function HouseholdShell({
  user,
  households,
  preferredId,
  preferredSection,
  refresh,
  logout,
  onSelect,
  onSectionChange,
  onEditing,
}: {
  user: User;
  households: Household[];
  preferredId?: string;
  preferredSection: HouseholdSection;
  refresh: (membershipId?: string) => Promise<void>;
  logout: () => Promise<void>;
  onSelect: (membershipId: string) => void;
  onSectionChange: (section: HouseholdSection) => void;
  onEditing: (editing: boolean) => void;
}) {
  const [activeId, setActiveId] = useState(preferredId ?? households[0]?.id ?? "");
  const [creating, setCreating] = useState(households.length === 0);
  const [section, setSection] = useState<HouseholdSection>(preferredSection);
  const active = households.find((household) => household.id === activeId);
  const alive = useRef(false);
  const contextVersion = useRef(0);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const editGuard = useRef<EditGuard>({ dirty: false, busy: false, unknown: false });
  const [navigation, setNavigation] = useState<{ run: () => void } | null>(null);
  const [navigationError, setNavigationError] = useState("");
  const requestNavigation = useCallback((run: () => void) => {
    if (editGuard.current.busy) {
      setNavigationError("Poczekaj na wynik trwającej operacji.");
      return;
    }
    if (editGuard.current.unknown) {
      setNavigationError("Najpierw sprawdź i dokończ poprzedni zapis przychodu.");
      return;
    }
    setNavigationError("");
    if (editGuard.current.dirty) setNavigation({ run });
    else run();
  }, []);
  const updateGuard = useCallback(
    (guard: EditGuard) => {
      editGuard.current = guard;
      onEditing(guard.dirty || guard.busy || guard.unknown);
    },
    [onEditing],
  );

  function selectSection(nextSection: HouseholdSection) {
    if (nextSection === section) return;
    requestNavigation(() => {
      setSection(nextSection);
      onSectionChange(nextSection);
    });
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <Link href="/" className="brand">
          <span className="brand-mark">
            <House size={22} aria-hidden="true" />
          </span>
          Domowe Finanse
        </Link>
        <p className="eyebrow">PRZESTRZEŃ DOMOWA</p>
        <Link href="#content" className={creating ? "nav-current active" : "nav-current"}>
          <House size={18} aria-hidden="true" />
          Gospodarstwa
        </Link>
        {active && !creating && (
          <nav className="section-nav" aria-label="Sekcje gospodarstwa">
            <button
              type="button"
              className={section === "family" ? "section-link active" : "section-link"}
              aria-current={section === "family" ? "page" : undefined}
              onClick={() => selectSection("family")}
            >
              <Users size={18} aria-hidden="true" />
              Zarządzanie rodziną
            </button>
            <button
              type="button"
              className={section === "settings" ? "section-link active" : "section-link"}
              aria-current={section === "settings" ? "page" : undefined}
              onClick={() => selectSection("settings")}
            >
              <Settings2 size={18} aria-hidden="true" />
              Ustawienia
            </button>
            <button
              type="button"
              className={section === "periods" ? "section-link active" : "section-link"}
              aria-current={section === "periods" ? "page" : undefined}
              onClick={() => selectSection("periods")}
            >
              <CalendarDays size={18} aria-hidden="true" />
              Okresy i przychody
            </button>
          </nav>
        )}
        <div className="sidebar-note">
          <ShieldCheck size={20} aria-hidden="true" />
          <p>Dane pozostają w Twojej lokalnej instalacji.</p>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            Gospodarstwa / {creating ? "Nowe gospodarstwo" : (active?.name ?? "Wybór")}
            {active && !creating ? ` / ${sectionLabels[section]}` : ""}
          </span>
          <div className="account-actions">
            <span>{user.username}</span>
            <ActionForm
              submit="Wyloguj się"
              submitVariant="secondary"
              action={async () => {
                if (
                  editGuard.current.dirty ||
                  editGuard.current.busy ||
                  editGuard.current.unknown
                ) {
                  requestNavigation(() => {
                    void logout().catch((cause) => setNavigationError(messageOf(cause)));
                  });
                } else await logout();
              }}
              onDenied={() => {
                void refresh();
              }}
            >
              {() => <LogOut size={16} aria-hidden="true" />}
            </ActionForm>
          </div>
        </header>
        <main id="content" className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">
                {creating
                  ? "GOSPODARSTWO"
                  : section === "settings"
                    ? "USTAWIENIA GOSPODARSTWA"
                    : active?.name.toUpperCase()}
              </p>
              <div className="heading-title-row">
                <h1>
                  {creating
                    ? "Nowe gospodarstwo"
                    : section === "settings"
                      ? "Ustawienia gospodarstwa"
                      : section === "periods"
                        ? "Okresy i przychody"
                        : "Twoja rodzina, w jednym miejscu"}
                </h1>
                {!!households.length && !creating && (
                  <div className="household-switcher">
                    <label className="sr-only" htmlFor="household-context">
                      Aktywne gospodarstwo
                    </label>
                    <select
                      id="household-context"
                      value={activeId}
                      onChange={(event) => {
                        const value = event.target.value;
                        requestNavigation(() => {
                          contextVersion.current++;
                          if (value === "create") {
                            setCreating(true);
                            selectSection("family");
                            return;
                          }
                          setActiveId(value);
                          const selected = households.find((home) => home.id === value);
                          if (selected) onSelect(selected.membership_id);
                          setCreating(false);
                          setSection("family");
                          onSectionChange("family");
                        });
                      }}
                    >
                      {households.map((household) => (
                        <option value={household.id} key={household.id}>
                          {household.name}
                        </option>
                      ))}
                      <option value="create">+ Nowe gospodarstwo</option>
                    </select>
                    <ChevronDown size={18} aria-hidden="true" />
                  </div>
                )}
              </div>
              <p className="muted">
                {section === "settings" && !creating
                  ? "Dostępy i zaproszenia dotyczą wybranego gospodarstwa."
                  : creating
                    ? "Nadaj nazwę nowemu gospodarstwu domowemu."
                    : section === "periods"
                      ? "Lata, miesiące i faktyczne przychody Twojego gospodarstwa."
                      : "Osoby, źródła dochodu i umowy Twojego gospodarstwa."}
              </p>
            </div>
          </div>
          {active && section === "settings" && !creating && (
            <p className="context-meta">
              <span className="badge">{roleLabels[active.role]}</span>
              <span>Waluta: {active.currency}</span>
            </p>
          )}
          {navigationError && (
            <p className="notice warning" role="alert">
              {navigationError}
            </p>
          )}
          {navigation && (
            <ConfirmAction
              variant="danger"
              title="Masz niezapisane zmiany"
              description="Opuszczenie widoku usunie szkic i kolejkę niezapisanych plików."
              confirm="Opuść widok i odrzuć szkic"
              pending={false}
              onCancel={() => setNavigation(null)}
              onConfirm={() => {
                const run = navigation.run;
                setNavigation(null);
                updateGuard({ dirty: false, busy: false, unknown: false });
                run();
              }}
            />
          )}
          {creating ? (
            <Panel
              title="Dane gospodarstwa"
              description="Otrzymasz rolę Owner. Domyślna waluta to PLN."
              className="panel-compact-form"
              action={
                households.length ? (
                  <Button type="button" variant="secondary" onClick={() => setCreating(false)}>
                    Anuluj
                  </Button>
                ) : undefined
              }
            >
              <ActionForm
                submit="Utwórz gospodarstwo"
                onDenied={() => {
                  void refresh();
                }}
                action={async (form) => {
                  const version = contextVersion.current;
                  const created = await api<Household>("/households/", {
                    method: "POST",
                    data: { name: form.get("name"), currency: form.get("currency") },
                  });
                  if (alive.current && version === contextVersion.current)
                    await refresh(created.membership_id);
                }}
              >
                {(fields) => (
                  <>
                    <Field
                      label="Nazwa gospodarstwa"
                      name="name"
                      required
                      maxLength={180}
                      error={fields.name}
                      placeholder="Np. Dom rodzinny"
                    />
                    <Field
                      label="Waluta (kod trzyliterowy)"
                      name="currency"
                      defaultValue="PLN"
                      pattern="[A-Z]{3}"
                      maxLength={3}
                      required
                      error={fields.currency}
                    />
                  </>
                )}
              </ActionForm>
            </Panel>
          ) : active && section === "settings" ? (
            <AccessPanel
              key={active.id}
              household={active}
              refresh={() => {
                void refresh(active.membership_id);
              }}
            />
          ) : active && section === "periods" ? (
            <PeriodsPanel
              key={active.id}
              household={active}
              requestNavigation={requestNavigation}
              onGuard={updateGuard}
            />
          ) : active && section === "family" ? (
            <FamilyPanel
              key={active.id}
              household={active}
              refreshAccess={() => {
                void refresh(active.membership_id);
              }}
            />
          ) : (
            <p className="empty">
              Nie masz jeszcze gospodarstwa. Utwórz je lub otwórz link zaproszenia od Ownera.
            </p>
          )}
        </main>
      </div>
    </div>
  );
}
