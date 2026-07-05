// ₹ formatting helpers — Indian digit grouping (lakh / crore), never $.

/** Full rupee value with Indian grouping, e.g. 186768 -> "₹1,86,768". */
export function inr(n) {
  const v = Math.round(Number(n) || 0);
  return "₹" + v.toLocaleString("en-IN");
}

/** Compact rupee value using Indian units: K (thousand), L (lakh), Cr (crore). */
export function inrCompact(n) {
  const v = Number(n) || 0;
  const abs = Math.abs(v);
  if (abs >= 1e7) return "₹" + trim(v / 1e7) + "Cr";
  if (abs >= 1e5) return "₹" + trim(v / 1e5) + "L";
  if (abs >= 1e3) return "₹" + trim(v / 1e3) + "K";
  return "₹" + Math.round(v).toLocaleString("en-IN");
}

/** Plain integer with Indian grouping (no ₹), e.g. views/counts. */
export function num(n) {
  return (Math.round(Number(n) || 0)).toLocaleString("en-IN");
}

function trim(x) {
  // one decimal place, but drop a trailing ".0"
  return (Math.round(x * 10) / 10).toString();
}
