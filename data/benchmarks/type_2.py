# Failure Target: TypeError
# Objective: Attempts to use mutable objects as lookup keys.

def cache_session_states():
    lookup_cache = {}
    active_tokens = ["auth_token_a", "auth_token_b"]

    # Bug: Lists are mutable and cannot be hashed as dictionary keys
    lookup_cache[active_tokens] = "Session_Active_01"
    return lookup_cache


if __name__ == "__main__":
    cache_session_states()