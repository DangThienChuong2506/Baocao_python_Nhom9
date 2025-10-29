import os
import pygame

# Simple sound manager for map music.
# Usage:
#   from core import sound
#   sound.init()            # after pygame.init()
#   sound.set_map(1)        # switch music for map index 1

_music_map = {
    # map index -> audio path
    # Map indices: some code uses 0 for the first background (assets/maps/background.png),
    # so include both 0 and 1 mapping to the same music file for compatibility.
    0: os.path.join('assets', 'sounds', 'soundmap', 'soundmap1.mp3'),
    1: os.path.join('assets', 'sounds', 'soundmap', 'soundmap1.mp3'),
    2: os.path.join('assets', 'sounds', 'soundmap', 'soundmap2.mp3'),
    3: os.path.join('assets', 'sounds', 'soundmap', 'soundmap3.mp3')
}

class SoundManager:
    def __init__(self):
        self.current_map = None
        self._initialized = False
        self._muted = False
        self._volume = 0.7
        # Try to initialize the mixer; caller should call init() after pygame.init()
        try:
            pygame.mixer.init()
            self._initialized = True
            pygame.mixer.music.set_volume(self._volume)
        except Exception:
            # mixer may fail in headless or missing backend environments
            self._initialized = False

    def set_map(self, map_index):
        """Set the currently playing map music. If same map, no-op.
        If a track is configured for the map, it will be played in a loop.
        If no track, playback is stopped.
        """
        if not self._initialized:
            # attempt again lazily
            try:
                pygame.mixer.init()
                pygame.mixer.music.set_volume(self._volume)
                self._initialized = True
            except Exception:
                self._initialized = False
                return
        if map_index == self.current_map:
            return
        self.current_map = map_index
        path = _music_map.get(map_index)
        if path and os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                # Use -1 to loop forever
                pygame.mixer.music.play(loops=-1)
            except Exception:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
        else:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def stop(self):
        if not self._initialized:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass


# module-level singleton
_manager = None

def init():
    global _manager
    if _manager is None:
        _manager = SoundManager()
    return _manager


def set_map(map_index):
    if _manager is None:
        init()
    try:
        _manager.set_map(map_index)
    except Exception:
        pass


def stop():
    if _manager is None:
        return
    try:
        _manager.stop()
    except Exception:
        pass


# Simple SFX support (short sounds played on events)
_sfx_map = {
    # Map skill keys to file paths. Q and E share the same file as requested.
    'Q': os.path.join('assets', 'sounds', 'soundplayer', 'Q,E skill.mp3'),
    'E': os.path.join('assets', 'sounds', 'soundplayer', 'Q,E skill.mp3'),
    'F': os.path.join('assets', 'sounds', 'soundplayer', 'F skill.mp3'),
    'R': os.path.join('assets', 'sounds', 'soundplayer', 'R skill.mp3'),
}

# Cache loaded pygame.mixer.Sound objects
_sfx_cache = {}

def play_sfx(path):
    """Play a short sound effect given a filesystem path. Safe no-op if mixer not available."""
    try:
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                return
        snd = _sfx_cache.get(path)
        if snd is None:
            if not os.path.exists(path):
                return
            try:
                snd = pygame.mixer.Sound(path)
                _sfx_cache[path] = snd
            except Exception:
                return
        try:
            snd.play()
        except Exception:
            pass
    except Exception:
        return

def play_skill(key):
    """Play configured skill sound for key in {'Q','E','F','R'}."""
    try:
        path = _sfx_map.get(key.upper())
        if not path:
            return
        play_sfx(path)
    except Exception:
        pass


def play_next_map():
    """Play the one-shot 'next map' sound effect when maps change."""
    try:
        path = os.path.join('assets', 'sounds', 'soundmap', 'soundnextmap.mp3')
        play_sfx(path)
    except Exception:
        pass


def play_game_lose():
    """Play the game-over / lose sound once.

    Path: assets/sounds/sound win_lose/GameLose.mp3
    """
    try:
        path = os.path.join('assets', 'sounds', 'sound win_lose', 'GameLose.mp3')
        play_sfx(path)
    except Exception:
        pass


def play_game_win():
    """Play the game-win / victory sound once.

    Path: assets/sounds/sound win_lose/GameWin.mp3
    """
    try:
        path = os.path.join('assets', 'sounds', 'sound win_lose', 'GameWin.mp3')
        play_sfx(path)
    except Exception:
        pass


def restart_map(map_index=None):
    """Force-restart the music for a given map index (or current manager map if None).

    This reloads the track and starts playback from the beginning even if it's the same map.
    Safe no-op if mixer not available or file missing.
    """
    try:
        if _manager is None:
            init()
        if _manager is None:
            return
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                return
        idx = map_index if map_index is not None else _manager.current_map
        path = _music_map.get(idx)
        if not path or not os.path.exists(path):
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops=-1)
            _manager.current_map = idx
        except Exception:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
    except Exception:
        return


def play_jump():
    """Play the player's jump sound once.

    Path: assets/sounds/soundplayer/jump.mp3
    """
    try:
        path = os.path.join('assets', 'sounds', 'soundplayer', 'jump.mp3')
        play_sfx(path)
    except Exception:
        pass


_walk_channel = None

def play_walk_start():
    """Start looping the walking/footstep sound until stopped.

    This will attempt to play assets/sounds/soundplayer/walk.mp3 in a loop. If the mixer
    isn't available or the file doesn't exist, this is a safe no-op.
    """
    global _walk_channel
    try:
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                return
        path = os.path.join('assets', 'sounds', 'soundplayer', 'walk.mp3')
        if not os.path.exists(path):
            return
        # Load sound into cache if needed
        snd = _sfx_cache.get(path)
        if snd is None:
            try:
                snd = pygame.mixer.Sound(path)
                _sfx_cache[path] = snd
            except Exception:
                return
        # If already playing on a reserved channel, do nothing
        try:
            if _walk_channel is not None and _walk_channel.get_busy():
                return
        except Exception:
            _walk_channel = None
        try:
            # play looped (-1) and reserve channel reference
            _walk_channel = snd.play(loops=-1)
        except Exception:
            _walk_channel = None
    except Exception:
        return


def play_walk_stop():
    """Stop the looping walking/footstep sound if it's playing."""
    global _walk_channel
    try:
        if _walk_channel is not None:
            try:
                _walk_channel.stop()
            except Exception:
                pass
        _walk_channel = None
    except Exception:
        _walk_channel = None
        return
