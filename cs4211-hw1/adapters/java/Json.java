// CS4211 HW1 --- a minimal JSON value, parser and printer.
//
// GIVEN.  You should not need to change this file.  Java has no JSON support
// in its standard library, so this is here purely so you can spend your time
// on the semantics rather than on parsing.
//
// JSON integers use BigInteger so the "int" semantics remains genuinely
// arbitrary precision all the way through the process interface.

import java.io.IOException;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public final class Json {
    public enum Type { NULL, BOOL, INT, STR, ARR, OBJ }

    public Type type = Type.NULL;
    public boolean b;
    public BigInteger i = BigInteger.ZERO;
    public String s;
    public List<Json> arr = new ArrayList<>();
    public Map<String, Json> obj = new TreeMap<>();   // sorted iteration

    public static Json nul()               { Json j = new Json(); j.type = Type.NULL; return j; }
    public static Json of(boolean v)       { Json j = new Json(); j.type = Type.BOOL; j.b = v; return j; }
    public static Json of(long v)          { return of(BigInteger.valueOf(v)); }
    public static Json of(BigInteger v)    { Json j = new Json(); j.type = Type.INT;  j.i = v; return j; }
    public static Json of(String v)        { Json j = new Json(); j.type = Type.STR;  j.s = v; return j; }
    public static Json array()             { Json j = new Json(); j.type = Type.ARR;  return j; }
    public static Json object()            { Json j = new Json(); j.type = Type.OBJ;  return j; }

    public boolean has(String k) { return type == Type.OBJ && obj.containsKey(k); }

    public Json at(String k) {
        Json v = obj.get(k);
        if (v == null) throw new RuntimeException("missing key: " + k);
        return v;
    }

    /** Put a member and return this, so calls chain. */
    public Json put(String k, Json v) {
        if (type != Type.OBJ) { type = Type.OBJ; }
        obj.put(k, v);
        return this;
    }
    public Json put(String k, String v)  { return put(k, of(v)); }
    public Json put(String k, long v)    { return put(k, of(v)); }
    public Json put(String k, BigInteger v) { return put(k, of(v)); }
    public Json put(String k, boolean v) { return put(k, of(v)); }

    public Json push(Json v) {
        if (type != Type.ARR) { type = Type.ARR; }
        arr.add(v);
        return this;
    }

    /** The "k" tag of an AST node. */
    public String kind() { return at("k").s; }

    /** A deep copy, so functional updates never alias. */
    public Json copy() {
        Json j = new Json();
        j.type = type; j.b = b; j.i = i; j.s = s;
        for (Json e : arr) j.arr.add(e.copy());
        for (Map.Entry<String, Json> e : obj.entrySet()) j.obj.put(e.getKey(), e.getValue().copy());
        return j;
    }

    @Override public boolean equals(Object o) {
        if (!(o instanceof Json)) return false;
        return dump().equals(((Json) o).dump());
    }
    @Override public int hashCode() { return dump().hashCode(); }
    @Override public String toString() { return dump(); }

    /** Canonical compact serialisation; object keys come out sorted. */
    public String dump() {
        StringBuilder sb = new StringBuilder();
        write(sb);
        return sb.toString();
    }

    private void write(StringBuilder sb) {
        switch (type) {
            case NULL: sb.append("null"); break;
            case BOOL: sb.append(b ? "true" : "false"); break;
            case INT:  sb.append(i); break;
            case STR:  writeString(sb, s); break;
            case ARR: {
                sb.append('[');
                for (int n = 0; n < arr.size(); n++) {
                    if (n > 0) sb.append(',');
                    arr.get(n).write(sb);
                }
                sb.append(']');
                break;
            }
            case OBJ: {
                sb.append('{');
                boolean first = true;
                for (Map.Entry<String, Json> e : obj.entrySet()) {
                    if (!first) sb.append(',');
                    first = false;
                    writeString(sb, e.getKey());
                    sb.append(':');
                    e.getValue().write(sb);
                }
                sb.append('}');
                break;
            }
        }
    }

    private static void writeString(StringBuilder sb, String v) {
        sb.append('"');
        for (int n = 0; n < v.length(); n++) {
            char ch = v.charAt(n);
            switch (ch) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n");  break;
                case '\r': sb.append("\\r");  break;
                case '\t': sb.append("\\t");  break;
                default:
                    if (ch < 0x20) sb.append(String.format("\\u%04x", (int) ch));
                    else sb.append(ch);
            }
        }
        sb.append('"');
    }

    // ------------------------------------------------------------------
    // parsing
    // ------------------------------------------------------------------

    public static Json parse(String text) { return new Parser(text).parseValue(); }

    public static Json readStdin() throws IOException {
        InputStream in = System.in;
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] chunk = new byte[8192];
        int n;
        while ((n = in.read(chunk)) > 0) buf.write(chunk, 0, n);
        return parse(new String(buf.toByteArray(), StandardCharsets.UTF_8));
    }

    private static final class Parser {
        private final String t;
        private int p = 0;

        Parser(String text) { this.t = text; }

        private void skip() {
            while (p < t.length()) {
                char c = t.charAt(p);
                if (c == ' ' || c == '\n' || c == '\r' || c == '\t') p++;
                else break;
            }
        }

        private char peek() {
            skip();
            if (p >= t.length()) throw new RuntimeException("unexpected end of JSON");
            return t.charAt(p);
        }

        private void expect(char c) {
            if (peek() != c) throw new RuntimeException("expected '" + c + "'");
            p++;
        }

        private boolean literal(String lit) {
            if (t.regionMatches(p, lit, 0, lit.length())) { p += lit.length(); return true; }
            return false;
        }

        Json parseValue() {
            char c = peek();
            if (c == '{') return parseObject();
            if (c == '[') return parseArray();
            if (c == '"') return Json.of(parseString());
            if (literal("true"))  return Json.of(true);
            if (literal("false")) return Json.of(false);
            if (literal("null"))  return Json.nul();
            return parseNumber();
        }

        private Json parseObject() {
            expect('{');
            Json o = Json.object();
            if (peek() == '}') { p++; return o; }
            while (true) {
                String k = parseString();
                expect(':');
                o.obj.put(k, parseValue());
                char c = peek();
                if (c == ',') { p++; continue; }
                expect('}');
                return o;
            }
        }

        private Json parseArray() {
            expect('[');
            Json a = Json.array();
            if (peek() == ']') { p++; return a; }
            while (true) {
                a.arr.add(parseValue());
                char c = peek();
                if (c == ',') { p++; continue; }
                expect(']');
                return a;
            }
        }

        private String parseString() {
            expect('"');
            StringBuilder sb = new StringBuilder();
            while (p < t.length() && t.charAt(p) != '"') {
                char c = t.charAt(p);
                if (c == '\\') {
                    p++;
                    if (p >= t.length()) throw new RuntimeException("bad escape");
                    char e = t.charAt(p);
                    switch (e) {
                        case 'n': sb.append('\n'); break;
                        case 't': sb.append('\t'); break;
                        case 'r': sb.append('\r'); break;
                        case 'b': sb.append('\b'); break;
                        case 'f': sb.append('\f'); break;
                        case '/': sb.append('/');  break;
                        case '"': sb.append('"');  break;
                        case '\\': sb.append('\\'); break;
                        case 'u':
                            sb.append((char) Integer.parseInt(t.substring(p + 1, p + 5), 16));
                            p += 4;
                            break;
                        default: throw new RuntimeException("bad escape: \\" + e);
                    }
                    p++;
                } else {
                    sb.append(c);
                    p++;
                }
            }
            expect('"');
            return sb.toString();
        }

        private Json parseNumber() {
            int start = p;
            if (p < t.length() && (t.charAt(p) == '-' || t.charAt(p) == '+')) p++;
            while (p < t.length() && Character.isDigit(t.charAt(p))) p++;
            if (start == p) throw new RuntimeException("bad number at offset " + p);
            return Json.of(new BigInteger(t.substring(start, p)));
        }
    }
}
