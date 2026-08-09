export function CanonQuote({ canon = true, cite, children }) {
  return (
    <blockquote style={{margin:"1.5rem 0",padding:"0.25rem 0 0.25rem 1.5rem",borderLeft:`3px solid ${canon?"var(--color-accent)":"var(--color-border-firm)"}`,color:"var(--color-text)",fontSize:canon?"1.03rem":"1rem"}}>
      {children}
      {cite && <cite style={{display:"block",marginTop:"0.5rem",fontSize:"0.85rem",fontStyle:"normal",color:"var(--color-text-muted)"}}>{cite}</cite>}
    </blockquote>
  );
}
