import type { CSSProperties } from "react";

export interface TimelineItem {
  id?: string;
  /** telegram | whatsapp | webchat */
  channel?: string;
  direction?: "inbound" | "outbound";
  timestamp?: string;
  text?: string;
}

export interface TimelineProps {
  items: TimelineItem[];
  style?: CSSProperties;
}

const timelineList: CSSProperties = { listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "var(--space-4)" };
const timelineItem: CSSProperties = { borderLeft: "var(--border-width-strong) solid var(--border-subtle)", paddingLeft: "var(--space-4)" };
const timelineMeta: CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "var(--text-micro)", letterSpacing: "var(--tracking-mono)", color: "var(--text-muted)", textTransform: "uppercase" };
const timelineBody: CSSProperties = { margin: "var(--space-2) 0 0", fontFamily: "var(--font-body)", fontSize: "var(--text-body-sm)", lineHeight: "var(--lh-body)", color: "var(--text-primary)" };

/** Communication log for a lead card. Inbound messages carry a deep-blue left rule. */
export function Timeline({ items = [], style, ...rest }: TimelineProps) {
  return (
    <ul style={{ ...timelineList, ...style }} {...rest}>
      {items.map((it, i) => (
        <li key={it.id || i} style={{ ...timelineItem, borderLeftColor: it.direction === "inbound" ? "var(--navy-700)" : "var(--border-subtle)" }}>
          <span style={timelineMeta}>{[it.channel, it.direction, it.timestamp].filter(Boolean).join(" · ")}</span>
          <p style={timelineBody}>{it.text}</p>
        </li>
      ))}
      {items.length === 0 ? <li style={{ fontFamily: "var(--font-body)", fontSize: "var(--text-body-sm)", color: "var(--text-muted)" }}>Коммуникаций пока нет</li> : null}
    </ul>
  );
}
