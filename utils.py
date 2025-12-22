"""
Utility functions for the handson.ai application.
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

load_dotenv()


def get_openrouter_client():
    """
    Returns a configured OpenAI client for OpenRouter API.
    
    Returns:
        OpenAI: Configured client with OpenRouter base URL and API key
        
    Raises:
        ValueError: If OPENROUTER_API_KEY is not found in environment variables
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def summarize_headlines(headlines):
    """
    Summarize a list of news headlines using NVIDIA Nemotron via OpenRouter.
    
    Args:
        headlines (list): List of dictionaries with 'title' and 'published' keys
        
    Returns:
        str: AI-generated summary of the headlines
        
    Raises:
        ValueError: If OPENROUTER_API_KEY is not found or API call fails
    """
    logging.info(f"summarize_headlines: Starting with {len(headlines)} headlines")
    
    if not headlines:
        logging.info("summarize_headlines: No headlines provided")
        return "No headlines to summarize."
    
    # Format headlines into a readable text
    logging.info("summarize_headlines: Formatting headlines into text")
    headlines_text = "\n".join([
        f"- {item['title']} (Published: {item['published']})"
        for item in headlines
    ])
    
    # Create prompt for summarization
    prompt = f"""Analyze and summarize the following news headlines. Provide a concise summary that:
1. Identifies the main themes and topics
2. Highlights any significant trends or patterns
3. Notes any breaking or urgent news
4. Provides context and insights

Headlines:
{headlines_text}

Provide a clear, well-structured summary."""
    
    logging.info(f"summarize_headlines: Prompt created (length: {len(prompt)} chars)")
    
    try:
        logging.info("summarize_headlines: Getting OpenRouter client")
        client = get_openrouter_client()
        
        logging.info("summarize_headlines: Calling OpenRouter API with nvidia/nemotron-3-nano-30b-a3b:free")
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            extra_body={"reasoning": {"enabled": True}}
        )
        
        logging.info("summarize_headlines: API call successful, extracting response")
        summary = response.choices[0].message.content
        logging.info(f"summarize_headlines: Summary generated (length: {len(summary)} chars)")
        
        return summary
        
    except Exception as e:
        logging.error(f"summarize_headlines: Exception occurred: {str(e)}", exc_info=True)
        raise ValueError(f"Error generating summary: {str(e)}")
