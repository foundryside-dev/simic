export function Note({ label, status = false, children }) {
  const spine = status ? "var(--color-warn)" : "var(--color-accent)";
  return (
    <div style={{maxWidth:"var(--measure)",margin:"1.5rem 0",padding:"1rem 1.5rem",background:status?"var(--color-bg-note-status)":"var(--color-bg-note)",border:"1px solid var(--color-border)",borderLeft:`3px solid ${spine}`,borderRadius:"var(--radius)"}}>
      {label && <span style={{display:"block",fontFamily:"var(--font-code)",fontSize:"0.78rem",letterSpacing:"0.08em",textTransform:"uppercase",color:spine,marginBottom:"0.25rem"}}>{label}</span>}
      <div style={{margin:0}}>{children}</div>
    </div>
  );
}
