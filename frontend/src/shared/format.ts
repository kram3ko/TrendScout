const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const compact = new Intl.NumberFormat("en-US", { notation: "compact" });
const dateTime = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" });

export function formatPrice(value: number | null): string {
  return value === null ? "—" : currency.format(value);
}

export function formatCount(value: number | null): string {
  return value === null ? "—" : compact.format(value);
}

export function formatDate(value: string | null): string {
  return value === null ? "—" : dateTime.format(new Date(value));
}
