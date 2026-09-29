const DECIMAL_VALUE = /^(\d+)(?:[.,](\d{1,2}))?$/;

export function normalizeDecimal(value: string): string {
  const normalized = value.trim().replaceAll(" ", "").replace(",", ".");
  if (!DECIMAL_VALUE.test(normalized)) return normalized;
  const [integer, fraction = ""] = normalized.split(".");
  return fraction ? `${integer}.${fraction.padEnd(2, "0")}` : `${integer}.00`;
}

export function formatMoney(value: string, currency: string): string {
  const match = DECIMAL_VALUE.exec(value);
  if (!match) return `${value} ${currency}`;
  const integer = match[1].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const fraction = (match[2] ?? "").padEnd(2, "0");
  return `${integer},${fraction} ${currency}`;
}
