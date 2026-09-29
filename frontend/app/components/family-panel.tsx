"use client";

import { useEffect, useState } from "react";
import { Database, FileText, Users } from "lucide-react";
import {
  apiAllPages,
  householdPath,
  messageOf,
  type Household,
  type HouseholdMember,
  type IncomeSource,
} from "../lib/api";
import { ContractPanel } from "./contract-panel";
import { MembersPanel } from "./members-panel";
import { OtherSourcesPanel } from "./other-sources-panel";
import { Button, Panel } from "./ui";

type FamilySection = "members" | "sources" | "contracts";

const familySections = [
  { id: "members", label: "Członkowie", icon: Users },
  { id: "sources", label: "Źródła dochodu", icon: Database },
  { id: "contracts", label: "Umowy", icon: FileText },
] as const;

export function FamilyPanel({
  household,
  refreshAccess,
}: {
  household: Household;
  refreshAccess: () => void;
}) {
  const [data, setData] = useState<{ sources: IncomeSource[]; members: HouseholdMember[] } | null>(
    null,
  );
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [converting, setConverting] = useState<IncomeSource | null>(null);
  const [section, setSection] = useState<FamilySection>("members");

  useEffect(() => {
    const controller = new AbortController();
    const base = householdPath(household.id);
    Promise.all([
      apiAllPages<IncomeSource>(`${base}income-sources/`, controller.signal),
      apiAllPages<HouseholdMember>(`${base}members/`, controller.signal),
    ])
      .then(([sources, members]) => {
        if (!controller.signal.aborted) {
          setData({ sources, members });
          setError("");
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [household.id, revision]);

  return (
    <div className="family-workspace">
      <div className="family-navigation" role="tablist" aria-label="Sekcje zarządzania rodziną">
        {familySections.map(({ id, label, icon: Icon }, index) => (
          <button
            key={id}
            type="button"
            className={section === id ? "family-navigation-link active" : "family-navigation-link"}
            id={`family-tab-${id}`}
            role="tab"
            aria-selected={section === id}
            aria-controls="family-tabpanel"
            tabIndex={section === id ? 0 : -1}
            onClick={() => setSection(id)}
            onKeyDown={(event) => {
              const direction = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
              const nextIndex =
                event.key === "Home"
                  ? 0
                  : event.key === "End"
                    ? familySections.length - 1
                    : direction
                      ? (index + direction + familySections.length) % familySections.length
                      : -1;
              if (nextIndex < 0) return;
              event.preventDefault();
              const nextSection = familySections[nextIndex].id;
              setSection(nextSection);
              document.getElementById(`family-tab-${nextSection}`)?.focus();
            }}
          >
            <Icon size={20} aria-hidden="true" />
            <span>{label}</span>
            {data && (
              <span className="tab-count">
                {id === "members"
                  ? data.members.length
                  : data.sources.filter(
                      (source) => source.kind === (id === "contracts" ? "contract" : "other"),
                    ).length}
              </span>
            )}
          </button>
        ))}
      </div>
      <section
        id="family-tabpanel"
        className="family-view"
        role="tabpanel"
        aria-labelledby={`family-tab-${section}`}
        tabIndex={0}
      >
        {error ? (
          <Panel title="Zarządzanie rodziną">
            <p className="notice error" role="alert">
              {error}
            </p>
            <Button type="button" onClick={() => setRevision((value) => value + 1)}>
              Spróbuj ponownie
            </Button>
          </Panel>
        ) : !data ? (
          <p role="status">Pobieranie danych rodziny…</p>
        ) : section === "members" ? (
          <MembersPanel
            household={household}
            refreshAccess={refreshAccess}
            sources={data.sources}
            onChanged={() => setRevision((value) => value + 1)}
          />
        ) : section === "sources" ? (
          <OtherSourcesPanel
            household={household}
            refreshAccess={refreshAccess}
            sources={data.sources}
            members={data.members}
            reloadSources={() => setRevision((value) => value + 1)}
            onConvert={(source) => {
              setConverting(source);
              setSection("contracts");
            }}
          />
        ) : (
          <ContractPanel
            household={household}
            refreshAccess={refreshAccess}
            members={data.members}
            converting={converting}
            onCancelConversion={() => setConverting(null)}
            reloadSources={() => setRevision((value) => value + 1)}
          />
        )}
      </section>
    </div>
  );
}
