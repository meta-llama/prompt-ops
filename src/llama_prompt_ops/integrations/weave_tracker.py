"""
W&B Weave integration for tracking prompts, datasets, and LLM calls.

Uses Weave's native classes:
- weave.StringPrompt for versioned prompts (with names)
- weave.Dataset for versioned datasets (with names)
- Automatic LLM tracing via weave.init()
"""
from typing import Dict, Any, Optional, List
import logging

try:
    import weave
    from weave import StringPrompt, Dataset
    WEAVE_AVAILABLE = True
except ImportError:
    WEAVE_AVAILABLE = False
    weave = None
    StringPrompt = None
    Dataset = None

from datasets import Dataset as HFDataset


logger = logging.getLogger(__name__)


class WeaveTracker:
    """
    Lightweight W&B Weave integration using native Weave classes.
    
    Provides:
    - Prompt versioning via weave.StringPrompt (named objects)
    - Dataset versioning via weave.Dataset (named objects)
    - Automatic LLM tracing via weave.init()
    """
    
    def __init__(
        self, 
        project_name: str,
        entity: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize Weave tracking.
        
        Args:
            project_name: Weave project name
            entity: W&B entity (optional)
            enabled: Whether tracking is enabled
        """
        self.project_name = project_name
        self.entity = entity
        self.enabled = enabled
        
        if not WEAVE_AVAILABLE:
            logger.warning("Weave not available. Install with: pip install weave")
            self.enabled = False
            return
            
        if self.enabled:
            self._initialize_weave()
    
    def _initialize_weave(self) -> None:
        """Initialize Weave project - enables automatic LLM tracing."""
        try:
            if self.entity:
                project_path = f"{self.entity}/{self.project_name}"
            else:
                project_path = self.project_name
                
            weave.init(project_path)
            logger.info(f"Weave initialized: {project_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weave: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Weave tracking is enabled."""
        return self.enabled and WEAVE_AVAILABLE
    
    def track_prompt_evolution(
        self,
        original_prompt: str,
        optimized_prompt: str,
        prompt_name: str = "system_prompt",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Track prompt evolution using the same named prompt for versioning.
        
        Args:
            original_prompt: Original prompt text
            optimized_prompt: Optimized prompt text
            prompt_name: Name for both versions (creates v1, v2, etc.)
            metadata: Optimization metadata (unused for now)
            
        Returns:
            Reference to published optimized prompt version
        """
        if not self.is_enabled():
            return None
            
        try:
            # Create StringPrompts (name goes with publish, not constructor)
            original = StringPrompt(original_prompt)
            optimized = StringPrompt(optimized_prompt)
            
            # Publish with same name to create versions
            weave.publish(original, name=prompt_name)
            optimized_ref = weave.publish(optimized, name=prompt_name)
            
            logger.info(f"Tracked prompt evolution: {optimized_ref}")
            return str(optimized_ref)
            
        except Exception as e:
            logger.error(f"Failed to track prompt evolution: {e}")
            return None
    
    def track_dataset(
        self,
        dataset: HFDataset,
        split: str = "train",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Track dataset using named weave.Dataset.
        
        Args:
            dataset: HuggingFace dataset to track
            split: Dataset split name
            metadata: Additional metadata (unused for now)
            
        Returns:
            Reference to published dataset
        """
        if not self.is_enabled():
            return None
            
        try:
            # Convert HF dataset to format expected by weave.Dataset
            rows = [dict(row) for row in dataset]
            
            # Create named Weave Dataset for auto-versioning
            weave_dataset = Dataset(
                name=f"dataset_{split}",
                rows=rows
            )
            
            # Publish dataset (automatically versioned by name)
            ref = weave.publish(weave_dataset)
            logger.info(f"Tracked dataset ({split}): {ref}")
            return str(ref)
            
        except Exception as e:
            logger.error(f"Failed to track dataset: {e}")
            return None
    
    def get_prompt(self, name: str = "system_prompt") -> Optional[StringPrompt]:
        """
        Retrieve prompt using Weave refs.
        
        Args:
            name: Prompt name to retrieve
            
        Returns:
            StringPrompt object, None if not found
        """
        if not self.is_enabled():
            return None
            
        try:
            ref = weave.ref(name)
            return ref.get()
        except Exception as e:
            logger.error(f"Failed to get prompt: {e}")
            return None
    
    def get_dataset(self, split: str = "train") -> Optional[Dataset]:
        """
        Retrieve dataset using Weave refs.
        
        Args:
            split: Dataset split to retrieve
            
        Returns:
            Dataset object, None if not found
        """
        if not self.is_enabled():
            return None
            
        try:
            ref = weave.ref(f"dataset_{split}")
            return ref.get()
        except Exception as e:
            logger.error(f"Failed to get dataset: {e}")
            return None