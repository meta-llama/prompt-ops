import dspy
import time
import logging

# Get the dedicated optimizer trace logger
optimizer_trace_logger = logging.getLogger("llama_prompt_ops.optimizer_trace")

class LoggingLM(dspy.LM):
    """
    A dspy.LM wrapper that logs interactions (prompts, responses, duration)
    to the optimizer_trace_logger.
    """
    def __init__(self, wrapped_lm: dspy.LM, **kwargs):
        super().__init__(model=getattr(wrapped_lm, 'model', 'unknown')) # Pass model if available
        self.wrapped_lm = wrapped_lm
        self.provider = getattr(wrapped_lm, 'provider', 'unknown')
        # Store any other relevant attributes from the wrapped_lm if necessary
        # For example, if wrapped_lm has specific config, you might want to copy it or parts of it.
        # Ensure that the base dspy.LM is initialized correctly.
        # We also pass kwargs to the super init in case dspy.LM evolves.
        # However, dspy.LM itself doesn't take arbitrary kwargs in its __init__ as of dspy-ai 2.4.8
        # It primarily expects 'model'. We will rely on __getattr__ for most passthroughs.

        # Propagate specific known attributes that dspy.LM might expect or use internally
        if hasattr(wrapped_lm, 'kwargs'):
            self.kwargs = wrapped_lm.kwargs
        else:
            self.kwargs = {}
        
        # A flag to identify this wrapper if needed elsewhere
        self.kwargs['logging_lm_wrapper'] = True


    def basic_request(self, prompt, **kwargs):
        """
        Intercepts the basic request to the LM, logs details, and calls the wrapped LM.
        """
        optimizer_trace_logger.debug(f"LoggingLM: Sending prompt to {self.wrapped_lm.__class__.__name__} (model: {getattr(self.wrapped_lm, 'model', 'N/A')})")
        # Truncate prompt for logging if too long, or log full if a more verbose level is set
        # For now, logging a summary or first N chars.
        prompt_summary = str(prompt)[:200] + "..." if len(str(prompt)) > 200 else str(prompt)
        optimizer_trace_logger.debug(f"Prompt (summary): {prompt_summary}")

        start_time = time.time()
        
        try:
            # Call the wrapped LM's basic_request method
            response = self.wrapped_lm.basic_request(prompt, **kwargs)
            duration = (time.time() - start_time) * 1000  # Duration in milliseconds

            optimizer_trace_logger.debug(f"LoggingLM: Received response from {self.wrapped_lm.__class__.__name__}")
            # Log raw response (or summary)
            # response_summary = str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
            # Actual response structure might be complex (e.g. ChatCompletion), so log carefully.
            # For now, let's assume response is a string or has a string representation.
            # In DSPy, the 'response' from basic_request is typically the raw model output (e.g. a dict or list of choices)
            
            # Extracting text from common response structures
            raw_response_text = ""
            if isinstance(response, dict) and "choices" in response and response["choices"]:
                if "text" in response["choices"][0]:
                    raw_response_text = response["choices"][0]["text"]
                elif "message" in response["choices"][0] and "content" in response["choices"][0]["message"]:
                    raw_response_text = response["choices"][0]["message"]["content"]
            elif isinstance(response, list) and response and isinstance(response[0], str): # For completion-style LMs
                 raw_response_text = response[0]
            elif isinstance(response, str):
                 raw_response_text = response
            else:
                raw_response_text = str(response) # Fallback

            response_summary = raw_response_text[:200] + "..." if len(raw_response_text) > 200 else raw_response_text
            optimizer_trace_logger.debug(f"Raw response (summary): {response_summary}")
            optimizer_trace_logger.debug(f"LoggingLM: Call duration: {duration:.2f} ms")

        except Exception as e:
            duration = (time.time() - start_time) * 1000  # Duration in milliseconds
            optimizer_trace_logger.error(f"LoggingLM: Error during request to {self.wrapped_lm.__class__.__name__}: {e}", exc_info=True)
            optimizer_trace_logger.debug(f"LoggingLM: Call duration (on error): {duration:.2f} ms")
            raise # Re-raise the exception

        return response

    def __call__(self, *args, **kwargs):
        """
        The main entry point for dspy.LM.
        This wrapper aims to be transparent, so it should primarily delegate all arguments
        to the wrapped LM's __call__ method. Logging is handled in basic_request,
        which is typically called by the wrapped LM's __call__ or request methods.
        """
        # Pass all positional and keyword arguments to the wrapped LM's __call__
        return self.wrapped_lm(*args, **kwargs)

    def __getattr__(self, name):
        """
        Forward any unhandled attribute access to the wrapped_lm instance.
        This helps in making the wrapper transparent for attributes/methods
        it doesn't explicitly override.
        """
        return getattr(self.wrapped_lm, name)

    def __repr__(self):
        return f"LoggingLM(wrapped_lm={self.wrapped_lm!r})"

    def __str__(self):
        return f"LoggingLM wrapping {str(self.wrapped_lm)}"

if __name__ == '__main__':
    # Example Usage (requires a dspy.LM to be configured, e.g. dspy.OpenAI)
    # This is for illustrative purposes and might need a proper dspy setup to run.
    
    # Configure a dummy LM for testing if no real LM is set up
    class DummyLM(dspy.LM):
        def __init__(self, model_name="dummy-model"):
            super().__init__(model_name)
            self.provider = "dummy"

        def basic_request(self, prompt, **kwargs):
            # Simulate a response
            return {"choices": [{"message": {"content": f"Response to: {prompt}"}}]}

        def __call__(self, prompt, **kwargs):
            # Simulate a __call__ that might generate multiple responses
            # For simplicity, just one for this dummy
            response_content = f"Response to: {prompt}"
            # DSPy expects a list of strings or list of dicts with 'message'
            # For chat models, it's usually a list of dicts like:
            # [{'choices': [{'message': {'content': 'response text'}}]}
            # For completion, it's a list of strings.
            # Let's simulate a chat-like raw response structure from basic_request
            # and then __call__ processes it into a list of strings.
            
            # This dummy __call__ will directly return a list of strings as dspy.Predict expects
            return [response_content]


    # Setup basic logging to see output for the example
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a dummy LM instance
    actual_lm = DummyLM()
    
    # Wrap it with LoggingLM
    logged_lm = LoggingLM(wrapped_lm=actual_lm)
    
    # Test __call__
    optimizer_trace_logger.info("Testing LoggingLM __call__...")
    try:
        # dspy.Predict and other modules use the __call__ method of the LM
        responses = logged_lm("This is a test prompt for __call__.")
        optimizer_trace_logger.info(f"Response from __call__: {responses}")
    except Exception as e:
        optimizer_trace_logger.error(f"Error during __call__ test: {e}")

    # Test basic_request directly (less common for external users, but good for wrapper testing)
    # optimizer_trace_logger.info("Testing LoggingLM basic_request...")
    # try:
    #     raw_response = logged_lm.basic_request("This is a test prompt for basic_request.")
    #     optimizer_trace_logger.info(f"Raw response from basic_request: {raw_response}")
    # except Exception as e:
    #     optimizer_trace_logger.error(f"Error during basic_request test: {e}")

    # Test attribute forwarding
    optimizer_trace_logger.info(f"Accessing wrapped_lm.provider via LoggingLM: {logged_lm.provider}")
    optimizer_trace_logger.info(f"Accessing wrapped_lm.model via LoggingLM: {logged_lm.model}")
    
    # Verify the logging_lm_wrapper flag
    optimizer_trace_logger.info(f"logging_lm_wrapper flag: {logged_lm.kwargs.get('logging_lm_wrapper')}")

    # Example of how dspy.Predict might use it
    # predictor = dspy.Predict("question -> answer")(lm=logged_lm)
    # result = predictor(question="What is DSPy?")
    # print(f"Predictor result: {result.answer}")
    
    optimizer_trace_logger.info("LoggingLM example usage finished.")
