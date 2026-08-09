export function DataTable({ caption, columns, rows }) {
  return (
    <div style={{maxWidth:"var(--page)",margin:"1.5rem 0",overflowX:"auto",border:"1px solid var(--color-border)",borderRadius:"var(--radius)"}}>
      <table style={{width:"100%",minWidth:"34rem",borderCollapse:"collapse",fontSize:"0.92rem"}}>
        {caption && <caption style={{textAlign:"left",padding:"0.5rem 1rem",fontSize:"0.85rem",color:"var(--color-text-muted)",borderBottom:"1px solid var(--color-border)"}}>{caption}</caption>}
        <thead><tr>
          {columns.map((c,i)=><th key={i} scope="col" style={{textAlign:"left",verticalAlign:"top",padding:"0.5rem 1rem",borderBottom:"1px solid var(--color-border)",color:"var(--color-heading)",fontSize:"0.8rem",letterSpacing:"0.06em",textTransform:"uppercase",background:"var(--color-bg-subtle)",whiteSpace:"nowrap"}}>{c}</th>)}
        </tr></thead>
        <tbody>
          {rows.map((r,ri)=><tr key={ri}>
            {r.map((cell,ci)=><td key={ci} style={{textAlign:"left",verticalAlign:"top",padding:"0.5rem 1rem",borderBottom:ri===rows.length-1?"none":"1px solid var(--color-border)",...(ci===0?{fontFamily:"var(--font-code)",color:"var(--color-heading)",whiteSpace:"nowrap"}:{})}}>{cell}</td>)}
          </tr>)}
        </tbody>
      </table>
    </div>
  );
}
