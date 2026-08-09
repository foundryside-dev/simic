export function Diagram({ lightSrc, darkSrc, label, caption, minWidth = 0 }) {
  return (
    <figure style={{margin:"1.5rem 0",maxWidth:"var(--page)"}}>
      <div role="img" aria-label={label} style={{overflowX:"auto",paddingBlock:"0.5rem"}}>
        <picture>
          {darkSrc && <source srcSet={darkSrc} media="(prefers-color-scheme: dark)" />}
          <img src={lightSrc} alt="" style={{display:"block",height:"auto",maxWidth:"100%",minWidth,marginInline:"auto"}} />
        </picture>
      </div>
      {caption && <figcaption style={{fontSize:"0.85rem",color:"var(--color-text-muted)",marginTop:"0.5rem"}}>{caption}</figcaption>}
    </figure>
  );
}
