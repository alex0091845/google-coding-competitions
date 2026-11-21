# Problem log

One row per attempt. Re-attempts get a new row.

**Outcome:** `A` solved alone · `H` solved after a hint · `E` solved after reading the analysis · `X` unsolved / abandoned · `?` not recorded
**Mistake tags:** `read` misread statement · `edge` missed edge case · `off1` off-by-one · `algo` wrong idea · `tle` too slow · `mle` memory · `io` input/output bug · `impl` implementation bug

| Date | Problem | Contest | Topics | Outcome | Time | Tests (sample / sets) | Mistakes | Key lesson |
|------|---------|---------|--------|---------|------|-----------------------|----------|------------|
| 2026-11-21 | Building Palindromes | KS 2022 Practice Session 2 | prefix sums, bitmask parity | H | 93m | 1/1 · 2/2 | — (slow: stuck on representation) | Only parity matters → prefix XOR of a 26-bit int mask; query = one XOR + popcount ≤ 1 |
