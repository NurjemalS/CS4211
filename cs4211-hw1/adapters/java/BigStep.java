import java.math.BigInteger;

/** PART A: implement the handout's definitive big-step rules here. */
final class BigStep {
    private BigStep() {}

    /**
     * Evaluate an arithmetic expression and return its value together with
     * its derivation.
     *
     * Implement the cases by testing the concrete AST class with instanceof:
     *
     *  1. Model.Num: read .value and construct a Num leaf.
     *  2. Model.Var: call state.readVariable(.name) and construct a Var leaf.
     *  3. Model.BinaryAExp: recursively evaluate .left and .right in the same
     *     state, call Arithmetic.apply, and construct Add/Sub/Mul/Div with the
     *     two derivations as premises in left-to-right order.
     *  4. Model.ArrayRead: evaluate .index, call state.readArray, and construct
     *     Arr-Read with the index derivation as its premise.
     *
     * Use Model.Derivation.expression and return new Model.EvalResult<>(...).
     * Expressions do not update the state.
     */
    static Model.EvalResult<BigInteger> bigA(
            Model.AExp expression,
            Model.State state,
            Model.ArithmeticMode arithmetic) {
        throw new UnsupportedOperationException("TODO Part A: bigA");
    }

    /** Evaluate Bool, Compare, Not, and BinaryBExp.  and/or are strict. */
    static Model.EvalResult<Boolean> bigB(
            Model.BExp expression,
            Model.State state,
            Model.ArithmeticMode arithmetic) {
        throw new UnsupportedOperationException("TODO Part A: bigB");
    }

    /** Execute Skip, Assign, SequenceCommand, If, While, and ArrayWrite. */
    static Model.EvalResult<Model.State> bigC(
            Model.Command command,
            Model.State state,
            Model.ArithmeticMode arithmetic) {
        throw new UnsupportedOperationException("TODO Part A: bigC");
    }
}
