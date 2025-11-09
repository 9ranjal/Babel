from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
MODEL_NAME = "BAAI/bge-large-en-v1.5"
_model = SentenceTransformer(MODEL_NAME)
EMBEDDING_DIMENSION = 1024

def get_embedding(text: str, normalize: bool = True, chunk_id: str = None) -> dict:
    """
    Generates an embedding for a given text using the BGE model.

    Args:
        text (str): The text to embed.
        normalize (bool): Whether to normalize the embedding.
        chunk_id (str): Optional chunk ID for error logging.

    Returns:
        dict: Embedding with vector and metadata.
    """
    if not text or not isinstance(text, str):
        if chunk_id:
            logger.warning(f"Empty or invalid text for chunk {chunk_id}")
        return {
            "vector": [0.0] * EMBEDDING_DIMENSION,
            "model": MODEL_NAME,
            "dimension": EMBEDDING_DIMENSION,
            "norm": 0.0,
            "generated_at": datetime.now().isoformat(),
            "source": "core"
        }
    
    try:
        # Add the required instruction prefix for BGE models
        prefixed_text = f"Represent this passage for retrieval: {text}"
    
        embedding = _model.encode(prefixed_text, normalize_embeddings=normalize)
        vector = embedding.tolist()
        
        # Calculate norm if not normalized
        norm = float(np.linalg.norm(embedding)) if not normalize else 1.0
        
        result = {
            "vector": vector,
            "model": MODEL_NAME,
            "dimension": EMBEDDING_DIMENSION,
            "norm": norm,
            "generated_at": datetime.now().isoformat(),
            "source": "core"
        }
        
        if chunk_id:
            logger.debug(f"Successfully generated embedding for chunk {chunk_id}")
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to generate embedding for chunk {chunk_id or 'unknown'}: {str(e)}"
        logger.error(error_msg)
        
        # Return zero vector as fallback
        return {
            "vector": [0.0] * EMBEDDING_DIMENSION,
            "model": MODEL_NAME,
            "dimension": EMBEDDING_DIMENSION,
            "norm": 0.0,
            "generated_at": datetime.now().isoformat(),
            "source": "core"
        }

def get_embedding_model_name() -> str:
    return MODEL_NAME

# Optionally, batch version for speed

def compute_embeddings(texts: list, chunk_ids: list = None, normalize: bool = True) -> list:
    """
    Compute embeddings for a batch of texts.
    
    Args:
        texts: List of texts to embed
        chunk_ids: Optional list of chunk IDs for error logging
        normalize: Whether to normalize embeddings
        
    Returns:
        List of embedding dictionaries with metadata
    """
    if not texts:
        return []
    
    try:
        # Add instruction prefix for all texts
        prefixed_texts = [f"Represent this passage for retrieval: {text}" for text in texts]
        
        embeddings = _model.encode(prefixed_texts, show_progress_bar=True, normalize_embeddings=normalize)
        result = []
        
        for i, emb in enumerate(embeddings):
            vector = emb.tolist()
            norm = float(np.linalg.norm(emb)) if not normalize else 1.0
            
            embedding_dict = {
                "vector": vector,
                "model": MODEL_NAME,
                "dimension": EMBEDDING_DIMENSION,
                "norm": norm,
                "generated_at": datetime.now().isoformat(),
                "source": "core"
            }
            result.append(embedding_dict)
        
        if chunk_ids:
            logger.info(f"Successfully generated embeddings for {len(texts)} chunks")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {str(e)}")
        
        # Return zero vectors as fallback with individual chunk ID logging
        fallback_embeddings = []
        for i, text in enumerate(texts):
            chunk_id = chunk_ids[i] if chunk_ids and i < len(chunk_ids) else f"batch_{i}"
            logger.warning(f"Using fallback embedding for chunk {chunk_id}: {str(e)}")
            fallback_embeddings.append({
                "vector": [0.0] * EMBEDDING_DIMENSION,
                "model": MODEL_NAME,
                "dimension": EMBEDDING_DIMENSION,
                "norm": 0.0,
                "generated_at": datetime.now().isoformat(),
                "source": "core"
            })
        
        return fallback_embeddings 