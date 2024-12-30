from llm_guard.output_scanners import Toxicity
from llm_guard.output_scanners.toxicity import MatchType

def output_judge(message,output):
    scanner = Toxicity(threshold=0.5, match_type=MatchType.SENTENCE)
    prompt = message
    model_output = output
    sanitized_output, is_valid, risk_score = scanner.scan(prompt, model_output)
    return is_valid
    