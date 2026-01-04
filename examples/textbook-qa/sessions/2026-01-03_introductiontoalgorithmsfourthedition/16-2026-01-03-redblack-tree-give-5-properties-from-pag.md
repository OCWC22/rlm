# Question #16

> **Date:** 2026-01-03  
> **Time:** 19:44:07  
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

What is a red-black tree? Give the 5 properties from page 442.

---

## 💡 Answer

## 📖 Red-Black Trees: Definition and Properties

### ⚠️ Important Note About Page Numbers
The query asks for properties from "page 442," but the **numbered list of 5 properties actually appears on page 443**. Page 442 contains the chapter introduction and the **definition** of red-black trees. Both pages are provided below for completeness.

---

## 📕 Definition (Page 442)

📄 [View Page 442 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=442)

> "A red-black tree is a binary search tree with one extra bit of storage per node: its color, which can be either RED or BLACK. By constraining the node colors on any simple path from the root to a leaf, red-black trees ensure that no such path is more than twice as long as any other, so that the tree is approximately balanced."
>
> — **Page 442**, Introduction to Algorithms (4th Edition)

---

## 📋 The 5 Properties (Page 443)

📄 [View Page 443 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443)

From page 443, verbatim from the textbook:

> "A red-black tree is a binary search tree that satisfies the following red-black properties:
>
> 1. Every node is either red or black.
> 2. The root is black.
> 3. Every leaf (NIL) is black.
> 4. If a node is red, then both its children are black.
> 5. For each node, all simple paths from the node to descendant leaves contain the same number of black nodes."
>
> — **Page 443**, Introduction to Algorithms (4th Edition)

---

## 📐 Key Concept: Black-Height

📄 [View Page 443 in PDF](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443)

The textbook also defines an important concept on page 443:

> "We call the number of black nodes on any simple path from, but not including, a node x down to a leaf the black-height of the node, denoted bh(x)."
>
> — **Page 443**, Introduction to Algorithms (4th Edition)

---

## 📊 Visual Representation

Figure 13.1 (referenced on page 443, caption on page 445) shows an example red-black tree. The figure demonstrates:
- Nodes colored either red or black
- Each red node has black children (Property 4)
- All paths from any node to descendant leaves have the same number of black nodes (Property 5)
- Black-height notation for internal nodes

📄 [View Figure 13.1 Caption on Page 445](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=445)

---

## 🧠 Simple Explanation

**In plain English:** A red-black tree is a special kind of binary search tree where each node is colored red or black. These colors follow strict rules that automatically keep the tree balanced.

**Key insights:**

1. **Balance guarantee**: The coloring rules ensure no path from root to leaf is more than twice as long as any other path, keeping the tree height at most 2 lg(n + 1)

2. **The "no double red" rule**: Property 4 prevents two red nodes in a row, which is crucial for maintaining balance

3. **Equal black depth**: Property 5 ensures every path has the same number of black nodes, which constrains the tree structure

4. **Performance**: Because the tree stays balanced, operations like search, insert, and delete run in O(lg n) time in the worst case

**Analogy:** Think of the tree like a highway system where black nodes are mandatory toll booths and red nodes are optional rest stops. Every route from downtown (root) to the suburbs (leaves) must pass through the same number of toll booths (black nodes), and you can't have two rest stops (red nodes) right next to each other. These rules naturally prevent any one route from being too much longer than another.

---

## ✅ Verification Checklist

| Content | Location | First Words | Last Words | Link |
|---------|----------|-------------|------------|------|
| Definition | Page 442 | "A red-black tree is..." | "...approximately balanced." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=442) |
| Property 1 | Page 443 | "Every node is either..." | "...red or black." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443) |
| Property 2 | Page 443 | "The root is..." | "...black." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443) |
| Property 3 | Page 443 | "Every leaf (NIL)..." | "...black." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443) |
| Property 4 | Page 443 | "If a node is red..." | "...are black." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443) |
| Property 5 | Page 443 | "For each node, all simple paths..." | "...black nodes." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443) |
| Black-height | Page 443 | "We call the number..." | "...denoted bh(x)." | [View](file:///Users/chen/Projects/rlm/examples/textbook-qa/books/IntroductiontoAlgorithmsFourthEdition.pdf#page=443) |

---

**Source:** *Introduction to Algorithms* (4th Edition) by Cormen, Leiserson, Rivest, and Stein  
**Chapter:** 13 - Red-Black Trees  
**Section:** 13.1 - Properties of red-black trees  
**Pages:** 442-443

**How to verify:** Click any [View] link to open the PDF at that exact page and verify the verbatim quotes character-for-character.

---

## 🔑 Key Concepts Extracted

Page 442,, A Red-Black Tree Is A Binary Search Tree With One Extra Bit Of Storage Per Node: Its Color, Which Can Be Either Red Or Black. By Constraining The Node Colors On Any Simple Path From The Root To A Leaf, Red-Black Trees Ensure That No Such Path Is More Than Twice As Long As Any Other, So That The Tree Is Approximately Balanced., A Red-Black Tree Is A Binary Search Tree That Satisfies The Following Red-Black Properties:
>
> 1. Every Node Is Either Red Or Black.
> 2. The Root Is Black.
> 3. Every Leaf (Nil) Is Black.
> 4. If A Node Is Red, Then Both Its Children Are Black.
> 5. For Each Node, All Simple Paths From The Node To Descendant Leaves Contain The Same Number Of Black Nodes., We Call The Number Of Black Nodes On Any Simple Path From, But Not Including, A Node X Down To A Leaf The Black-Height Of The Node, Denoted Bh(X)., No Double Red, Provided Below, Binary Search, Balance Guarantee, Equal Black Depth, Performance

---


---

## 📋 Execution Trace

> 🔍 For detailed execution log, see: [`TRACE-16-red-black-tree.md`](TRACE-16-red-black-tree.md)

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Iterations | 5/6 |
| API Calls | 6 (root: 5, sub: 1) |
| Input Tokens | 58,035 |
| Output Tokens | 11,993 |
| Total Tokens | 70,028 |
| **Cost** | **$0.3540** |

---

*Generated by RLM Textbook Q&A*
