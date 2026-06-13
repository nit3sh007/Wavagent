from langchain.tools import tool
import wikipedia
import os

@tool
def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for information about a country, event, or topic.
    Use this to get factual background information and current events.
    Input should be a specific topic like 'Japan current events 2026'
    """
    try:
        # Search for relevant pages
        search_results = wikipedia.search(query, results=3)
        
        if not search_results:
            return "No Wikipedia results found for this query."
        
        # Get the most relevant page
        try:
            page = wikipedia.page(search_results[0], auto_suggest=False)
            
            # Return first 2000 chars to avoid token overflow
            content = page.content[:2000]
            
            return f"""
Wikipedia: {page.title}
URL: {page.url}

Content:
{content}

...
"""
        except wikipedia.exceptions.DisambiguationError as e:
            # If disambiguation, try the first option
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                content = page.content[:2000]
                return f"""
Wikipedia: {page.title}
URL: {page.url}

Content:
{content}
"""
            except:
                return f"Multiple results found: {', '.join(e.options[:5])}. Please be more specific."
                
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{search_results[0]}'. Try different terms."
            
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}. Try alternative search terms."


@tool  
def get_country_overview(country: str) -> str:
    """
    Get a general overview of a country from Wikipedia.
    Use this at the start of research to understand the country context.
    Input should be just the country name like 'Japan' or 'Brazil'
    """
    try:
        page = wikipedia.page(country, auto_suggest=True)
        
        # Get introduction only (before first section)
        intro = page.content.split('\n\n')[0]
        
        return f"""
Country: {page.title}
URL: {page.url}

Overview:
{intro[:1500]}
"""
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            page = wikipedia.page(e.options[0])
            intro = page.content.split('\n\n')[0]
            return f"""
Country: {page.title}
URL: {page.url}

Overview:
{intro[:1500]}
"""
        except:
            return f"Could not find overview for {country}"
            
    except Exception as e:
        return f"Failed to get country overview: {str(e)}"