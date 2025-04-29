# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
"""
HotpotQA metric implementation.

This module provides metrics for evaluating HotpotQA predictions,
including answer correctness and supporting facts accuracy.
"""

import re
import string
import logging
from typing import Dict, List, Any, Optional, Union
from collections import Counter

from llama_prompt_ops.core.metrics import MetricBase

logger = logging.getLogger(__name__)

class HotpotQAMetric(MetricBase):
    """
    Metric for evaluating HotpotQA predictions.
    
    This metric evaluates both answer correctness and passage retrieval accuracy.
    """
    
    def __init__(
        self,
        output_field: str = "answer",
        strict_json: bool = False,
        passage_weight: float = 0.5,
        **kwargs
    ):
        """
        Initialize the HotpotQA metric.
        
        Args:
            output_field: Field name for the answer in the prediction
            strict_json: Whether to enforce strict JSON parsing
            passage_weight: Weight for passage retrieval in the combined score
            **kwargs: Additional arguments
        """
        self.output_field = output_field
        self.strict_json = strict_json
        self.passage_weight = passage_weight
    
    def __call__(self, gold: Any, pred: Any, trace: bool = False, **kwargs) -> float:
        """
        Call the metric to get a single score.
        
        Args:
            gold: The ground truth example
            pred: The model's prediction
            trace: Whether to enable tracing for debugging
            **kwargs: Additional metric-specific parameters
            
        Returns:
            Combined score as a float
        """
        results = self.evaluate(gold, pred, **kwargs)
        return results.get("combined_score", 0.0)
        
    def evaluate(self, ground_truth: Any, prediction: Any, **kwargs) -> Dict[str, Any]:
        """
        Evaluate a prediction against the ground truth following the official HotpotQA evaluation.
        
        Args:
            ground_truth: The ground truth example
            prediction: The model's prediction
            
        Returns:
            Dictionary with evaluation results
        """
        # Add detailed logging for debugging
        logger.info(f"Evaluating prediction against ground truth")
        logger.info(f"Ground truth type: {type(ground_truth)}")
        logger.info(f"Prediction type: {type(prediction)}")
        
        # Ensure ground_truth and prediction are not None
        if ground_truth is None or prediction is None:
            logger.warning(f"Ground truth or prediction is None: ground_truth={ground_truth}, prediction={prediction}")
            return {
                "answer_em": 0.0,
                "answer_f1": 0.0,
                "answer_precision": 0.0,
                "answer_recall": 0.0,
                "sp_em": 0.0,
                "sp_f1": 0.0,
                "sp_precision": 0.0,
                "sp_recall": 0.0,
                "joint_em": 0.0,
                "joint_f1": 0.0,
                "joint_precision": 0.0,
                "joint_recall": 0.0,
                "combined_score": 0.0
            }
        # Extract answer from prediction and ground truth
        pred_outputs = self._extract_value(prediction, "outputs", {})
        gold_outputs = self._extract_value(ground_truth, "outputs", {})
        
        # Log the extracted outputs for debugging
        logger.info(f"Extracted pred_outputs: {pred_outputs}")
        logger.info(f"Extracted gold_outputs: {gold_outputs}")
        
        # Handle None values
        pred_outputs = {} if pred_outputs is None else pred_outputs
        gold_outputs = {} if gold_outputs is None else gold_outputs
        
        pred_answer = pred_outputs.get(self.output_field, "")
        gold_answer = gold_outputs.get(self.output_field, "")
        
        # Log the extracted answers
        logger.info(f"Extracted pred_answer: '{pred_answer}'")
        logger.info(f"Extracted gold_answer: '{gold_answer}'")
        
        # Extract gold supporting facts if available
        gold_supporting_facts = self._extract_value(ground_truth, "supporting_facts", [])
        if not gold_supporting_facts:
            # Try to get from gold_titles if available
            if isinstance(ground_truth, dict) and "gold_titles" in ground_truth:
                gold_titles = self._extract_value(ground_truth, "gold_titles", [])
                gold_supporting_facts = [[title, 0] for title in gold_titles]
            # Default to empty list if not available
            else:
                gold_supporting_facts = []
        
        # Extract retrieved passages if available
        pred_inputs = self._extract_value(prediction, "inputs", {})
        
        # Ensure pred_inputs is a dictionary
        if pred_inputs is None or callable(pred_inputs):
            logger.warning(f"pred_inputs is not a dictionary: {type(pred_inputs)}")
            pred_inputs = {}
            
        # Get retrieved passages
        retrieved_passages = pred_inputs.get("context", [])
        retrieved_passages = [] if retrieved_passages is None else retrieved_passages
        
        # Log retrieved passages
        logger.info(f"Retrieved passages count: {len(retrieved_passages)}")
        if retrieved_passages:
            logger.info(f"First passage sample: {retrieved_passages[0][:100]}...")
        else:
            logger.info("No retrieved passages found")
        
        # Extract predicted supporting facts from retrieved passages
        pred_supporting_facts = self._extract_supporting_facts(retrieved_passages)
        
        # Log supporting facts
        logger.info(f"Gold supporting facts: {gold_supporting_facts}")
        logger.info(f"Predicted supporting facts: {pred_supporting_facts}")
        
        # Calculate answer exact match
        normalized_pred = self._normalize_answer(pred_answer)
        normalized_gold = self._normalize_answer(gold_answer)
        answer_exact_match = normalized_pred == normalized_gold
        
        # Log normalized answers
        logger.info(f"Normalized pred_answer: '{normalized_pred}'")
        logger.info(f"Normalized gold_answer: '{normalized_gold}'")
        logger.info(f"Answer exact match: {answer_exact_match}")
        
        # Calculate answer F1 score
        answer_f1, answer_precision, answer_recall = self._calculate_f1(pred_answer, gold_answer)
        
        # Log answer F1 scores
        logger.info(f"Answer F1: {answer_f1}, Precision: {answer_precision}, Recall: {answer_recall}")
        
        # Calculate supporting facts scores
        sp_f1, sp_precision, sp_recall, sp_em = self._calculate_sp_scores(
            pred_supporting_facts, gold_supporting_facts
        )
        
        # Log supporting facts scores
        logger.info(f"Supporting facts F1: {sp_f1}, Precision: {sp_precision}, Recall: {sp_recall}, EM: {sp_em}")
        
        # Calculate joint scores (if both answer and supporting facts are available)
        joint_precision = answer_precision * sp_precision
        joint_recall = answer_recall * sp_recall
        
        # Avoid division by zero
        if (joint_precision + joint_recall) > 0:
            joint_f1 = 2 * joint_precision * joint_recall / (joint_precision + joint_recall)
        else:
            joint_f1 = 0.0
            
        joint_em = 1.0 if answer_exact_match and sp_em else 0.0
        
        # Calculate combined score (weighted average of answer and supporting facts F1)
        combined_score = (
            (1 - self.passage_weight) * answer_f1 + 
            self.passage_weight * sp_f1
        )
        
        return {
            "answer_em": 1.0 if answer_exact_match else 0.0,
            "answer_f1": answer_f1,
            "answer_precision": answer_precision,
            "answer_recall": answer_recall,
            "sp_em": sp_em,
            "sp_f1": sp_f1,
            "sp_precision": sp_precision,
            "sp_recall": sp_recall,
            "joint_em": joint_em,
            "joint_f1": joint_f1,
            "joint_precision": joint_precision,
            "joint_recall": joint_recall,
            "combined_score": combined_score
        }
    
    def _extract_value(self, data: Any, field: str, default: Any = None) -> Any:
        """
        Extract a value from data, which can be a dict, string, or object.
        
        Args:
            data: The data to extract from
            field: The field to extract
            default: Default value if field is not found
            
        Returns:
            Extracted value or default
        """
        if data is None:
            logger.debug(f"Data is None when extracting field '{field}'")
            return default
        
        # Log the type of data for debugging
        logger.debug(f"Extracting field '{field}' from data of type {type(data)}")
        
        # Special handling for DSPy Example and Prediction objects
        if hasattr(data, '__class__') and data.__class__.__name__ in ['Example', 'Prediction']:
            # For DSPy Prediction objects
            if data.__class__.__name__ == 'Prediction':
                # If looking for outputs and this is a Prediction, extract the answer field
                if field == 'outputs':
                    # Check if the output field exists directly
                    if hasattr(data, self.output_field):
                        return {self.output_field: getattr(data, self.output_field)}
                    # Try to get from the object's dictionary
                    elif hasattr(data, '__dict__'):
                        if self.output_field in data.__dict__:
                            return {self.output_field: data.__dict__[self.output_field]}
                    # Try to access as a key
                    try:
                        if self.output_field in data:
                            return {self.output_field: data[self.output_field]}
                    except (TypeError, KeyError):
                        pass
                    # Default empty dict if no answer found
                    return {}
            
            # For DSPy Example objects
            if field == 'inputs':
                # Handle DSPy Example inputs
                if hasattr(data, '_input_keys') and hasattr(data, 'get'):
                    # Create a dictionary from the input keys
                    result = {}
                    for key in data._input_keys:
                        try:
                            value = data.get(key)
                            if value is not None:
                                result[key] = value
                        except Exception as e:
                            logger.debug(f"Error getting input key {key}: {e}")
                    logger.debug(f"Extracted inputs from DSPy object: {result}")
                    return result
                # Try accessing inputs as a property
                elif hasattr(data, 'inputs') and not callable(data.inputs):
                    return data.inputs
            elif field == 'outputs':
                # Handle DSPy Example outputs
                if hasattr(data, '_output_keys') and hasattr(data, 'get'):
                    # Create a dictionary from the output keys
                    result = {}
                    for key in data._output_keys:
                        try:
                            value = data.get(key)
                            if value is not None:
                                result[key] = value
                        except Exception as e:
                            logger.debug(f"Error getting output key {key}: {e}")
                    logger.debug(f"Extracted outputs from DSPy object: {result}")
                    return result
                # Try accessing outputs as a property
                elif hasattr(data, 'outputs') and not callable(data.outputs):
                    return data.outputs
            # For other fields, try direct attribute access
            elif hasattr(data, field):
                attr = getattr(data, field)
                if not callable(attr):
                    return attr
                else:
                    logger.debug(f"Attribute '{field}' is callable in DSPy object")
        
        # Handle dictionary-like objects
        if isinstance(data, dict):
            return data.get(field, default)
        
        # Handle callable objects - this is likely causing the error
        if callable(data):
            logger.warning(f"Received callable object when extracting field '{field}'. Cannot extract value.")
            return default
            
        # Handle objects with attributes
        if hasattr(data, field):
            attr = getattr(data, field, default)
            # If the attribute is callable (like a method), don't call it
            if callable(attr):
                logger.warning(f"Attribute '{field}' is callable. Not executing it.")
                return default
            return attr
            
        # If data is a string, try to parse it as JSON
        if isinstance(data, str) and self.strict_json:
            try:
                import json
                json_data = json.loads(data)
                if isinstance(json_data, dict):
                    return json_data.get(field, default)
            except Exception as e:
                logger.debug(f"Failed to parse string as JSON: {str(e)}")
                pass
        
        # If we got here, we couldn't extract the value
        logger.debug(f"Could not extract field '{field}' from data of type {type(data)}")
        return default
    
    def _normalize_answer(self, text: str) -> str:
        """
        Normalize answer text for comparison following the official HotpotQA evaluation.
        
        Args:
            text: The text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        def remove_articles(text):
            return re.sub(r'\b(a|an|the)\b', ' ', text)

        def white_space_fix(text):
            return ' '.join(text.split())

        def remove_punc(text):
            exclude = set(string.punctuation)
            return ''.join(ch for ch in text if ch not in exclude)

        def lower(text):
            return text.lower()

        return white_space_fix(remove_articles(remove_punc(lower(text))))
    
    def _calculate_f1(self, pred: str, gold: str) -> tuple:
        """
        Calculate F1 score between prediction and gold answer following the official HotpotQA evaluation.
        
        Args:
            pred: Predicted answer
            gold: Gold answer
            
        Returns:
            Tuple of (F1 score, precision, recall)
        """
        normalized_pred = self._normalize_answer(pred)
        normalized_gold = self._normalize_answer(gold)
        
        ZERO_METRIC = (0.0, 0.0, 0.0)
        
        # Special handling for yes/no answers
        if normalized_pred in ['yes', 'no', 'noanswer'] and normalized_pred != normalized_gold:
            return ZERO_METRIC
        if normalized_gold in ['yes', 'no', 'noanswer'] and normalized_pred != normalized_gold:
            return ZERO_METRIC
        
        # Tokenize
        pred_tokens = normalized_pred.split()
        gold_tokens = normalized_gold.split()
        
        # Use Counter to handle token frequency
        common = Counter(pred_tokens) & Counter(gold_tokens)
        num_same = sum(common.values())
        
        if num_same == 0:
            return ZERO_METRIC
            
        precision = 1.0 * num_same / len(pred_tokens) if pred_tokens else 0.0
        recall = 1.0 * num_same / len(gold_tokens) if gold_tokens else 0.0
        
        if precision + recall == 0:
            return ZERO_METRIC
            
        f1 = 2 * precision * recall / (precision + recall)
        return f1, precision, recall
    
    def _calculate_sp_scores(self, predicted_sp: List[List[str]], gold_sp: List[List[str]]) -> tuple:
        """
        Calculate supporting facts scores following the official HotpotQA evaluation.
        
        Args:
            predicted_sp: List of predicted supporting facts [title, sent_id]
            gold_sp: List of gold supporting facts [title, sent_id]
            
        Returns:
            Tuple of (F1 score, precision, recall, exact match)
        """
        if not gold_sp:
            return 0.0, 0.0, 0.0, 0.0
        
        if not predicted_sp:
            return 0.0, 0.0, 0.0, 0.0
        
        # Convert to sets of tuples for comparison
        pred_sp_set = set(map(tuple, predicted_sp))
        gold_sp_set = set(map(tuple, gold_sp))
        
        # Calculate true positives, false positives, false negatives
        tp, fp, fn = 0, 0, 0
        
        for sp in pred_sp_set:
            if sp in gold_sp_set:
                tp += 1
            else:
                fp += 1
                
        for sp in gold_sp_set:
            if sp not in pred_sp_set:
                fn += 1
        
        # Calculate precision, recall, F1
        precision = 1.0 * tp / (tp + fp) if tp + fp > 0 else 0.0
        recall = 1.0 * tp / (tp + fn) if tp + fn > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
        
        # Exact match is 1.0 if no false positives and no false negatives
        em = 1.0 if fp + fn == 0 else 0.0
        
        return f1, precision, recall, em
        
    def _extract_supporting_facts(self, retrieved_passages: Union[List[str], str]) -> List[List[str]]:
        """
        Extract supporting facts from retrieved passages.
        
        Args:
            retrieved_passages: List of retrieved passages or string of concatenated passages
            
        Returns:
            List of supporting facts in the format [[title, sent_id], ...]
        """
        if not retrieved_passages:
            return []
        
        # Handle string input (convert to list)
        if isinstance(retrieved_passages, str):
            retrieved_passages = retrieved_passages.split("\n\n")
        
        # Extract titles and assume all sentences are supporting facts
        # This is a simplification since we don't have sentence IDs
        supporting_facts = []
        for passage in retrieved_passages:
            if isinstance(passage, str) and " | " in passage:
                title = passage.split(" | ")[0]
                # Add as supporting fact with sent_id 0 (simplification)
                supporting_facts.append([title, 0])
        
        return supporting_facts
