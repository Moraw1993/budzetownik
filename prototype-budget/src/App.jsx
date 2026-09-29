import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  CalendarDays,
  Car,
  Check,
  ChevronDown,
  ChevronRight,
  CircleEllipsis,
  CreditCard,
  GraduationCap,
  Heart,
  House,
  Landmark,
  LogOut,
  Menu,
  PiggyBank,
  Plus,
  Settings2,
  ShieldCheck,
  ShoppingBasket,
  Sprout,
  Users,
  WalletCards,
  X,
} from "lucide-react";
import "@fontsource-variable/geist";

const INCOME = 14200;
const INITIAL_CATEGORIES = [
  { id: "home", name: "Mieszkanie", amount: 4200, icon: House, color: "purple" },
  { id: "food", name: "Żywność", amount: 2500, icon: ShoppingBasket, color: "blue" },
  { id: "transport", name: "Transport", amount: 1200, icon: Car, color: "blue" },
  { id: "health", name: "Zdrowie", amount: 600, icon: Heart, color: "red" },
  { id: "education", name: "Edukacja", amount: 1000, icon: GraduationCap, color: "blue" },
  { id: "leisure", name: "Rozrywka", amount: 600, icon: CircleEllipsis, color: "purple" },
  { id: "bills", name: "Rachunki", amount: 1000, icon: WalletCards, color: "blue" },
  { id: "other", name: "Inne wydatki", amount: 800, icon: CreditCard, color: "blue" },
  { id: "savings", name: "Oszczędności", amount: 2000, icon: Sprout, color: "green" },
];
const NAVIGATION = [
  ["Gospodarstwa", House],
  ["Przegląd", WalletCards],
  ["Plan miesiąca", CalendarDays],
  ["Dochody", CreditCard],
  ["Kredyty", Landmark],
  ["Cele", PiggyBank],
  ["Raporty", CircleEllipsis],
  ["Ustawienia", Settings2],
];
const formatMoney = (value) => `${new Intl.NumberFormat("pl-PL").format(value)} zł`;

function Sidebar({ section, setSection, mobileOpen, setMobileOpen }) {
  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Zamknij menu"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <span className="brand-mark">
            <House size={21} aria-hidden="true" />
          </span>
          <strong>Domowe Finanse</strong>
        </div>
        <p className="nav-heading">PRZESTRZEŃ DOMOWA</p>
        <nav className="navigation" aria-label="Główna nawigacja">
          {NAVIGATION.map(([label, Icon], index) => (
            <button
              key={label}
              type="button"
              className={`nav-item ${section === label ? "active" : ""} ${index === 7 ? "settings-item" : ""}`}
              aria-current={section === label ? "page" : undefined}
              onClick={() => {
                setSection(label);
                setMobileOpen(false);
              }}
            >
              <Icon size={19} strokeWidth={1.8} aria-hidden="true" />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <ShieldCheck size={19} aria-hidden="true" />
          <span>Twoje dane pozostają w lokalnej instalacji.</span>
        </div>
      </aside>
    </>
  );
}

function Topbar({ section, household, setHousehold, onMenu, onLogout }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="mobile-menu icon-button"
          type="button"
          aria-label="Otwórz menu"
          onClick={onMenu}
        >
          <Menu size={21} aria-hidden="true" />
        </button>
        <span className="breadcrumb">
          Gospodarstwa / {household} / {section}
        </span>
        <label className="household-switcher">
          <House size={17} aria-hidden="true" />
          <span className="sr-only">Aktywne gospodarstwo</span>
          <select value={household} onChange={(event) => setHousehold(event.target.value)}>
            <option>Dom rodzinny</option>
            <option>Dom rodziców</option>
          </select>
          <ChevronDown size={16} aria-hidden="true" />
        </label>
      </div>
      <div className="topbar-right">
        <span>arek</span>
        <button
          className="icon-button"
          type="button"
          aria-label="Informacja o wylogowaniu"
          onClick={onLogout}
        >
          <LogOut size={17} aria-hidden="true" />
        </button>
        <button className="primary-button logout-button" type="button" onClick={onLogout}>
          Wyloguj się
        </button>
      </div>
    </header>
  );
}

function BudgetSummary({ allocated, onAllocate }) {
  const remaining = INCOME - allocated;
  const percent = Math.min((allocated / INCOME) * 100, 100);
  return (
    <section className="summary-panel" aria-label="Podsumowanie planu miesiąca">
      <div className="summary-grid">
        <div className="summary-stat">
          <span>Dochód w miesiącu</span>
          <strong>{formatMoney(INCOME)}</strong>
          <small>Z 2 źródeł dochodu</small>
        </div>
        <div className="summary-stat">
          <span>Rozdysponowano</span>
          <strong>{formatMoney(allocated)}</strong>
          <small>{percent.toFixed(1).replace(".", ",")}% budżetu</small>
        </div>
        <div className="summary-stat">
          <span>Pozostało do rozdysponowania</span>
          <strong className={remaining < 0 ? "danger-text" : "success-text"}>
            {formatMoney(remaining)}
          </strong>
          <small>
            {Math.abs(100 - percent)
              .toFixed(1)
              .replace(".", ",")}
            % budżetu
          </small>
        </div>
        <button type="button" className="primary-button summary-action" onClick={onAllocate}>
          {remaining > 0 ? `Rozdysponuj ${formatMoney(remaining)}` : "Zmień plan"}
        </button>
      </div>
      <div
        className="progress-track"
        role="progressbar"
        aria-label="Rozdysponowanie budżetu"
        aria-valuenow={allocated}
        aria-valuemin={0}
        aria-valuemax={INCOME}
      >
        <span style={{ width: `${percent}%` }} />
      </div>
      <div className="progress-labels">
        <span>{percent.toFixed(1).replace(".", ",")}%</span>
        <span>
          {Math.max(100 - percent, 0)
            .toFixed(1)
            .replace(".", ",")}
          %
        </span>
      </div>
    </section>
  );
}

function CategoryTable({ categories, onAdd, onEdit }) {
  return (
    <section className="category-panel">
      <div className="section-heading">
        <h2>Kategorie budżetowe</h2>
        <button type="button" className="outline-button" onClick={onAdd}>
          <Plus size={17} aria-hidden="true" />
          Dodaj kategorię
        </button>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Kategoria</th>
              <th>Planowana kwota</th>
              <th>Udział w budżecie</th>
              <th>Status</th>
              <th>
                <span className="sr-only">Akcja</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {categories.map((item) => {
              const Icon = item.icon;
              return (
                <tr key={item.id}>
                  <td>
                    <span className={`category-icon ${item.color}`}>
                      <Icon size={21} aria-hidden="true" />
                    </span>
                    <strong className="category-name">{item.name}</strong>
                  </td>
                  <td>{formatMoney(item.amount)}</td>
                  <td>{((item.amount / INCOME) * 100).toFixed(1).replace(".", ",")}%</td>
                  <td>
                    <span className="status-pill">
                      <Check size={13} aria-hidden="true" />
                      Zaplanowano
                    </span>
                  </td>
                  <td>
                    <button
                      className="row-button"
                      type="button"
                      aria-label={`Edytuj kategorię ${item.name}`}
                      onClick={() => onEdit(item)}
                    >
                      <ChevronRight size={18} aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SidePanels({ onLoan, onGoal }) {
  return (
    <aside className="insight-column" aria-label="Dodatkowe informacje">
      <section className="insight-panel">
        <div className="insight-heading">
          <h2>Najbliższa rata</h2>
          <button type="button" className="text-button" onClick={onLoan}>
            Zobacz wszystkie
          </button>
        </div>
        <button type="button" className="loan-tile" onClick={onLoan}>
          <span className="tile-icon">
            <Landmark size={23} aria-hidden="true" />
          </span>
          <span className="loan-copy">
            <strong>Kredyt hipoteczny</strong>
            <small>Rata miesięczna</small>
            <b>2 450 zł</b>
            <small>1 października 2026</small>
          </span>
          <span className="due-pill">Za 8 dni</span>
        </button>
      </section>
      <section className="insight-panel">
        <div className="insight-heading">
          <h2>Cel oszczędnościowy</h2>
          <button type="button" className="text-button" onClick={onGoal}>
            Edytuj
          </button>
        </div>
        <div className="goal-tile">
          <div className="goal-heading">
            <span className="tile-icon">
              <PiggyBank size={24} aria-hidden="true" />
            </span>
            <span className="goal-copy">
              <strong>Wakacje 2027</strong>
              <small>12 000 zł</small>
            </span>
          </div>
          <div className="goal-progress">
            <span />
          </div>
          <div className="goal-labels">
            <span>Zebrano 7 000 zł</span>
            <span>Do celu 5 000 zł</span>
          </div>
        </div>
        <p className="info-note">Oszczędności są częścią Twojego planu miesięcznego.</p>
      </section>
    </aside>
  );
}

function EditDialog({ dialog, categories, remaining, onClose, onSave }) {
  const [name, setName] = useState(dialog.category?.name ?? "");
  const [amount, setAmount] = useState(
    String(dialog.mode === "allocate" ? Math.max(remaining, 0) : (dialog.category?.amount ?? "")),
  );
  const [target, setTarget] = useState(categories[0]?.id ?? "");
  const [error, setError] = useState("");
  const firstField = useRef(null);
  useEffect(() => {
    firstField.current?.focus();
  }, []);
  useEffect(() => {
    const escape = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [onClose]);
  const title =
    dialog.mode === "allocate"
      ? "Rozdysponuj środki"
      : dialog.mode === "add"
        ? "Dodaj kategorię"
        : "Edytuj kategorię";
  function submit(event) {
    event.preventDefault();
    const value = Number(amount);
    if (!Number.isInteger(value) || value < 0 || (dialog.mode === "add" && value === 0))
      return setError("Podaj kwotę w pełnych złotych większą od zera.");
    if (dialog.mode === "allocate" && value > remaining)
      return setError(`Możesz rozdysponować maksymalnie ${formatMoney(remaining)}.`);
    if (dialog.mode === "add" && !name.trim()) return setError("Podaj nazwę kategorii.");
    onSave({
      mode: dialog.mode,
      amount: value,
      target,
      name: name.trim(),
      categoryId: dialog.category?.id,
    });
  }
  return (
    <div
      className="dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="edit-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
        <div className="dialog-heading">
          <div>
            <p className="eyebrow">PLAN MIESIĄCA</p>
            <h2 id="dialog-title">{title}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Zamknij">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        <p className="dialog-description">
          {dialog.mode === "allocate"
            ? `Do rozdysponowania pozostało ${formatMoney(remaining)}.`
            : "Kwota opisuje plan miesiąca, nie faktyczny wydatek."}
        </p>
        <form onSubmit={submit}>
          {dialog.mode === "allocate" && (
            <label className="form-field">
              Kategoria
              <select
                ref={firstField}
                value={target}
                onChange={(event) => setTarget(event.target.value)}
              >
                {categories.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {dialog.mode === "add" && (
            <label className="form-field">
              Nazwa kategorii
              <input
                ref={firstField}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Np. Prezenty"
                maxLength={40}
              />
            </label>
          )}
          <label className="form-field">
            {dialog.mode === "allocate" ? "Kwota do rozdysponowania" : "Planowana kwota"}
            <span className="amount-input">
              <input
                ref={dialog.mode === "edit" ? firstField : undefined}
                type="number"
                min="0"
                step="1"
                inputMode="numeric"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
              <span>zł</span>
            </span>
          </label>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="dialog-actions">
            <button type="button" className="outline-button" onClick={onClose}>
              Anuluj
            </button>
            <button type="submit" className="primary-button">
              {dialog.mode === "allocate" ? "Przypisz środki" : "Zapisz"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SectionPreview({ section, onBack }) {
  const sections = {
    Gospodarstwa: [
      "Dom rodzinny",
      "Przykładowe gospodarstwo używane w makiecie.",
      Users,
      [
        ["Waluta", "PLN"],
        ["Członkowie", "2 osoby"],
        ["Rola", "Właściciel"],
      ],
    ],
    Przegląd: [
      "Przegląd finansów",
      "Najważniejsze wartości we wrześniu 2026.",
      WalletCards,
      [
        ["Dochód miesięczny", "14 200 zł"],
        ["Plan miesiąca", "13 900 zł"],
        ["Pozostało", "300 zł"],
      ],
    ],
    Dochody: [
      "Dochody",
      "Przykładowe źródła dochodu w tym miesiącu.",
      CreditCard,
      [
        ["Wynagrodzenie", "11 200 zł"],
        ["Pozostałe dochody", "3 000 zł"],
        ["Razem", "14 200 zł"],
      ],
    ],
    Kredyty: [
      "Kredyty",
      "Najbliższa zaplanowana rata.",
      Landmark,
      [
        ["Kredyt hipoteczny", "2 450 zł"],
        ["Termin", "1 października 2026"],
        ["Status", "Planowana"],
      ],
    ],
    Cele: [
      "Cele oszczędnościowe",
      "Postęp celu Wakacje 2027.",
      PiggyBank,
      [
        ["Cel", "12 000 zł"],
        ["Zebrano", "7 000 zł"],
        ["Do celu", "5 000 zł"],
      ],
    ],
    Raporty: [
      "Raporty",
      "Podstawowy odczyt planu na wrzesień 2026.",
      CircleEllipsis,
      [
        ["Dochód", "14 200 zł"],
        ["Rozdysponowano", "13 900 zł"],
        ["Udział", "97,9%"],
      ],
    ],
    Ustawienia: [
      "Ustawienia",
      "Kontekst przykładowego gospodarstwa.",
      Settings2,
      [
        ["Nazwa", "Dom rodzinny"],
        ["Waluta", "PLN"],
        ["Tryb", "Makieta demonstracyjna"],
      ],
    ],
  };
  const [title, description, Icon, rows] = sections[section];
  return (
    <main className="content section-preview">
      <p className="eyebrow">GOSPODARSTWO</p>
      <h1>{title}</h1>
      <p className="page-subtitle">{description}</p>
      <section className="preview-panel">
        <span className="preview-icon">
          <Icon size={28} aria-hidden="true" />
        </span>
        <div className="preview-rows">
          {rows.map(([label, value]) => (
            <div className="preview-row" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
        <button type="button" className="primary-button" onClick={onBack}>
          Wróć do planu miesiąca <ArrowRight size={17} aria-hidden="true" />
        </button>
      </section>
    </main>
  );
}

export function App() {
  const [section, setSection] = useState("Plan miesiąca");
  const [household, setHousehold] = useState("Dom rodzinny");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [categories, setCategories] = useState(INITIAL_CATEGORIES);
  const [dialog, setDialog] = useState(null);
  const [notice, setNotice] = useState("");
  const allocated = categories.reduce((sum, item) => sum + item.amount, 0);
  function saveDialog({ mode, amount, target, name, categoryId }) {
    if (mode === "allocate")
      setCategories((items) =>
        items.map((item) =>
          item.id === target ? { ...item, amount: item.amount + amount } : item,
        ),
      );
    if (mode === "add")
      setCategories((items) => [
        ...items,
        { id: `custom-${Date.now()}`, name, amount, icon: CircleEllipsis, color: "blue" },
      ]);
    if (mode === "edit")
      setCategories((items) =>
        items.map((item) => (item.id === categoryId ? { ...item, amount } : item)),
      );
    setDialog(null);
    setNotice("Plan miesiąca został zaktualizowany.");
  }
  return (
    <div className="app-shell">
      <Sidebar
        section={section}
        setSection={setSection}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />
      <div className="workspace">
        <Topbar
          section={section}
          household={household}
          setHousehold={setHousehold}
          onMenu={() => setMobileOpen(true)}
          onLogout={() => setNotice("To makieta demonstracyjna. Wylogowanie nie jest dostępne.")}
        />
        {section === "Plan miesiąca" ? (
          <main className="content">
            <div className="page-header">
              <div>
                <p className="eyebrow">PLAN MIESIĄCA</p>
                <h1>Budżet · wrzesień 2026</h1>
                <p className="page-subtitle">
                  Rozdziel dochody na kategorie i zaplanuj cały miesiąc.
                </p>
              </div>
              <p className="current-date">
                <CalendarDays size={18} aria-hidden="true" />
                środa, 23 września 2026
              </p>
            </div>
            <BudgetSummary
              allocated={allocated}
              onAllocate={() => setDialog({ mode: "allocate" })}
            />
            <div className="content-grid">
              <CategoryTable
                categories={categories}
                onAdd={() => setDialog({ mode: "add" })}
                onEdit={(category) => setDialog({ mode: "edit", category })}
              />
              <SidePanels onLoan={() => setSection("Kredyty")} onGoal={() => setSection("Cele")} />
            </div>
          </main>
        ) : (
          <SectionPreview section={section} onBack={() => setSection("Plan miesiąca")} />
        )}
      </div>
      {notice && (
        <div className="toast" role="status">
          <Check size={17} aria-hidden="true" />
          {notice}
          <button type="button" aria-label="Zamknij powiadomienie" onClick={() => setNotice("")}>
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      )}
      {dialog && (
        <EditDialog
          key={`${dialog.mode}-${dialog.category?.id ?? "new"}`}
          dialog={dialog}
          categories={categories}
          remaining={INCOME - allocated}
          onClose={() => setDialog(null)}
          onSave={saveDialog}
        />
      )}
    </div>
  );
}
