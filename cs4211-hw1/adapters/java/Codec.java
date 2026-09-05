import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.math.BigInteger;

/** GIVEN conversion between Json values and the typed objects in Model.java. */
final class Codec {
    private Codec() {}

    static Model.AExp decodeAExp(Json raw) {
        switch (raw.kind()) {
            case "num": return new Model.Num(raw.at("n").i);
            case "var": return new Model.Var(raw.at("x").s);
            case "aop": return new Model.BinaryAExp(
                    Model.ArithmeticOperator.fromWire(raw.at("op").s),
                    decodeAExp(raw.at("l")), decodeAExp(raw.at("r")));
            case "aget": return new Model.ArrayRead(raw.at("a").s, decodeAExp(raw.at("i")));
            default: throw new IllegalArgumentException("unknown AExp kind " + raw.kind());
        }
    }

    static Model.BExp decodeBExp(Json raw) {
        switch (raw.kind()) {
            case "bool": return new Model.Bool(raw.at("v").b);
            case "cmp": return new Model.Compare(
                    Model.ComparisonOperator.fromWire(raw.at("op").s),
                    decodeAExp(raw.at("l")), decodeAExp(raw.at("r")));
            case "not": return new Model.Not(decodeBExp(raw.at("e")));
            case "bop": return new Model.BinaryBExp(
                    Model.BooleanOperator.fromWire(raw.at("op").s),
                    decodeBExp(raw.at("l")), decodeBExp(raw.at("r")));
            default: throw new IllegalArgumentException("unknown BExp kind " + raw.kind());
        }
    }

    static Model.Command decodeCommand(Json raw) {
        switch (raw.kind()) {
            case "skip": return new Model.Skip();
            case "assign": return new Model.Assign(raw.at("x").s, decodeAExp(raw.at("e")));
            case "seq": return new Model.SequenceCommand(
                    decodeCommand(raw.at("l")), decodeCommand(raw.at("r")));
            case "if": return new Model.If(
                    decodeBExp(raw.at("b")), decodeCommand(raw.at("t")),
                    decodeCommand(raw.at("f")));
            case "while": return new Model.While(
                    decodeBExp(raw.at("b")), decodeCommand(raw.at("c")));
            case "aset": return new Model.ArrayWrite(
                    raw.at("a").s, decodeAExp(raw.at("i")), decodeAExp(raw.at("e")));
            case "choice": return new Model.Choice(
                    decodeCommand(raw.at("l")), decodeCommand(raw.at("r")));
            default: throw new IllegalArgumentException("unknown command kind " + raw.kind());
        }
    }

    static Model.State decodeState(Json raw) {
        Map<String, BigInteger> variables = new LinkedHashMap<>();
        Map<String, List<BigInteger>> arrays = new LinkedHashMap<>();
        if (raw.has("vars"))
            for (Map.Entry<String, Json> entry : raw.at("vars").obj.entrySet())
                variables.put(entry.getKey(), entry.getValue().i);
        if (raw.has("arrays"))
            for (Map.Entry<String, Json> entry : raw.at("arrays").obj.entrySet()) {
                List<BigInteger> row = new ArrayList<>();
                for (Json value : entry.getValue().arr) row.add(value.i);
                arrays.put(entry.getKey(), row);
            }
        return new Model.State(variables, arrays);
    }

    static Model.Request decodeRequest(Json raw) {
        String arithmetic = raw.has("arith") ? raw.at("arith").s : "int";
        long budget = raw.has("budget") ? raw.at("budget").i.longValueExact() : 10000L;
        return new Model.Request(
                raw.at("mode").s,
                Model.ArithmeticMode.fromWire(arithmetic),
                decodeCommand(raw.at("program")),
                decodeState(raw.at("state")),
                budget);
    }

    static Json encodeAExp(Model.AExp expression) {
        if (expression instanceof Model.Num) {
            return Json.object().put("k", "num").put("n", ((Model.Num) expression).value);
        }
        if (expression instanceof Model.Var) {
            return Json.object().put("k", "var").put("x", ((Model.Var) expression).name);
        }
        if (expression instanceof Model.BinaryAExp) {
            Model.BinaryAExp binary = (Model.BinaryAExp) expression;
            return Json.object().put("k", "aop").put("op", binary.operator.symbol)
                    .put("l", encodeAExp(binary.left)).put("r", encodeAExp(binary.right));
        }
        if (expression instanceof Model.ArrayRead) {
            Model.ArrayRead read = (Model.ArrayRead) expression;
            return Json.object().put("k", "aget").put("a", read.array)
                    .put("i", encodeAExp(read.index));
        }
        throw new IllegalArgumentException("cannot encode AExp " + expression);
    }

    static Json encodeBExp(Model.BExp expression) {
        if (expression instanceof Model.Bool) {
            return Json.object().put("k", "bool").put("v", ((Model.Bool) expression).value);
        }
        if (expression instanceof Model.Compare) {
            Model.Compare compare = (Model.Compare) expression;
            return Json.object().put("k", "cmp").put("op", compare.operator.symbol)
                    .put("l", encodeAExp(compare.left)).put("r", encodeAExp(compare.right));
        }
        if (expression instanceof Model.Not) {
            return Json.object().put("k", "not")
                    .put("e", encodeBExp(((Model.Not) expression).expression));
        }
        if (expression instanceof Model.BinaryBExp) {
            Model.BinaryBExp binary = (Model.BinaryBExp) expression;
            return Json.object().put("k", "bop").put("op", binary.operator.symbol)
                    .put("l", encodeBExp(binary.left)).put("r", encodeBExp(binary.right));
        }
        throw new IllegalArgumentException("cannot encode BExp " + expression);
    }

    static Json encodeCommand(Model.Command command) {
        if (command instanceof Model.Skip) return Json.object().put("k", "skip");
        if (command instanceof Model.Assign) {
            Model.Assign assign = (Model.Assign) command;
            return Json.object().put("k", "assign").put("x", assign.variable)
                    .put("e", encodeAExp(assign.expression));
        }
        if (command instanceof Model.SequenceCommand) {
            Model.SequenceCommand sequence = (Model.SequenceCommand) command;
            return Json.object().put("k", "seq").put("l", encodeCommand(sequence.first))
                    .put("r", encodeCommand(sequence.second));
        }
        if (command instanceof Model.If) {
            Model.If branch = (Model.If) command;
            return Json.object().put("k", "if").put("b", encodeBExp(branch.guard))
                    .put("t", encodeCommand(branch.thenBranch))
                    .put("f", encodeCommand(branch.elseBranch));
        }
        if (command instanceof Model.While) {
            Model.While loop = (Model.While) command;
            return Json.object().put("k", "while").put("b", encodeBExp(loop.guard))
                    .put("c", encodeCommand(loop.body));
        }
        if (command instanceof Model.ArrayWrite) {
            Model.ArrayWrite write = (Model.ArrayWrite) command;
            return Json.object().put("k", "aset").put("a", write.array)
                    .put("i", encodeAExp(write.index)).put("e", encodeAExp(write.expression));
        }
        if (command instanceof Model.Choice) {
            Model.Choice choice = (Model.Choice) command;
            return Json.object().put("k", "choice").put("l", encodeCommand(choice.left))
                    .put("r", encodeCommand(choice.right));
        }
        throw new IllegalArgumentException("cannot encode command " + command);
    }

    static Json encodeState(Model.State state) {
        Json variables = Json.object();
        Json arrays = Json.object();
        for (Map.Entry<String, BigInteger> entry : state.variables().entrySet())
            variables.obj.put(entry.getKey(), Json.of(entry.getValue()));
        for (Map.Entry<String, List<BigInteger>> entry : state.arrays().entrySet()) {
            Json row = Json.array();
            for (BigInteger value : entry.getValue()) row.arr.add(Json.of(value));
            arrays.obj.put(entry.getKey(), row);
        }
        return Json.object().put("vars", variables).put("arrays", arrays);
    }

    static Json encodeDerivation(Model.Derivation derivation) {
        Json premises = Json.array();
        for (Model.Derivation premise : derivation.premises)
            premises.arr.add(encodeDerivation(premise));
        Json result = Json.object().put("rule", derivation.rule)
                .put("in", encodeState(derivation.inputState)).put("prem", premises);
        if (derivation.booleanValue != null)
            result.put("val", derivation.booleanValue.booleanValue());
        else if (derivation.integerValue != null)
            result.put("val", derivation.integerValue);
        if (derivation.outputState != null) result.put("out", encodeState(derivation.outputState));
        if (derivation.subject != null) result.put("subj", derivation.subject);
        return result;
    }

    static Json encodeConfiguration(Model.Configuration configuration) {
        return Json.object().put("c", encodeCommand(configuration.command))
                .put("s", encodeState(configuration.state));
    }

    static Json encodeRunResult(Model.RunResult result) {
        Json configurations = Json.array();
        for (Model.Configuration configuration : result.configurations)
            configurations.arr.add(encodeConfiguration(configuration));
        Json output = Json.object().put("status", result.status)
                .put("steps", result.steps).put("configs", configurations);
        if (result.finalState != null) output.put("final", encodeState(result.finalState));
        if (result.reason != null) output.put("reason", result.reason);
        return output;
    }

    static Json encodeClassifyResult(Model.ClassifyResult result) {
        Json output = Json.object().put("status", result.status).put("steps", result.steps);
        if (result.finalState != null) output.put("final", encodeState(result.finalState));
        if (result.reason != null) output.put("reason", result.reason);
        if (result.cycleStart != null) output.put("cycle_start", result.cycleStart.longValue());
        if (result.cycleLength != null) output.put("cycle_length", result.cycleLength.longValue());
        return output;
    }

    static Json encodeExploreResult(Model.ExploreResult result) {
        Json finals = Json.array();
        for (Model.State state : result.finalsFound) finals.arr.add(encodeState(state));
        return Json.object().put("status", "ok").put("finals_found", finals)
                .put("stuck_found", result.stuckFound).put("truncated", result.truncated);
    }

    static String configurationKey(Model.Configuration configuration) {
        return encodeConfiguration(configuration).dump();
    }
}
