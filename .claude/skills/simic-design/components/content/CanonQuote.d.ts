/**
 * Blockquote. canon=true (default) gives the accent spine used for canonical design-doc quotes; false is the neutral quote.
 */
export interface CanonQuoteProps {
  canon?: boolean;
  /** Attribution line, usually a mono file path + section */
  cite?: React.ReactNode;
  children: React.ReactNode;
}
export declare function CanonQuote(props: CanonQuoteProps): JSX.Element;
