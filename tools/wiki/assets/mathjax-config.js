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
if (typeof document$ !== "undefined") {
  document$.subscribe(function () {
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.startup.output.clearCache();
      window.MathJax.typesetClear();
      window.MathJax.texReset();
      window.MathJax.typesetPromise();
    }
  });
}
