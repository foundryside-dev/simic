const DS = window.SimicDesignSystem_5a908e;
function OverviewScreen({ onNav }) {
  const { Masthead, SiteFooter, PageHead, Note, CanonQuote, Spine, DataTable, Diagram } = DS;
  return (
    <div style={{background:"var(--color-bg)",minHeight:"100vh",display:"flex",flexDirection:"column"}}>
      <Masthead current="Overview" items={[["Overview","#"],["Architecture","#"],["Why this design","#"],["Design docs","#"],["Source","#"]].map(([l,h])=>[l,h])} />
      <div style={{width:"100%"}} onClickCapture={e=>{const a=e.target.closest("a");if(a&&a.textContent==="Why this design"){e.preventDefault();e.stopPropagation();onNav("lineage");}}}>
      <main style={{flex:1}}>
        <div style={{maxWidth:"var(--page)",margin:"0 auto",padding:"3rem 1rem 4.5rem"}}>
          <PageHead title="Simic" tagline="Counterfactual Generative Morphogenesis"
            lede={<>New neural structure is <strong>generated from the live state of a host network</strong> — not selected from a fixed menu of human-authored blueprints — then causally screened against doing nothing. Measured counterfactuals instead of a reward function.</>} />
          <Note label="Project status" status>
            <p style={{margin:0}}><strong>Pre-implementation bootstrap.</strong> The design is complete and locked — HLD v4.1, Namespec 2.0 — and a Python scaffold exists, but there is <strong>no functional code yet</strong>. First engineering work is Phase A: Namespec, Leyline contracts, and dependency boundaries. Nothing on this site describes a running system or a measured result.</p>
          </Note>
          <div style={{maxWidth:"var(--measure)"}}>
            <h2>The idea</h2>
            <p>Growing a neural network at runtime raises four questions that existing systems tend to blur together: <em>what</em> new structure to add, <em>whether</em> it is structurally sound, <em>whether</em> it actually helps, and <em>who</em> gets to decide. Simic separates those concerns constitutionally.</p>
            <p>Structure is designed from live host telemetry; verified and canonicalised; compiled without semantic change; tested in flash-cloned counterfactual branches that share an identical future with the mainline; and admitted only if it beats a <strong>mandatory no-op alternative</strong> under a provider-blind judge. Everything — including failures, rejected pools, and no-op wins — is retained as history.</p>
            <h3>The loop, end to end</h3>
          </div>
          <Diagram lightSrc="../../assets/diagrams/core-loop-light.svg" darkSrc="../../assets/diagrams/core-loop-dark.svg" label="Flowchart of the core loop" minWidth={600}
            caption={<>The ordinary host-training loop and the growth loop share one execution reality, and the candidate pool is allowed to lose. Source: <code>docs/design/01-claim.md</code> §1.</>} />
          <div style={{maxWidth:"var(--measure)"}}>
            <h2>Guarantees</h2>
            <p>The constitution defines 45 blocking invariants, cited throughout the design as <code>INV-nn</code>. The spine:</p>
          </div>
          <Spine items={[
            {title:"Determinism", inv:"INV-05", body:"Identical snapshot plus identical future data produces bitwise-identical traces under the Academy execution profile."},
            {title:"Doing nothing is a real competitor", inv:"INV-15, INV-16", body:"Every admission and tenancy review includes a measured no-intervention branch with policy utility exactly zero. The whole candidate pool may lose to it."},
            {title:"Tail risk cannot be bought", inv:"INV-45", body:"Admission is lexicographic: the tail-risk veto is adjudicated before any utility comparison, and no measured benefit can offset it."},
            {title:"Absent signal stays absent", inv:"INV-38", body:"Invariant breaches fail loudly and visibly. A missing telemetry field never becomes a zero."},
          ]} />
          <div style={{maxWidth:"var(--measure)"}}>
            <h2>Fourteen domains, one sentence</h2>
            <p>Authority is split across fourteen bounded domains with deliberately vivid codenames. The names are not decoration: they act as an architecture linter.</p>
            <CanonQuote cite={<>The canonical sentence — <code>docs/design/02-constitution.md</code> §5.3</>}>
              <p style={{margin:0}}>Under Leyline, Ugin plans, Aurelia commissions and acts, Nissa observes, Momir designs, Elesh conforms, Urabrask compiles, Jin-Gitaxias tests in Tolaria, Isperia judges, Wrenn embodies, Emrakul destroys, and Tamiyo reveals; every precedent is kept in Urborg.</p>
            </CanonQuote>
            <h2>Where the design lives</h2>
            <p>The canonical authority is the HLD chapter set in the repository, not this site.</p>
          </div>
          <DataTable caption="Repository map" columns={["Path","Contents"]} rows={[
            ["docs/design/00-INDEX.md","Entry point to the HLD chapter set, with reading paths"],
            ["docs/design/01-claim.md","Executive summary, problem statement, goals, non-goals, the first defensible claim"],
            ["docs/design/02-constitution.md","Naming constitution and the 45 blocking invariants"],
            ["docs/design/04-architecture.md","System context, planes, and the control hierarchy"],
            ["src/simic/","Target code layout: one package per domain (scaffold only, today)"],
          ]} />
        </div>
      </main>
      </div>
      <SiteFooter />
    </div>
  );
}
window.OverviewScreen = OverviewScreen;
