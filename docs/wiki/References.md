# References

The algorithms in this project were implemented by the student team. The sources below were used to understand the theory and compare the implementation with established compiler techniques.

## Core references

1. Alfred V. Aho, Monica S. Lam, Ravi Sethi, and Jeffrey D. Ullman. *Compilers: Principles, Techniques, and Tools*. 2nd edition, Addison-Wesley, 2006. Relevant topics include lexical analysis, regular-expression translation, subset construction, and scanner behavior.

2. Ken Thompson. "Programming Techniques: Regular Expression Search Algorithm." *Communications of the ACM*, 11(6), 419-422, 1968. DOI: [10.1145/363347.363387](https://doi.org/10.1145/363347.363387).

3. Thomas Reps. "Maximal-Munch Tokenization in Linear Time." *ACM Transactions on Programming Languages and Systems*, 20(2), 259-273, 1998. DOI: [10.1145/276393.276394](https://doi.org/10.1145/276393.276394). An author-hosted copy is available from the [University of Wisconsin](https://research.cs.wisc.edu/wpis/papers/toplas98b.pdf).

## Project-specific note

The original CSC339 report also consulted course material and a Thompson-construction reference by Y. Manoj Kumar. Those sources informed the academic write-up. The code in this repository does not copy a lexer generator or a regular-expression engine.

## Scope of the claims

The cost analysis in this Wiki describes the implementation in this repository. In particular, the scanner keeps the last accepting position but may rescan lookahead after emitting a token. Its worst-case bound is therefore different from the linear-time method developed by Reps.
