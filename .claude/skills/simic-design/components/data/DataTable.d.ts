/**
 * Wrapped table: hairline frame, uppercase mono-ish header row on subtle fill, first column in mono (the "name" column).
 */
export interface DataTableProps {
  caption?: React.ReactNode;
  columns: React.ReactNode[];
  /** Row cells; first cell renders in mono heading style */
  rows: React.ReactNode[][];
}
export declare function DataTable(props: DataTableProps): JSX.Element;
