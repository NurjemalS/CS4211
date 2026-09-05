#pragma once

// GIVEN typed objects for the IMP abstract syntax, states, and semantic
// results.  codec.cpp converts between these objects and the JSON protocol.

#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <variant>
#include <vector>
#include "integer.hpp"

namespace imp {

using Integer = cs4211::BigInteger;

struct Stuck : std::runtime_error {
    explicit Stuck(const std::string& message) : std::runtime_error(message) {}
};

struct Malformed : std::runtime_error {
    explicit Malformed(const std::string& message) : std::runtime_error(message) {}
};

enum class ArithmeticMode { Integer, Int32 };
enum class ArithmeticOperator { Add, Subtract, Multiply, Divide };
enum class ComparisonOperator { Equal, LessOrEqual };
enum class BooleanOperator { And, Or };

struct AExp;
struct BExp;
struct Command;
using AExpPtr = std::shared_ptr<const AExp>;
using BExpPtr = std::shared_ptr<const BExp>;
using CommandPtr = std::shared_ptr<const Command>;

struct Num { Integer value; };
struct Var { std::string name; };
struct BinaryAExp {
    ArithmeticOperator op;
    AExpPtr left;
    AExpPtr right;
};
struct ArrayRead { std::string array; AExpPtr index; };

struct AExp {
    using Node = std::variant<Num, Var, BinaryAExp, ArrayRead>;
    Node node;
    explicit AExp(Node node_) : node(std::move(node_)) {}
};

struct Bool { bool value; };
struct Compare {
    ComparisonOperator op;
    AExpPtr left;
    AExpPtr right;
};
struct Not { BExpPtr expression; };
struct BinaryBExp {
    BooleanOperator op;
    BExpPtr left;
    BExpPtr right;
};

struct BExp {
    using Node = std::variant<Bool, Compare, Not, BinaryBExp>;
    Node node;
    explicit BExp(Node node_) : node(std::move(node_)) {}
};

struct Skip {};
struct Assign { std::string variable; AExpPtr expression; };
struct SequenceCommand { CommandPtr first; CommandPtr second; };
struct If { BExpPtr guard; CommandPtr thenBranch; CommandPtr elseBranch; };
struct While { BExpPtr guard; CommandPtr body; };
struct ArrayWrite { std::string array; AExpPtr index; AExpPtr expression; };
struct Choice { CommandPtr left; CommandPtr right; };

struct Command {
    using Node = std::variant<Skip, Assign, SequenceCommand, If, While, ArrayWrite, Choice>;
    Node node;
    explicit Command(Node node_) : node(std::move(node_)) {}
};

struct State {
    std::map<std::string, Integer> variables;
    std::map<std::string, std::vector<Integer>> arrays;

    State canonical() const;
    Integer readVariable(const std::string& name) const;
    State writeVariable(const std::string& name, const Integer& value) const;
    Integer readArray(const std::string& name, const Integer& index) const;
    State writeArray(const std::string& name, const Integer& index,
                     const Integer& value) const;
};

using DerivationValue = std::variant<Integer, bool>;

struct Derivation {
    std::string rule;
    State inputState;
    std::vector<Derivation> premises;
    std::optional<DerivationValue> value;
    std::optional<State> outputState;
    std::optional<std::string> subject;

    static Derivation expression(const std::string& rule, const State& state,
                                 DerivationValue value,
                                 std::vector<Derivation> premises = {});
    static Derivation command(const std::string& rule, const State& state,
                              const State& output,
                              std::vector<Derivation> premises = {});
};

template <typename T>
struct EvalResult {
    T value;
    Derivation derivation;
};

struct Configuration { CommandPtr command; State state; };

struct RunResult {
    std::string status;
    long long steps;
    std::vector<Configuration> configurations;
    std::optional<State> finalState;
    std::optional<std::string> reason;
};

struct ClassifyResult {
    std::string status;
    long long steps;
    std::optional<State> finalState;
    std::optional<std::string> reason;
    std::optional<long long> cycleStart;
    std::optional<long long> cycleLength;
};

struct ExploreResult {
    std::vector<State> finalsFound;
    bool stuckFound;
    bool truncated;
};

struct Request {
    std::string mode;
    ArithmeticMode arithmetic;
    CommandPtr program;
    State state;
    long long budget;
};

inline bool isFinal(const CommandPtr& command) {
    return std::holds_alternative<Skip>(command->node);
}

}  // namespace imp
