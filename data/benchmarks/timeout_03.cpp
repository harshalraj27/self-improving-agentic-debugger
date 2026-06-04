// Failure Target: Execution Timeout (Docker Force-Kill)
// Objective: Validates exit code 124 capturing under infinite native binary executions.

#include <iostream>
#include <vector>

int main() {
    std::vector<int> telemetry_packets = {1, 2, 3};
    auto it = telemetry_packets.begin();

    while (it != telemetry_packets.end()) {
        std::cout << "Processing packet ID: " << *it << std::endl;
        // Bug: Iterator is never incremented (++it is missing), creating an infinite loop
    }

    return 0;
}