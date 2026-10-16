"""newick.py: read and write Newick trees without dependencies.

parse returns the tree as parallel lists (parent, branch length, name, children), node 0 the root; it is iterative, so deep
trees do not hit the recursion limit. Internal labels, such as an age interval, are kept as names. newick writes a subtree back.
"""
import re


def parse(s):
    """Newick to parallel lists: parent, branch length, name, children. Iterative, so deep trees are fine."""
    parent, length, name, children = [], [], [], []

    def new(p):
        parent.append(p); length.append(0.0); name.append(None); children.append([])
        if p >= 0: children[p].append(len(parent) - 1)
        return len(parent) - 1
    s = s.strip().rstrip(";"); cur = new(-1); i = 0; tok = re.compile(r"([^(),:;]*)(?::([0-9.eE+-]+))?")
    while i < len(s):
        c = s[i]
        if c == "(": cur = new(cur); i += 1
        elif c == ",": cur = new(parent[cur]); i += 1
        elif c == ")":
            cur = parent[cur]; m = tok.match(s, i + 1)
            if m.group(1): name[cur] = m.group(1)
            if m.group(2): length[cur] = float(m.group(2))
            i = m.end()
        else:
            m = tok.match(s, i); name[cur] = m.group(1) or None
            if m.group(2): length[cur] = float(m.group(2))
            i = m.end()
    return parent, length, name, children


def newick(children, length, name, v, top=True):
    """Subtree at v as Newick (the Cypriniformes subtree is a few hundred levels deep at most, so recursion is fine)."""
    tail = "" if top else f":{length[v]:.6f}"
    if not children[v]: return f"{name[v]}{tail}"
    return "(" + ",".join(newick(children, length, name, c, False) for c in children[v]) + ")" + (name[v] or "") + tail
