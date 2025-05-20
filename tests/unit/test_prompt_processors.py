import unittest
from unittest.mock import MagicMock, patch

from llama_prompt_ops.core.prompt_processors import (
    PromptProcessor,
    LlamaFormatting,
    InstructionPreference,
    create_llama_processing_chain
)


class TestPromptProcessor(unittest.TestCase):
    def test_processor_chain(self):
        # Test basic processor chain
        processor1 = PromptProcessor()
        processor2 = PromptProcessor()
        processor1.set_next(processor2)
        
        # Simple pass-through test
        data = {"text": "Test prompt"}
        result = processor1.process(data)
        
        self.assertEqual(result["text"], "Test prompt")
    
    @patch('llama_prompt_ops.core.prompt_processors.format_prompt_for_llama')
    def test_llama_formatting(self, mock_format):
        # Configure mock
        mock_format.return_value = "[FORMATTED] Test prompt"
        
        # Test Llama formatting processor
        processor = LlamaFormatting()
        data = {
            "text": "Test prompt",
            "apply_formatting": True
        }
        
        result = processor.process(data)
        
        # Verify format_prompt_for_llama was called
        mock_format.assert_called_once()
        self.assertEqual(result["text"], "[FORMATTED] Test prompt")
    
    @patch('llama_prompt_ops.core.prompt_processors.select_instruction_preference')
    @patch('llama_prompt_ops.core.prompt_processors.get_task_type_from_prompt')
    def test_instruction_preference(self, mock_get_task, mock_select):
        # Configure mocks
        mock_get_task.return_value = "classification"
        mock_select.return_value = ["Use clear classification instructions"]
        
        # Test instruction preference processor
        processor = InstructionPreference(verbose=True)
        data = {
            "text": "Classify the following text",
            "input_fields": ["text"],
            "output_fields": ["category"]
        }
        
        result = processor.process(data)
        
        # Verify task type detection and preference selection
        mock_get_task.assert_called_once()
        mock_select.assert_called_once()
        self.assertIn("instruction_tips", result)
        self.assertIn("Use clear classification instructions", result["instruction_tips"])


class TestLlamaProcessingChain(unittest.TestCase):
    @patch('llama_prompt_ops.core.prompt_processors.format_prompt_for_llama')
    @patch('llama_prompt_ops.core.prompt_processors.select_instruction_preference')
    @patch('llama_prompt_ops.core.prompt_processors.get_task_type_from_prompt')
    def test_processing_chain(self, mock_get_task, mock_select, mock_format):
        # Configure mocks
        mock_get_task.return_value = "summarization"
        mock_select.return_value = ["Use concise language"]
        mock_format.return_value = "[FORMATTED] Summarize this text"
        
        # Create processing chain
        chain = create_llama_processing_chain(verbose=True)
        
        # Process data through the chain
        data = {
            "text": "Summarize this text",
            "input_fields": ["text"],
            "output_fields": ["summary"]
        }
        
        result = chain.process(data)
        
        # Verify all processors were applied
        mock_get_task.assert_called_once()
        mock_select.assert_called_once()
        mock_format.assert_called_once()
        self.assertEqual(result["text"], "[FORMATTED] Summarize this text")
        self.assertIn("instruction_tips", result)
    
    def test_chain_with_disabled_formatting(self):
        # Create processing chain with formatting disabled
        chain = create_llama_processing_chain(apply_formatting=False)
        
        # Process data
        data = {
            "text": "Original prompt",
            "apply_formatting": False
        }
        
        result = chain.process(data)
        
        # Verify formatting was not applied
        self.assertEqual(result["text"], "Original prompt")
    
    def test_chain_with_examples(self):
        # Create processing chain
        chain = create_llama_processing_chain()
        
        # Process data with examples
        data = {
            "text": "Answer this question",
            "examples": [
                {"question": "What is AI?", "answer": "AI is artificial intelligence"},
                {"question": "What is ML?", "answer": "ML is machine learning"}
            ]
        }
        
        # Mock the format_prompt_for_llama function to verify examples are passed
        with patch('llama_prompt_ops.core.prompt_processors.format_prompt_for_llama') as mock_format:
            mock_format.return_value = "[FORMATTED WITH EXAMPLES]"
            result = chain.process(data)
            
            # Verify examples were passed to the formatting function
            call_args = mock_format.call_args[1]
            self.assertEqual(len(call_args["examples"]), 2)
            self.assertEqual(result["text"], "[FORMATTED WITH EXAMPLES]")
