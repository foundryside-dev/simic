/* @ds-bundle: {"format":4,"namespace":"SimicDesignSystem_5a908e","components":[{"name":"CanonQuote","sourcePath":"components/content/CanonQuote.jsx"},{"name":"Note","sourcePath":"components/content/Note.jsx"},{"name":"PageHead","sourcePath":"components/content/PageHead.jsx"},{"name":"Spine","sourcePath":"components/content/Spine.jsx"},{"name":"CardGrid","sourcePath":"components/data/CardGrid.jsx"},{"name":"DataTable","sourcePath":"components/data/DataTable.jsx"},{"name":"Diagram","sourcePath":"components/data/Diagram.jsx"},{"name":"Split","sourcePath":"components/data/Split.jsx"},{"name":"Masthead","sourcePath":"components/navigation/Masthead.jsx"},{"name":"SiteFooter","sourcePath":"components/navigation/SiteFooter.jsx"}],"sourceHashes":{"components/content/CanonQuote.jsx":"c9e1c8eb1e1a","components/content/Note.jsx":"66b09bc24cab","components/content/PageHead.jsx":"4a16b7510e5e","components/content/Spine.jsx":"f4ef28d9f42c","components/data/CardGrid.jsx":"a6faf162cfb2","components/data/DataTable.jsx":"3c7c376deb62","components/data/Diagram.jsx":"0ae39c56c52b","components/data/Split.jsx":"33200805c2a5","components/navigation/Masthead.jsx":"9329d5716b0b","components/navigation/SiteFooter.jsx":"bc5491cbd861","ui_kits/website/LineageScreen.jsx":"cfeca53a4246","ui_kits/website/OverviewScreen.jsx":"9c5d64ebaa92"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.SimicDesignSystem_5a908e = window.SimicDesignSystem_5a908e || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/content/CanonQuote.jsx
try { (() => {
function CanonQuote({
  canon = true,
  cite,
  children
}) {
  return /*#__PURE__*/React.createElement("blockquote", {
    style: {
      margin: "1.5rem 0",
      padding: "0.25rem 0 0.25rem 1.5rem",
      borderLeft: `3px solid ${canon ? "var(--color-accent)" : "var(--color-border-firm)"}`,
      color: "var(--color-text)",
      fontSize: canon ? "1.03rem" : "1rem"
    }
  }, children, cite && /*#__PURE__*/React.createElement("cite", {
    style: {
      display: "block",
      marginTop: "0.5rem",
      fontSize: "0.85rem",
      fontStyle: "normal",
      color: "var(--color-text-muted)"
    }
  }, cite));
}
Object.assign(__ds_scope, { CanonQuote });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/CanonQuote.jsx", error: String((e && e.message) || e) }); }

// components/content/Note.jsx
try { (() => {
function Note({
  label,
  status = false,
  children
}) {
  const spine = status ? "var(--color-warn)" : "var(--color-accent)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--measure)",
      margin: "1.5rem 0",
      padding: "1rem 1.5rem",
      background: status ? "var(--color-bg-note-status)" : "var(--color-bg-note)",
      border: "1px solid var(--color-border)",
      borderLeft: `3px solid ${spine}`,
      borderRadius: "var(--radius)"
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontFamily: "var(--font-code)",
      fontSize: "0.78rem",
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      color: spine,
      marginBottom: "0.25rem"
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: 0
    }
  }, children));
}
Object.assign(__ds_scope, { Note });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Note.jsx", error: String((e && e.message) || e) }); }

// components/content/PageHead.jsx
try { (() => {
function PageHead({
  title,
  tagline,
  lede,
  crumb
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: "2rem"
    }
  }, crumb && /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: "0.88rem",
      color: "var(--color-text-muted)",
      margin: "0 0 1rem"
    }
  }, crumb), /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: "0 0 0.5rem"
    }
  }, title), tagline && /*#__PURE__*/React.createElement("p", {
    style: {
      fontFamily: "var(--font-code)",
      fontSize: "0.95rem",
      letterSpacing: "0.01em",
      color: "var(--color-accent)",
      margin: "0 0 1.5rem"
    }
  }, tagline), lede && /*#__PURE__*/React.createElement("p", {
    style: {
      maxWidth: "var(--measure)",
      fontSize: "1.12rem",
      lineHeight: 1.6,
      margin: 0
    }
  }, lede));
}
Object.assign(__ds_scope, { PageHead });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/PageHead.jsx", error: String((e && e.message) || e) }); }

// components/content/Spine.jsx
try { (() => {
function Spine({
  items
}) {
  return /*#__PURE__*/React.createElement("ul", {
    style: {
      maxWidth: "var(--measure)",
      margin: "1.5rem 0",
      padding: 0,
      listStyle: "none"
    }
  }, items.map((it, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: {
      padding: "1rem 0",
      borderTop: "1px solid var(--color-border)",
      borderBottom: i === items.length - 1 ? "1px solid var(--color-border)" : "none",
      margin: 0
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      display: "block",
      color: "var(--color-heading)",
      fontWeight: 650
    }
  }, it.title, it.inv && /*#__PURE__*/React.createElement(React.Fragment, null, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-code)",
      fontSize: "0.78rem",
      letterSpacing: "0.04em",
      color: "var(--color-accent)",
      whiteSpace: "nowrap"
    }
  }, it.inv))), it.body)));
}
Object.assign(__ds_scope, { Spine });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/content/Spine.jsx", error: String((e && e.message) || e) }); }

// components/data/CardGrid.jsx
try { (() => {
function CardGrid({
  cards
}) {
  return /*#__PURE__*/React.createElement("ul", {
    style: {
      display: "grid",
      gap: "1rem",
      gridTemplateColumns: "repeat(auto-fit, minmax(15rem, 1fr))",
      margin: "1.5rem 0 2rem",
      padding: 0,
      listStyle: "none"
    }
  }, cards.map((c, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: {
      margin: 0
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: c.href || "#",
    onClick: e => {
      if (!c.href) e.preventDefault();
    },
    style: {
      display: "block",
      height: "100%",
      padding: "1rem 1.5rem",
      background: "var(--color-bg-subtle)",
      border: "1px solid var(--color-border)",
      borderRadius: "var(--radius)",
      textDecoration: "none",
      color: "inherit"
    },
    onMouseEnter: e => e.currentTarget.style.borderColor = "var(--color-accent)",
    onMouseLeave: e => e.currentTarget.style.borderColor = "var(--color-border)"
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: "0 0 0.5rem",
      fontSize: "1rem",
      color: "var(--color-accent)"
    }
  }, c.title), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "0.92rem",
      color: "var(--color-text-muted)"
    }
  }, c.body)))));
}
Object.assign(__ds_scope, { CardGrid });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/CardGrid.jsx", error: String((e && e.message) || e) }); }

// components/data/DataTable.jsx
try { (() => {
function DataTable({
  caption,
  columns,
  rows
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--page)",
      margin: "1.5rem 0",
      overflowX: "auto",
      border: "1px solid var(--color-border)",
      borderRadius: "var(--radius)"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      minWidth: "34rem",
      borderCollapse: "collapse",
      fontSize: "0.92rem"
    }
  }, caption && /*#__PURE__*/React.createElement("caption", {
    style: {
      textAlign: "left",
      padding: "0.5rem 1rem",
      fontSize: "0.85rem",
      color: "var(--color-text-muted)",
      borderBottom: "1px solid var(--color-border)"
    }
  }, caption), /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, columns.map((c, i) => /*#__PURE__*/React.createElement("th", {
    key: i,
    scope: "col",
    style: {
      textAlign: "left",
      verticalAlign: "top",
      padding: "0.5rem 1rem",
      borderBottom: "1px solid var(--color-border)",
      color: "var(--color-heading)",
      fontSize: "0.8rem",
      letterSpacing: "0.06em",
      textTransform: "uppercase",
      background: "var(--color-bg-subtle)",
      whiteSpace: "nowrap"
    }
  }, c)))), /*#__PURE__*/React.createElement("tbody", null, rows.map((r, ri) => /*#__PURE__*/React.createElement("tr", {
    key: ri
  }, r.map((cell, ci) => /*#__PURE__*/React.createElement("td", {
    key: ci,
    style: {
      textAlign: "left",
      verticalAlign: "top",
      padding: "0.5rem 1rem",
      borderBottom: ri === rows.length - 1 ? "none" : "1px solid var(--color-border)",
      ...(ci === 0 ? {
        fontFamily: "var(--font-code)",
        color: "var(--color-heading)",
        whiteSpace: "nowrap"
      } : {})
    }
  }, cell)))))));
}
Object.assign(__ds_scope, { DataTable });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/DataTable.jsx", error: String((e && e.message) || e) }); }

// components/data/Diagram.jsx
try { (() => {
function Diagram({
  lightSrc,
  darkSrc,
  label,
  caption,
  minWidth = 0
}) {
  return /*#__PURE__*/React.createElement("figure", {
    style: {
      margin: "1.5rem 0",
      maxWidth: "var(--page)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    role: "img",
    "aria-label": label,
    style: {
      overflowX: "auto",
      paddingBlock: "0.5rem"
    }
  }, /*#__PURE__*/React.createElement("picture", null, darkSrc && /*#__PURE__*/React.createElement("source", {
    srcSet: darkSrc,
    media: "(prefers-color-scheme: dark)"
  }), /*#__PURE__*/React.createElement("img", {
    src: lightSrc,
    alt: "",
    style: {
      display: "block",
      height: "auto",
      maxWidth: "100%",
      minWidth,
      marginInline: "auto"
    }
  }))), caption && /*#__PURE__*/React.createElement("figcaption", {
    style: {
      fontSize: "0.85rem",
      color: "var(--color-text-muted)",
      marginTop: "0.5rem"
    }
  }, caption));
}
Object.assign(__ds_scope, { Diagram });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Diagram.jsx", error: String((e && e.message) || e) }); }

// components/data/Split.jsx
try { (() => {
function Split({
  left,
  right
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gap: "1.5rem",
      gridTemplateColumns: "repeat(auto-fit, minmax(18rem, 1fr))",
      maxWidth: "var(--page)",
      margin: "1.5rem 0"
    }
  }, /*#__PURE__*/React.createElement("section", null, left), /*#__PURE__*/React.createElement("section", null, right));
}
Object.assign(__ds_scope, { Split });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Split.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Masthead.jsx
try { (() => {
function Masthead({
  current = "Overview",
  items
}) {
  const nav = items ?? [["Overview", "index.html"], ["Architecture", "architecture.html"], ["Why this design", "lineage.html"], ["Design docs", "/design/"], ["Source", "https://github.com/foundryside-dev/simic"]];
  return /*#__PURE__*/React.createElement("header", {
    style: {
      borderBottom: "1px solid var(--color-border)",
      background: "var(--color-bg-subtle)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--page)",
      margin: "0 auto",
      padding: "1rem 1rem",
      display: "flex",
      flexWrap: "wrap",
      alignItems: "baseline",
      gap: "0.5rem 2rem"
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "#",
    style: {
      fontFamily: "var(--font-code)",
      fontSize: "1.05rem",
      fontWeight: 600,
      letterSpacing: "0.02em",
      color: "var(--color-heading)",
      textDecoration: "none"
    },
    onClick: e => e.preventDefault()
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--color-accent)"
    }
  }, "◈ "), "simic"), /*#__PURE__*/React.createElement("nav", {
    "aria-label": "Primary"
  }, /*#__PURE__*/React.createElement("ul", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: "0.5rem 1.5rem",
      margin: 0,
      padding: 0,
      listStyle: "none",
      fontSize: "0.94rem"
    }
  }, nav.map(([label, href]) => {
    const active = label === current;
    return /*#__PURE__*/React.createElement("li", {
      key: label,
      style: {
        margin: 0
      }
    }, /*#__PURE__*/React.createElement("a", {
      href: href,
      onClick: e => e.preventDefault(),
      style: {
        textDecoration: "none",
        color: active ? "var(--color-heading)" : "var(--color-text-muted)",
        paddingBlock: "0.25rem",
        borderBottom: active ? "2px solid var(--color-accent)" : "2px solid transparent"
      },
      onMouseEnter: e => {
        if (!active) e.currentTarget.style.color = "var(--color-accent)";
      },
      onMouseLeave: e => {
        if (!active) e.currentTarget.style.color = "var(--color-text-muted)";
      }
    }, label));
  })))));
}
Object.assign(__ds_scope, { Masthead });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Masthead.jsx", error: String((e && e.message) || e) }); }

// components/navigation/SiteFooter.jsx
try { (() => {
function SiteFooter() {
  return /*#__PURE__*/React.createElement("footer", {
    style: {
      borderTop: "1px solid var(--color-border)",
      background: "var(--color-bg-subtle)",
      fontSize: "0.9rem",
      color: "var(--color-text-muted)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--page)",
      margin: "0 auto",
      padding: "1.5rem 1rem",
      display: "flex",
      flexWrap: "wrap",
      gap: "0.5rem 2rem",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0
    }
  }, "Simic — a research project by tachyon-beep. Licensed Apache-2.0."), /*#__PURE__*/React.createElement("ul", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: "0.5rem 1.5rem",
      margin: 0,
      padding: 0,
      listStyle: "none"
    }
  }, /*#__PURE__*/React.createElement("li", {
    style: {
      margin: 0
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "https://github.com/foundryside-dev/simic"
  }, "github.com/foundryside-dev/simic")), /*#__PURE__*/React.createElement("li", {
    style: {
      margin: 0
    }
  }, "HLD v4.1 ", "·", " Namespec 1.0 — locked"))));
}
Object.assign(__ds_scope, { SiteFooter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/SiteFooter.jsx", error: String((e && e.message) || e) }); }

// ui_kits/website/LineageScreen.jsx
try { (() => {
const DS2 = window.SimicDesignSystem_5a908e;
function LineageScreen({
  onNav
}) {
  const {
    Masthead,
    SiteFooter,
    PageHead,
    Note,
    CanonQuote,
    Spine,
    Split,
    CardGrid
  } = DS2;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--color-bg)",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement(Masthead, {
    current: "Why this design"
  }), /*#__PURE__*/React.createElement("div", {
    onClickCapture: e => {
      const a = e.target.closest("a");
      if (a && a.textContent === "Overview") {
        e.preventDefault();
        e.stopPropagation();
        onNav("overview");
      }
    }
  }, /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--page)",
      margin: "0 auto",
      padding: "3rem 1rem 4.5rem"
    }
  }, /*#__PURE__*/React.createElement(PageHead, {
    crumb: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => {
        e.preventDefault();
        onNav("overview");
      },
      style: {
        color: "var(--color-text-muted)"
      }
    }, "Overview"), " ", "›", " Why this design"),
    title: "Why this design looks like this",
    lede: /*#__PURE__*/React.createElement(React.Fragment, null, "Almost nothing in Simic is speculative caution. Each defensive mechanism traces to a specific, documented failure — and each forward step is something the record earned the right to attempt.")
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--measure)"
    }
  }, /*#__PURE__*/React.createElement("h2", null, "The record this design answers"), /*#__PURE__*/React.createElement("p", null, "Simic is the third incarnation of one research programme. Early versions of the simic project (known as esper) built the morphogenetic chassis this design retains — reversible slots, staged maturation, lifecycle states — and that working record is the proximate reason for every major choice made here."), /*#__PURE__*/React.createElement("h2", null, "The pivot, stated plainly"), /*#__PURE__*/React.createElement("p", null, "This design ", /*#__PURE__*/React.createElement("strong", null, "replaces the reward function with measured counterfactuals"), ". Paired branches from one snapshot over identical futures cancel ordinary-training variance, so the difference between branches ", /*#__PURE__*/React.createElement("em", null, "is"), " the intervention effect."), /*#__PURE__*/React.createElement(CanonQuote, null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0
    }
  }, /*#__PURE__*/React.createElement("strong", null, "A model can hallucinate an interface, then use permissive access idioms to hide the hallucination behind silent defaults."))), /*#__PURE__*/React.createElement(Note, {
    label: "Read the claims against this"
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0
    }
  }, "Part of the expected improvement — dense per-step labels, attributable failures — is a training-procedure win that could arguably have been retrofitted to the earlier system. The architecture's irreducible contributions are the ones that could not: ", /*#__PURE__*/React.createElement("strong", null, "generated (not selected) structure, separated authorities, and provider blindness."))), /*#__PURE__*/React.createElement("h2", null, "Armour and forward motion"), /*#__PURE__*/React.createElement(CanonQuote, {
    cite: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("code", null, "docs/design/03-principles.md"), " \xA76.20")
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0
    }
  }, /*#__PURE__*/React.createElement("strong", null, "Where capability was validated, push forward; where the programme struggled, build armour.")))), /*#__PURE__*/React.createElement(Split, {
    left: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("h3", {
      style: {
        marginTop: 0
      }
    }, "The armour"), /*#__PURE__*/React.createElement("p", null, "Every mechanism that makes a documented failure class ", /*#__PURE__*/React.createElement("em", null, "unrepresentable"), " rather than policed. It faces in two directions, matching the two strata.")),
    right: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("h3", {
      style: {
        marginTop: 0
      }
    }, "The forward motion"), /*#__PURE__*/React.createElement("p", null, "What the record earned the right to attempt. Telemetry-conditioned structural decisions are ", /*#__PURE__*/React.createElement("em", null, "proven"), " sufficient."))
  }), /*#__PURE__*/React.createElement(Spine, {
    items: [{
      title: "Do not strip armour to speed the forward motion, and do not restrict the forward motion because the armour is heavy.",
      body: "The armour is why the forward signal exists."
    }, {
      title: "Armour must cite its scar.",
      body: "A proposed new constraint that cannot name the failure it prevents is bureaucracy, not armour."
    }]
  }), /*#__PURE__*/React.createElement(CardGrid, {
    cards: [{
      title: "The architecture →",
      body: "Fourteen bounded domains, the canonical sentence, the newsroom routing rule, and the sentence test used as a lint."
    }, {
      title: "The guarantees →",
      body: "The invariant spine each piece of armour is written into — cited as INV-nn throughout the design."
    }]
  })))), /*#__PURE__*/React.createElement(SiteFooter, null));
}
window.LineageScreen = LineageScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/website/LineageScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/website/OverviewScreen.jsx
try { (() => {
const DS = window.SimicDesignSystem_5a908e;
function OverviewScreen({
  onNav
}) {
  const {
    Masthead,
    SiteFooter,
    PageHead,
    Note,
    CanonQuote,
    Spine,
    DataTable,
    Diagram
  } = DS;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--color-bg)",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement(Masthead, {
    current: "Overview",
    items: [["Overview", "#"], ["Architecture", "#"], ["Why this design", "#"], ["Design docs", "#"], ["Source", "#"]].map(([l, h]) => [l, h])
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: "100%"
    },
    onClickCapture: e => {
      const a = e.target.closest("a");
      if (a && a.textContent === "Why this design") {
        e.preventDefault();
        e.stopPropagation();
        onNav("lineage");
      }
    }
  }, /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--page)",
      margin: "0 auto",
      padding: "3rem 1rem 4.5rem"
    }
  }, /*#__PURE__*/React.createElement(PageHead, {
    title: "Simic",
    tagline: "Counterfactual Generative Morphogenesis",
    lede: /*#__PURE__*/React.createElement(React.Fragment, null, "New neural structure is ", /*#__PURE__*/React.createElement("strong", null, "generated from the live state of a host network"), " — not selected from a fixed menu of human-authored blueprints — then causally screened against doing nothing. Measured counterfactuals instead of a reward function.")
  }), /*#__PURE__*/React.createElement(Note, {
    label: "Project status",
    status: true
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0
    }
  }, /*#__PURE__*/React.createElement("strong", null, "Pre-implementation bootstrap."), " The design is complete and locked — HLD v4.1, Namespec 1.0 — and a Python scaffold exists, but there is ", /*#__PURE__*/React.createElement("strong", null, "no functional code yet"), ". First engineering work is Phase A: Namespec, Leyline contracts, and dependency boundaries. Nothing on this site describes a running system or a measured result.")), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--measure)"
    }
  }, /*#__PURE__*/React.createElement("h2", null, "The idea"), /*#__PURE__*/React.createElement("p", null, "Growing a neural network at runtime raises four questions that existing systems tend to blur together: ", /*#__PURE__*/React.createElement("em", null, "what"), " new structure to add, ", /*#__PURE__*/React.createElement("em", null, "whether"), " it is structurally sound, ", /*#__PURE__*/React.createElement("em", null, "whether"), " it actually helps, and ", /*#__PURE__*/React.createElement("em", null, "who"), " gets to decide. Simic separates those concerns constitutionally."), /*#__PURE__*/React.createElement("p", null, "Structure is designed from live host telemetry; verified and canonicalised; compiled without semantic change; tested in flash-cloned counterfactual branches that share an identical future with the mainline; and admitted only if it beats a ", /*#__PURE__*/React.createElement("strong", null, "mandatory no-op alternative"), " under a provider-blind judge. Everything — including failures, rejected pools, and no-op wins — is retained as history."), /*#__PURE__*/React.createElement("h3", null, "The loop, end to end")), /*#__PURE__*/React.createElement(Diagram, {
    lightSrc: "../../assets/diagrams/core-loop-light.svg",
    darkSrc: "../../assets/diagrams/core-loop-dark.svg",
    label: "Flowchart of the core loop",
    minWidth: 600,
    caption: /*#__PURE__*/React.createElement(React.Fragment, null, "The ordinary host-training loop and the growth loop share one execution reality, and the candidate pool is allowed to lose. Source: ", /*#__PURE__*/React.createElement("code", null, "docs/design/01-claim.md"), " \xA71.")
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--measure)"
    }
  }, /*#__PURE__*/React.createElement("h2", null, "Guarantees"), /*#__PURE__*/React.createElement("p", null, "The constitution defines 45 blocking invariants, cited throughout the design as ", /*#__PURE__*/React.createElement("code", null, "INV-nn"), ". The spine:")), /*#__PURE__*/React.createElement(Spine, {
    items: [{
      title: "Determinism",
      inv: "INV-05",
      body: "Identical snapshot plus identical future data produces bitwise-identical traces under the Academy execution profile."
    }, {
      title: "Doing nothing is a real competitor",
      inv: "INV-15, INV-16",
      body: "Every admission and tenancy review includes a measured no-intervention branch with policy utility exactly zero. The whole candidate pool may lose to it."
    }, {
      title: "Tail risk cannot be bought",
      inv: "INV-45",
      body: "Admission is lexicographic: the tail-risk veto is adjudicated before any utility comparison, and no measured benefit can offset it."
    }, {
      title: "Absent signal stays absent",
      inv: "INV-38",
      body: "Invariant breaches fail loudly and visibly. A missing telemetry field never becomes a zero."
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: "var(--measure)"
    }
  }, /*#__PURE__*/React.createElement("h2", null, "Fourteen domains, one sentence"), /*#__PURE__*/React.createElement("p", null, "Authority is split across fourteen bounded domains with deliberately vivid codenames. The names are not decoration: they act as an architecture linter."), /*#__PURE__*/React.createElement(CanonQuote, {
    cite: /*#__PURE__*/React.createElement(React.Fragment, null, "The canonical sentence — ", /*#__PURE__*/React.createElement("code", null, "docs/design/02-constitution.md"), " \xA75.3")
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0
    }
  }, "Under Leyline, Ugin plans, Aurelia commissions and acts, Nissa observes, Momir designs, Elesh conforms, Urabrask compiles, Jin-Gitaxias tests in Tolaria, Isperia judges, Wrenn embodies, Emrakul destroys, and Tamiyo reveals; every precedent is kept in Urborg.")), /*#__PURE__*/React.createElement("h2", null, "Where the design lives"), /*#__PURE__*/React.createElement("p", null, "The canonical authority is the HLD chapter set in the repository, not this site.")), /*#__PURE__*/React.createElement(DataTable, {
    caption: "Repository map",
    columns: ["Path", "Contents"],
    rows: [["docs/design/00-INDEX.md", "Entry point to the HLD chapter set, with reading paths"], ["docs/design/01-claim.md", "Executive summary, problem statement, goals, non-goals, the first defensible claim"], ["docs/design/02-constitution.md", "Naming constitution and the 45 blocking invariants"], ["docs/design/04-architecture.md", "System context, planes, and the control hierarchy"], ["src/simic/", "Target code layout: one package per domain (scaffold only, today)"]]
  })))), /*#__PURE__*/React.createElement(SiteFooter, null));
}
window.OverviewScreen = OverviewScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/website/OverviewScreen.jsx", error: String((e && e.message) || e) }); }

__ds_ns.CanonQuote = __ds_scope.CanonQuote;

__ds_ns.Note = __ds_scope.Note;

__ds_ns.PageHead = __ds_scope.PageHead;

__ds_ns.Spine = __ds_scope.Spine;

__ds_ns.CardGrid = __ds_scope.CardGrid;

__ds_ns.DataTable = __ds_scope.DataTable;

__ds_ns.Diagram = __ds_scope.Diagram;

__ds_ns.Split = __ds_scope.Split;

__ds_ns.Masthead = __ds_scope.Masthead;

__ds_ns.SiteFooter = __ds_scope.SiteFooter;

})();
