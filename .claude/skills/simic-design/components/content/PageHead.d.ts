/**
 * Page header block: optional breadcrumb, h1, mono accent tagline, larger lede paragraph.
 */
export interface PageHeadProps {
  title: string;
  /** Mono accent line under the h1 (e.g. "Counterfactual Generative Morphogenesis") */
  tagline?: string;
  /** 1.12rem intro paragraph; accepts rich children */
  lede?: React.ReactNode;
  /** Breadcrumb line, e.g. "Overview \u203A Why this design" */
  crumb?: React.ReactNode;
}
export declare function PageHead(props: PageHeadProps): JSX.Element;
