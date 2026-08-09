export function SiteFooter() {
  return (
    <footer style={{borderTop:"1px solid var(--color-border)",background:"var(--color-bg-subtle)",fontSize:"0.9rem",color:"var(--color-text-muted)"}}>
      <div style={{maxWidth:"var(--page)",margin:"0 auto",padding:"1.5rem 1rem",display:"flex",flexWrap:"wrap",gap:"0.5rem 2rem",justifyContent:"space-between"}}>
        <p style={{margin:0}}>Simic — a research project by tachyon-beep. Licensed Apache-2.0.</p>
        <ul style={{display:"flex",flexWrap:"wrap",gap:"0.5rem 1.5rem",margin:0,padding:0,listStyle:"none"}}>
          <li style={{margin:0}}><a href="https://github.com/foundryside-dev/simic">github.com/foundryside-dev/simic</a></li>
          <li style={{margin:0}}>HLD v4.1 {"\u00B7"} Namespec 2.0 — locked</li>
        </ul>
      </div>
    </footer>
  );
}
