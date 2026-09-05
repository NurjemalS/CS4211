#pragma once

#include "model.hpp"

namespace imp {

// PART A
EvalResult<Integer> bigA(const AExpPtr& expression, const State& state,
                         ArithmeticMode arithmetic);
EvalResult<bool> bigB(const BExpPtr& expression, const State& state,
                      ArithmeticMode arithmetic);
EvalResult<State> bigC(const CommandPtr& command, const State& state,
                       ArithmeticMode arithmetic);

// PART B
std::optional<AExpPtr> stepA(const AExpPtr& expression, const State& state,
                             ArithmeticMode arithmetic);
std::optional<BExpPtr> stepB(const BExpPtr& expression, const State& state,
                             ArithmeticMode arithmetic);
std::optional<Configuration> stepC(const CommandPtr& command, const State& state,
                                   ArithmeticMode arithmetic);
RunResult run(const CommandPtr& command, const State& state,
              ArithmeticMode arithmetic, long long budget);

// PART C and BONUS
ClassifyResult classify(const CommandPtr& command, const State& state,
                        ArithmeticMode arithmetic, long long budget);
std::vector<Configuration> stepAll(const CommandPtr& command, const State& state,
                                   ArithmeticMode arithmetic);
ExploreResult explore(const CommandPtr& command, const State& state,
                      ArithmeticMode arithmetic, long long budget);

}  // namespace imp
