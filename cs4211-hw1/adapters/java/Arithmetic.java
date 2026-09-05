import java.math.BigInteger;

/** GIVEN arbitrary-precision arithmetic operations for the two modes. */
final class Arithmetic {
    private Arithmetic() {}

    private static final BigInteger TWO_31 = BigInteger.ONE.shiftLeft(31);
    private static final BigInteger TWO_32 = BigInteger.ONE.shiftLeft(32);

    static BigInteger wrapResult(BigInteger value, Model.ArithmeticMode arithmetic) {
        if (arithmetic == Model.ArithmeticMode.INT32) {
            return value.add(TWO_31).mod(TWO_32).subtract(TWO_31);
        }
        return value;
    }

    static BigInteger divide(BigInteger left, BigInteger right,
                             Model.ArithmeticMode arithmetic) {
        if (right.signum() == 0) throw new Model.Stuck("division by zero");
        return wrapResult(left.divide(right), arithmetic);
    }

    static BigInteger apply(Model.ArithmeticOperator operator, BigInteger left,
                            BigInteger right, Model.ArithmeticMode arithmetic) {
        switch (operator) {
            case ADD: return wrapResult(left.add(right), arithmetic);
            case SUBTRACT: return wrapResult(left.subtract(right), arithmetic);
            case MULTIPLY: return wrapResult(left.multiply(right), arithmetic);
            case DIVIDE: return divide(left, right, arithmetic);
            default: throw new IllegalArgumentException("unknown operator " + operator);
        }
    }
}
