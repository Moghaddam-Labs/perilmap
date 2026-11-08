"use client";

import { useEffect } from "react";
import { flushSync } from "react-dom";

/**
 * Getting the page ready to print or save as a PDF. Parts of the page register what they need to
 * do, such as copying the map into an image, and each returns how to undo it afterwards.
 */

type Undo = void | (() => void);

/**
 * `canWait` is true when printing from PerilMap's own button, which can wait for slow work such as
 * the map redrawing. Printing from the browser's menu can't wait, so preparers do what they can at once.
 */
type Preparer = (options: { canWait: boolean }) => Undo | Promise<Undo>;

const preparers = new Set<Preparer>();
let restoreActive: (() => void) | null = null;

export const THEME_EVENT = "perilmap:themechange";

/** Runs `prepare` before printing. Returns a function that stops it running. */
export function onPrintPrepare(prepare: Preparer) {
  preparers.add(prepare);
  return () => {
    preparers.delete(prepare);
  };
}

async function prepare(canWait: boolean) {
  if (restoreActive) return;
  const root = document.documentElement;
  const theme = root.getAttribute("data-theme");
  const undos: (() => void)[] = [];
  // Set straight away, so printing from the browser's menu still gets a full restore.
  restoreActive = () => {
    undos.forEach((undo) => undo());
    closed.forEach((details) => {
      details.open = false;
    });
    if (theme === null) root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    flushSync(() => {
      window.dispatchEvent(new Event(THEME_EVENT));
    });
    restoreActive = null;
  };
  // Paper is white, so a printout always uses the light colours, whatever the screen uses.
  root.setAttribute("data-theme", "light");
  flushSync(() => {
    window.dispatchEvent(new Event(THEME_EVENT));
  });
  // Every "About this data" section opens, so nothing is left out of the printout.
  const closed = [...document.querySelectorAll<HTMLDetailsElement>("details[data-print-open]")]
    .filter((details) => !details.open)
    .map((details) => {
      details.open = true;
      return details;
    });
  const results = [...preparers].map((each) => each({ canWait }));
  const keep = (undo: Undo) => {
    if (undo) undos.push(undo);
  };
  results.forEach((result) => {
    if (result instanceof Promise) result.then(keep, () => undefined);
    else keep(result);
  });
  if (canWait) {
    await Promise.allSettled(results);
  }
}

function restore() {
  restoreActive?.();
}

/** Gets the page ready, then opens the browser's print window, where "Save as PDF" is an option. */
export async function printPage(title: string) {
  await prepare(true);
  const original = document.title;
  // Browsers suggest the page title as the PDF's file name.
  document.title = title;
  // Gives the charts a moment to redraw in the light colours.
  await new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 50)));
  try {
    window.print();
  } finally {
    document.title = original;
    restore();
  }
}

/** Also gets the page ready when someone prints from the browser's own menu. */
export function usePrintSupport() {
  useEffect(() => {
    const beforePrint = () => void prepare(false);
    window.addEventListener("beforeprint", beforePrint);
    window.addEventListener("afterprint", restore);
    return () => {
      window.removeEventListener("beforeprint", beforePrint);
      window.removeEventListener("afterprint", restore);
    };
  }, []);
}
