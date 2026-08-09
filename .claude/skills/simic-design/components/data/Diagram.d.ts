/**
 * Pre-rendered Mermaid diagram frame: light/dark SVG pair swapped with the theme, horizontal scroll below minWidth, muted figcaption.
 */
export interface DiagramProps {
  lightSrc: string;
  darkSrc?: string;
  /** Accessible description of the diagram */
  label: string;
  caption?: React.ReactNode;
  /** px below which the frame scrolls instead of shrinking (legibility beats fitting) */
  minWidth?: number | string;
}
export declare function Diagram(props: DiagramProps): JSX.Element;
