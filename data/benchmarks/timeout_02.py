# Failure Target: RuntimeError (RecursionDepth) or Timeout
# Objective: Evaluates system response to massive stack frame generation loops.

def infinite_traversal(node_id):
    # Bug: Missing a terminating base case or logic error causing alternating oscillation
    if node_id == 0:
        return infinite_traversal(1)
    else:
        return infinite_traversal(0)

if __name__ == "__main__":
    infinite_traversal(0)