package sanga;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.awt.Desktop;
import java.io.IOException;
import java.net.BindException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;

public final class Server {
    private static final long SESSION_AGE_MS = Duration.ofHours(24).toMillis();
    private static final Map<String, String> TYPES = Map.of(
            "html", "text/html; charset=utf-8", "css", "text/css; charset=utf-8",
            "js", "text/javascript; charset=utf-8", "png", "image/png",
            "ttf", "font/ttf", "txt", "text/plain; charset=utf-8");
    private final Map<String, Game> games = new ConcurrentHashMap<>();

    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(args.length == 0 ? System.getenv().getOrDefault("PORT", "8080") : args[0]);
        var address = new InetSocketAddress(System.getenv().getOrDefault("GAME_HOST", "127.0.0.1"), port);
        HttpServer server;
        try {
            server = HttpServer.create(address, 0);
        } catch (BindException e) {
            System.err.println("Port " + port + " is in use. Choose another port, e.g. Play.cmd 8081");
            System.exit(1);
            return;
        }
        server.createContext("/", new Server()::handle);
        server.setExecutor(Executors.newFixedThreadPool(4));
        server.start();
        String url = "http://127.0.0.1:" + server.getAddress().getPort() + "/";
        System.out.println("Chicken Cha Cha Cha - " + url);
        System.out.println("Press Ctrl+C to stop the game server.");
        if (args.length > 1 && args[1].equals("--open")) {
            try {
                if (Desktop.isDesktopSupported() && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
                    Desktop.getDesktop().browse(URI.create(url));
                }
            } catch (IOException | UnsupportedOperationException | SecurityException e) {
                System.out.println("Open the address above in your browser.");
            }
        }
    }

    private void handle(HttpExchange exchange) throws IOException {
        try (exchange) {
            exchange.getResponseHeaders().set("X-Content-Type-Options", "nosniff");
            try {
                String path = exchange.getRequestURI().getPath();
                if (path.startsWith("/api/")) api(exchange, path);
                else asset(exchange, path);
            } catch (HttpError e) {
                json(exchange, e.status, Map.of("error", e.getMessage()));
            } catch (IllegalArgumentException e) {
                json(exchange, 400, Map.of("error", "The game request is invalid."));
            } catch (IllegalStateException e) {
                json(exchange, 409, Map.of("error", e.getMessage()));
            } catch (RuntimeException e) {
                e.printStackTrace(System.err);
                json(exchange, 500, Map.of("error", "The server could not finish this turn."));
            }
        }
    }

    private void api(HttpExchange exchange, String path) throws IOException {
        if (path.equals("/api/games")) {
            method(exchange, "POST");
            var form = readForm(exchange);
            Game game = Game.create(form.getOrDefault("name", List.of()));
            long cutoff = System.currentTimeMillis() - SESSION_AGE_MS;
            games.values().removeIf(existing -> existing.lastAccess() < cutoff);
            games.put(game.id(), game);
            json(exchange, 201, game.view());
            return;
        }
        String[] parts = path.split("/", -1);
        if (parts.length < 4 || !parts[2].equals("games")) throw missing();
        Game game = games.get(parts[3]);
        if (game == null) throw missing();
        if (parts.length == 4) {
            method(exchange, "GET");
            json(exchange, 200, game.view());
        } else if (parts.length == 5 && parts[4].equals("flip")) {
            method(exchange, "POST");
            var form = readForm(exchange);
            json(exchange, 200, game.flip(number(form, "slot"), number(form, "revision")));
        } else {
            throw missing();
        }
    }

    private static Map<String, List<String>> readForm(HttpExchange exchange) throws IOException {
        if (!"1".equals(exchange.getRequestHeaders().getFirst("X-Zicke-Game"))) {
            throw new HttpError(403, "Make your move from the game board.");
        }
        byte[] bytes = exchange.getRequestBody().readNBytes(4097);
        if (bytes.length > 4096) throw new HttpError(413, "The request is too large.");
        var values = new HashMap<String, List<String>>();
        for (String field : new String(bytes, StandardCharsets.UTF_8).split("&")) {
            String[] pair = field.split("=", 2);
            if (pair.length == 2) {
                String key = URLDecoder.decode(pair[0], StandardCharsets.UTF_8);
                String value = URLDecoder.decode(pair[1], StandardCharsets.UTF_8);
                values.computeIfAbsent(key, ignored -> new ArrayList<>()).add(value);
            }
        }
        return values;
    }

    private static int number(Map<String, List<String>> form, String key) {
        var values = form.get(key);
        if (values == null || values.size() != 1) throw new HttpError(400, "The move is missing required information.");
        return Integer.parseInt(values.get(0));
    }

    private static void asset(HttpExchange exchange, String path) throws IOException {
        boolean head = exchange.getRequestMethod().equals("HEAD");
        if (!head) method(exchange, "GET");
        if (path.equals("/")) path = "/index.html";
        if (!path.matches("/(?:assets/)?[a-zA-Z0-9_-]+\\.[a-zA-Z0-9]+")) throw missing();
        String type = TYPES.get(path.substring(path.lastIndexOf('.') + 1));
        if (type == null) throw missing();
        try (var stream = Server.class.getResourceAsStream("/web" + path)) {
            if (stream == null) throw missing();
            exchange.getResponseHeaders().set("Content-Type", type);
            exchange.getResponseHeaders().set("Cache-Control", "no-cache");
            if (head) {
                exchange.sendResponseHeaders(200, -1);
            } else {
                byte[] bytes = stream.readAllBytes();
                exchange.sendResponseHeaders(200, bytes.length);
                exchange.getResponseBody().write(bytes);
            }
        }
    }

    private static void method(HttpExchange exchange, String allowed) {
        if (!exchange.getRequestMethod().equals(allowed)) {
            exchange.getResponseHeaders().set("Allow", allowed);
            throw new HttpError(405, "This request method is not supported.");
        }
    }

    private static void json(HttpExchange exchange, int status, Object value) throws IOException {
        byte[] bytes = Json.encode(value).getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        exchange.getResponseHeaders().set("Cache-Control", "no-store");
        exchange.sendResponseHeaders(status, bytes.length);
        exchange.getResponseBody().write(bytes);
    }

    private static HttpError missing() {
        return new HttpError(404, "The game or resource could not be found.");
    }

    private static final class HttpError extends RuntimeException {
        final int status;

        HttpError(int status, String message) {
            super(message);
            this.status = status;
        }
    }
}
