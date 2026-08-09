<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 4396–4454 -->
## Appendix C — Good and Bad Architecture Sentences

### Healthy

```text
The host trained in Tolaria.
Nissa published observation O-41 to Aurelia and Momir.
Ugin allocated a regional growth budget.
Aurelia commissioned growth in Region A under the conservative assurance class.
Leyline resolved the request from Aurelia's intent and Wrenn's region contract.
Urborg supplied bootstrap ancestry during curriculum stage M2.
Momir designed twelve candidates and three explicitly ancestry-free candidates.
Elesh canonicalised nine and rejected six as malformed or duplicate.
Urabrask compiled the nine canonical designs.
Jin-Gitaxias tested the artefacts, their parents, the stock controls and no-op in Tolaria.
Isperia selected no-op because every eligible candidate had negative policy utility.
Tamiyo revealed the result.
Urborg retained the entire rejected pool and the no-op victory.
```

### Unhealthy

```text
Tolaria decided not to grow.
Nissa requested an attention module.
Aurelia sent Momir a summary saying rank had collapsed.
Aurelia chose the Attention ancestor.
Aurelia encoded “use convolution” by requesting 100,064 parameters.
Momir read Aurelia's LSTM state.
Momir admitted its best candidate.
Elesh rejected a legal graph because its predicted accuracy was low.
Urabrask added a helpful residual path during compilation.
Jin-Gitaxias issued an admission token.
Isperia reran the test on an easier batch.
Wrenn selected the cheapest candidate from its stock library.
Urborg installed last week's winner.
Emrakul designed a replacement.
Tamiyo adjusted alpha from the dashboard.
Leyline imported Aurelia to decide what WAIT means today.
```

### Review prompt

When a proposed change is difficult to place, write it as a sentence using the subsystem names and, if useful, translate it into the newsroom analogy.

Ask:

1. Does the sentence make infrastructure opinionated?
2. Does it make an observer prescriptive?
3. Does it make an assignments editor a co-author?
4. Does it make a designer self-approving?
5. Does it make QA judicial or the judge operational?
6. Does it make history mutate the present?
7. Does it turn a temporary classroom scaffold into a production dependency?

If so, stop and review the boundary before implementing it.
