#include "semantics.hpp"

#include "arithmetic.hpp"

namespace imp {

// PART A: Implement the handout's definitive big-step rules in this file.

EvalResult<Integer> bigA(const AExpPtr& expression, const State& state,
                         ArithmeticMode arithmetic) {
    // Implement four typed cases with std::get_if on expression->node:
    //
    // 1. Num: read .value and construct a Num leaf.
    // 2. Var: call state.readVariable(.name) and construct a Var leaf.
    // 3. BinaryAExp: recursively evaluate .left and .right in the same state,
    //    call applyArithmeticOperator, and construct Add/Sub/Mul/Div with the
    //    two derivations as premises in left-to-right order.
    // 4. ArrayRead: evaluate .index, call state.readArray, and construct
    //    Arr-Read with the index derivation as its premise.
    //
    // Use Derivation::expression and return EvalResult<Integer>{...}.
    // Expressions do not update the state.  The handout translates the
    // BinaryAExp rule into its recursive calls, premise order, and result.
    (void)expression; (void)state; (void)arithmetic;
    throw std::runtime_error("TODO Part A: bigA");
}

EvalResult<bool> bigB(const BExpPtr& expression, const State& state,
                      ArithmeticMode arithmetic) {
    // Implement Bool, Compare, Not, and BinaryBExp.  and/or are strict.
    (void)expression; (void)state; (void)arithmetic;
    throw std::runtime_error("TODO Part A: bigB");
}

EvalResult<State> bigC(const CommandPtr& command, const State& state,
                       ArithmeticMode arithmetic) {
    // Implement Skip, Assign, SequenceCommand, If, While, and ArrayWrite.
    (void)command; (void)state; (void)arithmetic;
    throw std::runtime_error("TODO Part A: bigC");
}

}  // namespace imp
