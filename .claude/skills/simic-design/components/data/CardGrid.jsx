export function CardGrid({ cards }) {
  return (
    <ul style={{display:"grid",gap:"1rem",gridTemplateColumns:"repeat(auto-fit, minmax(15rem, 1fr))",margin:"1.5rem 0 2rem",padding:0,listStyle:"none"}}>
      {cards.map((c,i)=>(
        <li key={i} style={{margin:0}}>
          <a href={c.href||"#"} onClick={e=>{if(!c.href)e.preventDefault()}}
             style={{display:"block",height:"100%",padding:"1rem 1.5rem",background:"var(--color-bg-subtle)",border:"1px solid var(--color-border)",borderRadius:"var(--radius)",textDecoration:"none",color:"inherit"}}
             onMouseEnter={e=>e.currentTarget.style.borderColor="var(--color-accent)"}
             onMouseLeave={e=>e.currentTarget.style.borderColor="var(--color-border)"}>
            <h3 style={{margin:"0 0 0.5rem",fontSize:"1rem",color:"var(--color-accent)"}}>{c.title}</h3>
            <p style={{margin:0,fontSize:"0.92rem",color:"var(--color-text-muted)"}}>{c.body}</p>
          </a>
        </li>
      ))}
    </ul>
  );
}
