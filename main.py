import os
import re
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables (expecting OPENAI_API_KEY)
load_dotenv()

# Configure logging for AI Defense monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ai_defense")


class GuardrailAction(Enum):
    """Actions that can be taken when a guardrail is triggered."""
    ALLOW = "allow"
    BLOCK = "block"
    LOG = "log"
    MODIFY = "modify"


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    passed: bool
    action: GuardrailAction
    message: str
    modified_content: Optional[str] = None
    violations: Optional[List[str]] = None


class CiscoAIDefenseGuardrails:
    """
    Cisco AI Defense Guardrails for LangChain applications.

    Application: langchain-cicd-app
    Description: Application ensuring AI security

    This class provides input validation, output validation, and security
    monitoring for LLM interactions.
    """

    # Patterns for detecting potentially malicious inputs
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+instructions",
        r"disregard\s+(your|the)\s+(instructions|rules|guidelines)",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"pretend\s+(you\s+are|to\s+be)",
        r"act\s+as\s+(if|a|an)",
        r"new\s+instructions:",
        r"override\s+(system|previous)",
        r"forget\s+(everything|your\s+instructions)",
        r"jailbreak",
        r"DAN\s+mode",
    ]

    # Patterns for detecting sensitive data in outputs
    SENSITIVE_DATA_PATTERNS = [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone number
        r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",  # SSN pattern
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b",  # Credit card
        r"sk-[a-zA-Z0-9]{48}",  # OpenAI API key pattern
        r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*",  # Bearer token
    ]

    # Blocked topics for this translation application
    BLOCKED_TOPICS = [
        "malware",
        "exploit",
        "hack",
        "illegal",
        "weapon",
    ]

    def __init__(
        self,
        application_name: str = "langchain-cicd-app",
        description: str = "Application ensuring AI security",
        enable_input_validation: bool = True,
        enable_output_validation: bool = True,
        enable_logging: bool = True,
        strict_mode: bool = False
    ):
        """
        Initialize the AI Defense Guardrails.

        Args:
            application_name: Name of the application for logging/monitoring
            description: Description of the application
            enable_input_validation: Whether to validate inputs
            enable_output_validation: Whether to validate outputs
            enable_logging: Whether to log all interactions
            strict_mode: If True, block on any violation; if False, log and allow
        """
        self.application_name = application_name
        self.description = description
        self.enable_input_validation = enable_input_validation
        self.enable_output_validation = enable_output_validation
        self.enable_logging = enable_logging
        self.strict_mode = strict_mode

        logger.info(
            f"AI Defense Guardrails initialized for '{application_name}': {description}"
        )

    def validate_input(self, user_input: str) -> GuardrailResult:
        """
        Validate user input before sending to the LLM.

        Checks for:
        - Prompt injection attempts
        - Blocked topics
        - Input length limits

        Args:
            user_input: The user's input text

        Returns:
            GuardrailResult with validation status
        """
        if not self.enable_input_validation:
            return GuardrailResult(
                passed=True,
                action=GuardrailAction.ALLOW,
                message="Input validation disabled"
            )

        violations = []

        # Check for prompt injection patterns
        input_lower = user_input.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                violations.append(f"Potential prompt injection detected: pattern '{pattern}'")

        # Check for blocked topics
        for topic in self.BLOCKED_TOPICS:
            if topic.lower() in input_lower:
                violations.append(f"Blocked topic detected: '{topic}'")

        # Check input length (prevent DoS via extremely long inputs)
        max_length = 10000
        if len(user_input) > max_length:
            violations.append(f"Input exceeds maximum length of {max_length} characters")

        if violations:
            if self.enable_logging:
                logger.warning(
                    f"[{self.application_name}] Input validation violations: {violations}"
                )

            if self.strict_mode:
                return GuardrailResult(
                    passed=False,
                    action=GuardrailAction.BLOCK,
                    message="Input blocked due to security violations",
                    violations=violations
                )
            else:
                return GuardrailResult(
                    passed=True,
                    action=GuardrailAction.LOG,
                    message="Input allowed with logged violations",
                    violations=violations
                )

        if self.enable_logging:
            logger.info(f"[{self.application_name}] Input validation passed")

        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW,
            message="Input validation passed"
        )

    def validate_output(self, llm_output: str) -> GuardrailResult:
        """
        Validate LLM output before returning to user.

        Checks for:
        - Sensitive data leakage
        - Blocked content patterns

        Args:
            llm_output: The LLM's response text

        Returns:
            GuardrailResult with validation status
        """
        if not self.enable_output_validation:
            return GuardrailResult(
                passed=True,
                action=GuardrailAction.ALLOW,
                message="Output validation disabled"
            )

        violations = []

        # Check for sensitive data patterns
        for pattern in self.SENSITIVE_DATA_PATTERNS:
            if re.search(pattern, llm_output):
                violations.append(f"Potential sensitive data detected: pattern '{pattern}'")

        if violations:
            if self.enable_logging:
                logger.warning(
                    f"[{self.application_name}] Output validation violations: {violations}"
                )

            if self.strict_mode:
                return GuardrailResult(
                    passed=False,
                    action=GuardrailAction.BLOCK,
                    message="Output blocked due to sensitive data detection",
                    violations=violations
                )
            else:
                return GuardrailResult(
                    passed=True,
                    action=GuardrailAction.LOG,
                    message="Output allowed with logged violations",
                    violations=violations
                )

        if self.enable_logging:
            logger.info(f"[{self.application_name}] Output validation passed")

        return GuardrailResult(
            passed=True,
            action=GuardrailAction.ALLOW,
            message="Output validation passed"
        )

    def wrap_llm_call(self, chain, input_dict: Dict[str, Any]) -> Optional[Any]:
        """
        Wrap an LLM chain invocation with guardrails.

        This method:
        1. Validates the input
        2. Invokes the LLM chain if input is valid
        3. Validates the output
        4. Returns the response if all checks pass

        Args:
            chain: The LangChain chain to invoke
            input_dict: The input dictionary for the chain

        Returns:
            The LLM response if all guardrails pass, None otherwise
        """
        # Extract the user input from the input dictionary
        user_input = input_dict.get("input", "")

        if self.enable_logging:
            logger.info(
                f"[{self.application_name}] Processing request with AI Defense Guardrails"
            )

        # Step 1: Validate input
        input_result = self.validate_input(user_input)
        if not input_result.passed:
            logger.error(
                f"[{self.application_name}] Request blocked at input validation: "
                f"{input_result.message}"
            )
            return None

        # Step 2: Invoke the LLM chain
        try:
            response = chain.invoke(input_dict)
        except Exception as e:
            logger.error(f"[{self.application_name}] LLM invocation error: {e}")
            raise

        # Step 3: Validate output
        output_content = response.content if hasattr(response, 'content') else str(response)
        output_result = self.validate_output(output_content)

        if not output_result.passed:
            logger.error(
                f"[{self.application_name}] Response blocked at output validation: "
                f"{output_result.message}"
            )
            return None

        return response


def main():
    # Check if API key is present
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found. Please set it in .env or environment variables.")
        return

    # Initialize the ChatOpenAI model
    llm = ChatOpenAI(model="gpt-3.5-turbo")

    # Define the prompt template with system and user messages
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that translates English to Japanese."),
        ("user", "{input}")
    ])

    # Create a chain combining the prompt and the LLM
    chain = prompt | llm

    # Initialize Cisco AI Defense Guardrails
    guardrails = CiscoAIDefenseGuardrails(
        application_name="langchain-cicd-app",
        description="Application ensuring AI security",
        enable_input_validation=True,
        enable_output_validation=True,
        enable_logging=True,
        strict_mode=True  # Block requests that fail validation
    )

    # Fixed user message to send
    user_message = "Hello, how are you?"

    # Invoke the chain with AI Defense Guardrails protection
    response = guardrails.wrap_llm_call(chain, {"input": user_message})

    # Print the response content
    if response:
        print(f"User: {user_message}")
        print(f"AI: {response.content}")
    else:
        print("Request was blocked by AI Defense Guardrails.")

if __name__ == "__main__":
    main()
