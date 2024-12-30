from llm_guard.input_scanners import PromptInjection
from llm_guard.input_scanners.prompt_injection import MatchType

def judgement(message):
    scanner = PromptInjection(threshold=0.5, match_type=MatchType.FULL)
    prompt = message
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return is_valid


