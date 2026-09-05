#include "codec.hpp"

#include <type_traits>

using cs4211::Json;

namespace imp {
namespace {

ArithmeticOperator decodeArithmeticOperator(const std::string& symbol) {
    if (symbol == "+") return ArithmeticOperator::Add;
    if (symbol == "-") return ArithmeticOperator::Subtract;
    if (symbol == "*") return ArithmeticOperator::Multiply;
    if (symbol == "/") return ArithmeticOperator::Divide;
    throw std::invalid_argument("unknown arithmetic operator " + symbol);
}

ComparisonOperator decodeComparisonOperator(const std::string& symbol) {
    if (symbol == "=") return ComparisonOperator::Equal;
    if (symbol == "<=") return ComparisonOperator::LessOrEqual;
    throw std::invalid_argument("unknown comparison operator " + symbol);
}

BooleanOperator decodeBooleanOperator(const std::string& symbol) {
    if (symbol == "and") return BooleanOperator::And;
    if (symbol == "or") return BooleanOperator::Or;
    throw std::invalid_argument("unknown Boolean operator " + symbol);
}

std::string encodeArithmeticOperator(ArithmeticOperator op) {
    switch (op) {
        case ArithmeticOperator::Add: return "+";
        case ArithmeticOperator::Subtract: return "-";
        case ArithmeticOperator::Multiply: return "*";
        case ArithmeticOperator::Divide: return "/";
    }
    throw std::logic_error("unreachable arithmetic operator");
}

std::string encodeComparisonOperator(ComparisonOperator op) {
    return op == ComparisonOperator::Equal ? "=" : "<=";
}

std::string encodeBooleanOperator(BooleanOperator op) {
    return op == BooleanOperator::And ? "and" : "or";
}

Json objectWithKind(const std::string& kind) {
    Json result = Json::object();
    result.obj["k"] = Json::str(kind);
    return result;
}

}  // namespace

AExpPtr decodeAExp(const Json& raw) {
    const std::string kind = raw.kind();
    if (kind == "num") return std::make_shared<AExp>(Num{raw.at("n").i});
    if (kind == "var") return std::make_shared<AExp>(Var{raw.at("x").s});
    if (kind == "aop") {
        return std::make_shared<AExp>(BinaryAExp{
            decodeArithmeticOperator(raw.at("op").s),
            decodeAExp(raw.at("l")), decodeAExp(raw.at("r"))});
    }
    if (kind == "aget") {
        return std::make_shared<AExp>(ArrayRead{raw.at("a").s, decodeAExp(raw.at("i"))});
    }
    throw std::invalid_argument("unknown AExp kind " + kind);
}

BExpPtr decodeBExp(const Json& raw) {
    const std::string kind = raw.kind();
    if (kind == "bool") return std::make_shared<BExp>(Bool{raw.at("v").b});
    if (kind == "cmp") {
        return std::make_shared<BExp>(Compare{
            decodeComparisonOperator(raw.at("op").s),
            decodeAExp(raw.at("l")), decodeAExp(raw.at("r"))});
    }
    if (kind == "not") return std::make_shared<BExp>(Not{decodeBExp(raw.at("e"))});
    if (kind == "bop") {
        return std::make_shared<BExp>(BinaryBExp{
            decodeBooleanOperator(raw.at("op").s),
            decodeBExp(raw.at("l")), decodeBExp(raw.at("r"))});
    }
    throw std::invalid_argument("unknown BExp kind " + kind);
}

CommandPtr decodeCommand(const Json& raw) {
    const std::string kind = raw.kind();
    if (kind == "skip") return std::make_shared<Command>(Skip{});
    if (kind == "assign") {
        return std::make_shared<Command>(Assign{raw.at("x").s, decodeAExp(raw.at("e"))});
    }
    if (kind == "seq") {
        return std::make_shared<Command>(SequenceCommand{
            decodeCommand(raw.at("l")), decodeCommand(raw.at("r"))});
    }
    if (kind == "if") {
        return std::make_shared<Command>(If{
            decodeBExp(raw.at("b")), decodeCommand(raw.at("t")),
            decodeCommand(raw.at("f"))});
    }
    if (kind == "while") {
        return std::make_shared<Command>(While{
            decodeBExp(raw.at("b")), decodeCommand(raw.at("c"))});
    }
    if (kind == "aset") {
        return std::make_shared<Command>(ArrayWrite{
            raw.at("a").s, decodeAExp(raw.at("i")), decodeAExp(raw.at("e"))});
    }
    if (kind == "choice") {
        return std::make_shared<Command>(Choice{
            decodeCommand(raw.at("l")), decodeCommand(raw.at("r"))});
    }
    throw std::invalid_argument("unknown command kind " + kind);
}

State decodeState(const Json& raw) {
    State state;
    if (raw.has("vars")) {
        for (const auto& entry : raw.at("vars").obj)
            state.variables[entry.first] = entry.second.i;
    }
    if (raw.has("arrays")) {
        for (const auto& entry : raw.at("arrays").obj) {
            std::vector<Integer> row;
            for (const Json& value : entry.second.arr) row.push_back(value.i);
            state.arrays[entry.first] = std::move(row);
        }
    }
    return state.canonical();
}

Request decodeRequest(const Json& raw) {
    ArithmeticMode arithmetic = ArithmeticMode::Integer;
    if (raw.has("arith") && raw.at("arith").s == "int32")
        arithmetic = ArithmeticMode::Int32;
    return Request{raw.at("mode").s, arithmetic, decodeCommand(raw.at("program")),
                   decodeState(raw.at("state")),
                   raw.has("budget") ? raw.at("budget").i.toLongLong() : 10000};
}

Json encodeAExp(const AExpPtr& expression) {
    return std::visit([&](const auto& node) -> Json {
        using T = std::decay_t<decltype(node)>;
        if constexpr (std::is_same_v<T, Num>) {
            Json result = objectWithKind("num");
            result.obj["n"] = Json::integer(node.value);
            return result;
        } else if constexpr (std::is_same_v<T, Var>) {
            Json result = objectWithKind("var");
            result.obj["x"] = Json::str(node.name);
            return result;
        } else if constexpr (std::is_same_v<T, BinaryAExp>) {
            Json result = objectWithKind("aop");
            result.obj["op"] = Json::str(encodeArithmeticOperator(node.op));
            result.obj["l"] = encodeAExp(node.left);
            result.obj["r"] = encodeAExp(node.right);
            return result;
        } else {
            Json result = objectWithKind("aget");
            result.obj["a"] = Json::str(node.array);
            result.obj["i"] = encodeAExp(node.index);
            return result;
        }
    }, expression->node);
}

Json encodeBExp(const BExpPtr& expression) {
    return std::visit([&](const auto& node) -> Json {
        using T = std::decay_t<decltype(node)>;
        if constexpr (std::is_same_v<T, Bool>) {
            Json result = objectWithKind("bool");
            result.obj["v"] = Json::boolean(node.value);
            return result;
        } else if constexpr (std::is_same_v<T, Compare>) {
            Json result = objectWithKind("cmp");
            result.obj["op"] = Json::str(encodeComparisonOperator(node.op));
            result.obj["l"] = encodeAExp(node.left);
            result.obj["r"] = encodeAExp(node.right);
            return result;
        } else if constexpr (std::is_same_v<T, Not>) {
            Json result = objectWithKind("not");
            result.obj["e"] = encodeBExp(node.expression);
            return result;
        } else {
            Json result = objectWithKind("bop");
            result.obj["op"] = Json::str(encodeBooleanOperator(node.op));
            result.obj["l"] = encodeBExp(node.left);
            result.obj["r"] = encodeBExp(node.right);
            return result;
        }
    }, expression->node);
}

Json encodeCommand(const CommandPtr& command) {
    return std::visit([&](const auto& node) -> Json {
        using T = std::decay_t<decltype(node)>;
        if constexpr (std::is_same_v<T, Skip>) {
            return objectWithKind("skip");
        } else if constexpr (std::is_same_v<T, Assign>) {
            Json result = objectWithKind("assign");
            result.obj["x"] = Json::str(node.variable);
            result.obj["e"] = encodeAExp(node.expression);
            return result;
        } else if constexpr (std::is_same_v<T, SequenceCommand>) {
            Json result = objectWithKind("seq");
            result.obj["l"] = encodeCommand(node.first);
            result.obj["r"] = encodeCommand(node.second);
            return result;
        } else if constexpr (std::is_same_v<T, If>) {
            Json result = objectWithKind("if");
            result.obj["b"] = encodeBExp(node.guard);
            result.obj["t"] = encodeCommand(node.thenBranch);
            result.obj["f"] = encodeCommand(node.elseBranch);
            return result;
        } else if constexpr (std::is_same_v<T, While>) {
            Json result = objectWithKind("while");
            result.obj["b"] = encodeBExp(node.guard);
            result.obj["c"] = encodeCommand(node.body);
            return result;
        } else if constexpr (std::is_same_v<T, ArrayWrite>) {
            Json result = objectWithKind("aset");
            result.obj["a"] = Json::str(node.array);
            result.obj["i"] = encodeAExp(node.index);
            result.obj["e"] = encodeAExp(node.expression);
            return result;
        } else {
            Json result = objectWithKind("choice");
            result.obj["l"] = encodeCommand(node.left);
            result.obj["r"] = encodeCommand(node.right);
            return result;
        }
    }, command->node);
}

Json encodeState(const State& state) {
    Json variables = Json::object();
    Json arrays = Json::object();
    for (const auto& entry : state.variables)
        variables.obj[entry.first] = Json::integer(entry.second);
    for (const auto& entry : state.arrays) {
        Json row = Json::array();
        for (const Integer& value : entry.second) row.arr.push_back(Json::integer(value));
        arrays.obj[entry.first] = std::move(row);
    }
    Json result = Json::object();
    result.obj["vars"] = std::move(variables);
    result.obj["arrays"] = std::move(arrays);
    return result;
}

Json encodeDerivation(const Derivation& derivation) {
    Json result = Json::object();
    result.obj["rule"] = Json::str(derivation.rule);
    result.obj["in"] = encodeState(derivation.inputState);
    Json premises = Json::array();
    for (const Derivation& premise : derivation.premises)
        premises.arr.push_back(encodeDerivation(premise));
    result.obj["prem"] = std::move(premises);
    if (derivation.value) {
        std::visit([&](const auto& value) {
            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, bool>)
                result.obj["val"] = Json::boolean(value);
            else
                result.obj["val"] = Json::integer(value);
        }, *derivation.value);
    }
    if (derivation.outputState) result.obj["out"] = encodeState(*derivation.outputState);
    if (derivation.subject) result.obj["subj"] = Json::str(*derivation.subject);
    return result;
}

Json encodeConfiguration(const Configuration& configuration) {
    Json result = Json::object();
    result.obj["c"] = encodeCommand(configuration.command);
    result.obj["s"] = encodeState(configuration.state);
    return result;
}

Json encodeRunResult(const RunResult& result) {
    Json output = Json::object();
    output.obj["status"] = Json::str(result.status);
    output.obj["steps"] = Json::integer(result.steps);
    Json configurations = Json::array();
    for (const Configuration& configuration : result.configurations)
        configurations.arr.push_back(encodeConfiguration(configuration));
    output.obj["configs"] = std::move(configurations);
    if (result.finalState) output.obj["final"] = encodeState(*result.finalState);
    if (result.reason) output.obj["reason"] = Json::str(*result.reason);
    return output;
}

Json encodeClassifyResult(const ClassifyResult& result) {
    Json output = Json::object();
    output.obj["status"] = Json::str(result.status);
    output.obj["steps"] = Json::integer(result.steps);
    if (result.finalState) output.obj["final"] = encodeState(*result.finalState);
    if (result.reason) output.obj["reason"] = Json::str(*result.reason);
    if (result.cycleStart) output.obj["cycle_start"] = Json::integer(*result.cycleStart);
    if (result.cycleLength) output.obj["cycle_length"] = Json::integer(*result.cycleLength);
    return output;
}

Json encodeExploreResult(const ExploreResult& result) {
    Json output = Json::object();
    output.obj["status"] = Json::str("ok");
    Json finals = Json::array();
    for (const State& state : result.finalsFound) finals.arr.push_back(encodeState(state));
    output.obj["finals_found"] = std::move(finals);
    output.obj["stuck_found"] = Json::boolean(result.stuckFound);
    output.obj["truncated"] = Json::boolean(result.truncated);
    return output;
}

std::string configurationKey(const Configuration& configuration) {
    return encodeConfiguration(configuration).dump();
}

}  // namespace imp
