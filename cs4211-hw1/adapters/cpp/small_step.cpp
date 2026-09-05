#include "semantics.hpp"

namespace imp {

// PART B: Implement the handout's definitive one-step rules and runs here.

std::optional<AExpPtr> stepA(const AExpPtr& expression, const State& state,
                             ArithmeticMode arithmetic) {
    // Return a residual AExpPtr, such as std::make_shared<AExp>(Num{value}),
    // not a bare Integer.  A numeral is a value and returns std::nullopt.
    // Arithmetic premises recursively call stepA, with all three arguments.
    (void)expression; (void)state; (void)arithmetic;
    throw std::runtime_error("TODO Part B: stepA");
}

std::optional<BExpPtr> stepB(const BExpPtr& expression, const State& state,
                             ArithmeticMode arithmetic) {
    // A Bool is a value and returns std::nullopt.  Comparisons step arithmetic
    // operands with stepA; Boolean operands are stepped with stepB.
    (void)expression; (void)state; (void)arithmetic;
    throw std::runtime_error("TODO Part B: stepB");
}

std::optional<Configuration> stepC(const CommandPtr& command, const State& state,
                                   ArithmeticMode arithmetic) {
    // Solution handles an outermost Skip before calling this function.  A Seq
    // whose first command is Skip is not final: it takes S-Seq-Done.  Return
    // std::nullopt only for a non-final command with no rule.  Division by
    // zero and out-of-bounds array access throw Stuck from supplied helpers.
    (void)command; (void)state; (void)arithmetic;
    throw std::runtime_error("TODO Part B: stepC");
}

RunResult run(const CommandPtr& command, const State& state,
              ArithmeticMode arithmetic, long long budget) {
    // Record the initial configuration.  At each iteration test finality,
    // then the budget, then call stepC.  Catch Stuck and also treat a
    // std::nullopt successor as stuck.  Append only real successors.
    (void)command; (void)state; (void)arithmetic; (void)budget;
    throw std::runtime_error("TODO Part B: run");
}

}  // namespace imp
