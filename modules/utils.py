# modules/utils.py

def chunk_clauses_with_overlap(clauses, overlap_size=1):
    """
    Chunk clauses with overlapping context.

    Args:
        clauses (List[str]): List of clauses (already split).
        overlap_size (int): Number of clauses to overlap.

    Returns:
        List[str]: Chunked and overlapped clauses.
    """
    chunks = []
    for i in range(0, len(clauses), overlap_size + 1):
        chunk = clauses[max(0, i - overlap_size): i + 1 + overlap_size]
        chunks.append(" ".join(chunk))
    return chunks
