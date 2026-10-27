// Carrier detection from a tracking ID. Only India Post for now; add new carriers to RULES.
export const normalizeTrackingId = (raw: string) => raw.toUpperCase().replace(/[\s-]+/g, "");

const RULES: { code: string; label: string; test: RegExp }[] = [
  { code: "india_post", label: "India Post", test: /^[A-Z]{2}\d{9}IN$/ },
];

export function detectCarrier(raw: string) {
  const id = normalizeTrackingId(raw);
  return RULES.find((r) => r.test.test(id)) ?? null;
}
