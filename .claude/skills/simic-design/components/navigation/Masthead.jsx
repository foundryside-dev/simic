export function Masthead({ current = "Overview", items }) {
  const nav = items ?? [["Overview","index.html"],["Architecture","architecture.html"],["Why this design","lineage.html"],["Design docs","/design/"],["Source","https://github.com/foundryside-dev/simic"]];
  return (
    <header style={{borderBottom:"1px solid var(--color-border)",background:"var(--color-bg-subtle)"}}>
      <div style={{maxWidth:"var(--page)",margin:"0 auto",padding:"1rem 1rem",display:"flex",flexWrap:"wrap",alignItems:"baseline",gap:"0.5rem 2rem"}}>
        <a href="#" style={{fontFamily:"var(--font-code)",fontSize:"1.05rem",fontWeight:600,letterSpacing:"0.02em",color:"var(--color-heading)",textDecoration:"none"}} onClick={e=>e.preventDefault()}>
          <span style={{color:"var(--color-accent)"}}>{"\u25C8 "}</span>simic
        </a>
        <nav aria-label="Primary">
          <ul style={{display:"flex",flexWrap:"wrap",gap:"0.5rem 1.5rem",margin:0,padding:0,listStyle:"none",fontSize:"0.94rem"}}>
            {nav.map(([label,href])=>{
              const active = label===current;
              return <li key={label} style={{margin:0}}>
                <a href={href} onClick={e=>e.preventDefault()} style={{textDecoration:"none",color:active?"var(--color-heading)":"var(--color-text-muted)",paddingBlock:"0.25rem",borderBottom:active?"2px solid var(--color-accent)":"2px solid transparent"}}
                   onMouseEnter={e=>{if(!active)e.currentTarget.style.color="var(--color-accent)"}}
                   onMouseLeave={e=>{if(!active)e.currentTarget.style.color="var(--color-text-muted)"}}>{label}</a>
              </li>;
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}
