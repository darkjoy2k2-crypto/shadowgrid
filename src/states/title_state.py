import os
import sys
import tempfile
import subprocess
import pygame
import cv2
from typing import Any, Optional
from src.core.state_machine import State
from src.utils.fade_controller import FadeController
from src.ui.nine_slice import NineSliceRenderer
from src.ui.font_manager import font_mgr, GREEN_TERMINAL, GREEN_BRIGHT, GREEN_DIM
from src.utils.logger import logger

class TitleState(State):
    """
    Titelbildschirm & Intro-Video Zustand für Shadowgrid.
    Phase 1: Zeigt start_screen.png, zentrierten "SHADOWGRID" Schriftzug & Start-Button.
    Phase 2: Nach Klick auf den Start-Button wird intro.mp4 abgespielt.
    Danach (oder bei Skip) startet das Hauptspiel (HUBGAME).
    Alle Phasen-Übergänge nutzen sanfte 0.5s FadeIn / FadeOut Effekte.
    """
    def __init__(self, state_machine: Any) -> None:
        super().__init__(state_machine)
        self.fade_controller = FadeController()
        self.nineslice = NineSliceRenderer()
        self.start_img: Optional[pygame.Surface] = None
        self.button_hovered = False
        
        # Modus: "START_SCREEN" oder "INTRO_VIDEO"
        self.mode = "START_SCREEN"
        
        # Video Playback Attribute
        self.video_cap: Optional[cv2.VideoCapture] = None
        self.video_sound: Optional[pygame.mixer.Sound] = None
        self.video_sound_channel: Optional[pygame.mixer.Channel] = None
        self.video_fps = 24.0
        self.video_duration = 0.0
        self.video_timer = 0.0
        self.current_video_frame_surf: Optional[pygame.Surface] = None
        self.video_fading_out = False
        self.temp_wav_path: Optional[str] = None

    def init(self) -> None:
        """Initialisiert den Titelzustand (Startbildschirm) und startet 0.5f Fade-In."""
        self.mode = "START_SCREEN"
        self._cleanup_video()
        
        # Pfad zu start_screen.png auflösen
        img_path = r"C:\Users\peter\Documents\_shadowgrid\media\images\start_screen.png"
        if not os.path.exists(img_path):
            img_path = os.path.abspath(os.path.join("media", "images", "start_screen.png"))
        if not os.path.exists(img_path):
            img_path = os.path.abspath(os.path.join("src", "gfx", "intro.png"))

        if os.path.exists(img_path):
            try:
                loaded = pygame.image.load(img_path).convert_alpha()
                self.start_img = pygame.transform.scale(loaded, (640, 360))
            except Exception as e:
                logger.error(f"Failed to load start image {img_path}: {e}")
                self.start_img = None

        if self.start_img is None:
            self.start_img = pygame.Surface((640, 360))
            self.start_img.fill((5, 12, 10))

        self.button_hovered = False
        self.fade_controller.start_fade_in(duration=0.5)

    def get_native_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        screen = pygame.display.get_surface()
        if screen and screen.get_width() > 0 and screen.get_height() > 0:
            return int(mx * 640 / screen.get_width()), int(my * 360 / screen.get_height())
        return mx // 2, my // 2

    def get_button_rect(self) -> pygame.Rect:
        w, h = 200, 32
        x = (640 - w) // 2
        y = 260
        return pygame.Rect(x, y, w, h)

    def handle_event(self, event: Any) -> None:
        if self.fade_controller.is_fading:
            return

        if self.mode == "START_SCREEN":
            native_mx, native_my = self.get_native_mouse_pos()
            btn_rect = self.get_button_rect()

            if event.type == pygame.MOUSEMOTION:
                self.button_hovered = btn_rect.collidepoint(native_mx, native_my)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_rect.collidepoint(native_mx, native_my):
                    self._start_title_fade_out()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._start_title_fade_out()

        elif self.mode == "INTRO_VIDEO":
            # Bei Klick oder Taste während des Videos -> 0.5f FadeOut & Video überspringen
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                if not self.video_fading_out:
                    self._start_video_fade_out()

    def _start_title_fade_out(self) -> None:
        sound_manager = self.sm.context.get("sound_manager")
        if sound_manager:
            sound_manager.play_spatial("hack_success", 320, 180, 320, 180, base_volume=0.8)
        self.fade_controller.start_fade_out(duration=0.5, on_complete=self._start_intro_video)

    def _start_intro_video(self) -> None:
        """Wird aufgerufen, wenn das Startbild zu 100% ausgedunkelt ist (FadeOut done)."""
        self.mode = "INTRO_VIDEO"
        self.video_fading_out = False
        self.video_timer = 0.0
        self.current_video_frame_surf = None
        
        video_path = r"C:\Users\peter\Documents\_shadowgrid\media\video\intro.mp4"
        if not os.path.exists(video_path):
            video_path = os.path.abspath(os.path.join("media", "video", "intro.mp4"))

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}. Skipping directly to game.")
            self._on_video_fade_out_done()
            return

        try:
            self.video_cap = cv2.VideoCapture(video_path)
            if not self.video_cap.isOpened():
                logger.error(f"Could not open video {video_path}")
                self._on_video_fade_out_done()
                return

            fps = self.video_cap.get(cv2.CAP_PROP_FPS)
            total_frames = self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.video_fps = fps if fps > 0 else 24.0
            self.video_duration = (total_frames / self.video_fps) if total_frames > 0 else 10.0

            # Audio aus Video extrahieren (falls vorhanden)
            self._prepare_video_audio(video_path)

        except Exception as e:
            logger.error(f"Error opening intro video: {e}")
            self._on_video_fade_out_done()
            return

        # Start 0.5f Fade-In für Video
        self.fade_controller.start_fade_in(duration=0.5)

        # Audio abspielen
        if self.video_sound:
            try:
                self.video_sound_channel = pygame.mixer.find_channel()
                if self.video_sound_channel:
                    self.video_sound_channel.play(self.video_sound)
            except Exception as e:
                logger.warning(f"Failed to play video audio: {e}")

    def _prepare_video_audio(self, video_path: str) -> None:
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            self.temp_wav_path = os.path.join(tempfile.gettempdir(), 'shadowgrid_intro_audio.wav')
            res = subprocess.run([exe, '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', self.temp_wav_path], capture_output=True)
            if os.path.exists(self.temp_wav_path) and os.path.getsize(self.temp_wav_path) > 0:
                self.video_sound = pygame.mixer.Sound(self.temp_wav_path)
        except Exception as e:
            logger.warning(f"Video audio extraction failed: {e}")

    def _start_video_fade_out(self) -> None:
        if self.video_fading_out:
            return
        self.video_fading_out = True
        if self.video_sound_channel:
            try:
                self.video_sound_channel.fadeout(500)
            except Exception:
                pass
        self.fade_controller.start_fade_out(duration=0.5, on_complete=self._on_video_fade_out_done)

    def _on_video_fade_out_done(self) -> None:
        self._cleanup_video()
        self.sm.change_state("HUBGAME")

    def _cleanup_video(self) -> None:
        if self.video_cap:
            try:
                self.video_cap.release()
            except Exception:
                pass
            self.video_cap = None
        if self.video_sound_channel:
            try:
                self.video_sound_channel.stop()
            except Exception:
                pass
            self.video_sound_channel = None
        self.video_sound = None
        if self.temp_wav_path and os.path.exists(self.temp_wav_path):
            try:
                os.remove(self.temp_wav_path)
            except Exception:
                pass
            self.temp_wav_path = None

    def update(self, dt: float) -> None:
        self.fade_controller.update(dt)

        if self.mode == "START_SCREEN":
            native_mx, native_my = self.get_native_mouse_pos()
            self.button_hovered = self.get_button_rect().collidepoint(native_mx, native_my)

        elif self.mode == "INTRO_VIDEO":
            if self.video_cap and self.video_cap.isOpened():
                self.video_timer += dt
                target_frame = int(self.video_timer * self.video_fps)

                curr_frame_idx = int(self.video_cap.get(cv2.CAP_PROP_POS_FRAMES))
                ret = True
                while curr_frame_idx <= target_frame and ret:
                    ret, frame = self.video_cap.read()
                    curr_frame_idx += 1
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, _ = frame_rgb.shape
                        raw_surf = pygame.image.frombuffer(frame_rgb.tobytes(), (w, h), 'RGB')
                        self.current_video_frame_surf = pygame.transform.scale(raw_surf, (640, 360))

                if not ret or self.video_timer >= self.video_duration:
                    if not self.video_fading_out:
                        self._start_video_fade_out()

    def update_draw(self) -> None:
        surface = self.sm.context.get("native_surface")
        if not surface:
            return

        if self.mode == "START_SCREEN":
            # 1. Hintergrundeigenschaften (start_screen.png)
            if self.start_img:
                surface.blit(self.start_img, (0, 0))
            else:
                surface.fill((5, 12, 10))

            # Ambient Dark Layer für bessere Lesbarkeit von Schrift und UI
            dark_dim = pygame.Surface((640, 360), pygame.SRCALPHA)
            dark_dim.fill((0, 10, 8, 140))
            surface.blit(dark_dim, (0, 0))

            # 2. Centered Big Title: "SHADOWGRID"
            title_base = font_mgr.render("SHADOWGRID", color=GREEN_BRIGHT, size="large")
            tw = title_base.get_width() * 2
            th = title_base.get_height() * 2
            title_big = pygame.transform.scale(title_base, (tw, th))
            title_x = (640 - tw) // 2
            title_y = 110

            # Titel-Schatten & Glow Effect
            glow_surf = pygame.transform.scale(font_mgr.render("SHADOWGRID", color=(0, 120, 60), size="large"), (tw + 4, th + 4))
            surface.blit(glow_surf, (title_x - 2, title_y - 2))
            surface.blit(title_big, (title_x, title_y))

            # Subtitle / OS Version Tagline
            sub = font_mgr.render("SYSTEM KERNEL // CYBERDECK OS v4.2", color=GREEN_DIM, size="tiny")
            surface.blit(sub, ((640 - sub.get_width()) // 2, title_y + th + 8))

            # 3. Interactive Button: "ENTER SHADOWGRID"
            btn_rect = self.get_button_rect()
            btn_panel = self.nineslice.render(25, 4)
            surface.blit(btn_panel, (btn_rect.x, btn_rect.y))

            if self.button_hovered:
                pygame.draw.rect(surface, GREEN_BRIGHT, btn_rect, 1)
                btn_txt = font_mgr.render("[ ENTER SHADOWGRID ]", color=GREEN_BRIGHT, size="small")
            else:
                pygame.draw.rect(surface, (0, 150, 100), btn_rect, 1)
                btn_txt = font_mgr.render("ENTER SHADOWGRID", color=GREEN_TERMINAL, size="small")

            btn_txt_x = btn_rect.x + (btn_rect.width - btn_txt.get_width()) // 2
            btn_txt_y = btn_rect.y + (btn_rect.height - btn_txt.get_height()) // 2
            surface.blit(btn_txt, (btn_txt_x, btn_txt_y))

        elif self.mode == "INTRO_VIDEO":
            if self.current_video_frame_surf:
                surface.blit(self.current_video_frame_surf, (0, 0))
            else:
                surface.fill((0, 0, 0))

        # 4. Fade Overlay (Fade-In / Fade-Out über alle Phasen)
        self.fade_controller.draw_overlay(surface)
