"""
HotpotQA metric implementation.

This module provides metrics for evaluating HotpotQA predictions,
including answer correctness and passage retrieval accuracy.
"""

import re
import string
import logging
from typing import Dict, List, Any, Optional, Union

from prompt_ops.core.metrics import MetricBase

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
    
    def __call__(self, ground_truth: Any, prediction: Any, **kwargs) -> float:
        """
        Call the metric to get a single score.
        
        Args:
            ground_truth: The ground truth example
            prediction: The model's prediction
            
        Returns:
            Combined score as a float
        """
        results = self.evaluate(ground_truth, prediction, **kwargs)
        return results.get("combined_score", 0.0)
        
    def evaluate(self, ground_truth: Any, prediction: Any, **kwargs) -> Dict[str, Any]:
        """
        Evaluate a prediction against the ground truth.
        
        Args:
            ground_truth: The ground truth example
            prediction: The model's prediction
            
        Returns:
            Dictionary with evaluation results
        """
        # Extract answer from prediction and ground truth
        pred_answer = self._extract_value(prediction, "outputs", {}).get(self.output_field, "")
        gold_answer = self._extract_value(ground_truth, "outputs", {}).get(self.output_field, "")
        
        # Extract gold titles if available
        gold_titles = self._extract_value(ground_truth, "gold_titles", [])
        
        # Extract retrieved passages if available
        retrieved_passages = self._extract_value(prediction, "inputs", {}).get("context", [])
        
        # Normalize answers for comparison
        norm_pred_answer = self._normalize_answer(pred_answer)
        norm_gold_answer = self._normalize_answer(gold_answer)
        
        # Calculate answer score (exact match)
        answer_exact_match = norm_pred_answer == norm_gold_answer
        
        # Calculate answer F1 score
        answer_f1 = self._calculate_f1(norm_pred_answer, norm_gold_answer)
        
        # Calculate passage recall if gold titles are available
        passage_recall = 0.0
        if gold_titles and retrieved_passages:
            passage_recall = self._calculate_passage_recall(gold_titles, retrieved_passages)
        
        # Calculate combined score
        combined_score = (
            (1 - self.passage_weight) * answer_f1 + 
            self.passage_weight * passage_recall
        )
        
        return {
            "answer_exact_match": 1.0 if answer_exact_match else 0.0,
            "answer_f1": answer_f1,
            "passage_recall": passage_recall,
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
            return default
            
        if isinstance(data, dict):
            return data.get(field, default)
            
        if hasattr(data, field):
            return getattr(data, field, default)
            
        # If data is a string, try to parse it as JSON
        if isinstance(data, str) and self.strict_json:
            try:
                import json
                json_data = json.loads(data)
                if isinstance(json_data, dict):
                    return json_data.get(field, default)
            except Exception:
                pass
                
        return default
    
    def _normalize_answer(self, text: str) -> str:
        """
        Normalize answer text for comparison.
        
        Args:
            text: The text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _calculate_f1(self, pred: str, gold: str) -> float:
        """
        Calculate F1 score between prediction and gold answer.
        
        Args:
            pred: Predicted answer
            gold: Gold answer
            
        Returns:
            F1 score
        """
        if not pred or not gold:
            return 0.0
        
        # Tokenize
        pred_tokens = pred.split()
        gold_tokens = gold.split()
        
        # Calculate precision, recall, F1
        common = set(pred_tokens) & set(gold_tokens)
        
        if not common:
            return 0.0
            
        precision = len(common) / len(pred_tokens) if pred_tokens else 0.0
        recall = len(common) / len(gold_tokens) if gold_tokens else 0.0
        
        if precision + recall == 0:
            return 0.0
            
        f1 = 2 * precision * recall / (precision + recall)
        return f1
    
    def _calculate_passage_recall(self, gold_titles: List[str], retrieved_passages: Union[List[str], str]) -> float:
        """
        Calculate passage recall - what fraction of gold titles were retrieved.
        
        Args:
            gold_titles: List of gold passage titles
            retrieved_passages: List of retrieved passages or string of concatenated passages
            
        Returns:
            Passage recall score
        """
        if not gold_titles:
            return 0.0
        
        # Handle string input (convert to list)
        if isinstance(retrieved_passages, str):
            retrieved_passages = retrieved_passages.split("\n\n")
        
        if not retrieved_passages:
            return 0.0
        
        # Extract titles from retrieved passages
        retrieved_titles = []
        for passage in retrieved_passages:
            if isinstance(passage, str) and " | " in passage:
                title = passage.split(" | ")[0].lower()
                retrieved_titles.append(title)
        
        # Normalize gold titles
        normalized_gold_titles = [title.lower() for title in gold_titles]
        
        # Count matches
        matches = 0
        for gold_title in normalized_gold_titles:
            if any(gold_title in retrieved_title for retrieved_title in retrieved_titles):
                matches += 1
        
        # Calculate recall
        recall = matches / len(normalized_gold_titles) if normalized_gold_titles else 0.0
        return recall
