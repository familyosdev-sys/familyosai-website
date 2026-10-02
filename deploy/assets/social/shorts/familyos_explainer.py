from manim import *

# FamilyOS brand palette
BG = "#150E08"
GOLD = "#F4C95D"
CREAM = "#F6E7C6"
TAUPE = "#A8946E"
NAVY = "#150E08"
DARK_BROWN = "#1C1206"
PURPLE = "#8B5CF6"
GREEN = "#A3C47E"

MONO = "Menlo"

class Scene1_Title(Scene):
    def construct(self):
        self.camera.background_color = BG
        
        # Title: FamilyOS
        title = Text("FamilyOS", font_size=64, color=GOLD, font=MONO, weight=BOLD)
        title.move_to(UP * 1.5)
        
        # Tagline
        tagline = Text("Let the app do the asking.", font_size=32, color=CREAM, font=MONO)
        tagline.move_to(UP * 0.3)
        
        # Gold line
        line = Line(LEFT * 2, RIGHT * 2, color=GOLD, stroke_width=3)
        line.move_to(DOWN * 0.5)
        
        # URL
        url = Text("familyosai.com", font_size=24, color=TAUPE, font=MONO)
        url.move_to(DOWN * 1.5)
        
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)
        self.play(Create(line), run_time=0.8)
        self.play(Write(tagline), run_time=1.5)
        self.wait(0.5)
        self.play(Write(url), run_time=1.0)
        self.wait(2.0)
        self.play(FadeOut(Group(title, tagline, line, url)), run_time=0.5)


class Scene2_TheProblem(Scene):
    def construct(self):
        self.camera.background_color = BG
        
        # The reminder treadmill
        header = Text("The Reminder Treadmill", font_size=44, color=CREAM, font=MONO, weight=BOLD)
        header.move_to(UP * 2.5)
        
        self.play(Write(header), run_time=1.5)
        self.wait(0.5)
        
        # Time stamps appearing one by one
        times = [
            ("6:47 AM", "Did you pack your lunch?"),
            ("7:02 AM", "Did you brush your teeth?"),
            ("7:15 AM", "Don't forget your library book."),
            ("7:22 AM", "Where's your other shoe?"),
        ]
        
        items = VGroup()
        for i, (time, question) in enumerate(times):
            time_text = Text(time, font_size=24, color=GOLD, font=MONO)
            q_text = Text(question, font_size=22, color=TAUPE, font=MONO)
            row = VGroup(time_text, q_text).arrange(RIGHT, buff=0.3)
            row.move_to(UP * (1.0 - i * 0.8))
            items.add(row)
        
        for row in items:
            self.play(Write(row), run_time=0.8)
            self.wait(0.3)
        
        self.wait(1.0)
        
        # The truth
        line = Line(LEFT * 3, RIGHT * 3, color=GOLD, stroke_width=2)
        line.move_to(DOWN * 2.0)
        self.play(Create(line), run_time=0.5)
        
        truth = Text("You weren't hired for this job.", font_size=28, color=CREAM, font=MONO)
        truth.move_to(DOWN * 2.8)
        self.play(Write(truth), run_time=1.5)
        self.wait(2.0)
        
        self.play(FadeOut(Group(header, items, line, truth)), run_time=0.5)


class Scene3_TheSolution(Scene):
    def construct(self):
        self.camera.background_color = BG
        
        header = Text("Put something between", font_size=40, color=CREAM, font=MONO, weight=BOLD)
        header2 = Text("the ask and the relationship.", font_size=40, color=CREAM, font=MONO, weight=BOLD)
        header.move_to(UP * 2.5)
        header2.move_to(UP * 1.7)
        
        self.play(Write(header), Write(header2), run_time=2.0)
        self.wait(0.5)
        
        line = Line(LEFT * 2.5, RIGHT * 2.5, color=GOLD, stroke_width=3)
        line.move_to(UP * 0.5)
        self.play(Create(line), run_time=0.5)
        
        # Two columns
        left_title = Text("To your kid:", font_size=26, color=GOLD, font=MONO)
        left_body = Text("That's your room done\n+20 toward the pool trip", font_size=22, color=CREAM, font=MONO)
        left_col = VGroup(left_title, left_body).arrange(DOWN, buff=0.3)
        left_col.move_to(LEFT * 3.5 + DOWN * 0.8)
        
        right_title = Text("To you:", font_size=26, color=GOLD, font=MONO)
        right_body = Text("Room is done and logged.\nLeo's had a rough afternoon;\nI moved the trash to tomorrow.", font_size=20, color=TAUPE, font=MONO)
        right_col = VGroup(right_title, right_body).arrange(DOWN, buff=0.3)
        right_col.move_to(RIGHT * 3.5 + DOWN * 0.8)
        
        self.play(Write(left_col), run_time=1.5)
        self.wait(0.5)
        self.play(Write(right_col), run_time=1.5)
        self.wait(2.0)
        
        self.play(FadeOut(Group(header, header2, line, left_col, right_col)), run_time=0.5)


class Scene4_TraumaInformed(Scene):
    def construct(self):
        self.camera.background_color = BG
        
        header = Text("Built for kids who've", font_size=40, color=CREAM, font=MONO, weight=BOLD)
        header2 = Text("learned to expect the worst.", font_size=40, color=CREAM, font=MONO, weight=BOLD)
        header.move_to(UP * 2.5)
        header2.move_to(UP * 1.7)
        
        self.play(Write(header), Write(header2), run_time=2.0)
        self.wait(0.5)
        
        principles = [
            ("The rules don't move.", GOLD),
            ("Nothing earned is taken back.", GOLD),
            ("No leaderboards, no comparison.", CREAM),
            ("Low-demand mode.", GREEN),
            ("A missed day just ends.", TAUPE),
        ]
        
        items = VGroup()
        for text, color in principles:
            item = Text(text, font_size=26, color=color, font=MONO)
            items.add(item)
        
        items.arrange(DOWN, buff=0.4)
        items.move_to(DOWN * 0.5)
        
        for item in items:
            self.play(Write(item), run_time=0.8)
            self.wait(0.3)
        
        self.wait(2.0)
        self.play(FadeOut(Group(header, header2, items)), run_time=0.5)


class Scene5_Privacy(Scene):
    def construct(self):
        self.camera.background_color = BG
        
        header = Text("The AI server sits in your home.", font_size=36, color=CREAM, font=MONO, weight=BOLD)
        header2 = Text("If you run one.", font_size=34, color=GOLD, font=MONO, weight=BOLD)
        header.move_to(UP * 2.0)
        header2.move_to(UP * 1.0)
        
        self.play(Write(header), run_time=1.5)
        self.play(Write(header2), run_time=1.0)
        self.wait(0.5)
        
        line = Line(LEFT * 3, RIGHT * 3, color=GOLD, stroke_width=2)
        line.move_to(DOWN * 0.0)
        self.play(Create(line), run_time=0.5)
        
        points = [
            Text("Chore records, proof photos and chat history", font_size=22, color=TAUPE, font=MONO),
            Text("live on your own hardware — and keep working", font_size=22, color=TAUPE, font=MONO),
            Text("with no AI server reachable at all.", font_size=22, color=TAUPE, font=MONO),
            Text("Chat and photo checks use your server,", font_size=22, color=GOLD, font=MONO, weight=BOLD),
            Text("or the relay if you have none.", font_size=22, color=GOLD, font=MONO, weight=BOLD),
        ]
        
        group = VGroup(*points).arrange(DOWN, buff=0.3)
        group.move_to(DOWN * 1.8)
        
        for p in points:
            self.play(Write(p), run_time=0.8)
            self.wait(0.3)
        
        self.wait(2.0)
        self.play(FadeOut(Group(header, header2, line, group)), run_time=0.5)


class Scene6_Pricing(Scene):
    def construct(self):
        self.camera.background_color = BG
        
        header = Text("One plan.", font_size=48, color=GOLD, font=MONO, weight=BOLD)
        header2 = Text("Flat family rate.", font_size=48, color=GOLD, font=MONO, weight=BOLD)
        header3 = Text("Never per kid.", font_size=48, color=GOLD, font=MONO, weight=BOLD)
        
        header.move_to(UP * 2.5)
        header2.move_to(UP * 1.5)
        header3.move_to(UP * 0.5)
        
        self.play(Write(header), run_time=1.0)
        self.play(Write(header2), run_time=1.0)
        self.play(Write(header3), run_time=1.0)
        self.wait(0.5)
        
        line = Line(LEFT * 2.5, RIGHT * 2.5, color=GOLD, stroke_width=3)
        line.move_to(DOWN * 0.5)
        self.play(Create(line), run_time=0.5)
        
        price = Text("$19.99/mo", font_size=56, color=CREAM, font=MONO, weight=BOLD)
        price.move_to(DOWN * 1.5)
        subtitle = Text("Your whole household.", font_size=30, color=TAUPE, font=MONO)
        subtitle.move_to(DOWN * 2.5)
        
        self.play(Write(price), run_time=1.5)
        self.play(Write(subtitle), run_time=1.0)
        self.wait(2.0)
        
        self.play(FadeOut(Group(header, header2, header3, line, price, subtitle)), run_time=0.5)


class Scene7_CTA(Scene):
    def construct(self):
        self.camera.background_color = DARK_BROWN
        
        line1 = Text("You've been the reminder", font_size=40, color=CREAM, font=MONO, weight=BOLD)
        line2 = Text("long enough.", font_size=40, color=CREAM, font=MONO, weight=BOLD)
        
        line1.move_to(UP * 1.0)
        line2.move_to(UP * 0.0)
        
        self.play(Write(line1), run_time=1.5)
        self.play(Write(line2), run_time=1.0)
        self.wait(0.5)
        
        line = Line(LEFT * 2, RIGHT * 2, color=GOLD, stroke_width=3)
        line.move_to(DOWN * 1.0)
        self.play(Create(line), run_time=0.5)
        
        cta = Text("familyosai.com", font_size=36, color=GOLD, font=MONO, weight=BOLD)
        cta.move_to(DOWN * 2.0)
        self.play(Write(cta), run_time=1.0)
        self.wait(3.0)
        
        self.play(FadeOut(Group(line1, line2, line, cta)), run_time=0.5)