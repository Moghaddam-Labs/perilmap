/**
 * What each result status looks like. An ordinary result needs no badge. A gap always gets one, so
 * it can't be mistaken for low risk. An unrecognised status is treated as a gap for the same reason.
 */

export type StatusIcon = "partial" | "unknown" | "outside" | "info" | "paused";

export interface StatusDisplay {
  label: string;
  icon: StatusIcon;
}

const STATUSES: Record<string, StatusDisplay | null> = {
  available: null,
  incomplete: { label: "May be incomplete", icon: "partial" },
  general_information: { label: "General information", icon: "info" },
  no_data: { label: "No data", icon: "unknown" },
  not_available_here: { label: "Not available here yet", icon: "outside" },
  temporarily_unavailable: { label: "Temporarily unavailable", icon: "paused" },
};

const UNKNOWN_STATUS: StatusDisplay = { label: "Check this result", icon: "unknown" };

export function statusDisplay(status: string): StatusDisplay | null {
  return Object.hasOwn(STATUSES, status) ? (STATUSES[status] ?? null) : UNKNOWN_STATUS;
}
