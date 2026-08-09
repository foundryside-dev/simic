const DS2 = window.SimicDesignSystem_5a908e;
function LineageScreen({ onNav }) {
  const { Masthead, SiteFooter, PageHead, Note, CanonQuote, Spine, Split, CardGrid } = DS2;
  return (
    <div style={{background:"var(--color-bg)",minHeight:"100vh",display:"flex",flexDirection:"column"}}>
      <Masthead current="Why this design" />
      <div onClickCapture={e=>{const a=e.target.closest("a");if(a&&a.textContent==="Overview"){e.preventDefault();e.stopPropagation();onNav("overview");}}}>
      <main style={{flex:1}}>
        <div style={{maxWidth:"var(--page)",margin:"0 auto",padding:"3rem 1rem 4.5rem"}}>
          <PageHead crumb={<><a href="#" onClick={e=>{e.preventDefault();onNav("overview")}} style={{color:"var(--color-text-muted)"}}>Overview</a> {"\u203A"} Why this design</>}
            title="Why this design looks like this"
            lede={<>Almost nothing in Simic is speculative caution. Each defensive mechanism traces to a specific, documented failure — and each forward step is something the record earned the right to attempt.</>} />
          <div style={{maxWidth:"var(--measure)"}}>
            <h2>The record this design answers</h2>
            <p>Simic is the third incarnation of one research programme. Early versions of the simic project (known as esper) built the morphogenetic chassis this design retains — reversible slots, staged maturation, lifecycle states — and that working record is the proximate reason for every major choice made here.</p>
            <h2>The pivot, stated plainly</h2>
            <p>This design <strong>replaces the reward function with measured counterfactuals</strong>. Paired branches from one snapshot over identical futures cancel ordinary-training variance, so the difference between branches <em>is</em> the intervention effect.</p>
            <CanonQuote>
              <p style={{margin:0}}><strong>A model can hallucinate an interface, then use permissive access idioms to hide the hallucination behind silent defaults.</strong></p>
            </CanonQuote>
            <Note label="Read the claims against this">
              <p style={{margin:0}}>Part of the expected improvement — dense per-step labels, attributable failures — is a training-procedure win that could arguably have been retrofitted to the earlier system. The architecture's irreducible contributions are the ones that could not: <strong>generated (not selected) structure, separated authorities, and provider blindness.</strong></p>
            </Note>
            <h2>Armour and forward motion</h2>
            <CanonQuote cite={<><code>docs/design/03-principles.md</code> §6.20</>}>
              <p style={{margin:0}}><strong>Where capability was validated, push forward; where the programme struggled, build armour.</strong></p>
            </CanonQuote>
          </div>
          <Split
            left={<><h3 style={{marginTop:0}}>The armour</h3><p>Every mechanism that makes a documented failure class <em>unrepresentable</em> rather than policed. It faces in two directions, matching the two strata.</p></>}
            right={<><h3 style={{marginTop:0}}>The forward motion</h3><p>What the record earned the right to attempt. Telemetry-conditioned structural decisions are <em>proven</em> sufficient.</p></>} />
          <Spine items={[
            {title:"Do not strip armour to speed the forward motion, and do not restrict the forward motion because the armour is heavy.", body:"The armour is why the forward signal exists."},
            {title:"Armour must cite its scar.", body:"A proposed new constraint that cannot name the failure it prevents is bureaucracy, not armour."},
          ]} />
          <CardGrid cards={[
            {title:"The architecture \u2192", body:"Fourteen bounded domains, the canonical sentence, the newsroom routing rule, and the sentence test used as a lint."},
            {title:"The guarantees \u2192", body:"The invariant spine each piece of armour is written into — cited as INV-nn throughout the design."},
          ]} />
        </div>
      </main>
      </div>
      <SiteFooter />
    </div>
  );
}
window.LineageScreen = LineageScreen;
