/**
 * Link-card grid: subtle fill, hairline border, accent title, border turns accent on hover. No shadows.
 */
export interface CardItem { title: React.ReactNode; body: React.ReactNode; href?: string; }
export interface CardGridProps { cards: CardItem[]; }
export declare function CardGrid(props: CardGridProps): JSX.Element;
