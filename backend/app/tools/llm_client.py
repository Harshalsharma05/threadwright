# This tool handles LLM operations within our graph execution, using Claude or Groq depending on your active API keys. It queries either Anthropic's Messages API or Groq's Chat Completions API, enforces JSON output, and safely parses the response back into a standard Python dictionary.

import json
import re
import logging
import httpx
from ..config import settings

logger = logging.getLogger(__name__)

def _clean_and_parse_json(text: str) -> dict:
    """
    Cleans up common markdown packaging issues like ```json ... ``` code blocks
    and parses the payload securely.
    """
    cleaned = text.strip()
    # Strip markdown block formatting if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM. Input raw text:\n{text}")
        raise ValueError(f"LLM returned invalid JSON payload: {e}")


async def _call_llm(system_prompt: str, user_prompt: str) -> dict:
    """
    Unified caller supporting fallback authentication structure.
    If Anthropic is available, it routes to Claude.
    Otherwise, if Groq is available, it routes to Llama-3.3 on Groq.
    """
    if settings.anthropic_api_key:
        logger.info("Routing LLM request to Anthropic (Claude-3-Haiku)...")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt + "\nIMPORTANT: Return ONLY a valid, raw JSON object. No explanation."}
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Anthropic API failed: {response.text}")
                response.raise_for_status()
            
            raw_text = response.json()["content"][0]["text"]
            parsed_data = _clean_and_parse_json(raw_text)
            
            parsed_data["llm_provider"] = "Claude (Anthropic)"
            
            return parsed_data

    elif settings.groq_api_key:
        logger.info("Routing LLM request to Groq (Llama-3.3-70b)...")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt + "\nOutput raw JSON only."},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Groq API failed: {response.text}")
                response.raise_for_status()
                
            raw_text = response.json()["choices"][0]["message"]["content"]
            parsed_data = _clean_and_parse_json(raw_text)
            parsed_data["llm_provider"] = "Llama-3.3 (Groq)"
            
            return parsed_data

    else:
        raise ValueError("No viable LLM API Keys found. Please configure ANTHROPIC_API_KEY or GROQ_API_KEY.")

# uses specific job description if provided
async def parse_job_posting(node_input: dict) -> dict:
    """
    Analyzes hiring signals. Uses a specific Job Description if provided, 
    otherwise falls back to general knowledge about the company.
    """
    company_name = node_input.get("company_name")
    raw_jd = node_input.get("raw_jd")

    # 1. System prompt strictly enforcing JSON output structure
    system_prompt = (
        "You are an expert technical interviewer and talent researcher. "
        "Your task is to analyze target roles and output a structured JSON mapping."
    )

    # 2. Conditional prompt logic
    if raw_jd:
        logger.info(f"Analyzing provided raw JD for {company_name}...")
        user_prompt = (
            f"""
            Analyze this pasted job description for the company "{company_name}":
            ---
            {raw_jd}
            ---
            Extract the core competencies required. Output exactly this JSON structure:
            {{
                "target_role": "Extracted role title",
                "required_tech_stack": ["list", "of", "technologies"],
                "must_have_skills": ["skill 1", "skill 2"],
                "implied_dsa_or_system_design_level": "e.g. Medium difficulty DSA, High focus on low-level system design",
                "source_type": "provided_job_description"
            }}
            """
        )
    else:
        logger.info(f"No JD provided. Inferring hiring landscape for {company_name}...")
        user_prompt = (
            f"""
            No specific job description was provided. Research and infer the typical Entry-to-Mid level Software Engineering 
            role profile for "{company_name}". Output exactly this JSON structure:
            {{
                "target_role": "Software Development Engineer (SDE-1 / SDE-2)",
                "required_tech_stack": ["expected", "technologies"],
                "must_have_skills": ["general skill 1", "general skill 2"],
                "implied_dsa_or_system_design_level": "Inferred interview focus expectations",
                "source_type": "inferred_general_profile"
            }}
        """
        )

    # 3. API execution using Groq
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()

        # Parse and return the JSON dictionary
        result_text = data["choices"][0]["message"]["content"]
        return json.loads(result_text)


# old one withoud jd
# async def parse_job_posting(node_input: dict) -> dict:
#     """
#     Analyzes hiring trends and job landscape strategy for a target company.
    
#     Expected input format: {"company": "Company Name"}
#     """
#     company = node_input.get("company")
#     if not company:
#         raise ValueError("Missing required key 'company' in node input.")

#     system_prompt = (
#         "You are an expert technical recruiter and market intelligence analyst. "
#         "Your output must be a single structured JSON object."
#     )
    
#     user_prompt = f"""
#     Analyze the technological and hiring strategy for the company: "{company}".
#     Provide a realistic profile containing hiring trends, key open roles, target tech stacks, 
#     and estimated engineering department scale.
    
#     You must output exactly this JSON structure:
#     {{
#         "hiring_status": "active" | "moderate" | "frozen",
#         "hiring_focus_areas": ["list", "of", "domains"],
#         "key_open_roles": ["role 1", "role 2"],
#         "primary_tech_stack": ["stack items"],
#         "estimated_engineering_scale": "e.g. 50-100 engineers"
#     }}
#     """
    
#     return await _call_llm(system_prompt, user_prompt)


async def synthesize_brief(node_input: dict) -> dict:
    """
    Synthesizes multi-source research inputs (News, GitHub, Reddit, and Job info)
    into a structured corporate intelligence brief.
    """
    # Grab upstream inputs
    news_data = node_input.get("news", {})
    github_data = node_input.get("github", {})
    reddit_data = node_input.get("reddit", {})
    job_data = node_input.get("jobs", {})

    system_prompt = (
        "You are an elite technical interview mentor and industry analyst. "
        "Your task is to synthesize news, public forums, developer activity, and job requirements into an actionable, "
        "personalized study and prep dossier for a candidate interviewing at this company."
        "Your output must be a single structured JSON object matching the requested schema."
    )

    user_prompt = f"""
    Build a comprehensive interview preparation blueprint based on these raw feeds:

    [MARKET NEWS & LANDSCAPE DATA]
    {json.dumps(news_data, indent=2)}

    [DEVELOPER STACK ACTIVITY]
    {json.dumps(github_data, indent=2)}

    [CANDIDATE DISCUSSIONS & SALARY INSIGHTS]
    {json.dumps(reddit_data, indent=2)}

    [JOB & COMPENTENCY CRITERIA]
    {json.dumps(job_data, indent=2)}

    Synthesize this intelligence and output a raw JSON object matching this exact structure:
    {{
        "market_and_competition": {{
            "direct_competitors": ["Competitor A", "Competitor B", "Competitor C"],
            "market_position_and_challenges": "How this company positions itself relative to competitors, including current challenges."
        }},
        "hiring_and_compensation": {{
            "fresher_hiring_trends": "Analysis of their fresher intake frequency, hiring volume, or general hiring health.",
            "estimated_compensation_range": "Expected salary package in LPA (e.g. '12 - 18 LPA base + stock') based on the inputs."
        }},
        "technical_interview_focus": {{
            "data_structures_and_algorithms": ["Specific topics highly prioritized, e.g. Trees, Dynamic Programming, Graphs"],
            "system_design_expectations": "Expected depth of low-level (LLD) or high-level (HLD) design questions.",
            "core_tech_stack_deep_dives": ["Framework or concept-specific topics, e.g., Concurrency in Java, DB indexing, React state lifecycle"]
        }},
        "recommended_portfolio_projects": [
            {{
                "project_title": "Actionable, relevant project idea a candidate could build to impress this team",
                "core_features": ["Feature 1", "Feature 2"],
                "target_tech_stack_to_use": ["Tech A", "Tech B"],
                "relevance_explanation": "Why this specific project stands out to this company's domain or tech stack."
            }}
        ],
        "strategic_interview_advice": "Final, actionable tips on matching culture, values, and addressing potential interview patterns."
    }}
    """

    return await _call_llm(system_prompt, user_prompt)