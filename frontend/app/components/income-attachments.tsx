"use client";
import { useEffect, useEffectEvent, useRef, useState } from "react";
import { api, ApiError, messageOf } from "../lib/api";
import { formatMoney } from "../lib/money";
import {
  attachmentList,
  canManage,
  downloadFile,
  incomePath,
  uncertain,
  uploadFiles,
  validateFiles,
  type Attachment,
  type Income,
  type PeriodContext,
} from "../lib/periods-api";
import { type EditGuard } from "./income-form";
import { Button, Field, Panel } from "./ui";
import { ConfirmAction, LoadError } from "./periods-common";

export function IncomeAttachments({
  context,
  income,
  initialFiles,
  onGuard,
  onRecheck,
}: {
  context: PeriodContext;
  income: Income;
  initialFiles: File[];
  onGuard: (guard: EditGuard) => void;
  onRecheck: () => void;
}) {
  const [data, setData] = useState<Attachment[] | null>(null);
  const [queue, setQueue] = useState(initialFiles);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(
    initialFiles.length ? "Przychód zapisany. Trwa dodawanie załączników." : "",
  );
  const [unknown, setUnknown] = useState(false);
  const [checked, setChecked] = useState(false);
  const [retryConfirm, setRetryConfirm] = useState(false);
  const [deleting, setDeleting] = useState<Attachment | null>(null);
  const [revision, setRevision] = useState(0);
  const [blocked, setBlocked] = useState(false);
  const lock = useRef(false);
  const autoStarted = useRef(false);
  const listGeneration = useRef(0);
  const lifetime = useRef<AbortController | null>(null);
  const writable = canManage(context.household) && context.month.state === "active" && !blocked;
  useEffect(() => {
    const controller = new AbortController();
    const generation = listGeneration.current;
    attachmentList(context, income.id, controller.signal)
      .then((reply) => {
        if (!controller.signal.aborted) {
          setData(reply);
          if (generation === listGeneration.current && generation > 0) setChecked(true);
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(messageOf(cause));
      });
    return () => controller.abort();
  }, [context, income.id, revision]);
  async function upload(signal = lifetime.current?.signal) {
    if (lock.current || !writable) return;
    lock.current = true;
    setPending(true);
    setError("");
    setRetryConfirm(false);
    try {
      await uploadFiles(context, income.id, queue, signal);
      if (signal?.aborted) return;
      setQueue([]);
      setUnknown(false);
      setNotice("Dodano załączniki.");
      setRevision((value) => value + 1);
    } catch (cause) {
      if (signal?.aborted) return;
      if (cause instanceof ApiError && [401, 403, 404].includes(cause.status)) setBlocked(true);
      setError(messageOf(cause));
      setNotice("Przychód zapisany, załączniki nie zostały potwierdzone.");
      if (uncertain(cause)) {
        listGeneration.current++;
        setUnknown(true);
        setChecked(false);
      }
      onRecheck();
    } finally {
      lock.current = false;
      if (!signal?.aborted) setPending(false);
    }
  }
  const startUpload = useEffectEvent((signal: AbortSignal) => {
    void upload(signal);
  });
  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    // Defer until after the Strict Mode setup/cleanup cycle; never replay an upload.
    void Promise.resolve().then(() => {
      if (!controller.signal.aborted && initialFiles.length && !autoStarted.current) {
        autoStarted.current = true;
        startUpload(controller.signal);
      }
    });
    return () => controller.abort();
  }, [initialFiles.length]);
  useEffect(() => {
    onGuard({ dirty: queue.length > 0, busy: pending, unknown: false });
    return () => onGuard({ dirty: false, busy: false, unknown: false });
  }, [queue, pending, onGuard]);
  useEffect(() => {
    if (!queue.length) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [queue]);
  async function remove() {
    if (!deleting || lock.current) return;
    lock.current = true;
    setPending(true);
    setError("");
    try {
      await api(incomePath(context, income.id, `attachments/${deleting.id}/`), {
        method: "DELETE",
        data: {},
        signal: lifetime.current?.signal,
      });
      setDeleting(null);
      setNotice("Usunięto załącznik.");
      setRevision((value) => value + 1);
    } catch (cause) {
      if (cause instanceof ApiError && [401, 403, 404].includes(cause.status)) setBlocked(true);
      setError(messageOf(cause));
      onRecheck();
      setRevision((value) => value + 1);
    } finally {
      lock.current = false;
      setPending(false);
    }
  }
  return (
    <div className="stack">
      <Panel
        title={`${income.recipient_snapshot.label} · ${income.source_snapshot.name}`}
        description="Załączniki przychodu"
      >
        <p className="period-amount">{formatMoney(income.amount, income.currency)}</p>
        <p>Data otrzymania: {income.receipt_date}</p>
      </Panel>
      {notice && (
        <p className="notice success" role="status">
          {notice}
        </p>
      )}
      {unknown && (
        <Panel
          title="Nie znamy wyniku dodawania plików"
          description="Sprawdź listę przed ponowieniem. Zgodna nazwa i rozmiar nie potwierdzają, że to ten sam plik."
        >
          <div className="row-actions">
            <Button
              type="button"
              variant="secondary"
              disabled={pending}
              onClick={() => {
                listGeneration.current++;
                setError("");
                setRevision((value) => value + 1);
              }}
            >
              Sprawdź listę
            </Button>
            {checked && (
              <Button
                type="button"
                variant="secondary"
                disabled={pending}
                onClick={() => {
                  setQueue([]);
                  setUnknown(false);
                  setNotice("Zakończono sprawdzanie. Lista pokazuje zapisane pliki.");
                }}
              >
                Zakończ bez ponowienia
              </Button>
            )}
          </div>
        </Panel>
      )}
      {retryConfirm && (
        <ConfirmAction
          title="Ponowić dodawanie tych plików?"
          description="Poprzednia próba mogła się udać. Sprawdzono listę; ponowienie może dodać duplikaty."
          confirm="Świadomie ponów dodawanie"
          pending={pending}
          onConfirm={() => void upload()}
          onCancel={() => setRetryConfirm(false)}
        />
      )}
      {deleting && (
        <ConfirmAction
          variant="danger"
          title="Usuń załącznik"
          description={deleting.original_name}
          confirm="Usuń załącznik"
          pending={pending}
          error={error}
          onConfirm={() => void remove()}
          onCancel={() => setDeleting(null)}
        />
      )}
      <Panel
        title="Zapisane załączniki"
        description="Pliki są prywatne i dostępne dla uprawnionych członków gospodarstwa."
      >
        {error && (
          <LoadError
            error={error}
            retry={() => {
              setError("");
              setRevision((value) => value + 1);
            }}
          />
        )}
        {data === null ? (
          <p role="status">Pobieranie załączników…</p>
        ) : !data.length ? (
          <p className="empty">Brak zapisanych załączników.</p>
        ) : (
          <ul className="period-files">
            {data.map((file) => (
              <li key={file.id}>
                <div>
                  <strong className="period-file-name">{file.original_name}</strong>
                  <p className="muted">
                    {file.media_type} · {(file.size_bytes / 1024 ** 2).toFixed(2)} MiB
                  </p>
                </div>
                <div className="row-actions">
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={pending}
                    onClick={() => {
                      void downloadFile(context, income.id, file, lifetime.current?.signal).catch(
                        (cause) => setError(messageOf(cause)),
                      );
                    }}
                  >
                    Pobierz
                  </Button>
                  {writable && (
                    <Button
                      type="button"
                      variant="danger"
                      disabled={pending}
                      onClick={() => setDeleting(file)}
                    >
                      Usuń
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>
      {writable ? (
        <Panel
          title="Dodaj pliki"
          description="PNG, JPG, JPEG lub PDF. 1–5 plików w partii, do 10 MiB na plik i 25 MiB na partię. Limit przychodu: 20 plików i 50 MiB."
        >
          <Field
            label="Wybierz pliki"
            type="file"
            multiple
            accept=".png,.jpg,.jpeg,.pdf"
            disabled={pending || unknown}
            onChange={(event) => {
              const files = Array.from(event.target.files ?? []);
              const issue = files.length ? validateFiles(files, data ?? []) : "";
              if (issue) {
                setError(issue);
                event.target.value = "";
                return;
              }
              setQueue(files);
              setError("");
            }}
          />
          {!!queue.length && (
            <>
              <h3>Oczekujące pliki</h3>
              <ul>
                {queue.map((file, index) => (
                  <li key={index} className="period-file-name">
                    {file.name} · oczekuje na zapis
                  </li>
                ))}
              </ul>
              <div className="row-actions">
                <Button
                  type="button"
                  disabled={pending || (unknown && !checked)}
                  onClick={() => (unknown ? setRetryConfirm(true) : void upload())}
                >
                  {pending
                    ? "Dodawanie plików…"
                    : unknown
                      ? "Ponów po sprawdzeniu listy"
                      : "Dodaj pliki"}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={pending || unknown}
                  onClick={() => setQueue([])}
                >
                  Wyczyść kolejkę
                </Button>
              </div>
            </>
          )}
        </Panel>
      ) : (
        <p className="notice warning">
          Tylko odczyt. Dodawanie i usuwanie plików wymaga aktywnego miesiąca oraz roli Ownera lub
          Administratora.
        </p>
      )}
      {blocked && (
        <Button type="button" onClick={() => setBlocked(false)}>
          Sprawdź dostęp ponownie
        </Button>
      )}
    </div>
  );
}
