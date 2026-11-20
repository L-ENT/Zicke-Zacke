package sanga;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.IntStream;

/** One shared-screen game. Only the symbol of a card just flipped leaves the server. */
final class Game {
    static final int CARD_COUNT = 12;
    static final int TRACK_LENGTH = 24;

    private final String id = UUID.randomUUID().toString();
    private final List<Integer> track;
    private final List<Integer> cards;
    private final List<Player> players = new ArrayList<>();
    private int active;
    private int turn = 1;
    private int revision;
    private int winner = -1;
    private volatile long lastAccess = System.currentTimeMillis();

    private static final class Player {
        final int id;
        final String name;
        final List<Integer> feathers = new ArrayList<>();
        int position;

        Player(int id, String name, int position) {
            this.id = id;
            this.name = name;
            this.position = position;
            feathers.add(id);
        }

        Map<String, Object> view() {
            return Map.of("id", id, "name", name, "position", position, "feathers", List.copyOf(feathers));
        }
    }

    private record Destination(int position, List<Player> passed) {}

    static Game create(List<String> names) {
        var symbols = IntStream.range(0, CARD_COUNT).boxed().toList();
        var track = new ArrayList<>(symbols);
        track.addAll(symbols);
        var cards = new ArrayList<>(symbols);
        Random random = ThreadLocalRandom.current();
        do {
            Collections.shuffle(track, random);
        } while (IntStream.range(0, TRACK_LENGTH)
                .anyMatch(i -> track.get(i).equals(track.get((i + 1) % TRACK_LENGTH))));
        Collections.shuffle(cards, random);
        return new Game(names, track, cards);
    }

    Game(List<String> names, List<Integer> track, List<Integer> cards) {
        if (names.size() < 2 || names.size() > 4) {
            throw new IllegalArgumentException("Choose two to four players.");
        }
        this.track = List.copyOf(track);
        this.cards = List.copyOf(cards);
        for (int i = 0; i < names.size(); i++) {
            String name = names.get(i).strip();
            if (name.isEmpty() || name.codePointCount(0, name.length()) > 24
                    || name.codePoints().anyMatch(Character::isISOControl)) {
                throw new IllegalArgumentException("Player names must have 1 to 24 characters.");
            }
            players.add(new Player(i, name, i * TRACK_LENGTH / names.size()));
        }
    }

    String id() {
        return id;
    }

    long lastAccess() {
        return lastAccess;
    }

    private Destination destination() {
        int position = players.get(active).position;
        var passed = new ArrayList<Player>();
        while (true) {
            position = (position + 1) % TRACK_LENGTH;
            Player occupant = null;
            for (Player player : players) {
                if (player.position == position) {
                    occupant = player;
                    break;
                }
            }
            if (occupant == null) {
                return new Destination(position, passed);
            }
            passed.add(occupant);
        }
    }

    synchronized Map<String, Object> view() {
        lastAccess = System.currentTimeMillis();
        return Map.of(
                "id", id, "revision", revision, "turn", turn, "active", active,
                "winner", winner, "target", winner == -1 ? destination().position() : -1,
                "track", track, "players", players.stream().map(Player::view).toList());
    }

    synchronized Map<String, Object> flip(int slot, int expectedRevision) {
        if (expectedRevision != revision || winner != -1) {
            throw new IllegalStateException("The board has changed. Use the current turn.");
        }
        if (slot < 0 || slot >= CARD_COUNT) {
            throw new IllegalArgumentException("That tile is outside the yard.");
        }
        var player = players.get(active);
        var next = destination();
        int symbol = cards.get(slot);
        boolean matched = symbol == track.get(next.position());
        int stolen = 0;
        if (matched) {
            player.position = next.position();
            for (Player other : next.passed()) {
                stolen += other.feathers.size();
                player.feathers.addAll(other.feathers);
                other.feathers.clear();
            }
            if (player.feathers.size() == players.size()) {
                winner = active;
            }
        } else {
            active = (active + 1) % players.size();
            turn++;
        }
        revision++;
        var reveal = Map.of("slot", slot, "symbol", symbol, "player", player.id,
                "matched", matched, "stolen", stolen, "jumped", matched ? next.passed().size() : 0);
        return Map.of("reveal", reveal, "game", view());
    }
}
