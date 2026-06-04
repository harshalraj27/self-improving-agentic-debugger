# Failure Target: TypeError
# Objective: Simulates reading unparsed payload strings directly into mathematical models.

def calculate_yield():
    base_coefficient = 1.45
    parsed_sensor_inputs = ["12", "45", "98", "invalid_string_float"]

    # Bug: Directly adding a float to a raw string element
    total_yield = base_coefficient + parsed_sensor_inputs[0]
    return total_yield


if __name__ == "__main__":
    calculate_yield()