# Question #18

> **Date:** 2026-01-03  
> **Time:** 19:58:49  
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

explain binary search trees

---

## 💡 Answer

## 📖 Verbatim from Textbook

### Definition (Pages 418-419)
📄 [View Page 418](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=418)

> "A binary search tree is organized, as the name suggests, in a binary tree, as shown in Figure 12.1."
>
> — Page 418

### The Binary-Search-Tree Property (Page 420)
📄 [View Page 420](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=420)

> "The keys in a binary search tree are always stored in such a way as to satisfy the binary-search-tree property:
>
> Let x be a node in a binary search tree. If y is a node in the left subtree of x, then y.key ≤ x.key. If y is a node in the right subtree of x, then y.key ≥ x.key."
>
> — Page 420

### Performance Characteristics (Page 418)
📄 [View Page 418](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=418)

> "Basic operations on a binary search tree take time proportional to the height of the tree. For a complete binary tree with n nodes, such operations run in Θ(lg n) worst-case time. If the tree is a linear chain of n nodes, however, the same operations take Θ(n) worst-case time."
>
> — Page 418

---

## 📊 Diagrams & Figures

### Figure 12.1: Binary Search Trees (Page 420)
📄 [View Figure on Page 420](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=420)

**Tree (a) - Balanced BST with height 2:**
```
           6
         /   \
        5     7
       / \     \
      2   5     8
```

> Caption: "For any node x, the keys in the left subtree of x are at most x.key, and the keys in the right subtree of x are at least x.key."
>
> Inorder traversal prints: 2, 5, 5, 6, 7, 8 (sorted order)

---

## 🔧 BST Algorithms (Pseudocode)

### INORDER-TREE-WALK (Page 421)
📄 [View Page 421](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=421)

```
INORDER-TREE-WALK(x)
1 if x ≠ NIL
2    INORDER-TREE-WALK(x.left)
3    print x.key
4    INORDER-TREE-WALK(x.right)
```

### TREE-SEARCH (Pages 423-424)
📄 [View Page 423](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=423)

```
TREE-SEARCH(x, k)
1 if x == NIL or k == x.key
2     return x
3 if k < x.key
4     return TREE-SEARCH(x.left, k)
5 else return TREE-SEARCH(x.right, k)
```

### ITERATIVE-TREE-SEARCH (Page 424)
📄 [View Page 424](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=424)

```
ITERATIVE-TREE-SEARCH(x, k)
1 while x ≠ NIL and k ≠ x.key
2     if k < x.key
3         x = x.left
4     else x = x.right
5 return x
```

### TREE-MINIMUM and TREE-MAXIMUM (Page 426)
📄 [View Page 426](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=426)

```
TREE-MINIMUM(x)
1 while x.left ≠ NIL
2    x = x.left
3 return x

TREE-MAXIMUM(x)
1 while x.right ≠ NIL
2    x = x.right
3 return x
```

### TREE-SUCCESSOR (Page 427)
📄 [View Page 427](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=427)

```
TREE-SUCCESSOR(x)
1 if x.right ≠ NIL
2     return TREE-MINIMUM(x.right)    // leftmost node in right subtree
3 else // find the lowest ancestor of x whose left child is an ancestor of x
4     y = x.p
5     while y ≠ NIL and x == y.right
6         x = y
7         y = y.p
8     return y
```

### TREE-INSERT (Page 430)
📄 [View Page 430](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=430)

```
TREE-INSERT(T, z)
  1 x = T.root                          // node being compared with z
  2 y = NIL                             // y will be parent of z
  3 while x ≠ NIL                       // descend until reaching a leaf
  4    y = x
  5    if z.key < x.key
  6        x = x.left
  7    else x = x.right
  8 z.p = y                             // found the location—insert z with parent y
  9 if y == NIL
 10    T.root = z                       // tree T was empty
 11 elseif z.key < y.key
 12    y.left = z
 13 else y.right = z
```

### TRANSPLANT Helper (Page 433)
📄 [View Page 433](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=433)

```
TRANSPLANT(T, u, v)
1 if u.p == NIL
2     T.root = v
3 elseif u == u.p.left
4     u.p.left = v
5 else u.p.right = v
6 if v ≠ NIL
7     v.p = u.p
```

### TREE-DELETE (Pages 434-435)
📄 [View Page 434](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=434)

```
TREE-DELETE(T, z)
  1 if z.left == NIL
  2     TRANSPLANT(T, z, z.right)      // replace z by its right child
  3 elseif z.right == NIL
  4     TRANSPLANT(T, z, z.left)       // replace z by its left child
  5 else y = TREE-MINIMUM(z.right)     // y is z's successor
  6     if y ≠ z.right                 // is y farther down the tree?
  7         TRANSPLANT(T, y, y.right)  // replace y by its right child
  8         y.right = z.right          // z's right child becomes
  9         y.right.p = y              //      y's right child
 10     TRANSPLANT(T, z, y)            // replace z by its successor y
 11     y.left = z.left                // and give z's left child to y,
 12     y.left.p = y                   //      which had no left child
```

---

## 🧠 Simple Explanation

**In plain English:** A binary search tree (BST) is a data structure where each node has at most two children, and all values in the left subtree are smaller than the node's value, while all values in the right subtree are larger. This property makes searching very efficient.

**Key points:**
1. **Binary-Search-Tree Property**: For any node x, all keys in its left subtree are ≤ x.key, and all keys in its right subtree are ≥ x.key
2. **Performance**: Operations take O(h) time where h is the height. For balanced trees, h = O(lg n), but for skewed trees, h = O(n)
3. **Core Operations**: Search, insert, delete, find minimum/maximum, find successor/predecessor
4. **Traversal**: Inorder traversal visits nodes in sorted order (left → root → right)
5. **Structure**: Each node has pointers to left child, right child, and parent

**Analogy:** Think of a BST like a decision tree for searching. At each node, you ask "Is my target less than or greater than this value?" and go left or right accordingly. Just like how you'd search for a word in a dictionary by repeatedly dividing the search space in half.

**Why it's useful:**
- Supports dynamic set operations (insert, delete, search) efficiently
- Can be used as both a dictionary and a priority queue
- Enables sorted traversal without explicit sorting
- Forms the basis for more advanced structures (red-black trees, AVL trees)

---

## ✅ Verification Checklist

| Content | Pages | Verified |
|---------|-------|----------|
| BST Definition | 418-419 | ✓ |
| BST Property | 420 | ✓ |
| Figure 12.1 | 420 | ✓ |
| INORDER-TREE-WALK | 421 | ✓ |
| TREE-SEARCH | 423-424 | ✓ |
| TREE-MINIMUM/MAXIMUM | 426 | ✓ |
| TREE-SUCCESSOR | 427 | ✓ |
| TREE-INSERT | 430 | ✓ |
| TRANSPLANT | 433 | ✓ |
| TREE-DELETE | 434-435 | ✓ |

---

**Source:** Chapter 12, *Introduction to Algorithms* (4th Edition)

**How to verify**: Click any [View Page N] link to open the PDF at that exact page in:
`/Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf`

---

## 🔑 Key Concepts Extracted

A Binary Search Tree Is Organized, As The Name Suggests, In A Binary Tree, As Shown In Figure 12.1., The Keys In A Binary Search Tree Are Always Stored In Such A Way As To Satisfy The Binary-Search-Tree Property:
>
> Let X Be A Node In A Binary Search Tree. If Y Is A Node In The Left Subtree Of X, Then Y.Key ≤ X.Key. If Y Is A Node In The Right Subtree Of X, Then Y.Key ≥ X.Key., Basic Operations On A Binary Search Tree Take Time Proportional To The Height Of The Tree. For A Complete Binary Tree With N Nodes, Such Operations Run In Θ(Lg N) Worst-Case Time. If The Tree Is A Linear Chain Of N Nodes, However, The Same Operations Take Θ(N) Worst-Case Time., For Any Node X, The Keys In The Left Subtree Of X Are At Most X.Key, And The Keys In The Right Subtree Of X Are At Least X.Key., Is My Target Less Than Or Greater Than This Value?, Always Stored, Node In, Binary, Performance, Core Operations

---


---

## 📋 Execution Trace

> 🔍 For detailed execution log, see: [`TRACE-18-binary-search-trees.md`](TRACE-18-binary-search-trees.md)

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Iterations | 8/10 |
| API Calls | 13 (root: 8, sub: 5) |
| Input Tokens | 142,192 |
| Output Tokens | 27,968 |
| Total Tokens | 170,160 |
| **Cost** | **$0.8461** |

---

*Generated by RLM Textbook Q&A*
