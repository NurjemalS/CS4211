#pragma once

#include "model.hpp"

namespace imp {

inline Integer wrapResult(const Integer& value, ArithmeticMode arithmetic) {
    if (arithmetic == ArithmeticMode::Int32) {
        const Integer two31("2147483648");
        const Integer two32("4294967296");
        Integer residue = (value + two31) % two32;
        if (residue < 0) residue += two32;
        return residue - two31;
    }
    return value;
}

inline Integer divide(const Integer& left, const Integer& right,
                      ArithmeticMode arithmetic) {
    if (right == 0) throw Stuck("division by zero");
    return wrapResult(left / right, arithmetic);
}

inline Integer applyArithmeticOperator(ArithmeticOperator op, const Integer& left,
                                       const Integer& right,
                                       ArithmeticMode arithmetic) {
    switch (op) {
        case ArithmeticOperator::Add: return wrapResult(left + right, arithmetic);
        case ArithmeticOperator::Subtract: return wrapResult(left - right, arithmetic);
        case ArithmeticOperator::Multiply: return wrapResult(left * right, arithmetic);
        case ArithmeticOperator::Divide: return divide(left, right, arithmetic);
    }
    throw std::logic_error("unreachable arithmetic operator");
}

}  // namespace imp
