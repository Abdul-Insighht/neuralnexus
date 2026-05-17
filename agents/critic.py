"""
Critic Agent
────────────
Answer quality assurance: reviews every response before the user sees it.
Scores on accuracy, completeness, uncertainty acknowledgment, and adds caveats.
"""

from typing import Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse


class CriticAgent(BaseAgent):
    """
    Reviews and quality-checks any answer before it reaches the user.
    
    Evaluates:
      - Factual accuracy (are claims supported by data?)
      - Completeness (are important aspects missing?)
      - Uncertainty acknowledgment (are limitations stated?)
      - Bias detection (is the answer one-sided?)
      - Actionability (can the user act on this?)
    """

    def __init__(self, min_quality_score: float = 0.6):
        super().__init__(
            agent_name="CriticAgent",
            model_key="critic",
            system_instruction=(
                "You are the CriticAgent — a quality assurance reviewer for enterprise AI responses. "
                "Your role is to critically evaluate answers for accuracy, completeness, and reliability. "
                "You must:\n"
                "1. Score the answer on 5 dimensions (each 0-100): "
                "Accuracy, Completeness, Uncertainty Handling, Actionability, Clarity\n"
                "2. Flag any unsupported claims\n"
                "3. Add necessary caveats or disclaimers\n"
                "4. Suggest improvements if the quality is below standard\n"
                "5. Give an overall quality score (0-100%) and PASS/REVISE verdict\n\n"
                "Be constructive but rigorous. Enterprise decisions depend on this."
            ),
        )
        self.min_score = min_quality_score

    def review(self, answer: AgentResponse,
               original_query: str = "",
               available_data_summary: str = "") -> Dict:
        """
        Review an agent's answer for quality.
        
        Returns:
            Dict with 'quality_score', 'verdict' (PASS/REVISE), 'caveats',
            'improved_answer', and detailed dimension scores.
        """
        context = (
            f"ORIGINAL USER QUERY:\n{original_query}\n\n"
            f"AGENT RESPONSE (from {answer.agent_name}):\n{answer.content}\n\n"
            f"RESPONSE CONFIDENCE: {answer.confidence:.0%}\n"
            f"SOURCES CITED: {', '.join(answer.sources_used) if answer.sources_used else 'None'}\n"
        )

        if available_data_summary:
            context += f"\nAVAILABLE DATA CONTEXT:\n{available_data_summary}\n"

        prompt = (
            "Review this enterprise AI response for quality. Provide your evaluation "
            "in this exact format:\n\n"
            "DIMENSION SCORES:\n"
            "- Accuracy: X/100\n"
            "- Completeness: X/100\n"
            "- Uncertainty Handling: X/100\n"
            "- Actionability: X/100\n"
            "- Clarity: X/100\n\n"
            "OVERALL: X/100\n"
            "VERDICT: PASS or REVISE\n\n"
            "UNSUPPORTED CLAIMS: [list any]\n\n"
            "CAVEATS TO ADD: [list any]\n\n"
            "IMPROVEMENTS: [if REVISE, explain what needs to change]\n"
        )

        review_response = self.query(prompt, context=context)

        # Parse the review
        result = {
            "quality_score": review_response.confidence,
            "verdict": "PASS" if review_response.confidence >= self.min_score else "REVISE",
            "review_text": review_response.content,
            "original_answer": answer.content,
            "caveats": self._extract_caveats(review_response.content),
        }

        # If quality is acceptable, enhance the answer with caveats
        if result["verdict"] == "PASS" and result["caveats"]:
            result["enhanced_answer"] = self._add_caveats(answer.content, result["caveats"])
        else:
            result["enhanced_answer"] = answer.content

        return result

    def quick_check(self, answer_text: str) -> Dict:
        """Quick quality check without full review."""
        prompt = (
            f"Rate this enterprise AI answer 0-100 on reliability. "
            f"Reply with just: SCORE: X, VERDICT: PASS/REVISE, MAIN_CONCERN: [one line]\n\n"
            f"Answer to review:\n{answer_text[:2000]}"
        )

        response = self.query(prompt, temperature=0.1)

        return {
            "quality_score": response.confidence,
            "verdict": "PASS" if response.confidence >= self.min_score else "REVISE",
            "feedback": response.content,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _extract_caveats(self, review_text: str) -> List[str]:
        """Extract caveats from review text."""
        caveats = []
        in_caveats = False
        for line in review_text.split("\n"):
            line_stripped = line.strip()
            if "CAVEAT" in line.upper():
                in_caveats = True
                continue
            if in_caveats and line_stripped.startswith(("-", "•", "*", "1", "2", "3")):
                caveat = line_stripped.lstrip("-•* 0123456789.")
                if caveat:
                    caveats.append(caveat.strip())
            elif in_caveats and line_stripped == "":
                in_caveats = False

        return caveats

    def _add_caveats(self, answer: str, caveats: List[str]) -> str:
        """Append caveats to an answer."""
        if not caveats:
            return answer

        caveat_section = "\n\n⚠️ **Important Caveats:**\n"
        for c in caveats:
            caveat_section += f"- {c}\n"

        return answer + caveat_section
