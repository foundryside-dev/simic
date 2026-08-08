// MathJax configuration for the design-docs wiki.
//
// The chapters write maths the way LaTeX does — \( ... \) inline and $$ ... $$
// displayed — which pymdownx.arithmatex (generic mode) wraps in the script
// tags MathJax picks up here. Nothing in docs/design/ was changed to suit this.
//
// processHtmlClass/ignoreHtmlClass keep MathJax away from code blocks, so a
// literal `$$` inside a fenced example is never typeset.
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

// mkdocs-material's instant navigation swaps page content without a reload,
// so MathJax has to be told to typeset the new document body.
// `clearCache` is CHTML-only: it clears the font-metric cache, and the SVG
// output jax this wiki loads (tex-mml-svg.js — see mkdocs.yml) has no such
// method. Called unguarded it THREW, and because it ran first, the three calls
// below that actually re-typeset never executed — so maths silently failed to
// render on every page reached by Material's instant navigation, while a direct
// load looked fine because MathJax's own startup typesets once. Optional
// chaining keeps the optimisation when it exists and skips it when it does not.
if (typeof document$ !== "undefined") {
  document$.subscribe(function () {
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.startup.output.clearCache?.();
      window.MathJax.typesetClear();
      window.MathJax.texReset();
      window.MathJax.typesetPromise();
    }
  });
}
