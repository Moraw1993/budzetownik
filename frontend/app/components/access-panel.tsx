"use client";

import { useEffect, useRef, useState } from "react";
import {
  api,
  householdPath,
  messageOf,
  roleLabels,
  type Household,
  type Invitation,
  type Membership,
  type Role,
} from "../lib/api";
import { ActionForm, Button, Panel, RoleSelect } from "./ui";

type AccessData = { members: Membership[]; invitations: Invitation[] };

function invitationStatus(invitation: Invitation): string {
  if (invitation.revoked_at) return "Odwołane";
  if (invitation.accepted_at) return "Przyjęte";
  return new Date(invitation.expires_at).getTime() <= Date.now() ? "Wygasłe" : "Aktywne";
}

export function AccessPanel({ household, refresh }: { household: Household; refresh: () => void }) {
  const [data, setData] = useState<AccessData | null>(null);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [link, setLink] = useState("");
  const [copyStatus, setCopyStatus] = useState("");
  const alive = useRef(false);
  const owner = household.role === "owner";
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    Promise.all([
      api<Membership[]>(householdPath(household.id, "memberships/"), options),
      owner
        ? api<Invitation[]>(householdPath(household.id, "invitations/"), options)
        : Promise.resolve([]),
    ])
      .then(([members, invitations]) => {
        if (!controller.signal.aborted) {
          setData({ members, invitations });
          setError("");
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) {
          setData(null);
          setError(messageOf(cause));
        }
      });
    return () => controller.abort();
  }, [household.id, owner, revision]);

  function reloadInvitations() {
    if (alive.current) {
      setData(null);
      setRevision((value) => value + 1);
    }
  }

  function refreshAccess() {
    if (alive.current) refresh();
  }

  if (error)
    return (
      <Panel title="Dostęp do gospodarstwa">
        <p role="alert" className="notice error">
          {error}
        </p>
        <Button onClick={refreshAccess}>Odśwież dostęp</Button>
      </Panel>
    );
  if (!data) return <p role="status">Pobieranie dostępów i zaproszeń…</p>;
  return (
    <div className="stack">
      <Panel
        title="Dostęp użytkowników"
        description={
          owner
            ? "Zarządzaj rolami kont. Role aplikacyjne są niezależne od relacji rodzinnych."
            : "Tryb odczytu. Role i zaproszenia może zmieniać wyłącznie Owner."
        }
      >
        <p className="hint">
          Na wąskim ekranie przewiń tabelę poziomo, aby zobaczyć wszystkie akcje. Możesz też użyć
          klawiszy strzałek po zaznaczeniu tabeli.
        </p>
        <div
          className="table-scroll"
          role="region"
          aria-label="Dostępy użytkowników — tabela przewijana poziomo"
          tabIndex={0}
        >
          <table>
            <caption className="sr-only">Konta z dostępem do gospodarstwa</caption>
            <thead>
              <tr>
                <th scope="col">Użytkownik</th>
                <th scope="col">Rola</th>
                {owner && <th scope="col">Zmiana dostępu</th>}
              </tr>
            </thead>
            <tbody>
              {data.members.map((member) => (
                <tr key={member.id}>
                  <th scope="row">{member.username}</th>
                  <td>
                    <span className="badge">{roleLabels[member.role]}</span>
                  </td>
                  {owner && (
                    <td>
                      <ActionForm
                        submit="Zapisz rolę"
                        onDenied={refreshAccess}
                        action={async (form) => {
                          await api(householdPath(household.id, "memberships/" + member.id + "/"), {
                            method: "PATCH",
                            data: { role: form.get("role") },
                          });
                          refreshAccess();
                        }}
                      >
                        {() => (
                          <RoleSelect
                            key={member.role}
                            initialRole={member.role}
                            label={"Rola użytkownika " + member.username}
                            name="role"
                          />
                        )}
                      </ActionForm>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      {owner && (
        <Panel
          title="Zaproszenia"
          description="Link działa na komputerze, na którym uruchomiona jest aplikacja. Jest jednorazowy i ważny przez 7 dni."
          className="panel-compact-form"
        >
          <ActionForm
            submit="Utwórz zaproszenie"
            onDenied={refreshAccess}
            action={async (form) => {
              const result = await api<Invitation>(householdPath(household.id, "invitations/"), {
                method: "POST",
                data: { role: form.get("role") as Role },
              });
              if (alive.current) {
                setLink(result.invitation_url ?? "");
                setCopyStatus("");
                reloadInvitations();
              }
            }}
          >
            {() => <RoleSelect />}
          </ActionForm>
          {link && (
            <div className="link-box">
              <label htmlFor="invitation-link">Nowy link — skopiuj przed opuszczeniem widoku</label>
              <input
                id="invitation-link"
                readOnly
                value={link}
                onFocus={(event) => event.currentTarget.select()}
              />
              <Button
                variant="secondary"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(link);
                    if (alive.current) setCopyStatus("✓ Link skopiowany.");
                  } catch {
                    if (alive.current)
                      setCopyStatus("Zaznacz link w polu i skopiuj go ręcznie (Ctrl+C).");
                  }
                }}
              >
                Kopiuj link
              </Button>
              <p role="status">{copyStatus}</p>
            </div>
          )}
          {!data.invitations.length ? (
            <p className="empty">Brak zaproszeń. Wybierz rolę i utwórz pierwszy link.</p>
          ) : (
            <ul className="invitation-list">
              {data.invitations.map((invitation) => (
                <li key={invitation.id}>
                  <div>
                    <strong>{roleLabels[invitation.role]}</strong>
                    <p>Ważne do: {new Date(invitation.expires_at).toLocaleString("pl-PL")}</p>
                    <span className="badge">○ {invitationStatus(invitation)}</span>
                  </div>
                  {invitationStatus(invitation) === "Aktywne" && (
                    <ActionForm
                      submit="Odwołaj zaproszenie"
                      onDenied={refreshAccess}
                      action={async () => {
                        if (
                          !window.confirm(
                            "Odwołać to zaproszenie? Link przestanie umożliwiać dołączenie do gospodarstwa.",
                          )
                        )
                          return;
                        await api(
                          householdPath(household.id, "invitations/" + invitation.id + "/"),
                          { method: "DELETE" },
                        );
                        if (alive.current) {
                          setLink("");
                          setCopyStatus("");
                          reloadInvitations();
                        }
                      }}
                    >
                      {() => null}
                    </ActionForm>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      )}
    </div>
  );
}
