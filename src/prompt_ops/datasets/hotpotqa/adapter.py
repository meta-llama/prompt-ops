"""
HotpotQA adapter implementation.

This module provides an adapter for the HotpotQA dataset that handles
multi-hop retrieval and reasoning.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from prompt_ops.core.datasets import DatasetAdapter
from prompt_ops.core.exceptions import DatasetError

logger = logging.getLogger(__name__)

class HotpotQAAdapter(DatasetAdapter):
    """
    Adapter for the HotpotQA dataset that handles multi-hop retrieval.
    
    This adapter loads the HotpotQA dataset and provides functionality for
    multi-hop retrieval during the optimization process.
    """
    
    def __init__(
        self,
        dataset_path: str,
        file_format: str = None,
        passages_per_hop: int = 3,
        max_hops: int = 2,
        retriever_url: str = None,
        **kwargs
    ):
        """
        Initialize the HotpotQA adapter.
        
        Args:
            dataset_path: Path to the dataset file
            file_format: Format of the file (defaults to json)
            passages_per_hop: Number of passages to retrieve per hop
            max_hops: Maximum number of retrieval hops
            retriever_url: URL for the retriever service (optional)
            **kwargs: Additional arguments
        """
        super().__init__(dataset_path, file_format or "json")
        self.passages_per_hop = passages_per_hop
        self.max_hops = max_hops
        self.retriever_url = retriever_url
        self.retriever = None
        
        # Initialize retriever if URL is provided
        if retriever_url:
            try:
                # Import here to avoid dependency issues
                # Only import if retriever is actually needed
                from dspy.retrieve import ColBERTv2
                self.retriever = ColBERTv2(url=retriever_url)
                logger.info(f"Initialized retriever with URL: {retriever_url}")
            except ImportError:
                logger.warning("DSPy not installed. Retriever functionality will be limited.")
            except Exception as e:
                logger.warning(f"Failed to initialize retriever: {e}")
    
    def adapt(self) -> List[Dict[str, Any]]:
        """
        Load and adapt the HotpotQA dataset.
        
        Returns:
            List of standardized examples with question, answer, and supporting_facts fields
        """
        try:
            # Load the dataset
            dataset_path = str(self.dataset_path) if hasattr(self.dataset_path, '__fspath__') else self.dataset_path
            
            if not os.path.exists(dataset_path):
                raise DatasetError(f"Dataset file not found: {dataset_path}")
            
            if str(dataset_path).endswith('.json'):
                # Load from a JSON file
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                raise DatasetError(f"Unsupported file format: {dataset_path}")
            
            # Transform to standardized format
            standardized_examples = []
            
            # Handle different possible JSON structures
            if isinstance(data, dict) and "data" in data:
                # SQuAD-like format
                items = data["data"]
            elif isinstance(data, list):
                # Direct list format
                items = data
            else:
                raise DatasetError(f"Unrecognized dataset format in {self.dataset_path}")
            
            for item in items:
                example = self._process_example(item)
                if example:
                    standardized_examples.append(example)
            
            if not standardized_examples:
                logger.warning(f"No examples found in dataset: {self.dataset_path}")
            
            return standardized_examples
            
        except Exception as e:
            logger.error(f"Error adapting HotpotQA dataset: {e}")
            raise DatasetError(f"Failed to adapt HotpotQA dataset: {e}")
    
    def _process_example(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single example from the dataset.
        
        Args:
            item: The raw example from the dataset
            
        Returns:
            Standardized example or None if invalid
        """
        try:
            # Extract question and answer
            question = item.get('question', '')
            answer = item.get('answer', '')
            
            # Skip invalid examples
            if not question or not answer:
                return None
            
            # Extract supporting facts (for evaluation)
            supporting_facts = item.get('supporting_facts', [])
            gold_titles = []
            
            if supporting_facts:
                if isinstance(supporting_facts, list):
                    if supporting_facts and isinstance(supporting_facts[0], dict):
                        # Format: [{"title": "...", "sent_id": ...}, ...]
                        gold_titles = [fact.get('title', '') for fact in supporting_facts]
                    else:
                        # Format: ["title1", "title2", ...]
                        gold_titles = supporting_facts
            
            # Extract context if available
            context = item.get('context', [])
            if not context and self.retriever:
                # If no context is provided but we have a retriever, perform retrieval
                retrieval_result = self.perform_multi_hop_retrieval(question)
                context = retrieval_result.get("context", [])
            
            # Create standardized example with inputs and outputs dictionaries
            example = {
                "inputs": {
                    "question": question
                },
                "outputs": {
                    "answer": answer
                },
                "gold_titles": gold_titles
            }
            
            # Add context if available
            if context:
                example["inputs"]["context"] = context
            
            return example
            
        except Exception as e:
            logger.warning(f"Error processing example: {e}")
            return None
    
    def retrieve_passages(self, query: str, k: int = None) -> List[str]:
        """
        Retrieve passages for a given query using the configured retriever.
        
        Args:
            query: The search query
            k: Number of passages to retrieve (defaults to passages_per_hop)
            
        Returns:
            List of retrieved passages
        """
        if not self.retriever:
            logger.warning("Retriever not initialized. Cannot retrieve passages.")
            return []
        
        k = k or self.passages_per_hop
        try:
            return self.retriever.search(query, k=k)
        except Exception as e:
            logger.error(f"Error retrieving passages: {e}")
            return []
    
    def perform_multi_hop_retrieval(self, question: str) -> Dict[str, Any]:
        """
        Perform multi-hop retrieval for a given question.
        
        Args:
            question: The question to answer
            
        Returns:
            Dictionary with retrieved passages and intermediate queries
        """
        if not self.retriever:
            logger.warning("Retriever not initialized. Cannot perform multi-hop retrieval.")
            return {"context": [], "queries": []}
        
        context = []
        queries = []
        
        # First hop
        first_query = question  # In practice, you'd use an LM to generate a better query
        queries.append(first_query)
        first_hop_passages = self.retrieve_passages(first_query)
        context.extend(first_hop_passages)
        
        # Second hop (if configured)
        if self.max_hops > 1 and first_hop_passages:
            # In practice, you'd use an LM to generate a better second query based on first hop results
            second_query = f"{question} {' '.join(first_hop_passages[0].split()[:10])}"
            queries.append(second_query)
            second_hop_passages = self.retrieve_passages(second_query)
            context.extend(second_hop_passages)
        
        return {
            "context": context,
            "queries": queries
        }
    
    def preprocess_for_model(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess an example before sending it to the model.
        
        This method ensures that all necessary fields are present and
        performs multi-hop retrieval if needed.
        
        Args:
            example: The example to preprocess
            
        Returns:
            Preprocessed example
        """
        # Make a copy to avoid modifying the original
        processed = example.copy()
        
        # Ensure inputs and outputs dictionaries exist
        if "inputs" not in processed:
            processed["inputs"] = {}
        if "outputs" not in processed:
            processed["outputs"] = {}
        
        # Ensure question is present
        if "question" not in processed["inputs"]:
            logger.warning("Example missing question field")
            processed["inputs"]["question"] = ""
        
        # Ensure context is present
        if "context" not in processed["inputs"] and self.retriever:
            # Perform retrieval to get context
            retrieval_result = self.perform_multi_hop_retrieval(processed["inputs"]["question"])
            processed["inputs"]["context"] = retrieval_result.get("context", [])
        elif "context" not in processed["inputs"]:
            # No retriever available, use empty context
            processed["inputs"]["context"] = []
        
        # Format context as a string if it's a list
        if isinstance(processed["inputs"]["context"], list):
            processed["inputs"]["context"] = "\n\n".join(processed["inputs"]["context"])
        
        return processed
