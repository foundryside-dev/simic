/**
 * The invariant "spine" list: hairline-ruled items with a bold title and a mono accent INV-nn chip.
 */
export interface SpineItem {
  title: React.ReactNode;
  /** e.g. "INV-15, INV-16" */
  inv?: string;
  body: React.ReactNode;
}
export interface SpineProps { items: SpineItem[]; }
export declare function Spine(props: SpineProps): JSX.Element;
