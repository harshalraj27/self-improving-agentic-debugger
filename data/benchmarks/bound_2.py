# Failure Target: IndexError / ValueError
# Objective: Simulates improper windowing/slicing algorithms on stream data.

def compute_moving_average():
    stream_data = [10.5, 20.1, 30.4]
    # Bug: Popping from empty list after exhausting elements in a naive loop
    for i in range(5):
        stream_data.pop(0)
        current_frame = stream_data[0]
    return stream_data

if __name__ == "__main__":
    compute_moving_average()