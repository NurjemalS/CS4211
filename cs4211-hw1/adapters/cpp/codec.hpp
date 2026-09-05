#pragma once

#include "json.hpp"
#include "model.hpp"

namespace imp {

AExpPtr decodeAExp(const cs4211::Json& raw);
BExpPtr decodeBExp(const cs4211::Json& raw);
CommandPtr decodeCommand(const cs4211::Json& raw);
State decodeState(const cs4211::Json& raw);
Request decodeRequest(const cs4211::Json& raw);

cs4211::Json encodeAExp(const AExpPtr& expression);
cs4211::Json encodeBExp(const BExpPtr& expression);
cs4211::Json encodeCommand(const CommandPtr& command);
cs4211::Json encodeState(const State& state);
cs4211::Json encodeDerivation(const Derivation& derivation);
cs4211::Json encodeConfiguration(const Configuration& configuration);
cs4211::Json encodeRunResult(const RunResult& result);
cs4211::Json encodeClassifyResult(const ClassifyResult& result);
cs4211::Json encodeExploreResult(const ExploreResult& result);
std::string configurationKey(const Configuration& configuration);

}  // namespace imp
