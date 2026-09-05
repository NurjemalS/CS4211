/**
 * GIVEN process driver.  Run this class; implement the semantic functions in
 * BigStep.java, SmallStep.java, and Analysis.java.
 */
public final class Solution {
    private Solution() {}

    static Json handle(Json rawRequest) {
        Model.Request request = Codec.decodeRequest(rawRequest);
        try {
            switch (request.mode) {
                case "bigstep": {
                    Model.EvalResult<Model.State> result =
                            BigStep.bigC(request.program, request.state, request.arithmetic);
                    return Json.object().put("status", "ok")
                            .put("final", Codec.encodeState(result.value))
                            .put("derivation", Codec.encodeDerivation(result.derivation));
                }
                case "step": {
                    if (request.program instanceof Model.Skip)
                        return Json.object().put("status", "final");
                    Model.Configuration next = SmallStep.stepC(
                            request.program, request.state, request.arithmetic);
                    if (next == null)
                        return Json.object().put("status", "stuck")
                                .put("reason", "no rule applies");
                    return Json.object().put("status", "ok")
                            .put("next", Codec.encodeConfiguration(next));
                }
                case "run":
                    return Codec.encodeRunResult(SmallStep.run(
                            request.program, request.state, request.arithmetic, request.budget));
                case "classify":
                    return Codec.encodeClassifyResult(Analysis.classify(
                            request.program, request.state, request.arithmetic, request.budget));
                case "explore":
                    return Codec.encodeExploreResult(Analysis.explore(
                            request.program, request.state, request.arithmetic, request.budget));
                default:
                    return Json.object().put("status", "error")
                            .put("reason", "unknown mode " + request.mode);
            }
        } catch (Model.Stuck error) {
            return Json.object().put("status", "stuck").put("reason", error.getMessage());
        } catch (Model.Malformed error) {
            return Json.object().put("status", "malformed")
                    .put("reasons", Json.array().push(Json.of(error.getMessage())));
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println(handle(Json.readStdin()).dump());
    }
}
