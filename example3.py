from dataclasses import dataclass
from functools import reduce
from typing import Optional, Tuple

from purelint import pipe


@dataclass(frozen=True)
class TreeNode:
    value: int
    left: Optional["TreeNode"] = None
    right: Optional["TreeNode"] = None


# Insert value into tree
def insert(node: Optional[TreeNode], value: int) -> TreeNode:
    if node is None:
        return TreeNode(value)
    if value < node.value:
        return TreeNode(node.value, left=insert(node.left, value), right=node.right)
    else:
        return TreeNode(node.value, left=node.left, right=insert(node.right, value))


# Delete value from tree
def delete(node: Optional[TreeNode], value: int) -> Optional[TreeNode]:
    if node is None:
        return None
    if value < node.value:
        return TreeNode(node.value, left=delete(node.left, value), right=node.right)
    elif value > node.value:
        return TreeNode(node.value, left=node.left, right=delete(node.right, value))
    else:  # node to delete
        if node.left is None:
            return node.right
        if node.right is None:
            return node.left
        # Two children: replace with inorder successor
        successor_value = inorder(node.right)[0]
        return TreeNode(
            successor_value, left=node.left, right=delete(node.right, successor_value)
        )


# Search value
def contains(node: Optional[TreeNode], value: int) -> bool:
    if node is None:
        return False
    if value == node.value:
        return True
    if value < node.value:
        return contains(node.left, value)
    return contains(node.right, value)


# In-order traversal (returns tuple)
def inorder(node: Optional[TreeNode]) -> Tuple[int, ...]:
    if node is None:
        return ()
    return inorder(node.left) + (node.value,) + inorder(node.right)


# Initial values
values = (5, 3, 7, 2, 4, 6, 8)


# Build tree from values
def build_tree(vals):
    return reduce(insert, vals, None)


# Define a transformation pipeline
sorted_after_deletes = pipe(
    build_tree(values),  # start with tree
    lambda t: delete(t, 2),  # delete 2
    lambda t: delete(t, 5),  # delete 5
    inorder,  # get sorted tuple
)

print(sorted_after_deletes)  # (3, 4, 6, 7, 8)
