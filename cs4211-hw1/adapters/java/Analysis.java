import java.util.List;

/** PART C and BONUS: repeated configurations and nondeterministic search. */
final class Analysis {
    private Analysis() {}

    /** Use Codec.configurationKey to compare configurations by value.
     *  At each iteration check, in order: Skip, a repeated configuration,
     *  and the budget. Then record the configuration and call
     *  SmallStep.stepC. Catch Model.Stuck and treat a null successor as
     *  stuck; a failed attempt does not increment the step count. */
    static Model.ClassifyResult classify(Model.Command command, Model.State state,
                                         Model.ArithmeticMode arithmetic, long budget) {
        throw new UnsupportedOperationException("TODO Part C: classify");
    }

    static List<Model.Configuration> stepAll(Model.Command command, Model.State state,
                                             Model.ArithmeticMode arithmetic) {
        throw new UnsupportedOperationException("TODO bonus: stepAll");
    }

    static Model.ExploreResult explore(Model.Command command, Model.State state,
                                       Model.ArithmeticMode arithmetic, long budget) {
        throw new UnsupportedOperationException("TODO bonus: explore");
    }
}
