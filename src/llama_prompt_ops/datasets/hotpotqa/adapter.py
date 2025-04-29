# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
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

# Import dspy for Example class
try:
    import dspy
    from dspy.primitives import Example as DSPyExample
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    # Fallback to dict if dspy not available
    DSPyExample = dict

from llama_prompt_ops.core.datasets import DatasetAdapter
from llama_prompt_ops.core.exceptions import DatasetError

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
        input_field: Union[str, List[str], Dict[str, str]] = None,
        golden_output_field: Union[str, List[str], Dict[str, str]] = None,
        context_field: str = None,
        supporting_facts_field: str = None,
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
            input_field: Field(s) to use as input (string, list, or dict)
            golden_output_field: Field to use as ground truth/reference output
            context_field: Field name for context passages
            supporting_facts_field: Field name for supporting facts
            **kwargs: Additional arguments
        """
        super().__init__(dataset_path, file_format or "json")
        self.passages_per_hop = passages_per_hop
        self.max_hops = max_hops
        self.retriever_url = retriever_url
        self.retriever = None
        
        # Store input and output field mappings
        self.input_field = input_field or "question"
        self.output_field = golden_output_field or "answer"
        self.context_field = context_field or "context"
        self.supporting_facts_field = supporting_facts_field or "supporting_facts"
        
        logger.info(f"Initialized HotpotQA adapter with input_field={self.input_field}, context_field={self.context_field}, supporting_facts_field={self.supporting_facts_field}, and output_field={self.output_field}")
        
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
    
    def _process_example(self, item: Dict[str, Any]) -> Optional[Any]:
        """
        Process a single example from the dataset.
        
        Args:
            item: The raw example from the dataset
            
        Returns:
            Standardized example with inputs and outputs fields for DSPy compatibility
        """
        try:
            # Extract required fields
            _id = item.get('_id', '')
            question = item.get('question', '')
            answer = item.get('answer', '')
            
            # Use the configured field names for context and supporting facts
            supporting_facts = item.get(self.supporting_facts_field, [])
            context = item.get(self.context_field, [])
            level = item.get('level', '')
            type_field = item.get('type', '')
            
            # Skip invalid examples
            if not question or not answer:
                return None
            
            # Create inputs and outputs dictionaries based on configured fields
            inputs = {}
            
            # Handle different types of input field configurations
            if isinstance(self.input_field, str):
                # Single input field
                inputs[self.input_field] = item.get(self.input_field, "")
                # Always add context field separately
                inputs[self.context_field] = context
            elif isinstance(self.input_field, list):
                # List of input fields
                for field in self.input_field:
                    if field == "question":
                        inputs[field] = question
                    elif field == self.context_field:
                        inputs[field] = context
                    else:
                        inputs[field] = item.get(field, "")
            elif isinstance(self.input_field, dict):
                # Dictionary mapping source fields to destination fields
                for src_field, dst_field in self.input_field.items():
                    if src_field == "question":
                        inputs[dst_field] = question
                    elif src_field == self.context_field:
                        inputs[dst_field] = context
                    else:
                        inputs[dst_field] = item.get(src_field, "")
            else:
                # Default to question and context
                inputs = {
                    "question": question,
                    self.context_field: context
                }
            
            # Create outputs dictionary based on configured output field
            outputs = {}
            if isinstance(self.output_field, str):
                outputs[self.output_field] = answer
            elif isinstance(self.output_field, list):
                for field in self.output_field:
                    if field == "answer":
                        outputs[field] = answer
                    else:
                        outputs[field] = item.get(field, "")
            elif isinstance(self.output_field, dict):
                for src_field, dst_field in self.output_field.items():
                    if src_field == "answer":
                        outputs[dst_field] = answer
                    else:
                        outputs[dst_field] = item.get(src_field, "")
            else:
                # Default to answer
                outputs = {
                    "answer": answer
                }
            
            # Always create a dictionary with the standardized format expected by create_dspy_example()
            # This ensures compatibility with the rest of the pipeline
            
            # Make sure the question is always included in inputs for consistency
            if "question" not in inputs and self.input_field != "question":
                inputs["question"] = question
                
            # Make sure the answer is always included in outputs for consistency
            if "answer" not in outputs and self.output_field != "answer":
                outputs["answer"] = answer
                
            example_dict = {
                "inputs": inputs,
                "outputs": outputs,
                "metadata": {
                    "_id": _id,
                    self.supporting_facts_field: supporting_facts,
                    "type": type_field,
                    "level": level
                }
            }
            
            # Log the created dictionary
            input_preview = {k: str(v)[:30] + '...' if isinstance(v, str) and len(str(v)) > 30 else v 
                           for k, v in inputs.items()}
            output_preview = {k: str(v)[:30] + '...' if isinstance(v, str) and len(str(v)) > 30 else v 
                            for k, v in outputs.items()}
            logger.debug(f"Created example dictionary with inputs: {input_preview} and outputs: {output_preview}")
            return example_dict
            
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
        if self.context_field not in processed["inputs"] and self.retriever:
            # Perform retrieval to get context
            retrieval_result = self.perform_multi_hop_retrieval(processed["inputs"]["question"])
            processed["inputs"][self.context_field] = retrieval_result.get("context", [])
        elif self.context_field not in processed["inputs"]:
            # No retriever available, use empty context
            processed["inputs"][self.context_field] = []
        
        # Format context as a string if it's a list of passages
        if isinstance(processed["inputs"][self.context_field], list):
            # Handle potential nested lists in the context field
            flattened_context = []
            for item in processed["inputs"][self.context_field]:
                if isinstance(item, list):
                    # If item is a list, extend our flattened context with string versions of each subitem
                    flattened_context.extend(str(subitem) for subitem in item)
                else:
                    # If item is not a list, just append the string version
                    flattened_context.append(str(item))
            
            # Join the flattened context items with double newlines
            processed["inputs"][self.context_field] = "\n\n".join(flattened_context)
        
        return processed
