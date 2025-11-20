from typing import List


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Découpe un texte en chunks avec chevauchement, en essayant de couper proprement.
    Approche simple basée sur les caractères (robuste sans tokenizer).
    Garantit toujours une progression pour éviter les boucles infinies.
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
        # Si aucun séparateur utile ou si le séparateur est trop tôt (dans la zone de chevauchement),
        # on coupe en fin de fenêtre pour garantir un avancement strict.
        if cut == -1 or end == n or cut <= chunk_overlap:
            cut = len(candidate)

        chunk = candidate[:cut].strip()
        if chunk:
            chunks.append(chunk)

        if end == n:
            break

        # Avancer avec chevauchement
        next_start = start + cut - chunk_overlap
        # Garde-fou supplémentaire: garantir une progression stricte
        if next_start <= start:
            next_start = start + max(1, chunk_size - chunk_overlap)
        start = next_start

    return chunks
