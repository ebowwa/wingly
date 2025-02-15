import uuid
from typing import Optional

def generate_session_id(prefix: Optional[str] = None) -> str:
    """
    Generate a unique session ID optionally prefixed with a string.
    
    Args:
        prefix (str, optional): A prefix to add to the UUID.
        
    Returns:
        str: A unique session identifier
    """
    session_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}-{session_id}"
    return session_id

if __name__ == "__main__":
    # Demonstration of usage
    print("\n🔑 UUID Session Generator Demo\n")
    
    # Generate a simple session ID
    simple_session = generate_session_id()
    print(f"Simple Session ID: {simple_session}")
    
    # Generate a session ID with prefix
    prefixed_session = generate_session_id(prefix="user")
    print(f"Prefixed Session ID: {prefixed_session}")
    
    # Generate multiple sessions to demonstrate uniqueness
    print("\nGenerating multiple sessions to demonstrate uniqueness:")
    sessions = [generate_session_id() for _ in range(3)]
    for i, session in enumerate(sessions, 1):
        print(f"Session {i}: {session}")