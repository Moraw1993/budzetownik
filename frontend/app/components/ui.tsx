"use client";

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { useEffect, useId, useRef, useState, type ComponentProps, type ReactNode } from "react";
import { ApiError, messageOf, roleLabels, type Role } from "../lib/api";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const buttonVariants = cva("button", {
  variants: {
    variant: { primary: "button-primary", secondary: "button-secondary", danger: "button-danger" },
  },
  defaultVariants: { variant: "primary" },
});

// shadcn-style button: native button semantics with Radix composition.
export function Button({
  className,
  variant,
  asChild = false,
  ...props
}: ComponentProps<"button"> & VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Component = asChild ? Slot : "button";
  return <Component className={cn(buttonVariants({ variant }), className)} {...props} />;
}

export function Field({
  label,
  error,
  ...props
}: ComponentProps<"input"> & { label: string; error?: string }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? id + "-error" : undefined}
      />
      {error && (
        <span id={id + "-error"} className="field-error">
          {error}
        </span>
      )}
    </div>
  );
}

export function SelectField({
  label,
  error,
  children,
  ...props
}: ComponentProps<"select"> & { label: string; error?: string }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? id + "-error" : undefined}
      >
        {children}
      </select>
      {error && (
        <span id={id + "-error"} className="field-error">
          {error}
        </span>
      )}
    </div>
  );
}

export function TextAreaField({
  label,
  error,
  ...props
}: ComponentProps<"textarea"> & { label: string; error?: string }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <textarea
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? id + "-error" : undefined}
      />
      {error && (
        <span id={id + "-error"} className="field-error">
          {error}
        </span>
      )}
    </div>
  );
}

export function RoleSelect({
  name = "role",
  initialRole = "viewer",
  label = "Rola aplikacyjna",
  value,
  onChange,
  disabled,
}: {
  name?: string;
  initialRole?: Role;
  label?: string;
  value?: Role;
  onChange?: (value: Role) => void;
  disabled?: boolean;
}) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        name={name}
        value={value}
        defaultValue={value ? undefined : initialRole}
        onChange={onChange ? (e) => onChange(e.target.value as Role) : undefined}
        disabled={disabled}
      >
        {Object.entries(roleLabels).map(([role, label]) => (
          <option key={role} value={role}>
            {label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function ActionForm({
  action,
  children,
  submit,
  submitVariant = "primary",
  onDenied,
  success,
  onPendingChange,
}: {
  action: (data: FormData) => Promise<void>;
  children: (fields: Record<string, string>, pending: boolean) => ReactNode;
  submit: string;
  submitVariant?: "primary" | "secondary" | "danger";
  onDenied?: () => void;
  success?: string;
  onPendingChange?: (pending: boolean) => void;
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [fields, setFields] = useState<Record<string, string>>({});
  const alive = useRef(true);
  const locked = useRef(false);
  const errorRef = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);
  useEffect(() => {
    onPendingChange?.(pending);
    return () => onPendingChange?.(false);
  }, [pending, onPendingChange]);
  return (
    <form
      onSubmit={async (event) => {
        event.preventDefault();
        if (locked.current) return;
        locked.current = true;
        const form = event.currentTarget;
        const data = new FormData(form);
        setPending(true);
        setError("");
        setFields({});
        setDone(false);
        try {
          await action(data);
          if (alive.current) setDone(true);
        } catch (cause) {
          if (!alive.current) return;
          setError(messageOf(cause));
          if (cause instanceof ApiError) {
            setFields(cause.fields);
            if ([401, 403, 404].includes(cause.status)) onDenied?.();
          }
        } finally {
          form.querySelectorAll<HTMLInputElement>('input[type="password"]').forEach((input) => {
            input.value = "";
          });
          locked.current = false;
          if (alive.current) setPending(false);
        }
      }}
      aria-busy={pending}
    >
      {error && (
        <p className="notice error" role="alert" tabIndex={-1} ref={errorRef}>
          {error}
        </p>
      )}
      {done && success && (
        <p className="notice success" role="status">
          ✓ {success}
        </p>
      )}
      <fieldset disabled={pending}>
        {children(fields, pending)}
        <Button type="submit" variant={submitVariant} disabled={pending}>
          {pending ? "Trwa zapisywanie…" : submit}
        </Button>
      </fieldset>
    </form>
  );
}

export function Panel({
  title,
  children,
  description,
  className,
  action,
}: {
  title: string;
  children: ReactNode;
  description?: string;
  className?: string;
  action?: ReactNode;
}) {
  return (
    <section className={cn("panel", className)}>
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {description && <p className="muted">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function Pagination({
  count,
  page,
  onPage,
  pageSize = 50,
}: {
  count: number;
  page: number;
  onPage: (page: number) => void;
  pageSize?: number;
}) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  if (pages === 1) return null;
  return (
    <nav className="pagination" aria-label="Stronicowanie listy">
      <Button
        type="button"
        variant="secondary"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      >
        Poprzednia
      </Button>
      <span aria-live="polite">
        Strona {page} z {pages}
      </span>
      <Button
        type="button"
        variant="secondary"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
      >
        Następna
      </Button>
    </nav>
  );
}
