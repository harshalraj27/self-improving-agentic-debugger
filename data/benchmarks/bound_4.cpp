// Failure Target: SIGSEGV (Segmentation Fault)
// Objective: Proves the sandbox intercepts raw memory access violations.

#include <iostream>

int main() {
    int static_matrix[3] = {10, 20, 30};

    // Bug: Writing wildly outside stack allocation boundaries
    for(int i = 0; i < 100; ++i) {
        static_matrix[i * 10] = 999;
    }

    return 0;
}