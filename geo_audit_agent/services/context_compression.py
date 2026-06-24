# context_compression.py
import logging
import torch

logger = logging.getLogger(__name__)

class LLMLinguaCompressor:
    """Manages token compression on long web context inputs using LLMLingua perplexity checks."""
    
    def __init__(self, model_name: str = "microsoft/llmlingua-2-bert-base-multilingual-cased-meeting"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compressor = None
        self.model_name = model_name
        
    def _lazy_load_compressor(self):
        """Lazy loads PromptCompressor to minimize warm-up latency on system start."""
        if self.compressor is None:
            try:
                from llmlingua import PromptCompressor
                logger.info(f"Initializing LLMLingua model: {self.model_name} on device: {self.device}")
                self.compressor = PromptCompressor(
                    model_name=self.model_name,
                    device_map=self.device
                )
            except ImportError:
                logger.error("LLMLingua package not found. Run: pip install llmlingua")
                raise
                
    def compress_context(self, raw_context: str, target_rate: float = 0.30) -> str:
        """
        Compresses input context by target rate.
        - target_rate = 0.30 results in a 70% compression (retaining 30% of original tokens).
        """
        if not raw_context or len(raw_context.split()) < 50:
            # Skip compression on short contents to save processing overhead
            return raw_context
            
        self._lazy_load_compressor()
        
        try:
            # Run compression
            assert self.compressor is not None
            result = self.compressor.compress_prompt(
                prompt=raw_context,
                rate=target_rate,
                force_tokens=["[", "]", "{", "}", "schema", "brand"],  # Keep syntax elements preserved
                drop_consecutive=True
            )
            
            compressed_prompt = result.get("compressed_prompt", "")
            original_tokens = result.get("origin_tokens", len(raw_context.split()))
            compressed_tokens = result.get("compressed_tokens", len(compressed_prompt.split()))
            
            logger.info(f"Context compressed successfully from {original_tokens} to {compressed_tokens} tokens.")
            return compressed_prompt
        except Exception as e:
            logger.error(f"LLMLingua context compression failed: {e}. Falling back to raw text.")
            return raw_context
