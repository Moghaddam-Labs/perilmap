"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import styles from "./ExplainerCards.module.css";

export interface Explainer {
  id: string;
  title: string;
  teaser: string;
  icon: ReactNode;
  content: ReactNode;
}

/**
 * Cards that open on click or tap to show more. Only one is open at a time, and it closes when you
 * click outside or press Escape. They never open on hover, so the page doesn't jump about.
 */
export function ExplainerCards({ cards }: { cards: Explainer[] }) {
  const baseId = useId();
  const listRef = useRef<HTMLUListElement>(null);
  const buttons = useRef(new Map<string, HTMLButtonElement>());
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    if (!openId) return;
    const closeOnOutside = (event: PointerEvent) => {
      if (!listRef.current?.contains(event.target as Node)) setOpenId(null);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      // Focus goes back to the card's button, so keyboard users don't lose their place.
      buttons.current.get(openId)?.focus();
      setOpenId(null);
    };
    document.addEventListener("pointerdown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [openId]);

  return (
    <ul ref={listRef} className={styles.cards}>
      {cards.map((card) => {
        const open = openId === card.id;
        const buttonId = `${baseId}-${card.id}-button`;
        const panelId = `${baseId}-${card.id}-panel`;
        return (
          <li key={card.id} className={styles.card} data-open={open || undefined}>
            <h3 className={styles.heading}>
              <button
                ref={(element) => {
                  if (element) buttons.current.set(card.id, element);
                  else buttons.current.delete(card.id);
                }}
                id={buttonId}
                type="button"
                className={styles.toggle}
                aria-expanded={open}
                aria-controls={panelId}
                onClick={() => setOpenId(open ? null : card.id)}
              >
                <span className={styles.icon} aria-hidden="true">
                  {card.icon}
                </span>
                {/* The space keeps screen readers from running the title into the line below. */}
                <span className={styles.title}>{card.title}</span>{" "}
                <span className={styles.teaser}>{card.teaser}</span>
                {/* Screen readers hear "expanded" or "collapsed" instead of this. */}
                <span className={styles.more} aria-hidden="true">
                  {open ? "Show less" : "Show more"}
                  <svg viewBox="0 0 12 12" aria-hidden="true" focusable="false">
                    <path d="M2.5 4.5 6 8l3.5-3.5" />
                  </svg>
                </span>
              </button>
            </h3>
            <div
              id={panelId}
              role="region"
              aria-label={card.title}
              className={styles.panel}
              hidden={!open}
            >
              {card.content}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
