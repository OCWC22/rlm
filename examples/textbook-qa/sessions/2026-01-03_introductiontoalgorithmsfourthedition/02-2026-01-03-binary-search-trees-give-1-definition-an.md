# Question #1

> **Date:** 2026-01-03  
> **Time:** 17:52:17  
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

What are binary search trees? Give me: 1) Definition and properties, 2) Key algorithms (insert, delete, search), 3) Traversal methods (inorder, preorder, postorder), 4) Common LeetCode patterns for BST problems

---

## 💡 Answer

# Binary Search Trees: A Comprehensive Guide

I'll provide a complete answer to your query about Binary Search Trees, covering all four requested topics.

## 1) Definition and Properties

**Definition:**
A Binary Search Tree (BST) is a hierarchical data structure where each node contains a value and has at most two children (left and right). The key defining property is that for every node:
- All values in the left subtree are **less than** the node's value
- All values in the right subtree are **greater than** the node's value

**Key Properties:**
- **Ordered structure**: Enables efficient searching, insertion, and deletion
- **Time Complexity**: Average case O(log n) for search, insert, and delete operations
- **Worst Case**: O(n) when the tree becomes skewed (essentially a linked list)
- **In-order traversal** produces values in sorted order
- **Space Complexity**: O(n) for storing n nodes

## 2) Key Algorithms

### **Search Operation**
```python
def search(root, target):
    if not root or root.val == target:
        return root
    if target < root.val:
        return search(root.left, target)
    return search(root.right, target)
```
Time: O(log n) average, O(n) worst

### **Insert Operation**
```python
def insert(root, val):
    if not root:
        return TreeNode(val)
    if val < root.val:
        root.left = insert(root.left, val)
    else:
        root.right = insert(root.right, val)
    return root
```
Time: O(log n) average, O(n) worst

### **Delete Operation**
```python
def delete(root, key):
    if not root:
        return None
    
    if key < root.val:
        root.left = delete(root.left, key)
    elif key > root.val:
        root.right = delete(root.right, key)
    else:
        # Node with one child or no child
        if not root.left:
            return root.right
        if not root.right:
            return root.left
        
        # Node with two children: get inorder successor
        min_larger = find_min(root.right)
        root.val = min_larger.val
        root.right = delete(root.right, min_larger.val)
    
    return root

def find_min(node):
    while node.left:
        node = node.left
    return node
```
Time: O(log n) average, O(n) worst

## 3) Traversal Methods

### **Inorder Traversal** (Left → Root → Right)
```python
def inorder(root):
    result = []
    if root:
        result.extend(inorder(root.left))
        result.append(root.val)
        result.extend(inorder(root.right))
    return result
```
**Output**: Values in ascending sorted order
**Use case**: Validating BST, getting sorted elements

### **Preorder Traversal** (Root → Left → Right)
```python
def preorder(root):
    result = []
    if root:
        result.append(root.val)
        result.extend(preorder(root.left))
        result.extend(preorder(root.right))
    return result
```
**Use case**: Creating a copy of the tree, prefix expressions

### **Postorder Traversal** (Left → Right → Root)
```python
def postorder(root):
    result = []
    if root:
        result.extend(postorder(root.left))
        result.extend(postorder(root.right))
        result.append(root.val)
    return result
```
**Use case**: Deleting the tree, postfix expressions

## 4) Common LeetCode Patterns for BST Problems

### **Pattern 1: Validation**
- **Validate BST**: Check if tree satisfies BST property using range constraints
```python
def isValidBST(root, min_val=float('-inf'), max_val=float('inf')):
    if not root:
        return True
    if root.val <= min_val or root.val >= max_val:
        return False
    return (isValidBST(root.left, min_val, root.val) and
            isValidBST(root.right, root.val, max_val))
```

### **Pattern 2: Search & Find**
- Kth smallest/largest element
- Lowest Common Ancestor (LCA)
- Search in BST
```python
def kthSmallest(root, k):
    # Inorder traversal approach
    stack, count = [], 0
    curr = root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        count += 1
        if count == k:
            return curr.val
        curr = curr.right
```

### **Pattern 3: Construction**
- Convert sorted array to BST
- Construct BST from preorder/postorder
```python
def sortedArrayToBST(nums):
    if not nums:
        return None
    mid = len(nums) // 2
    root = TreeNode(nums[mid])
    root.left = sortedArrayToBST(nums[:mid])
    root.right = sortedArrayToBST(nums[mid+1:])
    return root
```

### **Pattern 4: Modification**
- Insert/Delete node
- Convert BST to Greater Tree
- Trim BST

### **Pattern 5: Two Pointer/Iterator**
- Two Sum BST
- BST Iterator
- Inorder successor/predecessor

### **Common Techniques:**
1. **Recursive with bounds**: Pass min/max constraints
2. **Inorder traversal**: Leverage sorted property
3. **Iterative with stack**: Simulate recursion
4. **Morris Traversal**: O(1) space traversal
5. **DFS with state**: Track information during traversal

### **Key Problems to Practice:**
- LC 98: Validate Binary Search Tree
- LC 230: Kth Smallest Element in BST
- LC 235: Lowest Common Ancestor of BST
- LC 108: Convert Sorted Array to BST
- LC 450: Delete Node in BST
- LC 700: Search in BST
- LC 701: Insert into BST
- LC 538: Convert BST to Greater Tree

**Pro Tip**: Always remember that inorder traversal of BST gives sorted order—this is the foundation for many BST solutions!

---

## 🔑 Key Concepts Extracted

Hierarchical Data, Foundation For, Recursive With Bounds, Inorder Traversal, Iterative With Stack, Morris Traversal, Dfs With State

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Iterations | 1/10 |
| API Calls | 2 (root: 1, sub: 1) |
| Input Tokens | 1,680 |
| Output Tokens | 3,012 |
| Total Tokens | 4,692 |
| **Cost** | **$0.0502** |

---

*Generated by RLM Textbook Q&A*
