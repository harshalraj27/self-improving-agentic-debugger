// Failure Target: Compilation Error or Undefined Behavior / Crash
// Objective: Simulates critical memory scope leakage.

#include <iostream>

int* get_untrusted_pointer() {
    int temporary_scope_variable = 42;
    // Bug: Returning the address of a local variable that dies when the scope exits
    return &temporary_scope_variable;
}

int main() {
    int* leaked_ptr = get_untrusted_pointer();
    std::cout << "Leaked Value: " << *leaked_ptr << std::endl; // Undefined or fault
    return 0;
}