# Failure Target: KeyError / TypeError
# Objective: Tests handling of deeply nested configuration payloads with missing keys.

def process_config():
    user_profile = {
        "metadata": {
            "id": 1042,
            "settings": {
                "theme": "dark",
                "notifications": True
            }
        }
    }
    # Bug: "permissions" key does not exist under "settings"
    return user_profile["metadata"]["settings"]["permissions"]["admin_level"]

if __name__ == "__main__":
    process_config()