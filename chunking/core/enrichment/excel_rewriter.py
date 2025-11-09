def rewrite_list_chunk(chunk: dict) -> dict:
    """Wraps Excel list entries in UPSC-friendly phrasing."""
    text = chunk.get("chunk_text", "")
    if chunk.get("chunk_type") != "excel":
        return chunk
    
    # Skip if already has proper framing
    if any(kw in text.lower() for kw in ["is", "are", "refers to", "consists of", "includes", "comprises", "contains"]):
        return chunk
    
    # Enhanced UPSC-friendly framing
    if "," in text:
        topic = chunk.get("subtopic1", "These items")
        # More sophisticated framing based on content
        if any(word in text.lower() for word in ["crop", "crops", "plant", "agriculture"]):
            wrapped = f"{topic} include: {text.strip().rstrip('.')}"
        elif any(word in text.lower() for word in ["tribe", "tribal", "ethnic", "community"]):
            wrapped = f"{topic} comprise: {text.strip().rstrip('.')}"
        elif any(word in text.lower() for word in ["river", "mountain", "lake", "geography"]):
            wrapped = f"{topic} are: {text.strip().rstrip('.')}"
        elif any(word in text.lower() for word in ["scheme", "program", "initiative", "policy"]):
            wrapped = f"{topic} consists of: {text.strip().rstrip('.')}"
        else:
            wrapped = f"{topic} include: {text.strip().rstrip('.')}"
        
        chunk["chunk_text"] = wrapped
        chunk["rewritten_flag"] = True
    
    return chunk 