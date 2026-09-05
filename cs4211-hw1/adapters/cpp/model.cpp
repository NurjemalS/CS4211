#include "model.hpp"

namespace imp {

State State::canonical() const {
    State result = *this;
    for (auto it = result.variables.begin(); it != result.variables.end();) {
        if (it->second == 0) it = result.variables.erase(it); else ++it;
    }
    return result;
}

Integer State::readVariable(const std::string& name) const {
    const auto found = variables.find(name);
    return found == variables.end() ? 0 : found->second;
}

State State::writeVariable(const std::string& name, const Integer& value) const {
    State result = *this;
    if (value == 0) result.variables.erase(name); else result.variables[name] = value;
    return result;
}

Integer State::readArray(const std::string& name, const Integer& index) const {
    const auto found = arrays.find(name);
    if (found == arrays.end())
        throw Malformed("array " + name + " is not provided by the initial state");
    if (index < 0 || index >= Integer(std::to_string(found->second.size())))
        throw Stuck("index " + index.str() + " out of bounds for " + name);
    return found->second.at(index.toSizeT());
}

State State::writeArray(const std::string& name, const Integer& index,
                        const Integer& value) const {
    State result = *this;
    const auto found = result.arrays.find(name);
    if (found == result.arrays.end())
        throw Malformed("array " + name + " is not provided by the initial state");
    if (index < 0 || index >= Integer(std::to_string(found->second.size())))
        throw Stuck("index " + index.str() + " out of bounds for " + name);
    found->second.at(index.toSizeT()) = value;
    return result;
}

Derivation Derivation::expression(const std::string& rule, const State& state,
                                  DerivationValue value,
                                  std::vector<Derivation> premises) {
    return Derivation{rule, state, std::move(premises), std::move(value),
                      std::nullopt, std::nullopt};
}

Derivation Derivation::command(const std::string& rule, const State& state,
                               const State& output,
                               std::vector<Derivation> premises) {
    return Derivation{rule, state, std::move(premises), std::nullopt,
                      output, std::nullopt};
}

}  // namespace imp
