# Draws of generator G-0

**This file is the record of the draw.** The plan would pin these hosts as explicit configs and
never re-derive them at run time. The generator used numpy 2.5.1 (`uv.lock`), `default_rng`
(PCG64) and Python's `round`, which rounds half to even. numpy does not promise identical streams
across versions.

Seed 15000 is the only draw seed tried. That rests on the author's word. The first committed
generator (`6804678`) already uses width step 8, so git cannot show draw 0.

Draw 1's N0 row is the full-width reference, a descriptive control in revision 3. It does not
decide the reading.

## Draw 1 (current): widths rounded to multiples of 8

The output of `generator.py.txt`, verbatim; a re-run reproduces it byte for byte.

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

## Draw 0 (failed, superseded): widths rounded to multiples of 4

The same seed and the same random stream; only the rounding differs, so every host keeps its class, stage, base width and r.
The run stopped at F1, where `GroupNorm(8, 60)` cannot be built for the norm seed. It printed the table header, then failed. It printed no host rows and trained nothing.
The widths below were reconstructed on CPU from the same stream, not taken from the failed run's
output. The crash site matches: F1 is the first host with w2 = 60.

| Host | Class | Stage | Base width | w1/w2/w3 at step 4 | Impaired mid width | w2 divisible by 8 |
|---|---|---|---|---|---|---|
| F1 | capacity | 1 | 0.967 | 24/60/76 | 12 | no |
| F2 | capacity | 1 | 0.894 | 20/56/72 | 8 | yes |
| F3 | spatial | 1 | 0.963 | 24/60/76 | — | no |
| F4 | spatial | 2 | 0.906 | 20/56/72 | — | yes |
| F5 | depth | 2 | 1.236 | 28/80/100 | — | yes |
| F6 | depth | 1 | 0.951 | 24/60/76 | — | no |

Three of six hosts had a slot width the norm seed cannot use, so the rule changed to multiples of 8, which is what PDR-0057:159 and S3:333 already say. No host was re-drawn: class, stage, b and r are unchanged.

The rounding change did alter realised widths and one severity:
- F1: 24/60/76 with middle width 12 became 24/64/80 with middle width 16;
- F2: 20/56/72 became 24/56/72;
- F3 and F6: 24/60/76 became 24/64/80;
- F4: 20/56/72 became 24/56/72;
- F5: 28/80/100 became 32/80/96.
