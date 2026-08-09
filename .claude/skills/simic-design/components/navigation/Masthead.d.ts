/**
 * Site header: mono \u25C8 simic wordmark + primary nav. Active item gets heading color and a 2px accent underline.
 * @startingPoint section="Website" subtitle="Masthead with wordmark and primary nav" viewport="1100x80"
 */
export interface MastheadProps {
  /** Label of the current page */
  current?: string;
  /** [label, href] pairs; defaults to the live site's nav */
  items?: [string, string][];
}
export declare function Masthead(props: MastheadProps): JSX.Element;
