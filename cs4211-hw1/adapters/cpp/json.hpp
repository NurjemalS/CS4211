// CS4211 HW1 --- a minimal JSON value, parser and printer.
//
// GIVEN.  You should not need to change this file.  The C++ standard library
// has no JSON support, so this is here purely so you can spend your time on
// the semantics rather than on parsing.
//
// Integers use boost::multiprecision::cpp_int so the "int" semantics remains
// genuinely arbitrary precision through the process interface.
#ifndef CS4211_JSON_HPP
#define CS4211_JSON_HPP

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <stdexcept>
#include <sstream>
#include <iostream>
#include <cstring>
#include <cstdio>
#include <cctype>
#include "integer.hpp"

namespace cs4211 {

using Integer = BigInteger;

struct Json;
using JsonPtr = std::shared_ptr<Json>;

struct Json {
    enum Type { Null, Bool, Int, Str, Arr, Obj };
    Type type = Null;
    bool b = false;
    Integer i = 0;
    std::string s;
    std::vector<Json> arr;
    std::map<std::string, Json> obj;

    Json() {}
    static Json null()                    { Json j; j.type = Null; return j; }
    static Json boolean(bool v)           { Json j; j.type = Bool; j.b = v; return j; }
    static Json integer(const Integer& v) { Json j; j.type = Int;  j.i = v; return j; }
    static Json integer(long long v)      { return integer(Integer(v)); }
    static Json str(const std::string& v) { Json j; j.type = Str;  j.s = v; return j; }
    static Json array()                   { Json j; j.type = Arr;  return j; }
    static Json object()                  { Json j; j.type = Obj;  return j; }

    bool has(const std::string& k) const {
        return type == Obj && obj.find(k) != obj.end();
    }
    const Json& at(const std::string& k) const {
        auto it = obj.find(k);
        if (it == obj.end()) throw std::runtime_error("missing key: " + k);
        return it->second;
    }
    Json& operator[](const std::string& k) {
        if (type != Obj) { type = Obj; }
        return obj[k];
    }
    void push(const Json& v) { if (type != Arr) type = Arr; arr.push_back(v); }

    // Convenience accessors used by the semantics code.
    const std::string& kind() const { return at("k").s; }
    const Integer& asInt() const { return i; }
    bool asBool() const { return b; }

    bool operator==(const Json& o) const {
        if (type != o.type) return false;
        switch (type) {
            case Null: return true;
            case Bool: return b == o.b;
            case Int:  return i == o.i;
            case Str:  return s == o.s;
            case Arr:  return arr == o.arr;
            case Obj:  return obj == o.obj;
        }
        return false;
    }
    bool operator!=(const Json& o) const { return !(*this == o); }
    bool operator<(const Json& o) const { return dump() < o.dump(); }

    std::string dump() const {
        std::ostringstream out;
        write(out);
        return out.str();
    }

    void write(std::ostream& out) const {
        switch (type) {
            case Null: out << "null"; break;
            case Bool: out << (b ? "true" : "false"); break;
            case Int:  out << i; break;
            case Str:  writeString(out, s); break;
            case Arr: {
                out << '[';
                for (size_t n = 0; n < arr.size(); ++n) {
                    if (n) out << ',';
                    arr[n].write(out);
                }
                out << ']';
                break;
            }
            case Obj: {
                out << '{';
                bool first = true;
                for (const auto& kv : obj) {   // std::map iterates sorted
                    if (!first) out << ',';
                    first = false;
                    writeString(out, kv.first);
                    out << ':';
                    kv.second.write(out);
                }
                out << '}';
                break;
            }
        }
    }

private:
    static void writeString(std::ostream& out, const std::string& v) {
        out << '"';
        for (char ch : v) {
            switch (ch) {
                case '"':  out << "\\\""; break;
                case '\\': out << "\\\\"; break;
                case '\n': out << "\\n";  break;
                case '\r': out << "\\r";  break;
                case '\t': out << "\\t";  break;
                default:
                    if (static_cast<unsigned char>(ch) < 0x20) {
                        char buf[7];
                        snprintf(buf, sizeof buf, "\\u%04x", ch);
                        out << buf;
                    } else {
                        out << ch;
                    }
            }
        }
        out << '"';
    }
};

class JsonParser {
public:
    explicit JsonParser(const std::string& text) : t(text), p(0) {}

    Json parse() {
        Json v = value();
        skip();
        return v;
    }

private:
    const std::string& t;
    size_t p;

    void skip() {
        while (p < t.size() && (t[p] == ' ' || t[p] == '\n' || t[p] == '\r' || t[p] == '\t'))
            ++p;
    }
    char peek() {
        skip();
        if (p >= t.size()) throw std::runtime_error("unexpected end of JSON");
        return t[p];
    }
    void expect(char c) {
        if (peek() != c)
            throw std::runtime_error(std::string("expected '") + c + "'");
        ++p;
    }
    bool literal(const char* lit) {
        size_t n = strlen(lit);
        if (t.compare(p, n, lit) == 0) { p += n; return true; }
        return false;
    }

    Json value() {
        char c = peek();
        if (c == '{') return objectValue();
        if (c == '[') return arrayValue();
        if (c == '"') return Json::str(stringValue());
        if (literal("true"))  return Json::boolean(true);
        if (literal("false")) return Json::boolean(false);
        if (literal("null"))  return Json::null();
        return numberValue();
    }

    Json objectValue() {
        expect('{');
        Json o = Json::object();
        if (peek() == '}') { ++p; return o; }
        for (;;) {
            std::string k = stringValue();
            expect(':');
            o.obj[k] = value();
            char c = peek();
            if (c == ',') { ++p; continue; }
            expect('}');
            return o;
        }
    }

    Json arrayValue() {
        expect('[');
        Json a = Json::array();
        if (peek() == ']') { ++p; return a; }
        for (;;) {
            a.arr.push_back(value());
            char c = peek();
            if (c == ',') { ++p; continue; }
            expect(']');
            return a;
        }
    }

    std::string stringValue() {
        expect('"');
        std::string out;
        while (p < t.size() && t[p] != '"') {
            if (t[p] == '\\') {
                ++p;
                if (p >= t.size()) throw std::runtime_error("bad escape");
                switch (t[p]) {
                    case 'n': out += '\n'; break;
                    case 't': out += '\t'; break;
                    case 'r': out += '\r'; break;
                    case 'b': out += '\b'; break;
                    case 'f': out += '\f'; break;
                    case '/': out += '/';  break;
                    case '"': out += '"';  break;
                    case '\\': out += '\\'; break;
                    case 'u': {
                        // Test inputs are ASCII; keep this simple.
                        unsigned code = std::stoul(t.substr(p + 1, 4), nullptr, 16);
                        p += 4;
                        out += static_cast<char>(code & 0x7f);
                        break;
                    }
                    default: throw std::runtime_error("bad escape");
                }
                ++p;
            } else {
                out += t[p++];
            }
        }
        expect('"');
        return out;
    }

    Json numberValue() {
        size_t start = p;
        if (p < t.size() && (t[p] == '-' || t[p] == '+')) ++p;
        while (p < t.size() && isdigit(static_cast<unsigned char>(t[p]))) ++p;
        if (start == p) throw std::runtime_error("bad number");
        return Json::integer(Integer(t.substr(start, p - start)));
    }
};

inline Json parseJson(const std::string& text) { return JsonParser(text).parse(); }

inline Json readStdin() {
    std::ostringstream buf;
    buf << std::cin.rdbuf();
    return parseJson(buf.str());
}

}  // namespace cs4211
#endif
