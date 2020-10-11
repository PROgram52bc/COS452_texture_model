class ModuleError(Exception):
    """ when a module is not implemented according to the specification """
    pass

def spearmanrank(seq1, seq2):
    """calculate the spearman's rank coefficient for two sequence

    :seq1: the first sequence
    :seq2: the second sequence
    :returns: a float number representing the rank result

    Note: the two sequence must contain the same set of elements

    """
    if len(seq1) != len(seq2):
        raise ValueError(f"the two sequences are of different length: {len(seq1)} and {len(seq2)}")
    n = len(seq1)
    idx = [ seq1.index(x) for x in seq2 ]
    d_total = 0
    for i,x in enumerate(idx):
        d_total += (x-i)**2
    return 1 - 6 * d_total / (n * (n**2 - 1))
