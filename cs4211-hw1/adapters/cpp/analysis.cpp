#include "semantics.hpp"

#include "codec.hpp"

namespace imp {

ClassifyResult classify(const CommandPtr& command, const State& state,
                        ArithmeticMode arithmetic, long long budget) {
    // PART C: use configurationKey(...) to compare configurations by value.
    // At each iteration check Skip, a repeat, then the budget.  Record the
    // configuration and call stepC.  Catch Stuck and treat std::nullopt as
    // stuck; a failed attempt does not increment the step count.
    (void)command; (void)state; (void)arithmetic; (void)budget;
    throw std::runtime_error("TODO Part C: classify");
}

std::vector<Configuration> stepAll(const CommandPtr& command, const State& state,
                                   ArithmeticMode arithmetic) {
    (void)command; (void)state; (void)arithmetic;
    throw std::runtime_error("TODO bonus: stepAll");
}

ExploreResult explore(const CommandPtr& command, const State& state,
                      ArithmeticMode arithmetic, long long budget) {
    (void)command; (void)state; (void)arithmetic; (void)budget;
    throw std::runtime_error("TODO bonus: explore");
}

}  // namespace imp
