/** PART B: implement the handout's definitive one-step rules and runs here. */
final class SmallStep {
    private SmallStep() {}

    /** One arithmetic step, or null when expression is already Model.Num.
     *  Return another AExp object, such as new Model.Num(value), rather than
     *  a bare BigInteger.  Arithmetic premises recursively call stepA. */
    static Model.AExp stepA(Model.AExp expression, Model.State state,
                            Model.ArithmeticMode arithmetic) {
        throw new UnsupportedOperationException("TODO Part B: stepA");
    }

    /** One Boolean step, or null when expression is already Model.Bool.
     *  Comparisons use stepA; Boolean operands use stepB. */
    static Model.BExp stepB(Model.BExp expression, Model.State state,
                            Model.ArithmeticMode arithmetic) {
        throw new UnsupportedOperationException("TODO Part B: stepB");
    }

    /** One step from a non-final command.  Solution checks an outermost Skip
     *  before calling this method.  A Seq whose first command is Skip is not
     *  final: it takes S-Seq-Done.  Return null only for a non-final command
     *  with no rule; helpers throw Model.Stuck for division by zero or an
     *  out-of-bounds array access. */
    static Model.Configuration stepC(Model.Command command, Model.State state,
                                     Model.ArithmeticMode arithmetic) {
        throw new UnsupportedOperationException("TODO Part B: stepC");
    }

    /** Record the initial configuration, then repeatedly call stepC.  At each
     *  iteration test finality, then the budget, then attempt a step.  Catch
     *  Model.Stuck and also treat a null successor as stuck. */
    static Model.RunResult run(Model.Command command, Model.State state,
                               Model.ArithmeticMode arithmetic, long budget) {
        throw new UnsupportedOperationException("TODO Part B: run");
    }
}
