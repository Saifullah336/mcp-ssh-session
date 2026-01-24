"""Command validation and output limiting for SSH sessions."""
import os
import re
import tempfile
from typing import Optional, Tuple


class CommandValidator:
    """Validates commands for safety before execution."""

    # Maximum output size in bytes (10MB)
    MAX_OUTPUT_SIZE = 10 * 1024 * 1024

    # Patterns that indicate streaming/indefinite commands
    STREAMING_PATTERNS = []

    # Patterns for background processes
    BACKGROUND_PATTERNS = [
        r'&\s*$',  # Command ending with &
        r'\bnohup\b',
        r'\bdisown\b',
        r'\bscreen\b',
        r'\btmux\b',
    ]

    # Potentially dangerous commands (optional - can be enabled/disabled)
    DANGEROUS_PATTERNS = [
        r'\brm\s+.*-rf\s+/(?!home|tmp)',  # rm -rf on root paths
        r'\bdd\s+.*of=/dev/',  # dd to device files
        r'\b:\(\)\{.*:\|:.*\};:',  # fork bomb
        r'\bmkfs\b',
        r'\bformat\b',
    ]

    @classmethod
    def validate_command(cls, command: str, check_dangerous: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate a command for safety.

        Args:
            command: The command to validate
            check_dangerous: Whether to check for dangerous patterns

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        command_lower = command.lower().strip()

        # Check for streaming patterns
        for pattern in cls.STREAMING_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Streaming/interactive command blocked: Matches pattern '{pattern}'. Use finite operations (e.g., 'tail -n 100' instead of 'tail -f')."

        # Check for background processes
        for pattern in cls.BACKGROUND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Background process blocked: Matches pattern '{pattern}'. Background processes are not allowed."

        # Check for dangerous commands (optional)
        if check_dangerous:
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, f"Dangerous command blocked: Matches pattern '{pattern}'. This operation is not allowed for safety."

        return True, None


def check_permission(host: str, title: str, message: str) -> bool | str:
    """
    Ask for user permission using xdialog (cross-platform native dialogs).

    Paranoia mode is controlled per-host via env var: {host}_PARANOIA=1

    Args:
        host: SSH host/alias for paranoia mode check
        title: Dialog title
        message: Dialog message

    Returns:
        bool | str: True if user approves or paranoia mode disabled, error message string if denied
    """
    # Find the latest permission file in the known folder
    permission_dir = os.path.join(tempfile.gettempdir(), "mcp-ssh-permissions")
    permission_file = None
    
    if os.path.exists(permission_dir):
        try:
            # Get all files in the directory
            files = [os.path.join(permission_dir, f) for f in os.listdir(permission_dir) 
                     if os.path.isfile(os.path.join(permission_dir, f))]
            if files:
                # Find the most recently modified file
                permission_file = max(files, key=os.path.getmtime)
                # Write waiting status
                with open(permission_file, 'w') as f:
                    f.write("waiting")
        except:
            pass
    
    # Check if paranoia mode is enabled for this host
    if os.getenv(f"{host}_PARANOIA") != "1":
        # Write approved status if permission file exists
        if permission_file:
            try:
                with open(permission_file, 'w') as f:
                    f.write("approved")
            except:
                pass
        return True

    # Use zenity backend if available, otherwise fallback to default
    try:
        import xdialog.zenity_dialogs as zenity
        result = zenity.okcancel(title=title, message=message)
        approved = result == 0  # 0 = OK, 1 = Cancel
    except Exception:
        # Fallback to xdialog default
        import xdialog
        result = xdialog.okcancel(title=title, message=message)
        approved = result == 0  # 0 = OK, 1 = Cancel

    # Write final permission result if permission file exists
    if permission_file:
        try:
            with open(permission_file, 'w') as f:
                f.write("approved" if approved else "denied")
        except:
            pass

    # If denied, check for feedback file
    if not approved:
        feedback_file = os.getenv("FEEDBACK_FILE")
        if feedback_file and os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r') as f:
                    feedback = f.read().strip()
                if feedback:
                    # Clear the feedback file
                    try:
                        with open(feedback_file, 'w') as f:
                            f.write("")
                    except Exception:
                        pass  # Ignore errors when clearing
                    return f"Permission denied by user. user_message:{feedback}"
            except Exception:
                pass  # Ignore errors when reading feedback file
        return "Permission denied by user"

    return approved


class OutputLimiter:
    """Limits output size to prevent memory issues."""

    def __init__(self, max_size: int = CommandValidator.MAX_OUTPUT_SIZE):
        self.max_size = max_size
        self.current_size = 0
        self.truncated = False

    def add_chunk(self, chunk: str) -> Tuple[str, bool]:
        """
        Add a chunk of output, enforcing size limits.

        Args:
            chunk: The chunk of output to add

        Returns:
            Tuple of (chunk_to_add: str, should_continue: bool)
        """
        chunk_size = len(chunk.encode('utf-8'))

        if self.current_size + chunk_size > self.max_size:
            # Calculate how much we can still add
            remaining = self.max_size - self.current_size
            if remaining > 0:
                # Truncate the chunk
                truncated_chunk = chunk.encode('utf-8')[:remaining].decode('utf-8', errors='ignore')
                self.current_size = self.max_size
                self.truncated = True
                truncation_msg = f"\n\n[OUTPUT TRUNCATED: Maximum output size of {self.max_size} bytes exceeded]"
                return truncated_chunk + truncation_msg, False
            else:
                return "", False

        self.current_size += chunk_size
        return chunk, True