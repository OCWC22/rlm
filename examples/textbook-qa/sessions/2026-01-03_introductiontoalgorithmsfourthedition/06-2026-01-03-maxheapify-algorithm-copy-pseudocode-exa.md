# Question #1

> **Date:** 2026-01-03  
> **Time:** 18:29:07  
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

What is the MAX-HEAPIFY algorithm? Copy the pseudocode exactly from the textbook with page number.

---

## 💡 Answer

# MAX-HEAPIFY Algorithm

## PAGE NUMBER: [PAGE 234]

## Pseudocode (VERBATIM):

```
MAX-HEAPIFY(A, i)
  1 l = LEFT(i)
  2 r = RIGHT(i)
  3 if l ≤ A.heap-size and A[l] > A[i]
  4     largest = l
  5 else largest = i
  6 if r ≤ A.heap-size and A[r] > A[largest]
  7     largest = r
  8 if largest ≠ i
  9     exchange A[i] with A[largest]
 10     MAX-HEAPIFY(A, largest)
```

## Surrounding Explanatory Text:

**Text immediately before the algorithm:**

"The procedure MAX-HEAPIFY on the facing page maintains the max-heap property. Its inputs are an array A with the heap-size attribute and an index i into the array. When it is called, MAX-HEAPIFY assumes that the binary trees rooted at LEFT(i) and RIGHT(i) are max-heaps, but that A[i] might be smaller than its children, thus violating the max-heap property. MAX-HEAPIFY lets the value at A[i] "ﬂoat down" in the max-heap so that the subtree rooted at index i obeys the max-heap property.

Figure 6.2 illustrates the action of MAX-HEAPIFY. Each step determines the largest of the elements A[i], A[LEFT(i)], and A[RIGHT(i)] and stores the index of the largest element in largest. If A[i] is largest, then the subtree rooted at node i is already a max-heap and nothing else needs to be done. Otherwise, one of the two children contains the largest element. Positions i and largest swap their contents, which causes node i and its children to satisfy the max-heap property. The node indexed by largest, however, just had its value decreased, and thus the subtree rooted at largest might violate the max-heap property. Consequently, MAX-HEAPIFY calls itself recursively on that subtree."

**Text immediately after the algorithm:**

"To analyze MAX-HEAPIFY, let T (n) be the worst-case running time that the procedure takes on a subtree of size at most n. For a tree rooted at a given node i, the running time is the Θ(1) time to ﬁx up the relationships among the elements A[i], A[LEFT(i)], and A[RIGHT(i)], plus the time to run MAX-HEAPIFY on a subtree rooted at one of the children of node i (assuming that the recursive call occurs). The children's subtrees each have size at most 2n/3 (see Exercise 6.2-2), and therefore we can describe the running time of MAX-HEAPIFY by the recurrence

The solution to this recurrence, by case 2 of the master theorem (Theorem 4.1 on page 102), is T (n) = O(lg n). Alternatively, we can characterize the running time of MAX-HEAPIFY on a node of height h as O(h)."

---

## 🔑 Key Concepts Extracted

The Procedure Max-Heapify On The Facing Page Maintains The Max-Heap Property. Its Inputs Are An Array A With The Heap-Size Attribute And An Index I Into The Array. When It Is Called, Max-Heapify Assumes That The Binary Trees Rooted At Left(I) And Right(I) Are Max-Heaps, But That A[I] Might Be Smaller Than Its Children, Thus Violating The Max-Heap Property. Max-Heapify Lets The Value At A[I], In The Max-Heap So That The Subtree Rooted At Index I Obeys The Max-Heap Property.

Figure 6.2 Illustrates The Action Of Max-Heapify. Each Step Determines The Largest Of The Elements A[I], A[Left(I)], And A[Right(I)] And Stores The Index Of The Largest Element In Largest. If A[I] Is Largest, Then The Subtree Rooted At Node I Is Already A Max-Heap And Nothing Else Needs To Be Done. Otherwise, One Of The Two Children Contains The Largest Element. Positions I And Largest Swap Their Contents, Which Causes Node I And Its Children To Satisfy The Max-Heap Property. The Node Indexed By Largest, However, Just Had Its Value Decreased, And Thus The Subtree Rooted At Largest Might Violate The Max-Heap Property. Consequently, Max-Heapify Calls Itself Recursively On That Subtree., To Analyze Max-Heapify, Let T (N) Be The Worst-Case Running Time That The Procedure Takes On A Subtree Of Size At Most N. For A Tree Rooted At A Given Node I, The Running Time Is The Θ(1) Time To Fix Up The Relationships Among The Elements A[I], A[Left(I)], And A[Right(I)], Plus The Time To Run Max-Heapify On A Subtree Rooted At One Of The Children Of Node I (Assuming That The Recursive Call Occurs). The Children'S Subtrees Each Have Size At Most 2N/3 (See Exercise 6.2-2), And Therefore We Can Describe The Running Time Of Max-Heapify By The Recurrence

The Solution To This Recurrence, By Case 2 Of The Master Theorem (Theorem 4.1 On Page 102), Is T (N) = O(Lg N). Alternatively, We Can Characterize The Running Time Of Max-Heapify On A Node Of Height H As O(H)., An Array, Max

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Iterations | 2/6 |
| API Calls | 5 (root: 2, sub: 3) |
| Input Tokens | 53,873 |
| Output Tokens | 7,128 |
| Total Tokens | 61,001 |
| **Cost** | **$0.2685** |

---

*Generated by RLM Textbook Q&A*
