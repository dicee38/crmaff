import { useState } from "react";
import type { CSSProperties, ReactNode } from "react";

export interface DataTableColumn<Row = Record<string, unknown>> {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  /** Render the cell in the mono face — IDs, click_ids, hashes. */
  mono?: boolean;
  /** Tabular numerals + medium weight — amounts and counts. */
  numeric?: boolean;
  render?: (row: Row) => ReactNode;
}

export interface DataTableProps<Row = Record<string, unknown>> {
  columns: DataTableColumn<Row>[];
  rows: Row[];
  rowKey?: (row: Row) => string;
  emptyLabel?: string;
  onRowClick?: (row: Row) => void;
  dense?: boolean;
  style?: CSSProperties;
}

const tableShell: CSSProperties = { width: "100%", borderCollapse: "collapse", background: "var(--surface-card)", fontFamily: "var(--font-body)" };
const tableWrap: CSSProperties = { border: "var(--border-width) solid var(--border-subtle)", borderRadius: "var(--radius-md)", overflow: "hidden", overflowX: "auto" };
const tableHeadCell: CSSProperties = {
  textAlign: "left",
  padding: "var(--space-4) var(--space-5)",
  fontSize: "var(--text-micro)",
  fontWeight: "var(--weight-semibold)",
  letterSpacing: "var(--tracking-label)",
  textTransform: "uppercase",
  color: "var(--text-muted)",
  background: "var(--bone-50)",
  borderBottom: "var(--border-width) solid var(--border-subtle)",
  whiteSpace: "nowrap",
};
const tableCell: CSSProperties = {
  padding: "var(--space-4) var(--space-5)",
  fontSize: "var(--text-body-sm)",
  color: "var(--text-primary)",
  borderBottom: "var(--border-width) solid var(--border-subtle)",
  verticalAlign: "middle",
};
const tableEmpty: CSSProperties = { padding: "var(--space-8) var(--space-5)", fontSize: "var(--text-body-sm)", color: "var(--text-muted)", textAlign: "center" };

/** The workhorse CRM table: hairline rows, uppercase head, bone hover. */
export function DataTable<Row = Record<string, unknown>>({
  columns = [],
  rows = [],
  rowKey,
  emptyLabel = "Ничего не найдено",
  onRowClick,
  dense = false,
  style,
  ...rest
}: DataTableProps<Row>) {
  const [hoverIdx, setHoverIdx] = useState(-1);
  const pad: CSSProperties | null = dense ? { padding: "var(--space-3) var(--space-4)" } : null;
  return (
    <div style={{ ...tableWrap, ...style }} {...rest}>
      <table style={tableShell}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={{ ...tableHeadCell, ...pad, textAlign: c.align || "left" }}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={rowKey ? rowKey(row) : i}
              onClick={
                onRowClick
                  ? (e) => {
                      // Клик по кнопке/ссылке внутри строки (напр. "Удалить") не должен
                      // триггерить переход по строке.
                      if ((e.target as HTMLElement).closest("button, a")) return;
                      onRowClick(row);
                    }
                  : undefined
              }
              onMouseEnter={() => setHoverIdx(i)}
              onMouseLeave={() => setHoverIdx(-1)}
              style={{
                background: hoverIdx === i ? "var(--bone-50)" : "transparent",
                cursor: onRowClick ? "pointer" : "default",
                transition: "background var(--duration-fast) var(--ease-out)",
              }}
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  style={{
                    ...tableCell,
                    ...pad,
                    textAlign: c.align || "left",
                    ...(c.mono ? { fontFamily: "var(--font-mono)", fontSize: "var(--text-caption)", letterSpacing: "var(--tracking-mono)" } : null),
                    ...(c.numeric ? { fontVariantNumeric: "tabular-nums", fontWeight: "var(--weight-medium)" } : null),
                  }}
                >
                  {c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={tableEmpty}>
                {emptyLabel}
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
