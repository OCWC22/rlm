# Question #19

> **Date:** 2026-01-03  
> **Time:** 20:18:44  
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

what is binary search tree

---

## 💡 Answer

## 📖 Binary Search Tree - Verbatim from Textbook

### Definition: What is a Binary Search Tree?
📄 [View Page 418 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=418)

> "A binary search tree is organized, as the name suggests, in a binary tree, as shown in Figure 12.1. You can represent such a tree with a linked data structure, as in Section 10.3. In addition to a key and satellite data, each node object contains attributes left, right, and p that point to the nodes corresponding to its left child, its right child, and its parent, respectively. If a child or the parent is missing, the appropriate attribute contains the value NIL. The tree itself has an attribute root that points to the root node, or NIL if the tree is empty. The root node T.root is the only node in a tree T whose parent is NIL."
>
> — Pages 418-419

### The Binary-Search-Tree Property (Formal Definition)
📄 [View Page 420 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=420)

> "The keys in a binary search tree are always stored in such a way as to satisfy the binary-search-tree property:
>
> Let x be a node in a binary search tree. If y is a node in the left subtree of x, then y.key ≤ x.key. If y is a node in the right subtree of x, then y.key ≥ x.key."
>
> — Page 420

---

## 📊 Example Tree Structure

**Figure 12.1: Binary Search Trees** (Page 420)

```
Tree (a) - Height 2, 6 nodes:
         6
        / \
       /   \
      5     7
     / \     \
    2   5     8

Values in sorted order (inorder traversal): 2, 5, 5, 6, 7, 8
```

📄 [View Figure 12.1 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=420)

> "For any node x, the keys in the left subtree of x are at most x.key, and the keys in the right subtree of x are at least x.key."
>
> — Figure 12.1 caption, Page 420

### Example: How the Property Works
📄 [View Page 421 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=421)

> "Thus, in Figure 12.1(a), the key of the root is 6, the keys 2, 5, and 5 in its left subtree are no larger than 6, and the keys 7 and 8 in its right subtree are no smaller than 6. The same property holds for every node in the tree. For example, looking at the root's left child as the root of a subtree, this subtree root has the key 5, the key 2 in its left subtree is no larger than 5, and the key 5 in its right subtree is no smaller than 5."
>
> — Page 421

---

## 📝 Basic Operation: Inorder Tree Walk

### INORDER-TREE-WALK Algorithm (Verbatim Pseudocode)
📄 [View Page 421 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=421)

```
INORDER-TREE-WALK(x)
1 if x ≠ NIL
2    INORDER-TREE-WALK(x.left)
3    print x.key
4    INORDER-TREE-WALK(x.right)
```

> "Because of the binary-search-tree property, you can print out all the keys in a binary search tree in sorted order by a simple recursive algorithm, called an inorder tree walk... For example, the inorder tree walk prints the keys in each of the two binary search trees from Figure 12.1 in the order 2, 5, 5, 6, 7, 8."
>
> — Page 421

---

## 🧠 Simple Explanation

**In plain English:** A binary search tree is a way to organize data in a tree structure where each node has at most two children (left and right). The key property is that all values in the left subtree are smaller than or equal to the parent, and all values in the right subtree are greater than or equal to the parent. This property makes searching very efficient.

**Key points:**
1. **Structure**: Each node has a key, optional data, and pointers to left child, right child, and parent
2. **Ordering Property**: Left subtree ≤ parent ≤ Right subtree (for every node)
3. **Performance**: Operations take time proportional to tree height
   - Best case (balanced): Θ(lg n)
   - Worst case (linear chain): Θ(n)
4. **Inorder Traversal**: Visiting nodes in left-root-right order produces sorted output

**Analogy:** Think of a family tree where everyone on your left side of the family has shorter heights than you, and everyone on your right side is taller. This rule applies to every person in the tree, making it easy to find someone of a particular height.

---

## ✅ Verification Checklist

| Source | Page | First 5 Words | Last 5 Words | Link |
|--------|------|---------------|--------------|------|
| Definition | 418 | "A binary search tree is" | "whose parent is NIL." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=418) |
| BST Property | 420 | "Let x be a node" | "then y.key ≥ x.key." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=420) |
| Example | 421 | "Thus, in Figure 12.1(a), the" | "no smaller than 5." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=421) |
| Algorithm | 421 | "INORDER-TREE-WALK(x)" | "INORDER-TREE-WALK(x.right)" | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=421) |

---
**How to verify**: Click any [View] link to open the PDF at that exact page and see the original text.

**Source**: *Introduction to Algorithms, Fourth Edition* by Cormen, Leiserson, Rivest, and Stein, Chapter 12: Binary Search Trees

---

## 🔑 Key Concepts Extracted

A Binary Search Tree Is Organized, As The Name Suggests, In A Binary Tree, As Shown In Figure 12.1. You Can Represent Such A Tree With A Linked Data Structure, As In Section 10.3. In Addition To A Key And Satellite Data, Each Node Object Contains Attributes Left, Right, And P That Point To The Nodes Corresponding To Its Left Child, Its Right Child, And Its Parent, Respectively. If A Child Or The Parent Is Missing, The Appropriate Attribute Contains The Value Nil. The Tree Itself Has An Attribute Root That Points To The Root Node, Or Nil If The Tree Is Empty. The Root Node T.Root Is The Only Node In A Tree T Whose Parent Is Nil., The Keys In A Binary Search Tree Are Always Stored In Such A Way As To Satisfy The Binary-Search-Tree Property:
>
> Let X Be A Node In A Binary Search Tree. If Y Is A Node In The Left Subtree Of X, Then Y.Key ≤ X.Key. If Y Is A Node In The Right Subtree Of X, Then Y.Key ≥ X.Key., For Any Node X, The Keys In The Left Subtree Of X Are At Most X.Key, And The Keys In The Right Subtree Of X Are At Least X.Key., Thus, In Figure 12.1(A), The Key Of The Root Is 6, The Keys 2, 5, And 5 In Its Left Subtree Are No Larger Than 6, And The Keys 7 And 8 In Its Right Subtree Are No Smaller Than 6. The Same Property Holds For Every Node In The Tree. For Example, Looking At The Root'S Left Child As The Root Of A Subtree, This Subtree Root Has The Key 5, The Key 2 In Its Left Subtree Is No Larger Than 5, And The Key 5 In Its Right Subtree Is No Smaller Than 5., Because Of The Binary-Search-Tree Property, You Can Print Out All The Keys In A Binary Search Tree In Sorted Order By A Simple Recursive Algorithm, Called An Inorder Tree Walk... For Example, The Inorder Tree Walk Prints The Keys In Each Of The Two Binary Search Trees From Figure 12.1 In The Order 2, 5, 5, 6, 7, 8., Binary, Only Node, Always Stored, Structure, Ordering Property

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Iterations | 6/10 |
| API Calls | 10 (root: 6, sub: 4) |
| Input Tokens | 97,226 |
| Output Tokens | 16,988 |
| Total Tokens | 114,214 |
| **Cost** | **$0.5465** |

---

*Generated by RLM Textbook Q&A*
