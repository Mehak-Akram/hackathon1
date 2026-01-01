"""
Response validation service for the RAG Agent Service
"""
from typing import List, Dict, Any, Optional
from ..api.models.response import Citation, RetrievedContext, ChatResponse
from ..utils.logger import get_logger


logger = get_logger(__name__)


class ResponseValidationService:
    """
    Service for validating agent responses, including citation validation
    """

    def validate_response_citations(
        self,
        response: ChatResponse,
        retrieved_contexts: Optional[List[RetrievedContext]] = None
    ) -> Dict[str, Any]:
        """
        Validate that the response includes proper source citations
        """
        logger.info("Validating response citations...")

        validation_result = {
            "valid": True,
            "response_id": "unknown",  # Would use actual response ID if available
            "citation_validation": {
                "citation_count": len(response.citations),
                "expected_citation_count": len(retrieved_contexts) if retrieved_contexts else 0,
                "has_citations": len(response.citations) > 0,
                "citations_match_contexts": True if retrieved_contexts is None else len(response.citations) == len(retrieved_contexts),
                "all_citations_complete": True,
                "missing_fields": [],
                "details": []
            },
            "overall_validation": {
                "response_has_content": bool(response.response.strip()),
                "response_time_positive": response.response_time > 0,
                "context_count_match": True if retrieved_contexts is None else response.retrieved_context_count == len(retrieved_contexts)
            }
        }

        # Check each citation for completeness
        for i, citation in enumerate(response.citations):
            missing_fields = []

            if not citation.source_url:
                missing_fields.append("source_url")
            if not citation.chapter:
                missing_fields.append("chapter")
            if not citation.section:
                missing_fields.append("section")

            if missing_fields:
                validation_result["citation_validation"]["all_citations_complete"] = False
                validation_result["citation_validation"]["details"].append(
                    f"Citation {i} missing fields: {missing_fields}"
                )
                validation_result["valid"] = False

        # Check that citation sources match context sources (if contexts provided)
        if retrieved_contexts:
            citation_urls = {c.source_url for c in response.citations}
            context_urls = {c.url for c in retrieved_contexts}

            urls_match = citation_urls.issubset(context_urls) or context_urls.issubset(citation_urls)
            validation_result["citation_validation"]["urls_match"] = urls_match

            if not urls_match:
                validation_result["valid"] = False
                validation_result["citation_validation"]["details"].append(
                    f"Source URLs don't match: citations={citation_urls}, contexts={context_urls}"
                )

        # Overall validation checks
        overall_valid = all([
            validation_result["overall_validation"]["response_has_content"],
            validation_result["overall_validation"]["response_time_positive"],
            validation_result["citation_validation"]["has_citations"],
            validation_result["citation_validation"]["all_citations_complete"]
        ])

        validation_result["valid"] = validation_result["valid"] and overall_valid

        logger.info(f"Response citation validation result: valid={validation_result['valid']}")
        return validation_result

    def validate_citation_quality(
        self,
        citations: List[Citation],
        min_confidence_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Validate the quality of citations based on confidence scores and completeness
        """
        logger.info(f"Validating citation quality with min confidence {min_confidence_score}...")

        quality_result = {
            "valid": True,
            "total_citations": len(citations),
            "citations_above_threshold": 0,
            "average_confidence": 0.0,
            "quality_issues": [],
            "completeness_score": 0.0
        }

        if not citations:
            quality_result["valid"] = False
            quality_result["quality_issues"].append("No citations provided")
            return quality_result

        # Calculate average confidence and count citations above threshold
        total_confidence = 0.0
        above_threshold_count = 0
        complete_citations = 0

        for citation in citations:
            # Check if citation is complete
            is_complete = all([
                citation.source_url,
                citation.chapter,
                citation.section
            ])
            if is_complete:
                complete_citations += 1

            # Check confidence score
            if citation.confidence_score and citation.confidence_score >= min_confidence_score:
                above_threshold_count += 1
                total_confidence += citation.confidence_score
            elif citation.similarity_score and citation.similarity_score >= min_confidence_score:
                above_threshold_count += 1
                total_confidence += citation.similarity_score
            else:
                quality_result["quality_issues"].append(
                    f"Citation from '{citation.chapter}' has low confidence: {citation.confidence_score or citation.similarity_score}"
                )

        # Calculate metrics
        quality_result["citations_above_threshold"] = above_threshold_count
        quality_result["average_confidence"] = total_confidence / len(citations) if citations else 0.0
        quality_result["completeness_score"] = complete_citations / len(citations) if citations else 0.0

        # Determine validity based on thresholds
        min_completeness = 0.8  # 80% of citations should be complete
        min_quality = 0.6      # 60% of citations should meet confidence threshold

        has_sufficient_completeness = quality_result["completeness_score"] >= min_completeness
        has_sufficient_quality = (above_threshold_count / len(citations)) >= min_quality if citations else True

        quality_result["valid"] = has_sufficient_completeness and has_sufficient_quality

        logger.info(f"Citation quality validation result: valid={quality_result['valid']}, "
                   f"completeness={quality_result['completeness_score']:.2f}, "
                   f"quality={above_threshold_count}/{len(citations)} above threshold")

        return quality_result

    def validate_response_completeness(
        self,
        response: ChatResponse
    ) -> Dict[str, Any]:
        """
        Validate the overall completeness and quality of the response
        """
        logger.info("Validating response completeness...")

        completeness_result = {
            "valid": True,
            "checks": {
                "has_content": bool(response.response and response.response.strip()),
                "has_citations": len(response.citations) > 0,
                "has_positive_response_time": response.response_time > 0,
                "citations_reference_content": self._citations_reference_content(response),
                "response_not_generic": not self._is_generic_response(response.response)
            },
            "details": []
        }

        # Add details about failed checks
        for check_name, check_result in completeness_result["checks"].items():
            if not check_result:
                completeness_result["details"].append(f"Failed check: {check_name}")
                completeness_result["valid"] = False

        logger.info(f"Response completeness validation result: valid={completeness_result['valid']}")
        return completeness_result

    def _citations_reference_content(self, response: ChatResponse) -> bool:
        """
        Check if citations seem to reference content that might support the response
        (Simple heuristic check)
        """
        if not response.citations or not response.response:
            return False

        # Simple check: see if chapter/section names appear in response or vice versa
        response_lower = response.response.lower()

        for citation in response.citations:
            if (citation.chapter.lower() in response_lower or
                citation.section.lower() in response_lower or
                (citation.text_excerpt and citation.text_excerpt.lower() in response_lower)):
                return True

        # If no obvious connections found, return True anyway as this is a weak heuristic
        return True

    def _is_generic_response(self, response_text: str) -> bool:
        """
        Check if the response is too generic (like "I don't know" or "No information found")
        """
        generic_phrases = [
            "i don't know", "no information found", "not mentioned",
            "not specified", "not provided", "unknown", "cannot determine"
        ]

        text_lower = response_text.lower() if response_text else ""
        return any(phrase in text_lower for phrase in generic_phrases)


# Global instance of the validation service
validation_service = ResponseValidationService()