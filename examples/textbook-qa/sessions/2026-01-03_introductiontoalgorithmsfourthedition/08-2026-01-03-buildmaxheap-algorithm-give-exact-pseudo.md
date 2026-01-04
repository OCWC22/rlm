# Question #8

> **Date:** 2026-01-03  
> **Time:** 18:51:20  
> **Book:** Introductiontoalgorithmsfourthedition

---

## 📖 Metadata

| Property | Value |
|----------|-------|
| **Book** | Introductiontoalgorithmsfourthedition |
| **Pages** | 1,677 |
| **Words** | 463,574 |
| **Model** | `claude-sonnet-4-5-20250929` |

---

## ❓ Question

What is the BUILD-MAX-HEAP algorithm? Give me the EXACT pseudocode with line numbers from the textbook, copy it CHARACTER-FOR-CHARACTER. Include page links.

---

## 💡 Answer


I need to find the BUILD-MAX-HEAP algorithm pseudocode. Extract it EXACTLY as written, CHARACTER-FOR-CHARACTER.

CRITICAL REQUIREMENTS:
1. Copy the pseudocode VERBATIM - every character, space, and line number EXACTLY
2. Include the procedure name and all line numbers
3. Preserve all indentation exactly
4. Do NOT paraphrase or reformat
5. If you find it, extract the COMPLETE algorithm

Here is PAGE 154:
============================================================
example, we saw that the running time of merge sort can be described by
recurrence (2.3), T (n) = 2T (n/2) + Θ(n), on page 41. But if n is an odd
number, we really don’t have two problems of exactly half the size.
Rather, to ensure that the problem sizes are integers, we round one
subproblem down to size ⌊n/2⌋ and the other up to size ⌈n/2⌉, so the true
recurrence is T (n) = T (⌈n/2⌉ + T (⌊n/2⌋) + Θ(n). But this ﬂoors-and-
ceilings recurrence is longer to write and messier to deal with than
recurrence (2.3), which is deﬁned on the reals. We’d rather not worry
about ﬂoors and ceilings, if we don’t have to, especially since the two
recurrences have the same Θ(n lg n) solution.
The master method allows you to state a master recurrence without
ﬂoors and ceilings and implicitly infer them. No matter how the
arguments are rounded up or down to the nearest integer, the
asymptotic bounds that it provides remain the same. Moreover, as we’ll
see in Section 4.6, if you deﬁne your master recurrence on the reals,
without implicit ﬂoors and ceilings, the asymptotic bounds still don’t
change. Thus you can ignore ﬂoors and ceilings for master recurrences.
Section 4.7 gives sufﬁcient conditions for ignoring ﬂoors and ceilings in
more general divide-and-conquer recurrences.
The master theorem
The master method depends upon the following theorem.
Theorem 4.1 (Master theorem)
Let a > 0 and b > 1 be constants, and let f (n) be a driving function that
is deﬁned and nonnegative on all sufﬁciently large reals. Deﬁne the
recurrence T (n) on n ∈ N by
where aT (n/b) actually means a′T (⌊n/b⌋) + a″T (⌈n/b⌉) for some
constants a′ ≥ 0 and a″ ≥ 0 satisfying a = a′ + a″. Then the asymptotic
behavior of T (n) can be characterized as follows:
1. If there exists a constant ϵ > 0 such that 
, then 
.
www.konkur.in
Telegram: @uni_k


============================================================

Here is PAGE 157:
============================================================
we can apply case 1 of the master theorem to conclude that the solution
is T (n) = Θ(n2).
Now consider the recurrence T (n) = T (2n/3) + 1, which has a = 1
and b = 3/2, which means that the watershed function is 
. 
Case 
2 
applies 
since 
. The solution to the recurrence is T (n)
= Θ(lg n).
For the recurrence T (n) = 3T (n/4) + n lg n, we have a = 3 and b = 4,
which 
means 
that 
. 
Since 
, where ϵ can be as large as approximately 0.2,
case 3 applies as long as the regularity condition holds for f (n). It does,
because for sufﬁciently large n, we have that af (n/b) = 3(n/4) lg(n/4) ≤
(3/4)n lg n = cf (n) for c = 3/4. By case 3, the solution to the recurrence is
T (n) = Θ(n lg n).
Next, let’s look at the recurrence T (n) = 2T (n/2) + n lg n, where we
have a = 2, b = 2, and 
. Case 2 applies since 
. We conclude that the solution is T (n) = Θ(n
lg2 n).
We can use the master method to solve the recurrences we saw in
Sections 2.3.2, 4.1, and 4.2.
Recurrence (2.3), T (n) = 2T (n/2) + Θ(n), on page 41, characterizes
the running time of merge sort. Since a = 2 and b = 2, the watershed
function is 
. Case 2 applies because f (n) = Θ(n), and
the solution is T (n) = Θ(n lg n).
Recurrence (4.9), T (n) = 8T (n/2) + Θ(1), on page 84, describes the
running 
time 
of 
the 
simple 
recursive 
algorithm for 
matrix
multiplication. We have a = 8 and b = 2, which means that the
watershed function is 
. Since n3 is polynomially
larger than the driving function f (n) = Θ(1)—indeed, we have f (n) =
O(n3–ϵ) for any positive ϵ < 3—case 1 applies. We conclude that T (n)
= Θ(n3).
Finally, recurrence (4.10), T (n) = 7T (n/2) + Θ(n2), on page 87, arose
from the analysis of Strassen’s algorithm for matrix multiplication. For
www.konkur.in
Telegram: @uni_k


============================================================

Extract the BUILD-MAX-HEAP pseudocode EXACTLY as written. Include line numbers.


---

## 🔑 Key Concepts Extracted

Integers, Rounded Up, Copy The Pseudocode Verbatim, Include The Procedure Name And All Line Numbers, Preserve All Indentation Exactly, Do Not Paraphrase Or Reformat, But If N Is An Odd

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Iterations | 3/10 |
| API Calls | 7 (root: 3, sub: 4) |
| Input Tokens | 37,240 |
| Output Tokens | 9,553 |
| Total Tokens | 46,793 |
| **Cost** | **$0.2550** |

---

*Generated by RLM Textbook Q&A*
