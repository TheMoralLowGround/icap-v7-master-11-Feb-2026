import json
from typing import Dict, Any, Optional
from llm_clients import run_llm


class CodeGenerator:
    """Generate Python transformation code from natural language prompts using LLM."""

    def __init__(self):
        """Initialize code generator."""
        pass

    def generate(
        self, prompt: str, sample_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Python transformation code from natural language prompt.

        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prompt, sample_data)

        # Generate code using LLM client
        response, reasoning = run_llm(system_prompt, user_prompt)

        # Extract code from response
        code = self._extract_code(response)
        return code

    def _build_system_prompt(self) -> str:
        """Build system prompt with code generation requirements."""
        return """You are a code generator for JSON transformations. Generate Python code that transforms JSON data.

        CRITICAL REQUIREMENTS:
        1. Generate a Python function named 'transform_json' that takes 'data' as parameter
        2. The function MUST return a dictionary (modified copy of input)
        3. Use ONLY these imports: copy, json, argparse, datetime, decimal, re, collections, itertools, functools, math
        4. DO NOT use: eval, exec, __import__, network calls, os, sys (except for argparse)
        5. Use copy.deepcopy() to avoid mutating the input
        6. Include inline comments explaining the transformation logic
        7. Handle edge cases (missing keys, None values, empty arrays)
        8. Use type hints for clarity
        9. MUST include a main block with argparse for command-line execution

        CODE TEMPLATE:
        ```python
        import copy
        import json
        import argparse
        from typing import Dict, Any

        def transform_json(data: Dict[str, Any]) -> Dict[str, Any]:
            \"\"\"Transform JSON data according to requirements.\"\"\"
            result = copy.deepcopy(data)
            
            # Your transformation logic here
            
            return result


        if __name__ == '__main__':
            parser = argparse.ArgumentParser(description='Transform JSON data')
            parser.add_argument('-i', '--input', required=True, help='Input JSON file path')
            parser.add_argument('-p', '--prompt', help='Transformation prompt/description')
            parser.add_argument('-o', '--output', required=True, help='Output JSON file path')
            
            args = parser.parse_args()
            
            # Read input JSON file
            with open(args.input, 'r') as f:
                input_data = json.load(f)
            
            # Transform the data
            result = transform_json(input_data)
            
            # Write output JSON file
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"Transformation complete. Output written to {args.output}")
        ```

        IMPORTANT:
        - Generate ONLY the Python code (including necessary imports and main block)
        - Do NOT include explanations before or after the code
        - Do NOT include example usage or test cases
        - Ensure the code is production-ready and handles errors gracefully
        - ALWAYS include the main block with argparse as shown in the template"""

    def _build_user_prompt(
        self, prompt: str, sample_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build user prompt with transformation requirements."""
        user_msg = f"""Transform JSON according to this requirement:
        {prompt}"""

        if sample_data:
            user_msg += f"""Sample input data for context:
                        {json.dumps(sample_data, indent=2)}"""

        user_msg += "\nGenerate the complete Python code now. Include only the code, no explanations."

        return user_msg

    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response."""
        # Remove markdown code blocks if present
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code = parts[1].split("```")[0].strip()
                return code

        elif "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                code = parts[1].strip()
                # Remove language identifier if present
                if code.startswith("python\n"):
                    code = code[7:]
                return code

        # If no code blocks found, return the whole response stripped
        return response.strip()
