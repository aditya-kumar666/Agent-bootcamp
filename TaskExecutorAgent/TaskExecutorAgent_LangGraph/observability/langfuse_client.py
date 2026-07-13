"""Langfuse observability client for LLM tracing - Langfuse v4.14+ compatible."""

import os
import secrets
from contextlib import contextmanager
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from langfuse import Langfuse
    from langfuse.types import TraceContext
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class LangfuseObserver:
    """Wrapper for Langfuse tracing with graceful fallback.
    
    Compatible with Langfuse v4.14+ SDK.
    Uses TraceContext and update() pattern for observations.
    """
    
    def __init__(self):
        """Initialize Langfuse client if credentials available."""
        self.enabled = False
        self.client = None
        self.current_trace_context = None
        
        if LANGFUSE_AVAILABLE and self._has_credentials():
            try:
                secret_key = os.getenv("LANGFUSE_SECRET_KEY")
                public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
                host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
                
                self.client = Langfuse(
                    secret_key=secret_key,
                    public_key=public_key,
                    host=host,
                    flush_interval=10  # Auto-flush every 10s
                )
                self.enabled = True
                print(f"[OK] Langfuse observability enabled ({host})", flush=True)
            except Exception as e:
                print(f"[WARN] Langfuse initialization failed: {e}", flush=True)
    
    def _has_credentials(self) -> bool:
        """Check if Langfuse credentials are available."""
        return bool(os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY"))
    
    @contextmanager
    def trace(self, name: str, input_data: Dict[str, Any] = None, 
              metadata: Dict[str, Any] = None):
        """Context manager for tracing an operation.
        
        Uses Langfuse SDK v4.14+ observation API with TraceContext.
        
        Args:
            name: Name of the trace
            input_data: Input data for the operation
            metadata: Additional metadata
            
        Yields:
            Observation object or None if disabled
        """
        if not self.enabled or not self.client:
            yield None
            return
        
        observation = None
        try:
            # Create trace context with proper hex trace ID (32 chars)
            trace_id = secrets.token_hex(16)
            trace_context = TraceContext(trace_id=trace_id)
            self.current_trace_context = trace_context
            
            # Start observation (root span of the trace)
            observation = self.client.start_observation(
                name=name,
                trace_context=trace_context,
                as_type='span',
                input=input_data or {},
                metadata=metadata or {}
            )
            yield observation
            
            # End observation
            if observation:
                observation.end()
        except Exception as e:
            print(f"[WARN] Trace '{name}' failed: {e}", flush=True)
            yield None
        finally:
            self.current_trace_context = None
    
    def generation(self, observation, name: str, model: str, 
                   input_data: Dict[str, Any], 
                   output: str = None, tokens: Dict[str, int] = None):
        """Log an LLM generation.
        
        Args:
            observation: Parent observation object from trace()
            name: Name of generation
            model: Model used
            input_data: Input to model
            output: Model output
            tokens: Token usage {prompt_tokens, completion_tokens}
        """
        if not observation or not self.enabled:
            return None
        
        try:
            # Create nested generation span
            gen = self.client.start_observation(
                name=name,
                trace_context=observation.trace_context if hasattr(observation, 'trace_context') else self.current_trace_context,
                as_type='generation',
                model=model,
                input=input_data,
            )
            
            # Update with output and token usage
            if gen:
                gen.update(
                    output=output,
                    usage_details={
                        "input": tokens.get("prompt_tokens", 0) if tokens else 0,
                        "output": tokens.get("completion_tokens", 0) if tokens else 0,
                    }
                )
                gen.end()
            return gen
        except Exception as e:
            print(f"[WARN] Generation logging failed: {e}", flush=True)
            return None
    
    def span(self, observation, name: str, input_data: Dict[str, Any] = None,
             output: str = None):
        """Log a span (tool call, etc).
        
        Args:
            observation: Parent observation object from trace()
            name: Name of span
            input_data: Input data
            output: Output data
        """
        if not observation or not self.enabled:
            return None
        
        try:
            # Create nested span for tool call
            span = self.client.start_observation(
                name=name,
                trace_context=observation.trace_context if hasattr(observation, 'trace_context') else self.current_trace_context,
                as_type='span',
                input=input_data or {},
            )
            
            # Update with output
            if span:
                if output:
                    span.update(output=output)
                span.end()
            return span
        except Exception as e:
            print(f"[WARN] Span logging failed: {e}", flush=True)
            return None
    
    def flush(self):
        """Flush pending traces to Langfuse."""
        if self.enabled and self.client:
            try:
                self.client.flush()
                print("[OK] Langfuse traces flushed", flush=True)
            except Exception as e:
                print(f"[WARN] Flush failed: {e}", flush=True)


# Global instance
_langfuse_observer: Optional[LangfuseObserver] = None


def get_langfuse_client() -> LangfuseObserver:
    """Get or create the global Langfuse observer.
    
    Returns:
        LangfuseObserver instance
    """
    global _langfuse_observer
    if _langfuse_observer is None:
        _langfuse_observer = LangfuseObserver()
    return _langfuse_observer


def reset_langfuse_client():
    """Reset the global Langfuse observer (for testing)."""
    global _langfuse_observer
    if _langfuse_observer and _langfuse_observer.enabled:
        _langfuse_observer.flush()
    _langfuse_observer = None
