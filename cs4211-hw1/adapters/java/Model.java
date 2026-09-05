import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.math.BigInteger;

/**
 * GIVEN typed objects for the IMP abstract syntax, states, and semantic
 * results.  Codec.java converts between these classes and the JSON protocol.
 */
final class Model {
    private Model() {}

    enum ArithmeticMode {
        INTEGER("int"), INT32("int32");
        final String wireName;
        ArithmeticMode(String wireName) { this.wireName = wireName; }
        static ArithmeticMode fromWire(String name) {
            if ("int".equals(name)) return INTEGER;
            if ("int32".equals(name)) return INT32;
            throw new IllegalArgumentException("unknown arithmetic mode " + name);
        }
    }

    enum ArithmeticOperator {
        ADD("+"), SUBTRACT("-"), MULTIPLY("*"), DIVIDE("/");
        final String symbol;
        ArithmeticOperator(String symbol) { this.symbol = symbol; }
        static ArithmeticOperator fromWire(String symbol) {
            for (ArithmeticOperator op : values()) if (op.symbol.equals(symbol)) return op;
            throw new IllegalArgumentException("unknown arithmetic operator " + symbol);
        }
    }

    enum ComparisonOperator {
        EQUAL("="), LESS_OR_EQUAL("<=");
        final String symbol;
        ComparisonOperator(String symbol) { this.symbol = symbol; }
        static ComparisonOperator fromWire(String symbol) {
            for (ComparisonOperator op : values()) if (op.symbol.equals(symbol)) return op;
            throw new IllegalArgumentException("unknown comparison operator " + symbol);
        }
    }

    enum BooleanOperator {
        AND("and"), OR("or");
        final String symbol;
        BooleanOperator(String symbol) { this.symbol = symbol; }
        static BooleanOperator fromWire(String symbol) {
            for (BooleanOperator op : values()) if (op.symbol.equals(symbol)) return op;
            throw new IllegalArgumentException("unknown Boolean operator " + symbol);
        }
    }

    abstract static class AExp {}
    static final class Num extends AExp {
        final BigInteger value;
        Num(BigInteger value) { this.value = value; }
    }
    static final class Var extends AExp {
        final String name;
        Var(String name) { this.name = name; }
    }
    static final class BinaryAExp extends AExp {
        final ArithmeticOperator operator;
        final AExp left;
        final AExp right;
        BinaryAExp(ArithmeticOperator operator, AExp left, AExp right) {
            this.operator = operator; this.left = left; this.right = right;
        }
    }
    static final class ArrayRead extends AExp {
        final String array;
        final AExp index;
        ArrayRead(String array, AExp index) { this.array = array; this.index = index; }
    }

    abstract static class BExp {}
    static final class Bool extends BExp {
        final boolean value;
        Bool(boolean value) { this.value = value; }
    }
    static final class Compare extends BExp {
        final ComparisonOperator operator;
        final AExp left;
        final AExp right;
        Compare(ComparisonOperator operator, AExp left, AExp right) {
            this.operator = operator; this.left = left; this.right = right;
        }
    }
    static final class Not extends BExp {
        final BExp expression;
        Not(BExp expression) { this.expression = expression; }
    }
    static final class BinaryBExp extends BExp {
        final BooleanOperator operator;
        final BExp left;
        final BExp right;
        BinaryBExp(BooleanOperator operator, BExp left, BExp right) {
            this.operator = operator; this.left = left; this.right = right;
        }
    }

    abstract static class Command {}
    static final class Skip extends Command {}
    static final class Assign extends Command {
        final String variable;
        final AExp expression;
        Assign(String variable, AExp expression) {
            this.variable = variable; this.expression = expression;
        }
    }
    static final class SequenceCommand extends Command {
        final Command first;
        final Command second;
        SequenceCommand(Command first, Command second) {
            this.first = first; this.second = second;
        }
    }
    static final class If extends Command {
        final BExp guard;
        final Command thenBranch;
        final Command elseBranch;
        If(BExp guard, Command thenBranch, Command elseBranch) {
            this.guard = guard; this.thenBranch = thenBranch; this.elseBranch = elseBranch;
        }
    }
    static final class While extends Command {
        final BExp guard;
        final Command body;
        While(BExp guard, Command body) { this.guard = guard; this.body = body; }
    }
    static final class ArrayWrite extends Command {
        final String array;
        final AExp index;
        final AExp expression;
        ArrayWrite(String array, AExp index, AExp expression) {
            this.array = array; this.index = index; this.expression = expression;
        }
    }
    static final class Choice extends Command {
        final Command left;
        final Command right;
        Choice(Command left, Command right) { this.left = left; this.right = right; }
    }

    static final class State {
        private final Map<String, BigInteger> variables;
        private final Map<String, List<BigInteger>> arrays;

        State(Map<String, BigInteger> variables, Map<String, List<BigInteger>> arrays) {
            Map<String, BigInteger> canonical = new LinkedHashMap<>();
            for (Map.Entry<String, BigInteger> entry : variables.entrySet())
                if (entry.getValue().signum() != 0) canonical.put(entry.getKey(), entry.getValue());
            Map<String, List<BigInteger>> arrayCopy = new LinkedHashMap<>();
            for (Map.Entry<String, List<BigInteger>> entry : arrays.entrySet())
                arrayCopy.put(entry.getKey(), Collections.unmodifiableList(new ArrayList<>(entry.getValue())));
            this.variables = Collections.unmodifiableMap(canonical);
            this.arrays = Collections.unmodifiableMap(arrayCopy);
        }

        Map<String, BigInteger> variables() { return variables; }
        Map<String, List<BigInteger>> arrays() { return arrays; }

        BigInteger readVariable(String name) { return variables.getOrDefault(name, BigInteger.ZERO); }

        State writeVariable(String name, BigInteger value) {
            Map<String, BigInteger> next = new LinkedHashMap<>(variables);
            if (value.signum() == 0) next.remove(name); else next.put(name, value);
            return new State(next, arrays);
        }

        BigInteger readArray(String name, BigInteger index) {
            List<BigInteger> values = arrays.get(name);
            if (values == null) throw new Malformed("array " + name + " is not provided by the initial state");
            if (index.signum() < 0 || index.compareTo(BigInteger.valueOf(values.size())) >= 0)
                throw new Stuck("index " + index + " out of bounds for " + name);
            return values.get(index.intValueExact());
        }

        State writeArray(String name, BigInteger index, BigInteger value) {
            List<BigInteger> values = arrays.get(name);
            if (values == null) throw new Malformed("array " + name + " is not provided by the initial state");
            if (index.signum() < 0 || index.compareTo(BigInteger.valueOf(values.size())) >= 0)
                throw new Stuck("index " + index + " out of bounds for " + name);
            Map<String, List<BigInteger>> next = new LinkedHashMap<>(arrays);
            List<BigInteger> row = new ArrayList<>(values);
            row.set(index.intValueExact(), value);
            next.put(name, row);
            return new State(variables, next);
        }
    }

    static final class Derivation {
        final String rule;
        final State inputState;
        final List<Derivation> premises;
        final BigInteger integerValue;
        final Boolean booleanValue;
        final State outputState;
        final String subject;

        private Derivation(String rule, State inputState, List<Derivation> premises,
                           BigInteger integerValue, Boolean booleanValue,
                           State outputState, String subject) {
            this.rule = rule;
            this.inputState = inputState;
            this.premises = Collections.unmodifiableList(new ArrayList<>(premises));
            this.integerValue = integerValue;
            this.booleanValue = booleanValue;
            this.outputState = outputState;
            this.subject = subject;
        }

        static Derivation expression(String rule, State state, BigInteger value,
                                     List<Derivation> premises) {
            return new Derivation(rule, state, premises, value, null, null, null);
        }

        static Derivation expression(String rule, State state, boolean value,
                                     List<Derivation> premises) {
            return new Derivation(rule, state, premises, null, value, null, null);
        }

        static Derivation command(String rule, State state, State output,
                                  List<Derivation> premises) {
            return new Derivation(rule, state, premises, null, null, output, null);
        }
    }

    static final class EvalResult<T> {
        final T value;
        final Derivation derivation;
        EvalResult(T value, Derivation derivation) {
            this.value = value; this.derivation = derivation;
        }
    }

    static final class Configuration {
        final Command command;
        final State state;
        Configuration(Command command, State state) {
            this.command = command; this.state = state;
        }
    }

    static final class RunResult {
        final String status;
        final long steps;
        final List<Configuration> configurations;
        final State finalState;
        final String reason;
        RunResult(String status, long steps, List<Configuration> configurations,
                  State finalState, String reason) {
            this.status = status; this.steps = steps;
            this.configurations = Collections.unmodifiableList(new ArrayList<>(configurations));
            this.finalState = finalState; this.reason = reason;
        }
    }

    static final class ClassifyResult {
        final String status;
        final long steps;
        final State finalState;
        final String reason;
        final Long cycleStart;
        final Long cycleLength;
        ClassifyResult(String status, long steps, State finalState, String reason,
                       Long cycleStart, Long cycleLength) {
            this.status = status; this.steps = steps; this.finalState = finalState;
            this.reason = reason; this.cycleStart = cycleStart; this.cycleLength = cycleLength;
        }
    }

    static final class ExploreResult {
        final List<State> finalsFound;
        final boolean stuckFound;
        final boolean truncated;
        ExploreResult(List<State> finalsFound, boolean stuckFound, boolean truncated) {
            this.finalsFound = Collections.unmodifiableList(new ArrayList<>(finalsFound));
            this.stuckFound = stuckFound; this.truncated = truncated;
        }
    }

    static final class Request {
        final String mode;
        final ArithmeticMode arithmetic;
        final Command program;
        final State state;
        final long budget;
        Request(String mode, ArithmeticMode arithmetic, Command program,
                State state, long budget) {
            this.mode = mode; this.arithmetic = arithmetic; this.program = program;
            this.state = state; this.budget = budget;
        }
    }

    static final class Stuck extends RuntimeException {
        private static final long serialVersionUID = 1L;
        Stuck(String message) { super(message); }
    }

    static final class Malformed extends RuntimeException {
        private static final long serialVersionUID = 1L;
        Malformed(String message) { super(message); }
    }
}
