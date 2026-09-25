import asyncio
import pygame
from src.main import GameApp

async def main() -> None:
    pygame.init()
    app = GameApp(1280, 720, 0, False)
    
    while app.running:
        dt = app.clock.tick(60) / 1000.0
        app.handle_events()
        app.update(dt)
        app.update_draw()
        app.glitch_processor.process(app.native_surface)
        if app.screen:
            scaled = pygame.transform.scale(app.native_surface, app.screen.get_size())
            app.screen.blit(scaled, (0, 0))
            pygame.display.flip()
        await asyncio.sleep(0)

asyncio.run(main())
