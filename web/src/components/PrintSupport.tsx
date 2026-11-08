"use client";

import { usePrintSupport } from "@/lib/print";

/** Gets the page ready when someone prints from the browser's own menu. */
export function PrintSupport() {
  usePrintSupport();
  return null;
}
