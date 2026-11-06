import { statusDisplay, type StatusIcon } from "@/lib/status";
import styles from "./StatusBadge.module.css";

const ICONS: Record<StatusIcon, React.ReactNode> = {
  partial: <path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor" />,
  unknown: (
    <path
      d="M6 6.2a2.1 2.1 0 1 1 3.2 1.8c-.8.5-1.2 1-1.2 1.8M8 12.2v.1"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  ),
  outside: (
    <path
      d="M4.5 4.5l7 7M11.5 4.5l-7 7"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  ),
  info: (
    <path
      d="M8 7.4v4.2M8 4.6v.1"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  ),
  paused: (
    <path
      d="M6.2 5v6M9.8 5v6"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  ),
};

/** Says when a result isn't an ordinary one. Renders nothing for an ordinary result. */
export function StatusBadge({ status }: { status: string }) {
  const display = statusDisplay(status);
  if (!display) {
    return null;
  }
  return (
    <span className={styles.badge}>
      <svg viewBox="0 0 16 16" className={styles.icon} aria-hidden="true" focusable="false">
        <circle
          cx="8"
          cy="8"
          r="7.25"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeDasharray={
            display.icon === "outside" || display.icon === "unknown" ? "2.4 2" : undefined
          }
        />
        {ICONS[display.icon]}
      </svg>
      {display.label}
    </span>
  );
}
