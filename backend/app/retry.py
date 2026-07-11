# backend/app/retry.py
import asyncio
import random
import logging

logger = logging.getLogger(__name__)

async def run_with_retry(fn, *args, max_retries: int = 2, base_delay: float = 1.0, **kwargs):
    """
    Executes an async function with exponential backoff and jitter.
    
    :param fn: The async function to execute.
    :param max_retries: Total number of retry attempts allowed after the initial failure.
    :param base_delay: Initial wait duration in seconds.
    :return: The return value of the wrapped async function.
    """
    attempt = 0
    while True:
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Function {fn.__name__} failed permanently after {attempt} attempts. Error: {e}")
                raise
            
            # Calculate backoff: base_delay * 2^(attempt - 1)
            backoff = base_delay * (2 ** (attempt - 1))
            # Add uniform random jitter (0 to 300 milliseconds) to prevent synchronized retries
            jitter = random.uniform(0, 0.3)
            delay = backoff + jitter
            
            logger.warning(
                f"Function {fn.__name__} failed (Attempt {attempt}/{max_retries + 1}). "
                f"Retrying in {delay:.2f} seconds. Error: {e}"
            )
            
            await asyncio.sleep(delay)