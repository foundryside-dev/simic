export function Spine({ items }) {
  return (
    <ul style={{maxWidth:"var(--measure)",margin:"1.5rem 0",padding:0,listStyle:"none"}}>
      {items.map((it,i)=>(
        <li key={i} style={{padding:"1rem 0",borderTop:"1px solid var(--color-border)",borderBottom:i===items.length-1?"1px solid var(--color-border)":"none",margin:0}}>
          <b style={{display:"block",color:"var(--color-heading)",fontWeight:650}}>
            {it.title}{it.inv && <> <span style={{fontFamily:"var(--font-code)",fontSize:"0.78rem",letterSpacing:"0.04em",color:"var(--color-accent)",whiteSpace:"nowrap"}}>{it.inv}</span></>}
          </b>
          {it.body}
        </li>
      ))}
    </ul>
  );
}
