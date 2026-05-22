import logging
from config import get_settings

logger = logging.getLogger(__name__)

class KeyManager:
    def __init__(self):
        settings = get_settings()
        self.keys = []
        
        # Parse multiple keys from gemini_api_keys if configured
        if settings.gemini_api_keys:
            self.keys = [k.strip() for k in settings.gemini_api_keys.split(",") if k.strip()]
            
        # Fallback to single gemini_api_key if keys list is empty
        if not self.keys and settings.gemini_api_key:
            self.keys = [settings.gemini_api_key]
            
        self.current_index = 0
        logger.info(f"[KeyManager] Initialized with {len(self.keys)} API key(s).")

    def get_key(self) -> str:
        if not self.keys:
            raise RuntimeError("No Gemini API keys configured.")
        return self.keys[self.current_index]

    def rotate_key(self) -> str:
        if len(self.keys) <= 1:
            logger.warning("[KeyManager] Only one API key configured. Rotation has no effect.")
            return self.get_key()
            
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        logger.warning(
            f"[KeyManager] API Key rotated from index {old_index} to {self.current_index} "
            f"({self.get_key()[:8]}...)"
        )
        
        self._clear_caches()
        return self.get_key()

    def _clear_caches(self):
        """
        Clears client caches dynamically to ensure they pick up the newly active key.
        Uses local imports to prevent circular dependency issues.
        """
        try:
            import services.rag_pipeline
            services.rag_pipeline._get_llm.cache_clear()
            logger.info("[KeyManager] Cleared _get_llm cache in rag_pipeline.")
        except Exception as e:
            logger.warning(f"[KeyManager] Failed to clear rag_pipeline cache: {e}")
            
        try:
            import services.embedder
            services.embedder.get_embeddings.cache_clear()
            services.embedder.get_vector_store.cache_clear()
            logger.info("[KeyManager] Cleared get_embeddings and get_vector_store caches in embedder.")
        except Exception as e:
            logger.warning(f"[KeyManager] Failed to clear embedder caches: {e}")

# Global instance
key_manager = KeyManager()
