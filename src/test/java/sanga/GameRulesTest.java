package sanga;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.IntStream;

/** Regression cases for the circular track, chained captures and repeated clicks. */
public final class GameRulesTest {
    public static void main(String[] args) {
        shuffledSetup();
        tripleJump();
        stealBackAllFeathers();
        jumpAcrossStart();
        repeatedClick();
        System.out.println("Passed: setup for 2-4, triple jump, recapture, wraparound, duplicate flip and end of game.");
    }

    private static void shuffledSetup() {
        for (int count = 2; count <= 4; count++) {
            var state = Game.create(List.of("A", "B", "C", "D").subList(0, count)).view();
            List<?> track = (List<?>) state.get("track");
            equal(24, track.size());
            for (int symbol = 0; symbol < 12; symbol++) equal(2, Collections.frequency(track, symbol));
            for (int i = 0; i < count; i++) {
                var p = player(state, i);
                equal(i * 24 / count, p.get("position"));
                equal(List.of(i), p.get("feathers"));
            }
            equal(1, state.get("target"));
        }
    }

    private static void tripleJump() {
        var board = fixture(4);
        miss(board);                        // Leave A behind and line up the other chickens.
        moveTo(board, 11); miss(board);      // B
        moveTo(board, 17); miss(board);      // C
        miss(board);                        // D stays on 18.
        moveTo(board, 10); miss(board);      // A
        moveTo(board, 16); miss(board);      // B, C, D now occupy 16, 17, 18.
        miss(board);
        miss(board);
        moveTo(board, 15);
        equal(19, board.view().get("target"));
        var result = match(board);
        equal(3, reveal(result).get("jumped"));
        equal(3, reveal(result).get("stolen"));
        equal(19, player(board.view(), 0).get("position"));
        equal(0, board.view().get("winner"));
        for (int i = 1; i < 4; i++) equal(List.of(), player(board.view(), i).get("feathers"));
        equal(-1, board.view().get("target"));
        var finalState = board.view();
        try {
            board.flip(0, (int) finalState.get("revision"));
            throw new AssertionError("A finished game accepted a flip");
        } catch (IllegalStateException expected) {
            equal(finalState, board.view());
        }
    }

    private static void stealBackAllFeathers() {
        var board = fixture(3);
        moveTo(board, 7);
        match(board);
        equal(List.of(0, 1), player(board.view(), 0).get("feathers"));
        equal(List.of(), player(board.view(), 1).get("feathers"));
        miss(board);
        equal(1, board.view().get("active"));
        var result = match(board);          // B jumps over A and recovers its own feather too.
        equal(2, reveal(result).get("stolen"));
        equal(List.of(0, 1), player(board.view(), 1).get("feathers"));
        equal(-1, board.view().get("winner"));
        moveTo(board, 15);
        match(board);
        equal(1, board.view().get("winner"));
    }

    private static void jumpAcrossStart() {
        var board = fixture(2);
        miss(board);
        moveTo(board, 23);
        equal(1, board.view().get("target"));
        var result = match(board);
        equal(1, reveal(result).get("jumped"));
        equal(1, player(board.view(), 1).get("position"));
        equal(1, board.view().get("winner"));
    }

    private static void repeatedClick() {
        var board = fixture(2);
        var before = board.view();
        miss(board);
        var after = board.view();
        equal(player(before, 0).get("position"), player(after, 0).get("position"));
        equal(2, after.get("turn"));
        try {
            board.flip(1, (int) before.get("revision"));
            throw new AssertionError("A duplicate request advanced the turn");
        } catch (IllegalStateException expected) {
            equal(after, board.view());
        }
    }

    // Use the same rules with a known card order so each move can be reproduced.
    private static Game fixture(int count) {
        var track = IntStream.range(0, 24).map(i -> i % 12).boxed().toList();
        return new Game(List.of("A", "B", "C", "D").subList(0, count), track, track.subList(0, 12));
    }

    private static Map<?, ?> player(Map<String, Object> state, int id) {
        return (Map<?, ?>) ((List<?>) state.get("players")).get(id);
    }

    private static Map<?, ?> reveal(Map<String, Object> result) {
        return (Map<?, ?>) result.get("reveal");
    }

    private static Map<String, Object> match(Game board) {
        var state = board.view();
        return board.flip((int) state.get("target") % 12, (int) state.get("revision"));
    }

    private static void miss(Game board) {
        var state = board.view();
        board.flip(((int) state.get("target") + 1) % 12, (int) state.get("revision"));
    }

    private static void moveTo(Game board, int position) {
        for (int i = 0; i < 24; i++) {
            var state = board.view();
            if (player(state, (int) state.get("active")).get("position").equals(position)) return;
            match(board);
        }
        throw new AssertionError("Could not reach " + position);
    }

    private static void equal(Object expected, Object actual) {
        if (!expected.equals(actual)) throw new AssertionError("Expected " + expected + " but got " + actual);
    }
}
