| Host | Class | Impaired stage | Base width | w1/w2/w3 | Impaired mid width | Host params | Seed multiples (λ-predicted gain) | Role |
|---|---|---|---|---|---|---|---|---|
| F1 | capacity | 1 | 0.967 | 24/64/80 | 16 | 159,722 | norm 1.001x, λ-pred 0.000; attn 1.027x, λ-pred 0.001; conv_light 1.056x, λ-pred 0.002; conv_heavy 1.377x, λ-pred 0.012 (over cap) | counted |
| F2 | capacity | 1 | 0.894 | 24/56/72 | 8 | 126,514 | norm 1.001x, λ-pred 0.000; attn 1.030x, λ-pred 0.001; conv_light 1.062x, λ-pred 0.002; conv_heavy 1.416x, λ-pred 0.014 (over cap) | counted |
| F3 | spatial | 1 | 0.963 | 24/64/80 | — | 156,498 | norm 1.001x, λ-pred 0.000; attn 1.028x, λ-pred 0.001; conv_light 1.057x, λ-pred 0.002; conv_heavy 1.384x, λ-pred 0.013 (over cap) | counted |
| F4 | spatial | 2 | 0.906 | 24/56/72 | — | 94,594 | norm 1.001x, λ-pred 0.000; attn 1.040x, λ-pred 0.002; conv_light 1.082x, λ-pred 0.003; conv_heavy 1.556x, λ-pred 0.017 (over cap) | counted |
| F5 | depth | 2 | 1.236 | 32/80/96 | — | 186,826 | norm 1.001x, λ-pred 0.000; attn 1.029x, λ-pred 0.001; conv_light 1.059x, λ-pred 0.002; conv_heavy 1.402x, λ-pred 0.013 (over cap) | counted |
| F6 | depth | 1 | 0.951 | 24/64/80 | — | 156,450 | norm 1.001x, λ-pred 0.000; attn 1.028x, λ-pred 0.001; conv_light 1.057x, λ-pred 0.002; conv_heavy 1.384x, λ-pred 0.013 (over cap) | counted |
| S1 | honest-small | — | 0.500 | 16/32/40 | — | 43,242 | norm 1.002x, λ-pred 0.000; attn 1.051x, λ-pred 0.002; conv_light 1.104x, λ-pred 0.004 (over cap); conv_heavy 1.697x, λ-pred 0.021 (over cap) | descriptive |
| S2 | honest-small | — | 0.250 | 8/16/16 | — | 9,186 | norm 1.004x, λ-pred 0.000; attn 1.122x, λ-pred 0.004 (over cap); conv_light 1.253x, λ-pred 0.009 (over cap); conv_heavy 2.645x, λ-pred 0.038 (over cap) | descriptive |
| N0 | reference (negative control) | — | 1.000 | 24/64/80 | — | 161,682 | norm 1.001x, λ-pred 0.000; attn 1.027x, λ-pred 0.001; conv_light 1.055x, λ-pred 0.002; conv_heavy 1.372x, λ-pred 0.012 (over cap) | descriptive |
