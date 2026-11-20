package sanga;

import java.util.Map;
import java.util.StringJoiner;

/** Serializes the small set of values used in the HTTP responses. */
final class Json {
    private Json() {}

    static String encode(Object value) {
        if (value == null) return "null";
        if (value instanceof String string) return quote(string);
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Map<?, ?> map) {
            var out = new StringJoiner(",", "{", "}");
            map.forEach((key, item) -> out.add(quote((String) key) + ":" + encode(item)));
            return out.toString();
        }
        if (value instanceof Iterable<?> items) {
            var out = new StringJoiner(",", "[", "]");
            items.forEach(item -> out.add(encode(item)));
            return out.toString();
        }
        throw new IllegalArgumentException("Unsupported JSON value");
    }

    private static String quote(String value) {
        var out = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 32) out.append(String.format("\\u%04x", (int) c));
                    else out.append(c);
                }
            }
        }
        return out.append('"').toString();
    }
}
