import { Fragment } from "react";
import type { CSSProperties, ReactNode } from "react";

export interface DefinitionItem {
  term: string;
  value?: ReactNode;
  mono?: boolean;
}

export interface DefinitionListProps {
  items: DefinitionItem[];
  style?: CSSProperties;
}

const dlShell: CSSProperties = { display: "grid", gridTemplateColumns: "max-content 1fr", gap: "var(--space-3) var(--space-6)", margin: 0, fontFamily: "var(--font-body)" };
const dtStyle: CSSProperties = { fontSize: "var(--text-caption)", color: "var(--text-muted)" };
const ddStyle: CSSProperties = { margin: 0, fontSize: "var(--text-body-sm)", color: "var(--text-primary)" };

/** Term/value grid used inside lead-card blocks. Empty values render an em dash. */
export function DefinitionList({ items = [], style, ...rest }: DefinitionListProps) {
  return (
    <dl style={{ ...dlShell, ...style }} {...rest}>
      {items.map((it, i) => (
        <Fragment key={it.term || i}>
          <dt style={dtStyle}>{it.term}</dt>
          <dd style={{ ...ddStyle, ...(it.mono ? { fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)" } : null) }}>
            {it.value == null || it.value === "" ? "—" : it.value}
          </dd>
        </Fragment>
      ))}
    </dl>
  );
}
