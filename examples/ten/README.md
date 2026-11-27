# Ten programs in ER2

Short programs, one idea each, meant to be read in order. Run any of them with
`er2 examples/ten/01_mersenne.er2`; their exact output is checked by the golden tests
(`tests/examples/ten/`).

| Program | What it shows |
| --- | --- |
| [01_mersenne.er2](01_mersenne.er2) | Mersenne primes with `isprime`, and the Lucas-Lehmer test written in ER2 |
| [02_factorization.er2](02_factorization.er2) | `factor`, `divisors`, `sigma`; the perfect numbers below 10000 |
| [03_totient.er2](03_totient.er2) | Euler's `phi`: Gauss's divisor sum, Euler's theorem with `Mod`, the density 6/pi^2 |
| [04_moebius.er2](04_moebius.er2) | The Moebius function `mu` and the Mertens function |
| [05_algebra.er2](05_algebra.er2) | Polynomials over Q: `factor`, `expand`, `gcd`, `solve`, `discriminant` |
| [06_calculus.er2](06_calculus.er2) | `diff`, `integrate`, `limit` and `series`, exactly |
| [07_matrix.er2](07_matrix.er2) | An exact inverse, `det`, `solve`, `kernel` and `hermite_form` |
| [08_finite_field.er2](08_finite_field.er2) | `GF(7)` and `GF(8)`, and polynomials over F_p |
| [09_power_series.er2](09_power_series.er2) | Power series, the Fibonacci generating function, `series_reverse` |
| [10_number_field.er2](10_number_field.er2) | Q(sqrt(-5)), where unique factorization fails and ideals restore it |
