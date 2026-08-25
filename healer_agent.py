import os
import re
import subprocess
import sys
import time
from pathlib import Path

from google import genai


TARGET_FILE = Path("broken_app.py")
MODEL_NAME = "gemini-3.5-flash-lite"
MAX_ATTEMPTS = 3
LLM_RETRIES = 3

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def log(message: str) -> None:
    print(f"[HEALER] {message}")


def run_python_file(file_path: Path) -> subprocess.CompletedProcess:
    """
    Run the target Python program and capture its output.

    subprocess.run() creates a separate process.
    capture_output=True captures stdout and stderr.
    returncode 0 means success; anything else means failure.
    """

    log(f"Executing {file_path}...")

    return subprocess.run(
        [sys.executable, str(file_path)],
        capture_output=True,
        text=True
    )


def get_error_traceback(
    result: subprocess.CompletedProcess
) -> str:
    """Collect the program's output and traceback."""

    output_parts = []

    if result.stdout.strip():
        output_parts.append(
            "STDOUT:\n" + result.stdout.strip()
        )

    if result.stderr.strip():
        output_parts.append(
            "STDERR:\n" + result.stderr.strip()
        )

    return "\n\n".join(output_parts)


def create_gemini_client() -> genai.Client:
    """Create the Gemini API client."""

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY was not found.\n"
            'Run: $env:GEMINI_API_KEY="YOUR_API_KEY"'
        )

    return genai.Client(
        api_key=GEMINI_API_KEY
    )
SYSTEM_PROMPT = """
You are an expert Senior Python Debugging Engineer.

Your job is to repair a broken Python program.

You will receive:
1. The complete Python source code.
2. The exact runtime traceback.

STRICT RULES:
- Fix the actual root cause.
- Preserve the original purpose and functionality.
- Do not unnecessarily rewrite working code.
- Do not remove functionality just to avoid the error.
- Return the COMPLETE corrected Python program.
- Return ONLY ONE Python Markdown code block.
- Do not include explanations outside the code block.
- Do not say "Here is the corrected code".

Expected format:

```python
# complete corrected Python program
"""

def ask_gemini(
client: genai.Client,
source_code: str,
traceback: str
) -> str:
    prompt = f"""
SOURCE CODE
========================================

{source_code}

========================================

RUNTIME TRACEBACK
========================================

{traceback}

========================================

Repair the program according to the system instructions.
"""

    for retry in range(1, LLM_RETRIES + 1):

        try:
            log(
                f"Sending code and traceback to Gemini "
                f"(attempt {retry}/{LLM_RETRIES})..."
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT
                }
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as error:

            log(f"Gemini request failed: {error}")

            if retry < LLM_RETRIES:
                log("Retrying in 3 seconds...")
                time.sleep(3)

            else:
                raise RuntimeError(
                    "Gemini request failed after "
                    f"{LLM_RETRIES} attempts."
                ) from error

    raise RuntimeError("Unexpected Gemini failure.")


def extract_code(llm_response: str) -> str:
    """
    Extract Python code from Gemini's Markdown response.

    The regex looks for:

        ```python
        corrected code
        ```

    The (.*?) captures the code between the two code fences.

    re.DOTALL allows the regex to match multiple lines.
    """

    match = re.search(
        r"```python\s*(.*?)```",
        llm_response,
        flags=re.DOTALL | re.IGNORECASE
    )

    if not match:
        match = re.search(
            r"```\s*(.*?)```",
            llm_response,
            flags=re.DOTALL
        )

    if not match:
        raise ValueError(
            "No Python code block found in Gemini response."
        )

    clean_code = match.group(1).strip()

    if not clean_code:
        raise ValueError(
            "Gemini returned an empty code block."
        )

    return clean_code
# ============================================================
# FILE OPERATIONS
# ============================================================

def read_source(file_path: Path) -> str:
    """Read the current Python source code."""
    return file_path.read_text(encoding="utf-8")


def backup_file(file_path: Path) -> Path:
    """Create a backup before replacing the original file."""

    backup_path = file_path.with_suffix(".py.backup")

    original_code = read_source(file_path)

    backup_path.write_text(
        original_code,
        encoding="utf-8"
    )

    log(f"Backup created: {backup_path}")

    return backup_path


def write_fixed_code(
    file_path: Path,
    fixed_code: str
) -> None:
    """Replace the broken application with the AI-generated fix."""

    backup_file(file_path)

    file_path.write_text(
        fixed_code,
        encoding="utf-8"
    )

    log(f"AI-generated fix written to {file_path}")


# ============================================================
# SYNTAX VALIDATION
# ============================================================

def validate_syntax(
    source_code: str,
    file_path: Path
) -> None:
    """
    Check whether the AI-generated code is valid Python.

    compile() checks the code without actually executing it.
    """

    compile(
        source_code,
        str(file_path),
        "exec"
    )

    log("Syntax validation passed.")


# ============================================================
# EXECUTION VALIDATION
# ============================================================

def validate_execution(
    file_path: Path
) -> bool:
    """
    Run the repaired program.

    Exit code 0 means successful execution.
    """

    log("Starting secondary execution validation...")

    result = run_python_file(file_path)

    if result.stdout.strip():
        log("Program output:")
        print(result.stdout.strip())

    if result.returncode == 0:
        log("Validation successful: exit code = 0")
        return True

    log(
        f"Validation failed: exit code = "
        f"{result.returncode}"
    )

    if result.stderr.strip():
        log("New traceback:")
        print(result.stderr.strip())

    return False


# ============================================================
# SELF-HEALING LOOP
# ============================================================

def heal_application() -> bool:
    """
    Main self-healing loop.

    The agent can make at most three repair attempts.

    If a repair creates another error, the new traceback
    is sent to Gemini during the next attempt.
    """

    if not TARGET_FILE.exists():
        log(f"Target file not found: {TARGET_FILE}")
        return False

    client = create_gemini_client()

    for attempt in range(1, MAX_ATTEMPTS + 1):

        log("=" * 65)
        log(
            f"SELF-HEALING ATTEMPT "
            f"{attempt}/{MAX_ATTEMPTS}"
        )
        log("=" * 65)

        # Run the current application.
        result = run_python_file(TARGET_FILE)

        # If it already works, we are finished.
        if result.returncode == 0:

            log("Application is already healthy.")

            if result.stdout.strip():
                print(result.stdout.strip())

            return True

        # Capture the exact runtime traceback.
        traceback = get_error_traceback(result)

        log("Application crashed.")
        log("Captured runtime traceback:")

        print(traceback)

        # Read the current version of the source code.
        source_code = read_source(TARGET_FILE)

        # Ask Gemini to repair it.
        try:

            llm_response = ask_gemini(
                client,
                source_code,
                traceback
            )

        except Exception as error:

            log(f"LLM repair failed: {error}")
            return False

        # Extract the clean Python code.
        try:

            fixed_code = extract_code(
                llm_response
            )

        except ValueError as error:

            log(f"Code extraction failed: {error}")
            return False

        log(
            "Successfully extracted corrected Python code."
        )

        # Check syntax before modifying the original file.
        try:

            validate_syntax(
                fixed_code,
                TARGET_FILE
            )

        except SyntaxError as error:

            log(
                "Gemini generated invalid Python syntax."
            )

            log(
                f"Syntax error: {error}"
            )

            continue

        # Backup and replace the broken application.
        write_fixed_code(
            TARGET_FILE,
            fixed_code
        )

        # Run the repaired program.
        if validate_execution(TARGET_FILE):

            log("=" * 65)
            log("SELF-HEALING COMPLETE")
            log("=" * 65)

            return True

        log(
            "The AI fix did not completely resolve "
            "the problem."
        )

        log(
            "The next attempt will analyze the new error."
        )

    # Three attempts were unsuccessful.
    log("=" * 65)
    log("SELF-HEALING FAILED")
    log(
        f"Maximum attempts ({MAX_ATTEMPTS}) reached."
    )
    log("=" * 65)

    return False


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    log(
        "Starting Self-Healing Python Code Agent..."
    )

    log(
        f"Target application: {TARGET_FILE}"
    )

    log(
        f"Maximum repair attempts: {MAX_ATTEMPTS}"
    )

    try:

        success = heal_application()

    except KeyboardInterrupt:

        log("Agent interrupted by user.")

        sys.exit(130)

    except Exception as error:

        log(
            f"Unexpected agent error: {error}"
        )

        sys.exit(1)

    sys.exit(
        0 if success else 1
    )