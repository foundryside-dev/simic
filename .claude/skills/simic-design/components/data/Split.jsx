export function Split({ left, right }) {
  return (
    <div style={{display:"grid",gap:"1.5rem",gridTemplateColumns:"repeat(auto-fit, minmax(18rem, 1fr))",maxWidth:"var(--page)",margin:"1.5rem 0"}}>
      <section>{left}</section>
      <section>{right}</section>
    </div>
  );
}
