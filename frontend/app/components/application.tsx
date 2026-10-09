"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, messageOf, type Household, type User } from "../lib/api";
import { AccountPanel } from "./account-panel";
import { HouseholdShell, type HouseholdSection } from "./household-shell";
import { Button } from "./ui";

type Session = {
  user: User | null;
  setupRequired: boolean;
  households: Household[];
  preferredId?: string;
  preferredSection: HouseholdSection;
};

export function Application({ invitation = false }: { invitation?: boolean }) {
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState("");
  const [resolved, setResolved] = useState(false);
  const [token, setToken] = useState("");
  const invitationToken = useRef("");
  const selectedMembership = useRef<string | undefined>(undefined);
  const selectedSection = useRef<HouseholdSection>("family");
  const generation = useRef(0);
  const editing = useRef(false);
  const onEditing = useCallback((value: boolean) => {
    editing.current = value;
  }, []);
  const controller = useRef<AbortController | null>(null);

  const refresh = useCallback(async (membershipId?: string) => {
    const requestId = ++generation.current;
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setSession(null);
    setError("");
    try {
      const setup = await api<{ setup_required: boolean }>("/auth/setup/", {
        signal: request.signal,
      });
      let user: User | null = null;
      try {
        user = await api<User>("/auth/me/", { signal: request.signal });
      } catch (cause) {
        if (!(cause instanceof ApiError) || ![401, 403].includes(cause.status)) throw cause;
      }
      const households = user
        ? await api<Household[]>("/households/", { signal: request.signal })
        : [];
      if (requestId === generation.current) {
        if (!user) selectedSection.current = "family";
        const selected =
          households.find(
            (item) => item.membership_id === (membershipId ?? selectedMembership.current),
          ) ?? households[0];
        selectedMembership.current = selected?.membership_id;
        setSession({
          user,
          setupRequired: setup.setup_required,
          households,
          preferredId: selected?.id,
          preferredSection: selectedSection.current,
        });
      }
    } catch (cause) {
      if (requestId === generation.current && !request.signal.aborted) setError(messageOf(cause));
    } finally {
      if (requestId === generation.current)
        document.documentElement.classList.remove("session-hidden");
    }
  }, []);

  const invalidate = useCallback(() => {
    generation.current++;
    controller.current?.abort();
  }, []);
  useEffect(() => {
    if (invitation && window.location.hash.length > 1) {
      invitationToken.current = window.location.hash.slice(1);
      window.history.replaceState(null, "", window.location.pathname);
    }
    const start = Promise.resolve().then(() => {
      setToken(invitationToken.current);
      return refresh();
    });
    void start;
    function hide() {
      document.documentElement.classList.add("session-hidden");
    }
    function show(event: PageTransitionEvent) {
      if (event.persisted) void refresh();
    }
    function visibility() {
      if (document.visibilityState === "hidden") hide();
      else if (editing.current) document.documentElement.classList.remove("session-hidden");
      else void refresh();
    }
    window.addEventListener("pagehide", hide);
    window.addEventListener("pageshow", show);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      invalidate();
      window.removeEventListener("pagehide", hide);
      window.removeEventListener("pageshow", show);
      document.removeEventListener("visibilitychange", visibility);
      document.documentElement.classList.remove("session-hidden");
    };
  }, [invitation, refresh, invalidate]);

  async function logout() {
    await api("/auth/logout/", { method: "POST" });
    invitationToken.current = "";
    selectedSection.current = "family";
    setToken("");
    await refresh();
  }

  if (error)
    return (
      <main className="account">
        <h1>Nie można wczytać aplikacji</h1>
        <p role="alert" className="notice error">
          {error}
        </p>
        <Button
          onClick={() => {
            void refresh();
          }}
        >
          Spróbuj ponownie
        </Button>
      </main>
    );
  if (!session)
    return (
      <main className="account">
        <h1>Domowe Finanse</h1>
        <p role="status">Sprawdzanie dostępu…</p>
      </main>
    );
  const pendingInvitation = invitation && !resolved;
  return (
    <div className="session-guard">
      {!session.user || pendingInvitation ? (
        <main>
          <AccountPanel
            setupRequired={session.setupRequired}
            user={session.user}
            invitation={pendingInvitation}
            token={token}
            authenticated={() => refresh()}
            accepted={async (membershipId) => {
              window.history.replaceState(null, "", "/");
              invitationToken.current = "";
              selectedSection.current = "family";
              setToken("");
              setResolved(true);
              await refresh(membershipId);
            }}
          />
        </main>
      ) : (
        <HouseholdShell
          user={session.user}
          households={session.households}
          preferredId={session.preferredId}
          preferredSection={session.preferredSection}
          refresh={refresh}
          logout={logout}
          onEditing={onEditing}
          onSelect={(membershipId) => {
            selectedMembership.current = membershipId;
          }}
          onSectionChange={(section) => {
            selectedSection.current = section;
          }}
        />
      )}
    </div>
  );
}
