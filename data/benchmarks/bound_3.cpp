// Failure Target: std::out_of_range exception
// Objective: Validates that your runner catches C++ runtime exceptions safely.

#include <iostream>
#include <vector>

int main() {
    std::vector<int> dynamic_buffer = {101, 102, 103, 104};
    
    // Bug: .at() enforces bounds checking and throws std::out_of_range at index 4
    int critical_metric = dynamic_buffer.at(4); 
    
    std::cout << "Metric: " << critical_metric << std::endl;
    return 0;
}