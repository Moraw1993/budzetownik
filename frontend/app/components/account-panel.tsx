"use client";
import Link from "next/link";

import { useState } from "react";
import { api, ApiError, type Membership, type User } from "../lib/api";
import { ActionForm, Button, Field, Panel } from "./ui";

export function AccountPanel({
  setupRequired,
  user,
  invitation,
  token,
  authenticated,
  accepted,
}: {
  setupRequired: boolean;
  user: User | null;
  invitation: boolean;
  token: string;
  authenticated: () => Promise<void>;
  accepted: (membershipId: string) => Promise<void>;
}) {
  const [newAccount, setNewAccount] = useState(false);
  const register = setupRequired || (invitation && newAccount);
  const title = invitation
    ? "Dołącz do gospodarstwa"
    : setupRequired
      ? "Utwórz pierwsze konto"
      : "Zaloguj się";
  async function accept(credentials?: {
    username: FormDataEntryValue | null;
    password: FormDataEntryValue | null;
  }) {
    let membership: Membership;
    try {
      membership = await api<Membership>("/invitations/accept/", {
        method: "POST",
        data: { token, ...credentials },
      });
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 400 && !Object.keys(cause.fields).length) {
        throw new ApiError(
          400,
          "Zaproszenie jest nieprawidłowe, wygasłe, odwołane lub już użyte. Poproś Ownera o nowy link.",
        );
      }
      throw cause;
    }
    await accepted(membership.id);
  }

  return (
    <div className="account">
      <p className="eyebrow">DOMOWE FINANSE / DOSTĘP</p>
      <h1>{title}</h1>
      <p className="muted">
        {invitation
          ? "Link jest jednorazowy. Działa na komputerze z uruchomioną aplikacją."
          : "Konto umożliwia dostęp do Twoich gospodarstw domowych."}
      </p>
      <Panel
        title={user ? "Potwierdź dołączenie" : register ? "Dane nowego konta" : "Dane logowania"}
      >
        {invitation && !token ? (
          <p role="alert" className="notice error">
            Brakuje tokenu zaproszenia. Otwórz ponownie pełny link otrzymany od Ownera.
          </p>
        ) : user ? (
          <>
            <p>
              Dołączasz jako <strong>{user.username}</strong>.
            </p>
            <ActionForm
              submit="Przyjmij zaproszenie"
              action={() => accept()}
              onDenied={() => {
                void authenticated();
              }}
            >
              {() => null}
            </ActionForm>
          </>
        ) : (
          <>
            <ActionForm
              key={register ? "register" : "login"}
              submit={
                register ? (invitation ? "Utwórz konto i dołącz" : "Utwórz konto") : "Zaloguj się"
              }
              action={async (data) => {
                const credentials = {
                  username: data.get("username"),
                  password: data.get("password"),
                };
                if (invitation && register) await accept(credentials);
                else {
                  await api(register ? "/auth/setup/" : "/auth/login/", {
                    method: "POST",
                    data: credentials,
                  });
                  await authenticated();
                }
              }}
            >
              {(fields) => (
                <>
                  <Field
                    label="Login"
                    name="username"
                    autoComplete="username"
                    maxLength={150}
                    required
                    error={fields.username}
                  />
                  <Field
                    label="Hasło"
                    name="password"
                    type="password"
                    autoComplete={register ? "new-password" : "current-password"}
                    maxLength={128}
                    required
                    error={fields.password}
                  />
                  {register && (
                    <p className="hint">
                      Użyj co najmniej 12 znaków. Hasło nie może być zbyt popularne, wyłącznie
                      numeryczne ani podobne do loginu.
                    </p>
                  )}
                </>
              )}
            </ActionForm>
            {invitation && !setupRequired && (
              <Button variant="secondary" onClick={() => setNewAccount((value) => !value)}>
                {newAccount ? "Mam już konto — zaloguj się" : "Nie mam konta — utwórz konto"}
              </Button>
            )}
          </>
        )}
      </Panel>
      <p className="hint">
        Nie pamiętasz hasła? Operator tej instalacji może przywrócić dostęp zgodnie z instrukcją
        odzyskiwania konta w README projektu.
      </p>
      {invitation && <Link href="/">Wróć do gospodarstw</Link>}
    </div>
  );
}
