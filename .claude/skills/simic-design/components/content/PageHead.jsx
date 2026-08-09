export function PageHead({ title, tagline, lede, crumb }) {
  return (
    <div style={{marginBottom:"2rem"}}>
      {crumb && <p style={{fontSize:"0.88rem",color:"var(--color-text-muted)",margin:"0 0 1rem"}}>{crumb}</p>}
      <h1 style={{margin:"0 0 0.5rem"}}>{title}</h1>
      {tagline && <p style={{fontFamily:"var(--font-code)",fontSize:"0.95rem",letterSpacing:"0.01em",color:"var(--color-accent)",margin:"0 0 1.5rem"}}>{tagline}</p>}
      {lede && <p style={{maxWidth:"var(--measure)",fontSize:"1.12rem",lineHeight:1.6,margin:0}}>{lede}</p>}
    </div>
  );
}
