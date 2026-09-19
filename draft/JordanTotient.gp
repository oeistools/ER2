\\ Jordan Totient Function
\\ Date:   14/Abr/2010
\\ Author: Enrique Pérez Herrero 
\\ email: psychgeometry@gmail.com
\\ link: http://psychedelic-geometry.blogspot.com/

print("-------------------------------------------------");
print("Jordan Totient Function");
print("Date:   08/Jan/2010");
print("Author: Enrique Perez Herrero");
print("Link:   http://psychedelic-geometry.blogspot.com/");
print("-------------------------------------------------");


\\ Function definitions:

jordantot(n,k)=sumdiv(n,d,d^k*moebius(n/d));
dedekindpsi(n)=jordantot(n,2)/eulerphi(n);

A000010(n)=eulerphi(n);
A007434(n)=jordantot(n,2);
A059376(n)=jordantot(n,3);
A059377(n)=jordantot(n,4);
A059378(n)=jordantot(n,5);
A069091(n)=jordantot(n,6);
A069092(n)=jordantot(n,7);
A069093(n)=jordantot(n,8);
A069094(n)=jordantot(n,9);
A069095(n)=jordantot(n,10);
A067858(n)=jordantot(n,n);

A067858(n)=jordantot(n,n);
A000225(n)=jordantot(2,n);
A001615(n)=dedekindpsi(n);
A160889(n)=jordantot(n,3)/jordantot(n);
A160891(n)=jordantot(n,4)/jordantot(n);
A160893(n)=jordantot(n,5)/jordantot(n);
A160895(n)=jordantot(n,6)/jordantot(n);
A160897(n)=jordantot(n,7)/jordantot(n);
A160908(n)=jordantot(n,8)/jordantot(n);
A160960(n)=jordantot(n,9)/jordantot(n);
A160957(n)=jordantot(n,10)/jordantot(n);
A160960(n)=jordantot(n,11)/jordantot(n);
A160972(n)=jordantot(n,12)/jordantot(n);
A161010(n)=jordantot(n,13)/jordantot(n);
A161025(n)=jordantot(n,14)/jordantot(n);
A161139(n)=jordantot(n,15)/jordantot(n);
A161167(n)=jordantot(n,16)/jordantot(n);
A161213(n)=jordantot(n,17)/jordantot(n);

A065958(n)=jordantot(n,4)/jordantot(n,2);
A065959(n)=jordantot(n,6)/jordantot(n,3);
A065960(n)=jordantot(n,8)/jordantot(n,4);

\\Array reading functions

A002260(n)=n-binomial(floor(1/2+sqrt(2*n)),2); 
A004736(n)=binomial(floor(3/2+sqrt(2*n)),2)-n+1; 

A059379(n)=jordantot(A004736(n),A002260(n));
A059380(n)=jordantot(A002260(n),A004736(n)); 


\\Adding Help
addhelp(jordantot,"jordantot(n,k): A generalization of eulerphi(n).");

addhelp(A000225,"A000225: 2^n - 1. (Sometimes called Mersenne numbers, although that name is usually reserved for A001348.)");
addhelp(A001615,"A001615: Dedekind psi function: n * Product_{p|n, p prime} (1 + 1/p).");
addhelp(A000010,"A000010: Euler totient function phi(n): count numbers <= n and prime to n.");
addhelp(A007434,"A007434: Jordan function J_2(n) (a generalization of phi(n)).");
addhelp(A059376,"A059376: Jordan function J_3(n).");
addhelp(A059377,"A059377: Jordan function J_4(n).");
addhelp(A059378,"A059378: Jordan function J_5(n).");
addhelp(A069091,"A069091: Jordan function J_6(n).");
addhelp(A069092,"A069092: Jordan function J_7(n).");
addhelp(A069093,"A069093: Jordan function J_8(n).");
addhelp(A069094,"A069094: Jordan function J_9(n).");
addhelp(A069095,"A069095: Jordan function J_10(n).");

addhelp(A067858,"A067858: J_n(n), where J is the Jordan function, J_n(n) = n^n product{p|n}(1 - 1/p^n), the product is over the distinct primes, p, dividing n.");

addhelp(A160889,"A160889: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 4.");
addhelp(A160891,"A160891: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 4.");
addhelp(A160893,"A160893: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 5.");
addhelp(A160895,"A160895: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 6.");
addhelp(A160897,"A160897: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 7.");
addhelp(A160908,"A160908: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 8.");
addhelp(A160953,"A160953: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 9.");
addhelp(A160957,"A160957: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 10.");
addhelp(A160960,"A160960: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 11.");
addhelp(A160972,"A160972: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 12.");
addhelp(A161010,"A161010: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 13.");
addhelp(A161025,"A161025: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 14.");
addhelp(A161139,"A161139: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 15.");
addhelp(A161167,"A161167: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 16.");
addhelp(A161213,"A161213: Sum_{d|n} Moebius(n/d)*d^(b-1)/phi(n) for b = 17.");

addhelp(A065958,"A065958: n^2*Product_{distinct primes p dividing n} (1+1/p^2).");
addhelp(A065959,"A065959: n^3*Product_{distinct primes p dividing n} (1+1/p^3).");
addhelp(A065960,"A065960: n^4*Product_{distinct primes p dividing n} (1+1/p^4).");

\\Array reading functions help.
addhelp(A002260,"A002260: Integers 1 to k followed by integers 1 to k+1 etc. (a fractal sequence).");
addhelp(A004736,"A004736: Triangle T(n,k)=n-k, n>=1, 0<=k<n. Fractal sequence formed by repeatedly appending strings m m-1 . . . 2 1.");
addhelp(A059379,"A059379: Array of values of Jordan function J_k(n) read by antidiagonals (version 1).");
addhelp(A059380,"A059380: Array of values of Jordan function J_k(n) read by antidiagonals (version 2).");

