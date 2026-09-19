"""Short documentation animations for the lexical analyzer project.

Every scene uses ordinary Manim shapes and Text objects, so LaTeX is not
required. Render all scenes with ``python render.py`` from this directory.
"""

import numpy as np

from manim import (
    AnimationGroup,
    Arrow,
    BLUE_C,
    Circle,
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    GREEN_C,
    Indicate,
    LEFT,
    Line,
    ORIGIN,
    RED_C,
    ReplacementTransform,
    RIGHT,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    Transform,
    UP,
    VGroup,
    WHITE,
    Write,
    YELLOW_C,
    config,
)


BG = "#0c0a09"
PANEL = "#1c1917"
MUTED = "#a8a29e"
AMBER = "#f59e0b"
GREEN = "#34d399"
BLUE = "#60a5fa"
PURPLE = "#a78bfa"
RED = "#fb7185"
STATE_RADIUS = 0.42

config.background_color = BG
config.frame_rate = 15


def label(text, size=28, color=WHITE, weight="NORMAL"):
    return Text(text, font="Segoe UI", font_size=size, color=color, weight=weight)


def mono(text, size=28, color=WHITE, weight="NORMAL"):
    return Text(text, font="Consolas", font_size=size, color=color, weight=weight)


def card(width, height, stroke=MUTED):
    return RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.16,
        color=stroke,
        stroke_width=2,
        fill_color=PANEL,
        fill_opacity=1,
    )


def state_node(name, accepting=False, color=BLUE):
    outer = Circle(radius=STATE_RADIUS, color=color, stroke_width=3, fill_color=PANEL, fill_opacity=1)
    pieces = [outer]
    if accepting:
        pieces.append(Circle(radius=0.34, color=color, stroke_width=2))
    pieces.append(mono(name, 20))
    return VGroup(*pieces)


def transition(left, right, text, color=MUTED, label_side=1, label_offset=0.2):
    """Draw a clipped state transition with a readable, offset label."""
    start = left.get_center()
    end = right.get_center()
    direction = end - start
    length = np.linalg.norm(direction)
    if length == 0:
        raise ValueError("A transition needs two different state positions")
    unit = direction / length

    edge = Arrow(
        start,
        end,
        buff=STATE_RADIUS + 0.08,
        stroke_width=2.5,
        color=color,
        max_tip_length_to_length_ratio=0.15,
    )
    normal = np.array([-unit[1], unit[0], 0.0]) * label_side
    edge_label = mono(text, 18, color)
    edge_label.move_to(edge.point_from_proportion(0.5) + normal * label_offset)
    label_background = SurroundingRectangle(
        edge_label,
        buff=0.04,
        color=PANEL,
        stroke_width=0,
        fill_color=PANEL,
        fill_opacity=0.96,
    )
    return VGroup(edge, label_background, edge_label)


class PortfolioScene(Scene):
    """Shared title and footer treatment."""

    scene_title = ""
    scene_subtitle = ""

    def add_heading(self):
        title = label(self.scene_title, 34, WHITE, "BOLD").to_edge(UP, buff=0.35)
        subtitle = label(self.scene_subtitle, 19, MUTED).next_to(title, DOWN, buff=0.12)
        rule = Line(LEFT * 6.4, RIGHT * 6.4, color="#292524", stroke_width=2).next_to(
            subtitle, DOWN, buff=0.22
        )
        self.play(Write(title), FadeIn(subtitle), Create(rule), run_time=0.7)
        return VGroup(title, subtitle, rule)

    def add_footer(self):
        footer = label("CSC339 Lexical Analyzer Visualizer", 15, "#78716c")
        footer.to_edge(DOWN, buff=0.18).to_edge(RIGHT, buff=0.35)
        self.add(footer)


class ThompsonConstruction(PortfolioScene):
    scene_title = "Thompson's Construction"
    scene_subtitle = "Build a small epsilon-NFA for each regex operator"

    def construct(self):
        self.add_footer()
        heading = self.add_heading()

        regex_card = card(3.5, 0.85, AMBER).shift(UP * 1.75)
        regex = mono("(a|b)*", 34, "#fbbf24", "BOLD").move_to(regex_card)
        self.play(FadeIn(regex_card), Write(regex), run_time=0.6)

        a0 = state_node("a0").move_to(LEFT * 4.8 + DOWN * 0.4)
        a1 = state_node("a1", True, GREEN).move_to(LEFT * 3.0 + DOWN * 0.4)
        b0 = state_node("b0").move_to(RIGHT * 1.5 + DOWN * 0.4)
        b1 = state_node("b1", True, GREEN).move_to(RIGHT * 3.3 + DOWN * 0.4)
        a_edge = transition(a0, a1, "a", BLUE)
        b_edge = transition(b0, b1, "b", BLUE)

        literal_label = label("1. Literal fragments", 20, MUTED).shift(LEFT * 4.0 + UP * 0.55)
        self.play(FadeIn(literal_label), FadeIn(a0), FadeIn(a1), Create(a_edge), run_time=0.75)
        self.play(FadeIn(b0), FadeIn(b1), Create(b_edge), run_time=0.75)

        fragments = VGroup(a0, a1, a_edge, b0, b1, b_edge, literal_label)
        self.play(fragments.animate.scale(0.72).shift(UP * 0.15), run_time=0.55)

        union_panel = card(8.8, 3.4, PURPLE).shift(DOWN * 0.85)
        union_title = label("2. Union adds epsilon branches", 18, "#c4b5fd")
        union_title.next_to(union_panel.get_top(), DOWN, buff=0.18)
        u0 = state_node("u0", color=PURPLE).move_to(LEFT * 3.25 + DOWN * 0.85)
        ua = state_node("a").move_to(LEFT * 1.0 + DOWN * 0.35)
        ub = state_node("b").move_to(LEFT * 1.0 + DOWN * 1.35)
        uf = state_node("uf", True, GREEN).move_to(RIGHT * 1.75 + DOWN * 0.85)
        edges = VGroup(
            transition(u0, ua, "ε", PURPLE, label_side=1),
            transition(u0, ub, "ε", PURPLE, label_side=-1),
            transition(ua, uf, "a", BLUE, label_side=1),
            transition(ub, uf, "b", BLUE, label_side=-1),
        )
        self.play(FadeOut(fragments), FadeIn(union_panel), FadeIn(union_title), run_time=0.5)
        self.play(FadeIn(VGroup(u0, ua, ub, uf)), Create(edges), run_time=1.1)

        loop = Arrow(
            uf.get_bottom(),
            u0.get_bottom(),
            buff=0.08,
            path_arc=-1.2,
            color=AMBER,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )
        skip = Arrow(
            u0.get_top(),
            uf.get_top(),
            buff=0.08,
            path_arc=-0.65,
            color=AMBER,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )
        star_caption = label("3. Star adds epsilon skip (top) and repeat (bottom)", 19, "#fbbf24")
        star_caption.next_to(union_panel, DOWN, buff=0.28)
        self.play(Create(loop), Create(skip), FadeIn(star_caption), run_time=1.0)
        self.play(Indicate(VGroup(u0, ua, ub, uf), color=GREEN_C, scale_factor=1.04), run_time=0.7)
        self.wait(0.9)


class SubsetConstruction(PortfolioScene):
    scene_title = "Subset Construction"
    scene_subtitle = "Each DFA state represents an epsilon-closed set of NFA states"

    def construct(self):
        self.add_footer()
        self.add_heading()

        nfa_panel = card(5.45, 4.0, BLUE).shift(LEFT * 3.3 + DOWN * 0.45)
        dfa_panel = card(5.45, 4.0, PURPLE).shift(RIGHT * 3.3 + DOWN * 0.45)
        nfa_title = label("NFA", 22, "#93c5fd", "BOLD").next_to(nfa_panel.get_top(), DOWN, buff=0.18)
        dfa_title = label("DFA", 22, "#c4b5fd", "BOLD").next_to(dfa_panel.get_top(), DOWN, buff=0.18)
        self.play(FadeIn(nfa_panel), FadeIn(dfa_panel), FadeIn(nfa_title), FadeIn(dfa_title), run_time=0.6)

        q0 = state_node("q0").move_to(LEFT * 5.0 + DOWN * 0.45)
        q1 = state_node("q1").move_to(LEFT * 3.55 + UP * 0.45)
        q2 = state_node("q2", True, GREEN).move_to(LEFT * 2.0 + UP * 0.45)
        q3 = state_node("q3").move_to(LEFT * 3.55 + DOWN * 1.35)
        q4 = state_node("q4", True, GREEN).move_to(LEFT * 2.0 + DOWN * 1.35)
        nfa_edges = VGroup(
            transition(q0, q1, "ε", PURPLE, label_side=1),
            transition(q0, q3, "ε", PURPLE, label_side=-1),
            transition(q1, q2, "a", BLUE, label_side=1),
            transition(q3, q4, "b", BLUE, label_side=-1),
        )
        self.play(FadeIn(VGroup(q0, q1, q2, q3, q4)), Create(nfa_edges), run_time=1.0)

        closure = mono("epsilon-closure(q0)\n= {q0, q1, q3}", 22, "#fbbf24")
        closure.move_to(RIGHT * 3.3 + UP * 0.7)
        self.play(Write(closure), run_time=0.7)

        a = state_node("A").move_to(RIGHT * 1.55 + DOWN * 0.65)
        b = state_node("B", True, GREEN).move_to(RIGHT * 3.45 + DOWN * 0.05)
        c = state_node("C", True, GREEN).move_to(RIGHT * 3.45 + DOWN * 1.3)
        dfa_edges = VGroup(
            transition(a, b, "a", BLUE, label_side=1),
            transition(a, c, "b", BLUE, label_side=-1),
        )
        state_sets = VGroup(
            mono("{q0,q1,q3}", 16, MUTED).next_to(a, DOWN, buff=0.1),
            mono("{q2}", 16, MUTED).next_to(b, RIGHT, buff=0.1),
            mono("{q4}", 16, MUTED).next_to(c, RIGHT, buff=0.1),
        )
        self.play(ReplacementTransform(closure, a), run_time=0.65)
        self.play(Create(dfa_edges), FadeIn(b), FadeIn(c), FadeIn(state_sets), run_time=1.0)

        explain = label("One set, one deterministic state", 21, "#fbbf24")
        explain.next_to(dfa_panel, DOWN, buff=0.25)
        self.play(FadeIn(explain), Indicate(VGroup(a, b, c), color=YELLOW_C, scale_factor=1.05), run_time=0.8)
        self.wait(1.0)


class MaximalMunch(PortfolioScene):
    scene_title = "Maximal-Munch Scanning"
    scene_subtitle = "Remember the last accepting state, then emit the longest lexeme"

    def construct(self):
        self.add_footer()
        self.add_heading()

        rules_panel = card(3.2, 3.85, AMBER).shift(LEFT * 4.75 + DOWN * 0.4)
        rules_title = label("Priority", 22, "#fbbf24", "BOLD").next_to(rules_panel.get_top(), DOWN, buff=0.18)
        rules = VGroup(
            mono("1  KW_IF   if", 20),
            mono("2  ID      [A-Za-z]+", 20),
            mono("3  EQ      ==", 20),
            mono("4  ASSIGN  =", 20),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(rules_panel.get_center() + DOWN * 0.18)
        self.play(FadeIn(rules_panel), FadeIn(rules_title), FadeIn(rules), run_time=0.75)

        source_panel = card(8.2, 1.35, BLUE).shift(RIGHT * 1.8 + UP * 0.7)
        source_title = label("Source tape", 18, "#93c5fd").next_to(source_panel.get_top(), DOWN, buff=0.12)
        raw = ["=", "=", " ", "i", "f", "x", " ", "i", "f"]
        display = [c if c != " " else "middot" for c in raw]
        glyphs = VGroup(*[
            mono("·" if c == "middot" else c, 36, "#57534e" if c == "middot" else WHITE)
            for c in display
        ]).arrange(RIGHT, buff=0.26).move_to(source_panel.get_center() + DOWN * 0.12)
        self.play(FadeIn(source_panel), FadeIn(source_title), Write(glyphs), run_time=0.8)

        status_panel = card(4.6, 1.35, PURPLE).shift(DOWN * 1.15)
        output_panel = card(3.65, 1.35, GREEN).shift(RIGHT * 4.35 + DOWN * 1.15)
        status = label("Start at DFA initial state", 21, "#c4b5fd").move_to(status_panel)
        output_title = label("Emitted tokens", 17, "#6ee7b7").next_to(output_panel.get_top(), DOWN, buff=0.1)
        outputs = VGroup().move_to(output_panel.get_center() + DOWN * 0.04)
        self.play(FadeIn(status_panel), FadeIn(output_panel), FadeIn(status), FadeIn(output_title), run_time=0.65)

        cursor = SurroundingRectangle(glyphs[0], color=AMBER, buff=0.12, stroke_width=4)
        self.play(Create(cursor), run_time=0.35)

        def update_status(message, color="#c4b5fd"):
            new = label(message, 20, color).move_to(status_panel)
            self.play(Transform(status, new), run_time=0.38)

        def move_cursor(index):
            new = SurroundingRectangle(glyphs[index], color=AMBER, buff=0.12, stroke_width=4)
            self.play(Transform(cursor, new), run_time=0.3)

        def emit(text_value, token, color):
            badge_box = RoundedRectangle(
                width=0.85,
                height=0.48,
                corner_radius=0.1,
                color=color,
                fill_color=color,
                fill_opacity=0.16,
            )
            lexeme = mono(text_value, 18, WHITE).move_to(badge_box)
            token_name = label(token, 13, color).next_to(badge_box, DOWN, buff=0.04)
            complete = VGroup(badge_box, lexeme, token_name)
            outputs.add(complete)
            outputs.arrange(RIGHT, buff=0.24).move_to(output_panel.get_center() + DOWN * 0.04)
            self.play(FadeIn(complete, shift=UP * 0.1), run_time=0.35)

        update_status("'=' accepted as ASSIGN", "#93c5fd")
        move_cursor(1)
        update_status("'==' accepted as EQ", "#6ee7b7")
        move_cursor(2)
        update_status("Trap on space: emit longest match", "#fbbf24")
        emit("==", "EQ", GREEN)

        move_cursor(3)
        update_status("'i' accepted as ID", "#93c5fd")
        move_cursor(4)
        update_status("'if' accepts KW_IF and ID", "#c4b5fd")
        move_cursor(5)
        update_status("'ifx' extends only ID", "#93c5fd")
        move_cursor(6)
        update_status("Trap on space: emit longest match", "#fbbf24")
        emit("ifx", "ID", BLUE)

        move_cursor(7)
        update_status("'i' accepted as ID", "#93c5fd")
        move_cursor(8)
        update_status("EOF tie: earlier rule wins", "#fbbf24")
        emit("if", "KW_IF", AMBER)
        self.play(Indicate(outputs, color=GREEN_C, scale_factor=1.04), FadeOut(cursor), run_time=0.7)
        update_status("Scanning complete", "#6ee7b7")
        self.wait(1.1)
