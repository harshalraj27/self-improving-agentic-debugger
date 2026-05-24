def calculate_metrics():
    # Intentionally trying to use an uninitialized variable to force a NameError
    undefined_variable_name = 42  # Initialize the variable
    print(undefined_variable_name)

if __name__ == "__main__":
    calculate_metrics()