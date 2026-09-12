import type { CSSProperties } from "react";

import { Button } from "../core/Button";

export interface PaginationProps {
  onPrev?: () => void;
  onNext?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
  /** Range note, e.g. "1–20 из 12 480". */
  note?: string;
  style?: CSSProperties;
}

const pagerShell: CSSProperties = { display: "flex", alignItems: "center", gap: "var(--space-3)", marginTop: "var(--space-5)" };
const pagerNote: CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)", color: "var(--text-muted)", marginLeft: "var(--space-3)" };

/** Cursor pagination controls for the CRM's keyset-paged lists. */
export function Pagination({ onPrev, onNext, hasPrev = false, hasNext = false, note, style, ...rest }: PaginationProps) {
  return (
    <div style={{ ...pagerShell, ...style }} {...rest}>
      <Button size="sm" variant="secondary" disabled={!hasPrev} onClick={onPrev}>
        Назад
      </Button>
      <Button size="sm" variant="secondary" disabled={!hasNext} onClick={onNext}>
        Вперёд
      </Button>
      {note ? <span style={pagerNote}>{note}</span> : null}
    </div>
  );
}
