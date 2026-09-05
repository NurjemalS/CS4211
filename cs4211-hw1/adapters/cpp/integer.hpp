#ifndef CS4211_INTEGER_HPP
#define CS4211_INTEGER_HPP

// GIVEN arbitrary-precision signed integers for the C++ adapter.
//
// The C++ standard library has no arbitrary-precision integer type.  This
// small class supplies exactly the operations used by IMP: comparison,
// addition, subtraction, multiplication, division, remainder, parsing, and
// printing.  Students do not need to modify this file.

#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <ostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace cs4211 {

class BigInteger {
public:
    BigInteger() = default;
    BigInteger(long long value) { assign(value); }
    explicit BigInteger(const std::string& text) { parse(text); }

    std::string str() const {
        if (sign_ == 0) return "0";
        std::ostringstream out;
        if (sign_ < 0) out << '-';
        out << digits_.back();
        for (std::size_t i = digits_.size() - 1; i-- > 0;)
            out << std::setw(9) << std::setfill('0') << digits_[i];
        return out.str();
    }

    long long toLongLong() const {
        const BigInteger minimum(std::numeric_limits<long long>::min());
        const BigInteger maximum(std::numeric_limits<long long>::max());
        if (*this < minimum || *this > maximum)
            throw std::overflow_error("integer does not fit in long long");
        unsigned long long magnitude = 0;
        for (std::size_t i = digits_.size(); i-- > 0;)
            magnitude = magnitude * base_ + digits_[i];
        if (sign_ >= 0) return static_cast<long long>(magnitude);
        if (magnitude == (1ULL << 63)) return std::numeric_limits<long long>::min();
        return -static_cast<long long>(magnitude);
    }

    std::size_t toSizeT() const {
        if (sign_ < 0) throw std::overflow_error("negative array index");
        const BigInteger maximum(std::to_string(std::numeric_limits<std::size_t>::max()));
        if (*this > maximum) throw std::overflow_error("array index is too large");
        std::size_t value = 0;
        for (std::size_t i = digits_.size(); i-- > 0;)
            value = value * static_cast<std::size_t>(base_) + digits_[i];
        return value;
    }

    BigInteger operator-() const {
        BigInteger result = *this;
        result.sign_ = -result.sign_;
        return result;
    }

    friend BigInteger operator+(const BigInteger& left, const BigInteger& right) {
        if (left.sign_ == 0) return right;
        if (right.sign_ == 0) return left;
        if (left.sign_ == right.sign_) {
            BigInteger result = addAbs(left, right);
            result.sign_ = left.sign_;
            return result;
        }
        const int order = compareAbs(left, right);
        if (order == 0) return BigInteger();
        BigInteger result = order > 0 ? subtractAbs(left, right) : subtractAbs(right, left);
        result.sign_ = order > 0 ? left.sign_ : right.sign_;
        return result;
    }

    friend BigInteger operator-(const BigInteger& left, const BigInteger& right) {
        return left + (-right);
    }

    friend BigInteger operator*(const BigInteger& left, const BigInteger& right) {
        if (left.sign_ == 0 || right.sign_ == 0) return BigInteger();
        BigInteger result;
        result.digits_.assign(left.digits_.size() + right.digits_.size(), 0);
        for (std::size_t i = 0; i < left.digits_.size(); ++i) {
            std::uint64_t carry = 0;
            for (std::size_t j = 0; j < right.digits_.size() || carry != 0; ++j) {
                const std::uint64_t product = result.digits_[i + j] + carry
                    + static_cast<std::uint64_t>(left.digits_[i])
                    * (j < right.digits_.size() ? right.digits_[j] : 0U);
                result.digits_[i + j] = static_cast<std::uint32_t>(product % base_);
                carry = product / base_;
            }
        }
        result.sign_ = left.sign_ * right.sign_;
        result.normalise();
        return result;
    }

    friend BigInteger operator/(const BigInteger& left, const BigInteger& right) {
        return divmod(left, right).first;
    }

    friend BigInteger operator%(const BigInteger& left, const BigInteger& right) {
        return divmod(left, right).second;
    }

    BigInteger& operator+=(const BigInteger& other) { return *this = *this + other; }
    BigInteger& operator-=(const BigInteger& other) { return *this = *this - other; }
    BigInteger& operator*=(const BigInteger& other) { return *this = *this * other; }
    BigInteger& operator/=(const BigInteger& other) { return *this = *this / other; }
    BigInteger& operator%=(const BigInteger& other) { return *this = *this % other; }

    friend bool operator==(const BigInteger& left, const BigInteger& right) {
        return left.sign_ == right.sign_ && left.digits_ == right.digits_;
    }
    friend bool operator!=(const BigInteger& left, const BigInteger& right) {
        return !(left == right);
    }
    friend bool operator<(const BigInteger& left, const BigInteger& right) {
        if (left.sign_ != right.sign_) return left.sign_ < right.sign_;
        if (left.sign_ == 0) return false;
        const int order = compareAbs(left, right);
        return left.sign_ > 0 ? order < 0 : order > 0;
    }
    friend bool operator>(const BigInteger& left, const BigInteger& right) { return right < left; }
    friend bool operator<=(const BigInteger& left, const BigInteger& right) { return !(right < left); }
    friend bool operator>=(const BigInteger& left, const BigInteger& right) { return !(left < right); }

    friend std::ostream& operator<<(std::ostream& out, const BigInteger& value) {
        return out << value.str();
    }

private:
    static constexpr std::uint32_t base_ = 1000000000U;
    int sign_ = 0;
    std::vector<std::uint32_t> digits_;  // little-endian base 10^9

    void assign(long long value) {
        sign_ = 0;
        digits_.clear();
        if (value == 0) return;
        sign_ = value < 0 ? -1 : 1;
        unsigned long long magnitude;
        if (value < 0)
            magnitude = static_cast<unsigned long long>(-(value + 1)) + 1ULL;
        else
            magnitude = static_cast<unsigned long long>(value);
        while (magnitude != 0) {
            digits_.push_back(static_cast<std::uint32_t>(magnitude % base_));
            magnitude /= base_;
        }
    }

    void parse(const std::string& text) {
        sign_ = 0;
        digits_.clear();
        if (text.empty()) throw std::invalid_argument("empty integer");
        std::size_t start = 0;
        int parsedSign = 1;
        if (text[0] == '-' || text[0] == '+') {
            parsedSign = text[0] == '-' ? -1 : 1;
            start = 1;
        }
        if (start == text.size()) throw std::invalid_argument("invalid integer");
        for (std::size_t i = start; i < text.size(); ++i)
            if (text[i] < '0' || text[i] > '9')
                throw std::invalid_argument("invalid integer " + text);
        for (std::size_t end = text.size(); end > start;) {
            const std::size_t begin = end >= start + 9 ? end - 9 : start;
            digits_.push_back(static_cast<std::uint32_t>(
                std::stoul(text.substr(begin, end - begin))));
            end = begin;
        }
        sign_ = parsedSign;
        normalise();
    }

    void normalise() {
        while (!digits_.empty() && digits_.back() == 0) digits_.pop_back();
        if (digits_.empty()) sign_ = 0;
    }

    static int compareAbs(const BigInteger& left, const BigInteger& right) {
        if (left.digits_.size() != right.digits_.size())
            return left.digits_.size() < right.digits_.size() ? -1 : 1;
        for (std::size_t i = left.digits_.size(); i-- > 0;) {
            if (left.digits_[i] != right.digits_[i])
                return left.digits_[i] < right.digits_[i] ? -1 : 1;
        }
        return 0;
    }

    static BigInteger addAbs(const BigInteger& left, const BigInteger& right) {
        BigInteger result;
        const std::size_t count = std::max(left.digits_.size(), right.digits_.size());
        result.digits_.resize(count);
        std::uint64_t carry = 0;
        for (std::size_t i = 0; i < count; ++i) {
            const std::uint64_t sum = carry
                + (i < left.digits_.size() ? left.digits_[i] : 0U)
                + (i < right.digits_.size() ? right.digits_[i] : 0U);
            result.digits_[i] = static_cast<std::uint32_t>(sum % base_);
            carry = sum / base_;
        }
        if (carry != 0) result.digits_.push_back(static_cast<std::uint32_t>(carry));
        result.sign_ = 1;
        return result;
    }

    // Requires |larger| >= |smaller|.
    static BigInteger subtractAbs(const BigInteger& larger, const BigInteger& smaller) {
        BigInteger result;
        result.digits_.resize(larger.digits_.size());
        std::int64_t borrow = 0;
        for (std::size_t i = 0; i < larger.digits_.size(); ++i) {
            std::int64_t difference = static_cast<std::int64_t>(larger.digits_[i])
                - (i < smaller.digits_.size() ? smaller.digits_[i] : 0U) - borrow;
            if (difference < 0) { difference += base_; borrow = 1; }
            else borrow = 0;
            result.digits_[i] = static_cast<std::uint32_t>(difference);
        }
        result.sign_ = 1;
        result.normalise();
        return result;
    }

    static BigInteger multiplyDigit(const BigInteger& value, std::uint32_t digit) {
        if (value.sign_ == 0 || digit == 0) return BigInteger();
        BigInteger result;
        result.digits_.resize(value.digits_.size());
        std::uint64_t carry = 0;
        for (std::size_t i = 0; i < value.digits_.size(); ++i) {
            const std::uint64_t product =
                static_cast<std::uint64_t>(value.digits_[i]) * digit + carry;
            result.digits_[i] = static_cast<std::uint32_t>(product % base_);
            carry = product / base_;
        }
        if (carry != 0) result.digits_.push_back(static_cast<std::uint32_t>(carry));
        result.sign_ = 1;
        return result;
    }

    void shiftBaseAndAdd(std::uint32_t digit) {
        if (sign_ == 0 && digit == 0) return;
        digits_.insert(digits_.begin(), digit);
        sign_ = 1;
        normalise();
    }

    static std::pair<BigInteger, BigInteger> divmod(
        const BigInteger& dividend, const BigInteger& divisor) {
        if (divisor.sign_ == 0) throw std::domain_error("division by zero");
        if (dividend.sign_ == 0) return {BigInteger(), BigInteger()};

        BigInteger numerator = dividend;
        BigInteger denominator = divisor;
        numerator.sign_ = 1;
        denominator.sign_ = 1;
        if (compareAbs(numerator, denominator) < 0)
            return {BigInteger(), dividend};

        BigInteger quotient;
        quotient.sign_ = 1;
        quotient.digits_.assign(numerator.digits_.size(), 0);
        BigInteger remainder;

        for (std::size_t i = numerator.digits_.size(); i-- > 0;) {
            remainder.shiftBaseAndAdd(numerator.digits_[i]);
            std::uint32_t low = 0;
            std::uint32_t high = base_ - 1;
            std::uint32_t best = 0;
            while (low <= high) {
                const std::uint32_t middle = low + (high - low) / 2;
                const BigInteger candidate = multiplyDigit(denominator, middle);
                if (candidate <= remainder) {
                    best = middle;
                    if (middle == base_ - 1) break;
                    low = middle + 1;
                } else {
                    if (middle == 0) break;
                    high = middle - 1;
                }
            }
            quotient.digits_[i] = best;
            remainder = subtractAbs(remainder, multiplyDigit(denominator, best));
        }

        quotient.sign_ = dividend.sign_ * divisor.sign_;
        quotient.normalise();
        remainder.sign_ = dividend.sign_;
        remainder.normalise();
        return {quotient, remainder};
    }
};

}  // namespace cs4211

#endif
