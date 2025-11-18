from typing import List


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Découpe un texte en chunks avec chevauchement, en essayant de couper proprement.
    Approche simple basée sur les caractères (robuste sans tokenizer).
    """
    if not text:
        return []

    # Normaliser fins de lignes
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    chunks: List[str] = []
    start = 0
    n = len(text)

    # Garde-fou
    chunk_size = max(200, chunk_size)
    chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))

    while start < n:
        end = min(start + chunk_size, n)
        candidate = text[start:end]

        # Essayer de couper au dernier séparateur raisonnable
        cut = max(candidate.rfind("\n\n"), candidate.rfind("\n"), candidate.rfind(". "))
        if cut == -1 or (end == n):
            cut = len(candidate)

        chunk = candidate[:cut].strip()
        if chunk:
            chunks.append(chunk)

        if end == n:
            break

        # Avancer avec chevauchement
        start = start + cut - chunk_overlap
        if start < 0:
            start = 0

    return chunks

