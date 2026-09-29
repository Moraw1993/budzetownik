"use client";

import { useEffect, useState } from "react";
import { BriefcaseBusiness, Link2, UserRound, WalletCards, Plus } from "lucide-react";
import {
  api,
  apiAllPages,
  householdPath,
  messageOf,
  type Household,
  type HouseholdMember,
  type IncomeSource,
  type Membership,
  type Paginated,
  type RelationType,
} from "../lib/api";
import { ActionForm, Button, Field, Pagination, Panel, SelectField } from "./ui";

type MembersData = {
  members: Paginated<HouseholdMember>;
  relations: RelationType[];
  accounts: Membership[];
};

function MemberForm({
  household,
  member,
  relations,
  accounts,
  onSaved,
  onDenied,
}: {
  household: Household;
  member: HouseholdMember | null;
  relations: RelationType[];
  accounts: Membership[];
  onSaved: (message: string) => void;
  onDenied: () => void;
}) {
  const activeRelations = relations.filter((relation) => relation.is_active);
  const relationAvailable = activeRelations.some(
    (relation) => relation.id === member?.relation_type_id,
  );
  const accountAvailable = accounts.some((account) => account.user_id === member?.account_id);
  return (
    <ActionForm
      submit={member ? "Zapisz członka" : "Dodaj członka"}
      onDenied={onDenied}
      action={async (form) => {
        const relation = String(form.get("relation_type_id") ?? "");
        const account = String(form.get("account_id") ?? "");
        await api(householdPath(household.id, member ? `members/${member.id}/` : "members/"), {
          method: member ? "PATCH" : "POST",
          data: {
            display_name: String(form.get("display_name") ?? ""),
            relation_type_id: relation || null,
            account_id: account ? Number(account) : null,
          },
        });
        onSaved(member ? "Zapisano dane członka." : "Dodano członka gospodarstwa.");
      }}
    >
      {(fields) => (
        <>
          <Field
            label="Nazwa członka"
            name="display_name"
            required
            maxLength={180}
            defaultValue={member?.display_name}
            error={fields.display_name}
            placeholder="Np. Anna"
          />
          <SelectField
            label="Relacja rodzinna"
            name="relation_type_id"
            defaultValue={relationAvailable ? (member?.relation_type_id ?? "") : ""}
            error={fields.relation_type_id}
          >
            <option value="">Bez przypisanej relacji</option>
            {activeRelations.map((relation) => (
              <option key={relation.id} value={relation.id}>
                {relation.name}
              </option>
            ))}
          </SelectField>
          {member?.relation_type_id && !relationAvailable && (
            <p className="notice warning" role="status">
              Poprzednia relacja jest archiwalna. Wybierz aktywną relację albo pozostaw pole puste.
            </p>
          )}
          <SelectField
            label="Powiązane konto"
            name="account_id"
            defaultValue={accountAvailable ? (member?.account_id ?? "") : ""}
            error={fields.account_id}
          >
            <option value="">Bez konta</option>
            {accounts.map((account) => (
              <option key={account.user_id} value={account.user_id}>
                {account.username}
              </option>
            ))}
          </SelectField>
          {member?.account_id && !accountAvailable && (
            <p className="notice warning" role="status">
              Poprzednio powiązane konto nie ma już dostępu. Wybierz dostępne konto albo usuń
              powiązanie.
            </p>
          )}
        </>
      )}
    </ActionForm>
  );
}

function RelationForm({
  household,
  relation,
  onSaved,
  onDenied,
}: {
  household: Household;
  relation: RelationType | null;
  onSaved: (message: string) => void;
  onDenied: () => void;
}) {
  return (
    <ActionForm
      submit={relation ? "Zapisz relację" : "Dodaj relację"}
      onDenied={onDenied}
      action={async (form) => {
        await api(
          householdPath(
            household.id,
            relation ? `relation-types/${relation.id}/` : "relation-types/",
          ),
          {
            method: relation ? "PATCH" : "POST",
            data: { name: String(form.get("name") ?? "") },
          },
        );
        onSaved(relation ? "Zmieniono nazwę relacji." : "Dodano relację rodzinną.");
      }}
    >
      {(fields) => (
        <Field
          label="Nazwa relacji"
          name="name"
          required
          maxLength={100}
          defaultValue={relation?.name}
          error={fields.name}
          placeholder="Np. Rodzic"
        />
      )}
    </ActionForm>
  );
}

export function MembersPanel({
  household,
  refreshAccess,
  sources,
  onChanged,
}: {
  household: Household;
  refreshAccess: () => void;
  sources: IncomeSource[];
  onChanged: () => void;
}) {
  const [data, setData] = useState<MembersData | null>(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [editingMember, setEditingMember] = useState<HouseholdMember | null>(null);
  const [editingRelation, setEditingRelation] = useState<RelationType | null>(null);
  const [showMemberForm, setShowMemberForm] = useState(false);
  const [showRelations, setShowRelations] = useState(false);
  const [showRelationForm, setShowRelationForm] = useState(false);
  const [formRevision, setFormRevision] = useState(0);
  const [notice, setNotice] = useState("");
  const canEdit = household.role === "owner" || household.role === "administrator";

  useEffect(() => {
    if (showMemberForm)
      document.querySelector<HTMLInputElement>('#member-form input[name="display_name"]')?.focus();
  }, [showMemberForm, editingMember]);

  useEffect(() => {
    if (showRelations && showRelationForm)
      document.querySelector<HTMLInputElement>('.embedded-form input[name="name"]')?.focus();
  }, [showRelations, showRelationForm, editingRelation]);

  useEffect(() => {
    const controller = new AbortController();
    const base = householdPath(household.id);
    Promise.all([
      api<Paginated<HouseholdMember>>(`${base}members/?page=${page}`, {
        signal: controller.signal,
      }),
      apiAllPages<RelationType>(`${base}relation-types/`, controller.signal),
      api<Membership[]>(`${base}memberships/`, { signal: controller.signal }),
    ])
      .then(([members, relations, accounts]) => {
        if (!controller.signal.aborted) setData({ members, relations, accounts });
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [household.id, page, revision]);

  function reload(message?: string) {
    setEditingMember(null);
    setEditingRelation(null);
    setShowMemberForm(false);
    setShowRelationForm(false);
    setFormRevision((value) => value + 1);
    setNotice(message ?? "");
    setData(null);
    setError("");
    setRevision((value) => value + 1);
    onChanged();
  }

  function changePage(nextPage: number) {
    setData(null);
    setError("");
    setPage(nextPage);
  }

  function denied() {
    refreshAccess();
  }

  if (error)
    return (
      <Panel title="Członkowie gospodarstwa">
        <p className="notice error" role="alert">
          {error}
        </p>
        <Button
          onClick={() => {
            setError("");
            setRevision((value) => value + 1);
          }}
        >
          Spróbuj ponownie
        </Button>
      </Panel>
    );
  if (!data) return <p role="status">Pobieranie członków i relacji…</p>;

  return (
    <div className="stack">
      {notice && (
        <p className="notice success" role="status">
          ✓ {notice}
        </p>
      )}
      <Panel
        title={showRelations ? "Relacje rodzinne" : "Członkowie rodziny"}
        className="family-primary-panel"
        description={
          !canEdit ? "Tryb odczytu. Członków może zmieniać Owner lub Administrator." : undefined
        }
        action={
          <div className="family-heading-actions">
            <Button
              type="button"
              variant="secondary"
              aria-expanded={showRelations}
              aria-controls="family-relations"
              onClick={() => {
                setShowRelations((value) => !value);
                setShowRelationForm(false);
                setEditingRelation(null);
                setShowMemberForm(false);
                setEditingMember(null);
              }}
            >
              {showRelations ? "Wróć do członków" : "Relacje rodzinne"}
            </Button>
            {canEdit && !showMemberForm && !showRelations && (
              <Button
                type="button"
                aria-controls="member-form"
                onClick={() => {
                  setEditingMember(null);
                  setShowMemberForm(true);
                  setNotice("");
                }}
              >
                <Plus size={18} aria-hidden="true" />
                Dodaj członka
              </Button>
            )}
          </div>
        }
      >
        {!showRelations &&
          !showMemberForm &&
          (!data.members.results.length ? (
            <p className="empty">Brak członków. Dodaj pierwszą osobę do gospodarstwa.</p>
          ) : (
            <>
              <div className="member-grid">
                {data.members.results.map((member, index) => {
                  const relation = data.relations.find(
                    (item) => item.id === member.relation_type_id,
                  );
                  const account = data.accounts.find((item) => item.user_id === member.account_id);
                  const linkedSources = sources.filter((source) => source.member_id === member.id);
                  const initials = member.display_name
                    .trim()
                    .split(/\s+/)
                    .slice(0, 2)
                    .map((part) => part[0])
                    .join("")
                    .toUpperCase();
                  return (
                    <article
                      className="member-card"
                      key={member.id}
                      data-tone={index % 3}
                      aria-label={member.display_name}
                    >
                      <div className="member-card-top">
                        <span className="member-avatar" aria-hidden="true">
                          {initials}
                        </span>
                        <span
                          className={member.is_active ? "member-status" : "member-status archived"}
                        >
                          {member.is_active ? "Aktywny" : "Archiwalny"}
                        </span>
                      </div>
                      <h3>{member.display_name}</h3>
                      <p className="member-relation">
                        {relation?.name ?? "Bez przypisanej relacji"}
                      </p>
                      <div className="member-account">
                        {account ? (
                          <Link2 size={18} aria-hidden="true" />
                        ) : (
                          <UserRound size={18} aria-hidden="true" />
                        )}
                        <span>Konto aplikacji</span>
                        <span className="member-account-value">
                          {account?.username ?? "Bez konta"}
                        </span>
                      </div>
                      <div className="member-income">
                        <p className="member-label">Źródła dochodu</p>
                        {linkedSources.length ? (
                          <ul className="source-mini-list">
                            {linkedSources.slice(0, 3).map((source) => (
                              <li key={source.id}>
                                {source.kind === "contract" ? (
                                  <BriefcaseBusiness size={18} aria-hidden="true" />
                                ) : (
                                  <WalletCards size={18} aria-hidden="true" />
                                )}
                                <span>
                                  {source.name}
                                  {!source.is_active && " · Archiwalne"}
                                </span>
                              </li>
                            ))}
                            {linkedSources.length > 3 && (
                              <li className="muted">+ {linkedSources.length - 3} pozostałe</li>
                            )}
                          </ul>
                        ) : (
                          <p className="member-no-income">Nie przypisano źródeł dochodu.</p>
                        )}
                      </div>
                      <div className="member-card-footer">
                        {canEdit && member.is_active ? (
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={() => {
                              setEditingMember(member);
                              setShowMemberForm(true);
                              setNotice("");
                            }}
                          >
                            Edytuj
                          </Button>
                        ) : (
                          <span className="hint">
                            {member.is_active ? "Tryb odczytu" : "Historia zachowana"}
                          </span>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
              <p className="hint family-hint">Członek rodziny może istnieć bez konta aplikacji.</p>
            </>
          ))}
        {!showRelations && !showMemberForm && (
          <Pagination count={data.members.count} page={page} onPage={changePage} />
        )}
      </Panel>

      {canEdit && showMemberForm && (
        <div id="member-form">
          <Panel
            title={editingMember ? `Edycja: ${editingMember.display_name}` : "Dodaj członka"}
            description="Relacja i konto są opcjonalne."
            className="panel-compact-form"
            action={
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setEditingMember(null);
                  setShowMemberForm(false);
                }}
              >
                Anuluj
              </Button>
            }
          >
            <MemberForm
              key={`${editingMember?.id ?? "new"}-${formRevision}`}
              household={household}
              member={editingMember}
              relations={data.relations}
              accounts={data.accounts}
              onDenied={denied}
              onSaved={reload}
            />
            {editingMember && (
              <div className="member-danger-action">
                <ActionForm
                  submit="Dezaktywuj członka"
                  submitVariant="danger"
                  onDenied={denied}
                  action={async () => {
                    if (
                      !window.confirm(
                        `Dezaktywować ${editingMember.display_name}? Historia pozostanie zachowana.`,
                      )
                    )
                      return;
                    await api(
                      householdPath(household.id, `members/${editingMember.id}/deactivate/`),
                      {
                        method: "POST",
                        data: {},
                      },
                    );
                    reload("Członek został oznaczony jako archiwalny.");
                  }}
                >
                  {() => null}
                </ActionForm>
              </div>
            )}
          </Panel>
        </div>
      )}

      {showRelations && (
        <div id="family-relations">
          <Panel
            title="Lista relacji"
            description={
              canEdit
                ? "Relacje opisują członków i są niezależne od uprawnień do aplikacji."
                : "Tryb odczytu. Relacje może zmieniać Owner lub Administrator."
            }
            action={
              canEdit && !showRelationForm ? (
                <Button
                  type="button"
                  onClick={() => {
                    setEditingRelation(null);
                    setShowRelationForm(true);
                  }}
                >
                  Dodaj relację
                </Button>
              ) : undefined
            }
            className="family-relations-panel"
          >
            {!data.relations.length ? (
              <p className="empty">Brak zdefiniowanych relacji rodzinnych.</p>
            ) : (
              <ul className="record-list">
                {data.relations.map((relation) => (
                  <li key={relation.id}>
                    <div>
                      <strong>{relation.name}</strong>
                      <p className="muted">{relation.is_active ? "✓ Aktywna" : "○ Archiwalna"}</p>
                    </div>
                    {canEdit && relation.is_active && (
                      <div className="row-actions">
                        <Button
                          type="button"
                          variant="secondary"
                          onClick={() => {
                            setEditingRelation(relation);
                            setShowRelationForm(true);
                            setNotice("");
                          }}
                        >
                          Edytuj
                        </Button>
                        <ActionForm
                          submit="Dezaktywuj"
                          submitVariant="danger"
                          onDenied={denied}
                          action={async () => {
                            if (
                              !window.confirm(
                                `Dezaktywować relację ${relation.name}? Istniejące powiązania pozostaną w historii.`,
                              )
                            )
                              return;
                            await api(
                              householdPath(
                                household.id,
                                `relation-types/${relation.id}/deactivate/`,
                              ),
                              { method: "POST", data: {} },
                            );
                            reload("Relacja została oznaczona jako archiwalna.");
                          }}
                        >
                          {() => null}
                        </ActionForm>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {canEdit && showRelationForm && (
              <div className="embedded-form">
                <h3>{editingRelation ? `Edycja: ${editingRelation.name}` : "Dodaj relację"}</h3>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => {
                    setEditingRelation(null);
                    setShowRelationForm(false);
                  }}
                >
                  Anuluj
                </Button>
                <RelationForm
                  key={`${editingRelation?.id ?? "new"}-${formRevision}`}
                  household={household}
                  relation={editingRelation}
                  onDenied={denied}
                  onSaved={reload}
                />
              </div>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
}
