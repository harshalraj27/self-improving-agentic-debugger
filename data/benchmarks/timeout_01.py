# Failure Target: Execution Timeout (Docker Force-Kill)
# Objective: Tests if your timeout parameter prevents CPU starvation on the host machine.

import time


def process_event_loop():
    event_queue_length = 10
    processed_count = 0

    while processed_count < event_queue_length:
        # Bug: Logic path forgets to increment processed_count, freezing execution indefinitely
        if False:
            processed_count += 1
        time.sleep(0.1)


if __name__ == "__main__":
    process_event_loop()