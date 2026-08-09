/**
 * Callout with a 3px left spine and mono uppercase label. Teal note by default; status=true switches to the amber warning treatment.
 */
export interface NoteProps {
  /** Mono uppercase label, e.g. "Project status" */
  label?: string;
  /** Amber status variant */
  status?: boolean;
  children: React.ReactNode;
}
export declare function Note(props: NoteProps): JSX.Element;
