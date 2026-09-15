def traverse_tree(node, values):
    """Clean recursive tree traversal O(N)."""
    if not node:
        return
    values.append(node.value)
    traverse_tree(node.left, values)
    traverse_tree(node.right, values)
