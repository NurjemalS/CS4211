// GIVEN process driver.  Run this program; implement the semantics in
// big_step.cpp, small_step.cpp, and analysis.cpp.

#include "codec.hpp"
#include "semantics.hpp"

#include <iostream>

using cs4211::Json;

namespace {

Json handle(const Json& rawRequest) {
    const imp::Request request = imp::decodeRequest(rawRequest);
    Json response = Json::object();
    try {
        if (request.mode == "bigstep") {
            const auto result = imp::bigC(request.program, request.state, request.arithmetic);
            response.obj["status"] = Json::str("ok");
            response.obj["final"] = imp::encodeState(result.value);
            response.obj["derivation"] = imp::encodeDerivation(result.derivation);
            return response;
        }
        if (request.mode == "step") {
            if (imp::isFinal(request.program)) {
                response.obj["status"] = Json::str("final");
                return response;
            }
            const auto next = imp::stepC(request.program, request.state, request.arithmetic);
            if (!next) {
                response.obj["status"] = Json::str("stuck");
                response.obj["reason"] = Json::str("no rule applies");
                return response;
            }
            response.obj["status"] = Json::str("ok");
            response.obj["next"] = imp::encodeConfiguration(*next);
            return response;
        }
        if (request.mode == "run")
            return imp::encodeRunResult(imp::run(
                request.program, request.state, request.arithmetic, request.budget));
        if (request.mode == "classify")
            return imp::encodeClassifyResult(imp::classify(
                request.program, request.state, request.arithmetic, request.budget));
        if (request.mode == "explore")
            return imp::encodeExploreResult(imp::explore(
                request.program, request.state, request.arithmetic, request.budget));
    } catch (const imp::Stuck& error) {
        response.obj["status"] = Json::str("stuck");
        response.obj["reason"] = Json::str(error.what());
        return response;
    } catch (const imp::Malformed& error) {
        response.obj["status"] = Json::str("malformed");
        Json reasons = Json::array();
        reasons.arr.push_back(Json::str(error.what()));
        response.obj["reasons"] = std::move(reasons);
        return response;
    }
    response.obj["status"] = Json::str("error");
    response.obj["reason"] = Json::str("unknown mode " + request.mode);
    return response;
}

}  // namespace

int main() {
    std::ios::sync_with_stdio(false);
    const Json request = cs4211::readStdin();
    std::cout << handle(request).dump() << '\n';
    return 0;
}
