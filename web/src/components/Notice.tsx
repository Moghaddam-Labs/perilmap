import type { ReactNode } from "react";
import styles from "./Notice.module.css";

interface NoticeProps {
  title: string;
  tone?: "info" | "error";
  className?: string;
  children: ReactNode;
}

/** A short message set apart from the page. Errors are announced as soon as they appear. */
export function Notice({ title, tone = "info", className, children }: NoticeProps) {
  return (
    <div
      className={[styles.notice, styles[tone], className].filter(Boolean).join(" ")}
      role={tone === "error" ? "alert" : undefined}
    >
      <p className={styles.title}>{title}</p>
      <div>{children}</div>
    </div>
  );
}
