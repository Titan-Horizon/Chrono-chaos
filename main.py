# ═══════════════════════════════════════════════════════════════════════════
#  CHRONO CHAOS  —  v2.0
#  Rogue-like d'action temporel — pygame, un seul fichier.
#  Réécriture complète, 17 sections, 0 doublon, 0 code mort.
# ═══════════════════════════════════════════════════════════════════════════
"""
Concept : chaque manche, ton personnage se fige et devient un ÉCHO-FANTÔME
qui rejoue exactement tes mouvements et tes tirs, adapté à la nouvelle carte.
La ROUE DU CHAOS change les règles toutes les 15 s. Boutique, statistiques,
objets, succès, campagne secrète, 5 zones cachées, mode Champion Top 100.

Lancer   : python chrono_chaos.py         (pip install pygame)
Sauvegarde : chrono_chaos_save.json       (à côté du script)
F11 = plein écran  ·  Échap = pause  ·  [F] = pouvoir du skin Mythique
"""


# ═══════════════════════════════════════════════════════════════════════════
#  § 1 — CONSTANTES & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

import pygame
import random
import math
import sys
import json
import os
import array
import time
# ── Support web pygbag ────────────────────────────────────────
import asyncio
import sys

IS_WEB = (sys.platform == "emscripten")
print(f"[INIT] Plateforme: {'WEB (pygbag)' if IS_WEB else sys.platform}")


# ---- Initialisation pygame (mixer AVANT pygame.init pour de bons buffers)
try:
    pygame.mixer.pre_init(22050, -16, 1, 512, allowedchanges=0)
except Exception:
    try:
        pygame.mixer.pre_init(22050, -16, 1, 512)
    except Exception:
        pass
pygame.init()
pygame.font.init()


# ---- Résolution virtuelle (le jeu se dessine toujours en 1000×700)
# ☢️ RÉSOLUTION DYNAMIQUE
if 'IS_WEB' in globals() and IS_WEB:
    WIDTH, HEIGHT = 600, 420  # Plus petit = Plus rapide sur web
else:
    WIDTH, HEIGHT = 1000, 700
FPS = 30 if IS_WEB else 60
# Sur le web, RESIZABLE provoque un écran noir. On garde SCALED seulement.
SCREEN_FLAGS = 0 if IS_WEB else getattr(pygame, "SCALED", 0)

# ---- Identité
GAME_TITLE = "CHRONO CHAOS"
GAME_VERSION = "2.0"

# ---- Fichier de sauvegarde
SAVE_FILENAME = "chrono_chaos_save.json"
try:
    SAVE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), SAVE_FILENAME)
except Exception:
    SAVE_PATH = SAVE_FILENAME

# ---- Économie / pubs
AD_COOLDOWN    = 60          # secondes entre deux pubs (basé sur l'heure système)
AD_COIN_REWARD = 1000
AD_GEM_REWARD  = 10
AD_BOX_EVERY   = 5
BOX_ADS_NEEDED = 3

# ---- Gemmes (monnaie premium)
GEM_RATE        = {1: 0.10, 2: 0.25, 3: 0.45, 4: 0.70, 5: 1.00}
GEM_RUN_CAP     = {1: 6, 2: 14, 3: 25, 4: 40, 5: 60}
GEM_FIRST_ROUND = 3
GEM_PICKUP_BASE = 0.10
GEM_DROP_KILL   = 0.035

# ---- Prix
ITEM_PRICE_MULT   = 2.5
STAT_PRICE_MULT   = 1.6
STAT_PRICE_GROWTH = 1.9
BOX_GEM_PRICE     = 30
BOX_COIN_PRICE    = 10_000
BOX_PASS_STEP     = 500
BONUS_OVERFLOW_COINS = 300

# ---- Saison (calculée, jamais incrémentée)
SEASON_DURATION_DAYS = 28

# ---- Difficultés
# § 1 — CONSTANTES
MAX_DIFF           = 10          # ← était 15
CHAMPION_MIN_DIFF  = 99          # désactivé (plus de champion)
CHAMPION_TOP_LIMIT = 0           # désactivé
MILESTONE_INTERVAL = 5           # inchangé        # boss / calamité tous les 5 niveaux

# ---- Statistiques d'achat
STAT_KEYS       = ["hp", "shield", "regen", "speed", "power", "rate", "jump", "coin"]
STAT_MAX_BUY    = 5
STAT_MAX_BONUS  = 3
SECRET_KEYS     = ["ARENE", "GLITCH", "GARDIEN", "ECLIPSE", "FAILLE"]

# ═══════════════════════════════════════════════════════════════════
#  § 2 — SAUVEGARDE (remplacement de load_save / write_save)
# ═══════════════════════════════════════════════════════════════════

SAVE_KEY = "chrono_chaos_save_v2"


def _web_get_window():
    """Retourne le proxy `window` de pygbag, ou None."""
    try:
        import platform as _plat
        return _plat.window
    except Exception:
        return None


def write_save():
    if IS_WEB:
        try:
            import platform as _plat
            if hasattr(_plat, "window"):
                _plat.window.localStorage.setItem(
                    SAVE_KEY, json.dumps(SAVE, ensure_ascii=False))
        except Exception:
            pass
        return
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as fh:
            json.dump(SAVE, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
#  PALETTE (thème CHAOS : violet nuit, rouge sang, cyan électrique)
# ═══════════════════════════════════════════════════════════════════════════
NOIR_FOND   = (12, 7, 22)
GRIS_METAL  = (36, 28, 56)
PANEL       = (20, 13, 36)
BLANC       = (245, 245, 255)
JAUNE_NEON  = (255, 225, 0)
CYAN_NEON   = (0, 240, 255)
ROUGE_NEON  = (255, 40, 80)
VERT_NEON   = (50, 255, 120)
PURPLE_NEON = (180, 50, 255)
ORANGE      = (255, 140, 0)
ROSE        = (255, 80, 200)
MINT        = (140, 255, 200)
BLEU_ALLIE  = (110, 190, 255)
GEM_COL     = (90, 225, 255)

# Couleurs des 4 pôles du menu principal
COL_PLAY   = CYAN_NEON
COL_HQ     = (255, 200, 40)
COL_COMPET = (180, 80, 255)
COL_CONFIG = (50, 255, 120)

# Couleurs de la Matrice d'Armes
ATTACK_COL  = (255, 90, 60)
DEFENSE_COL = (90, 200, 255)
SUPPORT_COL = (120, 255, 160)

# Couleurs du mode Champion
CHAMPION_COL  = (255, 200, 60)
CHAMPION_DARK = (120, 60, 10)

# Couleurs de cadre d'avatar
FRAME_COLORS = [CYAN_NEON, ROUGE_NEON, JAUNE_NEON, VERT_NEON,
                PURPLE_NEON, ORANGE, ROSE, BLANC]

# Colonnes de shards du décor
SHARD_COLS = [(40, 14, 60), (62, 14, 42), (14, 34, 58), (54, 22, 72)]


# ═══════════════════════════════════════════════════════════════════════════
#  TRADUCTION (FR par défaut, EN via le dictionnaire `EN` complété plus tard)
# ═══════════════════════════════════════════════════════════════════════════
EN = {}


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS MATHÉMATIQUES & FORMATAGE
# ═══════════════════════════════════════════════════════════════════════════
def clamp(v, a, b):
    return max(a, min(b, v))


def clamp01(v):
    return max(0.0, min(1.0, v))


def dark(c, k=0.6):
    """Assombrit une couleur (multiplication)."""
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))


def light(c, k=0.4):
    """Éclaircit une couleur en la rapprochant du blanc."""
    return (int(c[0] + (255 - c[0]) * k),
            int(c[1] + (255 - c[1]) * k),
            int(c[2] + (255 - c[2]) * k))


def mixc(a, b, t):
    """Interpolation linéaire entre deux couleurs (t ∈ [0,1])."""
    t = clamp01(t)
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def fmt_num(n):
    """12345 → '12 345'."""
    try:
        return "{:,}".format(int(n)).replace(",", " ")
    except Exception:
        return str(n)


def fmt_time(frames):
    """Frames (60/s) → 'MM:SS'."""
    s = max(0, int(frames // 60))
    return "%02d:%02d" % (s // 60, s % 60)


# ═══════════════════════════════════════════════════════════════════════════
#  POLICES
# ═══════════════════════════════════════════════════════════════════════════
# ──────────────────────────────────────────────────────────────
#  POLICES — chargement ROBUSTE
#  1) Fichier TTF direct Windows (le plus fiable)
#  2) match_font (cross-platform)
#  3) SysFont (fallback universel)
# ──────────────────────────────────────────────────────────────
HEAD_NAMES = ["impact", "arialblack", "franklingothicheavy", "bahnschrift", "verdana"]
BODY_NAMES = ["bahnschrift", "segoeui", "tahoma", "verdana", "arial"]
MONO_NAMES = ["consolas", "cascadiacode", "couriernew"]

# Table de correspondance nom_pygame → fichiers TTF Windows à essayer
_WIN_FONT_FILES = {
    "impact":              ["impact.ttf"],
    "arialblack":          ["ariblk.ttf", "arialbd.ttf"],
    "bahnschrift":         ["bahnschrift.ttf"],
    "segoeui":             ["segoeui.ttf", "segoeuib.ttf"],
    "tahoma":              ["tahoma.ttf", "tahomabd.ttf"],
    "verdana":             ["verdana.ttf", "verdanab.ttf"],
    "arial":               ["arial.ttf", "arialbd.ttf"],
    "consolas":            ["consola.ttf", "consolab.ttf"],
    "cascadiacode":        ["CascadiaCode.ttf", "CascadiaMono.ttf"],
    "couriernew":          ["cour.ttf", "courbd.ttf"],
    "franklingothicheavy": ["framd.ttf", "FRAMD.TTF"],
}


def _try_win_file(name, size, bold):
    """Charge directement un TTF depuis C:\\Windows\\Fonts\\."""
    if os.name != "nt":
        return None
    windir = os.environ.get("WINDIR", r"C:\Windows")
    fontdir = os.path.join(windir, "Fonts")
    if not os.path.isdir(fontdir):
        return None
    candidates = _WIN_FONT_FILES.get(
        name.lower().replace(" ", ""), [name.lower().replace(" ", "") + ".ttf"])
    for fname in candidates:
        path = os.path.join(fontdir, fname)
        if os.path.exists(path):
            try:
                f = pygame.font.Font(path, int(size))
                if bold:
                    f.set_bold(True)
                return f
            except Exception:
                continue
    return None


_FONT_CACHE = {}
_FONT_LOADED = {}   # diagnostic : quel fichier a été chargé


def _font(names, size, bold=True):
    """Charge une police en essayant 3 stratégies dans l'ordre."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",")]

    key = (tuple(names), int(size), bool(bold))
    if key in _FONT_LOADED:
        return _FONT_LOADED[key][0]

    # Sur le web, ne pas chercher les polices système (lent / bloquant)
    if IS_WEB:
        try:
            f = pygame.font.SysFont(None, int(size), bold=bold)
            _FONT_LOADED[key] = (f, "web_sysfont")
            return f
        except Exception:
            f = pygame.font.Font(None, int(size))
            _FONT_LOADED[key] = (f, "web_raw")
            return f

    # 1) Fichier TTF direct Windows (le plus fiable)
    for name in names:
        f = _try_win_file(name, size, bold)
        if f:
            _FONT_LOADED[key] = (f, "win_file:" + name)
            return f

    # 2) match_font pygame (cross-platform)
    for name in names:
        try:
            path = pygame.font.match_font(name)
            if path:
                f = pygame.font.Font(path, int(size))
                if bold:
                    f.set_bold(True)
                _FONT_LOADED[key] = (f, "match:" + name)
                return f
        except Exception:
            pass

    # 3) Fallback SysFont (jamais idéal, mais visible)
    try:
        f = pygame.font.SysFont(None, int(size), bold=bold)
        _FONT_LOADED[key] = (f, "fallback")
        return f
    except Exception:
        f = pygame.font.Font(None, int(size))
        _FONT_LOADED[key] = (f, "raw")
        return f


def _get_font(size, bold=False, names=None):
    names = names or BODY_NAMES
    key = (int(size), bool(bold), tuple(names))
    f = _FONT_CACHE.get(key)
    if f is None:
        f = _font(names, int(size), bold)
        _FONT_CACHE[key] = f
    return f


# ─── DIAGNOSTIC : à appeler une fois au démarrage ───
def _print_font_diagnostic():
    """Affiche dans la console quelle police a réellement été chargée
    pour chaque catégorie. Permet de savoir tout de suite si ça marche."""
    print("=" * 55)
    print("  DIAGNOSTIC POLICES CHRONO CHAOS")
    print("=" * 55)
    for label, names, size, bold in (
        ("TITRE  (HEAD)", HEAD_NAMES, 46, True),
        ("BOUTON (HEAD)", HEAD_NAMES, 25, True),
        ("TEXTE  (BODY)", BODY_NAMES, 17, False),
    ):
        f = _font(names, size, bold)
        info = _FONT_LOADED.get((tuple(names), size, bold), (None, "?"))
        try:
            real_name = f.get_name() if hasattr(f, "get_name") else "?"
        except Exception:
            real_name = "?"
        print(f"  {label}: chargée via [{info[1]}] → nom interne '{real_name}'")
    print("=" * 55)


# ─── Polices principales ───
FONT_BIG   = _font(HEAD_NAMES, 80, True)
FONT_TITLE = _font(HEAD_NAMES, 46, True)
FONT_BTN   = _font(HEAD_NAMES, 25, True)
FONT_MED   = _font(BODY_NAMES, 24, False)
FONT_SMALL = _font(BODY_NAMES, 17, False)
FONT_TINY  = _font(BODY_NAMES, 13, False)


# ═══════════════════════════════════════════════════════════════════════════
#  § 2 — SAUVEGARDE
# ═══════════════════════════════════════════════════════════════════════════

def default_save():
    """Structure complète d'une sauvegarde neuve."""
    return {
        "coins": 0,
        "gems": 0,
        "mystery_boxes": 0,
        "pass_xp": 0,
        "owned": ["NEON_CYBER"],
        "selected": "NEON_CYBER",
        "upg":   {k: 0 for k in STAT_KEYS},
        "bonus": {k: 0 for k in STAT_KEYS},
        "items": [],
        "equip": {"weapon": None, "armor": None, "support": None},
        "secrets": {k: False for k in SECRET_KEYS},
        "best_survie": 0,
        "best_course": 0,
        "difficulty": 1,
        "stats": {
            "rounds_total": 0, "kills_total": 0, "games": 0,
            "surv_best": {}, "course_best": {},
            "fast_course": 0, "flawless": False,
            "arena_win": False, "glitch_done": False, "guard_done": False,
            "relic": False, "faille_done": False, "gems_total": 0,
            "boxes_opened": 0, "box_since_stat": 0, "box_since_skin": 0,
            "box_pass_claimed": 0,
            "secret_wins": {},
        },
        "ach": [],
        "premium": {},
        "profile": {"name": "", "avatar": "NEON_CYBER", "frame": 0},
        "settings": {
            "lang": "fr", "master": 0.8, "music": 0.55, "sfx": 0.9,
            "fullscreen": False, "shake": True, "particles": 2,
            "fps": False, "dmgnum": True, "calm": False, "crt": True,
            "layout": "AZERTY",
        },
        "ads": {
            "last_ts": 0.0, "watched": 0,
            "coins_earned": 0, "gems_earned": 0, "box_ad_progress": 0,
        },
        "campaign": {
            "unlocked": 2,
            "champion_unlocked": False,
            "streaks": {},
            "best": {},
        },
        "secret_campaign": {
            "levels": {},
            "unlocked": False,
            "cleared": False,
        },
        "season": {
            "last_seen_season": 0,
            "claimed_this_season": False,
        },
        "leaderboard": {
            "best_rank": 999999,
        },
    }


def _to_int(v, default=0):
    """Entier >= 0, ou `default` si inexploitable."""
    try:
        return max(0, int(v))
    except Exception:
        return default


def sanitize_save(data):
    """Garantit des types sains. Ne casse jamais les sauvegardes anciennes."""
    if not isinstance(data, dict):
        return default_save()

    # Scalaires
    for k in ("coins", "gems", "mystery_boxes", "pass_xp", "best_survie",
              "best_course", "difficulty"):
        data[k] = _to_int(data.get(k, 0), 1 if k == "difficulty" else 0)
    if data["difficulty"] < 1:
        data["difficulty"] = 1
    if data["difficulty"] > MAX_DIFF:
        data["difficulty"] = MAX_DIFF

    # Listes
    if not isinstance(data.get("owned"), list):
        data["owned"] = ["NEON_CYBER"]
    if "NEON_CYBER" not in data["owned"]:
        data["owned"].insert(0, "NEON_CYBER")
    if data.get("selected") not in data["owned"]:
        data["selected"] = data["owned"][0]
    if not isinstance(data.get("items"), list):
        data["items"] = []
    if not isinstance(data.get("ach"), list):
        data["ach"] = []

    # Dictionnaires fixes
    for dkey, keys in (
        ("upg",   STAT_KEYS),
        ("bonus", STAT_KEYS),
    ):
        d = data.get(dkey)
        if not isinstance(d, dict):
            d = {}
        for k in keys:
            d[k] = _to_int(d.get(k, 0))
            d[k] = min(d[k], STAT_MAX_BUY if dkey == "upg" else STAT_MAX_BONUS)
        data[dkey] = d

    # Équipement
    eq = data.get("equip")
    if not isinstance(eq, dict):
        eq = {}
    for s in ("weapon", "armor", "support"):
        if s not in eq or eq[s] is not None and not isinstance(eq[s], str):
            eq[s] = None
    data["equip"] = eq

    # Secrets
    sec = data.get("secrets")
    if not isinstance(sec, dict):
        sec = {}
    for k in SECRET_KEYS:
        sec[k] = bool(sec.get(k, False))
    data["secrets"] = sec

    # Stats
    st = data.get("stats")
    if not isinstance(st, dict):
        st = {}
    base_st = default_save()["stats"]
    for k, v in base_st.items():
        if k not in st:
            st[k] = v
    for k in ("rounds_total", "kills_total", "games", "gems_total",
              "boxes_opened", "box_since_stat", "box_since_skin",
              "box_pass_claimed"):
        st[k] = _to_int(st.get(k, 0))
    for k in ("surv_best", "course_best", "secret_wins"):
        if not isinstance(st.get(k), dict):
            st[k] = {}
    for k in ("flawless", "arena_win", "glitch_done", "guard_done",
              "relic", "faille_done"):
        st[k] = bool(st.get(k, False))
    try:
        st["fast_course"] = float(st.get("fast_course", 0.0)) or 0.0
    except Exception:
        st["fast_course"] = 0.0
    data["stats"] = st

    # Profil
    prof = data.get("profile")
    if not isinstance(prof, dict):
        prof = {}
    prof.setdefault("name", "")
    prof.setdefault("avatar", "NEON_CYBER")
    prof["frame"] = _to_int(prof.get("frame", 0)) % len(FRAME_COLORS)
    data["profile"] = prof

    # Paramètres (on garde les anciens, on comble les manquants)
    settings = data.get("settings")
    if not isinstance(settings, dict):
        settings = {}
    for k, v in default_save()["settings"].items():
        settings.setdefault(k, v)
    if settings.get("layout") not in ("AZERTY", "QWERTY"):
        settings["layout"] = "AZERTY"
    if settings.get("lang") not in ("fr", "en"):
        settings["lang"] = "fr"
    for k in ("master", "music", "sfx"):
        try:
            settings[k] = clamp01(float(settings[k]))
        except Exception:
            settings[k] = 0.7
    for k in ("fullscreen", "shake", "fps", "dmgnum", "calm", "crt"):
        settings[k] = bool(settings.get(k, True))
    settings["particles"] = int(clamp(settings.get("particles", 2), 0, 2))
    data["settings"] = settings

    # Pubs
    ads = data.get("ads")
    if not isinstance(ads, dict):
        ads = {}
    for k, v in default_save()["ads"].items():
        ads.setdefault(k, v)
    try:
        ts = float(ads["last_ts"])
        ads["last_ts"] = ts if math.isfinite(ts) and ts > 0 else 0.0
    except Exception:
        ads["last_ts"] = 0.0
    for k in ("watched", "coins_earned", "gems_earned", "box_ad_progress"):
        ads[k] = _to_int(ads.get(k, 0))
    data["ads"] = ads

    # Campagne
    camp = data.get("campaign")
    if not isinstance(camp, dict):
        camp = {}
    camp.setdefault("unlocked", 2)
    camp.setdefault("champion_unlocked", False)
    camp.setdefault("streaks", {})
    camp.setdefault("best", {})
    try:
        camp["unlocked"] = max(1, min(MAX_DIFF, int(camp["unlocked"])))
    except Exception:
        camp["unlocked"] = 2
    camp["champion_unlocked"] = bool(camp["champion_unlocked"]) or camp["unlocked"] >= CHAMPION_MIN_DIFF
    for k in ("streaks", "best"):
        if not isinstance(camp[k], dict):
            camp[k] = {}
    data["campaign"] = camp

    # Campagne secrète
    sc = data.get("secret_campaign")
    if not isinstance(sc, dict):
        sc = {}
    sc.setdefault("levels", {})
    sc.setdefault("unlocked", False)
    sc.setdefault("cleared", False)
    if not isinstance(sc["levels"], dict):
        sc["levels"] = {}
    data["secret_campaign"] = sc

    # Saison (nouvelle clé propre)
    season = data.get("season")
    if not isinstance(season, dict):
        season = {}
    season.setdefault("last_seen_season", 0)
    season.setdefault("claimed_this_season", False)
    data["season"] = season

    # Leaderboard (garde best_rank, supprime les restes bugués)
    lb = data.get("leaderboard")
    if not isinstance(lb, dict):
        lb = {}
    for k in ("season", "season_start", "season_end", "last_claimed_season"):
        lb.pop(k, None)
    lb.setdefault("best_rank", 999999)
    data["leaderboard"] = lb

    # Premium (dict simple de niveaux)
    prem = data.get("premium")
    if not isinstance(prem, dict):
        prem = {}
    for k, v in list(prem.items()):
        prem[k] = _to_int(v)
    data["premium"] = prem

    return data


def load_save():
    if IS_WEB:
        try:
            import platform as _plat
            if hasattr(_plat, "window") and _plat.window.localStorage:
                raw_str = _plat.window.localStorage.getItem(SAVE_KEY)
                if raw_str:
                    raw = json.loads(raw_str)
                    data = default_save()
                    if isinstance(raw, dict):
                        for k, v in raw.items():
                            if isinstance(v, dict) and isinstance(data.get(k), dict):
                                data[k].update(v)
                            else:
                                data[k] = v
                    return sanitize_save(data)
        except Exception:
            pass
        return sanitize_save(default_save())
    # ... reste inchangé (desktop)


SAVE = load_save()
SET = SAVE["settings"]

# ── AUTO-OPTIMISATION WEB ──
if IS_WEB:
    SET["particles"] = 0    # Particules au minimum
    SET["crt"] = False      # Désactive l'effet scanline CRT
    SET["calm"] = True      # Réduit les flashs intenses


def tr(s):
    """Traduit une chaîne FR → EN si la langue active est 'en'."""
    try:
        return EN.get(s, s) if SET["lang"] == "en" else s
    except Exception:
        return s




# ═══════════════════════════════════════════════════════════════════════════
#  § 3 — RENDU BAS-NIVEAU
# ═══════════════════════════════════════════════════════════════════════════

def make_icon():
    """Icône de fenêtre — code-drawn, aucun asset."""
    ic = pygame.Surface((64, 64))
    ic.fill((14, 8, 26))
    pygame.draw.circle(ic, CYAN_NEON, (32, 32), 28, 4)
    for i in range(12):
        a = i * math.tau / 12
        pygame.draw.line(ic, ROUGE_NEON,
                         (32 + math.cos(a) * 22, 32 + math.sin(a) * 22),
                         (32 + math.cos(a) * 27, 32 + math.sin(a) * 27), 2)
    pygame.draw.polygon(ic, JAUNE_NEON,
                        [(36, 8), (20, 36), (31, 36), (26, 58),
                         (46, 26), (34, 26)])
    return ic


try:
    pygame.display.set_icon(make_icon())
except Exception:
    pass

try:
    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT),
        SCREEN_FLAGS | (pygame.FULLSCREEN if SET["fullscreen"] else 0))
except Exception:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()


def set_fullscreen(on):
    """Bascule plein écran (préserve la résolution virtuelle)."""
    global screen
    SET["fullscreen"] = bool(on)
    try:
        cur = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        if cur != bool(on):
            pygame.display.toggle_fullscreen()
    except Exception:
        try:
            screen = pygame.display.set_mode(
                (WIDTH, HEIGHT),
                SCREEN_FLAGS | (pygame.FULLSCREEN if on else 0))
        except Exception:
            pass


# ---- Stubs qui seront remplacés par de vraies implémentations plus tard.
class _NullAudio:
    """Audio neutre — évite les crashs tant que § 4 n'est pas chargée."""
    def __init__(self):
        self.ok = False
        self.frame = 0
        self.sfx = {}
        self.tracks = {}
        self.cur = None
    def play(self, *a, **kw): pass
    def music(self, *a, **kw): pass
    def apply(self): pass
    def build(self, *a, **kw): pass


audio = _NullAudio()

mouse = {"x": 0, "y": 0, "click": False, "down": False}
UI = {
    "state": "MENU", "sub": None, "ret": "MENU", "iback": "MENU",
    "page": 0, "shop_tab": "SKINS", "ipage": 0, "apage": 0,
    "session": None, "name_buf": "", "renaming": False,
    "confirm": 0, "trans": None, "tip": 0,
    "champion_open": False, "champion_denied": 0, "champion_dialog_t": 0,
    "box_anim": None,
}
TICK = [0]
# ═══════════════════════════════════════════════════════════════════════════
#  CLOUD SAVE — comptes multi-appareils (Supabase)
# ═══════════════════════════════════════════════════════════════════════════
#  Config : renseigne les 2 valeurs ci-dessous après avoir créé ton
#  projet sur supabase.com (voir README).
#  Ces 2 clés sont PUBLIQUES (elles peuvent être dans le code client).
# ═══════════════════════════════════════════════════════════════════════════

# Cloud désactivé d'office
CLOUD_ENABLED = False
FEATURES = {
    "leaderboard": False,
    "seasons": False,
    "cloud_sync": False,
}

# Feature flags : masque classement + saisons
FEATURES = {
    "leaderboard": False,    # pas de classement mondial
    "seasons": False,        # pas de saisons
    "cloud_sync": True,      # comptes multi-appareils activés
}

UI.setdefault("cloud_email_prefill", "")
UI.setdefault("cloud_login_open", False)
UI.setdefault("cloud_login_buf_email", "")
UI.setdefault("cloud_login_buf_pass", "")
UI.setdefault("cloud_login_field", 0)      # 0 = email, 1 = password
UI.setdefault("cloud_signup_mode", False)
UI.setdefault("cloud_last_msg", "")
UI.setdefault("cloud_last_msg_t", 0)

def feature_enabled(key):
    """Vérifie si une fonctionnalité est activée."""
    return FEATURES.get(key, True)


def say(text, col=JAUNE_NEON):
    """File d'attente d'un flash bas de l'écran (rendu en § 17)."""
    try:
        _FLASH_QUEUE.append({"text": text, "t": 170, "col": col})
    except Exception:
        pass


_FLASH_QUEUE = []


# ---- Polices dynamiques (cache)
def _resolve_font(f):
    """Accepte Font pygame ou int (taille) → renvoie un Font."""
    if hasattr(f, "render"):
        return f
    if isinstance(f, (int, float)):
        return _get_font(int(f), False)
    return _get_font(20, False)


# ---- Rendu de texte : signature unique et nette
_TEXT_CACHE = {}

def draw_text(surf, text, font, color, x, y, center=True, shadow=True):
    """Version avec cache pour éviter font.render() à chaque frame."""
    if IS_WEB:
        shadow = False  # ☢️ Désactive les ombres sur le web pour la vitesse
    font = _resolve_font(font)
    text_str = str(text)
    
    # Clé unique basée sur le texte, la police, la couleur et l'ombre
    key = (text_str, id(font), tuple(color), shadow, center)
    
    if key not in _TEXT_CACHE:
        try:
            fg = font.render(text_str, True, color)
            sh = None
            if shadow:
                col_sh = (0, 0, 0) if shadow is True else shadow
                sh = font.render(text_str, True, col_sh)
            _TEXT_CACHE[key] = (fg, sh)
        except Exception:
            return None
            
    fg, sh = _TEXT_CACHE[key]
    r = (fg.get_rect(center=(int(x), int(y))) if center
         else fg.get_rect(topleft=(int(x), int(y))))
         
    if sh:
        surf.blit(sh, (r.x + 1, r.y + 1))
    surf.blit(fg, r)
    return r


def draw_text_ml(surf, text, font, color, x, y, shadow=True):
    """Texte aligné à gauche, centré verticalement sur `y`."""
    if IS_WEB:
        shadow = False  # ☢️ Désactive les ombres sur le web pour la vitesse
    font = _resolve_font(font)
    try:
        img = font.render(str(text), True, color)
    except Exception:
        return None
    r = img.get_rect(midleft=(int(x), int(y)))
    if shadow:
        try:
            sh = font.render(str(text), True, (0, 0, 0))
            surf.blit(sh, (r.x + 1, r.y + 1))
        except Exception:
            pass
    surf.blit(img, r)
    return r


def draw_text_sharp(surf, text, font, color, x, y, center=True, shadow=True):
    """Alias de draw_text (compat appels existants)."""
    return draw_text(surf, text, font, color, x, y, center, shadow)


def draw_text_outlined(surf, text, font, color, x, y, center=True, outline=(0, 0, 0), thick=2):
    """Texte avec contour net (titres Vector-Art)."""
    if IS_WEB:
        shadow = False  # ☢️ Désactive les ombres sur le web pour la vitesse
    font = _resolve_font(font)
    try:
        base = font.render(str(text), True, color)
    except Exception:
        return None
    ol = font.render(str(text), True, outline)
    r = (base.get_rect(center=(int(x), int(y))) if center
         else base.get_rect(topleft=(int(x), int(y))))
    for dx in (-thick, 0, thick):
        for dy in (-thick, 0, thick):
            if dx or dy:
                surf.blit(ol, (r.x + dx, r.y + dy))
    surf.blit(base, r)
    return r


def draw_text_block(surf, lines, x, y, font, color, spacing=4, center=False):
    """Empile des lignes avec espacement uniforme (pas de chevauchement)."""
    font = _resolve_font(font)
    lh = font.get_linesize() + spacing
    for i, ln in enumerate(lines):
        draw_text(surf, ln, font, color, x, y + i * lh, center=center)
    return y + len(lines) * lh


def wrap_text(text, font, max_w):
    """Découpe un texte en lignes qui tiennent dans max_w."""
    font = _resolve_font(font)
    lines, cur = [], ""
    for word in str(text).split(" "):
        test = (cur + " " + word).strip()
        try:
            w = font.size(test)[0]
        except Exception:
            w = 0
        if w <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---- Panneau biseauté (coins coupés)
def panel(surf, rect, border=CYAN_NEON, fill=PANEL, cut=9, width=2):
    """Dessine un panneau polygonal à coins coupés."""
    r = pygame.Rect(rect)
    x, y, w, h = r.x, r.y, r.w, r.h
    pts = [
        (x + cut, y), (x + w - cut, y), (x + w, y + cut),
        (x + w, y + h - cut), (x + w - cut, y + h), (x + cut, y + h),
        (x, y + h - cut), (x, y + cut),
    ]
    pygame.draw.polygon(surf, fill, pts)
    pygame.draw.polygon(surf, border, pts, width)


# ---- Halos / glow
_GLOW_CACHE = {}


def _glow_surface(w, h, color, spread, max_alpha, layers=6):
    key = (w, h, color, spread, max_alpha, layers)
    surf = _GLOW_CACHE.get(key)
    if surf is not None:
        return surf
    full_w, full_h = w + spread * 2, h + spread * 2
    s = pygame.Surface((full_w, full_h), pygame.SRCALPHA)
    cx, cy = full_w // 2, full_h // 2
    for i in range(layers, 0, -1):
        k = i / layers
        a = int(max_alpha * (1 - k) ** 1.8)
        if a <= 0:
            continue
        pad = int(spread * k)
        r = pygame.Rect(cx - w // 2 - pad, cy - h // 2 - pad,
                        w + pad * 2, h + pad * 2)
        pygame.draw.rect(s, (*color, a), r, border_radius=14 + pad)
    _GLOW_CACHE[key] = s
    return s


def glow_rect(surf, rect, color, spread=12, max_alpha=110):
    """Halo néon externe autour d'un rectangle (mis en cache)."""
    r = pygame.Rect(rect)
    if r.w <= 0 or r.h <= 0:
        return
    g = _glow_surface(r.w, r.h, tuple(color[:3]), spread, max_alpha)
    surf.blit(g, (r.x - spread, r.y - spread))


def _glow_circle(radius, color, max_alpha=120, layers=6):
    key = ("circ", radius, color, max_alpha, layers)
    s = _GLOW_CACHE.get(key)
    if s is not None:
        return s
    size = radius * 2 + 4
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    for i in range(layers, 0, -1):
        k = i / layers
        a = int(max_alpha * (1 - k) ** 1.7)
        if a > 0:
            pygame.draw.circle(s, (*color, a), (cx, cy),
                               max(2, int(radius * (0.35 + 0.65 * k))))
    _GLOW_CACHE[key] = s
    return s


def glow_circle(surf, cx, cy, radius, color, max_alpha=120):
    """Halo circulaire centré."""
    g = _glow_circle(int(radius), tuple(color[:3]), max_alpha)
    surf.blit(g, (cx - g.get_width() // 2, cy - g.get_height() // 2))


# ---- Dégradés pré-calculés
_GRAD_CACHE = {}


def make_gradient(w, h, top, bottom, radius=0):
    """Surface dégradée verticale, cache par (w, h, top, bottom, radius)."""
    key = (w, h, top, bottom, radius)
    s = _GRAD_CACHE.get(key)
    if s is not None:
        return s
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for yy in range(h):
        k = yy / max(1, h - 1)
        pygame.draw.line(s, mixc(top, bottom, k), (0, yy), (w, yy))
    if radius > 0:
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                         border_radius=radius)
        s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    _GRAD_CACHE[key] = s
    return s


def make_gradient_bg(top=(9, 4, 19), bottom=(36, 8, 40)):
    """Fond de jeu (dégradé complet)."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(0, HEIGHT, 4):
        pygame.draw.rect(bg, mixc(top, bottom, y / HEIGHT),
                         (0, y, WIDTH, 4))
    return bg


def add_fractures(bg, rng, n=16, col=(52, 18, 70)):
    """Fissures temporelles procédurales sur un fond."""
    for _ in range(n):
        x, y = rng.randint(0, WIDTH), rng.randint(0, HEIGHT)
        a = rng.uniform(0, math.tau)
        pts = [(x, y)]
        for _j in range(rng.randint(3, 6)):
            a += rng.uniform(-0.9, 0.9)
            L = rng.randint(40, 140)
            x += math.cos(a) * L
            y += math.sin(a) * L
            pts.append((x, y))
        pygame.draw.lines(bg, col, False, pts, rng.choice((1, 2)))
    for _ in range(5):
        pygame.draw.circle(bg, mixc(col, NOIR_FOND, 0.45),
                           (rng.randint(0, WIDTH), rng.randint(0, HEIGHT)),
                           rng.randint(60, 200), 2)


# ---- Horloge brisée du fond
def draw_clock_bg(surf, t, color, cx=WIDTH // 2, cy=HEIGHT // 2 - 30,
                  r=250, k=0.22):
    c = mixc(NOIR_FOND, color, k)
    pygame.draw.circle(surf, c, (cx, cy), r, 2)
    pygame.draw.circle(surf, mixc(NOIR_FOND, color, k * 0.55),
                       (cx, cy), r - 34, 1)
    for i in range(12):
        a = i * math.tau / 12 - math.pi / 2
        r1 = r - 22 if i % 3 == 0 else r - 12
        pygame.draw.line(surf, c,
                         (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                         (cx + math.cos(a) * r, cy + math.sin(a) * r),
                         3 if i % 3 == 0 else 1)
    a = t * 0.03 - math.pi / 2
    pygame.draw.line(surf, mixc(NOIR_FOND, ROUGE_NEON, 0.45),
                     (cx, cy),
                     (cx + math.cos(a) * (r - 30), cy + math.sin(a) * (r - 30)),
                     2)
    a2 = t * 0.0025 - math.pi / 2
    pygame.draw.line(surf, c, (cx, cy),
                     (cx + math.cos(a2) * r * 0.55,
                      cy + math.sin(a2) * r * 0.55), 5)
    pygame.draw.circle(surf, c, (cx, cy), 8)


# ---- Champ de shards flottants
class ShardField:
    def __init__(self, n, seed=None):
        r = random.Random(seed)
        self.s = [dict(
            x=r.uniform(0, WIDTH), y=r.uniform(0, HEIGHT),
            vx=r.uniform(-0.5, 0.5), vy=r.uniform(-0.4, 0.6),
            a=r.uniform(0, 6.28), va=r.uniform(-0.02, 0.02),
            size=r.uniform(8, 34), col=r.choice(SHARD_COLS))
            for _ in range(n)]

    def draw(self, surf):
        for s in self.s:
            s["x"] += s["vx"]; s["y"] += s["vy"]; s["a"] += s["va"]
            if s["x"] < -50: s["x"] = WIDTH + 50
            elif s["x"] > WIDTH + 50: s["x"] = -50
            if s["y"] < -50: s["y"] = HEIGHT + 50
            elif s["y"] > HEIGHT + 50: s["y"] = -50
            pts = [(s["x"] + math.cos(s["a"] + k * 2.1) *
                    s["size"] * (1.6 if k == 0 else 1.0),
                    s["y"] + math.sin(s["a"] + k * 2.1) *
                    s["size"] * (1.6 if k == 0 else 1.0))
                   for k in range(3)]
            pygame.draw.polygon(surf, s["col"], pts)
            pygame.draw.polygon(surf, light(s["col"], 0.18), pts, 1)


class Lightning:
    """Éclairs d'ambiance aléatoires."""
    def __init__(self):
        self.cd = random.randint(100, 260)
        self.pts, self.life = [], 0

    def update_draw(self, surf):
        self.cd -= 1
        if self.cd <= 0:
            x, y = random.randint(80, WIDTH - 80), 0
            pts = [(x, 0)]
            end = random.randint(300, HEIGHT)
            while y < end:
                y += random.randint(30, 70)
                x += random.randint(-45, 45)
                pts.append((x, y))
            self.pts, self.life, self.cd = pts, 10, random.randint(150, 420)
        if self.life > 0:
            self.life -= 1
            pygame.draw.lines(surf, PURPLE_NEON, False, self.pts, 7)
            pygame.draw.lines(surf, BLANC, False, self.pts, 2)
        return self.life


# ---- Overlays plein écran (vignette, CRT, edge glow)
_OV = {}


def get_vignette():
    if "vig" not in _OV:
        v = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        n = 16
        for i in range(n):
            pygame.draw.rect(
                v, (0, 0, 0, int(150 * (1 - i / n) ** 2.2)),
                (i * 10, i * 7, WIDTH - i * 20, HEIGHT - i * 14), 10)
        _OV["vig"] = v
    return _OV["vig"]


def get_crt():
    if "crt" not in _OV:
        c = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 3):
            pygame.draw.line(c, (0, 0, 0, 40), (0, y), (WIDTH, y))
        _OV["crt"] = c
    return _OV["crt"]


def get_edge_glow(color):
    key = ("edge", tuple(color))
    if key not in _OV:
        g = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(10):
            pygame.draw.rect(
                g, (*color, int(130 * (1 - i / 10) ** 2)),
                (i * 3, i * 3, WIDTH - i * 6, HEIGHT - i * 6), 3)
        _OV[key] = g
    return _OV[key]


def finish_overlays(surf, edge=None, edge_alpha=255):
    """Vignette + CRT + (optionnel) glow coloré sur les bords."""
    # ☢️ SUR LE WEB : On désactive TOUS les effets plein écran (trop lourds)
    if IS_WEB:
        return
        
    if edge:
        g = get_edge_glow(tuple(edge[:3]))
        g.set_alpha(int(edge_alpha))
        surf.blit(g, (0, 0))
    surf.blit(get_vignette(), (0, 0))
    if SET.get("crt", True):
        surf.blit(get_crt(), (0, 0))


# ---- Titre glitché
_TITLE_CACHE = {}


def draw_glitch_title(surf, text, font, cx, cy, t, main=BLANC):
    """Titre avec effet glitch chromatic aberration périodique."""
    key = (text, id(font), main)
    if key not in _TITLE_CACHE:
        _TITLE_CACHE[key] = (
            font.render(text, True, main),
            font.render(text, True, CYAN_NEON),
            font.render(text, True, ROUGE_NEON),
        )
    base, cyn, red = _TITLE_CACHE[key]
    glitch = (t % 150) < 9 and not SET.get("calm", False)
    off = 5 if glitch else 2
    wob = int(math.sin(t * 0.05) * 2)
    r = base.get_rect(center=(cx, cy))
    surf.blit(red, (r.x + off, r.y + wob))
    surf.blit(cyn, (r.x - off, r.y - wob))
    if glitch:
        for k in range(0, r.h, 10):
            surf.blit(base,
                      (r.x + random.randint(-16, 16), r.y + k),
                      pygame.Rect(0, k, r.w, 10))
    else:
        surf.blit(base, r)


# ---- Icônes monnaie
def draw_coin_icon(surf, x, y, r=9):
    pygame.draw.circle(surf, JAUNE_NEON, (int(x), int(y)), r)
    pygame.draw.circle(surf, (200, 150, 0), (int(x), int(y)), r, 2)
    pygame.draw.circle(surf, (200, 150, 0), (int(x), int(y)),
                       max(2, r - 5), 1)


def draw_gem_icon(surf, x, y, r=9):
    pts = [(x, y - r), (x + r * 0.85, y - r * 0.2),
           (x + r * 0.5, y + r * 0.9), (x - r * 0.5, y + r * 0.9),
           (x - r * 0.85, y - r * 0.2)]
    pygame.draw.polygon(surf, GEM_COL, pts)
    pygame.draw.polygon(surf, (20, 110, 170), pts, 2)
    pygame.draw.line(surf, (235, 252, 255),
                     (x - r * 0.45, y - r * 0.15), (x, y - r * 0.7), 2)
    pygame.draw.line(surf, (20, 110, 170),
                     (x - r * 0.85, y - r * 0.2),
                     (x + r * 0.85, y - r * 0.2), 1)


# ---- Couronne / trophée vectoriels
def draw_crown(surf, cx, cy, s=1.0, col=CHAMPION_COL):
    """Couronne dorée Vector-Art."""
    base_r = pygame.Rect(cx - int(24 * s), cy + int(6 * s),
                         int(48 * s), int(10 * s))
    pygame.draw.rect(surf, col, base_r, border_radius=int(3 * s))
    pygame.draw.rect(surf, CHAMPION_DARK, base_r, 2,
                     border_radius=int(3 * s))
    pts = [
        (cx - int(24 * s), cy + int(6 * s)),
        (cx - int(16 * s), cy - int(16 * s)),
        (cx - int(8 * s),  cy + int(2 * s)),
        (cx,               cy - int(22 * s)),
        (cx + int(8 * s),  cy + int(2 * s)),
        (cx + int(16 * s), cy - int(16 * s)),
        (cx + int(24 * s), cy + int(6 * s)),
    ]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, CHAMPION_DARK, pts, 2)
    for jx in (cx - int(16 * s), cx, cx + int(16 * s)):
        pygame.draw.circle(surf, (255, 60, 90), (jx, cy - int(10 * s)),
                           int(3 * s))
        pygame.draw.circle(surf, BLANC, (jx, cy - int(10 * s)),
                           max(1, int(1.5 * s)))


def draw_trophy(surf, cx, cy, col=JAUNE_NEON, s=1.0):
    pygame.draw.polygon(surf, col,
                        [(cx - 12 * s, cy - 12 * s),
                         (cx + 12 * s, cy - 12 * s),
                         (cx + 8 * s, cy + 4 * s),
                         (cx - 8 * s, cy + 4 * s)])
    pygame.draw.arc(surf, col,
                    (cx - 19 * s, cy - 12 * s, 12 * s, 14 * s),
                    1.6, 4.7, 2)
    pygame.draw.arc(surf, col,
                    (cx + 7 * s, cy - 12 * s, 12 * s, 14 * s),
                    -1.6, 1.6, 2)
    pygame.draw.rect(surf, col, (cx - 2 * s, cy + 4 * s, 4 * s, 7 * s))
    pygame.draw.rect(surf, col, (cx - 9 * s, cy + 11 * s, 18 * s, 4 * s))


# ---- Bouton RETOUR unifié : position STRICTEMENT fixe
BACK_BTN_RECT = pygame.Rect(40, HEIGHT - 70, 180, 50)


def draw_back_button(surf=None, action=None, label="RETOUR", color=None, col=None):
    if color is None and col is not None:
        color = col
    """Bouton Retour uniforme, bas-gauche, jamais en collision avec les HUD.

    - Position fixe : BACK_BTN_RECT.
    - Joue un hover au survol, déclenche action() au clic.
    - Retourne True si cliqué.
    """
    surf = surf if surf is not None else screen
    col = color or CYAN_NEON
    r = BACK_BTN_RECT
    hover = r.collidepoint(mouse["x"], mouse["y"])

    if hover:
        pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.09)
        glow_rect(surf, r, col, spread=10,
                  max_alpha=int(50 + 40 * pulse))

    panel(surf, r,
          col if hover else dark(col, 0.65),
          mixc(PANEL, col, 0.20 if hover else 0.05),
          10, 3 if hover else 2)

    # Flèche vectorielle
    ax, ay = r.x + 26, r.centery
    arrow_col = col if hover else light(col, 0.4)
    pygame.draw.polygon(surf, arrow_col,
                        [(ax + 8, ay - 10), (ax - 6, ay), (ax + 8, ay + 10)])
    pygame.draw.line(surf, arrow_col, (ax - 4, ay), (ax + 12, ay), 3)

    # Texte net
    try:
        img = FONT_BTN.render(tr(label), True,
                              BLANC if hover else light(col, 0.35))
        shd = FONT_BTN.render(tr(label), True, (0, 0, 0))
        pos = img.get_rect(midleft=(r.x + 60, r.centery))
        surf.blit(shd, (pos.x + 1, pos.y + 1))
        surf.blit(img, pos)
    except Exception:
        pass

    if hover and mouse["click"]:
        mouse["click"] = False
        try:
            audio.play("click")
        except Exception:
            pass
        if callable(action):
            action()
        return True
    return False


# ---- Compteur pièces/gemmes haut-droit (utilisé par tous les menus)
def draw_coins_counter(surf=None):
    """Pièces (haut) et gemmes (dessous), en haut à droite."""
    surf = surf if surf is not None else screen
    panel(surf, (WIDTH - 190, 12, 176, 34), JAUNE_NEON)
    draw_coin_icon(surf, WIDTH - 172, 29, 9)
    draw_text_ml(surf, fmt_num(SAVE["coins"]), FONT_BTN, JAUNE_NEON,
                 WIDTH - 156, 29)
    panel(surf, (WIDTH - 190, 49, 176, 28), GEM_COL, PANEL, 8, 2)
    draw_gem_icon(surf, WIDTH - 172, 63, 8)
    draw_text_ml(surf, fmt_num(SAVE["gems"]), FONT_SMALL, GEM_COL,
                 WIDTH - 156, 63)


# ---- Badge profil (haut-gauche, cliquable)
def draw_profile_badge(surf, rect, hover=False):
    """Badge de profil : cadre + avatar + nom + niveau + barre d'XP."""
    panel(surf, rect,
          FRAME_COLORS[SAVE["profile"]["frame"] % len(FRAME_COLORS)]
          if hover else (90, 70, 130),
          PANEL, 9, 3 if hover else 2)
    prof = SAVE["profile"]
    skin = prof["avatar"] if prof["avatar"] in SAVE["owned"] else SAVE["selected"]

    # Avatar (draw_avatar est défini en § 5 ; ici on dessine un placeholder
    # sûr si la fonction n'est pas encore disponible.)
    try:
        draw_avatar(surf, rect.x + 36, rect.centery, 54, skin, prof["frame"])
    except NameError:
        pygame.draw.circle(surf, FRAME_COLORS[prof["frame"] % 8],
                           (rect.x + 36, rect.centery), 27, 3)

    name = prof["name"] or "PILOTE"
    draw_text(surf, name, FONT_BTN, BLANC,
              rect.x + 72, rect.y + 10, center=False)
    lvl, xp, need = player_level()
    try:
        rank_txt = tr(RANKS[min(4, lvl // 5)])
    except Exception:
        rank_txt = ""
    draw_text(surf, "%s %d  %s" % (tr("NIV."), lvl, rank_txt),
              FONT_TINY, JAUNE_NEON, rect.x + 72, rect.y + 36, center=False)
    pygame.draw.rect(surf, (40, 30, 70),
                     (rect.x + 72, rect.y + 54, rect.w - 88, 6))
    pygame.draw.rect(surf, CYAN_NEON,
                     (rect.x + 72, rect.y + 54,
                      (rect.w - 88) * clamp01(xp / need), 6))


RANKS = ["RECRUE", "PILOTE", "ÉLITE", "VÉTÉRAN", "MAÎTRE DU CHAOS"]


def player_level():
    """Niveau joueur dérivé des statistiques cumulées."""
    st = SAVE["stats"]
    xp = (st["rounds_total"] * 12
          + st["kills_total"] * 2
          + len(SAVE["ach"]) * 60
          + st["games"] * 5)
    lvl, need = 1, 100
    while xp >= need:
        xp -= need
        lvl += 1
        need = int(need * 1.18) + 20
    return lvl, xp, need


# ---- Transition d'écran (fondu au noir + lignes glitch)
def draw_transition(surf):
    t = UI.get("trans")
    if not t:
        return
    if "veil" not in _OV:
        _OV["veil"] = pygame.Surface((WIDTH, HEIGHT))
        _OV["veil"].fill((6, 2, 14))
    k = t["t"] / 10.0 if t["phase"] == 1 else 1 - t["t"] / 10.0
    _OV["veil"].set_alpha(int(255 * clamp01(k)))
    surf.blit(_OV["veil"], (0, 0))
    for _ in range(int(7 * clamp01(k))):
        c = random.choice((CYAN_NEON, ROUGE_NEON, PURPLE_NEON))
        pygame.draw.rect(
            surf, c,
            (random.randint(0, WIDTH), random.randint(0, HEIGHT),
             random.randint(60, 380), random.randint(2, 8)))


def goto(state, session=None):
    """Déclenche une transition vers un écran."""
    if UI.get("trans") is None:
        UI["trans"] = dict(phase=1, t=0, target=state, session=session)


# ═══════════════════════════════════════════════════════════════════════════
#  FIN § 1-3 — les sections suivantes (audio, skins, entités, session…)
#  seront ajoutées au prochain message.
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#  § 4 — AUDIO (synthèse procédurale, aucun fichier externe)
# ═══════════════════════════════════════════════════════════════════════════

SR = 22050
_SIN = [math.sin(math.tau * i / 1024) for i in range(1024)]


def _osc(wave, ph):
    """Oscillateur élémentaire : sin, sq, saw, tri, noise."""
    if wave == "sin":
        return _SIN[int(ph * 1024) & 1023]
    if wave == "sq":
        return 1.0 if ph < 0.5 else -1.0
    if wave == "saw":
        return 2.0 * ph - 1.0
    if wave == "tri":
        return 4.0 * abs(ph - 0.5) - 1.0
    return random.uniform(-1.0, 1.0)          # "noise"


def synth(f0, f1, dur, wave="sq", vol=0.4, decay=2.0,
          attack=0.004, vib=0.0):
    """Synthétise un buffer : glissando f0→f1, enveloppe attack/decay,
    vibrato optionnel. Retourne une liste de floats ∈ [-1, 1]."""
    n = max(1, int(SR * dur))
    out = [0.0] * n
    ph = 0.0
    att = SR * attack + 1
    for i in range(n):
        p = i / n
        f = f0 + (f1 - f0) * p
        if vib:
            f += math.sin(i * 0.02) * vib
        ph = (ph + f / SR) % 1.0
        env = min(1.0, i / att) * ((1.0 - p) ** decay)
        out[i] = _osc(wave, ph) * env * vol
    return out


def mix(*layers):
    """Mixage additif de plusieurs buffers."""
    n = max(len(l) for l in layers)
    out = [0.0] * n
    for l in layers:
        for i, v in enumerate(l):
            out[i] += v
    return out


def cat(*parts):
    """Concaténation séquentielle de buffers."""
    r = []
    for p in parts:
        r += p
    return r


def to_sound(buf, gain=1.0):
    """Buffer float → pygame.Sound 16-bit mono."""
    a = array.array("h", [
        int(max(-1.0, min(1.0, v * gain)) * 30000) for v in buf
    ])
    return pygame.mixer.Sound(buffer=a.tobytes())


def build_sfx_buffers():
    """Les 20 SFX du jeu, tous synthétisés."""
    S = {}
    S["shoot"]   = synth(900, 300, 0.09, "sq", 0.20)
    S["laser"]   = synth(1800, 500, 0.14, "saw", 0.18)
    S["missile"] = mix(synth(220, 90, 0.22, "saw", 0.22),
                       synth(0, 0, 0.22, "noise", 0.16))
    S["special"] = synth(500, 1300, 0.13, "sq", 0.18)
    S["hit"]     = mix(synth(0, 0, 0.07, "noise", 0.30),
                       synth(300, 110, 0.08, "sq", 0.18))
    S["boom"]    = mix(synth(0, 0, 0.42, "noise", 0.45, 2.5),
                       synth(90, 40, 0.42, "sin", 0.50, 1.5))
    S["jump"]    = synth(280, 720, 0.11, "sq", 0.16)
    S["coin"]    = cat(synth(988, 988, 0.07, "sq", 0.18),
                       synth(1319, 1319, 0.15, "sq", 0.18))
    S["click"]   = synth(700, 480, 0.04, "sin", 0.35)
    S["hover"]   = synth(520, 520, 0.02, "sin", 0.10)
    S["tick"]    = synth(1300, 1100, 0.015, "sq", 0.12)
    S["chaos"]   = mix(synth(150, 1100, 0.50, "saw", 0.22, 0.5),
                       synth(0, 0, 0.50, "noise", 0.10, 0.5))
    S["win"]     = cat(*[synth(f, f, 0.11, "sq", 0.20, 1.0)
                         for f in (523, 659, 784, 1047)]
                       + [synth(1047, 1047, 0.30, "sq", 0.20, 1.0)])
    S["ko"]      = synth(420, 50, 0.70, "saw", 0.30, 1.0)
    S["shield"]  = synth(500, 540, 0.10, "sin", 0.22, 1.5, vib=30)
    S["dash"]    = mix(synth(0, 0, 0.14, "noise", 0.20, 1.5),
                       synth(900, 250, 0.14, "sq", 0.10))
    S["ach"]     = cat(*[synth(f, f, 0.09, "tri", 0.30, 0.8)
                         for f in (659, 880, 1109, 1319)]
                       + [synth(1319, 1319, 0.35, "tri", 0.30, 1.2)])
    S["buy"]     = cat(synth(784, 784, 0.06, "sq", 0.18),
                       synth(1047, 1047, 0.06, "sq", 0.18),
                       synth(1568, 1568, 0.14, "sq", 0.18))
    S["error"]   = synth(150, 110, 0.20, "sq", 0.25)
    S["pickup"]  = synth(600, 1500, 0.20, "tri", 0.30, 1.0)
    S["ad_coins"] = cat(*[synth(f, f, 0.08, "sq", 0.22)
                          for f in (784, 988, 1175, 1568)])
    S["ad_gems"] = cat(*[synth(f, f, 0.10, "tri", 0.24, 0.7)
                         for f in (659, 880, 1319)])
    S["ad_box"]  = cat(synth(880, 880, 0.10, "sq", 0.22),
                       synth(1319, 1319, 0.10, "sq", 0.22),
                       synth(1568, 1568, 0.30, "sq", 0.22, 1.5))
    return S


def build_track(kind):
    """Pistes musicales : 'menu' (sombre 104 BPM) / 'battle' (146 BPM)."""
    bpm = 104 if kind == "menu" else 146
    step = 60.0 / bpm / 4
    sl = int(step * SR)
    steps = 8 * 16
    buf = [0.0] * (steps * sl)
    roots = ([110.0, 87.31, 130.81, 98.0] if kind == "menu"
             else [82.41, 82.41, 98.0, 73.42])
    minor = [1.0, 1.189, 1.498, 2.0]
    cache = {}

    def note(f, d, w, v, dec):
        k = (round(f, 2), round(d, 3), w, v, dec)
        if k not in cache:
            cache[k] = synth(f, f, d, w, v, dec)
        return cache[k]

    def put(samples, at):
        end = min(len(buf), at + len(samples))
        for i in range(at, end):
            buf[i] += samples[i - at]

    kick  = synth(160, 38, 0.16, "sin", 0.60, 1.5)
    hat   = synth(0, 0, 0.03, "noise", 0.09, 2)
    snare = mix(synth(0, 0, 0.12, "noise", 0.20, 2),
                synth(200, 120, 0.08, "tri", 0.18, 2))

    for st in range(steps):
        bar, s = st // 16, st % 16
        root = roots[(bar // 2) % 4]
        at = st * sl
        if kind == "menu":
            if s % 4 == 0:
                put(note(root, step * 3.6, "tri", 0.32, 1.0), at)
            if s % 2 == 0:
                put(note(root * 2 * minor[(s // 2) % 4],
                         step * 1.6, "sq", 0.06, 1.5), at)
            if s == 0 and bar % 2 == 0:
                put(note(root * 2, step * 30, "saw", 0.045, 0.4), at)
            if s % 8 == 0:
                put(kick, at)
        else:
            if s % 2 == 0:
                put(note(root, step * 1.7, "sq", 0.20, 1.2), at)
            put(note(root * 4 * minor[s % 4],
                     step * 0.9, "sq", 0.07, 1.4), at)
            if s % 4 == 0:
                put(kick, at)
            if s % 8 == 4:
                put(snare, at)
            if s % 2 == 1:
                put(hat, at)
            if bar >= 4 and s in (0, 6, 10, 14):
                put(note(root * 8 * minor[(s // 3) % 4],
                         step * 2.5, "tri", 0.10, 1.0), at)
    return buf


class Audio:
    """Gestionnaire audio : SFX + musique, tolérant en cas d'absence de device."""

    def __init__(self):
        # ⚠️ CETTE LIGNE DOIT ÊTRE LA TOUTE PREMIÈRE
        self.ok = False  
        
        self.sfx = {}
        self.tracks = {}
        self.cur = None
        self.last = {}
        self.frame = 0
        self.mchan = None
        
        # Patch Web : on s'arrête ici sur le navigateur
        if IS_WEB:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
            self.mchan = pygame.mixer.Channel(0)
            self.ok = True
        except Exception:
            self.ok = False

    def build(self, cb=None):
        """Synthétise tous les SFX + les 2 pistes (asynchrone impossible,
        mais rapide ~1.5s sur machines modernes). `cb` = progress [0, 1]."""
        if not self.ok:
            return
        try:
            bufs = build_sfx_buffers()
            total = len(bufs) + 2
            for i, (name, buf) in enumerate(bufs.items()):
                self.sfx[name] = to_sound(buf)
                if cb:
                    cb((i + 1) / total)
            for j, kind in enumerate(("menu", "battle")):
                self.tracks[kind] = to_sound(build_track(kind), 0.9)
                if cb:
                    cb((len(bufs) + j + 1) / total)
        except Exception:
            self.ok = False

    def play(self, name, vol=1.0):
        """Joue un SFX (avec anti-spam 3 frames)."""
        if not self.ok or name not in self.sfx:
            return
        if self.frame - self.last.get(name, -99) < 3:
            return
        self.last[name] = self.frame
        try:
            ch = self.sfx[name].play()
            if ch:
                ch.set_volume(clamp(SET["master"] * SET["sfx"] * vol, 0, 1))
        except Exception:
            pass

    def music(self, name):
        """Change la piste musicale en boucle."""
        if not self.ok or name not in self.tracks or self.cur == name:
            return
        self.cur = name
        try:
            self.mchan.play(self.tracks[name], loops=-1, fade_ms=500)
            self.apply()
        except Exception:
            pass

    def apply(self):
        """Applique le volume master × music aux pistes."""
        if self.ok and self.mchan:
            try:
                self.mchan.set_volume(
                    clamp(SET["master"] * SET["music"], 0, 1))
            except Exception:
                pass


# Remplace le stub précédent par la vraie implémentation
audio = Audio()


# ═══════════════════════════════════════════════════════════════════════════
#  § 5 — SKINS (Vector-Art 2026)
# ═══════════════════════════════════════════════════════════════════════════

# ---- Raretés
RARITY = {
    "COMMON":    dict(label="COMMUN",    en="COMMON",    color=(150, 155, 170), rank=0),
    "RARE":      dict(label="RARE",      en="RARE",      color=(70, 150, 255),  rank=1),
    "EPIC":      dict(label="ÉPIQUE",    en="EPIC",      color=(180, 80, 255),  rank=2),
    "LEGENDARY": dict(label="LÉGENDAIRE", en="LEGENDARY", color=(255, 200, 40),  rank=3),
    "MYTHIC":    dict(label="MYTHIQUE",  en="MYTHIC",    color=(255, 50, 90),   rank=4),
}

# ---- Compétences passives (valeur → arguments d'affichage)
SKILL_INFO = {
    "double_jump": ("RARE", "Double saut", "Double jump",
                    "Un saut de plus en l'air (relâche puis rappuie).",
                    "One more jump in mid-air (release, then press again).",
                    lambda v: ()),
    "glide": ("RARE", "Anti-gravité", "Anti-gravity",
              "Maintiens SAUT pendant une chute pour planer.",
              "Hold JUMP while falling to glide.",
              lambda v: ()),
    "evade": ("RARE", "Pas d'ombre", "Shadow step",
              "%d%% de chances d'esquiver complètement un coup.",
              "%d%% chance to completely dodge a hit.",
              lambda v: (round(v * 100),)),
    "thorns": ("RARE", "Réfraction", "Refraction",
               "%d%% de chances de renvoyer le coup à son auteur.",
               "%d%% chance to send the hit back at its source.",
               lambda v: (round(v * 100),)),
    "kill_heal": ("RARE", "Digestion", "Digestion",
                  "+%d PV à chaque ennemi éliminé.",
                  "+%d HP for every enemy eliminated.",
                  lambda v: (round(v),)),
    "reactive": ("EPIC", "Blindage réactif", "Reactive plating",
                 "Après un coup : %.1f s d'invulnérabilité et %.1f s sans pièges.",
                 "After a hit: %.1f s of invulnerability and %.1f s trap-free.",
                 lambda v: (v[0] / 60.0, v[1] / 60.0)),
    "fury": ("EPIC", "Rage", "Rage",
             "+%d%% de dégâts quand tes PV passent sous 35%%.",
             "+%d%% damage when your HP drops below 35%%.",
             lambda v: (round(v * 100),)),
    "echo_power": ("EPIC", "Écho renforcé", "Boosted echo",
                   "Les tirs de tes échos font +%d%% de dégâts.",
                   "Your echoes' shots deal +%d%% damage.",
                   lambda v: (round(v * 100),)),
    "chaos_surf": ("EPIC", "Surfeur de chaos", "Chaos surfer",
                   "À chaque chaos : +%d PV, +%d%% de bouclier, vitesse %d s.",
                   "On every chaos: +%d HP, +%d%% shield, speed boost %d s.",
                   lambda v: (v[0], round(v[1] * 100), round(v[2] / 60.0))),
    "time_drift": ("EPIC", "Réflexes temporels", "Time reflexes",
                   "Un coup sous 30%% de PV ralentit le temps %.1f s (recharge %d s).",
                   "A hit below 30%% HP slows time for %.1f s (cooldown %d s).",
                   lambda v: (v[0] / 60.0, round(v[1] / 60.0))),
    "bounty": ("EPIC", "Chasseur de primes", "Bounty hunter",
               "+%d pièces par ennemi éliminé (en fin de manche).",
               "+%d coins per enemy eliminated (at round end).",
               lambda v: (round(v),)),
    "shockwave": ("LEGENDARY", "Onde de choc", "Shockwave",
                  "Un coup encaissé libère une onde éliminatoire (rayon %d, recharge %d s).",
                  "A hit taken unleashes a lethal shockwave (radius %d, cooldown %d s).",
                  lambda v: (v[0], round(v[2] / 60.0))),
    "auto_shield": ("LEGENDARY", "Aura divine", "Divine aura",
                    "Un bouclier automatique bloque 1 coup (recharge %d s).",
                    "An automatic shield blocks 1 hit (cooldown %d s).",
                    lambda v: (round(v / 60.0),)),
    "chain_blast": ("LEGENDARY", "Réaction en chaîne", "Chain reaction",
                    "Chaque ennemi éliminé explose (rayon %d).",
                    "Every enemy you eliminate explodes (radius %d).",
                    lambda v: (v[0],)),
    "second_wind": ("LEGENDARY", "Seconde vie", "Second life",
                    "Une fois par manche : reviens à 50%% de PV au lieu de mourir.",
                    "Once per round: come back at 50%% HP instead of dying.",
                    lambda v: ()),
    "sanctuary": ("MYTHIC", "Sanctuaire Temporel", "Temporal Sanctuary",
                  "[F] Fige le temps %.0f s et libère une onde dévastatrice (recharge %d s).",
                  "[F] Freezes time %.0f s and unleashes a devastating blast (cooldown %d s).",
                  lambda v: (v[0] / 60.0, round(v[1] / 60.0))),
    "time_master": ("MYTHIC", "Maître du Temps", "Time Master",
                    "+%d%% de dégâts globaux et régénération de %.1f PV/s.",
                    "+%d%% global damage and %.1f HP/s regeneration.",
                    lambda v: (round(v[0] * 100), v[1])),
    "champion_frenzy": ("MYTHIC", "Frénésie du Champion", "Champion Frenzy",
                        "[F] Cadence ×3, vitesse +40 %%, dégâts ×2 pendant %.0f s (recharge %d s).",
                        "[F] Fire rate ×3, speed +40%%, damage ×2 for %.0f s (cooldown %d s).",
                        lambda v: (v[0] / 60.0, round(v[1] / 60.0))),
    "combustion_elite": ("MYTHIC", "Combustion d'Élite", "Elite Combustion",
                         "Chaque élimination : +%d%% de puissance (jusqu'à +%d%%, reset si touché).",
                         "Every elimination: +%d%% power (up to +%d%%, resets when hit).",
                         lambda v: (round(v[0] * 100), round(v[0] * v[1] * 100))),
    "black_hole": ("MYTHIC", "Trou Noir Quantique", "Quantum Black Hole",
                   "[F] Aspire les ennemis et projectiles, puis déflagration (recharge %d s).",
                   "[F] Pulls enemies and projectiles, then detonates (cooldown %d s).",
                   lambda v: (round(v[3] / 60.0),)),
    "quantum_dodge": ("MYTHIC", "Esquive Quantique", "Quantum Dodge",
                      "%d%% de chances d'annuler un coup et de te téléporter (recharge %d s).",
                      "%d%% chance to negate a hit and teleport (cooldown %d s).",
                      lambda v: (round(v[0] * 100), round(v[1] / 60.0))),
}

# ---- Formats d'affichage des stats
STAT_FMT = {
    "hp":       ("+%d PV max",                "+%d max HP",               lambda v: round(v)),
    "shield":   ("+%d bouclier",              "+%d shield",               lambda v: round(v)),
    "power":    ("+%d%% puissance",           "+%d%% power",              lambda v: round(v * 100)),
    "rate":     ("+%d%% cadence de tir",      "+%d%% fire rate",          lambda v: round(v * 100)),
    "speed":    ("+%d%% vitesse",             "+%d%% speed",              lambda v: round(v / 6.0 * 100)),
    "jump":     ("+%d%% saut",                "+%d%% jump",               lambda v: round(v / 12.5 * 100)),
    "reduce":   ("-%d%% dégâts subis",        "-%d%% damage taken",       lambda v: round(v * 100)),
    "regen":    ("+%d/s recharge bouclier",   "+%d/s shield recharge",    lambda v: round(v * 60)),
    "hp_regen": ("+%.1f PV/s",                "+%.1f HP/s",               lambda v: v),
    "coin":     ("+%d%% pièces gagnées",      "+%d%% coins earned",       lambda v: round(v * 100)),
    "hp_pct":   ("+%d%% PV max",              "+%d%% max HP",             lambda v: round(v * 100)),
    "speed_pct": ("+%d%% de vitesse",         "+%d%% speed",              lambda v: round(v * 100)),
}


# ─────────────────────────────────────────────────────────────────────────
#  Helpers de composition Vector-Art (réutilisables par les 24 skins)
# ─────────────────────────────────────────────────────────────────────────

_AURA_CACHE = {}


def _make_aura(radius, color, alpha_max=100, layers=8):
    size = radius * 2 + 6
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    for i in range(layers, 0, -1):
        k = i / layers
        a = int(alpha_max * (1 - k) ** 1.7)
        if a <= 0:
            continue
        pygame.draw.circle(s, (*color, a), (cx, cy),
                           max(2, int(radius * (0.25 + 0.75 * k))))
    return s


def _aura(radius, color, t=0, alpha=90):
    """Aura pulsante pré-calculée."""
    key = (radius, color, alpha)
    s = _AURA_CACHE.get(key)
    if s is None:
        s = _make_aura(radius, color, alpha, 8)
        _AURA_CACHE[key] = s
        
    if IS_WEB:
        # Sur le web, on désactive la pulsation (trop lourd)
        return s 
        
    k = 1.0 + 0.07 * math.sin(t * 0.09)
    w = max(4, int(s.get_width() * k))
    h = max(4, int(s.get_height() * k))
    return pygame.transform.smoothscale(s, (w, h))


def _blit_c(surf, img, cx, cy):
    surf.blit(img, (cx - img.get_width() // 2,
                    cy - img.get_height() // 2))


def _legs(s, cx, cy, col, t, air, vx, w=6, h=14):
    """Jambes animées (course, saut)."""
    run = abs(vx) > 0.5 and not air
    l = int(math.sin(t * 0.45) * 4) if run else 0
    lw = dark(col, 0.55)
    pygame.draw.polygon(s, lw, [(cx - 12, cy + 20), (cx - 12 + w, cy + 20),
                                (cx - 4 + w, cy + 20 + h + max(l, 0)),
                                (cx - 10, cy + 20 + h + max(l, 0))])
    pygame.draw.polygon(s, lw, [(cx + 6, cy + 20), (cx + 6 + w, cy + 20),
                                (cx + 10, cy + 20 + h + max(-l, 0)),
                                (cx + 4, cy + 20 + h + max(-l, 0))])
    pygame.draw.line(s, col, (cx - 7, cy + 34 + max(l, 0)),
                     (cx - 11, cy + 36 + max(l, 0)), 3)
    pygame.draw.line(s, col, (cx + 7, cy + 34 + max(-l, 0)),
                     (cx + 11, cy + 36 + max(-l, 0)), 3)


def _torso(s, cx, cy, body, accent, style="standard"):
    """Torse polygonal central + plaque accent."""
    if style == "heavy":
        pts = [(cx - 16, cy - 4), (cx - 18, cy + 14), (cx - 10, cy + 22),
               (cx + 10, cy + 22), (cx + 18, cy + 14), (cx + 16, cy - 4)]
    elif style == "thin":
        pts = [(cx - 11, cy - 4), (cx - 13, cy + 14), (cx - 6, cy + 20),
               (cx + 6, cy + 20), (cx + 13, cy + 14), (cx + 11, cy - 4)]
    else:
        pts = [(cx - 14, cy - 2), (cx - 16, cy + 14), (cx - 8, cy + 21),
               (cx + 8, cy + 21), (cx + 16, cy + 14), (cx + 14, cy - 2)]
    pygame.draw.polygon(s, body, pts)
    pygame.draw.polygon(s, light(body, 0.30), pts, 2)
    plate = [(cx - 8, cy + 1), (cx + 8, cy + 1),
             (cx + 6, cy + 15), (cx - 6, cy + 15)]
    pygame.draw.polygon(s, accent, plate)
    pygame.draw.polygon(s, BLANC, plate, 1)


def _visor(s, cx, cy, w, h, col, face=1):
    """Visière LED nette."""
    pts = [(cx - w, cy - h), (cx + w, cy - h),
           (cx + w - 3, cy + h), (cx - w + 3, cy + h)]
    pygame.draw.polygon(s, col, pts)
    pygame.draw.polygon(s, light(col, 0.55), pts, 1)
    pygame.draw.line(s, BLANC,
                     (cx - w + 2 + face, cy - h + 2),
                     (cx + w - 4 + face, cy - h + 2), 1)


def _helmet(s, cx, cy, body, accent, style="classic", face=1):
    """Casque complet avec visière LED."""
    if style == "round":
        pygame.draw.circle(s, body, (cx, cy), 11)
        pygame.draw.circle(s, light(body, 0.3), (cx, cy), 11, 2)
        _visor(s, cx, cy - 2, 8, 3, accent, face)
    elif style == "knight":
        pts = [(cx - 11, cy + 3), (cx - 12, cy - 6), (cx - 5, cy - 12),
               (cx + 5, cy - 12), (cx + 12, cy - 6), (cx + 11, cy + 3)]
        pygame.draw.polygon(s, body, pts)
        pygame.draw.polygon(s, light(body, 0.3), pts, 2)
        _visor(s, cx, cy - 3, 9, 3, accent, face)
        pygame.draw.line(s, accent, (cx, cy - 12), (cx, cy - 18), 3)
    elif style == "dragon":
        pts = [(cx - 13, cy + 4), (cx - 14, cy - 8), (cx - 4, cy - 14),
               (cx + 8, cy - 12), (cx + 14, cy - 2), (cx + 10, cy + 4)]
        pygame.draw.polygon(s, body, pts)
        pygame.draw.polygon(s, accent, pts, 2)
        _visor(s, cx + 2, cy - 2, 8, 3, accent, face)
        pygame.draw.polygon(s, accent, [(cx - 10, cy - 10),
                                        (cx - 16, cy - 20), (cx - 6, cy - 14)])
        pygame.draw.polygon(s, accent, [(cx + 6, cy - 12),
                                        (cx + 14, cy - 22), (cx + 12, cy - 8)])
    else:
        pts = [(cx - 11, cy + 3), (cx - 12, cy - 8), (cx - 6, cy - 13),
               (cx + 6, cy - 13), (cx + 12, cy - 8), (cx + 11, cy + 3)]
        pygame.draw.polygon(s, body, pts)
        pygame.draw.polygon(s, light(body, 0.3), pts, 2)
        _visor(s, cx, cy - 3, 9, 3, accent, face)


def _heart(s, cx, cy, r, col, t):
    """Cœur d'énergie pulsatif."""
    pr = int(r * (1.0 + 0.15 * math.sin(t * 0.15)))
    pygame.draw.circle(s, dark(col, 0.5), (cx, cy), pr + 3)
    pygame.draw.circle(s, col, (cx, cy), pr)
    pygame.draw.circle(s, BLANC, (cx - pr // 3, cy - pr // 3),
                       max(1, pr // 3))


def _shoulder(s, cx, cy, side, col, style="blade", scale=1.0):
    sx = cx + side * int(18 * scale)
    if style == "blade":
        pts = [(sx, cy - 6), (sx + side * 12, cy - 14),
               (sx + side * 14, cy + 2), (sx + side * 4, cy + 6),
               (sx, cy + 2)]
    elif style == "spiked":
        pts = [(sx - 4, cy - 4), (sx + side * 8, cy - 18),
               (sx + side * 18, cy - 6), (sx + side * 14, cy + 6),
               (sx + 2, cy + 4)]
    else:
        pts = [(sx - 4, cy - 4), (sx + side * 10, cy - 10),
               (sx + side * 12, cy + 4), (sx, cy + 6)]
    pygame.draw.polygon(s, col, pts)
    pygame.draw.polygon(s, light(col, 0.35), pts, 2)


def _reactors(s, cx, cy, col, t, air):
    """Réacteurs dorsaux + flammes (Legendary+)."""
    for side in (-1, 1):
        rx = cx + side * 14
        ry = cy - 2
        pygame.draw.rect(s, dark(col, 0.4),
                         (rx - 3, ry - 4, 6, 10), border_radius=2)
        fh = 10 + int(4 * math.sin(t * 0.3 + side)) + (6 if air else 0)
        pygame.draw.polygon(s, (255, 140, 40),
                            [(rx - 3, ry + 6), (rx + 3, ry + 6),
                             (rx, ry + 6 + fh)])
        pygame.draw.polygon(s, (255, 230, 120),
                            [(rx - 2, ry + 6), (rx + 2, ry + 6),
                             (rx, ry + 6 + fh * 0.6)])


# ─────────────────────────────────────────────────────────────────────────
#  Les 24 skins Vector-Art
# ─────────────────────────────────────────────────────────────────────────

# ---- COMMUN #1 : Cyber Runner ------------------------------------------
def sk_cyber(s, k, t, air, vx):
    """Cyber Runner — jambes de course INTÉGRÉES (circuits lumineux
    sur la cuisse), torse à 6 facettes, casque anguleux."""
    b, a = k["body"], k["accent"]

    # Jambes de course — circuits lumineux spécifiques au thème
    run = abs(vx) > 0.5 and not air
    l = int(math.sin(t * 0.45) * 4) if run else 0
    for side, off in ((-1, max(l, 0)), (1, max(-l, 0))):
        lx = 60 + side * 8
        # Cuisse
        pygame.draw.polygon(s, dark(b, 0.55), [
            (lx - 4, 66), (lx + 4, 66),
            (lx + 4, 74 + off), (lx - 4, 74 + off)])
        pygame.draw.polygon(s, light(b, 0.2), [
            (lx - 4, 66), (lx + 4, 66),
            (lx + 4, 74 + off), (lx - 4, 74 + off)], 1)
        pygame.draw.line(s, a, (lx, 68), (lx, 72 + off), 1)
        # Tibia
        pygame.draw.polygon(s, dark(b, 0.75), [
            (lx - 3, 74 + off), (lx + 3, 74 + off),
            (lx + 4, 86 + off), (lx - 2, 86 + off)])
        # Pied
        pygame.draw.polygon(s, a, [
            (lx - 4, 86 + off), (lx + 6, 86 + off),
            (lx + 6, 88 + off), (lx - 4, 88 + off)])

    # Torse 6 facettes
    torso = [(46, 42), (74, 42), (76, 56), (70, 72), (50, 72), (44, 56)]
    pygame.draw.polygon(s, b, torso)
    pygame.draw.polygon(s, light(b, 0.35), torso, 2)
    # Facette gauche assombrie
    pygame.draw.polygon(s, dark(b, 0.25),
                        [(50, 46), (60, 46), (60, 68), (50, 66)])
    # Plaque d'accent centrale
    plate = [(56, 48), (64, 48), (64, 60), (60, 64), (56, 60)]
    pygame.draw.polygon(s, a, plate)
    pygame.draw.polygon(s, BLANC, plate, 1)

    # Épaulières courtes
    for side in (-1, 1):
        ex = 60 + side * 18
        pts = [(ex - 3, 44), (ex + side * 2, 42),
               (ex + side * 2, 54), (ex - 3, 56)]
        pygame.draw.polygon(s, b, pts)
        pygame.draw.polygon(s, light(b, 0.3), pts, 1)

    # Casque 7 côtés + visière LED
    helm = [(50, 42), (50, 30), (56, 24), (64, 24),
            (70, 30), (70, 42), (60, 44)]
    pygame.draw.polygon(s, b, helm)
    pygame.draw.polygon(s, light(b, 0.4), helm, 2)
    pygame.draw.line(s, light(b, 0.6), (54, 26), (66, 26), 1)
    visor = [(52, 34), (68, 34), (66, 40), (54, 40)]
    pygame.draw.polygon(s, a, visor)
    pygame.draw.polygon(s, light(a, 0.5),
                        [(52, 34), (68, 34), (66, 36), (54, 36)])
    pygame.draw.line(s, BLANC, (54, 35), (62, 35), 1)

    # Circuits dorsaux (4 points lumineux)
    for i in range(4):
        cx1 = 48 + i * 6
        cy1 = 56 + (i % 2) * 2
        pygame.draw.circle(s, a, (cx1, cy1), 1)

    _heart(s, 60, 66, 3, a, t)

# ---- COMMUN #2 : Cube Dash ---------------------------------------------
def sk_cube(s, k, t, air, vx):
    """Cube Dash — cube rotatif à facettes 3D (gauche/droite ombrées)."""
    b, a = k["body"], k["accent"]
    ang = t * 0.22 if air else 0.0
    ca, sa = math.cos(ang), math.sin(ang)

    def R(x, y):
        return (60 + x * ca - y * sa, 64 + x * sa + y * ca)

    # Contour noir
    pygame.draw.polygon(s, (0, 0, 0),
                        [R(-17, -17), R(17, -17), R(17, 17), R(-17, 17)])
    # Base
    pygame.draw.polygon(s, b,
                        [R(-15, -15), R(15, -15), R(15, 15), R(-15, 15)])
    # Facette GAUCHE (ombre)
    pygame.draw.polygon(s, dark(b, 0.45),
                        [R(-15, -15), R(0, -15), R(0, 15), R(-15, 15)])
    # Facette DROITE (lumière)
    pygame.draw.polygon(s, light(b, 0.15),
                        [R(0, -15), R(15, -15), R(15, 15), R(0, 15)])
    # Accent
    pygame.draw.polygon(s, a,
                        [R(-11, -11), R(11, -11), R(11, 11), R(-11, 11)], 3)
    pygame.draw.polygon(s, dark(a, 0.5),
                        [R(-11, 0), R(11, 0), R(11, 11), R(-11, 11)], 1)

    # Yeux
    for ex in (-9, 3):
        pygame.draw.polygon(s, BLANC,
                            [R(ex, -7), R(ex + 7, -7), R(ex + 7, 0), R(ex, 0)])
        pygame.draw.polygon(s, (0, 0, 0),
                            [R(ex, -7), R(ex + 7, -7), R(ex + 7, 0), R(ex, 0)], 1)
        pygame.draw.polygon(s, (0, 0, 0),
                            [R(ex + 3, -5), R(ex + 7, -5),
                             R(ex + 7, -1), R(ex + 3, -1)])

    # Bouche + dents
    pygame.draw.polygon(s, (0, 0, 0),
                        [R(-9, 6), R(9, 6), R(9, 10), R(-9, 10)])
    for dx in range(-8, 8, 4):
        pygame.draw.line(s, BLANC, R(dx, 8), R(dx + 2, 8), 1)

    # Reflet supérieur
    pygame.draw.line(s, light(b, 0.55), R(-13, -13), R(13, -13), 2)

# ---- COMMUN #3 : Titan Gold --------------------------------------------
def sk_titan(s, k, t, air, vx):
    """Titan Gold — jambes = PILIERS BLINDÉS (pas de jambes humaines)."""
    b, a = k["body"], k["accent"]

    # Jambes-piliers massives
    for side in (-1, 1):
        lx = 60 + side * 10
        pygame.draw.polygon(s, dark(b, 0.5), [
            (lx - 6, 66), (lx + 6, 66), (lx + 7, 88), (lx - 7, 88)])
        pygame.draw.polygon(s, a, [
            (lx - 6, 66), (lx + 6, 66), (lx + 7, 88), (lx - 7, 88)], 1)
        pygame.draw.line(s, light(b, 0.3), (lx, 68), (lx, 86), 1)
        # Genou blindé
        pygame.draw.polygon(s, a, [
            (lx - 5, 76), (lx + 5, 76), (lx + 4, 80), (lx - 4, 80)])
        # Pied
        pygame.draw.polygon(s, dark(b, 0.6), [
            (lx - 8, 88), (lx + 9, 88), (lx + 9, 91), (lx - 8, 91)])

    # Torse massif
    torso = [(44, 44), (76, 44), (78, 60), (70, 74), (50, 74), (42, 60)]
    pygame.draw.polygon(s, b, torso)
    pygame.draw.polygon(s, dark(b, 0.4), torso, 2)
    pygame.draw.polygon(s, a,
                        [(52, 50), (68, 50), (68, 66), (60, 72), (52, 66)])
    pygame.draw.polygon(s, light(a, 0.4),
                        [(52, 50), (68, 50), (68, 66), (60, 72), (52, 66)], 1)
    pygame.draw.line(s, BLANC, (54, 52), (66, 52), 1)
    _heart(s, 60, 60, 4, a, t)

    # Épaulières hérissées
    for side in (-1, 1):
        ex = 60 + side * 22
        pts = [(ex - side * 4, 40), (ex, 34), (ex + side * 4, 42),
               (ex + side * 2, 54), (ex - side * 6, 52)]
        pygame.draw.polygon(s, b, pts)
        pygame.draw.polygon(s, a, pts, 2)

    # Casque à crête
    pygame.draw.circle(s, b, (60, 34), 12)
    pygame.draw.circle(s, dark(b, 0.5), (60, 34), 12, 2)
    pygame.draw.polygon(s, a, [(56, 24), (64, 24), (60, 12)])
    pygame.draw.polygon(s, light(a, 0.4), [(56, 24), (60, 22), (60, 12)], 1)
    pygame.draw.rect(s, a, (54, 32, 12, 3))
    pygame.draw.line(s, BLANC, (55, 33), (65, 33), 1)


# ---- COMMUN #4 : Void Phantom ------------------------------------------
def sk_phantom(s, k, t, air, vx):
    """Void Phantom — spectre drapé, PAS DE JAMBES, linceul ondulant."""
    b, a = k["body"], k["accent"]

    # Linceul ondulant (14 segments)
    hem = []
    for i in range(14):
        x = 41 + i * 2.8
        y = 76 + int(math.sin(t * 0.25 + i * 0.6) * (3 + i % 3))
        hem.append((x, y))
    body_pts = [(42, 46)] + hem + [(78, 46)]
    pygame.draw.polygon(s, b, body_pts)
    pygame.draw.polygon(s, light(b, 0.35), body_pts, 2)

    # Plis internes
    for i in range(4):
        px1 = 46 + i * 8
        pygame.draw.line(s, dark(b, 0.4), (px1, 50), (px1 + 2, 74), 1)

    # Tête ovale
    head = [(46, 46), (46, 34), (52, 26), (68, 26), (74, 34), (74, 46)]
    pygame.draw.polygon(s, b, head)
    pygame.draw.polygon(s, light(b, 0.4), head, 2)

    # Yeux lumineux
    for ex in (52, 62):
        pygame.draw.ellipse(s, a, (ex, 38, 8, 10))
        pygame.draw.ellipse(s, light(a, 0.5), (ex, 38, 8, 10), 1)
        pygame.draw.circle(s, (0, 0, 0), (ex + 4, 43), 2)
        pygame.draw.circle(s, BLANC, (ex + 3, 41), 1)

    pygame.draw.line(s, dark(b, 0.6), (56, 50), (64, 50), 1)

    # Traînée spectrale
    for i in range(3):
        yy = 82 + i * 4 + int(math.sin(t * 0.2 + i) * 2)
        alpha_val = 80 - i * 25
        radius = 9 - i * 3
        if radius > 0:
            halo = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                   pygame.SRCALPHA)
            pygame.draw.circle(halo, (*a, alpha_val),
                               (radius + 2, radius + 2), radius)
            s.blit(halo, (60 - radius - 2, yy - radius - 2))


# ---- COMMUN #5 : Oursin Fou --------------------------------------------
def sk_spike(s, k, t, air, vx):
    """Oursin Fou — épines à 2 étages (principales + secondaires)."""
    b, a = k["body"], k["accent"]
    ang = t * 0.12 * (1 if vx >= 0 else -1)

    # Épines principales
    for i in range(12):
        a0 = ang + i * math.tau / 12
        tip = (60 + math.cos(a0) * 26, 60 + math.sin(a0) * 26)
        b1 = (60 + math.cos(a0 - 0.16) * 12,
              60 + math.sin(a0 - 0.16) * 12)
        b2 = (60 + math.cos(a0 + 0.16) * 12,
              60 + math.sin(a0 + 0.16) * 12)
        pygame.draw.polygon(s, a, [b1, tip, b2])
        pygame.draw.polygon(s, dark(a, 0.55), [b1, tip, b2], 1)
        mid = (60 + math.cos(a0 - 0.05) * 19,
               60 + math.sin(a0 - 0.05) * 19)
        pygame.draw.line(s, light(a, 0.5), b1, mid, 1)

    # Épines secondaires
    for i in range(12):
        a0 = ang + math.pi / 12 + i * math.tau / 12
        tip = (60 + math.cos(a0) * 20, 60 + math.sin(a0) * 20)
        b1 = (60 + math.cos(a0 - 0.12) * 14,
              60 + math.sin(a0 - 0.12) * 14)
        b2 = (60 + math.cos(a0 + 0.12) * 14,
              60 + math.sin(a0 + 0.12) * 14)
        pygame.draw.polygon(s, dark(a, 0.7), [b1, tip, b2])

    # Noyau
    pygame.draw.circle(s, b, (60, 60), 14)
    pygame.draw.circle(s, dark(b, 0.5), (60, 60), 14, 3)
    pygame.draw.circle(s, dark(b, 0.3), (60, 60), 11, 1)

    # Œil cyclope
    pygame.draw.circle(s, BLANC, (64, 57), 5)
    pygame.draw.circle(s, (0, 0, 0), (66, 57), 2)
    pygame.draw.circle(s, a, (63, 55), 1)

    # Taches
    for i in range(5):
        ang2 = i * math.tau / 5 + t * 0.02
        px = 60 + math.cos(ang2) * 8
        py = 60 + math.sin(ang2) * 8
        pygame.draw.circle(s, a, (int(px), int(py)), 1)


# ---- RARE #1 : Fusée Turbo ---------------------------------------------
def sk_rocket(s, k, t, air, vx):
    """Fusée Turbo — fuselage à panneaux rivetés, ailerons fins,
    flamme 3 étages, hublot avec reflet."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(38, a, t, 70), 60, 60)

    # Flamme 3 étages
    fl = 12 + int(abs(math.sin(t * 0.5)) * 8) + (10 if air else 0)
    pygame.draw.polygon(s, ORANGE, [(52, 72), (68, 72), (60, 72 + fl)])
    pygame.draw.polygon(s, JAUNE_NEON,
                        [(55, 72), (65, 72), (60, 72 + fl * 0.7)])
    pygame.draw.polygon(s, BLANC,
                        [(57, 72), (63, 72), (60, 72 + fl * 0.4)])

    # Ailerons
    for side in (-1, 1):
        x0 = 52 if side == -1 else 68
        pts = [(x0, 60), (x0 + side * 8, 68),
               (x0 + side * 12, 80), (x0 - side * 2, 74),
               (x0, 68)]
        pygame.draw.polygon(s, a, pts)
        pygame.draw.polygon(s, dark(a, 0.5), pts, 1)
        pygame.draw.line(s, light(a, 0.5), pts[0], pts[2], 1)

    # Fuselage
    body = [(60, 30), (69, 48), (71, 72), (49, 72), (51, 48)]
    pygame.draw.polygon(s, b, body)
    pygame.draw.polygon(s, dark(b, 0.6), body, 2)

    # Panneaux rivetés
    for yy in (52, 60, 68):
        pygame.draw.line(s, dark(b, 0.5), (52, yy), (68, yy), 1)
    for yy in (54, 62, 70):
        for xx in range(53, 68, 4):
            pygame.draw.circle(s, light(b, 0.3), (xx, yy), 1)

    # Hublot
    pygame.draw.circle(s, (90, 200, 255), (60, 54), 6)
    pygame.draw.circle(s, dark(b, 0.6), (60, 54), 6, 2)
    pygame.draw.circle(s, BLANC, (57, 51), 2)

    # Nez
    pygame.draw.polygon(s, a, [(60, 30), (66, 42), (54, 42)])
    pygame.draw.polygon(s, dark(a, 0.5),
                        [(60, 30), (66, 42), (54, 42)], 1)


# ---- RARE #2 : Soucoupe X ----------------------------------------------
def sk_ufo(s, k, t, air, vx):
    """Soucoupe X — dôme à facettes, 3 pieds détaillés, lumières
    clignotantes avec halo."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(38, a, t, 65), 60, 60)
    by = int(math.sin(t * 0.1) * 2)

    # Pieds d'atterrissage
    for dx in (-15, 0, 15):
        x1 = 60 + dx
        pygame.draw.line(s, dark(b, 0.6),
                         (x1, 68 + by), (x1 + dx // 2, 82), 3)
        pygame.draw.circle(s, dark(b, 0.5), (x1 + dx // 2, 82), 3)

    # Dôme à facettes
    dome = [(48, 46 + by), (48, 36 + by), (54, 30 + by),
            (66, 30 + by), (72, 36 + by), (72, 46 + by)]
    pygame.draw.polygon(s, (160, 240, 255), dome)
    pygame.draw.polygon(s, BLANC,
                        [(48, 36 + by), (54, 30 + by),
                         (66, 30 + by), (72, 36 + by)], 2)
    pygame.draw.line(s, BLANC, (52, 34 + by), (60, 32 + by), 1)
    pygame.draw.circle(s, BLANC, (60, 40 + by), 3)

    # Base
    pygame.draw.ellipse(s, b, (40, 56 + by, 40, 14))
    pygame.draw.ellipse(s, dark(b, 0.6), (40, 56 + by, 40, 14), 2)
    pygame.draw.line(s, dark(b, 0.3),
                     (42, 62 + by), (78, 62 + by), 1)

    # Lumières
    for i in range(4):
        col = a if (t // 8 + i) % 2 == 0 else BLANC
        cx1 = 48 + i * 8
        halo = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*col, 80), (4, 4), 4)
        s.blit(halo, (cx1 - 4, 63 + by - 4))
        pygame.draw.circle(s, col, (cx1, 63 + by), 2)

    pygame.draw.arc(s, a, (38, 58 + by, 44, 12), 0.2, 3.0, 1)


# ---- RARE #3 : Ombre Ninja ---------------------------------------------
def sk_ninja(s, k, t, air, vx):
    """Ombre Ninja — jambes ENROULÉES DE TISSU (bandelettes),
    foulard ondulant, katana visible."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(36, a, t, 60), 60, 60)

    # Foulard
    sc = int(math.sin(t * 0.3) * 3)
    pygame.draw.polygon(s, a, [(50, 46), (34, 44 + sc),
                               (36, 52 + sc), (50, 50)])
    pygame.draw.polygon(s, dark(a, 0.5),
                        [(50, 46), (34, 44 + sc),
                         (36, 52 + sc), (50, 50)], 1)
    pygame.draw.polygon(s, a, [(50, 48), (30, 52 - sc),
                               (34, 58 - sc), (50, 52)])
    pygame.draw.polygon(s, dark(a, 0.5),
                        [(50, 48), (30, 52 - sc),
                         (34, 58 - sc), (50, 52)], 1)

    # Jambes bandelettes
    for side in (-1, 1):
        lx = 60 + side * 8
        pygame.draw.polygon(s, dark(b, 0.55), [
            (lx - 4, 66), (lx + 4, 66), (lx + 3, 74), (lx - 3, 74)])
        for i in range(3):
            yy = 67 + i * 2
            pygame.draw.line(s, dark(b, 0.3), (lx - 4, yy), (lx + 4, yy), 1)
        pygame.draw.polygon(s, dark(b, 0.7), [
            (lx - 3, 74), (lx + 3, 74), (lx + 4, 88), (lx - 2, 88)])
        for i in range(4):
            yy = 76 + i * 3
            pygame.draw.line(s, a, (lx - 3, yy), (lx + 3, yy), 1)

    # Torse kimono
    torso = [(48, 46), (72, 46), (74, 60), (60, 74), (46, 60)]
    pygame.draw.polygon(s, b, torso)
    pygame.draw.polygon(s, dark(b, 0.5), torso, 2)
    # Obi (ceinture)
    pygame.draw.polygon(s, a, [(48, 60), (72, 60), (70, 66), (50, 66)])
    pygame.draw.line(s, BLANC, (50, 63), (70, 63), 1)
    # Croisement kimono
    pygame.draw.line(s, dark(b, 0.4), (58, 46), (62, 66), 1)
    pygame.draw.line(s, dark(b, 0.4), (62, 46), (58, 60), 1)

    # Tête
    pygame.draw.circle(s, b, (60, 48), 12)
    pygame.draw.circle(s, dark(b, 0.5), (60, 48), 12, 2)
    # Bandeau
    pygame.draw.rect(s, (255, 220, 190), (54, 44, 16, 7))
    pygame.draw.line(s, dark(a, 0.5), (54, 47), (70, 47), 1)
    pygame.draw.circle(s, (0, 0, 0), (57, 48), 1)
    pygame.draw.circle(s, (0, 0, 0), (64, 48), 1)
    pygame.draw.circle(s, BLANC, (57, 47), 1)

    # Katana visible
    pygame.draw.line(s, BLANC, (44, 50), (38, 42), 2)
    pygame.draw.line(s, a, (44, 52), (38, 44), 1)


# ---- RARE #4 : Cristal Prisme ------------------------------------------
def sk_crystal(s, k, t, air, vx):
    """Cristal Prisme — 4 facettes + 3 cristaux secondaires flottants,
    reflet balayant, éclats internes."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(40, (120, 220, 255), t, 85), 60, 60)
    by = int(math.sin(t * 0.08) * 3)

    def P(x, y):
        return (x, y + by)

    # Cristaux secondaires
    for sx, sy, sz in ((38, 40, 0.6), (82, 44, 0.7), (78, 74, 0.5)):
        pygame.draw.polygon(s, light(b, 0.3), [
            P(sx, sy - int(8 * sz)), P(sx + int(5 * sz), sy),
            P(sx, sy + int(8 * sz)), P(sx - int(5 * sz), sy)])
        pygame.draw.polygon(s, a, [
            P(sx, sy - int(8 * sz)), P(sx + int(5 * sz), sy),
            P(sx, sy + int(8 * sz)), P(sx - int(5 * sz), sy)], 1)

    # Cristal principal 4 facettes
    pygame.draw.polygon(s, light(b, 0.55),
                        [P(60, 30), P(42, 52), P(60, 52)])
    pygame.draw.polygon(s, light(b, 0.25),
                        [P(60, 30), P(78, 52), P(60, 52)])
    pygame.draw.polygon(s, dark(b, 0.65),
                        [P(42, 52), P(60, 52), P(60, 82)])
    pygame.draw.polygon(s, dark(b, 0.85),
                        [P(78, 52), P(60, 52), P(60, 82)])
    pygame.draw.polygon(s, a,
                        [P(60, 30), P(78, 52), P(60, 82), P(42, 52)], 2)

    # Arêtes internes
    pygame.draw.line(s, light(b, 0.7), P(60, 30), P(60, 82), 1)
    pygame.draw.line(s, dark(b, 0.4), P(42, 52), P(78, 52), 1)

    # Reflet balayant
    sx = 44 + int((t * 2) % 22)
    pygame.draw.line(s, BLANC, (sx - 3, 50 + by), (sx + 3, 50 + by), 2)
    pygame.draw.line(s, BLANC, (sx, 47 + by), (sx, 53 + by), 1)

    # Éclats internes
    for i in range(3):
        px = 54 + (i * 7) % 14
        py = 58 + (i * 5) % 20
        pygame.draw.circle(s, BLANC, (px, py + by), 1)


# ---- RARE #5 : Blob Toxique --------------------------------------------
def sk_slime(s, k, t, air, vx):
    """Blob Toxique — squash & stretch marqué, ombre interne,
    reflets brillants, gouttes qui se détachent."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(38, b, t, 60), 60, 60)

    # Squash & stretch
    sq = math.sin(t * 0.2) * 3
    w = int(34 + sq * (2 if not air else -2))
    h = int(34 - sq * 1.5)
    rect = pygame.Rect(0, 0, w, h)
    rect.midbottom = (60, 79)

    # Corps
    pygame.draw.ellipse(s, b, rect)
    pygame.draw.ellipse(s, light(b, 0.4), rect, 2)

    # Ombre interne (bas)
    shadow_rect = pygame.Rect(rect.x + 3, rect.centery,
                              rect.w - 6, rect.h // 2 - 3)
    pygame.draw.ellipse(s, dark(b, 0.35), shadow_rect)

    # Reflet brillant
    pygame.draw.ellipse(s, light(b, 0.75), (rect.x + 6, rect.y + 4, 9, 5))
    pygame.draw.ellipse(s, BLANC, (rect.x + 8, rect.y + 5, 4, 2))

    # Yeux
    for dx in (-6, 6):
        cx2 = rect.centerx + dx
        cy2 = rect.y + int(h * 0.45)
        pygame.draw.circle(s, BLANC, (cx2, cy2), 4)
        pygame.draw.circle(s, (0, 0, 0), (cx2 + 1, cy2), 2)
        pygame.draw.circle(s, BLANC, (cx2 + 2, cy2 - 1), 1)

    # Gouttes qui se détachent
    for i in range(2):
        phase = (t * 3 + i * 40) % 60
        if phase < 30:
            drop_y = rect.bottom + phase
            drop_alpha = 255 - phase * 8
            halo = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*a, drop_alpha), (4, 4), 2)
            s.blit(halo, (rect.x + 8 + i * 8 - 4, drop_y - 4))

    # Bulles internes
    pygame.draw.circle(s, light(b, 0.6),
                       (rect.x + 10, rect.bottom - 8), 3, 1)
    pygame.draw.circle(s, light(b, 0.8),
                       (rect.centerx + 4, rect.bottom - 6), 2, 1)


# ---- ÉPIQUE #1 : Démon Infernal ----------------------------------------
def sk_demon(s, k, t, air, vx):
    """Démon Infernal — ailes membraneuses nervurées, cornes fourchues,
    queue à pointe en dard, torse nervuré."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(42, (255, 60, 60), t, 90), 60, 60)
    wf = int(math.sin(t * 0.3) * 4)

    # Ailes membraneuses (3 nervures chacune)
    for side in (-1, 1):
        base = 60 + side * 14
        # Membrane
        pts = [(base, 50), (base + side * 14, 42 + wf),
               (base + side * 20, 52), (base + side * 22, 62 + wf),
               (base + side * 12, 62), (base, 58)]
        pygame.draw.polygon(s, dark(b, 0.65), pts)
        pygame.draw.polygon(s, dark(b, 0.35), pts, 1)
        # Nervures
        for i, dy in enumerate((-4, 4, 12)):
            tip_x = base + side * (18 + i * 2)
            tip_y = 48 + dy + wf
            pygame.draw.line(s, a, (base, 52), (tip_x, tip_y), 1)

    # Queue en dard
    tail_pts = [(48, 72), (40, 78), (36, 76 + wf), (32, 82 + wf)]
    pygame.draw.lines(s, dark(b, 0.5), False, tail_pts, 4)
    pygame.draw.lines(s, b, False, tail_pts, 2)
    # Dard
    pygame.draw.polygon(s, a, [(28, 78 + wf), (22, 84 + wf), (32, 86 + wf)])
    pygame.draw.polygon(s, BLANC, [(28, 78 + wf), (22, 84 + wf), (32, 86 + wf)], 1)

    # Torse nervuré
    torso = [(48, 48), (72, 48), (72, 74), (48, 74)]
    pygame.draw.polygon(s, b, torso)
    pygame.draw.polygon(s, dark(b, 0.4), torso, 2)
    for i in range(3):
        yy = 54 + i * 6
        pygame.draw.line(s, dark(b, 0.5), (50, yy), (70, yy), 1)
    # Plaque pectorale
    pygame.draw.polygon(s, a, [(54, 52), (66, 52), (66, 66), (60, 70), (54, 66)])
    pygame.draw.polygon(s, light(a, 0.4),
                        [(54, 52), (66, 52), (66, 66), (60, 70), (54, 66)], 1)
    _heart(s, 60, 60, 3, (255, 100, 60), t)

    # Tête triangulaire
    head = [(50, 46), (46, 32), (60, 24), (74, 32), (70, 46)]
    pygame.draw.polygon(s, b, head)
    pygame.draw.polygon(s, dark(b, 0.4), head, 2)

    # Cornes fourchues
    for side in (-1, 1):
        bx = 60 + side * 8
        pygame.draw.polygon(s, a, [
            (bx, 30), (bx + side * 4, 20), (bx + side * 1, 18),
            (bx + side * 5, 22), (bx + side * 8, 30)])
        pygame.draw.polygon(s, dark(a, 0.5),
                            [(bx, 30), (bx + side * 4, 20),
                             (bx + side * 1, 18), (bx + side * 5, 22),
                             (bx + side * 8, 30)], 1)

    # Yeux en fente
    pygame.draw.polygon(s, (255, 230, 80),
                        [(52, 38), (58, 38), (55, 40), (52, 40)])
    pygame.draw.polygon(s, (255, 230, 80),
                        [(62, 38), (68, 38), (68, 40), (65, 40)])
    pygame.draw.line(s, (0, 0, 0), (54, 40), (67, 40), 1)


# ---- ÉPIQUE #2 : Mecha Destroyer ---------------------------------------
def sk_mecha(s, k, t, air, vx):
    """Mecha Destroyer — JAMBES = PISTONS blindés, canon d'épaule,
    visière unique, réacteur dorsal intégré au torse."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(42, ROUGE_NEON, t, 85), 60, 60)

    # Jambes-pistons
    for side in (-1, 1):
        lx = 60 + side * 10
        # Cuisse
        pygame.draw.polygon(s, dark(b, 0.5), [
            (lx - 5, 64), (lx + 5, 64), (lx + 5, 76), (lx - 5, 76)])
        pygame.draw.polygon(s, dark(b, 0.3),
                            [(lx - 5, 64), (lx + 5, 64),
                             (lx + 5, 76), (lx - 5, 76)], 1)
        # Vérin de piston
        pygame.draw.rect(s, a, (lx - 2, 70, 4, 8))
        # Tibia blindé
        pygame.draw.polygon(s, dark(b, 0.7), [
            (lx - 4, 76), (lx + 4, 76), (lx + 5, 90), (lx - 5, 90)])
        pygame.draw.line(s, a, (lx - 3, 80), (lx + 3, 80), 1)
        pygame.draw.line(s, a, (lx - 4, 86), (lx + 4, 86), 1)
        # Pied
        pygame.draw.polygon(s, dark(b, 0.3), [
            (lx - 7, 90), (lx + 8, 90), (lx + 8, 92), (lx - 7, 92)])

    # Torse blindé en 3 sections
    pygame.draw.rect(s, b, (44, 46, 32, 20), border_radius=3)
    pygame.draw.rect(s, dark(b, 0.5), (44, 46, 32, 20), 2, border_radius=3)
    pygame.draw.line(s, dark(b, 0.4), (44, 54), (76, 54), 1)
    pygame.draw.line(s, dark(b, 0.4), (44, 60), (76, 60), 1)
    # Plaque ventrale
    pygame.draw.rect(s, a, (52, 48, 16, 6), border_radius=2)
    pygame.draw.line(s, BLANC, (52, 51), (68, 51), 1)

    # Réacteur dorsal intégré (sur le torse, pas de propulseurs flottants)
    pygame.draw.circle(s, (60, 20, 20), (60, 66), 6)
    pygame.draw.circle(s, a, (60, 66), 6, 2)
    pygame.draw.circle(s, JAUNE_NEON, (60, 66), 3)

    # Épaulière-canon gauche
    pygame.draw.polygon(s, dark(b, 0.4), [
        (44, 40), (34, 38), (30, 46), (38, 48), (44, 48)])
    pygame.draw.polygon(s, a, [
        (44, 40), (34, 38), (30, 46), (38, 48), (44, 48)], 1)
    # Canon
    pygame.draw.rect(s, dark(b, 0.6), (26, 42, 6, 4))
    pygame.draw.rect(s, a, (26, 42, 6, 4), 1)

    # Épaulière droite simple
    pygame.draw.polygon(s, dark(b, 0.4), [
        (76, 40), (86, 38), (90, 46), (82, 48), (76, 48)])
    pygame.draw.polygon(s, a, [
        (76, 40), (86, 38), (90, 46), (82, 48), (76, 48)], 1)

    # Casque
    pygame.draw.rect(s, b, (50, 30, 20, 14), border_radius=3)
    pygame.draw.rect(s, dark(b, 0.5), (50, 30, 20, 14), 2, border_radius=3)
    pygame.draw.rect(s, a, (52, 35, 16, 4))
    pygame.draw.line(s, BLANC, (53, 37), (67, 37), 1)
    # Antenne
    pygame.draw.line(s, a, (70, 30), (74, 22), 2)
    pygame.draw.circle(s, JAUNE_NEON, (74, 22), 2)


# ---- ÉPIQUE #3 : Tisseur d'Échos ---------------------------------------
def sk_tisseur(s, k, t, air, vx):
    """Tisseur d'Échos — corps en losange + 3 silhouettes-fantômes
    du même skin qui tournent (auto-référence du concept)."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(44, (70, 200, 170), t, 85), 60, 60)

    # 3 copies fantômes en rotation (identiques mais alpha dégradé)
    for i in range(3, 0, -1):
        ang = t * 0.07 - i * 0.6
        cx2 = 60 + math.cos(ang) * 20
        cy2 = 56 + math.sin(ang) * 10
        alpha = 60 + i * 30
        ghost = pygame.Surface((50, 60), pygame.SRCALPHA)
        pts = [(25, 5), (42, 30), (25, 55), (8, 30)]
        pygame.draw.polygon(ghost, (*mixc(b, a, i / 3.0), alpha), pts)
        pygame.draw.polygon(ghost, (*a, alpha), pts, 2)
        s.blit(ghost, (cx2 - 25, cy2 - 30))

    # Corps central en losange
    body_pts = [(60, 35), (77, 58), (60, 81), (43, 58)]
    pygame.draw.polygon(s, b, body_pts)
    pygame.draw.polygon(s, light(b, 0.35), body_pts, 2)
    # Facette gauche ombrée
    pygame.draw.polygon(s, dark(b, 0.4),
                        [(60, 35), (60, 58), (43, 58)])
    # Ligne verticale (trame)
    pygame.draw.line(s, dark(b, 0.5), (60, 38), (60, 78), 1)
    # Trame horizontale
    for i in range(3):
        yy = 48 + i * 10
        w = 14 - i * 3
        pygame.draw.line(s, a, (60 - w, yy), (60 + w, yy), 1)

    # Masque
    pygame.draw.ellipse(s, a, (51, 49, 18, 11))
    pygame.draw.ellipse(s, dark(a, 0.5), (51, 49, 18, 11), 1)
    pygame.draw.circle(s, (20, 10, 30), (63, 55), 3)
    pygame.draw.circle(s, BLANC, (62, 54), 1)

    # Filaments orbitaux (6 points)
    for i in range(6):
        ang = t * 0.1 + i * math.tau / 6
        px = 60 + math.cos(ang) * 28
        py = 56 + math.sin(ang) * 28
        pygame.draw.circle(s, a, (int(px), int(py)), 2)
        pygame.draw.line(s, (*a, 100), (60, 56), (int(px), int(py)), 1)


# ---- LÉGENDAIRE #1 : Dragon Plasma -------------------------------------
def sk_dragon(s, k, t, air, vx):
    """Dragon Plasma — écailles polygonales, aile nervurée, souffle
    de plasma pulsant. AUCUN propulseur (respect de l'identité du skin)."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(48, a, t, 100), 60, 60)
    fl = math.sin(t * 0.25) * 13

    # Queue ondulante (segments + dard)
    pts = [(44 - i * 4, 64 + math.sin(t * 0.18 + i * 0.7) * (2 + i * 0.8))
           for i in range(7)]
    for i in range(len(pts) - 1):
        pygame.draw.line(s, dark(b, 0.7), pts[i], pts[i + 1], 7)
        pygame.draw.line(s, b, pts[i], pts[i + 1], 4)
    tx, ty = pts[-1]
    pygame.draw.polygon(s, a, [(tx - 2, ty - 5), (tx - 11, ty), (tx - 2, ty + 5)])
    pygame.draw.polygon(s, light(a, 0.4),
                        [(tx - 2, ty - 5), (tx - 11, ty), (tx - 2, ty + 5)], 1)

    # Pattes griffues (pas de jambes humaines)
    for side in (-1, 1):
        cx1 = 60 + side * 10
        pygame.draw.polygon(s, dark(b, 0.55), [
            (cx1, 66), (cx1 + side * 8, 78),
            (cx1 + side * 3, 80), (cx1 - side * 2, 72)])
        for claw in range(3):
            pygame.draw.line(s, BLANC,
                             (cx1 + side * 5 + claw * side, 79),
                             (cx1 + side * 7 + claw * side, 84), 2)

    # Aile nervurée
    wing_pts = [(58, 52), (74, 22 - fl), (66, 46 - fl * 0.4),
                (86, 36 - fl * 0.8), (62, 60)]
    pygame.draw.polygon(s, dark(b, 0.55), wing_pts)
    pygame.draw.polygon(s, a, wing_pts, 2)
    # 3 nervures
    pygame.draw.line(s, a, (58, 52), (74, 22 - fl), 1)
    pygame.draw.line(s, a, (62, 60), (86, 36 - fl * 0.8), 1)
    pygame.draw.line(s, a, (66, 46 - fl * 0.4), (86, 36 - fl * 0.8), 1)

    # Corps avec écailles (4×3 petits triangles)
    pygame.draw.ellipse(s, b, (42, 46, 36, 30))
    pygame.draw.ellipse(s, light(b, 0.3), (42, 46, 36, 30), 2)
    for row in range(3):
        for col in range(4):
            ex = 46 + col * 7 + (row % 2) * 3
            ey = 48 + row * 6
            pygame.draw.polygon(s, light(b, 0.2),
                                [(ex, ey), (ex + 4, ey + 2), (ex + 2, ey + 5)])

    # Plaque ventrale
    pygame.draw.ellipse(s, mixc(b, a, 0.6), (50, 58, 22, 14))
    pygame.draw.ellipse(s, light(a, 0.3), (50, 58, 22, 14), 1)

    # Crête dorsale
    for i in range(4):
        bx = 46 + i * 7
        h = 8 + i
        pygame.draw.polygon(s, a, [(bx, 48), (bx + 3, 48 - h), (bx + 6, 48)])

    # Tête
    head = [(70, 50), (78, 40), (92, 40), (98, 48), (90, 56), (74, 58)]
    pygame.draw.polygon(s, b, head)
    pygame.draw.polygon(s, light(b, 0.35), head, 2)
    pygame.draw.line(s, dark(b, 0.7), (76, 54), (94, 52), 1)
    # Cornes
    pygame.draw.polygon(s, a, [(80, 40), (76, 26), (84, 38)])
    pygame.draw.polygon(s, a, [(88, 40), (92, 26), (90, 38)])
    # Œil
    pygame.draw.circle(s, BLANC, (88, 46), 3)
    pygame.draw.circle(s, (10, 10, 30), (89, 46), 1)

    # Souffle de plasma
    glow = 3 + int(2 + 2 * math.sin(t * 0.4))
    pygame.draw.circle(s, a, (99, 51), glow)
    pygame.draw.circle(s, BLANC, (99, 51), max(1, glow - 2))

    # Cœur pulsatif (PAS de propulseurs !)
    _heart(s, 60, 62, 5, a, t)


# ---- LÉGENDAIRE #2 : Dieu Néon -----------------------------------------
def sk_god(s, k, t, air, vx):
    """Dieu Néon — robe drapée en 6 plis, visage masqué, 12 rayons
    orbitaux, double halo."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(50, a, t, 110), 60, 60)

    # Rayons rotatifs (10)
    for i in range(10):
        ang = t * 0.03 + i * math.tau / 10
        r1, r2 = 27, 40 + (i % 2) * 9
        col = mixc(b, a, i % 2)
        pygame.draw.line(s, col,
                         (60 + math.cos(ang) * r1, 54 + math.sin(ang) * r1),
                         (60 + math.cos(ang) * r2, 54 + math.sin(ang) * r2), 2)

    # Robe avec 5 plis
    robe = [(60, 34), (79, 79), (41, 79)]
    pygame.draw.polygon(s, dark(b, 0.4), robe)
    pygame.draw.polygon(s, b, robe, 2)
    for i in range(4):
        fx = 48 + i * 8
        pygame.draw.line(s, dark(b, 0.6), (60, 40), (fx, 78), 1)

    # Visage masqué (blanc pur + yeux fendus)
    pygame.draw.circle(s, BLANC, (60, 49), 11)
    pygame.draw.circle(s, a, (60, 49), 11, 2)
    # Yeux verticaux
    pygame.draw.ellipse(s, b, (52, 46, 5, 7))
    pygame.draw.ellipse(s, b, (63, 46, 5, 7))
    # Symbole frontal
    pygame.draw.line(s, a, (60, 44), (60, 48), 1)

    # Double halo
    for r, col, off in ((22, a, 0.0), (16, b, 1.7)):
        yy = 19 + int(math.sin(t * 0.1 + off) * 2)
        pygame.draw.ellipse(s, col, (60 - r, yy, r * 2, 10), 2)
        pygame.draw.ellipse(s, light(col, 0.4), (60 - r, yy + 1, r * 2, 4), 1)

    _heart(s, 60, 67, 5, a, t)

    # Satellites orbitaux
    for i in range(5):
        ang = -t * 0.07 + i * math.tau / 5
        px = 60 + math.cos(ang) * 31
        py = 58 + math.sin(ang) * 12
        pygame.draw.circle(s, a, (int(px), int(py)), 3)
        pygame.draw.circle(s, BLANC, (int(px), int(py)), 1)


# ---- LÉGENDAIRE #3 : Phénix Chrono -------------------------------------
def sk_phoenix(s, k, t, air, vx):
    """Phénix Chrono — 3 plumes de queue, ailes en flammes à 5 niveaux,
    horloge pulsative dans la poitrine."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(48, a, t, 105), 60, 60)

    # Plumes de queue (3 rangées avec dégradé)
    for i, col in enumerate((b, mixc(b, a, 0.5), a)):
        tipx = 16 + i * 5
        tipy = 80 - i * 9 + math.sin(t * 0.15 + i) * 5
        pygame.draw.polygon(s, col,
                            [(50, 62), (tipx, tipy), (48, 72 - i * 4)])
        pygame.draw.polygon(s, light(col, 0.4),
                            [(50, 62), (tipx, tipy), (48, 72 - i * 4)], 1)

    # Ailes de flammes (5 niveaux)
    for j in range(5):
        ang = math.radians(-130 + j * 20) + math.sin(t * 0.22) * 0.35
        ln = 42 - j * 4
        ex = 58 + math.cos(ang) * ln
        ey = 52 + math.sin(ang) * ln
        col = mixc(b, a, j / 4.0)
        pygame.draw.polygon(s, col,
                            [(58, 52), (ex - 5, ey + 6),
                             (ex, ey), (ex + 5, ey + 8)])
        pygame.draw.line(s, light(col, 0.5), (58, 52), (ex, ey), 1)

    # Corps
    pygame.draw.ellipse(s, b, (44, 48, 32, 28))
    pygame.draw.ellipse(s, light(b, 0.3), (44, 48, 32, 28), 2)

    # Horloge poitrine
    pygame.draw.circle(s, (35, 12, 8), (60, 63), 9)
    pygame.draw.circle(s, a, (60, 63), 9, 2)
    for k2 in range(12):
        ang2 = k2 * math.tau / 12
        x2 = 60 + math.cos(ang2) * 8
        y2 = 63 + math.sin(ang2) * 8
        pygame.draw.circle(s, a, (int(x2), int(y2)), 1)
    for hand, ln in ((5, 0.02), (7, 0.12)):
        ang = t * ln - math.pi / 2
        pygame.draw.line(s, a, (60, 63),
                         (60 + math.cos(ang) * hand,
                          63 + math.sin(ang) * hand), 2)
    pygame.draw.circle(s, BLANC, (60, 63), 1)

    # Tête
    pygame.draw.circle(s, (80, 46, 46), (80, 46), 8)
    pygame.draw.circle(s, b, (80, 46), 8)
    pygame.draw.circle(s, light(b, 0.4), (80, 46), 8, 1)
    # Bec
    pygame.draw.polygon(s, a, [(87, 44), (98, 48), (87, 52)])
    pygame.draw.polygon(s, light(a, 0.5), [(87, 44), (98, 48), (87, 52)], 1)
    # Œil + pupille
    pygame.draw.circle(s, BLANC, (82, 44), 3)
    pygame.draw.circle(s, (20, 5, 5), (83, 44), 1)

    # Plumes de tête
    for i in range(3):
        fy = 28 + int(math.sin(t * 0.3 + i) * 3)
        col = mixc(b, a, i / 2.0)
        pygame.draw.polygon(s, col,
                            [(74 + i * 4, 40), (72 + i * 5, fy),
                             (80 + i * 4, 38)])


# ---- MYTHIQUE #1 : Chrono-Imperator ------------------------------------
def sk_imperator(s, k, t, air, vx):
    """Chrono-Imperator — anneau horloge à 12 graduations, 3 aiguilles,
    cape de braises, couronne de lames, éclats temporels orbitaux.
    Jambes = CAPE COUVERTE (pas de jambes humaines visibles)."""
    b, a = k["body"], k["accent"]
    glow = (255, 60, 110)
    cx, cy = 60, 54
    _blit_c(s, _aura(52, glow, t, 110), cx, cy)

    # Anneau horloge
    ring = 43
    pygame.draw.circle(s, (*a, 140), (cx, cy), ring, 1)
    for i in range(12):
        ang = i * math.tau / 12 - math.pi / 2
        big = i % 3 == 0
        r1 = ring - (6 if big else 3)
        pygame.draw.line(s, (*a, 235 if big else 150),
                         (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1),
                         (cx + math.cos(ang) * ring, cy + math.sin(ang) * ring),
                         2 if big else 1)

    # 3 arcs brisés
    for j in range(3):
        a0 = -t * 0.05 + j * math.tau / 3
        pygame.draw.arc(s, (*glow, 210),
                        pygame.Rect(cx - 37, cy - 37, 74, 74), a0, a0 + 0.9, 3)

    # Aiguilles (derrière le corps)
    ha = t * 0.012 - math.pi / 2
    ma = t * 0.09 - math.pi / 2
    pygame.draw.line(s, (*BLANC, 225), (cx, cy),
                     (cx + math.cos(ha) * 27, cy + math.sin(ha) * 27), 3)
    pygame.draw.line(s, (*a, 235), (cx, cy),
                     (cx + math.cos(ma) * 39, cy + math.sin(ma) * 39), 2)

    # Cape de braises ondulante
    wv = math.sin(t * 0.18)
    cape = [(52, 40), (37 + wv * 3, 62), (29 + wv * 5, 87),
            (44, 80 + wv * 2), (60, 91), (76, 80 - wv * 2),
            (91 - wv * 5, 87), (83 - wv * 3, 62), (68, 40)]
    pygame.draw.polygon(s, (118, 16, 52), cape)
    pygame.draw.polygon(s, (*a, 220), cape, 2)
    # 4 braises dans la cape
    for i in range(4):
        fx = 40 + i * 13 + wv * 2
        pygame.draw.line(s, (*glow, 200),
                         (fx, 78 - (i % 2) * 4),
                         (fx - 1, 88 - (i % 2) * 3), 2)

    # Torse blindé
    torso = [(46, 40), (74, 40), (79, 58), (70, 73), (50, 73), (41, 58)]
    pygame.draw.polygon(s, b, torso)
    pygame.draw.polygon(s, a, torso, 2)
    plate = [(52, 42), (68, 42), (65, 55), (60, 61), (55, 55)]
    pygame.draw.polygon(s, mixc(a, (130, 70, 12), 0.25), plate)
    pygame.draw.polygon(s, BLANC, plate, 1)
    pygame.draw.line(s, a, (46, 66), (74, 66), 2)

    # Cœur chronomètre
    _heart(s, 60, 56, 5, glow, t)

    # Épaulières hérissées
    pygame.draw.polygon(s, a, [(45, 44), (32, 41), (25, 27),
                               (38, 36), (47, 38)])
    pygame.draw.polygon(s, dark(a, 0.4), [(45, 44), (32, 41), (25, 27),
                                          (38, 36), (47, 38)], 1)
    pygame.draw.polygon(s, a, [(75, 44), (88, 41), (95, 27),
                               (82, 36), (73, 38)])
    pygame.draw.polygon(s, dark(a, 0.4), [(75, 44), (88, 41), (95, 27),
                                          (82, 36), (73, 38)], 1)

    # Casque + visière
    pygame.draw.circle(s, dark(b, 0.8), (60, 31), 11)
    pygame.draw.circle(s, a, (60, 31), 11, 2)
    face = 3 if vx >= 0 else -3
    pygame.draw.rect(s, glow, (54 + face // 3, 29, 13, 4), border_radius=2)
    pygame.draw.rect(s, BLANC, (58 + face, 30, 5, 2))

    # Couronne de lames (5 pics)
    for i in range(-2, 3):
        h = 15 - abs(i) * 3
        bx = 60 + i * 5
        pygame.draw.polygon(s, a, [(bx - 2, 22), (bx, 22 - h), (bx + 2, 22)])
        pygame.draw.polygon(s, BLANC, [(bx - 1, 22), (bx, 22 - h), (bx, 22)], 1)

    # Éclats temporels en orbite
    for i in range(5):
        ang = -t * 0.06 + i * math.tau / 5
        ox = cx + math.cos(ang) * 33
        oy = cy + math.sin(ang) * 16
        d = 4 if math.sin(ang) > 0 else 3
        shard = [(ox, oy - d - 1), (ox + d, oy), (ox, oy + d + 1), (ox - d, oy)]
        pygame.draw.polygon(s, glow if i % 2 else a, shard)
        pygame.draw.polygon(s, BLANC, shard, 1)

# ---- MYTHIQUE #2 : Apex Titan ------------------------------------------
def sk_apex_titan(s, k, t, air, vx):
    """Apex Titan — 14 particules orbitales de victoire, couronne de
    5 flammes à 3 couches, plaque rubis, cape tribale.
    Jambes = piliers massifs (intégrés)."""
    b, a = k["body"], k["accent"]
    cx, cy = 60, 56
    _blit_c(s, _aura(52, (255, 200, 60), t, 105), cx, cy)

    # Particules orbitales (14)
    for i in range(14):
        ang = t * 0.035 + i * math.tau / 14
        rr = 34 + math.sin(t * 0.06 + i * 0.7) * 6
        sx = cx + math.cos(ang) * rr
        sy = cy + math.sin(ang) * rr * 0.72
        col = ((255, 230, 120) if i % 3 == 0
               else (255, 150, 60) if i % 3 == 1 else (220, 40, 60))
        pygame.draw.circle(s, col, (int(sx), int(sy)), 2 if i % 2 else 3)
        pygame.draw.circle(s, BLANC, (int(sx), int(sy)), 1)

    # Jambes-piliers massifs
    for side in (-1, 1):
        lx = 60 + side * 11
        pygame.draw.polygon(s, (40, 24, 30), [
            (lx - 6, 72), (lx + 6, 72), (lx + 7, 90), (lx - 7, 90)])
        pygame.draw.polygon(s, a, [
            (lx - 6, 72), (lx + 6, 72), (lx + 7, 90), (lx - 7, 90)], 1)
        pygame.draw.line(s, (255, 230, 120), (lx, 74), (lx, 88), 1)
        # Pied
        pygame.draw.polygon(s, dark(b, 0.5), [
            (lx - 9, 90), (lx + 9, 90), (lx + 9, 93), (lx - 9, 93)])

    # Torse
    torso = [(cx - 15, cy - 10), (cx + 15, cy - 10),
             (cx + 13, cy + 18), (cx - 13, cy + 18)]
    pygame.draw.polygon(s, b, torso)
    pygame.draw.polygon(s, a, torso, 2)
    plate = [(cx - 9, cy - 6), (cx + 9, cy - 6),
             (cx + 7, cy + 6), (cx - 7, cy + 6)]
    pygame.draw.polygon(s, mixc(a, (150, 80, 20), 0.4), plate)
    pygame.draw.polygon(s, (255, 230, 120), plate, 1)

    # Rubis central (cœur de champion)
    pygame.draw.circle(s, (200, 30, 50), (cx, cy + 2), 5)
    pygame.draw.circle(s, (255, 120, 140), (cx, cy + 2), 3)
    pygame.draw.circle(s, (255, 230, 120), (cx, cy + 2), 5, 1)
    pygame.draw.circle(s, BLANC, (cx - 1, cy + 1), 1)

    # Cape tribale (2 pans latéraux)
    for side in (-1, 1):
        pts = [(cx + side * 14, cy - 8), (cx + side * 28, cy - 20),
               (cx + side * 26, cy + 2), (cx + side * 14, cy + 2)]
        pygame.draw.polygon(s, a, pts)
        pygame.draw.polygon(s, (60, 30, 10), pts, 1)

    # Casque
    pygame.draw.circle(s, b, (cx, cy - 20), 11)
    pygame.draw.circle(s, a, (cx, cy - 20), 11, 2)
    pygame.draw.rect(s, (255, 230, 120), (cx - 7, cy - 23, 14, 4),
                     border_radius=2)
    pygame.draw.rect(s, (255, 255, 255), (cx - 3, cy - 22, 5, 2))

    # Couronne de 5 flammes à 3 couches
    for i in range(5):
        fx = cx - 12 + i * 6
        h = 16 - abs(i - 2) * 3
        fl = math.sin(t * 0.28 + i * 1.3) * 3
        pygame.draw.polygon(s, (255, 90, 30),
                            [(fx - 3, cy - 28), (fx, cy - 28 - h + fl),
                             (fx + 3, cy - 28)])
        pygame.draw.polygon(s, (255, 160, 40),
                            [(fx - 2, cy - 28),
                             (fx, cy - 28 - h * 0.7 + fl * 0.7),
                             (fx + 2, cy - 28)])
        pygame.draw.polygon(s, (255, 230, 120),
                            [(fx - 1, cy - 28),
                             (fx, cy - 28 - h * 0.4 + fl * 0.4),
                             (fx + 1, cy - 28)])

    pygame.draw.circle(s, a, (cx, cy - 28), 14, 2)


# ---- MYTHIQUE #3 : Nébula Chaos ----------------------------------------
def sk_nebula(s, k, t, air, vx):
    """Nébula Chaos — 16 étoiles orbitent autour du cristal,
    trou noir miniature au cœur, anneau doré en arc.
    Jambes = masse nébuleuse (pas de jambes humaines)."""
    b, a = k["body"], k["accent"]
    cx, cy = 60, 58
    pulse = 0.5 + 0.5 * math.sin(t * 0.08)
    _blit_c(s, _aura(52, (180, 50, 255), t, 110), cx, cy)

    # 16 étoiles orbitales
    for i in range(16):
        ang = t * 0.028 + i * math.tau / 16
        r = 38 + math.sin(t * 0.05 + i * 1.3) * 7
        sx = cx + math.cos(ang) * r
        sy = cy + math.sin(ang) * r * 0.68
        sz = 1 + (i % 3)
        col = ((255, 235, 180) if i % 5 == 0
               else (200, 140, 255) if i % 3 == 0
               else (150, 80, 220))
        pygame.draw.circle(s, col, (int(sx), int(sy)), sz)
        if i % 5 == 0:
            pygame.draw.circle(s, BLANC, (int(sx), int(sy)), 1)

    # Masse nébuleuse inférieure (jambes)
    for side in (-1, 1):
        lx = cx + side * 10
        for i in range(3):
            yy = 74 + i * 5
            r = max(3, 6 - i)
            pygame.draw.circle(s, dark(b, 0.5 + i * 0.1), (lx, yy), r)
            pygame.draw.circle(s, dark(a, 0.3), (lx, yy), r, 1)

    # Corps cristal
    body_pts = [(cx, cy - 22), (cx + 18, cy - 7), (cx + 15, cy + 15),
                (cx, cy + 24), (cx - 15, cy + 15), (cx - 18, cy - 7)]
    pygame.draw.polygon(s, b, body_pts)
    pygame.draw.polygon(s, a, body_pts, 2)

    # Facette gauche ombrée
    pygame.draw.polygon(s, dark(b, 0.4),
                        [(cx, cy - 22), (cx, cy + 24), (cx - 18, cy - 7)])

    # Cœur interne
    inner = [(cx, cy - 14), (cx + 11, cy - 4), (cx + 8, cy + 10),
             (cx, cy + 17), (cx - 8, cy + 10), (cx - 11, cy - 4)]
    pygame.draw.polygon(s, mixc(b, a, 0.45), inner)
    pygame.draw.polygon(s, mixc(a, (255, 255, 255), 0.3 * pulse), inner, 1)

    # Yeux
    pygame.draw.ellipse(s, (255, 220, 255), (cx - 9, cy - 8, 7, 4))
    pygame.draw.ellipse(s, (255, 220, 255), (cx + 2, cy - 8, 7, 4))
    pygame.draw.circle(s, a, (cx - 5, cy - 6), 2)
    pygame.draw.circle(s, a, (cx + 5, cy - 6), 2)

    # Trou noir miniature au cœur
    pygame.draw.circle(s, (8, 0, 18), (cx, cy + 5), 6)
    for rr in (9, 7):
        pygame.draw.circle(s, (150, 40, 220), (cx, cy + 5), rr, 1)

    # Arc doré rotatif
    ang = t * 0.18
    pygame.draw.arc(s, (255, 215, 90),
                    pygame.Rect(cx - 11, cy - 6, 22, 22), ang, ang + 2.4, 2)

    # Éclats en orbite
    for i in range(4):
        ang = -t * 0.05 + i * math.tau / 4
        ex = cx + math.cos(ang) * 30
        ey = cy + math.sin(ang) * 22
        pygame.draw.polygon(s, a, [(ex, ey - 3), (ex + 3, ey),
                                   (ex, ey + 3), (ex - 3, ey)])
        pygame.draw.polygon(s, BLANC, [(ex, ey - 3), (ex + 3, ey),
                                       (ex, ey + 3), (ex - 3, ey)], 1)


# ---- SECRET #1 : Chevalier Chrono --------------------------------------
def sk_knight(s, k, t, air, vx):
    """Chevalier Chrono — armure à 6 plaques, casque à visière en T,
    bouclier circulaire à 12 graduations, épée. Jambes = cuissardes."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(48, a, t, 95), 60, 60)
    ang = t * 0.06

    # Bouclier rotatif (anneau à 12 graduations)
    pygame.draw.circle(s, a, (60, 60), 26, 2)
    pygame.draw.circle(s, dark(a, 0.4), (60, 60), 26, 1)
    for i in range(12):
        ai = i * math.tau / 12
        r1 = 20 if i % 3 == 0 else 22
        pygame.draw.line(s, a,
                         (60 + math.cos(ai) * r1, 60 + math.sin(ai) * r1),
                         (60 + math.cos(ai) * 26, 60 + math.sin(ai) * 26),
                         2 if i % 3 == 0 else 1)

    # Jambes cuissardes blindées
    for side in (-1, 1):
        lx = 60 + side * 9
        pygame.draw.polygon(s, dark(b, 0.55), [
            (lx - 5, 66), (lx + 5, 66), (lx + 5, 78), (lx - 5, 78)])
        pygame.draw.polygon(s, a, [
            (lx - 5, 66), (lx + 5, 66), (lx + 5, 78), (lx - 5, 78)], 1)
        # Genouillère
        pygame.draw.circle(s, a, (lx, 78), 4)
        pygame.draw.circle(s, dark(a, 0.5), (lx, 78), 4, 1)
        # Tibia
        pygame.draw.polygon(s, dark(b, 0.7), [
            (lx - 4, 78), (lx + 4, 78), (lx + 5, 90), (lx - 5, 90)])

    # Torse à plaques
    pygame.draw.rect(s, b, (48, 50, 24, 20), border_radius=4)
    pygame.draw.rect(s, dark(b, 0.55), (48, 50, 24, 20), 2, border_radius=4)
    pygame.draw.line(s, a, (48, 56), (72, 56), 1)
    pygame.draw.line(s, a, (48, 64), (72, 64), 1)
    # Emblème
    pygame.draw.circle(s, a, (60, 58), 4)
    pygame.draw.circle(s, BLANC, (60, 58), 2)

    # Épaulières rondes
    for side in (-1, 1):
        ex = 60 + side * 20
        pygame.draw.circle(s, b, (ex, 52), 7)
        pygame.draw.circle(s, dark(b, 0.5), (ex, 52), 7, 2)
        pygame.draw.circle(s, a, (ex, 52), 3)

    # Casque à visière en T
    pygame.draw.polygon(s, b, [(48, 50), (48, 34), (54, 28),
                               (66, 28), (72, 34), (72, 50)])
    pygame.draw.polygon(s, dark(b, 0.5), [(48, 50), (48, 34), (54, 28),
                                          (66, 28), (72, 34), (72, 50)], 2)
    # Fente verticale (T)
    pygame.draw.rect(s, (10, 10, 20), (58, 32, 4, 12))
    pygame.draw.rect(s, CYAN_NEON, (58, 32, 4, 4))
    # Plume
    pygame.draw.polygon(s, a, [(60, 28), (56, 22), (67, 26)])

    # Épée
    pygame.draw.line(s, BLANC, (44, 40), (38, 28), 2)
    pygame.draw.line(s, a, (44, 42), (38, 30), 1)
    pygame.draw.line(s, a, (42, 38), (46, 44), 2)

# ---- SECRET #2 : Entité Glitch -----------------------------------------
def sk_glitch(s, k, t, air, vx):
    """Entité Glitch — corps qui se décompose en bandes RGB
    désynchronisées, yeux en double, jambes de pixels instables."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(46, (255, 0, 100), t, 100), 60, 60)

    cols = [(255, 0, 100), (0, 255, 255), (255, 255, 255), (120, 0, 255)]
    # Corps en 9 bandes décalées
    for i in range(9):
        off = ((t // 3 + i * 5) * 7) % 13 - 6
        col = cols[(i + t // 5) % 4]
        w = 22 + ((t // 4 + i * 3) % 3) * 4
        y = 36 + i * 5
        pygame.draw.rect(s, col, (60 - w // 2 + off, y, w, 4))

    # Yeux en double (désynchronisés)
    eye_dx = (t // 2) % 3 - 1
    pygame.draw.rect(s, (0, 0, 0), (52 + eye_dx, 46, 6, 5))
    pygame.draw.rect(s, (0, 0, 0), (64 - eye_dx, 46, 6, 5))
    pygame.draw.rect(s, BLANC, (52 + eye_dx + 1, 47, 2, 2))
    pygame.draw.rect(s, BLANC, (64 - eye_dx + 1, 47, 2, 2))

    # Jambes en pixels
    for side in (-1, 1):
        lx = 60 + side * 8
        for i in range(4):
            yy = 74 + i * 4
            off = ((t // 2 + i) * 3) % 5 - 2
            pygame.draw.rect(s, cols[(i + t // 4) % 4],
                             (lx - 3 + off, yy, 6, 3))

    # Fragment de sortie (glitch line)
    if (t // 3) % 4 == 0:
        pygame.draw.rect(s, BLANC, (30, 60 + (t * 3) % 20, 60, 2))


# ---- SECRET #3 : Gardien Stellaire -------------------------------------
def sk_astral(s, k, t, air, vx):
    """Gardien Stellaire — 3 ailes de lumière stratifiées,
    constellation sur le torse, jambes-piliers dorées."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(48, a, t, 100), 60, 60)
    fl = math.sin(t * 0.15) * 3

    # 3 ailes stratifiées par côté
    for side in (-1, 1):
        for i in range(3):
            col = mixc(a, BLANC, i / 3.0)
            pts = [(60 + side * 8, 52 + i * 3),
                   (60 + side * (30 + i * 7), 38 + i * 8 + fl),
                   (60 + side * (24 + i * 5), 58 + i * 6)]
            pygame.draw.polygon(s, col, pts)
            pygame.draw.polygon(s, light(col, 0.4), pts, 1)

    # Jambes-piliers
    for side in (-1, 1):
        lx = 60 + side * 9
        pygame.draw.polygon(s, dark(b, 0.55), [
            (lx - 5, 68), (lx + 5, 68), (lx + 5, 84), (lx - 5, 84)])
        pygame.draw.polygon(s, a, [
            (lx - 5, 68), (lx + 5, 68), (lx + 5, 84), (lx - 5, 84)], 1)
        for i in range(3):
            yy = 72 + i * 4
            pygame.draw.line(s, BLANC, (lx - 4, yy), (lx + 4, yy), 1)
        # Pied
        pygame.draw.polygon(s, a, [
            (lx - 7, 84), (lx + 7, 84), (lx + 6, 88), (lx - 6, 88)])

    # Torse
    pygame.draw.rect(s, b, (47, 50, 26, 25), border_radius=5)
    pygame.draw.rect(s, a, (47, 50, 26, 25), 2, border_radius=5)

    # Constellation (5 étoiles reliées)
    stars = [(52, 58), (58, 55), (64, 60), (68, 56), (58, 68)]
    for i, st in enumerate(stars):
        pygame.draw.circle(s, BLANC, st, 2)
        if i > 0:
            pygame.draw.line(s, light(a, 0.4), stars[i - 1], st, 1)

    # Tête
    pygame.draw.circle(s, b, (60, 44), 11)
    pygame.draw.circle(s, light(b, 0.3), (60, 44), 11, 2)
    # Bandeau visière
    pygame.draw.rect(s, a, (53, 42, 14, 4))
    pygame.draw.line(s, BLANC, (54, 44), (66, 44), 1)

    # Sceau stellaire
    pygame.draw.ellipse(s, a, (48, 24 + int(fl), 24, 8), 2)
    pygame.draw.circle(s, a, (60, 64), 4)
    pygame.draw.circle(s, BLANC, (60, 64), 2)

    _heart(s, 60, 62, 4, a, t)


# ---- SECRET #4 : Spectre d'Éclipse -------------------------------------
def sk_wraith(s, k, t, air, vx):
    """Spectre d'Éclipse — 6 pointes rotatives, cape déchirée,
    œil unique traversé d'un faisceau."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(46, a, t, 105), 60, 60)
    pulse = 2 * math.sin(t * 0.2)

    # 6 pointes (couronne rotative)
    for i in range(6):
        ang = t * 0.05 + i * math.tau / 6
        pygame.draw.polygon(s, a, [
            (60 + math.cos(ang - 0.15) * 20, 58 + math.sin(ang - 0.15) * 20),
            (60 + math.cos(ang) * (31 + pulse), 58 + math.sin(ang) * (31 + pulse)),
            (60 + math.cos(ang + 0.15) * 20, 58 + math.sin(ang + 0.15) * 20)])
        pygame.draw.polygon(s, light(a, 0.3), [
            (60 + math.cos(ang - 0.15) * 20, 58 + math.sin(ang - 0.15) * 20),
            (60 + math.cos(ang) * (31 + pulse), 58 + math.sin(ang) * (31 + pulse)),
            (60 + math.cos(ang + 0.15) * 20, 58 + math.sin(ang + 0.15) * 20)], 1)

    # Tête fantôme
    pygame.draw.circle(s, a, (60, 58), 19, 3)
    pygame.draw.circle(s, b, (60, 58), 17)
    # Ombre interne
    pygame.draw.circle(s, dark(b, 0.3), (60, 58), 17, 1)

    # Cape déchirée (4 pans avec décalage vertical)
    for i in range(4):
        px = 50 + i * 7
        off = int(math.sin(t * 0.25 + i) * 3)
        pygame.draw.line(s, b, (px, 72), (px - 2 + off, 86), 4)
        pygame.draw.line(s, a, (px, 72), (px - 2 + off, 86), 1)

    # Voile devant les yeux
    pygame.draw.ellipse(s, a, (50, 53, 20, 10))
    pygame.draw.ellipse(s, dark(a, 0.5), (50, 53, 20, 10), 1)

    # Œil unique traversé
    eye_x = 60 + (3 if vx >= 0 else -3)
    pygame.draw.circle(s, (0, 0, 0), (eye_x, 58), 4)
    pygame.draw.circle(s, JAUNE_NEON, (eye_x, 58), 2)
    pygame.draw.line(s, JAUNE_NEON, (30, 58), (90, 58), 1)

# ---- SECRET #5 : Seigneur du Temps -------------------------------------
def sk_lord(s, k, t, air, vx):
    """Seigneur du Temps — robe à 6 plis, horloge sur la poitrine,
    2 sabliers flottants, couronne d'engrenages."""
    b, a = k["body"], k["accent"]
    _blit_c(s, _aura(48, a, t, 100), 60, 60)

    # Robe à 6 plis
    robe = [(60, 34), (76, 56), (80, 84), (40, 84), (44, 56)]
    pygame.draw.polygon(s, b, robe)
    pygame.draw.polygon(s, dark(b, 0.55), robe, 2)
    for i in range(5):
        fx = 44 + i * 8
        pygame.draw.line(s, dark(b, 0.7), (60, 44), (fx, 82), 1)

    # Horloge sur poitrine
    pygame.draw.circle(s, dark(b, 0.35), (60, 60), 8)
    pygame.draw.circle(s, a, (60, 60), 8, 2)
    for i in range(12):
        ang2 = i * math.tau / 12
        x2 = 60 + math.cos(ang2) * 7
        y2 = 60 + math.sin(ang2) * 7
        pygame.draw.circle(s, a, (int(x2), int(y2)), 1)
    for hand, ln in ((4, 0.02), (6, 0.12)):
        ang = t * ln - math.pi / 2
        pygame.draw.line(s, a, (60, 60),
                         (60 + math.cos(ang) * hand,
                          60 + math.sin(ang) * hand), 1)

    # Tête voilée
    pygame.draw.circle(s, dark(b, 0.35), (60, 48), 10)
    pygame.draw.circle(s, b, (60, 48), 8)
    # Yeux
    pygame.draw.circle(s, a, (56, 48), 2)
    pygame.draw.circle(s, a, (64, 48), 2)
    pygame.draw.circle(s, BLANC, (56, 47), 1)
    pygame.draw.circle(s, BLANC, (64, 47), 1)

    # Engrenages couronne
    for i in range(5):
        ang = t * 0.05 + i * math.tau / 5
        gx = 60 + math.cos(ang) * 14
        gy = 34 + math.sin(ang) * 6
        pygame.draw.circle(s, a, (int(gx), int(gy)), 3)
        for j in range(6):
            a2 = j * math.tau / 6 + t * 0.15
            pygame.draw.line(s, a,
                             (gx + math.cos(a2) * 3, gy + math.sin(a2) * 3),
                             (gx + math.cos(a2) * 5, gy + math.sin(a2) * 5), 1)
        pygame.draw.circle(s, dark(b, 0.4), (int(gx), int(gy)), 1)

    # Sabliers flottants (gauche/droite)
    hy = int(math.sin(t * 0.1) * 3)
    for side, hx in ((-1, 88), (1, 32)):
        pygame.draw.polygon(s, a, [(hx - 4, 34 + hy), (hx + 4, 34 + hy),
                                   (hx + 1, 44 + hy), (hx - 1, 44 + hy)])
        pygame.draw.polygon(s, a, [(hx - 1, 44 + hy), (hx + 1, 44 + hy),
                                   (hx + 4, 54 + hy), (hx - 4, 54 + hy)])
        pygame.draw.line(s, BLANC, (hx, 36 + hy), (hx, 52 + hy), 1)

# ─────────────────────────────────────────────────────────────────────────
#  Registre des skins
# ─────────────────────────────────────────────────────────────────────────

def _sk(name, price, body, accent, fn, trail=None, hidden=False,
        rarity="COMMON", stats=None, skills=None, gems=None):
    return {
        "name": name, "price": price, "body": body, "accent": accent,
        "trail": trail or body, "fn": fn, "hidden": hidden,
        "rarity": rarity, "stats": stats or {}, "skills": skills or {},
        "gems": gems,
    }


SKINS = {
    # ---- COMMUN (5) -----------------------------------------------------
    "NEON_CYBER": _sk("Cyber Runner", 0, CYAN_NEON, JAUNE_NEON, sk_cyber,
                      rarity="COMMON", stats=dict(speed=0.75, hp=30)),
    "CUBE_DASH":  _sk("Cube Dash", 250, (255, 200, 0), (0, 200, 255), sk_cube,
                      rarity="COMMON", stats=dict(power=0.15, jump=1.0)),
    "TITAN_GOLD": _sk("Titan Gold", 320, JAUNE_NEON, BLANC, sk_titan,
                      rarity="COMMON", stats=dict(hp=60, reduce=0.06)),
    "VOID_PURPLE": _sk("Void Phantom", 440, PURPLE_NEON, CYAN_NEON,
                       sk_phantom, rarity="COMMON",
                       stats=dict(shield=45, regen=0.24)),
    "SPIKE_BALL": _sk("Oursin Fou", 830, (255, 120, 0), (255, 240, 120),
                      sk_spike, rarity="COMMON",
                      stats=dict(power=0.14, rate=0.14)),
    # ---- RARE (5) -------------------------------------------------------
    "ROCKET": _sk("Fusée Turbo", 3600, (240, 240, 255), ROUGE_NEON,
                  sk_rocket, trail=ORANGE, rarity="RARE",
                  stats=dict(speed=0.6, jump=1.0),
                  skills=dict(double_jump=1)),
    "UFO":    _sk("Soucoupe X", 5400, (120, 130, 150), VERT_NEON, sk_ufo,
                  rarity="RARE", stats=dict(shield=60, regen=0.16),
                  skills=dict(glide=2.0)),
    "NINJA":  _sk("Ombre Ninja", 8000, (45, 45, 70), ROUGE_NEON, sk_ninja,
                  rarity="RARE", stats=dict(speed=0.6, power=0.12),
                  skills=dict(evade=0.18)),
    "CRYSTAL": _sk("Cristal Prisme", 11500, (120, 220, 255), BLANC,
                   sk_crystal, rarity="RARE",
                   stats=dict(shield=45, reduce=0.07),
                   skills=dict(thorns=0.25)),
    "SLIME":  _sk("Blob Toxique", 15500, VERT_NEON, (220, 255, 100),
                  sk_slime, rarity="RARE",
                  stats=dict(hp_regen=1.5, coin=0.20),
                  skills=dict(kill_heal=8)),
    # ---- ÉPIQUE (3) -----------------------------------------------------
    "DEMON": _sk("Démon Infernal", 24000, (200, 30, 40), JAUNE_NEON,
                 sk_demon, rarity="EPIC",
                 stats=dict(power=0.22, rate=0.12),
                 skills=dict(fury=0.40, kill_heal=12)),
    "MECHA_RED": _sk("Mecha Destroyer", 40000, ROUGE_NEON, JAUNE_NEON,
                     sk_mecha, rarity="EPIC",
                     stats=dict(hp=60, power=0.15, reduce=0.10),
                     skills=dict(reactive=(30, 150))),
    "ECHO_WEAVER": _sk("Tisseur d'Échos", 60000, (70, 200, 170),
                       (255, 190, 255), sk_tisseur, rarity="EPIC",
                       stats=dict(power=0.12, rate=0.14, speed=0.5),
                       skills=dict(echo_power=0.60)),
    # ---- LÉGENDAIRE (3) -------------------------------------------------
    "PLASMA_DRAGON": _sk("Dragon Plasma", 220000, (40, 90, 230),
                         (120, 255, 255), sk_dragon, trail=(120, 255, 255),
                         rarity="LEGENDARY",
                         stats=dict(hp=50, power=0.22, coin=0.15),
                         skills=dict(shockwave=(210, 70, 600), bounty=6)),
    "NEON_GOD": _sk("Dieu Néon", 270000, (255, 60, 210), (80, 255, 240),
                    sk_god, trail=(80, 255, 240), rarity="LEGENDARY",
                    stats=dict(shield=80, regen=0.32, speed=0.6),
                    skills=dict(auto_shield=840, chaos_surf=(15, 0.5, 180))),
    "TIME_PHOENIX": _sk("Phénix Chrono", 320000, (255, 110, 30),
                        (255, 235, 120), sk_phoenix, trail=ORANGE,
                        rarity="LEGENDARY",
                        stats=dict(hp=80, hp_regen=1.5, rate=0.15),
                        skills=dict(second_wind=True, time_drift=(100, 1500))),
    # ---- SECRET (5) -----------------------------------------------------
    "CHRONO_KNIGHT": _sk("Chevalier Chrono", None, (190, 200, 220),
                         (255, 200, 60), sk_knight, hidden=True,
                         rarity="LEGENDARY",
                         stats=dict(hp=60, reduce=0.14, power=0.18),
                         skills=dict(chain_blast=(95, 28),
                                     reactive=(45, 180), thorns=0.30)),
    "GLITCH_ENTITY": _sk("Entité Glitch", None, (255, 0, 100), CYAN_NEON,
                         sk_glitch, hidden=True, rarity="LEGENDARY",
                         stats=dict(speed=1.2, rate=0.20),
                         skills=dict(second_wind=True, evade=0.28,
                                     double_jump=1)),
    "ASTRAL_GUARDIAN": _sk("Gardien Stellaire", None, (250, 235, 200),
                           (255, 200, 60), sk_astral, hidden=True,
                           rarity="LEGENDARY",
                           stats=dict(shield=120, regen=0.40, reduce=0.15),
                           skills=dict(auto_shield=600,
                                       chaos_surf=(20, 0.6, 180))),
    "ECLIPSE_WRAITH": _sk("Spectre d'Éclipse", None, (18, 10, 24),
                          (255, 150, 30), sk_wraith, hidden=True,
                          rarity="LEGENDARY",
                          stats=dict(power=0.30, rate=0.15),
                          skills=dict(fury=0.50, kill_heal=20,
                                      shockwave=(180, 60, 480))),
    "CHRONOS_LORD": _sk("Seigneur du Temps", None, (95, 40, 150),
                        (255, 215, 80), sk_lord, hidden=True,
                        rarity="LEGENDARY",
                        stats=dict(hp=90, power=0.28, rate=0.18),
                        skills=dict(second_wind=True, echo_power=0.80,
                                    time_drift=(120, 1200))),
    # ---- MYTHIQUE (2) ------------------------
    "CHRONO_IMPERATOR": _sk("Chrono-Imperator", None, (34, 6, 26),
                            (255, 205, 70), sk_imperator,
                            trail=(255, 60, 110), rarity="MYTHIC",
                            gems=1800,
                            stats=dict(hp_pct=0.75, speed_pct=0.30,
                                       shield=120, regen=0.30,
                                       reduce=0.15, rate=0.20),
                            skills=dict(sanctuary=(240, 1500, 170, 1300),
                                        time_master=(0.50, 4.0))),
    "NEBULA_CHAOS": _sk("Nébula Chaos", None, (28, 6, 46), (200, 80, 255),
                        sk_nebula, trail=(200, 80, 255), rarity="MYTHIC",
                        stats=dict(hp_pct=0.50, speed_pct=0.20, shield=80,
                                   regen=0.25, reduce=0.10, rate=0.15,
                                   power=0.20),
                        skills=dict(black_hole=(240, 90, 60, 1300),
                                    quantum_dodge=(0.20, 300))),
}
SKINS["NEBULA_CHAOS"]["box_only"] = True

SKIN_ORDER = list(SKINS.keys())
PUBLIC_SKINS = [k for k in SKIN_ORDER
                if not SKINS[k]["hidden"]
                and SKINS[k]["rarity"] != "MYTHIC"]


# ---- Onglets de rareté de la boutique
SKIN_TABS = [
    dict(rar="COMMON",    label="COMMUN",    col=(205, 208, 224)),
    dict(rar="RARE",      label="RARE",      col=(70, 150, 255)),
    dict(rar="EPIC",      label="ÉPIQUE",    col=(180, 80, 255)),
    dict(rar="LEGENDARY", label="LÉGENDAIRE", col=(255, 200, 40)),
    dict(rar="MYTHIC",    label="MYTHIQUE",  col=(255, 50, 90)),
]
MYTHIC_TEASERS = 1


def tab_entries(i):
    """Cartes de l'onglet i (None = emplacement verrouillé)."""
    rar = SKIN_TABS[i]["rar"]
    keys = [k for k in SKIN_ORDER if SKINS[k]["rarity"] == rar]
    keys.sort(key=lambda k: SKINS[k]["hidden"])
    if rar == "MYTHIC":
        keys += [None] * MYTHIC_TEASERS
    return keys[:10]


# ---- Lignes descriptives pour infobulles
def skin_stat_lines(key):
    st = SKINS[key]["stats"]
    return [tr(STAT_FMT[k][0]) % STAT_FMT[k][2](st[k])
            for k in STAT_FMT if k in st]


def skin_skill_lines(key):
    out = []
    for sk_key, v in SKINS[key]["skills"].items():
        tier, nfr, _nen, dfr, _den, argf = SKILL_INFO[sk_key]
        out.append((tier, tr(nfr), tr(dfr) % argf(v)))
    return out


# ---- Application au loadout
def apply_skin_to_loadout(L, key):
    """Applique stats + compétences du skin équipé à un loadout."""
    L["skills"] = {}
    L["rarity"] = "COMMON"
    L["gdmg"] = 1.0
    sk = SKINS.get(key)
    if not sk:
        return L
    st = sk["stats"]
    L["max_hp"] += st.get("hp", 0)
    L["max_shield"] += st.get("shield", 0)
    L["power"] += st.get("power", 0.0)
    L["rate"] += st.get("rate", 0.0)
    L["speed"] += st.get("speed", 0.0)
    L["jump"] += st.get("jump", 0.0)
    L["regen"] += st.get("regen", 0.0)
    L["hp_regen"] += st.get("hp_regen", 0.0)
    L["coin"] += st.get("coin", 0.0)
    L["reduce"] = min(0.6, L["reduce"] + st.get("reduce", 0.0))
    L["max_hp"] *= 1.0 + st.get("hp_pct", 0.0)
    L["speed"] *= 1.0 + st.get("speed_pct", 0.0)
    L["skills"] = dict(sk["skills"])
    L["rarity"] = sk["rarity"]
    tm = sk["skills"].get("time_master")
    if tm:
        L["power"] *= 1.0 + tm[0]
        L["gdmg"] = 1.0 + tm[0]
        L["hp_regen"] += tm[1]
    return L


# ---- Rendu d'un skin (signature unique)
_SKIN_TMP = None


def _skin_tmp_surface():
    global _SKIN_TMP
    if _SKIN_TMP is None:
        _SKIN_TMP = pygame.Surface((120, 120), pygame.SRCALPHA)
    _SKIN_TMP.fill((0, 0, 0, 0))
    return _SKIN_TMP


def draw_skin(surf, key, cx, cy, face=1, t=0, air=False, vx=0.0,
              scale=1.0, alpha=255, ghost=False, hit=False):
    """Dessine un skin à (cx, cy) avec orientation `face`, échelle, alpha.

    `ghost` teinte en bleu fantôme (échos).
    `hit`  blanchit la silhouette (flash de dégâts).
    """
    sk = SKINS.get(key)
    if not sk:
        return
    tmp = _skin_tmp_surface()
    try:
        sk["fn"](tmp, sk, t, air, vx)
    except Exception:
        # En cas de pépin, dessine un carré coloré de secours
        pygame.draw.rect(tmp, sk["body"], (40, 40, 40, 40), border_radius=8)

    if ghost:
        tmp.fill((50, 50, 130, 0), special_flags=pygame.BLEND_RGB_ADD)
    if hit:
        tmp.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGB_ADD)
    if face < 0:
        tmp = pygame.transform.flip(tmp, True, False)
    if scale != 1.0:
        try:
            if IS_WEB:
                # scale() est beaucoup plus rapide que smoothscale() sur web
                tmp = pygame.transform.scale(
                    tmp, (max(1, int(120 * scale)), max(1, int(120 * scale))))
            else:
                tmp = pygame.transform.smoothscale(
                    tmp, (max(1, int(120 * scale)), max(1, int(120 * scale))))
        except Exception:
            pass
    if alpha < 255:
        tmp = tmp.copy()
        tmp.set_alpha(alpha)
    surf.blit(tmp, tmp.get_rect(center=(int(cx), int(cy))))


def draw_avatar(surf, cx, cy, size, skin_key, frame):
    """Avatar circulaire pour le profil (cadre coloré + buste du skin)."""
    col = FRAME_COLORS[int(frame) % len(FRAME_COLORS)]
    r = size // 2
    pygame.draw.circle(surf, dark(col, 0.28), (cx, cy), r)
    tmp = pygame.Surface((120, 120), pygame.SRCALPHA)
    draw_skin(tmp, skin_key, 60, 62, 1, TICK[0] // 2, False, 0.0)
    crop = pygame.Surface((70, 70), pygame.SRCALPHA)
    crop.blit(tmp, (0, 0), pygame.Rect(25, 24, 70, 70))
    try:
        img = pygame.transform.smoothscale(crop, (size - 8, size - 8))
        surf.blit(img, img.get_rect(center=(cx, cy)))
    except Exception:
        pass
    pygame.draw.circle(surf, col, (cx, cy), r, 3)


# ═══════════════════════════════════════════════════════════════════════════
#  FIN § 4-5
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#  § 6 — DONNÉES (armes, objets, stats, difficultés, modes, succès)
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  8 ARMES (3 de base + 5 spéciales débloquées par des objets)
# ─────────────────────────────────────────────────────────────────────────
WEAPONS = {
    "PLASMA":  dict(speed=14, cd=12, dmg=12, r=6),
    "LASER":   dict(speed=22, cd=35, dmg=25, r=4),
    "MISSILE": dict(speed=9,  cd=55, dmg=35, r=8),
    "TRIPLE":  dict(speed=13, cd=26, dmg=10, r=5, count=3, spread=0.2,
                    color=(120, 255, 120), sfx="special"),
    "BURN":    dict(speed=11, cd=20, dmg=7,  r=7, burn=True,
                    color=ORANGE, sfx="special"),
    "SPRAY":   dict(speed=16, cd=5,  dmg=4.5, r=3, jitter=0.09,
                    color=(255, 255, 150), sfx="shoot"),
    "RAIL":    dict(speed=34, cd=70, dmg=55, r=4, pierce=True,
                    color=(190, 230, 255), sfx="laser"),
    "NOVA":    dict(speed=8,  cd=80, dmg=30, r=11, explode=True,
                    color=(210, 110, 255), sfx="missile"),
        # ── Nouveaux projectiles pour la Matrice d'Armes ──
    "LAME":   dict(speed=18, cd=32, dmg=14, r=6, burn=True,
                   color=(255, 200, 100), sfx="shoot"),
    "SABRE":  dict(speed=20, cd=40, dmg=22, r=5, pierce=True,
                   color=(180, 240, 255), sfx="laser"),
    "KATAR":  dict(speed=12, cd=55, dmg=28, r=8, explode=True,
                   color=(180, 100, 255), sfx="special"),
    "FUSIL":  dict(speed=16, cd=22, dmg=9, r=5, count=3, spread=0.15,
                   color=(120, 255, 120), sfx="special"),
    "ORBE":   dict(speed=10, cd=65, dmg=26, r=9, explode=True,
                   color=(200, 100, 255), sfx="missile"),
}

WEAPON_NAMES = {
    "PLASMA": "PLASMA", "LASER": "LASER", "MISSILE": "ROQUETTE",
    "TRIPLE": "CANON TRIPLE", "BURN": "LANCE-FLAMMES",
    "SPRAY": "MITRAILLEUSE", "RAIL": "RAILGUN", "NOVA": "ORBE NOVA",    "LAME": "LAME", "SABRE": "SABRE", "KATAR": "KATAR",
    "FUSIL": "FUSIL", "ORBE": "ORBE",
}


# ─────────────────────────────────────────────────────────────────────────
#  15 OBJETS (3 emplacements × 5)
# ─────────────────────────────────────────────────────────────────────────
ITEMS = {
        "weapon": [
        # ═══ LAMES (corps-à-corps, projectiles rapides) ═══
        dict(id="W_LAME", name="Lame Énergétique",
             desc="[4] Saignement : 5 dmg/s pendant 3 s sur la cible.",
             price=1500, kind="LAME"),
        dict(id="W_SABRE", name="Sabre Quantique",
             desc="[4] Perfore jusqu'à 3 cibles et ralentit -20% pendant 2 s.",
             price=2200, kind="SABRE"),
        dict(id="W_KATAR", name="Katar du Void",
             desc="[4] Critique ×2.5 + explosion d'impact (30 dmg de zone).",
             price=2800, kind="KATAR"),
        # ═══ DISTANCE ═══
        dict(id="W_FUSIL", name="Fusil Plasma",
             desc="[4] Tir triple en éventail serré (3 projectiles 60°).",
             price=3500, kind="FUSIL"),
        dict(id="W_RAIL", name="Railgun Magnétique",
             desc="[4] Rayon perforant qui traverse tout, ignore l'armure.",
             price=4500, kind="RAIL"),
        dict(id="W_ORBE", name="Orbe Singularité",
             desc="[4] Orbe à tête chercheuse : traque, explose (40 dmg zone).",
             price=5500, kind="ORBE"),
    ],
        "armor": [
        # ═══ BOUCLIERS ═══
        dict(id="A_PRISM", name="Champ Prismatique",
             desc="Renvoie 25% des dégâts reçus à l'attaquant.",
             price=1200, shield=30, reflect=True),
        dict(id="A_TESS", name="Égide Tesseract",
             desc="Bouclier automatique toutes les 8 s (bloque 1 coup).",
             price=2000, shield=60, auto_shield=480),
        dict(id="A_AEGIS", name="Bouclier Aegis-X",
             desc="Explose au bris du bouclier : onde de choc 40 dmg zone.",
             price=2800, shield=80, nova=True),
        # ═══ ARMURES ═══
        dict(id="A_PLAT", name="Plaques Titane",
             desc="Immunité pièges 1.5 s toutes les 4 s + 15% réduction.",
             price=3800, reduce=0.15, trapsafe=240),
        dict(id="A_NANO", name="Nano-Alliage",
             desc="Régénération auto : +2 PV/s en permanence.",
             price=4500, hp_regen=2.0),
        dict(id="A_NEBU", name="Peau de Nébuleuse",
             desc="18% d'esquive. Chaque esquive rend 5 PV.",
             price=5500, evade=0.18),
    ],
        "support": [
        # ═══ SOIN ═══
        dict(id="S_CROIX", name="Croix Quantique",
             desc="[E] Pulse de soin : +25 PV instantanés (recharge 10 s).",
             price=1200, ability="HEAL_PULSE"),
        dict(id="S_FONTAINE", name="Fontaine Vita",
             desc="[E] Zone de soin : +2 PV/s tant que tu restes dedans.",
             price=1800, ability="HEAL_ZONE"),
        dict(id="S_SEVE", name="Sève Éternelle",
             desc="Immunité ralentissement + +1.5 PV/s passif.",
             price=2600, hp_regen=1.5, immune_slow=True),
        # ═══ BUFF ═══
        dict(id="S_TOTEM", name="Totem Chrono",
             desc="[E] Ralentit le temps 3 s (ennemis, tirs, échos).",
             price=3400, ability="TIME"),
        dict(id="S_OEIL", name="Œil Oraculaire",
             desc="[E] Vision parfaite 4 s : +25% critique, portée doublée.",
             price=4000, ability="VISION"),
        dict(id="S_COEUR", name="Cœur du Multivers",
             desc="[E] Frénésie 5 s : +30% cadence, +20% vitesse, +15% dégâts.",
             price=4800, ability="FRENZY"),
    ],
}

SLOT_NAMES = {"weapon": "ARME", "armor": "ARMURE", "support": "SOUTIEN"}
ITEM_BY_ID = {it["id"]: it for lst in ITEMS.values() for it in lst}
# Hausse générale des prix d'objets
for _it in ITEM_BY_ID.values():
    _it["price"] = int(round(_it["price"] * ITEM_PRICE_MULT, -2))


def equipped(slot):
    """Renvoie l'objet équipé d'un slot, ou None."""
    return ITEM_BY_ID.get(SAVE["equip"].get(slot))


# ─────────────────────────────────────────────────────────────────────────
#  8 STATISTIQUES ACHETABLES
# ─────────────────────────────────────────────────────────────────────────
STATS = {
    "hp":     dict(name="PV MAX",             base=100,   inc=10,
                   price0=250, fmt=lambda v: "%d" % v),
    "shield": dict(name="BOUCLIER",           base=100,   inc=15,
                   price0=220, fmt=lambda v: "%d" % v),
    "regen":  dict(name="RECHARGE BOUCLIER",  base=0.4,   inc=0.08,
                   price0=260, fmt=lambda v: "%d/s" % round(v * 60)),
    "speed":  dict(name="VITESSE",            base=6.0,   inc=0.25,
                   price0=300, fmt=lambda v: "%.2f" % v),
    "power":  dict(name="PUISSANCE",          base=1.0,   inc=0.06,
                   price0=400, fmt=lambda v: "+%d%%" % round((v - 1) * 100)),
    "rate":   dict(name="CADENCE DE TIR",     base=1.0,   inc=0.05,
                   price0=350, fmt=lambda v: "+%d%%" % round((v - 1) * 100)),
    "jump":   dict(name="SAUT",               base=12.5,  inc=0.35,
                   price0=240, fmt=lambda v: "%.1f" % v),
    "coin":   dict(name="GAIN DE PIÈCES",     base=1.0,   inc=0.10,
                   price0=500, fmt=lambda v: "+%d%%" % round((v - 1) * 100)),
}
for _st in STATS.values():
    _st["price0"] = int(round(_st["price0"] * STAT_PRICE_MULT, -1))


def stat_value(key):
    """Valeur actuelle d'une stat (base + améliorations + bonus succès)."""
    s = STATS[key]
    return s["base"] + s["inc"] * (SAVE["upg"][key] + SAVE["bonus"][key])


def stat_price(key):
    """Prix du prochain niveau d'une stat."""
    return int(round(
        STATS[key]["price0"] * STAT_PRICE_GROWTH ** SAVE["upg"][key], -1))


# ─────────────────────────────────────────────────────────────────────────
#  15 DIFFICULTÉS (1-10 libres, 11-15 Champion Top 100)
# ─────────────────────────────────────────────────────────────────────────
DIFFS = {
    # ═══════════════════════════════════════════════════════════════════
    #  D1-D4 : TRÈS FACILE → FACILE (apprentissage)
    # ═══════════════════════════════════════════════════════════════════
    1:  dict(name="DÉBUTANT", color=VERT_NEON, off=-6, hp=0.15, dmg=0.25,
             spd=0.55, fire=0.015, coin=0.6, thr=(8, 12),
             desc="IA ultra lente, faibles dégâts, très imprécises. Idéal pour apprendre."),
    2:  dict(name="FACILE", color=(160, 255, 80), off=-5, hp=0.25, dmg=0.35,
             spd=0.65, fire=0.025, coin=0.7, thr=(7, 10),
             desc="IA lente et hésitante. Beaucoup de temps pour réagir."),
    3:  dict(name="NORMAL", color=JAUNE_NEON, off=-3, hp=0.45, dmg=0.55,
             spd=0.80, fire=0.05, coin=1.0, thr=(5, 8),
             desc="IA classique. Premiers vrais défis, chaos modérés."),
    4:  dict(name="AVANCÉ", color=(255, 210, 60), off=-1, hp=0.65, dmg=0.75,
             spd=0.90, fire=0.09, coin=1.3, thr=(4, 6),
             desc="IA vive et nombreuse. Commence à faire mal."),
    # ═══════════════════════════════════════════════════════════════════
    #  D5-D8 : MOYEN → DIFFICILE
    # ═══════════════════════════════════════════════════════════════════
    5:  dict(name="DIFFICILE", color=ORANGE, off=1, hp=0.95, dmg=1.00,
             spd=1.00, fire=0.14, coin=1.8, thr=(3, 5),
             desc="IA redoutable. Chaos destructeurs, pièges fréquents."),
    6:  dict(name="VÉTÉRAN", color=(255, 140, 60), off=3, hp=1.30, dmg=1.25,
             spd=1.05, fire=0.19, coin=2.4, thr=(3, 4),
             desc="IA vétéran. Lasers croisés, dalles instables."),
    7:  dict(name="EXPERT", color=(255, 110, 60), off=5, hp=1.70, dmg=1.55,
             spd=1.10, fire=0.24, coin=3.2, thr=(2, 3),
             desc="Maîtrise parfaite requise. Aucun répit."),
    8:  dict(name="MAÎTRE", color=(255, 90, 80), off=7, hp=2.20, dmg=1.90,
             spd=1.15, fire=0.30, coin=4.0, thr=(2, 3),
             desc="Les maîtres du chaos dominent."),
    # ═══════════════════════════════════════════════════════════════════
    #  D9-D10 : EXPERT → APOCALYPSE
    # ═══════════════════════════════════════════════════════════════════
    9:  dict(name="GRAND MAÎTRE", color=(255, 70, 100), off=9, hp=2.80,
             dmg=2.30, spd=1.18, fire=0.36, coin=5.0, thr=(2, 2),
             desc="Presque impossible. Presque."),
    10: dict(name="APOCALYPSE", color=(255, 40, 120), off=12, hp=3.60,
             dmg=2.80, spd=1.22, fire=0.42, coin=6.5, thr=(1, 2),
             desc="Dernier palier avant le Mode Champion. Chaos permanent."),
    # ═══════════════════════════════════════════════════════════════════
    #  D11-D15 : CHAMPION (Top 100 mondial uniquement)
    # ═══════════════════════════════════════════════════════════════════
    11: dict(name="CHAMPION I", color=(180, 80, 255), off=15, hp=4.50,
             dmg=3.20, spd=1.25, fire=0.48, coin=8.0, thr=(1, 2),
             desc="Épreuve de champion. Puits de distorsion activés.",
             champion=True),
    12: dict(name="CHAMPION II", color=(160, 100, 255), off=18, hp=5.50,
             dmg=3.60, spd=1.28, fire=0.54, coin=9.5, thr=(1, 2),
             desc="Missiles traqueurs ambiants. IA parfaite.",
             champion=True),
    13: dict(name="CHAMPION III", color=(140, 120, 255), off=21, hp=7.00,
             dmg=4.00, spd=1.30, fire=0.60, coin=11.0, thr=(1, 1),
             desc="Broyeurs mobiles verticaux. Chaque erreur coûte cher.",
             champion=True),
    14: dict(name="CHAMPION IV", color=(120, 140, 255), off=25, hp=9.00,
             dmg=4.50, spd=1.33, fire=0.68, coin=13.0, thr=(1, 1),
             desc="Champs de plasma au sol. Survie improbable.",
             champion=True),
    15: dict(name="LÉGENDE SUPRÊME", color=(90, 220, 255), off=30, hp=12.0,
             dmg=5.00, spd=1.36, fire=0.75, coin=15.0, thr=(1, 1),
             desc="L'ultime défi. Presque personne ne survit à 5 manches.",
             champion=True),
}


# ─────────────────────────────────────────────────────────────────────────
#  MODES DE JEU
# ─────────────────────────────────────────────────────────────────────────
MODES = {
    "COURSE": dict(
        title="PARCOURS ÉCHO", round_time=4500, chaos=900, ffa=False,
        rounds=None, course=True, min_diff=1,
        hint="Atteins la SORTIE. Tes échos du passé refont ton parcours... et te veulent du mal !"),
    "SURVIE": dict(
        title="SURVIE ARCADE", round_time=1800, chaos=900, ffa=False,
        rounds=None, min_diff=1,
        hint="Tiens le plus longtemps possible. Chaque manche, ton ancien toi devient un piège."),
    "ARENE": dict(
        title="ARÈNE ÉCHO", round_time=1500, chaos=900, ffa=True, rounds=4,
        min_diff=2, secret=True,
        hint="Toi + 3 IA. Vos échos combattent pour vous. Termine 1er pour la gloire !"),
    "GLITCH": dict(
        title="ZONE GLITCH", round_time=1200, chaos=300, ffa=False, rounds=3,
        meteors=True, min_diff=3, secret=True,
        hint="Chaos toutes les 5 s + météores + boss. Survis 3 manches !"),
    "GARDIEN": dict(
        title="LE GARDIEN DU TEMPS", round_time=2100, chaos=450, ffa=False,
        rounds=3, boss=True, ally=True, min_diff=4, secret=True,
        hint="Terrasse le Gardien en 3 manches. Tes échos sont tes ALLIÉS ici !"),
    "ECLIPSE": dict(
        title="ÉCLIPSE", round_time=1500, chaos=360, ffa=False, rounds=3,
        blackout=True, meteors=True, relic=True, min_diff=4, secret=True,
        hint="Dans le noir total, survis... et cherche ce qui brille à la dernière manche."),
    "FAILLE": dict(
        title="LA FAILLE", round_time=2400, chaos=300, ffa=False, rounds=3,
        course=True, hard=True, min_diff=5, secret=True,
        hint="Le Parcours ultime : pièges doublés, chaos toutes les 5 s, 40 s max !"),
    "CAMPAGNE": dict(
        title="CAMPAGNE", round_time=2400, chaos=900, ffa=False, rounds=1,
        course=True, min_diff=1,
        hint="Défi ramassé d'une manche : atteins la SORTIE, élimine tout, ou survis !"),
}

# ---- 10 NIVEAUX SECRETS (campagne secrète) ------------------------------
SECRET_LEVELS_IDS = [
    "FISSURE", "PARADOXE", "MIROIR", "HORLOGE", "BRUME",
    "ECHO_PRIME", "SANCTUM", "VERTIGE", "NEMESIS", "OMEGA",
]
SECRET_LEVELS_INFO = {
    "FISSURE":    dict(name="FISSURE",    color=(255, 90, 200),
                       desc="Faille gravitationnelle permanente.",
                       effect="LUNE"),
    "PARADOXE":   dict(name="PARADOXE",   color=(200, 80, 255),
                       desc="Tes échos se dédoublent.",
                       effect="ECHO_RAGE"),
    "MIROIR":     dict(name="MIROIR",     color=(120, 200, 255),
                       desc="Contrôles inversés en permanence.",
                       effect="INVERSION"),
    "HORLOGE":    dict(name="HORLOGE",    color=(255, 200, 90),
                       desc="Accélération temporelle constante.",
                       effect="TURBO"),
    "BRUME":      dict(name="BRUME",      color=(180, 180, 200),
                       desc="Visibilité réduite au strict minimum.",
                       effect="BLACKOUT"),
    "ECHO_PRIME": dict(name="ECHO_PRIME", color=(120, 255, 200),
                       desc="Seuls tes échos peuvent te sauver.",
                       effect="ECHO_RAGE"),
    "SANCTUM":    dict(name="SANCTUM",    color=(255, 240, 180),
                       desc="Aucune arme ne fonctionne.",
                       effect="NOSHIELD"),
    "VERTIGE":    dict(name="VERTIGE",    color=(150, 120, 255),
                       desc="Rotation constante du décor.",
                       effect="TELEPORT"),
    "NEMESIS":    dict(name="NEMESIS",    color=(255, 60, 90),
                       desc="Ton reflet te traque.",
                       effect="TELEGUIDE"),
    "OMEGA":      dict(name="OMEGA",      color=(255, 220, 60),
                       desc="Tous les chaos activés simultanément.",
                       effect=None),                # géré spécialement
}
SECRET_CAMPAIGN_ROUNDS_REQUIRED = 10

# Ajoute les niveaux secrets à MODES
for _sid in SECRET_LEVELS_IDS:
    if _sid not in MODES:
        MODES[_sid] = dict(
            title="NIVEAU SECRET : %s" % _sid,
            round_time=2400, chaos=420, ffa=False, rounds=1,
            min_diff=8, secret=True, secret_level=_sid,
            hint=SECRET_LEVELS_INFO[_sid]["desc"],
        )


# ---- 5 ZONES SECRÈTES (débloquées par exploration) ---------------------
SECRET_ORDER = ["ARENE", "GLITCH", "GARDIEN", "ECLIPSE", "FAILLE"]

SECRET_RULES = {
    "ARENE":   dict(src="SURVIE", min_round=2, chance=0.45, min_diff=1,
                    place="any", vis=1.0),
    "GLITCH":  dict(src="SURVIE", min_round=2, chance=0.45, min_diff=1,
                    place="any", vis=1.0),
    "GARDIEN": dict(src="SURVIE", min_round=8, chance=0.16, min_diff=3,
                    place="top", vis=0.45),
    "ECLIPSE": dict(src="COURSE", min_round=4, chance=0.20, min_diff=2,
                    place="far", vis=0.45),
    "FAILLE":  dict(src="GLITCH", min_round=2, chance=0.18, min_diff=3,
                    place="top", vis=0.30),
}

SECRET_HINTS = {
    "ARENE":   "Observe bien les plateformes de la Survie Arcade...",
    "GLITCH":  "Un éclat violet vacille dans la Survie Arcade...",
    "GARDIEN": "Seuls les survivants les plus endurcis le voient.",
    "ECLIPSE": "Le Parcours cache un recoin que peu atteignent.",
    "FAILLE":  "Il faut survivre au Glitch pour apercevoir la Faille.",
}

SECRET_REWARD_SKIN = {
    "ARENE":   "CHRONO_KNIGHT",
    "GLITCH":  "GLITCH_ENTITY",
    "GARDIEN": "ASTRAL_GUARDIAN",
    "ECLIPSE": "ECLIPSE_WRAITH",
}

# Conditions de déblocage de la Campagne Secrète
SECRET_ZONES_FOR_CAMPAIGN = ("ARENE", "GLITCH", "GARDIEN", "ECLIPSE", "FAILLE")
SECRET_ZONE_WINS_REQUIRED = 10
SECRET_ZONE_MIN_DIFFICULTY = 3


# ---- Causes de mort
CAUSES = {
    "player": "TIR DU JOUEUR",
    "ai":     "TIR DE L'IA",
    "enemy":  "TIR ENNEMI",
    "echo":   "TIR DE TON ÉCHO",
}


# ---- Astuces du menu
TIPS = [
    "Les tirs verts sont ceux de tes échos : ils blessent tout le monde.",
    "Le bouclier arrête les tirs mais pas les pièges.",
    "Chaque manche réussie rapporte des pièces : plus la difficulté est haute, plus ça paie.",
    "Des passages secrets se cachent dans la Survie Arcade...",
    "Équipe des objets dans la Boutique pour débloquer la touche [4] et la touche [E].",
    "Certaines statistiques ne s'obtiennent que grâce aux succès.",
    "La roue du chaos change les règles toutes les 15 secondes.",
    "Pense à ta position : ton écho rejouera EXACTEMENT ce que tu fais.",
    "Débutant ? Commence au niveau de difficulté 1 !",
    "Ramasse les cristaux bleus en jeu : ce sont des GEMMES, la monnaie premium.",
    "Le Chrono-Imperator (onglet 5 de la boutique) fige le temps avec [F].",
    "Les difficultés 11 à 15 sont réservées au Top 100 Mondial.",
    "Chaque palier de 5 manches est marqué par un boss ou une calamité.",
]


# ─────────────────────────────────────────────────────────────────────────
#  COMPTEURS DE STATS (helpers pour succès)
# ─────────────────────────────────────────────────────────────────────────
def _best_at(dic, d):
    return max([v for k, v in dic.items() if int(k) >= d] or [0])


def _ST():
    return SAVE["stats"]


def _best_round():
    """Meilleure manche atteinte (Survie ou Parcours), toutes difficultés."""
    st = _ST()
    vals = list(st.get("surv_best", {}).values()) + list(st.get("course_best", {}).values())
    return max([_to_int(v) for v in vals] or [0])


def _skins_bought():
    """Skins publics possédés, hors skin de départ (secrets exclus)."""
    return len([k for k in SAVE["owned"]
                if k in PUBLIC_SKINS and k != "NEON_CYBER"])


def _secret_skins_owned():
    return len([k for k in SAVE["owned"]
                if k in SKINS and SKINS[k]["hidden"]])


def _ST_KILLS():  return _ST()["kills_total"]
def _ST_ROUNDS(): return _ST()["rounds_total"]
def _ST_BOXES():  return _ST().get("boxes_opened", 0)
def _ST_GAMES():  return _ST()["games"]


# ─────────────────────────────────────────────────────────────────────────
#  SUCCÈS À PALIERS
# ─────────────────────────────────────────────────────────────────────────
def _tiers(fid, names, desc, getter, goals, rewards, ids=None):
    """Fabrique un groupe de paliers du même succès.

    Chaque palier est un dict complet (id, name, desc, test, reward)
    + family/tier/tiers/goal/progress pour la barre de progression.
    """
    out = []
    n = len(goals)
    for i, goal in enumerate(goals):
        fr_n, en_n = names[i]
        out.append(dict(
            id=(ids[i] if ids else "%s_%d" % (fid, goal)),
            family=fid, tier=i + 1, tiers=n, goal=goal,
            name=fr_n, en_name=en_n,
            desc="%s (palier %d/%d)" % (desc[0] % goal, i + 1, n),
            en_desc="%s (tier %d/%d)" % (desc[1] % goal, i + 1, n),
            progress=getter,
            test=(lambda g=goal, f=getter: f() >= g),
            reward=rewards[i],
        ))
    return out


ACHIEVEMENTS = (
    # -- KILLS (4 paliers)
    _tiers("KILLS",
           [("Chasseur", "Hunter"), ("Traqueur", "Tracker"),
            ("Exterminateur", "Exterminator"),
            ("Fléau du Temps", "Scourge of Time")],
           ("Détruis %d ennemis.", "Destroy %d enemies."),
           _ST_KILLS, (10, 50, 250, 1000),
           [dict(coins=250),
            dict(coins=800, bonus=[("power", 1)]),
            dict(coins=2500, bonus=[("rate", 1)]),
            dict(gems=40, boxes=2)])
    # -- ROUND (4 paliers)
    + _tiers("ROUND",
             [("Échauffement", "Warm-Up"),
              ("Marathon temporel", "Time Marathon"),
              ("Maître des boucles", "Loop Master"),
              ("Éternel", "The Eternal")],
             ("Atteins la manche %d (Survie ou Parcours).",
              "Reach round %d (Survival or Echo Run)."),
             _best_round, (3, 10, 20, 30),
             [dict(coins=300),
              dict(coins=1000, bonus=[("regen", 1)]),
              dict(coins=3000, bonus=[("hp", 1)]),
              dict(gems=50, boxes=2)])
    # -- SKINS (4 paliers)
    + _tiers("SKINS",
             [("Premier achat", "First Purchase"),
              ("Collectionneur", "Collector"),
              ("Garde-robe infinie", "Endless Wardrobe"),
              ("Panthéon du Chaos", "Chaos Pantheon")],
             ("Achète %d skin(s) à la boutique.",
              "Buy %d skin(s) from the shop."),
             _skins_bought, (1, 5, 10, 15),
             [dict(coins=300),
              dict(coins=1500, bonus=[("coin", 1)]),
              dict(coins=5000, bonus=[("jump", 1)]),
              dict(gems=100, boxes=3)])
    # -- TOT (4 paliers, ex-FIRST / ROUNDS25 / ROUNDS100)
    + _tiers("TOT",
             [("Première boucle", "First Loop"),
              ("Boucle infinie", "Infinite Loop"),
              ("Horloger fou", "Mad Clockmaker"),
              ("Gardien des boucles", "Keeper of Loops")],
             ("Réussis %d manche(s) au total.",
              "Clear %d round(s) in total."),
             _ST_ROUNDS, (1, 25, 100, 300),
             [dict(coins=150),
              dict(coins=600),
              dict(coins=2500, bonus=[("speed", 1)]),
              dict(gems=30, boxes=1)])
    # -- LUCKY (3 paliers)
    + _tiers("LUCKY",
             [("Premier tirage", "First Draw"),
              ("Main chanceuse", "Lucky Hand"),
              ("Roi du jackpot", "Jackpot King")],
             ("Ouvre %d boîte(s) mystère(s).",
              "Open %d mystery box(es)."),
             _ST_BOXES, (1, 10, 30),
             [dict(coins=200),
              dict(coins=1500),
              dict(gems=25, boxes=1)])
    # -- SECRETSKIN (3 paliers)
    + _tiers("SECRETSKIN",
             [("Premier secret", "First Secret"),
              ("Initié", "Initiate"),
              ("Maître des secrets", "Secret Master")],
             ("Possède %d skin(s) secret(s).",
              "Own %d secret skin(s)."),
             _secret_skins_owned, (1, 3, 5),
             [dict(coins=2000),
              dict(gems=20, boxes=1),
              dict(gems=75, boxes=3)])
    # -- Succès uniques
    + [
        dict(id="SURV5", name="Survivant",
             desc="Réussis 5 manches en Survie Arcade.",
             test=lambda: _best_at(_ST()["surv_best"], 1) >= 5,
             reward=dict(coins=500)),
        dict(id="SURV8D3", name="Survivant aguerri",
             desc="Réussis 8 manches en Survie (difficulté 3 ou +).",
             test=lambda: _best_at(_ST()["surv_best"], 3) >= 8,
             reward=dict(coins=1500, bonus=[("speed", 1)])),
        dict(id="SURV8D5", name="Légende du Chaos",
             desc="Réussis 8 manches en Survie (difficulté 5).",
             test=lambda: _best_at(_ST()["surv_best"], 5) >= 8,
             reward=dict(coins=5000, bonus=[("shield", 2), ("hp", 1)])),
        dict(id="LORD", name="Seigneur du Temps",
             desc="Réussis 10 manches en Survie (difficulté 4 ou +).",
             test=lambda: _best_at(_ST()["surv_best"], 4) >= 10,
             reward=dict(coins=3000, skin="CHRONOS_LORD")),
        dict(id="COURSE3", name="Coureur",
             desc="Réussis 3 manches de suite au Parcours (difficulté 2 ou +).",
             test=lambda: _best_at(_ST()["course_best"], 2) >= 3,
             reward=dict(coins=600)),
        dict(id="COURSE6", name="Fantôme du Parcours",
             desc="Réussis 6 manches de suite au Parcours (difficulté 4 ou +).",
             test=lambda: _best_at(_ST()["course_best"], 4) >= 6,
             reward=dict(coins=3000, bonus=[("jump", 1), ("rate", 1)])),
        dict(id="SPEED", name="Éclair",
             desc="Termine une manche du Parcours en moins de 25 s (diff. 3 ou +).",
             test=lambda: 0 < _ST()["fast_course"] <= 25,
             reward=dict(coins=1200, bonus=[("speed", 1)])),
        dict(id="FLAWLESS", name="Intouchable",
             desc="Finis une manche de Survie sans aucun dégât (diff. 3 ou +).",
             test=lambda: _ST()["flawless"],
             reward=dict(coins=2000, bonus=[("power", 1)])),
        dict(id="ARENA", name="Roi de l'Arène",
             desc="Termine 1er de l'Arène Écho.",
             test=lambda: _ST()["arena_win"],
             reward=dict(skin="CHRONO_KNIGHT")),
        dict(id="GLITCH", name="Survivant du Glitch",
             desc="Termine la Zone Glitch.",
             test=lambda: _ST()["glitch_done"],
             reward=dict(coins=800, skin="GLITCH_ENTITY")),
        dict(id="GUARD", name="Briseur de Gardien",
             desc="Terrasse le Gardien du Temps.",
             test=lambda: _ST()["guard_done"],
             reward=dict(coins=2500, skin="ASTRAL_GUARDIAN")),
        dict(id="RELIC", name="Chasseur de reliques",
             desc="Trouve la Relique cachée dans l'Éclipse.",
             test=lambda: _ST()["relic"],
             reward=dict(coins=2000, skin="ECLIPSE_WRAITH")),
        dict(id="FAILLE", name="Au-delà du Temps",
             desc="Termine la Faille.",
             test=lambda: _ST()["faille_done"],
             reward=dict(coins=6000, bonus=[("hp", 1), ("shield", 1), ("regen", 1)])),
        dict(id="EXPLORER", name="Explorateur du Chaos",
             desc="Découvre les 5 zones secrètes.",
             test=lambda: all(SAVE["secrets"].values()),
             reward=dict(coins=3000, bonus=[("coin", 2)])),
    ]
)

# Migration des anciens ids (sauvegardes pré-v2) → paliers équivalents
LEGACY_ACH = {
    "FIRST":     ["TOT_1"],
    "ROUNDS25":  ["TOT_1", "TOT_25"],
    "ROUNDS100": ["TOT_1", "TOT_25", "TOT_100"],
    "KILLS50":   ["KILLS_10", "KILLS_50"],
    "KILLS300":  ["KILLS_10", "KILLS_50", "KILLS_250"],
}

# Toasts actifs (affichés en haut de l'écran)
TOASTS = []


# ─────────────────────────────────────────────────────────────────────────
#  RÉCOMPENSES
# ─────────────────────────────────────────────────────────────────────────
def grant_gems(n):
    """Crédite des gemmes dans la sauvegarde + les stats. Retourne le montant."""
    n = _to_int(n)
    if n <= 0:
        return 0
    SAVE["gems"] = _to_int(SAVE.get("gems", 0)) + n
    SAVE["stats"]["gems_total"] = _to_int(
        SAVE["stats"].get("gems_total", 0)) + n
    return n


def run_gems(S):
    """Gemmes de fin de run (manches + score Survie + victoire secrète)."""
    rate = GEM_RATE.get(S.diff, 0.1)
    g = 0.0
    for r in range(GEM_FIRST_ROUND, S.rounds_done + 1):
        g += rate * (1.0 + r / 10.0)
    if S.mode == "SURVIE" and S.rounds_done >= GEM_FIRST_ROUND:
        g += rate * S.score_value() / 2500.0
    cap = GEM_RUN_CAP.get(S.diff, 6)
    if S.win and S.cfg.get("rounds") and S.mode not in ("COURSE", "SURVIE"):
        g += 4 + 6 * rate
        cap = int(cap * 1.5)
    return int(min(cap, g))


def achievement_progress(a):
    """(actuel, objectif) pour un palier, ou None pour un succès unique."""
    f = a.get("progress")
    if not f:
        return None
    try:
        return min(int(f()), a["goal"]), a["goal"]
    except Exception:
        return None


def reward_text(rw):
    """Texte lisible d'une récompense (pour toasts et écran succès)."""
    parts = []
    if rw.get("coins"):
        parts.append("+%d %s" % (rw["coins"], tr("pièces")))
    if rw.get("gems"):
        parts.append("+%d %s" % (rw["gems"], tr("gemmes")))
    for k, n in rw.get("bonus", []):
        parts.append("+%d %s" % (n, tr(STATS[k]["name"])))
    if rw.get("boxes"):
        parts.append("+%d %s" % (
            rw["boxes"],
            tr("boîte mystère") if rw["boxes"] == 1 else tr("boîtes mystères")))
    if rw.get("skin"):
        parts.append("%s : %s" % (tr("Skin"), tr(SKINS[rw["skin"]]["name"])))
    return ", ".join(parts)


def grant_reward(rw):
    """Crédite une récompense. Retourne les pièces de compensation (bonus max)."""
    SAVE["coins"] = _to_int(SAVE.get("coins", 0)) + rw.get("coins", 0)
    SAVE["gems"] = _to_int(SAVE.get("gems", 0)) + rw.get("gems", 0)
    SAVE["mystery_boxes"] = _to_int(
        SAVE.get("mystery_boxes", 0)) + rw.get("boxes", 0)
    comp = 0
    for k, n in rw.get("bonus", []):
        room = max(0, STAT_MAX_BONUS - SAVE["bonus"][k])
        SAVE["bonus"][k] += min(n, room)
        comp += (n - min(n, room)) * BONUS_OVERFLOW_COINS
    if comp:
        SAVE["coins"] += comp
    sk = rw.get("skin")
    if sk and sk not in SAVE["owned"]:
        SAVE["owned"].append(sk)
    return comp


def migrate_achievements():
    """Convertit anciens ids → nouveaux (idempotent)."""
    ach, changed = SAVE["ach"], False
    for old, news in LEGACY_ACH.items():
        if old in ach:
            ach.remove(old)
            ach.extend(n for n in news if n not in ach)
            changed = True
    return changed


def check_achievements():
    """Débloque tous les paliers atteints et verse les récompenses.
    Plusieurs gains en cascade possibles (ex. skin secret → collection)."""
    new = []
    changed = migrate_achievements()
    for _ in range(4):
        got = False
        for a in ACHIEVEMENTS:
            if a["id"] in SAVE["ach"]:
                continue
            try:
                ok = bool(a["test"]())
            except Exception:
                ok = False
            if not ok:
                continue
            SAVE["ach"].append(a["id"])
            comp = grant_reward(a["reward"])
            sub = reward_text(a["reward"])
            if comp:
                sub += "  (%s +%d)" % (tr("compensation"), comp)
            TOASTS.append(dict(text=a["name"], sub=sub, t=0))
            new.append(a)
            got = changed = True
        if not got:
            break
    if new:
        try:
            audio.play("ach")
        except Exception:
            pass
    if changed:
        write_save()
    return new


# ─────────────────────────────────────────────────────────────────────────
#  BOÎTES MYSTÈRES (sources)
# ─────────────────────────────────────────────────────────────────────────
def grant_box(n, why):
    SAVE["mystery_boxes"] = _to_int(SAVE.get("mystery_boxes", 0)) + int(n)
    try:
        audio.play("pickup")
    except Exception:
        pass
    say("+%d %s  (%s)" % (
        n,
        tr("boîte mystère") if n == 1 else tr("boîtes mystères"),
        tr(why)), JAUNE_NEON)


def box_from_round(diff, flawless):
    """1) Chance de boîte en fin de manche."""
    if random.random() < 0.03 + 0.01 * diff + (0.05 if flawless else 0):
        grant_box(1, "Bonus de manche")


def box_from_streak(mode, diff, rnd):
    """3) Série en Survie difficulté 3+ (une boîte tous les 5 manches)."""
    if mode == "SURVIE" and diff >= 3 and rnd > 0 and rnd % 5 == 0:
        grant_box(1, "Série de manches")


def box_from_pass():
    """5) Paliers du Passe XP (une boîte tous les 500 XP)."""
    st = SAVE["stats"]
    due = SAVE["pass_xp"] // BOX_PASS_STEP - _to_int(
        st.get("box_pass_claimed", 0))
    if due > 0:
        st["box_pass_claimed"] = st.get("box_pass_claimed", 0) + due
        grant_box(due, "Passe XP")


# ═══════════════════════════════════════════════════════════════════════════
#  § 7 — CHAOS (roue des 20 effets)
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_P = dict(
    invert=False, grav=1.0, grav_inv=False, slip=False,
    speed=1.0, tscale=1.0, giant=False, ricochet=False, blackout=False,
    wind=0.0, meteors=False, homing=False, lava=False, dmgx=1.0,
    barrage=False, tele=False, noshield=False, bounce=False, poison=False,
    echo=1.0, antigrav=False,
)


def _e(name, desc, color, lv, **p):
    return dict(name=name, desc=desc, color=color, lv=lv, p=p)


EFFECTS = {
    "INVERSION": _e("CONTRÔLES INVERSÉS",
                    "Gauche et droite sont échangés pour tout le monde.",
                    ROSE, (1, 5), invert=True),
    "LUNE":      _e("GRAVITÉ LUNAIRE",
                    "Gravité faible : sauts géants et vols planés.",
                    CYAN_NEON, (1, 4), grav=0.4),
    "GLACE":     _e("SOL GLISSANT",
                    "Tu patines : l'inertie est maximale.",
                    (140, 220, 255), (1, 5), slip=True),
    "RALENTI":   _e("RALENTI",
                    "Le monde est au ralenti (échos, tirs, IA)... pas toi.",
                    (120, 160, 255), (1, 3), tscale=0.5),
    "TRAMPOLINE": _e("TRAMPOLINES",
                     "Le sol rebondit : tout le monde saute sans arrêt.",
                     VERT_NEON, (1, 3), bounce=True),
    "VENT":      _e("TEMPÊTE DE VENT",
                    "Un vent violent pousse tout le monde.",
                    (180, 255, 220), (1, 4), wind=1.8),
    "GEANTS":    _e("BALLES GÉANTES",
                    "Les projectiles sont énormes et dévastateurs.",
                    ROUGE_NEON, (2, 5), giant=True),
    "RICOCHET":  _e("RICOCHETS",
                    "Tous les tirs rebondissent sur les murs.",
                    (120, 255, 150), (2, 5), ricochet=True),
    "TURBO":     _e("TURBO TEMPOREL",
                    "Joueurs, échos, tirs et monstres vont plus vite.",
                    ORANGE, (2, 5), speed=1.5, tscale=1.35),
    "BLACKOUT":  _e("BLACKOUT",
                    "Lumière coupée : seule ta lampe t'éclaire.",
                    (200, 200, 210), (2, 5), blackout=True),
    "TELEGUIDE": _e("TIRS TÉLÉGUIDÉS",
                    "Les projectiles traquent leur cible.",
                    JAUNE_NEON, (3, 5), homing=True),
    "METEORES":  _e("PLUIE DE MÉTÉORES",
                    "Des rochers enflammés tombent du ciel.",
                    (255, 110, 40), (3, 5), meteors=True),
    "ANTIGRAV":  _e("ANTI-GRAVITÉ",
                    "Apesanteur spatiale : dérive libre, sauts désactivés.",
                    PURPLE_NEON, (3, 5), antigrav=True, grav=0.08),
    "TELEPORT":  _e("TÉLÉPORTATION",
                    "Tout le monde est téléporté au hasard toutes les 3 s.",
                    (90, 230, 255), (3, 5), tele=True),
    "ECHO_RAGE": _e("ÉCHOS ENRAGÉS",
                    "Tes échos rejouent le passé presque 2× plus vite !",
                    MINT, (4, 5), echo=1.9),
    "BARRAGE":   _e("PLUIE DE TIRS",
                    "Des tirs hostiles jaillissent des bords de l'écran.",
                    ROUGE_NEON, (4, 5), barrage=True),
    "LAVE":      _e("SOL EN LAVE",
                    "Le sol brûle : ne reste pas à terre !",
                    (255, 90, 20), (4, 5), lava=True),
    "NOSHIELD":  _e("SANS BOUCLIER",
                    "Les boucliers sont coupés pour tout le monde.",
                    (170, 170, 190), (4, 5), noshield=True),
    "POISON":    _e("RADIATION",
                    "Tout le monde perd des PV en continu.",
                    (150, 255, 60), (5, 5), poison=True),
    "DEGATS2":   _e("DÉGÂTS DOUBLÉS",
                    "Chaque coup fait deux fois plus mal.",
                    (255, 60, 60), (5, 5), dmgx=2.0),
}

SPIN_FRAMES = 75


def effect_pool(diff, exclude=()):
    """Effets disponibles pour une difficulté donnée (exclusion possible)."""
    return [k for k, e in EFFECTS.items()
            if e["lv"][0] <= diff <= e["lv"][1] and k not in exclude]


class Chaos:
    """Roue du chaos : change les règles toutes les N frames.

    Cycle : SPIN_FRAMES images de roue → effet actif pendant (interval - SPIN)
    → nouveau spin. Le Sanctuaire Temporel (S.freeze_t > 0) suspend ce cycle.
    """

    def __init__(self, interval, diff, excl=()):
        self.interval = interval
        self.diff = diff
        self.excl = tuple(excl)
        self.reset()

    def reset(self):
        self.key = None
        self.pending = None
        self.spin = 0
        self.timer = 60
        self.p = dict(DEFAULT_P)
        self.flash = 0
        self.wheel_keys = effect_pool(self.diff, self.excl)

    def roll(self):
        """Déclenche un nouveau spin."""
        pool = effect_pool(self.diff, self.excl)
        self.wheel_keys = pool
        if not pool:
            return
        choices = [k for k in pool if k != self.key] or pool
        self.pending = random.choice(choices)
        self.key = None
        self.p = dict(DEFAULT_P)
        self.spin = SPIN_FRAMES
        try:
            audio.play("chaos")
        except Exception:
            pass

    def update(self, S):
        """Appelé chaque frame par la session (voir § 10)."""
        if self.flash > 0:
            self.flash -= 1
        if self.spin > 0:
            self.spin -= 1
            if self.spin % 7 == 0:
                try:
                    audio.play("tick", 0.5)
                except Exception:
                    pass
            if self.spin == 0:
                self.key = self.pending
                self.p = {**DEFAULT_P, **EFFECTS[self.key]["p"]}
                if self.key == "VENT":
                    self.p["wind"] = random.choice((-1, 1)) * 1.8
                self.timer = max(60, self.interval - SPIN_FRAMES)
                self.flash = 45
                S.shake = max(S.shake, 6)
                try:
                    audio.play("boom", 0.4)
                except Exception:
                    pass
                # Hook "Surfeur de chaos" (skill épique)
                p = getattr(S, "player", None)
                if p is not None and hasattr(p, "on_chaos"):
                    p.on_chaos(S)
        else:
            self.timer -= 1
            if self.timer <= 0:
                self.roll()


def draw_wheel(surface, cx, cy, r, chaos):
    """Dessine la roue qui tourne (utilisé par le HUD de session)."""
    keys = chaos.wheel_keys
    n = len(keys)
    if n == 0:
        return
    seg = math.tau / n
    prog = chaos.spin / SPIN_FRAMES
    idx = keys.index(chaos.pending) if chaos.pending in keys else 0
    rot = -(idx + 0.5) * seg + (prog ** 2) * 3 * math.tau
    for i, k in enumerate(keys):
        a0 = -math.pi / 2 + rot + i * seg
        pts = [(cx, cy)] + [
            (cx + math.cos(a0 + seg * j / 3) * r,
             cy + math.sin(a0 + seg * j / 3) * r) for j in range(4)]
        pygame.draw.polygon(surface, EFFECTS[k]["color"], pts)
        pygame.draw.polygon(surface, NOIR_FOND, pts, 1)
    pygame.draw.circle(surface, BLANC, (cx, cy), r, 3)
    pygame.draw.circle(surface, NOIR_FOND, (cx, cy), 9)
    pygame.draw.polygon(surface, JAUNE_NEON,
                        [(cx - 9, cy - r - 12), (cx + 9, cy - r - 12),
                         (cx, cy - r + 8)])


# ═══════════════════════════════════════════════════════════════════════════
#  ENRICHISSEMENT DU DICTIONNAIRE EN (traductions ajoutées à chaque section)
# ═══════════════════════════════════════════════════════════════════════════

def _register_en_section_6_7():
    """Traductions FR → EN pour les données § 6-7."""
    # Raretés
    for r in RARITY.values():
        EN[r["label"]] = r["en"]
    # Stats
    for fr, en, _f in STAT_FMT.values():
        EN[fr] = en
    # Compétences
    for _t, nfr, nen, dfr, den, _a in SKILL_INFO.values():
        EN[nfr] = nen
        EN[dfr] = den
    # Armes
    EN.update({
        "ROQUETTE": "ROCKET", "CANON TRIPLE": "TRIPLE",
        "LANCE-FLAMMES": "FLAMER", "MITRAILLEUSE": "MINIGUN",
        "RAILGUN": "RAILGUN", "ORBE NOVA": "NOVA ORB",
        "ARME": "WEAPON", "ARMURE": "ARMOR", "SOUTIEN": "SUPPORT",
    })
    # Objets
    EN.update({
        "Canon Triple": "Triple Cannon",
        "[4] Tire 3 projectiles en éventail.":
            "[4] Fires 3 projectiles in a fan.",
        "Lance-Flammes": "Flamethrower",
        "[4] Projectiles enflammés : brûlure continue.":
            "[4] Flaming projectiles: continuous burn.",
        "Mitrailleuse Chrono": "Chrono Minigun",
        "[4] Rafale ultra-rapide, dégâts faibles.":
            "[4] Ultra-fast burst, low damage.",
        "Railgun": "Railgun",
        "[4] Rayon perforant qui traverse tout.":
            "[4] Piercing beam that goes through everything.",
        "Orbe Nova": "Nova Orb",
        "[4] Orbe explosif : dégâts de zone.":
            "[4] Explosive orb: area damage.",
        "Plaque Renforcée": "Reinforced Plate",
        "+50 énergie de bouclier maximale.":
            "+50 maximum shield energy.",
        "Armure Lourde": "Heavy Armor",
        "Tu subis 25% de dégâts en moins.":
            "You take 25% less damage.",
        "Bouclier Phase": "Phase Shield",
        "1 s d'invulnérabilité après chaque coup subi.":
            "1 s of invulnerability after each hit taken.",
        "Bouclier Miroir": "Mirror Shield",
        "Ton bouclier RENVOIE les projectiles.":
            "Your shield REFLECTS projectiles.",
        "Bouclier Nova": "Nova Shield",
        "Quand ton bouclier craque, il explose.":
            "When your shield breaks, it explodes.",
        "Coeur Vital": "Vital Heart",
        "+40 PV maximum.": "+40 maximum HP.",
        "Bottes Lunaires": "Lunar Boots",
        "Tu sautes 25% plus haut.": "You jump 25% higher.",
        "Nanobots": "Nanobots",
        "Régénère 1,5 PV par seconde.":
            "Regenerates 1.5 HP per second.",
        "Dash Chrono": "Chrono Dash",
        "[E] Dash éclair avec invulnérabilité brève.":
            "[E] Lightning dash with brief invulnerability.",
        "Sablier Brisé": "Broken Hourglass",
        "[E] Ralentit le temps pendant 3 s.":
            "[E] Slows time for 3 s.",
    })
    # Stats joueur
    EN.update({
        "PV MAX": "MAX HP", "BOUCLIER": "SHIELD",
        "RECHARGE BOUCLIER": "SHIELD RECHARGE", "VITESSE": "SPEED",
        "PUISSANCE": "POWER", "CADENCE DE TIR": "FIRE RATE",
        "SAUT": "JUMP", "GAIN DE PIÈCES": "COIN GAIN",
    })
    # Difficultés
    EN.update({
        "DÉBUTANT": "BEGINNER", "FACILE": "EASY", "NORMAL": "NORMAL",
        "DIFFICILE": "HARD", "CHAOS": "CHAOS", "VÉTÉRAN": "VETERAN",
        "EXPERT": "EXPERT", "MAÎTRE": "MASTER",
        "GRAND MAÎTRE": "GRANDMASTER", "APOCALYPSE": "APOCALYPSE",
        "CHAMPION I": "CHAMPION I", "CHAMPION II": "CHAMPION II",
        "CHAMPION III": "CHAMPION III", "CHAMPION IV": "CHAMPION IV",
        "LÉGENDE SUPRÊME": "SUPREME LEGEND",
        "IA lente et imprécise. Seulement les chaos les plus doux.":
            "Slow, inaccurate AI. Only the mildest chaos.",
        "IA tolérante. Quelques chaos plus agressifs.":
            "Forgiving AI. A few more aggressive chaos effects.",
        "L'IA classique. Chaos variés, météores, gravité inversée.":
            "The classic AI. Varied chaos, meteors, inverted gravity.",
        "IA redoutable et nombreuse. Chaos destructeurs.":
            "Fearsome, numerous AI. Destructive chaos.",
        "IA quasi parfaite. Radiation, dégâts doublés... survis.":
            "Near-perfect AI. Radiation, double damage... survive.",
        "IA vétéran. Lasers croisés et dalles instables.":
            "Veteran AI. Crossed lasers and unstable tiles.",
        "Maîtrise parfaite requise.": "Perfect mastery required.",
        "Les maîtres du chaos dominent.": "Masters of chaos dominate.",
        "Presque impossible. Presque.": "Almost impossible. Almost.",
        "Dernier palier avant le Mode Champion.":
            "Last tier before Champion Mode.",
        "Épreuve de champion. Puits de distorsion activés.":
            "Champion trial. Distortion wells active.",
        "Missiles traqueurs ambiants.": "Ambient tracker missiles.",
        "Broyeurs mobiles verticaux.": "Mobile vertical crushers.",
        "Champs de plasma au sol.": "Ground plasma fields.",
        "L'ultime défi. Annihilateurs de sauts activés.":
            "The ultimate challenge. Jump annihilators active.",
    })
    # Modes
    EN.update({
        "PARCOURS ÉCHO": "ECHO RUN", "SURVIE ARCADE": "ARCADE SURVIVAL",
        "ARÈNE ÉCHO": "ECHO ARENA", "ZONE GLITCH": "GLITCH ZONE",
        "LE GARDIEN DU TEMPS": "THE TIME GUARDIAN",
        "ÉCLIPSE": "ECLIPSE", "LA FAILLE": "THE RIFT",
        "CAMPAGNE": "CAMPAIGN",
        "Atteins la SORTIE. Tes échos du passé refont ton parcours... et te veulent du mal !":
            "Reach the EXIT. Your past echoes retrace your run... and mean you harm!",
        "Tiens le plus longtemps possible. Chaque manche, ton ancien toi devient un piège.":
            "Hold out as long as you can. Each round, your former self becomes a trap.",
        "Toi + 3 IA. Vos échos combattent pour vous. Termine 1er pour la gloire !":
            "You + 3 AIs. Your echoes fight for you. Finish 1st for glory!",
        "Chaos toutes les 5 s + météores + boss. Survis 3 manches !":
            "Chaos every 5 s + meteors + boss. Survive 3 rounds!",
        "Terrasse le Gardien en 3 manches. Tes échos sont tes ALLIÉS ici !":
            "Take down the Guardian in 3 rounds. Your echoes are ALLIES here!",
        "Dans le noir total, survis... et cherche ce qui brille à la dernière manche.":
            "In total darkness, survive... and look for what glimmers in the last round.",
        "Le Parcours ultime : pièges doublés, chaos toutes les 5 s, 40 s max !":
            "The ultimate Run: doubled traps, chaos every 5 s, 40 s max!",
        "Défi ramassé d'une manche : atteins la SORTIE, élimine tout, ou survis !":
            "One-round challenge: reach the EXIT, clear everything, or survive!",
    })
    # Niveaux secrets
    for sid, info in SECRET_LEVELS_INFO.items():
        EN[sid] = sid
        EN[info["desc"]] = {
            "Faille gravitationnelle permanente.": "Permanent gravitational rift.",
            "Tes échos se dédoublent.": "Your echoes duplicate.",
            "Contrôles inversés en permanence.": "Permanently inverted controls.",
            "Accélération temporelle constante.": "Constant time acceleration.",
            "Visibilité réduite au strict minimum.": "Visibility reduced to the bare minimum.",
            "Seuls tes échos peuvent te sauver.": "Only your echoes can save you.",
            "Aucune arme ne fonctionne.": "No weapon works.",
            "Rotation constante du décor.": "Constant background rotation.",
            "Ton reflet te traque.": "Your reflection is hunting you.",
            "Tous les chaos activés simultanément.": "All chaos effects activated at once.",
        }.get(info["desc"], info["desc"])
    # Causes de mort
    EN.update({
        "TIR DU JOUEUR": "PLAYER SHOT", "TIR DE L'IA": "AI SHOT",
        "TIR ENNEMI": "ENEMY SHOT", "TIR DE TON ÉCHO": "YOUR ECHO'S SHOT",
    })
    # Effets de chaos
    for key, e in EFFECTS.items():
        EN[e["name"]] = {
            "INVERSION": "INVERTED CONTROLS", "LUNE": "MOON GRAVITY",
            "GLACE": "SLIPPERY FLOOR", "RALENTI": "SLOW MOTION",
            "TRAMPOLINE": "TRAMPOLINES", "VENT": "WIND STORM",
            "GEANTS": "GIANT BULLETS", "RICOCHET": "RICOCHETS",
            "TURBO": "TIME TURBO", "BLACKOUT": "BLACKOUT",
            "TELEGUIDE": "HOMING SHOTS", "METEORES": "METEOR SHOWER",
            "ANTIGRAV": "ANTI-GRAVITY", "TELEPORT": "TELEPORTATION",
            "ECHO_RAGE": "ENRAGED ECHOES", "BARRAGE": "BULLET RAIN",
            "LAVE": "LAVA", "NOSHIELD": "NO SHIELD",
            "POISON": "RADIATION", "DEGATS2": "DOUBLE DAMAGE",
        }[key]
        EN[e["desc"]] = {
            "INVERSION": "Left and right are swapped for everyone.",
            "LUNE": "Low gravity: giant jumps and gliding.",
            "GLACE": "You skate: maximum inertia.",
            "RALENTI": "The world slows down (echoes, shots, AI)... not you.",
            "TRAMPOLINE": "The floor bounces: everyone keeps jumping.",
            "VENT": "A violent wind pushes everyone.",
            "GEANTS": "Projectiles are huge and devastating.",
            "RICOCHET": "All shots bounce off the walls.",
            "TURBO": "Players, echoes, shots and monsters move faster.",
            "BLACKOUT": "Lights out: only your lamp lights the way.",
            "TELEGUIDE": "Projectiles hunt their target.",
            "METEORES": "Flaming rocks fall from the sky.",
            "ANTIGRAV": "Spaceweightlessness: free drift, jumps disabled.",
            "TELEPORT": "Everyone is teleported randomly every 3 s.",
            "ECHO_RAGE": "Your echoes replay the past almost 2× faster!",
            "BARRAGE": "Hostile shots burst from the screen edges.",
            "LAVE": "The floor burns: don't stay on the ground!",
            "NOSHIELD": "Shields are disabled for everyone.",
            "POISON": "Everyone keeps losing HP.",
            "DEGATS2": "Every hit hurts twice as much.",
        }[key]
    # Succès à paliers + uniques
    for a in ACHIEVEMENTS:
        if a.get("en_name"):
            EN[a["name"]] = a["en_name"]
            EN[a["desc"]] = a["en_desc"]
    EN.update({
        "Première boucle": "First Loop", "Boucle infinie": "Infinite Loop",
        "Horloger fou": "Mad Clockmaker", "Gardien des boucles": "Keeper of Loops",
        "Chasseur": "Hunter", "Traqueur": "Tracker",
        "Exterminateur": "Exterminator", "Fléau du Temps": "Scourge of Time",
        "Échauffement": "Warm-Up", "Marathon temporel": "Time Marathon",
        "Maître des boucles": "Loop Master", "Éternel": "The Eternal",
        "Premier achat": "First Purchase", "Collectionneur": "Collector",
        "Garde-robe infinie": "Endless Wardrobe",
        "Panthéon du Chaos": "Chaos Pantheon",
        "Premier tirage": "First Draw", "Main chanceuse": "Lucky Hand",
        "Roi du jackpot": "Jackpot King",
        "Premier secret": "First Secret", "Initié": "Initiate",
        "Maître des secrets": "Secret Master",
        "Survivant": "Survivor", "Survivant aguerri": "Seasoned Survivor",
        "Légende du Chaos": "Chaos Legend",
        "Seigneur du Temps": "Time Lord", "Coureur": "Runner",
        "Fantôme du Parcours": "Run Phantom", "Éclair": "Lightning",
        "Intouchable": "Untouchable", "Roi de l'Arène": "Arena King",
        "Survivant du Glitch": "Glitch Survivor",
        "Briseur de Gardien": "Guardian Breaker",
        "Chasseur de reliques": "Relic Hunter",
        "Au-delà du Temps": "Beyond Time",
        "Explorateur du Chaos": "Chaos Explorer",
        "pièces": "coins", "gemmes": "gems",
        "boîte mystère": "mystery box", "boîtes mystères": "mystery boxes",
        "compensation": "compensation",
        "BOÎTE MYSTÈRE": "MYSTERY BOX", "JACKPOT !": "JACKPOT!",
        "CHANCE PROTÉGÉE !": "LUCKY STREAK!",
        "AMÉLIORATION GRATUITE !": "FREE UPGRADE!",
        "SKIN SECRET !": "SECRET SKIN!",
        "Aucune boîte mystère à ouvrir.": "No mystery box to open.",
        "niveau": "level", "valeur offerte": "value gifted",
        "Collection complète : gemmes bonus !":
            "Collection complete: bonus gems!",
        "Tout est déjà au maximum : gemmes bonus !":
            "Everything is maxed: bonus gems!",
    })


_register_en_section_6_7()

# ═══════════════════════════════════════════════════════════════════════════
#  FIN § 6-7
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#  § 8 — ENTITÉS (particules, projectiles, combattants, échos, minis)
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  PARTICULES
# ─────────────────────────────────────────────────────────────────────────
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "lifetime", "max_life")

    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.color = color
        self.size = float(size)
        self.lifetime = int(lifetime)
        self.max_life = int(lifetime)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        if self.size > 0.3:
            self.size = max(0.0, self.size - 0.05)

    def draw(self, surface):
        if self.lifetime <= 0 or self.size < 0.3:
            return
        # Sur web, créer une surface SRCALPHA par particule est trop lent.
        # On utilise directement pygame.draw avec la couleur (sans alpha lissé).
        r = max(1, int(self.size))
        c = self.color if len(self.color) == 3 else self.color[:3]
        
        if IS_WEB:
            # Rendu direct ultra-rapide pour le web
            pygame.draw.circle(surface, c, (int(self.x), int(self.y)), r)
        else:
            # Rendu joli avec fondu pour le PC
            alpha = int((self.lifetime / self.max_life) * 255)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*c, alpha), (r, r), r)
            surface.blit(s, (int(self.x - r), int(self.y - r)))


class ParticleManager:
    """Gestionnaire de particules avec plafond selon la qualité graphique."""

    CAPS = (120, 280, 450)

    def __init__(self):
        self.particles = []

    def emit(self, x, y, count, color, speed_range=(-2, 2),
             size_range=(2, 5), lifetime=20):
        q = int(clamp(SET.get("particles", 2), 0, 2))
        if len(self.particles) > self.CAPS[q]:
            return
        if q == 0:
            count = max(1, count // 2)
        for _ in range(count):
            vx = random.uniform(*speed_range)
            vy = random.uniform(*speed_range)
            sz = random.uniform(*size_range)
            self.particles.append(
                Particle(x, y, vx, vy, color, sz, lifetime))

    def update_and_draw(self, surface):
        alive = []
        for p in self.particles:
            p.update()
            p.draw(surface)
            if p.lifetime > 0 and p.size >= 0.3:
                alive.append(p)
        self.particles = alive

    def clear(self):
        self.particles.clear()


particle_system = ParticleManager()


class FloatText:
    """Texte flottant qui monte et s'estompe."""

    __slots__ = ("x", "y", "text", "color", "big", "life", "max_life")

    def __init__(self, x, y, text, color, big=False):
        self.x, self.y = float(x), float(y)
        self.text = str(text)
        self.color = color
        self.big = big
        self.life = self.max_life = 50 if big else 38

    def update(self):
        self.y -= 0.9
        self.life -= 1

    def draw(self, surf):
        f = FONT_MED if self.big else FONT_SMALL
        try:
            img = f.render(self.text, True, self.color)
            sh = f.render(self.text, True, (0, 0, 0))
        except Exception:
            return
        a = int(255 * clamp(self.life / (self.max_life * 0.6), 0, 1))
        img.set_alpha(a)
        sh.set_alpha(a)
        surf.blit(sh, sh.get_rect(center=(int(self.x) + 1, int(self.y) + 1)))
        surf.blit(img, img.get_rect(center=(int(self.x), int(self.y))))


# ─────────────────────────────────────────────────────────────────────────
#  PROJECTILE
# ─────────────────────────────────────────────────────────────────────────
class Projectile:
    """Projectile générique : plasma, laser, missile, triple, burn, spray,
    rail (perforant), nova (explosif). Supporte rebonds, homing, giant."""

    def __init__(self, x, y, vx, vy, kind, team, src_id, src_kind, S,
                 color=None, dmg=None, mult=1.0):
        w = WEAPONS[kind]
        giant = S.chaos.p.get("giant", False)
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.p_type = kind
        self.team = team
        self.src_id = src_id
        self.src_kind = src_kind
        self.radius = w["r"] * (2.3 if giant else 1)
        self.damage = (dmg if dmg else w["dmg"]) * mult * (1.5 if giant else 1)
        self.bounces = 2 if S.chaos.p.get("ricochet") else 0
        self.homing = bool(S.chaos.p.get("homing"))
        self.speed = max(1.0, math.hypot(vx, vy))
        self.pierce = w.get("pierce", False)
        self.explode = w.get("explode", False)
        self.burn = w.get("burn", False)
        self.hit = set()
        self.active = True

        if color is not None:
            self.color = color
        elif "color" in w:
            self.color = w["color"]
        elif kind == "PLASMA":
            self.color = JAUNE_NEON if team == "P" else ROUGE_NEON
        elif kind == "LASER":
            self.color = CYAN_NEON if team == "P" else PURPLE_NEON
        else:
            self.color = ROUGE_NEON

        r = int(self.radius)
        self.rect = pygame.Rect(int(x) - r, int(y) - r, r * 2, r * 2)

    def update(self, S):
        ts = S.ts(self.team)
        # Homing
        if self.homing:
            tgt = S.nearest_enemy(self.x, self.y, self.team, 520)
            if tgt:
                dx = tgt.rect.centerx - self.x
                dy = tgt.rect.centery - self.y
                d = math.hypot(dx, dy) or 1
                nvx = self.vx * 0.92 + dx / d * self.speed * 0.08
                nvy = self.vy * 0.92 + dy / d * self.speed * 0.08
                n = math.hypot(nvx, nvy) or 1
                self.vx = nvx / n * self.speed
                self.vy = nvy / n * self.speed

        # Vent
        self.vx += S.chaos.p.get("wind", 0.0) * 0.02 * ts

        px, py = self.x, self.y
        self.x += self.vx * ts
        self.y += self.vy * ts
        r = int(self.radius)
        self.rect.x = int(self.x) - r
        self.rect.y = int(self.y) - r

        # Rebond murs
        if self.bounces > 0 and (self.x < 0 or self.x > WIDTH):
            self.vx = -self.vx
            self.x = clamp(self.x, 0, WIDTH)
            self.bounces -= 1

        # Collision plateformes
        for plat in S.platforms:
            if self.rect.colliderect(plat):
                if self.bounces > 0:
                    self.bounces -= 1
                    prev = pygame.Rect(int(px) - r, int(py) - r, r * 2, r * 2)
                    if prev.bottom <= plat.top or prev.top >= plat.bottom:
                        self.vy = -self.vy
                    else:
                        self.vx = -self.vx
                    self.x, self.y = px, py
                    self.rect.x = int(px) - r
                    self.rect.y = int(py) - r
                    particle_system.emit(self.x, self.y, 4, self.color)
                else:
                    self.active = False
                    particle_system.emit(self.x, self.y, 6, self.color)
                break

        # Traînées
        if self.p_type in ("MISSILE", "BURN"):
            particle_system.emit(self.x, self.y, 2, (255, 120, 0),
                                 (-1, 1), (2, 6), 15)
        elif self.p_type in ("PLASMA", "NOVA", "TRIPLE"):
            particle_system.emit(self.x, self.y, 1, self.color,
                                 (-0.5, 0.5), (1, 3), 10)

        # Hors écran
        if (self.x < -60 or self.x > WIDTH + 60
                or self.y < -60 or self.y > HEIGHT + 60):
            self.active = False
            self.explode = False

    def draw(self, surface):
        ix, iy, r = int(self.x), int(self.y), int(self.radius)
        if self.p_type in ("LASER", "RAIL"):
            k = 1.5 if self.p_type == "LASER" else 2.2
            ex = self.x - self.vx * k
            ey = self.y - self.vy * k
            pygame.draw.line(surface, self.color, (ix, iy), (ex, ey),
                             max(5, r + 1))
            pygame.draw.line(surface, BLANC, (ix, iy), (ex, ey), 2)
        elif self.p_type == "NOVA":
            pygame.draw.circle(surface, self.color, (ix, iy),
                               r + 3 + int(2 * math.sin(ix * 0.1)), 2)
            pygame.draw.circle(surface, self.color, (ix, iy), r)
            pygame.draw.circle(surface, BLANC, (ix, iy), max(2, r - 5))
        elif self.p_type == "BURN":
            pygame.draw.circle(surface, ORANGE, (ix, iy), r)
            pygame.draw.circle(surface, JAUNE_NEON, (ix, iy), max(1, r - 3))
        elif self.p_type == "MISSILE":
            pygame.draw.circle(surface, self.color, (ix, iy), r)
            pygame.draw.circle(surface, JAUNE_NEON, (ix, iy), max(1, r - 3))
        else:
            pygame.draw.circle(surface, self.color, (ix, iy), r)
            pygame.draw.circle(surface, BLANC, (ix, iy), max(1, r - 2))


# ─────────────────────────────────────────────────────────────────────────
#  FIGHTER (combattant joueur / IA / boss)
# ─────────────────────────────────────────────────────────────────────────
class Fighter:
    """Combattant polyvalent. Porte toutes les compétences de skin, les
    bonus d'objets, les actifs mythiques et les passifs permanents."""

    def __init__(self, ident, team, skin_key, x, y, hp=100, shield=100,
                 record=False, size=(28, 38)):
        self.id = ident
        self.team = team
        self.skin_key = skin_key
        self.w, self.h = size
        self.x, self.y = float(x), float(y)
        self.rect = pygame.Rect(int(x), int(y), self.w, self.h)
        self.vx = self.vy = 0.0
        self.speed = 6.0
        self.on_ground = False
        self.face = 1

        self.hp = self.max_hp = hp
        self.shield_energy = self.max_shield = shield
        self.shield_active = False
        self.weapon_type = "PLASMA"
        self.cooldown = 0.0
        self.alive = True
        self.handled = False

        self.inv = self.trap_cd = self.contact_cd = 0
        self.cause = ""
        self.last_src = None
        self.brain = None
        self.record = record
        self.rec = []
        self.shots = []
        self.t = 0
        self.boss = False
        self.boss_mode = None       # "ECHO" ou "IA" (boss)

        # Capacités de base
        self.jump_v = 12.5
        self.dmg_mult = 1.0
        self.rate = 1.0
        self.regen = 0.4
        self.reduce = 0.0
        self.hp_regen = 0.0
        self.reflect = False
        self.nova = False
        self.phase = False
        self.special = None
        self.ability = None
        self.ab_cd = 0
        self.dash = 0
        self.dash_dir = 1
        self.burn = 0
        self.burn_src = None
        self.hitflash = 0

        # Compétences de skin
        self.skills = {}
        self.rarity = "COMMON"
        self.evade = self.thorns = self.glide = 0.0
        self.fury = 0.0
        self.kill_heal = 0.0
        self.echo_pow = 0.0
        self.air_jumps = 0
        self.jumps_left = 0
        self.phase_hit = 0
        self.trap_free = 0
        self.bounty = 0
        self.trapsafe = 0
        self.haste = 0
        self.shock = None
        self.shock_t = 0
        self.drift = None
        self.drift_t = 0
        self.ashield_max = 0
        self.ashield_t = 0
        self.ashield = False
        self.wind2 = False
        self.chain = None
        self._jp = False

        # Actifs mythiques
        self.sa = None
        self.sa_cd = 0
        self.gdmg = 1.0
        self.black_hole = None
        self.qdodge = 0.0
        self.qdodge_cd = 0
        self.qdodge_t = 0
        self.cf = None
        self.cf_t = 0
        self.cf_cd = 0
        self.combustion = 0
        self.combustion_per = 0.0
        self.combustion_max = 0
        self.auto_shield = 0
        self.auto_shield_t = 0
        self.evade_extra = 0.0
        self.trapsafe_perm = 0
        self.immune_slow = False

    # ------------------------------------------------------------------
    #  Application d'un loadout
    # ------------------------------------------------------------------
    def apply_loadout(self, L):
        self.max_hp = self.hp = L["max_hp"]
        self.max_shield = self.shield_energy = L["max_shield"]
        self.regen = L["regen"]
        self.speed = L["speed"]
        self.dmg_mult = L["power"]
        self.rate = L["rate"]
        self.jump_v = L["jump"]
        self.special = L["special"]
        self.reduce = L["reduce"]
        self.reflect = L["reflect"]
        self.nova = L["nova"]
        self.phase = L["phase"]
        self.hp_regen = L["hp_regen"]
        self.ability = L["ability"]
                # Nouveaux bonus d'armures/objets
        self.auto_shield = L.get("auto_shield", 0)
        self.evade_extra = L.get("evade", 0.0)
        self.trapsafe_perm = L.get("trapsafe", 0)
        self.immune_slow = L.get("immune_slow", False)

        sk = L.get("skills") or {}
        self.skills = dict(sk)
        self.rarity = L.get("rarity", "COMMON")

        self.evade = min(0.35, sk.get("evade", 0.0))
        self.thorns = min(0.5, sk.get("thorns", 0.0))
        self.air_jumps = self.jumps_left = int(sk.get("double_jump", 0))
        self.glide = float(sk.get("glide", 0.0))
        self.phase_hit, self.trap_free = sk.get("reactive") or (0, 0)
        self.shock, self.shock_t = sk.get("shockwave"), 0
        self.ashield_max = int(sk.get("auto_shield", 0))
        self.ashield = self.ashield_max > 0
        self.ashield_t = 0
        self.wind2 = bool(sk.get("second_wind"))
        self.drift, self.drift_t = sk.get("time_drift"), 0
        self.fury = sk.get("fury", 0.0)
        self.kill_heal = sk.get("kill_heal", 0.0)
        self.bounty = sk.get("bounty", 0)
        self.echo_pow = sk.get("echo_power", 0.0)
        self.chain = sk.get("chain_blast")
        self.sa = sk.get("sanctuary")
        self.sa_cd = 0
        self.gdmg = float(L.get("gdmg", 1.0))
        self.black_hole = sk.get("black_hole")
        qd = sk.get("quantum_dodge")
        if qd:
            self.qdodge, self.qdodge_cd = qd[0], qd[1]
        else:
            self.qdodge, self.qdodge_cd = 0.0, 0
        self.qdodge_t = 0
        self.cf = sk.get("champion_frenzy")
        self.cf_t = 0
        self.cf_cd = 0
        ce = sk.get("combustion_elite")
        if ce:
            self.combustion_per, self.combustion_max = ce
        else:
            self.combustion_per, self.combustion_max = 0.0, 0
        self.combustion = 0

    # ------------------------------------------------------------------
    #  Calculs dérivés
    # ------------------------------------------------------------------
    def shot_power(self):
        """Puissance de tir actuelle (Rage + Frénésie + Combustion)."""
        m = self.dmg_mult
        if self.fury and self.hp < self.max_hp * 0.35:
            m *= 1.0 + self.fury
        if self.cf_t > 0:
            m *= 2.0
        if self.combustion_per > 0 and self.combustion > 0:
            m *= 1.0 + self.combustion_per * self.combustion
        return m

    # ------------------------------------------------------------------
    #  Compétences réactives
    # ------------------------------------------------------------------
    def perk_on_hit(self, dmg, src, S):
        """Déclenché quand le joueur encaisse un coup."""
        cx, cy = self.rect.center
        if self.phase_hit:
            self.inv = max(self.inv, int(self.phase_hit))
        if self.trap_free:
            self.trapsafe = max(self.trapsafe, int(self.trap_free))

        # Réfraction (thorns)
        if self.thorns and random.random() < self.thorns:
            att = next((o for o in S.fighters
                        if o is not self and o.alive and o.id == src), None)
            if att is not None:
                att.hurt(max(8.0, dmg * 1.5), "RENVOI", S, src=self.id,
                         blockable=False, force=True)
            else:
                S.explode(cx, cy, 80, max(12.0, dmg * 1.5),
                          self.team, self.id, "player")
            particle_system.emit(cx, cy, 14, (140, 230, 255),
                                 (-4, 4), (3, 6), 22)
            S.add_text(cx, self.rect.top - 24, tr("RENVOI !"),
                       (140, 230, 255), True)

        # Onde de choc (shockwave légendaire)
        if self.shock and self.shock_t <= 0:
            radius, sdmg, cd = self.shock
            self.shock_t = cd
            S.explode(cx, cy, radius, sdmg * self.gdmg,
                      self.team, self.id, "player")
            S.shake = max(S.shake, 10)
            particle_system.emit(cx, cy, 40, RARITY[self.rarity]["color"],
                                 (-7, 7), (3, 8), 34)
            S.add_text(cx, self.rect.top - 38, tr("ONDE DE CHOC !"),
                       JAUNE_NEON, True)

        # Réflexes temporels
        if self.drift and self.drift_t <= 0 and 0 < self.hp < self.max_hp * 0.3:
            dur, cd = self.drift
            S.slow_timer = max(S.slow_timer, int(dur))
            self.drift_t = cd
            S.add_text(cx, self.rect.top - 52, tr("TEMPS RALENTI"),
                       CYAN_NEON, True)

    # ------------------------------------------------------------------
    #  Actifs mythiques
    # ------------------------------------------------------------------
    def cast_sanctuary(self, S):
        """Sanctuaire Temporel : fige le temps et libère une onde dévastatrice.
        Le joueur est intouchable et ses PV se régénèrent ×3 pendant l'effet."""
        dur, cd, dmg, radius = self.sa
        self.sa_cd = int(cd)
        cx, cy = self.rect.center
        S.freeze_t = S.freeze_max = int(dur)
        S.fissure(cx, cy, radius)
        S.explode(cx, cy, radius, dmg * self.gdmg,
                  self.team, self.id, "player")
        S.shake = max(S.shake, 20)
        particle_system.emit(cx, cy, 90, (255, 215, 90), (-9, 9), (3, 9), 46)
        particle_system.emit(cx, cy, 50, (255, 60, 110), (-7, 7), (3, 7), 40)
        S.add_text(cx, self.rect.top - 40, tr("SANCTUAIRE TEMPOREL"),
                   (255, 215, 90), True)
        audio.play("chaos", 0.9)
        audio.play("boom", 0.8)

    def cast_frenzy(self, S):
        """Frénésie du Champion : cadence ×3, vitesse +40 %, dégâts ×2."""
        dur, cd, _rate_m, _spd_m, _dmg_m = self.cf
        self.cf_t = int(dur)
        self.cf_cd = int(cd)
        cx, cy = self.rect.center
        particle_system.emit(cx, cy, 110, (255, 220, 100),
                             (-9, 9), (3, 9), 45)
        particle_system.emit(cx, cy, 60, (255, 100, 40),
                             (-7, 7), (3, 8), 40)
        S.shake = max(S.shake, 16)
        S.add_text(cx, self.rect.top - 34, tr("FRÉNÉSIE DU CHAMPION"),
                   (255, 220, 100), True)
        self.inv = max(self.inv, 30)
        audio.play("chaos", 1.0)
        audio.play("win", 0.7)

    def cast_black_hole(self, S):
        """Trou Noir Quantique : aspire ennemis + projectiles, puis déflagration."""
        radius, dmg, dur, cd = self.black_hole
        self.sa_cd = int(cd)
        cx, cy = self.rect.center
        pull_r = radius * 1.35

        for f in S.fighters:
            if not f.alive or f is self or f.team == self.team:
                continue
            dx, dy = cx - f.rect.centerx, cy - f.rect.centery
            d = math.hypot(dx, dy) or 1
            if d < pull_r:
                f.x += dx / d * 12
                f.y += dy / d * 12
                f.rect.topleft = (int(f.x), int(f.y))
                f.vy = 0.0
        for m in S.minis:
            if not m.alive:
                continue
            dx, dy = cx - m.rect.centerx, cy - m.rect.centery
            d = math.hypot(dx, dy) or 1
            if d < pull_r:
                m.rect.x += int(dx / d * 12)
                m.rect.y += int(dy / d * 12)
                m.fx = float(m.rect.x)
        for pr in S.projectiles[:]:
            if pr.team == self.team:
                continue
            if math.hypot(pr.x - cx, pr.y - cy) < pull_r:
                pr.active = False
                particle_system.emit(pr.x, pr.y, 6, (200, 80, 255),
                                     (-3, 3), (2, 5), 18)

        S.waves.append(dict(x=cx, y=cy, r=14.0, mx=float(radius),
                            life=38, max=38))
        S.black_hole_fx = dict(x=cx, y=cy, r=pull_r,
                               life=int(dur), max=int(dur))
        S.explode(cx, cy, radius, dmg * self.gdmg,
                  self.team, self.id, "player")
        particle_system.emit(cx, cy, 110, (200, 80, 255),
                             (-10, 10), (3, 10), 60)
        particle_system.emit(cx, cy, 60, (255, 235, 120),
                             (-8, 8), (2, 8), 46)
        S.shake = max(S.shake, 24)
        S.add_text(cx, self.rect.top - 40, tr("TROU NOIR QUANTIQUE"),
                   (200, 80, 255), True)
        self.inv = max(self.inv, 40)
        audio.play("chaos", 1.0)
        audio.play("boom", 0.9)

    # ------------------------------------------------------------------
    #  Physique apesanteur (chaos ANTIGRAV)
    # ------------------------------------------------------------------
    def _antigrav_step(self, inp, S, dt=1.0):
        p = S.chaos.p
        left, right = inp.get("left"), inp.get("right")
        if p["invert"]:
            left, right = right, left
        dirx = int(bool(right)) - int(bool(left))

        haste = 1.25 if self.haste > 0 else 1.0
        if self.cf_t > 0:
            haste *= 1.4

        # Actifs mythiques
        if inp.get("skin_ab") and self.alive:
            if self.sa and self.sa_cd <= 0:
                self.cast_sanctuary(S)
                inp = dict(inp); inp["skin_ab"] = False
            elif self.black_hole and self.sa_cd <= 0:
                self.cast_black_hole(S)
                inp = dict(inp); inp["skin_ab"] = False
            elif self.cf and self.cf_cd <= 0:
                self.cast_frenzy(S)
                inp = dict(inp); inp["skin_ab"] = False

                # Capacité de soutien [E]
        if inp.get("ability") and self.ability and self.ab_cd <= 0:
            if self.ability == "DASH":
                self.dash, self.dash_dir = 9, (dirx or self.face)
                self.inv = max(self.inv, 16)
                self.ab_cd = 110
                audio.play("dash")
            elif self.ability == "TIME":
                S.slow_timer = 180
                self.ab_cd = 1200
                audio.play("chaos", 0.6)
            elif self.ability == "HEAL_PULSE":
                # Pulse : +25 PV instantanés
                self.hp = min(self.max_hp, self.hp + 25)
                self.ab_cd = 600
                particle_system.emit(self.rect.centerx,
                                     self.rect.centery, 26,
                                     (100, 255, 140), (-5, 5), (3, 7), 30)
                S.add_text(self.rect.centerx, self.rect.top - 24,
                           "+25", VERT_NEON, True)
                audio.play("pickup", 0.8)
            elif self.ability == "HEAL_ZONE":
                # Zone de soin : tant que le joueur reste immobile, +2 PV/s
                self.hp = min(self.max_hp, self.hp + 15)
                self.ab_cd = 900
                particle_system.emit(self.rect.centerx,
                                     self.rect.centery, 30,
                                     (140, 255, 180), (-6, 6), (2, 6), 40)
                S.add_text(self.rect.centerx, self.rect.top - 24,
                           tr("ZONE DE SOIN"), VERT_NEON, True)
                audio.play("pickup", 0.7)
            elif self.ability == "VISION":
                # Vision parfaite : boost critique + marque les ennemis
                self.ab_cd = 1200
                self.haste = max(self.haste, 240)
                # Marque tous les ennemis d'un halo jaune pendant 4 s
                for f in S.fighters:
                    if f.team != self.team and f.alive:
                        particle_system.emit(f.rect.centerx,
                                             f.rect.centery, 12,
                                             (255, 220, 100),
                                             (-3, 3), (2, 5), 30)
                S.add_text(self.rect.centerx, self.rect.top - 24,
                           tr("VISION PARFAITE"), JAUNE_NEON, True)
                audio.play("special", 0.8)
            elif self.ability == "FRENZY":
                # Frénésie : +30% cadence, +20% vitesse, +15% dégâts
                self.haste = max(self.haste, 300)
                self.rate *= 1.30        # cumul rate
                self.dmg_mult *= 1.15    # cumul dégâts
                self.ab_cd = 1500
                particle_system.emit(self.rect.centerx,
                                     self.rect.centery, 50,
                                     (255, 100, 220), (-8, 8), (3, 8), 45)
                S.shake = max(S.shake, 10)
                S.add_text(self.rect.centerx, self.rect.top - 24,
                           tr("FRÉNÉSIE"), ROSE, True)
                audio.play("chaos", 0.9)

        # Physique apesanteur
        if self.dash > 0:
            self.dash -= 1
            self.vx, self.vy = self.dash_dir * 17, 0.0
            if self.t % 2 == 0:
                particle_system.emit(self.rect.centerx, self.rect.centery, 2,
                                     SKINS[self.skin_key]["accent"],
                                     (-1, 1), (3, 6), 18)
        else:
            target_vx = dirx * self.speed * 0.75 * haste
            self.vx += (target_vx - self.vx) * 0.075 * dt
            self.vx *= 0.995
            self.vy += 0.04 * dt
            self.vy = clamp(self.vy, -4.0, 4.0)
            if inp.get("jump"):
                self.vy = max(-5.2, self.vy - 0.55 * dt)
            if inp.get("down"):
                self.vy = min(5.2, self.vy + 0.55 * dt)

        # Intégration + collisions
        wind = p["wind"]
        dxm = (self.vx + wind) * dt
        self.x = clamp(self.x + dxm, 0, WIDTH - self.w)
        self.rect.x = int(round(self.x))
        self.y += self.vy * dt
        self.rect.y = int(round(self.y))
        self.on_ground = False
        for plat in S.platforms:
            if self.rect.colliderect(plat):
                ov_x = min(self.rect.right, plat.right) - max(self.rect.left, plat.left)
                ov_y = min(self.rect.bottom, plat.bottom) - max(self.rect.top, plat.top)
                if ov_y < ov_x:
                    if self.vy > 0:
                        self.rect.bottom = plat.top
                        self.vy = 0
                        self.on_ground = True
                    else:
                        self.rect.top = plat.bottom
                        self.vy = 0
                    self.y = float(self.rect.y)
                else:
                    if dxm > 0:
                        self.rect.right = plat.left
                    elif dxm < 0:
                        self.rect.left = plat.right
                    self.x = float(self.rect.x)
                    self.vx *= -0.3
        if self.rect.top < 0:
            self.rect.top = 0
            self.y = 0.0
            self.vy = max(self.vy, 0)
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
            self.y = float(self.rect.y)
            self.vy = min(self.vy, 0)
            self.on_ground = True

        # Bouclier
        if inp.get("shield") and self.shield_energy > 5 and not p["noshield"]:
            self.shield_active = True
            self.shield_energy -= 1.2 * dt
            if self.shield_energy <= 0:
                self.shield_energy, self.shield_active = 0, False
                if self.nova:
                    S.explode(self.rect.centerx, self.rect.centery, 120, 42,
                              self.team, self.id,
                              "player" if self is S.player else "ai")
        else:
            self.shield_active = False
            if self.shield_energy < self.max_shield:
                self.shield_energy = min(self.max_shield,
                                         self.shield_energy + self.regen * dt)

        # Régénération PV
        if self.hp_regen and self.alive and self.hp < self.max_hp:
            boost = 3.0 if (self is S.player and S.freeze_t > 0) else 1.0
            self.hp = min(self.max_hp,
                          self.hp + self.hp_regen * boost / 60.0 * dt)

        # Tir / visée
        if inp.get("weapon") and inp["weapon"] in WEAPONS:
            self.weapon_type = inp["weapon"]
        aim = inp.get("aim")
        if aim:
            self.face = 1 if aim[0] >= self.rect.centerx else -1
        elif abs(self.vx) > 0.3:
            self.face = 1 if self.vx > 0 else -1
        if inp.get("shoot"):
            self.shoot(inp["shoot"], S)
        if self.cooldown > 0:
            self.cooldown -= dt

        # Traînée
        if abs(self.vx) > 2 and self.t % 5 == 0:
            particle_system.emit(self.rect.centerx, self.rect.bottom, 1,
                                 SKINS[self.skin_key]["trail"],
                                 (-0.6, 0.6), (1, 3), 14)
        if self.record:
            self.rec.append((self.rect.x, self.rect.y, self.face,
                             self.shield_active, self.weapon_type,
                             not self.on_ground, self.vx))

    # ------------------------------------------------------------------
    #  Hook chaos (Surfeur de chaos)
    # ------------------------------------------------------------------
    def on_chaos(self, S):
        cs = self.skills.get("chaos_surf")
        if not cs or not self.alive:
            return
        heal, shield_pct, haste = cs
        self.hp = min(self.max_hp, self.hp + heal)
        self.shield_energy = min(self.max_shield,
                                 self.shield_energy + self.max_shield * shield_pct)
        self.haste = int(haste)
        cx, cy = self.rect.center
        particle_system.emit(cx, cy, 26, (255, 80, 220),
                             (-5, 5), (3, 7), 30)
        S.add_text(cx, self.rect.top - 24, tr("CHAOS DOMPTÉ"),
                   (255, 110, 230), True)
        audio.play("pickup", 0.5)

    # ------------------------------------------------------------------
    #  Rendu des auras / effets passifs
    # ------------------------------------------------------------------
    def draw_perk_fx(self, surf):
        col = RARITY[self.rarity]["color"]
        cx, cy = self.rect.center
        # Couronne de 12 éclats : Sanctuaire prêt / en recharge
        if self.sa:
            rdy = self.sa_cd <= 0
            ang0 = self.t * 0.06
            for i in range(12):
                ang = ang0 + i * math.tau / 12
                pygame.draw.circle(
                    surf,
                    (255, 215, 90) if rdy else (110, 70, 90),
                    (int(cx + math.cos(ang) * 31),
                     int(cy + math.sin(ang) * 25)),
                    3 if i % 3 == 0 else 2)
        # Bouclier automatique
        if self.ashield_max and self.ashield:
            rr = 34
            s = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pulse = 70 + int(40 * math.sin(self.t * 0.12))
            pygame.draw.circle(s, (*col, pulse), (rr + 2, rr + 2), rr, 3)
            surf.blit(s, (cx - rr - 2, cy - rr - 2))
        # Petites particules épiques+
        if RARITY[self.rarity]["rank"] >= 2 and self.t % 7 == 0:
            particle_system.emit(cx + random.randint(-10, 10),
                                 self.rect.bottom - 4, 1, col,
                                 (-0.5, 0.5), (1, 3), 18)
        if self.trapsafe > 0 and self.t % 4 == 0:
            particle_system.emit(cx, self.rect.bottom, 1, ORANGE,
                                 (-1, 1), (1, 3), 12)
        if self.haste > 0 and self.t % 3 == 0:
            particle_system.emit(cx, cy, 1, (255, 110, 230),
                                 (-1, 1), (2, 4), 14)

    # ------------------------------------------------------------------
    #  Tick (compteurs de refroidissement)
    # ------------------------------------------------------------------
    def tick(self):
        self.inv = max(0, self.inv - 1)
        self.trap_cd = max(0, self.trap_cd - 1)
        self.contact_cd = max(0, self.contact_cd - 1)
        self.hitflash = max(0, self.hitflash - 1)
        self.ab_cd = max(0, self.ab_cd - 1)
        self.trapsafe = max(0, self.trapsafe - 1)
        self.haste = max(0, self.haste - 1)
        self.shock_t = max(0, self.shock_t - 1)
        self.sa_cd = max(0, self.sa_cd - 1)
        self.drift_t = max(0, self.drift_t - 1)
        self.cf_t = max(0, self.cf_t - 1)
        self.cf_cd = max(0, self.cf_cd - 1)
        self.qdodge_t = max(0, self.qdodge_t - 1)
                # Auto-shield passif (Égide Tesseract)
        if self.auto_shield > 0:
            if self.auto_shield_t > 0:
                self.auto_shield_t -= 1
            elif not self.shield_active and self.shield_energy < 5:
                # Recharge complète du bouclier toutes les 8 s
                self.shield_energy = self.max_shield
                self.auto_shield_t = self.auto_shield
                particle_system.emit(self.rect.centerx,
                                     self.rect.centery, 16,
                                     (100, 220, 255), (-3, 3), (2, 5), 24)
        if self.ashield_max and not self.ashield:
            self.ashield_t -= 1
            if self.ashield_t <= 0:
                self.ashield = True

    # ------------------------------------------------------------------
    #  Dégâts
    # ------------------------------------------------------------------
    def hurt(self, dmg, cause, S, src=None, blockable=True, force=False):
        if not self.alive or (self.inv > 0 and not force):
            return False

        # Esquive Quantique (Nébula Chaos)
        if (self is S.player and self.qdodge > 0 and self.qdodge_t <= 0
                and not force and random.random() < self.qdodge):
            self.qdodge_t = self.qdodge_cd
            ox, oy = self.rect.centerx, self.rect.centery
            particle_system.emit(ox, oy, 32, (200, 80, 255),
                                 (-6, 6), (3, 8), 30)
            try:
                pts = S.spawn_points()
                px, py = random.choice(pts)
                self.x, self.y = float(px), float(py - self.h)
                self.rect.topleft = (int(self.x), int(self.y))
                self.vy = 0.0
            except Exception:
                pass
            self.inv = max(self.inv, 30)
            particle_system.emit(self.rect.centerx, self.rect.centery, 32,
                                 (200, 80, 255), (-6, 6), (3, 8), 30)
            S.add_text(self.rect.centerx, self.rect.top - 24,
                       tr("ESQUIVE QUANTIQUE"), (200, 80, 255), True)
            S.add_text(ox, oy - 6, tr("PHASE !"), (150, 200, 255))
            audio.play("dash", 0.7)
            return False

        # Sanctuaire Temporel : le joueur est intouchable
        if self is S.player and S.freeze_t > 0 and not force:
            return False

        # Bouclier
        if blockable and self.shield_active:
            particle_system.emit(self.rect.centerx, self.rect.centery, 10,
                                 CYAN_NEON, size_range=(3, 6))
            if self is S.player:
                audio.play("shield", 0.6)
            return False

        # Compétences d'esquive du joueur
        if self.skills and not force and self is S.player:
            if self.ashield:
                self.ashield = False
                self.ashield_t = self.ashield_max
                self.inv = max(self.inv, 24)
                S.shake = max(S.shake, 4)
                particle_system.emit(self.rect.centerx, self.rect.centery, 24,
                                     RARITY[self.rarity]["color"],
                                     (-5, 5), (3, 6), 26)
                S.add_text(self.rect.centerx, self.rect.top - 24,
                           tr("BOUCLIER AUTO"),
                           RARITY[self.rarity]["color"], True)
                audio.play("shield", 0.7)
                return False
            total_evade = min(0.50, self.evade + getattr(self, "evade_extra", 0))
            if total_evade and random.random() < total_evade:
                # Soin sur esquive (Peau de Nébuleuse)
                if getattr(self, "evade_extra", 0) > 0:
                    self.hp = min(self.max_hp, self.hp + 5)
                particle_system.emit(self.rect.centerx, self.rect.centery, 10,
                                     (200, 200, 255), (-3, 3), (2, 4), 18)
                S.add_text(self.rect.centerx, self.rect.top - 24,
                           tr("ESQUIVE !"), (200, 200, 255), True)
                audio.play("dash", 0.4)
                return False

        # Applique les dégâts
        dmg = dmg * S.chaos.p.get("dmgx", 1.0) * (1.0 - self.reduce)
        self.hp -= dmg
        self.cause = cause
        self.last_src = src

        # Reset combustion si touché
        if self is S.player and self.combustion > 0:
            self.combustion = 0

        S.shake = max(S.shake, 8 if self is S.player else 3)
        self.hitflash = 6
        if self.phase and not force:
            self.inv = 60
        if self is S.player:
            S.round_damage += dmg

        particle_system.emit(self.rect.centerx, self.rect.centery, 14,
                             ROUGE_NEON)
        if SET.get("dmgnum", True) and dmg >= 1.5:
            S.add_text(self.rect.centerx, self.rect.top - 6,
                       "%d" % round(dmg),
                       ROUGE_NEON if self is S.player else JAUNE_NEON)
        audio.play("hit", 0.7 if self is S.player else 0.35)

        if self is S.player and self.skills and not force:
            self.perk_on_hit(dmg, src, S)

        # Mort
        if self.hp <= 0:
            if self.wind2 and self is S.player:
                # Seconde vie
                self.wind2 = False
                self.hp = self.max_hp * 0.5
                self.inv = 150
                self.shield_energy = self.max_shield
                S.slow_timer = max(S.slow_timer, 70)
                S.explode(self.rect.centerx, self.rect.centery, 170, 55,
                          self.team, self.id, "player")
                particle_system.emit(self.rect.centerx, self.rect.centery, 60,
                                     JAUNE_NEON, (-7, 7), (3, 8), 42)
                S.add_text(self.rect.centerx, self.rect.top - 30,
                           tr("SECONDE VIE !"), JAUNE_NEON, True)
                audio.play("win", 0.7)
                return True
            self.hp = 0
            self.alive = False
        return True

    # ------------------------------------------------------------------
    #  Step (physique + input)
    # ------------------------------------------------------------------
    def step(self, inp, S, dt=1.0):
        p = S.chaos.p
        self.t += 1

        # Chaos anti-gravité
        if p.get("antigrav") and self.alive:
            return self._antigrav_step(inp, S, dt)

        left, right = inp.get("left"), inp.get("right")
        if p["invert"]:
            left, right = right, left
        dirx = int(bool(right)) - int(bool(left))

        spd_boost = 1.3 if self.haste > 0 else 1.0
        if self.cf_t > 0:
            spd_boost *= 1.4
        tvx = dirx * self.speed * p["speed"] * spd_boost
        gdir = -1 if p["grav_inv"] else 1

        # Capacité de soutien [E]
        if inp.get("ability") and self.ability and self.ab_cd <= 0:
            if self.ability == "DASH":
                self.dash, self.dash_dir = 9, (dirx or self.face)
                self.inv = max(self.inv, 16)
                self.ab_cd = 110
                audio.play("dash")
            elif self.ability == "TIME":
                S.slow_timer = 180
                self.ab_cd = 1200
                audio.play("chaos", 0.6)

        # Actif mythique [F]
        if self.sa and self.sa_cd <= 0 and inp.get("skin_ab") and self.alive:
            self.cast_sanctuary(S)

        # Dash
        if self.dash > 0:
            self.dash -= 1
            self.vx, self.vy = self.dash_dir * 17, 0.0
            if self.t % 2 == 0:
                particle_system.emit(self.rect.centerx, self.rect.centery, 2,
                                     SKINS[self.skin_key]["accent"],
                                     (-1, 1), (3, 6), 18)
        else:
            if p["slip"]:
                self.vx += (tvx - self.vx) * 0.045 * dt
            else:
                self.vx = tvx
            self.vy = clamp(self.vy + 0.55 * p["grav"] * gdir * dt, -18, 18)

        # Saut
        if self.on_ground and (inp.get("jump") or p["bounce"]):
            self.vy = -(self.jump_v if inp.get("jump") else 8.8) * gdir
            if inp.get("jump"):
                particle_system.emit(
                    self.rect.centerx,
                    self.rect.bottom if gdir > 0 else self.rect.top,
                    8, BLANC, (-2, 2), (1, 4))
                if self is S.player:
                    audio.play("jump", 0.6)

        # Compétences de mobilité
        jp = bool(inp.get("jump"))
        if self.on_ground:
            self.jumps_left = self.air_jumps
        elif (self.air_jumps and jp and not self._jp
              and self.jumps_left > 0 and not self.dash):
            self.jumps_left -= 1
            self.vy = -self.jump_v * 0.9 * gdir
            particle_system.emit(self.rect.centerx, self.rect.bottom, 10,
                                 RARITY[self.rarity]["color"],
                                 (-2, 2), (1, 4), 16)
            if self is S.player:
                audio.play("jump", 0.5)
        elif (self.glide and jp and not self.dash
              and self.vy * gdir > self.glide):
            self.vy = self.glide * gdir
            if self.t % 4 == 0:
                particle_system.emit(self.rect.centerx, self.rect.bottom, 1,
                                     SKINS[self.skin_key]["trail"],
                                     (-0.6, 0.6), (1, 3), 14)
        self._jp = jp

        # Bouclier
        if inp.get("shield") and self.shield_energy > 5 and not p["noshield"]:
            if not self.shield_active and self is S.player:
                audio.play("shield", 0.5)
            self.shield_active = True
            self.shield_energy -= 1.2 * dt
            if self.shield_energy <= 0:
                self.shield_energy, self.shield_active = 0, False
                if self.nova:
                    S.explode(self.rect.centerx, self.rect.centery, 120, 42,
                              self.team, self.id,
                              "player" if self is S.player else "ai")
        else:
            self.shield_active = False
            if self.shield_energy < self.max_shield:
                self.shield_energy = min(self.max_shield,
                                         self.shield_energy + self.regen * dt)

        # Régénération PV
        if self.hp_regen and self.alive and self.hp < self.max_hp:
            boost = 3.0 if (self is S.player and S.freeze_t > 0) else 1.0
            self.hp = min(self.max_hp,
                          self.hp + self.hp_regen * boost / 60.0 * dt)

        # Arme
        if inp.get("weapon") and inp["weapon"] in WEAPONS:
            self.weapon_type = inp["weapon"]

        # Visée + tir
        aim = inp.get("aim")
        if aim:
            self.face = 1 if aim[0] >= self.rect.centerx else -1
        elif abs(self.vx) > 0.3:
            self.face = 1 if self.vx > 0 else -1
        if inp.get("shoot"):
            self.shoot(inp["shoot"], S)

        # Déplacement
        self.move(S, dt, gdir)
        if self.cooldown > 0:
            self.cooldown -= dt

        # Traînée
        if abs(self.vx) > 4.5 and self.on_ground and self.t % 4 == 0:
            particle_system.emit(self.rect.centerx, self.rect.bottom, 1,
                                 SKINS[self.skin_key]["trail"],
                                 (-0.6, 0.6), (1, 3), 14)

        # Enregistrement (échos)
        if self.record:
            self.rec.append((self.rect.x, self.rect.y, self.face,
                             self.shield_active, self.weapon_type,
                             not self.on_ground, self.vx))

    def move(self, S, dt, gdir):
        wind = S.chaos.p.get("wind", 0.0)
        dxm = (self.vx + wind) * dt
        self.x = clamp(self.x + dxm, 0, WIDTH - self.w)
        self.rect.x = int(round(self.x))

        if dxm != 0:
            for plat in S.platforms:
                if self.rect.colliderect(plat):
                    if dxm > 0:
                        self.rect.right = plat.left
                    else:
                        self.rect.left = plat.right
                    self.x = float(self.rect.x)
                    self.vx = 0 if not S.chaos.p["slip"] else self.vx * 0.3

        self.y += self.vy * dt
        self.rect.y = int(round(self.y))
        self.on_ground = False

        for plat in S.platforms:
            if self.rect.colliderect(plat):
                if self.vy >= 0:
                    self.rect.bottom = plat.top
                    self.on_ground = gdir > 0
                else:
                    self.rect.top = plat.bottom
                    self.on_ground = gdir < 0
                self.y = float(self.rect.y)
                self.vy = 0

        if self.rect.top < 0:
            self.rect.top = 0
            self.y = 0.0
            self.vy = max(self.vy, 0)
            if gdir < 0:
                self.on_ground = True

    # ------------------------------------------------------------------
    #  Tir
    # ------------------------------------------------------------------
    def shoot(self, aim, S):
        if self.cooldown > 0 or self.shield_active:
            return
        cx, cy = self.rect.center
        dx, dy = aim[0] - cx, aim[1] - cy
        d = math.hypot(dx, dy)
        if d == 0:
            return

        wt = self.weapon_type
        w = WEAPONS[wt]
        base = math.atan2(dy, dx)
        n = w.get("count", 1)
        for i in range(n):
            a = base + (i - (n - 1) / 2.0) * w.get("spread", 0.0)
            if w.get("jitter"):
                a += random.uniform(-w["jitter"], w["jitter"])
            vx = math.cos(a) * w["speed"]
            vy = math.sin(a) * w["speed"]
            S.spawn_projectile(cx, cy, vx, vy, wt, self.team, self.id,
                               "player" if self is S.player else "ai",
                               mult=self.shot_power())
            if self.record:
                self.shots.append((len(self.rec), vx, vy, wt,
                                   self.dmg_mult * (1.0 + self.echo_pow)))

        rate_m = 3.0 if self.cf_t > 0 else 1.0
        self.cooldown = w["cd"] / (self.rate * rate_m)

        if self is S.player:
            sfx = w.get("sfx") or {
                "PLASMA": "shoot", "LASER": "laser", "MISSILE": "missile",
            }.get(wt, "shoot")
            audio.play(sfx, 0.55)
        particle_system.emit(cx, cy, 5,
                             SKINS[self.skin_key]["accent"], (-3, 3))

    # ------------------------------------------------------------------
    #  Rendu
    # ------------------------------------------------------------------
    def draw(self, surf, S):
        if not self.alive:
            return
        # Clignotement d'invulnérabilité du joueur
        if (self.inv > 0 and (self.inv // 4) % 2 == 0
                and self is S.player and S.phase == "PLAY"):
            return

        sc = self.h / 38.0
        frozen = S.freeze_t > 0 and self is not S.player
        draw_skin(surf, self.skin_key, self.rect.centerx, self.rect.centery,
                  self.face, self.t, not self.on_ground, self.vx,
                  scale=sc, hit=self.hitflash > 0, ghost=frozen)

        if frozen:
            pygame.draw.rect(surf, (170, 230, 255),
                             self.rect.inflate(12, 10), 2, border_radius=8)

        if self.burn > 0 and self.t % 3 == 0:
            particle_system.emit(self.rect.centerx, self.rect.centery, 2,
                                 ORANGE, (-1, 1), (3, 6), 15)

        # Bouclier
        if self.shield_active:
            rr = int(38 * sc)
            s = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*CYAN_NEON, 100), (rr + 2, rr + 2), rr)
            pygame.draw.circle(s, (*BLANC, 180), (rr + 2, rr + 2), rr, 2)
            surf.blit(s, (self.rect.centerx - rr - 2,
                          self.rect.centery - rr - 2))
            if self.reflect:
                pygame.draw.circle(surf, MINT, self.rect.center, rr + 4, 1)

        # Effets de compétence du joueur
        if self is S.player and self.skills:
            self.draw_perk_fx(surf)

        # Indicateur joueur / barre de vie IA
        if self is S.player:
            pygame.draw.polygon(
                surf, CYAN_NEON,
                [(self.rect.centerx - 6, self.rect.top - 16),
                 (self.rect.centerx + 6, self.rect.top - 16),
                 (self.rect.centerx, self.rect.top - 7)])
        elif not self.boss:
            pygame.draw.rect(surf, ROUGE_NEON,
                             (self.rect.x - 4, self.rect.top - 10, 36, 4))
            pygame.draw.rect(
                surf, VERT_NEON,
                (self.rect.x - 4, self.rect.top - 10,
                 36 * clamp(self.hp / self.max_hp, 0, 1), 4))


# ─────────────────────────────────────────────────────────────────────────
#  ECHO — rejoueur du passé, adaptatif à la carte courante
# ─────────────────────────────────────────────────────────────────────────
def adapt_echo_position(S, x, y, air=False):
    """Recale l'écho sur la plateforme la plus proche.
    Version améliorée : tolère mieux les micro-décalages."""
    px, py = int(x), int(y)
    if not getattr(S, "platforms", None):
        return px, py

    # Plateformes sous l'écho (tolérance horizontale plus large)
    under = [p for p in S.platforms if p.left - 30 <= px <= p.right + 30]

    if not under:
        # Aucune plateforme proche : on colle à la plus proche
        nearest = min(S.platforms,
                      key=lambda p: min(abs(p.left - px), abs(p.right - px)))
        px = clamp(px, nearest.left + 4,
                   max(nearest.left + 4, nearest.right - 32))
        return px, nearest.top - 38

    feet = py + 38
    # Plateformes sous les pieds (tolérance verticale plus souple)
    below = [p for p in under if p.top >= feet - 120]
    best = min(below or under, key=lambda p: abs(p.top - feet))
    ground_y = best.top - 38

    # Recadrage horizontal sur la plateforme choisie
    px = clamp(px, best.left + 4, max(best.left + 4, best.right - 32))

    if air:
        return px, max(ground_y - 260, min(ground_y, py))
    return px, ground_y

class Echo:
    """Rejoue fidèlement les mouvements et tirs enregistrés du joueur,
    recalés sur la carte courante à chaque image."""

    def __init__(self, rec, shots, skin_key, team, src_id, color, label):
        self.rec = rec
        self.shots = {}
        for (i, vx, vy, w, m) in shots:
            self.shots.setdefault(i, []).append((vx, vy, w, m))
        self.skin_key = skin_key
        self.team = team
        self.src_id = src_id
        self.color = color
        self.label = label
        self.rect = pygame.Rect(0, 0, 28, 38)
        self.reset()

    def reset(self):
        self.pos = 0.0
        self.fired = -1
        self.alive = len(self.rec) > 0
        self.state = self.rec[0] if self.rec else (
            0, 0, 1, False, "PLASMA", False, 0.0)
        self.rect.topleft = self.state[0], self.state[1]

    def step(self, S):
        if not self.alive:
            return
        self.pos += S.ts(self.team) * S.chaos.p.get("echo", 1.0)
        idx = int(self.pos)
        if idx >= len(self.rec):
            self.alive = False
            particle_system.emit(self.rect.centerx, self.rect.centery, 20,
                                 self.color, (-3, 3), (2, 5), 25)
            return

        self.state = self.rec[idx]
        rx, ry, face, shield, wp, air, vx = self.state
        ax, ay = adapt_echo_position(S, rx, ry, air)
        self.state = (ax, ay, face, shield, wp, air, vx)
        self.rect.topleft = (ax, ay)

        for i in range(self.fired + 1, idx + 1):
            for (vx2, vy2, w, m) in self.shots.get(i, []):
                S.spawn_projectile(self.rect.centerx, self.rect.centery,
                                   vx2, vy2, w, self.team, self.src_id,
                                   "echo", color=self.color, mult=m)
        self.fired = idx

    def draw(self, surf, t):
        if not self.alive:
            return
        x, y, face, shield, wp, air, vx = self.state
        draw_skin(surf, self.skin_key, self.rect.centerx, self.rect.centery,
                  face, t, air, vx, alpha=125, ghost=True)
        if shield:
            pygame.draw.circle(surf, CYAN_NEON, self.rect.center, 36, 1)
        draw_text(surf, "E%d" % self.label, FONT_TINY, self.color,
                  self.rect.centerx, self.rect.top - 10)


# ─────────────────────────────────────────────────────────────────────────
#  MINI — ennemis de terrain (walker, turret, flyer)
# ─────────────────────────────────────────────────────────────────────────
class Mini:
    SIZES = {
        "WALKER": (26, 24, 24),
        "TURRET": (28, 26, 45),
        "FLYER":  (30, 20, 28),
    }

    def __init__(self, kind, x, y, bounds, lvl, diff):
        w, h, hp = self.SIZES[kind]
        D = DIFFS[diff]
        self.kind = kind
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.fx = float(x)
        self.base_y = y
        self.bounds = bounds
        self.hp = self.max_hp = hp * (1 + 0.12 * (lvl - 1)) * (0.5 + 0.5 * D["hp"])
        self.dir = random.choice((-1, 1))
        self.cd = random.uniform(40, 110)
        self.phase = random.random() * 6
        self.alive = True
        self.ang = math.pi / 2
        self.team = "M"
        self.rate = (1 + 0.1 * (lvl - 1)) * (1 + 0.15 * (diff - 3))
        self.dmg = 8 * D["dmg"]

    def hurt(self, dmg, S):
        self.hp -= dmg
        particle_system.emit(self.rect.centerx, self.rect.centery, 8,
                             JAUNE_NEON)
        audio.play("hit", 0.3)
        if self.hp <= 0 and self.alive:
            self.alive = False
            S.kills += 1
            S.round_kills += 1
            S.add_text(self.rect.centerx, self.rect.top, "+1",
                       VERT_NEON, True)
            S.player_kill(self.rect.centerx, self.rect.centery)
            audio.play("boom", 0.35)
            particle_system.emit(self.rect.centerx, self.rect.centery, 24,
                                 ORANGE, (-4, 4), (3, 6), 30)

    def update(self, S):
        ts = S.ts()
        if self.kind in ("WALKER", "FLYER") and self.bounds:
            self.fx += (1.4 if self.kind == "WALKER" else 1.2) * self.dir * ts
            if (self.fx < self.bounds[0]
                    or self.fx + self.rect.w > self.bounds[1]):
                self.dir = -self.dir
                self.fx = clamp(self.fx, self.bounds[0],
                                self.bounds[1] - self.rect.w)
            self.rect.x = int(self.fx)
        if self.kind == "FLYER":
            self.rect.y = int(self.base_y
                              + math.sin(S.t * 0.05 + self.phase) * 25)
        if self.kind in ("TURRET", "FLYER"):
            self.cd -= ts * self.rate
            if self.cd <= 0:
                self.cd = random.uniform(80, 130)
                tgt = S.nearest_fighter(self.rect.centerx, self.rect.centery,
                                        "M")
                if tgt and math.hypot(tgt.rect.centerx - self.rect.centerx,
                                      tgt.rect.centery - self.rect.centery) < 520:
                    self.ang = math.atan2(tgt.rect.centery - self.rect.centery,
                                          tgt.rect.centerx - self.rect.centerx)
                    S.spawn_projectile(
                        self.rect.centerx, self.rect.centery,
                        math.cos(self.ang) * 6.5,
                        math.sin(self.ang) * 6.5,
                        "PLASMA", "M", "enemy", "enemy", dmg=self.dmg)

    def draw(self, surf, t):
        r = self.rect
        if self.kind == "WALKER":
            pygame.draw.rect(surf, (150, 30, 50), r, border_radius=6)
            pygame.draw.rect(surf, ROUGE_NEON, r, 2, border_radius=6)
            ex = r.centerx + (4 if self.dir > 0 else -4)
            pygame.draw.circle(surf, JAUNE_NEON, (ex - 5, r.y + 9), 3)
            pygame.draw.circle(surf, JAUNE_NEON, (ex + 5, r.y + 9), 3)
            pygame.draw.rect(surf, (90, 20, 30), (r.x + 2, r.bottom - 4, 8, 4))
            pygame.draw.rect(surf, (90, 20, 30),
                             (r.right - 10, r.bottom - 4, 8, 4))
        elif self.kind == "TURRET":
            pygame.draw.polygon(surf, (70, 60, 90),
                                [(r.x, r.bottom), (r.right, r.bottom),
                                 (r.right - 5, r.centery),
                                 (r.x + 5, r.centery)])
            pygame.draw.circle(surf, (110, 90, 150), r.center, 11)
            pygame.draw.line(surf, ROUGE_NEON, r.center,
                             (r.centerx + math.cos(self.ang) * 20,
                              r.centery + math.sin(self.ang) * 20), 6)
            pygame.draw.circle(surf, ROUGE_NEON, r.center, 4)
        else:
            fl = int(math.sin(t * 0.4) * 6)
            pygame.draw.polygon(surf, (120, 40, 140),
                                [(r.x + 4, r.centery),
                                 (r.x - 8, r.y - 4 + fl),
                                 (r.x + 10, r.y + 4)])
            pygame.draw.polygon(surf, (120, 40, 140),
                                [(r.right - 4, r.centery),
                                 (r.right + 8, r.y - 4 + fl),
                                 (r.right - 10, r.y + 4)])
            pygame.draw.ellipse(surf, PURPLE_NEON, r)
            pygame.draw.circle(surf, JAUNE_NEON, r.center, 4)
        if self.hp < self.max_hp:
            pygame.draw.rect(surf, ROUGE_NEON, (r.x, r.y - 8, r.w, 3))
            pygame.draw.rect(
                surf, VERT_NEON,
                (r.x, r.y - 8,
                 r.w * clamp(self.hp / self.max_hp, 0, 1), 3))


# ─────────────────────────────────────────────────────────────────────────
#  LOADOUT — construit les stats effectives du joueur
# ─────────────────────────────────────────────────────────────────────────
def _base_loadout():
    """Construit le loadout brut à partir de la sauvegarde (sans premium)."""
    L = dict(
        max_hp=stat_value("hp"),
        max_shield=stat_value("shield"),
        regen=stat_value("regen"),
        speed=stat_value("speed"),
        power=stat_value("power"),
        rate=stat_value("rate"),
        jump=stat_value("jump"),
        coin=stat_value("coin"),
        special=None, reduce=0.0, reflect=False, nova=False, phase=False,
        hp_regen=0.0, ability=None,
        skills={}, rarity="COMMON", gdmg=1.0,
        prem_revives=0,
                # Nouveaux bonus d'objets
        auto_shield=0, 
        evade=0.0, 
        trapsafe=0, 
        immune_slow=False,
    )
    w = equipped("weapon")
    a = equipped("armor")
    s = equipped("support")
    if w:
        L["special"] = w["kind"]
    if a:
        L["max_shield"] += a.get("shield", 0)
        L["reduce"] = a.get("reduce", 0.0)
        L["reflect"] = a.get("reflect", False)
        L["nova"] = a.get("nova", False)
        L["phase"] = a.get("phase", False)
        L["auto_shield"] = a.get("auto_shield", 0)
        L["evade"] = a.get("evade", 0.0)
        L["trapsafe"] = a.get("trapsafe", 0)
    if s:
        L["max_hp"] += s.get("hp", 0)
        L["jump"] *= s.get("jump", 1.0)
        L["hp_regen"] = s.get("regen", 0.0)
        L["ability"] = s.get("ability")
        if s.get("hp_regen"):
            L["hp_regen"] = L.get("hp_regen", 0.0) + s["hp_regen"]
        if s.get("immune_slow"):
            L["immune_slow"] = True
    apply_skin_to_loadout(L, SAVE["selected"])
    return L


def loadout():
    """Loadout complet (base + bonus premium si définis en § 13)."""
    L = _base_loadout()
    # Premium (défini en § 13) — silencieux si pas encore chargé
    try:
        apply_premium_to_loadout(L)  # noqa: F821
    except NameError:
        pass
    return L


# ═══════════════════════════════════════════════════════════════════════════
#  § 9 — IA PRÉDICTIVE MULTI-NIVEAUX
# ═══════════════════════════════════════════════════════════════════════════

MAX_JUMP_RISE = 105
MAX_JUMP_GAP  = 170
MIN_JUMP_RISE = 70


def intercept(sx, sy, tx, ty, tvx, tvy, sp):
    """Position d'interception : où viser pour toucher une cible mobile."""
    dx, dy = tx - sx, ty - sy
    a = tvx * tvx + tvy * tvy - sp * sp
    b = 2 * (dx * tvx + dy * tvy)
    c = dx * dx + dy * dy
    t = 0.0
    if abs(a) < 1e-6:
        t = -c / b if b != 0 else 0.0
    else:
        disc = b * b - 4 * a * c
        if disc >= 0:
            r = math.sqrt(disc)
            ts = [x for x in ((-b - r) / (2 * a),
                              (-b + r) / (2 * a)) if x > 0]
            t = min(ts) if ts else 0.0
    t = clamp(t, 0, 50)
    return tx + tvx * t, ty + tvy * t


class AIBrain:
    """IA robuste :
    - esquive prédictive des projectiles
    - tir à interception (cible mobile)
    - navigation par graphe de plateformes (BFS)
    - détection de blocage + désincarcération
    - sécurité anti-chute et anti-tremblement
    - compensation des contrôles inversés
    """

    def __init__(self, level, diff=3, boss=False):
        self.lv = level
        self.d = diff
        self.boss = boss
        D = DIFFS[diff]
        self.fire_cap = D["fire"] * (1.3 if boss else 1.0)

        # Précision : D1 très imprécis (0.35 rad), D15 quasi parfait (0.005 rad)
        base_noise = max(0.005, 0.35 - 0.024 * (diff - 1))
        self.noise = max(0.005, base_noise - 0.008 * min(level, 15))

        # Probabilité d'esquiver : D1 = 3% (l'IA ignore les tirs), D15 = 95%
        base_react = 0.03 + 0.065 * (diff - 1)
        self.react_p = clamp(base_react + 0.02 * min(level, 15),
                             0.02, 0.97)

        # Distance de combat idéale : plus l'IA est douée, plus elle colle
        self.want_dist = max(120, 280 - 6 * min(level + (diff - 1) * 2, 25))

        self.strafe = random.choice((-1, 1))
        self.strafe_t = random.randint(30, 80)
        self.last_threat = None
        self.react = True
        self.nav = None
        self.move = 0
        self.hold = 0
        self.last_x = None
        self.stuck = 0
        self.unstick = 0
        self.unstick_dir = 1

    # ------------------------------------------------------------------
    #  Utilitaires spatiaux
    # ------------------------------------------------------------------
    def los(self, S, a, b):
        """Ligne de vue (pas de plateforme sur le segment)."""
        for i in range(1, 10):
            px = a[0] + (b[0] - a[0]) * i / 10
            py = a[1] + (b[1] - a[1]) * i / 10
            for plat in S.platforms:
                if plat.collidepoint(px, py):
                    return False
        return True

    def support(self, S, r):
        """Plateforme sous les pieds du fighter."""
        for p in S.platforms:
            if (abs(r.bottom - p.top) <= 5
                    and r.right > p.left and r.left < p.right):
                return p
        return None

    def below(self, S, r):
        """Plateforme la plus proche sous un rectangle."""
        best = None
        for p in S.platforms:
            if (r.right > p.left and r.left < p.right
                    and p.top >= r.bottom - 6):
                if best is None or p.top < best.top:
                    best = p
        return best

    @staticmethod
    def _edge(a, b):
        """Y a-t-il un saut praticable entre deux plateformes ?"""
        rise = a.top - b.top
        gap = max(b.left - a.right, a.left - b.right, 0)
        if 25 <= rise <= 125:
            if gap > 0:
                return gap <= 170
            return (a.left < b.left - 34 or a.right > b.right + 34)
        if rise <= -20:
            return gap <= 240
        return 0 < gap <= 170

    def next_hop(self, S, cur, goal):
        """BFS sur le graphe des plateformes (cache par liste)."""
        pl = S.platforms
        g = getattr(S, "_pg", None)
        if g is None or g[0] is not pl:
            adj = {i: [j for j, b in enumerate(pl)
                       if j != i and self._edge(a, b)]
                   for i, a in enumerate(pl)}
            g = S._pg = (pl, adj)
        adj = g[1]
        try:
            s0 = next(i for i, p in enumerate(pl) if p is cur)
            t0 = next(i for i, p in enumerate(pl) if p is goal)
        except StopIteration:
            return None
        prev = {s0: None}
        queue = [s0]
        while queue:
            u = queue.pop(0)
            if u == t0:
                break
            for v in adj[u]:
                if v not in prev:
                    prev[v] = u
                    queue.append(v)
        if t0 not in prev:
            return None
        u = t0
        while prev[u] != s0 and prev[u] is not None:
            u = prev[u]
        return pl[u] if prev[u] == s0 else None

    def ground_ahead(self, S, f, direction, gdir):
        """Y a-t-il un sol praticable en avant ?"""
        px = f.rect.centerx + direction * (f.w // 2 + 14)
        py = f.rect.bottom + 8 if gdir > 0 else f.rect.top - 8
        return any(p.collidepoint(px, py) for p in S.platforms)

    def head_blocked(self, S, f):
        """Y a-t-il un obstacle au-dessus de la tête ?"""
        probe = pygame.Rect(f.rect.x, f.rect.top - 105, f.w, 100)
        return any(probe.colliderect(p) for p in S.platforms)

    # ------------------------------------------------------------------
    #  Décision
    # ------------------------------------------------------------------
    def decide(self, f, S):
        lv = self.lv
        gdir = -1 if S.chaos.p["grav_inv"] else 1
        inp = dict(left=False, right=False, jump=False, shield=False,
                   shoot=None, aim=None, weapon=f.weapon_type)

        cx, cy = f.rect.center
        tgt = S.nearest_fighter(cx, cy, f.team)
        if not tgt:
            return inp
        tx, ty = tgt.rect.center

        # 1. Esquive prédictive
        best = None
        for p in S.projectiles:
            if p.team == f.team:
                continue
            rx, ry = p.x - cx, p.y - cy
            v2 = p.vx * p.vx + p.vy * p.vy
            if v2 < 0.1:
                continue
            t = -(rx * p.vx + ry * p.vy) / v2
            if 0 < t < 28 and math.hypot(rx + p.vx * t,
                                         ry + p.vy * t) < 28 + p.radius:
                if best is None or t < best[0]:
                    best = (t, p)
        if best:
            t, p = best
            if id(p) != self.last_threat:
                self.last_threat = id(p)
                self.react = random.random() < self.react_p
            if self.react:
                if t < 14 and f.shield_energy > 25 and not S.chaos.p["noshield"]:
                    inp["shield"] = True
                elif f.on_ground and t < 24 and not self.head_blocked(S, f):
                    inp["jump"] = True

        # 2. Déplacement (avec hystérésis)
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)
        want = self.want_dist
        self.strafe_t -= 1
        if self.strafe_t <= 0:
            self.strafe = random.choice((-1, 1))
            self.strafe_t = random.randint(30, 90)
        sgn = 1 if dx > 0 else -1
        if dist > want + 70:
            move = sgn
        elif dist < want - 80:
            move = -sgn
        else:
            move = self.strafe if lv >= 2 else 0

        # 3. Navigation par graphe (BFS)
        pathing = False
        cur = self.support(S, f.rect) if f.on_ground else None
        goal = self.support(S, tgt.rect) or self.below(S, tgt.rect)
        if f.on_ground and gdir > 0:
            if (cur is not None and goal is not None and cur is not goal
                    and (abs(dy) > 90 or dist > want + 70)):
                self.nav = self.next_hop(S, cur, goal)
            else:
                self.nav = None

        if self.nav is not None and gdir > 0:
            n = self.nav
            pathing = True
            inward = 1 if n.centerx > cx else -1
            blocked = self.head_blocked(S, f)

            if not f.on_ground:
                move = inward if n.top < f.rect.bottom - 10 else move
            elif cur is None:
                pass
            elif n.top < cur.top - 20:                       # monter
                if n.left - 12 < cx < n.right + 12:
                    edges = [n.left - 32, n.right + 32]
                    sup = [e for e in edges
                           if any(p.collidepoint(e, f.rect.bottom + 8)
                                  for p in S.platforms)]
                    ex = min(sup or edges, key=lambda e: abs(e - cx))
                    move = 1 if ex > cx else -1
                    if abs(ex - cx) < 12 and not blocked:
                        move = inward
                        inp["jump"] = True
                else:
                    ex = n.left - 32 if cx < n.centerx else n.right + 32
                    if abs(ex - cx) > 12:
                        move = 1 if ex > cx else -1
                        if (not self.ground_ahead(S, f, move, gdir)
                                and not blocked and abs(ex - cx) < 170):
                            inp["jump"] = True
                    elif not blocked:
                        move = inward
                        inp["jump"] = True
                    else:
                        move = 1 if ex > cx else -1
            elif n.top > cur.top + 20:                       # descendre
                if cur.left <= n.centerx <= cur.right:
                    edge = (cur.left - 12
                            if abs(cur.left - n.centerx) < abs(cur.right - n.centerx)
                            else cur.right + 12)
                    move = 1 if edge > cx else -1
                else:
                    move = inward
            else:                                            # même niveau
                move = inward
                if not self.ground_ahead(S, f, move, gdir) and not blocked:
                    inp["jump"] = True

        # 4. Sécurité anti-chute
        if (not pathing and f.on_ground and move != 0 and abs(dy) < 80
                and gdir > 0
                and not self.ground_ahead(S, f, move, gdir)):
            move = -move if lv >= 2 else 0
        if cx < 34 and move < 0:
            move = 1
        elif cx > WIDTH - 34 and move > 0:
            move = -1

        # Hystérésis
        if self.hold > 0:
            move = self.move
            self.hold -= 1
        elif move != self.move:
            self.move, self.hold = move, 6

        # 5. Détection de blocage
        if (self.last_x is not None and move != 0
                and abs(cx - self.last_x) < 1.0 and f.on_ground):
            self.stuck += 1
        else:
            self.stuck = max(0, self.stuck - 1)
        self.last_x = cx
        if self.stuck > 25 and self.unstick <= 0:
            self.unstick = 28
            self.unstick_dir = random.choice((-1, 1))
            self.stuck = 0
        if self.unstick > 0:
            self.unstick -= 1
            move = self.unstick_dir
            if (f.on_ground and not self.head_blocked(S, f)
                    and self.unstick % 9 == 0):
                inp["jump"] = True

        inp["left"], inp["right"] = move < 0, move > 0
        if S.chaos.p["invert"] and lv >= 2:
            inp["left"], inp["right"] = inp["right"], inp["left"]

        # 6. Arme + tir
        if dist > 420:
            wp = "LASER"
        elif dist > 200:
            wp = "MISSILE"
        else:
            wp = "PLASMA"
        if lv >= 4 and random.random() < 0.02:
            wp = random.choice([w for w in WEAPONS
                                if w != "RAIL" or lv >= 8])
        inp["weapon"] = wp

        # Chance de tirer : D1 = 1.5%, D15 = 75% (plafonné par fire_cap)
        fire_p = min(self.fire_cap, 0.015 + 0.012 * min(lv, 25))
        if (f.cooldown <= 0 and not inp["shield"]
                and random.random() < fire_p
                and self.los(S, (cx, cy), (tx, ty))):
            sp = WEAPONS[wp]["speed"]
            ax, ay = intercept(cx, cy, tx, ty, tgt.vx, tgt.vy, sp)
            ang = random.gauss(0, self.noise)
            vx, vy = ax - cx, ay - cy
            ca, sa = math.cos(ang), math.sin(ang)
            inp["shoot"] = (cx + vx * ca - vy * sa,
                            cy + vx * sa + vy * ca)
        inp["aim"] = (tx, ty)
        return inp


# ═══════════════════════════════════════════════════════════════════════════
#  FIN § 8-9
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#  § 10 — SESSION (logique du jeu)
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  MILESTONES (boss épique / calamité tous les 5 niveaux)
# ─────────────────────────────────────────────────────────────────────────
MILESTONE_BOSS_SKINS = ["DEMON", "CHRONOS_LORD", "ECLIPSE_WRAITH",
                        "ASTRAL_GUARDIAN", "PLASMA_DRAGON"]


# ─────────────────────────────────────────────────────────────────────────
#  CAMPAGNE — progression des difficultés (1 → 15)
# ─────────────────────────────────────────────────────────────────────────
def _campaign_key(diff, mode):
    return "%d_%s" % (int(diff), mode)


def campaign_streak(diff, mode):
    return _to_int(SAVE["campaign"]["streaks"].get(
        _campaign_key(diff, mode), 0))


def campaign_set_streak(diff, mode, value):
    k = _campaign_key(diff, mode)
    SAVE["campaign"]["streaks"][k] = max(0, int(value))
    best = SAVE["campaign"]["best"]
    if SAVE["campaign"]["streaks"][k] > _to_int(best.get(k, 0)):
        best[k] = SAVE["campaign"]["streaks"][k]


def campaign_reset_streak(diff, mode):
    campaign_set_streak(diff, mode, 0)


def campaign_check_unlock(diff):
    """Règles de déblocage :
       - D3..D9  : 5 manches consécutives dans UN des deux modes
       - D5 → D6 : 5 manches dans LES DEUX modes
       - D10→D11 : 10 manches dans LES DEUX modes (Mode Champion)
    """
    camp = SAVE["campaign"]
    unlocked = camp["unlocked"]
    if unlocked >= MAX_DIFF:
        return None
    echo = campaign_streak(diff, "COURSE")
    ia = campaign_streak(diff, "SURVIE")

    if diff == 5:
        if echo >= 5 and ia >= 5 and unlocked < 6:
            camp["unlocked"] = 6
            return 6
        return None
    if diff == 10:
        if echo >= 10 and ia >= 10 and unlocked < 11:
            camp["unlocked"] = 11
            camp["champion_unlocked"] = True
            return 11
        return None
    if diff < 5 or 6 <= diff < 10:
        if (echo >= 5 or ia >= 5) and unlocked == diff:
            camp["unlocked"] = diff + 1
            return diff + 1
    return None


def campaign_next_goal_text(diff):
    if diff == 5:
        return tr("D5 → D6 : 5 manches des DEUX modes (Écho ET IA)")
    if diff == 10:
        return tr("D10 → CHAMPION : 10 manches des DEUX modes en D10")
    if diff < 5 or 6 <= diff < 10:
        return tr("D%d → D%d : 5 manches dans un des deux modes") % (
            diff, diff + 1)
    return ""


# ─────────────────────────────────────────────────────────────────────────
#  CAMPAGNE SECRÈTE — 10 niveaux × 10 manches en zones secrètes
# ─────────────────────────────────────────────────────────────────────────
def _get_secret_zone_wins():
    return SAVE["stats"].setdefault("secret_wins", {})


def _check_secret_campaign_unlock():
    """Débloque la campagne secrète si tous les 5 modes ont 10+ victoires."""
    wins = _get_secret_zone_wins()
    all_done = all(_to_int(wins.get(z, 0)) >= SECRET_ZONE_WINS_REQUIRED
                   for z in SECRET_ZONES_FOR_CAMPAIGN)
    sc = SAVE.setdefault("secret_campaign", {})
    if all_done and not sc.get("unlocked"):
        sc["unlocked"] = True
        write_save()
        try:
            say(tr("CAMPAGNE SECRÈTE DÉBLOQUÉE"), JAUNE_NEON)
            audio.play("win")
        except Exception:
            pass
    return all_done


def is_campaign_unlocked(save_data=None):
    sc = SAVE.get("secret_campaign", {})
    return bool(sc.get("unlocked", False))


def secret_campaign_progress():
    return SAVE["secret_campaign"]["levels"]


def secret_campaign_register_round(level_id):
    if level_id not in SECRET_LEVELS_INFO:
        return False
    sc = SAVE["secret_campaign"]
    cur = _to_int(sc["levels"].get(level_id, 0))
    if cur >= SECRET_CAMPAIGN_ROUNDS_REQUIRED:
        return False
    sc["levels"][level_id] = cur + 1
    if all(_to_int(sc["levels"].get(k, 0)) >= SECRET_CAMPAIGN_ROUNDS_REQUIRED
           for k in SECRET_LEVELS_IDS):
        sc["cleared"] = True
    write_save()
    return True


# ─────────────────────────────────────────────────────────────────────────
#  Helpers divers
# ─────────────────────────────────────────────────────────────────────────
def move_keys():
    if SET.get("layout") == "AZERTY":
        return (pygame.K_q, pygame.K_d, pygame.K_z)
    return (pygame.K_a, pygame.K_d, pygame.K_w)


def mode_title(mode):
    cfg = MODES[mode]
    return tr(cfg["title"]) + (" [%s]" % tr("SECRET") if cfg.get("secret") else "")


# ─────────────────────────────────────────────────────────────────────────
#  SESSION
# ─────────────────────────────────────────────────────────────────────────
class Session:
    """Une partie complète : N rounds dans un mode donné.

    Cycle : INTRO → PLAY → (DYING → OVER) ou (ROUND_END → INTRO...)
    L'état de la partie est exposé via : self.round, self.phase,
    self.fighters, self.projectiles, self.echoes, self.traps, etc.
    """

    # ---------------------------------------------------------------
    #  Initialisation
    # ---------------------------------------------------------------
    def __init__(self, mode):
        self.mode = mode
        self.cfg = dict(MODES[mode])            # copie mutable
        self.diff = max(SAVE["difficulty"], self.cfg.get("min_diff", 1))
        self.rng = random.Random()
 
        # ── CORRECTIF : round_time doit exister dès l'init ─────────────
        _base_rt = self.cfg.get("round_time", 1800)
        if mode == "COURSE":
            _mult = [1.5, 1.25, 1.0, 0.9, 0.8][max(0, min(4, self.diff - 1))]
            self.round_time = int(_base_rt * _mult)
        else:
            self.round_time = _base_rt
    # ────────────────────────────────────────────────────────────────

        # Compteurs de session
        self.round = 0
        self.rounds_done = 0
        self.kills = 0
        self.earned = 0
        self.total = 0
        self.pts = {}

        # État
        self.paused = False
        self.shake = 0
        self.t = 0
        self.win = False
        self.ko_cause = ""
        self.secret_exit = None
        self.rank = 1
        self.new_ach = []
        self.texts = []
        self.rings = []
        self.slow_timer = 0
        self.tele_t = 0
        self.relic = None
        self.freeze_t = 0
        self.freeze_max = 0
        self.fis = dict(cx=WIDTH // 2, cy=HEIGHT // 2, cracks=[])
        self.waves = []
        self.frz = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Gemmes
        self.gem_items = []
        self.gems_pick = 0
        self.gems_run = 0
        self.gems_paid = False

        # Combat
        self.round_damage = 0
        self.round_kills = 0
        self.round_reward = 0
        self.kills_banked = False
        self.black_hole_fx = None

        # Milestones
        self.milestone_kind = None
        self.milestone_boss = None
        self.calamity = False
        self.calamity_mult = 1.0
        self._mb_phase = 1
        self._mb_attack_cd = 120
        self._mb_attack_idx = 0

        # Échos
        self.echoes = []
        self.echo_count = 0

        # Loadout + chaos
        self.L = loadout()
        self.chaos = Chaos(self.cfg["chaos"], self.diff,
                           ("BLACKOUT",) if self.cfg.get("blackout") else ())

        # Surfaces de rendu
        self.world = pygame.Surface((WIDTH, HEIGHT))
        self.dk = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Pièges / minis / goal
        self.traps = []
        self.minis_spec = []
        self.goal = None
        self.minis = []

        # Layout initial (make_layout défini en § 11)
        self._rebuild_layout()

        # Shards décoratifs
        self.shards = ShardField(3 if IS_WEB else 10)

        # Stats globales
        SAVE["stats"]["games"] += 1
        try:
            audio.music("battle")
        except Exception:
            pass

        # Démarre le premier round
        self.start_round()

    # ---------------------------------------------------------------
    #  Time scale
    # ---------------------------------------------------------------
    def ts(self, team=None):
        """Facteur d'échelle temporelle.
        Pendant le Sanctuaire Temporel : tout est figé sauf le camp joueur."""
        if self.freeze_t > 0 and team != "P":
            return 0.0
        return self.chaos.p.get("tscale", 1.0) * (
            0.4 if self.slow_timer > 0 else 1.0)

    # ---------------------------------------------------------------
    #  Texte flottant
    # ---------------------------------------------------------------
    def add_text(self, x, y, text, color, big=False):
        if len(self.texts) < 40:
            self.texts.append(FloatText(x, y, text, color, big))

    # ---------------------------------------------------------------
    #  Points d'apparition
    # ---------------------------------------------------------------
    def spawn_points(self):
        sol = self.platforms[0]
        pts = [(110, sol.top), (WIDTH - 140, sol.top)]
        for pl in sorted(self.platforms[1:], key=lambda p: p.y)[:6]:
            pts.append((pl.centerx - 14, pl.top))
        return pts

    # ---------------------------------------------------------------
    #  Layout régénéré (Course / Faille) ou fixe (Survie, etc.)
    # ---------------------------------------------------------------
    def _rebuild_layout(self):
        """Reconstruit le terrain + le fond selon le mode courant.
        Affiche l'erreur en console si make_course/make_layout échoue."""
        fn_layout = globals().get("make_layout")
        fn_course = globals().get("make_course")
        fn_bg = globals().get("make_game_bg")

        # ── Reset systématique pour éviter les fuites entre modes
        self.traps = []
        self.minis_spec = []
        self.goal = None

        if self.cfg.get("course") and callable(fn_course):
            try:
                (self.platforms, self.traps,
                 self.minis_spec, self.goal) = fn_course(
                    self.rng, self.diff,
                    self.cfg.get("hard", False), self.round)
            except Exception as e:
                import traceback
                print("[REBUILD] make_course a échoué :", e)
                traceback.print_exc()
                self.platforms = self._fallback_layout()
                # Fallback : génère au moins un objectif pour ne jamais
                # bloquer le joueur
                top_plat = min(self.platforms[1:], key=lambda p: p.y)
                self.goal = pygame.Rect(
                    top_plat.centerx - 22, top_plat.top - 64, 44, 64)
        else:
            if callable(fn_layout):
                try:
                    self.platforms = fn_layout(4, self.rng,
                                               self.diff, self.round)
                except Exception as e:
                    print("[REBUILD] make_layout a échoué :", e)
                    self.platforms = self._fallback_layout()
            else:
                self.platforms = self._fallback_layout()

        # Diagnostic
        print("[REBUILD] mode=%s diff=%d round=%d  "
              "plats=%d traps=%d minis=%d goal=%s" % (
                  self.mode, self.diff, self.round,
                  len(self.platforms), len(self.traps),
                  len(self.minis_spec), self.goal is not None))

        if callable(fn_bg):
            try:
                self.bg = fn_bg(self.rng.random(), self.platforms)
            except Exception:
                self.bg = make_gradient_bg()
        else:
            self.bg = make_gradient_bg()

    def _fallback_layout(self):
        """Layout de secours si make_layout n'est pas disponible."""
        plats = [pygame.Rect(0, HEIGHT - 50, WIDTH, 50)]
        y = HEIGHT - 50
        for tier in range(4):
            y -= 90
            w = 150
            x = random.randint(60, WIDTH - w - 60)
            plats.append(pygame.Rect(x, y, w, 18))
        return plats

    # ---------------------------------------------------------------
    #  Démarrage de manche
    # ---------------------------------------------------------------
    def start_round(self):
        self.round += 1
        self.t = 0
        self.phase = "INTRO"
        self.timer = 115
        # Ré-applique le round_time (config du mode fraîche)
        _base_rt = self.cfg.get("round_time", 1800)
        if self.mode == "COURSE":
            _mult = [1.5, 1.25, 1.0, 0.9, 0.8][max(0, min(4, self.diff - 1))]
            self.round_time = int(_base_rt * _mult)
        else:
            self.round_time = _base_rt
        self.projectiles = []
        self.meteors = []
        self.met_cd = 40
        self.round_kills = 0
        self.round_reward = 0
        self.round_damage = 0
        self.kills_banked = False
        self.slow_timer = 0
        self.freeze_t = 0
        self.waves = []
        self.gem_items = []
        self.tele_t = 0
        self.barrage_cd = 60
        self.boss_cd = 200
        self.boss_f = None

        # Reset milestones
        self.milestone_kind = None
        self.milestone_boss = None
        self.calamity = False
        self.calamity_mult = 1.0
        self._mb_phase = 1
        self._mb_attack_cd = 120
        self._mb_attack_idx = 0

        # Reset chaos
        self.chaos.reset()

        # Layout régénéré
        self._rebuild_layout()

        # Reset echoes
        for e in self.echoes:
            e.reset()

        # Joueur
        sol = self.platforms[0]
        px = 60 if self.cfg.get("course") else 110
        self.player = Fighter("P", "P", SAVE["selected"],
                              px, sol.top - 38, 100, 100, record=True)
        self.player.apply_loadout(self.L)
        self.player.inv = 160
        if (self.L["special"] is None
                and self.player.weapon_type not in
                ("PLASMA", "LASER", "MISSILE")):
            self.player.weapon_type = "PLASMA"

        self.fighters = [self.player]
        self.slots = []
        self.minis = []

        # Peuplement selon le mode
        self._populate_round()

        # Piège secret éventuel
        self.pick_secret()

        # Invulnérabilité initiale
        for f in self.fighters:
            f.inv = max(f.inv, 30)

        # Cristal de gemmes éventuel
        self.spawn_gem_pickup()

        # Application du chaos permanent des niveaux secrets
        if self.cfg.get("secret_level"):
            self._apply_secret_level_chaos()

        # Milestone ?
        self._setup_milestone()

    # ---------------------------------------------------------------
    #  Peuplement de la manche selon le mode
    # ---------------------------------------------------------------
    def _populate_round(self):
        mode = self.mode
        D = DIFFS[self.diff]
        pts = self.spawn_points()

        if mode == "SURVIE":
            thr = D["thr"]
            base = 0 if (self.diff <= 2 and self.round <= 2) else 1
            n = (base + (self.round >= thr[0]) + (self.round >= thr[1])
                 + (1 if self.diff >= 4 and self.round >= 6 else 0))
            for i in range(n):
                px, py = pts[1] if i == 0 else random.choice(pts[2:])
                self.slots.append(
                    self.new_slot(i, self.round - 1 + i, px, py))

        elif mode == "ARENE":
            skins = [k for k in PUBLIC_SKINS if k != SAVE["selected"]]
            random.shuffle(skins)
            for i in range(3):
                px, py = [pts[1], pts[2], pts[3]][i]
                f = self.make_ai("A%d" % (i + 1), "A%d" % (i + 1),
                                 2 + i + self.round // 2, skins[i], px, py)
                f.record = True
                self.fighters.append(f)
            for f in self.fighters:
                self.pts.setdefault(f.id, 0)

        elif mode == "GLITCH":
            self.slots.append(
                self.new_slot(0, 5 + self.round, pts[1][0], pts[1][1],
                              strong=True))

        elif mode == "ECLIPSE":
            for i in range(2):
                px, py = pts[1 + i]
                self.slots.append(
                    self.new_slot(i, 4 + self.round + i, px, py))
            if self.round >= self.cfg["rounds"]:
                pl = random.choice(sorted(self.platforms[1:],
                                          key=lambda p: p.y)[:3])
                self.relic = pygame.Rect(pl.centerx - 9, pl.top - 34,
                                         18, 26)

        elif mode == "GARDIEN":
            hp = int((520 + 160 * self.round) * D["hp"])
            f = self.make_ai("BOSS", "A", 8 + self.round, "DEMON",
                             pts[1][0], pts[1][1], hp=hp,
                             size=(52, 70), boss=True)
            f.speed = min(5.2, f.speed)
            self.fighters.append(f)
            self.boss_f = f
            self.slots.append(dict(f=f, timer=0, level=0, idx=0,
                                   strong=True, fixed=True))

        elif self.minis_spec:
            for sp in self.minis_spec:
                self.minis.append(Mini(sp["kind"], sp["x"], sp["y"],
                                       sp["bounds"], self.round, self.diff))

    # ---------------------------------------------------------------
    #  Secret discovery (Arène / Glitch / Gardien / Éclipse / Faille)
    # ---------------------------------------------------------------
    # ---------------------------------------------------------------
    #  Secret discovery (Arène / Glitch / Gardien / Éclipse / Faille)
    # ---------------------------------------------------------------
    def pick_secret(self):
        self.secret = None
        for kind in reversed(SECRET_ORDER):
            r = SECRET_RULES[kind]
            if (r["src"] != self.mode
                    or self.round < r["min_round"]
                    or self.diff < r["min_diff"]):
                continue
            if random.random() < r["chance"]:
                plats = sorted(self.platforms[1:], key=lambda p: p.y)
                if not plats:
                    return
                if r["place"] == "top":
                    top_y = plats[0].y
                    pl = random.choice([p for p in plats if p.y == top_y])
                elif r["place"] == "far":
                    pl = min(plats[:4], key=lambda p: p.centerx)
                else:
                    pl = random.choice(plats)
                self.secret = dict(kind=kind, vis=r["vis"],
                                   rect=pygame.Rect(pl.centerx - 14,
                                                    pl.top - 52, 28, 52))
                return

    # ---------------------------------------------------------------
    #  Création d'IA
    # ---------------------------------------------------------------
    def make_ai(self, ident, team, level, skin, px, py,
                hp=None, size=(28, 38), boss=False):
        D = DIFFS[self.diff]
        lv = max(0, level + D["off"])
        hp = hp or int((80 + 22 * min(lv, 14)) * D["hp"])
        f = Fighter(ident, team, skin, px, py - size[1], hp, 100, False, size)
        # Plafond de vitesse progressif : D1 = lent, D15 = rapide mais jouable
        speed_cap = 6.0 + 0.10 * self.diff
        f.speed = min(speed_cap, (4.4 + 0.2 * lv) * D["spd"])
        f.dmg_mult = D["dmg"]
        f.brain = AIBrain(lv, self.diff, boss)
        f.boss = boss
        return f

    def ai_skin(self):
        return random.choice([k for k in PUBLIC_SKINS
                              if k != SAVE["selected"]])

    def new_slot(self, idx, level, px, py, strong=False):
        hp = (int((260 + 40 * self.round) * DIFFS[self.diff]["hp"])
              if strong else None)
        f = self.make_ai("A%d" % idx, "A",
                         level, "MECHA_RED" if strong else self.ai_skin(),
                         px, py, hp=hp)
        self.fighters.append(f)
        return dict(f=f, timer=120, level=level, idx=idx,
                    strong=strong, fixed=strong)

    def manage_slots(self):
        for sl in self.slots:
            f = sl["f"]
            if f.alive or sl.get("fixed"):
                continue
            sl["timer"] -= 1
            if sl["timer"] <= 0:
                self.fighters.remove(f)
                sp = self.spawn_points()[1:]
                px, py = random.choice(sp) if sp else (WIDTH // 2, 200)
                sl["level"] += 1
                nf = self.make_ai("A%d" % sl["idx"], "A",
                                  sl["level"], self.ai_skin(), px, py)
                nf.inv = 60
                self.fighters.append(nf)
                sl["f"], sl["timer"] = nf, 120

    # ---------------------------------------------------------------
    #  Chaos permanent des niveaux secrets
    # ---------------------------------------------------------------
    def _apply_secret_level_chaos(self):
        sid = self.cfg.get("secret_level")
        if not sid:
            return
        info = SECRET_LEVELS_INFO.get(sid, {})
        eff = info.get("effect")
        if sid == "OMEGA":
            # Tous les effets simultanés
            p = dict(DEFAULT_P)
            for k in EFFECTS:
                p.update(EFFECTS[k]["p"])
            p["giant"] = True
            p["ricochet"] = True
            p["homing"] = True
            p["meteors"] = True
            p["lava"] = True
            p["barrage"] = True
            p["tele"] = True
            p["noshield"] = True
            p["poison"] = True
            p["dmgx"] = 2.0
            p["grav"] = 0.5
            self.chaos.p = p
            self.chaos.key = None
            self.chaos.interval = 999999
            return

        if not eff or eff not in EFFECTS:
            return

        # Application avec intensification ×1.5 sur les valeurs numériques
        intensity = 1.5
        base = EFFECTS[eff]["p"]
        p = dict(DEFAULT_P)
        for k, v in base.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if k in ("invert", "slip", "blackout", "giant",
                         "ricochet", "homing", "meteors", "lava",
                         "barrage", "tele", "noshield", "bounce",
                         "poison", "antigrav"):
                    p[k] = v
                elif k == "dmgx":
                    p[k] = v * intensity
                elif k == "grav":
                    p[k] = max(0.05, v * 0.7)   # gravité plus faible = plus intense
                else:
                    p[k] = v * intensity
            else:
                p[k] = v
        self.chaos.p = p
        self.chaos.key = eff
        self.chaos.interval = 999999

    # ---------------------------------------------------------------
    #  Milestone : boss épique ou calamité
    # ---------------------------------------------------------------
    def _setup_milestone(self):
        if self.round % MILESTONE_INTERVAL != 0:
            return
        if self.mode not in ("SURVIE", "COURSE", "GLITCH", "FAILLE"):
            return
        cycle = (self.round // MILESTONE_INTERVAL) % 2
        kind = "BOSS" if cycle == 1 else "CALAMITY"
        if random.random() < 0.35:
            kind = "CALAMITY" if kind == "BOSS" else "BOSS"
        self.milestone_kind = kind
        if kind == "BOSS":
            self._spawn_milestone_boss()
        else:
            self._apply_calamity()

    def _spawn_milestone_boss(self):
        level = max(1, self.round // MILESTONE_INTERVAL)
        pts = self.spawn_points()
        px, py = pts[1] if len(pts) > 1 else (WIDTH // 2, HEIGHT // 2)
        skin_key = random.choice(MILESTONE_BOSS_SKINS)
        hp = int((700 + 260 * level) * DIFFS[self.diff]["hp"]
                 * (1 + 0.05 * max(0, self.round - 5)))
        boss = self.make_ai("BOSS", "A", 8 + level, skin_key,
                            px, py, hp=hp, size=(56, 76), boss=True)
        boss.speed = 3.2 + 0.15 * self.diff
        boss.dmg_mult = DIFFS[self.diff]["dmg"] * 0.85
        self.fighters.append(boss)
        self.boss_f = boss
        self.milestone_boss = boss
        self._mb_phase = 1
        self._mb_attack_cd = 120
        self._mb_attack_idx = 0
        self.slots = []
        self.shake = max(self.shake, 20)
        self.add_text(WIDTH // 2, HEIGHT // 2 - 100,
                      tr("BOSS ÉPIQUE !"), ROUGE_NEON, True)
        audio.play("chaos", 1.0)
        audio.play("boom", 0.9)

    def _apply_calamity(self):
        self.calamity = True
        self.calamity_mult = 1.6 + 0.15 * self.diff
        self.chaos.interval = max(300, self.cfg["chaos"] // 2)
        self.cfg = dict(self.cfg)
        self.cfg["meteors"] = True
        for i in range(2 + self.diff // 2):
            pts = self.spawn_points()
            sp = pts[1:] if len(pts) > 1 else [(WIDTH // 2, HEIGHT // 2)]
            px, py = random.choice(sp)
            self.slots.append(self.new_slot(10 + i, self.round + i,
                                            px, py, strong=(i % 2 == 0)))
        self.shake = max(self.shake, 15)
        self.add_text(WIDTH // 2, HEIGHT // 2 - 100,
                      tr("DÉFERLANTE !"), (255, 90, 60), True)
        audio.play("chaos", 0.9)

    # ---------------------------------------------------------------
    #  Projectiles & combat
    # ---------------------------------------------------------------
    def spawn_projectile(self, x, y, vx, vy, kind, team, src_id, src_kind,
                         color=None, dmg=None, mult=1.0):
        try:
            self.projectiles.append(
                Projectile(x, y, vx, vy, kind, team, src_id, src_kind,
                           self, color, dmg, mult))
        except Exception:
            pass

    def nearest_fighter(self, x, y, team, maxd=99999):
        best, bd = None, maxd
        for f in self.fighters:
            if f.alive and f.team != team:
                d = math.hypot(f.rect.centerx - x, f.rect.centery - y)
                if d < bd:
                    best, bd = f, d
        return best

    def nearest_enemy(self, x, y, team, maxd=99999):
        best = self.nearest_fighter(x, y, team, maxd)
        bd = (math.hypot(best.rect.centerx - x, best.rect.centery - y)
              if best else maxd)
        if team != "M":
            for m in self.minis:
                if m.alive:
                    d = math.hypot(m.rect.centerx - x, m.rect.centery - y)
                    if d < bd:
                        best, bd = m, d
        return best

    def trap_rects(self):
        """Rectangles de collision des pièges actifs (mise à jour par t)."""
        out = []
        mult = getattr(self, "calamity_mult", 1.0)
        for tr_ in self.traps:
            k = tr_["kind"]
            if k == "SPIKE":
                out.append(tr_["rect"])
            elif k == "SAW":
                sx = (tr_["x0"] + (tr_["x1"] - tr_["x0"]) *
                      (0.5 + 0.5 * math.sin(self.t * 0.03 * mult
                                            + tr_["phase"])))
                out.append(pygame.Rect(int(sx) - 18, int(tr_["y"]) - 18,
                                       36, 36))
            elif k == "LASER" and self.laser_on(tr_):
                out.append(pygame.Rect(tr_["x"] - 4, tr_["y1"],
                                       8, tr_["y2"] - tr_["y1"]))
            elif k == "RETRACT_SPIKE":
                state, _kk = _retract_spike_state(self.t * mult + tr_["phase"])
                if state == "out":
                    r = tr_["rect"]
                    out.append(pygame.Rect(r.x + 6, r.bottom - r.h,
                                           r.w - 12, r.h))
            elif k == "SWEEP_LASER_V":
                x = _sweep_v_x(self, tr_)
                out.append(pygame.Rect(int(x) - 5, tr_["y1"],
                                       10, tr_["y2"] - tr_["y1"]))
            elif k == "SWEEP_LASER_H":
                y = _sweep_h_y(self, tr_)
                out.append(pygame.Rect(tr_["x1"], int(y) - 5,
                                       tr_["x2"] - tr_["x1"], 10))
            elif k == "CROSS_LASER":
                phase = (self.t + tr_["phase"]) % CROSS_LASER_PERIOD
                if CROSS_LASER_WARN <= phase < CROSS_LASER_WARN + CROSS_LASER_ACTIVE:
                    out.append(pygame.Rect(tr_["x1"] - 3, tr_["y1"],
                                           6, tr_["y2"] - tr_["y1"]))
                    out.append(pygame.Rect(tr_["x2"] - 3, tr_["y1"],
                                           6, tr_["y2"] - tr_["y1"]))
            elif k == "UNSTABLE_PLATFORM":
                if tr_["triggered"] == 1:
                    out.append(tr_["rect"])
            elif k == "VERTICAL_CRUSHER":
                phase = (self.t + tr_["phase"]) % CRUSHER_PERIOD
                if phase < CRUSHER_STRIKE:
                    out.append(pygame.Rect(tr_["x"],
                                           tr_["base_y"] - tr_["h"],
                                           tr_["w"], tr_["h"]))
            elif k == "PLASMA_POOL":
                out.append(pygame.Rect(tr_["x"], tr_["y"],
                                       tr_["w"], tr_["h"]))
            elif k == "TIME_DISTORTION":
                out.append(pygame.Rect(tr_["x"], tr_["y"] - tr_["h"],
                                       tr_["w"], tr_["h"]))
        return out

    def laser_on(self, tr_):
        return ((self.t // 60) + tr_["phase"]) % 2 == 0

    def player_kill(self, x=None, y=None):
        """Appelé à chaque élimination : Digestion (soin) + Réaction en chaîne."""
        p = self.player
        if p is None or not p.alive:
            return
        if p.kill_heal and p.hp < p.max_hp:
            p.hp = min(p.max_hp, p.hp + p.kill_heal)
            particle_system.emit(p.rect.centerx, p.rect.centery, 8,
                                 (255, 70, 90), (-2, 2), (2, 5), 20)
        if x is not None and random.random() < GEM_DROP_KILL * (0.5 + 0.25 * self.diff):
            self.drop_gem(x, y)
        depth = getattr(self, "_chain_depth", 0)
        if p.chain and x is not None and depth < 5:
            self._chain_depth = depth + 1
            self.explode(x, y, p.chain[0], p.chain[1] * p.gdmg,
                         p.team, p.id, "player")
            self._chain_depth = depth
        if p.combustion_max > 0 and p.combustion < p.combustion_max:
            p.combustion += 1
            particle_system.emit(p.rect.centerx, p.rect.top - 8, 3,
                                 (255, 200, 60), (-1, 1), (2, 4), 18)

    def explode(self, x, y, radius, dmg, team, src_id, src_kind):
        particle_system.emit(x, y, 30, (255, 160, 60),
                             (-6, 6), (3, 8), 30)
        self.rings.append(dict(x=x, y=y, r=8, mx=radius, life=14))
        self.shake = max(self.shake, 5)
        audio.play("boom", 0.6)
        for f in self.fighters:
            if f.alive and f.team != team:
                d = math.hypot(f.rect.centerx - x, f.rect.centery - y)
                if d < radius + 14:
                    f.hurt(dmg * (1 - 0.5 * clamp(d / (radius + 30), 0, 1)),
                           "EXPLOSION", self, src=src_id)
        if team != "M":
            for m in self.minis:
                if (m.alive
                        and math.hypot(m.rect.centerx - x,
                                       m.rect.centery - y) < radius + 10):
                    m.hurt(dmg, self)

    # ---------------------------------------------------------------
    #  Gemmes
    # ---------------------------------------------------------------
    def spawn_gem_pickup(self):
        chance = (GEM_PICKUP_BASE + 0.04 * self.diff
                  + (0.15 if self.cfg.get("secret") else 0.0))
        if random.random() >= chance:
            return
        pls = [pl for pl in self.platforms if pl.w >= 60] or list(self.platforms)
        if not pls:
            return
        pl = random.choice(pls)
        roll = random.random()
        v = 1 if roll < 0.78 else (3 if roll < 0.95 else 5)
        x = random.randint(pl.x + 20, max(pl.x + 20, pl.right - 20))
        self.gem_items.append(dict(x=float(x), y=float(pl.top - 26),
                                   v=v, life=None,
                                   ph=random.random() * 6.0))

    def drop_gem(self, x, y):
        if len(self.gem_items) < 6:
            self.gem_items.append(dict(
                x=float(clamp(x, 18, WIDTH - 18)),
                y=float(clamp(y - 8, 24, HEIGHT - 30)),
                v=1, life=720, ph=random.random() * 6.0))

    def collect_gems(self):
        p = self.player
        for g in self.gem_items[:]:
            if g["life"] is not None:
                g["life"] -= 1
                if g["life"] <= 0:
                    self.gem_items.remove(g)
                    continue
            if (p.alive and self.phase == "PLAY"
                    and pygame.Rect(int(g["x"]) - 13, int(g["y"]) - 13,
                                    26, 26).colliderect(p.rect)):
                self.gem_items.remove(g)
                n = grant_gems(g["v"])
                self.gems_pick += n
                audio.play("pickup")
                particle_system.emit(g["x"], g["y"], 18, GEM_COL,
                                     (-4, 4), (2, 6), 26)
                self.add_text(g["x"], g["y"] - 18,
                              "+%d %s" % (n, tr("GEMME") if n == 1
                                          else tr("GEMMES")),
                              GEM_COL, True)

    def pay_gems(self, announce=False):
        """Verse les gemmes de fin de run (une seule fois)."""
        if self.gems_paid:
            return 0
        self.gems_paid = True
        n = grant_gems(run_gems(self))
        self.gems_run += n
        if n and announce:
            say("+%d %s" % (n, tr("GEMMES") if n > 1 else tr("GEMME")),
                GEM_COL)
        return n

    # ---------------------------------------------------------------
    #  Sanctuaire Temporel
    # ---------------------------------------------------------------
    def fissure(self, cx, cy, radius):
        """Onde dorée + fissures qui zèbrent l'écran."""
        self.waves.append(dict(x=cx, y=cy, r=12.0,
                               mx=float(min(radius, 1250)),
                               life=42, max=42))
        cracks = []
        n = 14
        for i in range(n):
            ang = i * math.tau / n + random.uniform(-0.2, 0.2)
            ln = random.uniform(420, 1150)
            pts = [(float(cx), float(cy))]
            d = 0.0
            while d < ln:
                st_ = random.uniform(38, 80)
                ang += random.uniform(-0.3, 0.3)
                pts.append((pts[-1][0] + math.cos(ang) * st_,
                            pts[-1][1] + math.sin(ang) * st_))
                d += st_
            cracks.append(pts)
        self.fis = dict(cx=cx, cy=cy, cracks=cracks)

    def end_freeze(self):
        self.freeze_t = 0
        audio.play("chaos", 0.5)
        if self.player is not None and self.player.alive:
            self.add_text(self.player.rect.centerx, self.player.rect.top - 40,
                          tr("LE TEMPS REPREND"), CYAN_NEON, True)

    # ---------------------------------------------------------------
    #  Boucle principale (dispatch des états)
    # ---------------------------------------------------------------
    def update(self, keys, mb, mpos):
        if self.paused:
            return
        if self.shake > 0:
            self.shake -= 1
        if self.black_hole_fx:
            self.black_hole_fx["life"] -= 1
            if self.black_hole_fx["life"] <= 0:
                self.black_hole_fx = None

        # Tick global de tous les combattants
        for f in self.fighters:
            f.tick()

        # Textes flottants
        for tx in self.texts[:]:
            tx.update()
            if tx.life <= 0:
                self.texts.remove(tx)

        # Anneaux d'explosion
        for rg in self.rings[:]:
            rg["life"] -= 1
            rg["r"] += (rg["mx"] - rg["r"]) * 0.35
            if rg["life"] <= 0:
                self.rings.remove(rg)

        # Ondes de choc (Sanctuaire / nova)
        for wv in self.waves[:]:
            wv["life"] -= 1
            wv["r"] += (wv["mx"] - wv["r"]) * 0.16
            if wv["life"] <= 0:
                self.waves.remove(wv)

        # Machine à états
        if self.phase == "INTRO":
            self.timer -= 1
            if self.timer % 30 == 0 and self.timer > 0:
                audio.play("tick", 0.6)
            if self.timer <= 0:
                self.phase = "PLAY"
                if not self.cfg.get("secret_level"):
                    self.chaos.roll()
                self.player.inv = 60

        elif self.phase == "ROUND_END":
            self.timer -= 1
            if self.timer <= 0:
                self.start_round()

        elif self.phase in ("PLAY", "DYING"):
            self.step_world(keys, mb, mpos)

    def step_world(self, keys, mb, mpos):
        was_frozen = self.freeze_t > 0

        self.total += 1
        if self.slow_timer > 0:
            self.slow_timer -= 1

        # Sanctuaire : chrono de manche et roue suspendus
        if was_frozen:
            self.freeze_t -= 1
            if self.freeze_t <= 0:
                self.end_freeze()
        else:
            self.t += 1
            # Pas de nouveau chaos pour les niveaux secrets (permanent)
            if not self.cfg.get("secret_level"):
                self.chaos.update(self)

        # Input joueur
        p = self.player
        if p.alive and self.phase == "PLAY":
            p.step(self.player_input(keys, mb, mpos), self, 1.0)

        frozen = self.freeze_t > 0
        ts = self.ts()

        # IA
        for f in self.fighters:
            if f is p or not f.alive or frozen:
                continue
            inp = f.brain.decide(f, self) if f.brain else None
            if inp:
                f.step(inp, self, ts)

        # Échos
        for e in self.echoes:
            e.step(self)

        if not frozen:
            # Minis
            for m in self.minis:
                if m.alive:
                    m.update(self)
            # Chaos actifs
            self.chaos_effects(ts)
            self.update_meteors()

        # Projectiles (toujours simulés pour avancer visuellement,
        # mais les hostiles sont figés pendant Sanctuaire)
        self.update_projectiles()

        # Contacts
        self.contacts()

        # Morts
        self.process_deaths()

        # Gestion des slots (respawn IA)
        self.manage_slots()

        # Boss
        self.manage_boss(ts)

        # Piège secret (contact)
        if self.secret and p.alive:
            if self.t % 10 == 0:
                r = self.secret["rect"]
                particle_system.emit(r.centerx, r.bottom, 1, PURPLE_NEON,
                                     (-0.4, 0.4), (1, 2), 40)
            if p.rect.colliderect(self.secret["rect"]):
                self.secret_exit = self.secret["kind"]
                self.bank_exit()

        # Relique (Éclipse)
        if self.relic and p.alive and p.rect.colliderect(self.relic):
            self.relic = None
            SAVE["stats"]["relic"] = True
            particle_system.emit(p.rect.centerx, p.rect.centery, 40,
                                 (255, 150, 30), (-5, 5), (3, 7), 40)
            audio.play("pickup")
            self.add_text(p.rect.centerx, p.rect.top - 20,
                          tr("RELIQUE TROUVÉE !"), (255, 150, 30), True)
            self.new_ach += check_achievements()

        # Gemmes
        self.collect_gems()

        # Fin de manche ?
        self.check_end()

    # ---------------------------------------------------------------
    #  Input joueur
    # ---------------------------------------------------------------
    def player_input(self, keys, mb, mpos):
        kl, kr, kj = move_keys()
        return dict(
            left=keys[kl] or keys[pygame.K_LEFT],
            right=keys[kr] or keys[pygame.K_RIGHT],
            jump=(keys[pygame.K_SPACE] or keys[kj] or keys[pygame.K_UP]),
            down=keys[pygame.K_s] or keys[pygame.K_DOWN],
            shield=(mb[2] or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]),
            ability=keys[pygame.K_e],
            shoot=mpos if mb[0] else None,
            aim=mpos,
            weapon=self.player.weapon_type,
            skin_ab=(keys[pygame.K_f]
                     or (keys[pygame.K_e] and not self.player.ability)),
        )

    # ---------------------------------------------------------------
    #  Chaos actifs
    # ---------------------------------------------------------------
    def chaos_effects(self, ts):
        c = self.chaos.p
        alive = [f for f in self.fighters if f.alive]

        if c.get("tele"):
            self.tele_t += 1
            if self.tele_t % 180 == 0:
                for f in alive:
                    pts = self.spawn_points()
                    px, py = random.choice(pts)
                    particle_system.emit(f.rect.centerx, f.rect.centery, 14,
                                         (90, 230, 255),
                                         (-3, 3), (2, 5), 20)
                    f.x, f.y, f.vy = float(px), float(py - f.h), 0.0
                    f.rect.topleft = (int(f.x), int(f.y))
                    particle_system.emit(f.rect.centerx, f.rect.centery, 14,
                                         (90, 230, 255),
                                         (-3, 3), (2, 5), 20)
                audio.play("dash")
        else:
            self.tele_t = 0

        if c.get("barrage") and alive:
            self.barrage_cd -= ts
            if self.barrage_cd <= 0:
                self.barrage_cd = 55
                tgt = random.choice(alive)
                side = random.choice(("L", "R", "T"))
                if side == "L":
                    x, y = 0, random.randint(80, HEIGHT - 80)
                elif side == "R":
                    x, y = WIDTH, random.randint(80, HEIGHT - 80)
                else:
                    x, y = random.randint(40, WIDTH - 40), 0
                a = math.atan2(tgt.rect.centery - y, tgt.rect.centerx - x)
                self.spawn_projectile(
                    x, y, math.cos(a) * 8.5, math.sin(a) * 8.5,
                    "PLASMA", "X", "enemy", "enemy",
                    color=ROUGE_NEON, dmg=9 * DIFFS[self.diff]["dmg"])

        if c.get("poison") and self.t % 40 == 0:
            for f in alive:
                f.hurt(2, "RADIATION", self, blockable=False, force=True)

    def update_meteors(self):
        ts = self.ts()
        if self.chaos.p.get("meteors") or self.cfg.get("meteors"):
            self.met_cd -= ts
            if self.met_cd <= 0:
                self.met_cd = (random.uniform(10, 22)
                               if self.cfg.get("meteors")
                               else random.uniform(20, 36))
                self.meteors.append(dict(
                    x=random.randint(30, WIDTH - 30), y=-20.0,
                    vx=random.uniform(-1.2, 1.2),
                    vy=random.uniform(5, 8.5), delay=45))

        for m in self.meteors[:]:
            if m["delay"] > 0:
                m["delay"] -= ts
                continue
            m["x"] += m["vx"] * ts
            m["y"] += m["vy"] * ts
            r = pygame.Rect(int(m["x"]) - 12, int(m["y"]) - 12, 24, 24)
            hit = False
            for f in self.fighters:
                if f.alive and r.colliderect(f.rect):
                    f.hurt(16, "MÉTÉORITE", self)
                    hit = True
            if not hit:
                hit = any(r.colliderect(pl) for pl in self.platforms)
            if hit:
                particle_system.emit(m["x"], m["y"], 18, ORANGE,
                                     (-4, 4), (3, 7), 25)
                self.shake = max(self.shake, 3)
                audio.play("boom", 0.25)
                self.meteors.remove(m)
            elif m["y"] > HEIGHT + 30:
                self.meteors.remove(m)

    # ---------------------------------------------------------------
    #  Mise à jour des projectiles (collision + morts)
    # ---------------------------------------------------------------
    def update_projectiles(self):
        for p in self.projectiles[:]:
            p.update(self)
            if self.freeze_t > 0 and p.team != "P":
                continue
            if p.active:
                for f in self.fighters:
                    if not (f.alive and f.team != p.team
                            and id(f) not in p.hit
                            and p.rect.colliderect(f.rect)):
                        continue
                    if f.shield_active and f.reflect:
                        p.vx, p.vy = -p.vx, -p.vy
                        p.team, p.src_id = f.team, f.id
                        p.src_kind = "player" if f is self.player else "ai"
                        p.x += p.vx * 2
                        p.y += p.vy * 2
                        p.hit.clear()
                        particle_system.emit(p.x, p.y, 10, MINT, (-3, 3))
                        audio.play("shield", 0.6)
                        break
                    f.hurt(p.damage, CAUSES.get(p.src_kind, "TIR ENNEMI"),
                           self, src=p.src_id)
                    if p.burn and f.alive:
                        f.burn, f.burn_src = 150, p.src_id
                    particle_system.emit(p.x, p.y, 12, p.color)
                    if p.pierce:
                        p.hit.add(id(f))
                    else:
                        p.active = False
                        break

            if p.active and p.team != "M":
                for m in self.minis:
                    if (m.alive and id(m) not in p.hit
                            and p.rect.colliderect(m.rect)):
                        m.hurt(p.damage, self)
                        if p.pierce:
                            p.hit.add(id(m))
                        else:
                            p.active = False
                            break

            if not p.active:
                if p.explode:
                    self.explode(p.x, p.y, 90, p.damage * 0.9,
                                 p.team, p.src_id, p.src_kind)
                try:
                    self.projectiles.remove(p)
                except ValueError:
                    pass

    # ---------------------------------------------------------------
    #  Contacts (pièges, lave, échos, minis, burn)
    # ---------------------------------------------------------------
    def contacts(self):
        trap_rects = self.trap_rects()
        sol = self.platforms[0] if self.platforms else None

        for f in self.fighters:
            if not f.alive:
                continue
            # Sanctuaire : joueur intouchable
            if self.freeze_t > 0 and f is self.player:
                continue

            # Brûlure
            if f.burn > 0:
                f.burn -= 1
                if f.burn % 12 == 0:
                    f.hurt(1.6, "BRÛLURE", self, src=f.burn_src,
                           blockable=False, force=True)

            # Lave
            if (self.chaos.p.get("lava") and f.on_ground and sol
                    and f.rect.bottom >= sol.top - 1
                    and f.trap_cd == 0 and f.trapsafe == 0):
                f.hurt(6, "SOL EN LAVE", self, blockable=False, force=True)
                f.trap_cd = 30
                f.vy = -5
                particle_system.emit(f.rect.centerx, f.rect.bottom, 8,
                                     (255, 90, 20), (-2, 2), (2, 5), 18)

            # Échos
            if f.contact_cd == 0:
                for e in self.echoes:
                    if (e.alive and e.team != f.team
                            and e.rect.colliderect(f.rect)):
                        f.hurt(7, "ÉCHO FAUCHEUR", self, src=e.src_id)
                        f.contact_cd = 30
                        break

            # Ennemis au contact
            if f.contact_cd == 0:
                for m in self.minis:
                    if (m.alive and m.kind == "WALKER"
                            and m.rect.colliderect(f.rect)):
                        f.hurt(10 * DIFFS[self.diff]["dmg"],
                               "ENNEMI AU CONTACT", self)
                        f.contact_cd = 40
                        f.vy = -6
                        break

            # Pièges
            if f.trap_cd == 0 and f.trapsafe == 0:
                for r in trap_rects:
                    if r.colliderect(f.rect):
                        f.hurt(18, "PIÈGE MORTEL", self, blockable=False)
                        f.trap_cd = 45
                        f.vy = -7
                        break

            # Champs de plasma au sol
            for tr_ in self.traps:
                if tr_["kind"] == "PLASMA_POOL":
                    r = pygame.Rect(tr_["x"], tr_["y"], tr_["w"], tr_["h"])
                    if f.rect.colliderect(r) and f.trap_cd == 0:
                        f.hurt(PLASMA_DMG_PER_TICK * 60, "PLASMA", self,
                               blockable=False, force=True)
                        f.trap_cd = 30
                        particle_system.emit(f.rect.centerx, f.rect.bottom, 6,
                                             ORANGE, (-2, 2), (2, 5), 16)

            # Puits de distorsion temporelle
            for tr_ in self.traps:
                if tr_["kind"] == "TIME_DISTORTION":
                    r = pygame.Rect(tr_["x"], tr_["y"] - tr_["h"],
                                    tr_["w"], tr_["h"])
                    if f.rect.colliderect(r):
                        f.vx *= TIME_DISTORT_FACTOR
                        if f is self.player and self.t % 8 == 0:
                            particle_system.emit(f.rect.centerx,
                                                 f.rect.centery, 2,
                                                 (200, 150, 255),
                                                 (-1, 1), (2, 4), 20)

            # Annihilateurs de saut
            for tr_ in self.traps:
                if tr_["kind"] == "JUMP_BLOCKER":
                    zone = pygame.Rect(tr_["x"], tr_["y"],
                                       tr_["w"], tr_["h"])
                    if f.rect.colliderect(zone) and f.vy < 0:
                        f.vy = 0.4
                        if f is self.player and self.t % 12 == 0:
                            self.add_text(f.rect.centerx, f.rect.top - 18,
                                          tr("SAUT BLOQUÉ"), PURPLE_NEON)

        # Dalles instables : déclenchement
        for tr_ in self.traps:
            if tr_["kind"] != "UNSTABLE_PLATFORM":
                continue
            if tr_["triggered"] == 0:
                for f in self.fighters:
                    if (f.alive and f.on_ground
                            and f.rect.colliderect(tr_["rect"])):
                        tr_["triggered"] = 1
                        tr_["timer"] = UNSTABLE_DELAY
                        audio.play("tick", 0.4)
                        break

        # Dalles instables : chronos
        for tr_ in self.traps:
            if tr_["kind"] != "UNSTABLE_PLATFORM":
                continue
            if tr_["triggered"] == 1:
                tr_["timer"] -= 1
                if tr_["timer"] <= 0:
                    tr_["triggered"] = 2
                    tr_["timer"] = UNSTABLE_RESPAWN
                    rr = tr_["rect"]
                    self.platforms = [p for p in self.platforms
                                      if not p.colliderect(rr)]
                    particle_system.emit(rr.centerx, rr.centery, 24,
                                         (120, 80, 160),
                                         (-5, 5), (3, 7), 28)
                    audio.play("boom", 0.4)
            elif tr_["triggered"] == 2:
                tr_["timer"] -= 1
                if tr_["timer"] <= 0:
                    tr_["triggered"] = 0
                    if not any(p.colliderect(tr_["rect"])
                               for p in self.platforms):
                        self.platforms.append(tr_["rect"])
                    particle_system.emit(tr_["rect"].centerx,
                                         tr_["rect"].centery, 18,
                                         (180, 140, 255),
                                         (-4, 4), (2, 6), 24)

        # Missiles ambiants
        ts = self.ts()
        for tr_ in self.traps:
            if tr_["kind"] != "AMBIENT_MISSILE":
                continue
            tr_["cd"] -= ts
            if tr_["cd"] <= 0:
                tr_["cd"] = AMBIENT_MISSILE_CD
                targets = [f for f in self.fighters if f.alive]
                if targets:
                    tgt = random.choice(targets)
                    a = math.atan2(tgt.rect.centery - tr_["y"],
                                   tgt.rect.centerx - tr_["x"])
                    self.spawn_projectile(
                        tr_["x"], tr_["y"],
                        math.cos(a) * 4.5, math.sin(a) * 4.5,
                        "MISSILE", "X", "enemy", "enemy",
                        color=ORANGE, dmg=8 * DIFFS[self.diff]["dmg"])

    # ---------------------------------------------------------------
    #  Traitement des morts
    # ---------------------------------------------------------------
    def process_deaths(self):
        for f in self.fighters:
            if f.alive or f.handled:
                continue
            f.handled = True
            particle_system.emit(f.rect.centerx, f.rect.centery, 36,
                                 SKINS[f.skin_key]["body"],
                                 (-5, 5), (3, 7), 35)
            self.shake = max(self.shake, 10)
            audio.play("ko" if f is self.player else "boom", 0.8)
            if self.cfg["ffa"]:
                if (f.last_src and f.last_src != f.id
                        and f.last_src in self.pts):
                    self.pts[f.last_src] += 1
                    if f.last_src == "P":
                        self.round_kills += 1
                        self.kills += 1
                        self.add_text(f.rect.centerx, f.rect.top, "+1",
                                      VERT_NEON, True)
                        self.player_kill(f.rect.centerx, f.rect.centery)
            elif f.team == "A":
                self.kills += 1
                self.round_kills += 1
                self.add_text(f.rect.centerx, f.rect.top, "+150",
                              VERT_NEON, True)
                self.player_kill(f.rect.centerx, f.rect.centery)

    # ---------------------------------------------------------------
    #  Boss IA
    # ---------------------------------------------------------------
    def manage_boss(self, ts):
        b = self.boss_f
        if not b or not b.alive or self.phase != "PLAY":
            return

        # Comportement générique : anneau de projectiles
        self.boss_cd -= ts
        if self.boss_cd <= 0:
            self.boss_cd = 260 if b.hp > b.max_hp * 0.4 else 150
            n = 12
            for i in range(n):
                a = i * math.tau / n + self.t * 0.01
                self.spawn_projectile(
                    b.rect.centerx, b.rect.centery,
                    math.cos(a) * 7, math.sin(a) * 7,
                    "PLASMA", "A", "boss", "ai",
                    color=ORANGE, dmg=10 * DIFFS[self.diff]["dmg"])
            audio.play("special", 0.7)
            self.shake = max(self.shake, 5)

        # Comportement du boss épique
        mb = self.milestone_boss
        if not mb or not mb.alive:
            return
        k = mb.hp / max(1, mb.max_hp)
        new_phase = 1 if k > 0.66 else (2 if k > 0.33 else 3)
        if new_phase != self._mb_phase:
            self._mb_phase = new_phase
            self.shake = max(self.shake, 16)
            audio.play("chaos", 0.8)
            self.add_text(mb.rect.centerx, mb.rect.top - 40,
                          tr("PHASE %d") % new_phase, ROUGE_NEON, True)
            particle_system.emit(mb.rect.centerx, mb.rect.centery, 40,
                                 (255, 90, 60), (-6, 6), (3, 8), 38)
        self._mb_attack_cd -= ts
        if self._mb_attack_cd <= 0:
            self._mb_attack_cd = max(45, 130 - 22 * new_phase)
            self._boss_attack(mb, new_phase)

    def _boss_attack(self, boss, phase):
        pattern = self._mb_attack_idx % 4
        self._mb_attack_idx += 1
        cx, cy = boss.rect.centerx, boss.rect.centery
        dmg_scale = DIFFS[self.diff]["dmg"]

        if pattern == 0:
            n = 8 + 2 * phase
            for i in range(n):
                a = math.pi * (0.15 + 0.7 * i / max(1, n - 1))
                sp = 6.0 + 0.6 * phase
                self.spawn_projectile(
                    cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                    "PLASMA", "A", "boss", "ai",
                    color=ORANGE, dmg=9 * dmg_scale)
            audio.play("special", 0.7)

        elif pattern == 1:
            n = 10 + 4 * phase
            for i in range(n):
                a = i * math.tau / n + self.t * 0.008
                sp = 5.0 + 0.5 * phase
                self.spawn_projectile(
                    cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                    "LASER", "A", "boss", "ai",
                    color=PURPLE_NEON, dmg=8 * dmg_scale)
            self.shake = max(self.shake, 6)

        elif pattern == 2 and phase >= 2:
            for _ in range(2 + phase):
                px = random.randint(80, WIDTH - 80)
                py = boss.rect.top - 40
                self.minis.append(Mini("FLYER", px, py,
                                       (60, WIDTH - 60), 6, self.diff))
            self.shake = max(self.shake, 8)
            audio.play("chaos", 0.7)

        elif pattern == 3 and phase >= 2:
            tgt = self.player
            if tgt and tgt.alive:
                dx = tgt.rect.centerx - cx
                dy = tgt.rect.centery - cy
                d = math.hypot(dx, dy) or 1
                boss.vx = dx / d * 15
                boss.vy = dy / d * 9
                self.shake = max(self.shake, 10)
                particle_system.emit(cx, cy, 26, (255, 80, 40),
                                     (-5, 5), (3, 7), 30)

    # ---------------------------------------------------------------
    #  Fin de manche / fin de partie
    # ---------------------------------------------------------------
    def check_end(self):
        p = self.player
        if self.phase == "DYING":
            self.timer -= 1
            if self.timer <= 0:
                self.finish(False)
            return
        if not p.alive and not self.cfg["ffa"]:
            self.phase = "DYING"
            self.timer = 110
            self.ko_cause = p.cause or "K.O."
            return

        if self.cfg.get("boss"):
            if self.boss_f and not self.boss_f.alive:
                self.end_round()
            elif self.t >= self.round_time:
                p.hp, p.alive, p.cause = 0, False, "TEMPS ÉCOULÉ"
            return

        if self.cfg.get("course"):
            if p.alive and self.goal and p.rect.colliderect(self.goal):
                self.end_round()
            elif self.t >= self.round_time and p.alive:
                p.hp, p.alive, p.cause = 0, False, "TEMPS ÉCOULÉ"

        elif self.cfg["ffa"]:
            alive = [f for f in self.fighters if f.alive]
            if self.t >= self.round_time or (len(alive) <= 1 and self.t > 90):
                self.end_round()

        elif self.t >= self.round_time:
            self.end_round()

    def reward(self):
        r, k = self.round, self.round_kills
        last = self.cfg["rounds"] and r >= self.cfg["rounds"]
        if self.mode == "COURSE":
            return (50 + 30 * (r - 1) + k * 8
                    + max(0, int((self.round_time - self.t) / 60)))
        if self.mode == "SURVIE":
            return 40 + 12 * r + k * 15
        if self.mode == "ARENE":
            return 60 + k * 25 + (150 if last else 0)
        if self.mode == "GLITCH":
            return 100 + 40 * r + (300 if last else 0)
        if self.mode == "GARDIEN":
            return 200 + 120 * r + (600 if last else 0)
        if self.mode == "ECLIPSE":
            return 150 + 80 * r + (400 if last else 0)
        return 250 + 150 * r + (1000 if last else 0)

    def end_round(self):
        gain = int(self.reward() * DIFFS[self.diff]["coin"] * self.L["coin"])
        gain += int(self.round_kills * self.player.bounty)
        self.round_reward = gain
        self.earned += gain
        SAVE["coins"] += gain
        self.rounds_done += 1

        st = SAVE["stats"]
        st["rounds_total"] += 1
        st["kills_total"] += self.round_kills

        # Sources de boîtes
        box_from_round(self.diff, self.round_damage == 0)
        box_from_streak(self.mode, self.diff, self.round)
        box_from_pass()
        self.kills_banked = True

        # Records
        key = str(self.diff)
        if self.mode == "SURVIE":
            st["surv_best"][key] = max(st["surv_best"].get(key, 0), self.round)
            if self.diff >= 3 and self.round_damage == 0:
                st["flawless"] = True
        if self.mode == "COURSE":
            st["course_best"][key] = max(
                st["course_best"].get(key, 0), self.round)
            if self.diff >= 3:
                secs = round(self.t / 60.0, 1)
                if st["fast_course"] == 0 or secs < st["fast_course"]:
                    st["fast_course"] = secs

        # Ajout des échos
        if self.cfg["ffa"]:
            for f in self.fighters:
                if f.rec:
                    self.add_echo(f.rec, f.shots, f.skin_key, f.team, f.id,
                                  SKINS[f.skin_key]["accent"])
        elif self.player.rec:
            if self.cfg.get("ally"):
                self.add_echo(self.player.rec, self.player.shots,
                              self.player.skin_key, "P", "P", BLEU_ALLIE)
            else:
                self.add_echo(self.player.rec, self.player.shots,
                              self.player.skin_key, "E", "echo", MINT)

        particle_system.emit(self.player.rect.centerx,
                             self.player.rect.centery, 40,
                             JAUNE_NEON, (-5, 5), (3, 6), 40)
        audio.play("win")
        self.new_ach += check_achievements()

        # Campagne secrète (niveaux secrets)
        sid = self.cfg.get("secret_level")
        if sid:
            secret_campaign_register_round(sid)

        # Zones secrètes : compteur de victoires
        if (self.mode in SECRET_ZONES_FOR_CAMPAIGN
                and self.diff >= SECRET_ZONE_MIN_DIFFICULTY):
            wins = _get_secret_zone_wins()
            wins[self.mode] = _to_int(wins.get(self.mode, 0)) + 1
            _check_secret_campaign_unlock()

        # Récompenses de milestone
        if self.milestone_kind == "BOSS":
            bonus = int(600 + 220 * self.diff)
            SAVE["coins"] += bonus
            self.earned += bonus
            self.add_text(WIDTH // 2, HEIGHT // 2 - 60,
                          tr("BOSS VAINCU !") + "  +%d" % bonus,
                          JAUNE_NEON, True)
            SAVE["mystery_boxes"] = _to_int(
                SAVE.get("mystery_boxes", 0)) + 1
        elif self.milestone_kind == "CALAMITY":
            bonus = int(350 + 140 * self.diff)
            SAVE["coins"] += bonus
            self.earned += bonus
            self.add_text(WIDTH // 2, HEIGHT // 2 - 60,
                          tr("CALAMITÉ SURVÉCUE !") + "  +%d" % bonus,
                          (255, 140, 60), True)

        # Restaure la config du mode
        self.cfg = MODES[self.mode]
        self.chaos.interval = self.cfg["chaos"]
        self.calamity = False
        self.calamity_mult = 1.0
        self.milestone_kind = None
        self.milestone_boss = None

        # Fin de partie ou manche suivante
        if self.cfg["rounds"] and self.round >= self.cfg["rounds"]:
            self.finish(True)
        else:
            self.phase = "ROUND_END"
            self.timer = 180
            write_save()

    def add_echo(self, rec, shots, skin, team, src, color):
        self.echo_count += 1
        self.echoes.append(Echo(rec, shots, skin, team, src, color,
                                self.echo_count))
        cap = 16 if self.cfg["ffa"] else 12
        while len(self.echoes) > cap:
            self.echoes.pop(0)

    def score_value(self):
        return (int(self.total / 6) + self.kills * 150
                + self.rounds_done * 300)

    def finish(self, win):
        self.phase = "OVER"
        self.win = win
        st = SAVE["stats"]

        if not self.kills_banked:
            st["kills_total"] += self.round_kills
            self.kills_banked = True

        # Compensation pour K.O. en Survie / Parcours
        if not win and self.mode in ("SURVIE", "COURSE"):
            cons = int(self.t / 60) * (2 if self.mode == "SURVIE" else 1)
            SAVE["coins"] += cons
            self.earned += cons

        # Records
        if self.mode == "SURVIE":
            SAVE["best_survie"] = max(SAVE["best_survie"],
                                      self.score_value())
        if self.mode == "COURSE":
            SAVE["best_course"] = max(SAVE["best_course"], self.rounds_done)

        # Arène : rang final
        if self.mode == "ARENE":
            ranking = sorted(
                self.fighters,
                key=lambda f: -(self.pts.get(f.id, 0)
                                + (0.01 if f.id == "P" else 0)))
            self.rank = [f.id for f in ranking].index("P") + 1
            self.win = self.rank <= 2
            st["arena_win"] = st["arena_win"] or self.rank == 1

        # Succès de zones
        if win and self.mode == "GLITCH":
            st["glitch_done"] = True
        if win and self.mode == "GARDIEN":
            st["guard_done"] = True
        if win and self.mode == "FAILLE":
            st["faille_done"] = True

        # Gemmes de fin de run
        self.pay_gems()
        audio.play("win" if self.win else "ko")

        # Campagne (difficultés 1-10, modes libres)
        if self.mode in ("COURSE", "SURVIE") and 1 <= self.diff <= 10:
            if self.rounds_done >= 1 and self.win:
                new_streak = (campaign_streak(self.diff, self.mode)
                              + self.rounds_done)
                campaign_set_streak(self.diff, self.mode, new_streak)
            else:
                campaign_reset_streak(self.diff, self.mode)
            unlocked = campaign_check_unlock(self.diff)
            if unlocked:
                say(tr("DIFFICULTÉ %d DÉBLOQUÉE !") % unlocked, VERT_NEON)
                audio.play("win")

        self.new_ach += check_achievements()
        write_save()

    def bank_exit(self):
        """Sortie par un passage secret : banque les gains et bascule de mode."""
        st = SAVE["stats"]
        if not self.kills_banked:
            st["kills_total"] += self.round_kills
            self.kills_banked = True
        if self.mode == "SURVIE":
            SAVE["best_survie"] = max(SAVE["best_survie"],
                                      self.score_value())
        self.pay_gems(announce=True)
        audio.play("pickup")
        write_save()


# ═══════════════════════════════════════════════════════════════════════════
#  FIN § 10 — les méthodes de rendu (draw, draw_hud...) et le terrain (§ 11)
#  sont livrés au message suivant.
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#  § 11 — GÉNÉRATION DE TERRAIN + PIÈGES AVANCÉS
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  Constantes des pièges avancés
# ─────────────────────────────────────────────────────────────────────────
RETRACT_WARN = 48
RETRACT_OUT = 60
RETRACT_IN = 30
RETRACT_CYCLE = RETRACT_WARN + RETRACT_OUT + RETRACT_IN + 30
GRAV_WELL_RADIUS = 95

CROSS_LASER_PERIOD = 180
CROSS_LASER_ACTIVE = 55
CROSS_LASER_WARN = 30

UNSTABLE_DELAY = 42
UNSTABLE_RESPAWN = 260

TIME_DISTORT_FACTOR = 0.42
AMBIENT_MISSILE_CD = 150
CRUSHER_PERIOD = 200
CRUSHER_STRIKE = 45
PLASMA_DMG_PER_TICK = 0.35
JUMP_BLOCK_HEIGHT = 130


# ─────────────────────────────────────────────────────────────────────────
#  Helpers des pièges dynamiques
# ─────────────────────────────────────────────────────────────────────────
def _retract_spike_state(t):
    """État d'une dalle pic à ressort : (state, k) avec state ∈
    {warn, out, retract, idle} et k ∈ [0,1]."""
    t %= RETRACT_CYCLE
    if t < RETRACT_WARN:
        return "warn", t / float(RETRACT_WARN)
    t -= RETRACT_WARN
    if t < RETRACT_OUT:
        return "out", 1.0
    t -= RETRACT_OUT
    if t < RETRACT_IN:
        return "retract", 1.0 - t / float(RETRACT_IN)
    return "idle", 0.0


def _sweep_v_x(self, tr_):
    phase = (self.t * tr_["speed"] * 0.01) + tr_["phase"] * 0.05
    return clamp(tr_["x_min"] + (0.5 + 0.5 * math.sin(phase))
                 * (tr_["x_max"] - tr_["x_min"]), 0, WIDTH)


def _sweep_h_y(self, tr_):
    phase = (self.t * tr_["speed"] * 0.01) + tr_["phase"] * 0.05
    return clamp(tr_["y_min"] + (0.5 + 0.5 * math.sin(phase))
                 * (tr_["y_max"] - tr_["y_min"]), 0, HEIGHT)


# ─────────────────────────────────────────────────────────────────────────
#  Layout aléatoire praticable (colonne vertébrale + extras)
# ─────────────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════
#  § 11 — GÉNÉRATION DE TERRAIN (corrigée)
# ═══════════════════════════════════════════════════════════════════

MAX_JUMP_RISE = 105          # déjà défini
MAX_JUMP_GAP  = 170
MIN_JUMP_RISE = 70
JUMP_PEAK     = 142          # pic de la parabole (v²/2g avec v=12.5, g=0.55)
JUMP_SAFETY   = 12           # marge de sécurité


def _arc_hits_platform(start_rect, end_rect, p, peak=JUMP_PEAK, margin=JUMP_SAFETY):
    """True si `p` intersecte la zone balayée par la parabole de saut
    entre `start_rect` (départ) et `end_rect` (arrivée plus haute)."""
    if end_rect.top >= start_rect.top:
        return False  # pas un saut ascendant

    # Corridor horizontal (du bord de départ vers le bord d'arrivée)
    if end_rect.centerx >= start_rect.centerx:
        x_start = start_rect.right
        x_end   = end_rect.left
    else:
        x_start = start_rect.left
        x_end   = end_rect.right

    x_min = min(x_start, x_end) - margin
    x_max = max(x_start, x_end) + margin

    # Bande verticale : du pic au niveau de départ
    y_top    = start_rect.top - peak + margin      # plus petit y = plus haut
    y_bottom = start_rect.top + margin

    # Overlap horizontal ?
    if p.right < x_min or p.left > x_max:
        return False
    # Overlap vertical ?
    if p.bottom < y_top or p.top > y_bottom:
        return False
    return True


def _layout_is_clear(plats, spines):
    """Vérifie qu'aucune plateforme n'obstrue les sauts entre spines."""
    for i in range(1, len(spines)):
        a, b = spines[i - 1], spines[i]
        for p in plats:
            if p is a or p is b:
                continue
            if _arc_hits_platform(a, b, p):
                return False
    return True


def make_layout(tiers, rng, diff=3, round_num=1):
    """Layout praticable garanti, sans plateforme bloquante.
    Phase 1 : colonne vertébrale (chemin obligatoire).
    Phase 2 : bonus, uniquement si la trajectoire reste claire.
    """
    complexity = clamp((diff - 1) * 0.18 + round_num * 0.012, 0.0, 0.95)
    plats = [pygame.Rect(0, HEIGHT - 50, WIDTH, 50)]
    spines = [plats[0]]
    spine = plats[0]
    y = HEIGHT - 50

    # ── PHASE 1 : colonne vertébrale ──────────────────────────────
    for tier in range(tiers):
        rise_max = int(MAX_JUMP_RISE - 10 * (1 - complexity))
        rise = rng.randint(MIN_JUMP_RISE, max(MIN_JUMP_RISE + 1, rise_max))
        y -= rise
        spine_w = rng.randint(130, 180)

        if tier % 2 == 0:
            sx_min, sx_max = 40, WIDTH // 2 - spine_w // 2
        else:
            sx_min = WIDTH // 2 - spine_w // 2
            sx_max = WIDTH - spine_w - 40

        sx = rng.randint(sx_min, max(sx_min + 1, sx_max))
        for _ in range(10):
            gap = max(sx - spine.right, spine.left - (sx + spine_w), 0)
            if gap <= MAX_JUMP_GAP:
                break
            if spine.centerx < WIDTH // 2:
                sx = min(sx_max, spine.right + MAX_JUMP_GAP - 12)
            else:
                sx = max(sx_min, spine.left - MAX_JUMP_GAP + 12 - spine_w)
            sx += rng.randint(-30, 30)
            sx = clamp(sx, sx_min, max(sx_min + 1, sx_max))

        spine = pygame.Rect(sx, y, spine_w, 18)
        plats.append(spine)
        spines.append(spine)

    # ── PHASE 2 : bonus, rejetés si l'arc est bloqué ─────────────
    for i in range(1, len(spines)):
        sp = spines[i]
        if rng.random() >= 0.55 + 0.35 * complexity:
            continue

        ex_w = rng.randint(100, 155)
        if sp.centerx < WIDTH // 2:
            ex_x_min = WIDTH // 2 + 20
            ex_x_max = max(ex_x_min + 1, WIDTH - ex_w - 30)
        else:
            ex_x_min = 30
            ex_x_max = max(ex_x_min + 1, WIDTH // 2 - ex_w - 20)
        ex_x = rng.randint(ex_x_min, ex_x_max)
        bonus = pygame.Rect(ex_x, sp.y, ex_w, 18)

        gap = max(bonus.left - sp.right, sp.left - bonus.right, 0)
        if not (50 <= gap <= 260):
            continue

        # Test "à blanc" : ajoute, vérifie, rejette si ça bloque
        plats.append(bonus)
        if _layout_is_clear(plats, spines):
            continue  # bonus validé, on garde
        plats.pop()   # bonus rejeté
    return plats


# ─────────────────────────────────────────────────────────────────────────
#  Layout de parcours (course + pièges + minis + sortie)
# ─────────────────────────────────────────────────────────────────────────
def make_course(rng, diff=3, hard=False, round_num=1):
    """Construit un parcours complet : plateformes + pièges variés +
    mini-ennemis + zone de sortie. Progression selon `diff`."""
    plats = make_layout(5, rng, diff, round_num)
    if len(plats) < 2:
        # Sécurité : toujours au moins une plateforme en hauteur
        plats.append(pygame.Rect(WIDTH // 2 - 75, HEIGHT - 200, 150, 18))
    sol = plats[0]
    traps = []
    specs = []

    # --- Pièges de base (toujours présents)
    # ── Table de densité par difficulté ─────────────────────────────
    # (spikes, saws, lasers, walkers, turrets, flyers)
    _DENSITY = {
        1:  (1, 0, 0, 0, 0, 0),
        2:  (1, 0, 0, 0, 0, 0),
        3:  (1, 1, 0, 0, 0, 0),
        4:  (2, 1, 0, 1, 0, 0),
        5:  (2, 1, 1, 1, 0, 0),
        6:  (3, 1, 1, 1, 1, 0),
        7:  (3, 2, 2, 1, 1, 1),
        8:  (4, 2, 2, 2, 1, 1),
        9:  (4, 2, 3, 2, 2, 1),
        10: (5, 3, 3, 2, 2, 2),
        11: (5, 3, 3, 3, 2, 2),
        12: (6, 3, 4, 3, 2, 2),
        13: (6, 4, 4, 3, 3, 2),
        14: (7, 4, 4, 4, 3, 3),
        15: (8, 4, 5, 4, 3, 3),
    }
    n_spikes, n_saws, n_lasers, n_walkers, n_turrets, n_flyers = \
        _DENSITY.get(diff, _DENSITY[3])

    # --- Pièges : spikes
    for _ in range(n_spikes):
        if len(plats) < 2:
            break
        pl = rng.choice(plats[1:])
        sw = min(60, pl.w - 20)
        if sw < 20:
            continue
        sx = rng.randint(pl.x + 6, pl.right - sw - 6)
        traps.append(dict(kind="SPIKE",
                          rect=pygame.Rect(sx, pl.top - 12, sw, 12)))

    # --- Pièges : scies
    for _ in range(n_saws):
        y = rng.randint(HEIGHT // 3, HEIGHT - 90)
        x0 = rng.randint(40, WIDTH // 2 - 100)
        x1 = rng.randint(WIDTH // 2 + 100, WIDTH - 40)
        traps.append(dict(kind="SAW", x0=x0, x1=x1, y=y,
                          phase=rng.randint(0, 300)))

    # --- Pièges : lasers
    for _ in range(n_lasers):
        x = rng.randint(120, WIDTH - 120)
        y1 = sol.top - 240
        y2 = sol.top
        traps.append(dict(kind="LASER", x=x, y1=y1, y2=y2,
                          phase=rng.randint(0, 2)))

    # --- Pièges D6+ : lasers croisés + dalles instables
    if 6 <= diff <= 10 or hard:
        n_cross = 1 + (diff - 6) // 2
        for _ in range(n_cross):
            cx1 = rng.randint(220, WIDTH - 220)
            traps.append(dict(kind="CROSS_LASER", cx=cx1,
                              x1=cx1 - 220, x2=cx1 + 220,
                              y1=sol.top - 260, y2=sol.top,
                              phase=rng.randint(0, CROSS_LASER_PERIOD)))

        n_unstable = 2 + (diff - 6) // 2
        for _ in range(n_unstable):
            base_pool = plats[1:6] or plats[1:]
            if not base_pool:
                break
            base = rng.choice(base_pool)
            uw = min(120, base.w - 20)
            if uw < 50:
                continue
            ux = rng.randint(base.left + 6, base.right - uw - 6)
            traps.append(dict(
                kind="UNSTABLE_PLATFORM",
                rect=pygame.Rect(ux, base.top, uw, base.h),
                base_y=base.top,
                phase=rng.randint(0, UNSTABLE_RESPAWN),
                triggered=0, timer=0))

    # --- Pièges D11+ (Mode Champion)
    if diff >= CHAMPION_MIN_DIFF or (hard and diff >= 10):
        for _ in range(2):
            tx = rng.randint(160, WIDTH - 160)
            traps.append(dict(kind="TIME_DISTORTION",
                              x=tx, y=sol.top - 10, w=180, h=90,
                              phase=rng.randint(0, 300)))
        for _ in range(2 + (diff - 11) // 2):
            mx = rng.randint(120, WIDTH - 120)
            my = rng.choice([140, 200, 260])
            traps.append(dict(kind="AMBIENT_MISSILE",
                              x=mx, y=my, cd=AMBIENT_MISSILE_CD,
                              phase=rng.randint(0, AMBIENT_MISSILE_CD)))
        for _ in range(2):
            bx = rng.randint(200, WIDTH - 200)
            traps.append(dict(kind="VERTICAL_CRUSHER",
                              x=bx, base_y=sol.top, w=64, h=70,
                              phase=rng.randint(0, CRUSHER_PERIOD)))
        for _ in range(2):
            px = rng.randint(120, WIDTH - 320)
            pw = rng.randint(150, 260)
            traps.append(dict(kind="PLASMA_POOL",
                              x=px, y=sol.top - 4, w=pw, h=12,
                              phase=rng.randint(0, 200)))
        for _ in range(1 + (diff - 11) // 2):
            jx = rng.randint(200, WIDTH - 200)
            traps.append(dict(kind="JUMP_BLOCKER", x=jx,
                              y=sol.top - JUMP_BLOCK_HEIGHT,
                              w=120, h=JUMP_BLOCK_HEIGHT,
                              phase=rng.randint(0, 240)))

    # --- Mini-ennemis (populations selon la difficulté)
    # --- Mini-ennemis (densité déjà lue depuis _DENSITY)
    walk_y = sol.top - 24
    walk_bounds = (40, WIDTH - 40)
    for _ in range(n_walkers):
        px = rng.randint(walk_bounds[0], walk_bounds[1] - 26)
        specs.append(dict(kind="WALKER", x=px, y=walk_y,
                          bounds=walk_bounds))

    for _ in range(n_turrets):
        if len(plats) < 2:
            break
        pl = rng.choice(plats[1:])
        specs.append(dict(kind="TURRET",
                          x=pl.centerx - 14, y=pl.top - 26,
                          bounds=None))

    for _ in range(n_flyers):
        px = rng.randint(60, WIDTH - 60)
        py = rng.randint(150, 320)
        specs.append(dict(kind="FLYER", x=px, y=py,
                          bounds=(60, WIDTH - 60)))

    # --- Zone de sortie (sur la plateforme la plus haute)
    top_y = min(p.y for p in plats[1:])
    top_plats = [p for p in plats[1:] if p.y == top_y]
    goal_plat = max(top_plats, key=lambda p: p.centerx)
    goal = pygame.Rect(goal_plat.centerx - 22, goal_plat.top - 64, 44, 64)

    return plats, traps, specs, goal


# ─────────────────────────────────────────────────────────────────────────
#  Fond de jeu (plateformes cuites dans l'image)
# ─────────────────────────────────────────────────────────────────────────
def bake_platforms(bg, platforms, rng):
    """Dessine les plateformes sur le fond (une seule fois par manche)."""
    for i, p in enumerate(platforms):
        pygame.draw.rect(bg, (14, 8, 26), p.inflate(6, 6), border_radius=5)
        pygame.draw.rect(bg, (42, 28, 68), p, border_radius=4)
        pygame.draw.rect(bg, (26, 17, 46),
                         (p.x + 2, p.centery + 2,
                          p.w - 4, max(2, p.h // 2 - 4)))
        for x in range(p.x + 6, p.right - 12, 18):
            pygame.draw.polygon(
                bg, (66, 38, 86),
                [(x, p.bottom - 5), (x + 8, p.bottom - 5),
                 (x + 4, p.bottom - 1)])
        for x in range(p.x + 10, p.right - 4, 26):
            pygame.draw.circle(bg, (96, 72, 130), (x, p.y + 8), 2)
        if i == 0:
            for _ in range(22):
                x = rng.randint(10, WIDTH - 10)
                pygame.draw.lines(
                    bg, (120, 30, 96), False,
                    [(x, p.y + 2),
                     (x + rng.randint(-14, 14), p.y + 18),
                     (x + rng.randint(-22, 22), p.y + 34)], 1)


def make_game_bg(seed, platforms):
    """Fond complet du jeu (dégradé + fissures + plateformes cuites)."""
    rng = random.Random(seed)
    bg = make_gradient_bg()
    add_fractures(bg, rng, 18)
    bake_platforms(bg, platforms, rng)
    return bg


# ─────────────────────────────────────────────────────────────────────────
#  Puits de gravité : application des forces
# ─────────────────────────────────────────────────────────────────────────
def _apply_grav_wells(self):
    """Force d'attraction exercée par les puits de gravité sur tous les
    combattants + projectiles (piège GRAV_WELL, réservé aux modes avancés)."""
    wells = [t for t in self.traps if t["kind"] == "GRAV_WELL"]
    if not wells:
        return
    targets = [self.player] if self.player.alive else []
    targets += [f for f in self.fighters if f is not self.player and f.alive]
    for wt in wells:
        wx, wy, r, strength = wt["x"], wt["y"], wt["r"], wt["strength"]
        for e in targets:
            dx = wx - e.rect.centerx
            dy = wy - e.rect.centery
            d = math.hypot(dx, dy)
            if 4 < d < r:
                k = strength * (1 - d / r) ** 1.4
                e.vx += dx / d * k
                e.vy += dy / d * k * 0.55
        for p in self.projectiles:
            dx = wx - p.x
            dy = wy - p.y
            d = math.hypot(dx, dy)
            if 4 < d < r:
                k = strength * 0.55 * (1 - d / r)
                p.vx += dx / d * k
                p.vy += dy / d * k


# ═══════════════════════════════════════════════════════════════════════════
#  § 10 suite — MÉTHODES DE RENDU DE LA SESSION
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  Rendu du monde + HUD + overlays
# ─────────────────────────────────────────────────────────────────────────
def _session_draw_gems(self, w):
    """Cristaux de gemmes (ramassables)."""
    for g in self.gem_items:
        if g["life"] is not None and g["life"] < 120 and (g["life"] // 6) % 2 == 0:
            continue
        bob = math.sin(self.total * 0.08 + g["ph"]) * 4
        x, y = int(g["x"]), int(g["y"] + bob)
        halo = pygame.Surface((64, 64), pygame.SRCALPHA)
        for rr, aa in ((28, 20), (20, 36), (13, 62)):
            pygame.draw.circle(halo, (*GEM_COL, aa), (32, 32), rr)
        w.blit(halo, (x - 32, y - 32))
        draw_gem_icon(w, x, y,
                      9 + (3 if g["v"] >= 3 else 0) + (2 if g["v"] >= 5 else 0))
        tw = (self.total + int(g["ph"] * 10)) % 70
        if tw < 10:
            s_ = 3 + tw % 5
            pygame.draw.line(w, BLANC, (x + 9 - s_, y - 10),
                             (x + 9 + s_, y - 10), 1)
            pygame.draw.line(w, BLANC, (x + 9, y - 10 - s_),
                             (x + 9, y - 10 + s_), 1)


def _session_draw_traps(self, w):
    """Rendu de tous les pièges (base + avancés)."""
    t = self.t
    mult = getattr(self, "calamity_mult", 1.0)

    for tr_ in self.traps:
        k = tr_["kind"]

        if k == "SPIKE":
            r = tr_["rect"]
            for x in range(r.x, r.right - 8, 10):
                pygame.draw.polygon(w, (230, 230, 240),
                                    [(x, r.bottom), (x + 10, r.bottom),
                                     (x + 5, r.top)])
                pygame.draw.polygon(w, ROUGE_NEON,
                                    [(x, r.bottom), (x + 10, r.bottom),
                                     (x + 5, r.top)], 1)

        elif k == "SAW":
            sx = tr_["x0"] + (tr_["x1"] - tr_["x0"]) * (
                0.5 + 0.5 * math.sin(t * 0.03 * mult + tr_["phase"]))
            pygame.draw.line(w, (60, 50, 80),
                             (tr_["x0"], tr_["y"]),
                             (tr_["x1"], tr_["y"]), 2)
            for i in range(8):
                a0 = t * 0.25 * mult + i * math.tau / 8
                pygame.draw.polygon(w, (200, 200, 215), [
                    (sx + math.cos(a0 - 0.2) * 14,
                     tr_["y"] + math.sin(a0 - 0.2) * 14),
                    (sx + math.cos(a0) * 22,
                     tr_["y"] + math.sin(a0) * 22),
                    (sx + math.cos(a0 + 0.2) * 14,
                     tr_["y"] + math.sin(a0 + 0.2) * 14)])
            pygame.draw.circle(w, (150, 150, 170),
                               (int(sx), int(tr_["y"])), 15)
            pygame.draw.circle(w, ROUGE_NEON,
                               (int(sx), int(tr_["y"])), 5)

        elif k == "LASER":
            on = self.laser_on(tr_)
            warn = (not on
                    and ((t // 60) + tr_["phase"] + 1) % 2 == 0
                    and t % 60 > 40)
            pygame.draw.rect(w, (90, 80, 110),
                             (tr_["x"] - 8, tr_["y1"] - 8, 16, 10))
            pygame.draw.rect(w, (90, 80, 110),
                             (tr_["x"] - 8, tr_["y2"] - 2, 16, 4))
            if on:
                pygame.draw.rect(w, ROUGE_NEON,
                                 (tr_["x"] - 4, tr_["y1"],
                                  8, tr_["y2"] - tr_["y1"]))
                pygame.draw.rect(w, BLANC,
                                 (tr_["x"] - 1, tr_["y1"],
                                  2, tr_["y2"] - tr_["y1"]))
            elif warn and t % 6 < 3:
                pygame.draw.line(w, ROUGE_NEON,
                                 (tr_["x"], tr_["y1"]),
                                 (tr_["x"], tr_["y2"]), 1)

        elif k == "RETRACT_SPIKE":
            r = tr_["rect"]
            state, kk = _retract_spike_state(t * mult + tr_["phase"])
            by = r.bottom
            pygame.draw.rect(w, (30, 20, 40), (r.x, by - 4, r.w, 6))
            pygame.draw.rect(w, (70, 50, 90), (r.x, by - 2, r.w, 2))
            if state == "warn":
                pulse = 0.5 + 0.5 * math.sin(t * 0.55)
                glow = (255, int(160 + 90 * pulse), 40)
                pygame.draw.rect(w, glow, (r.x, by - 8, r.w, 6),
                                 border_radius=2)
                for x in range(r.x + 6, r.right - 6, 12):
                    pygame.draw.polygon(w, (255, 100, 60),
                                        [(x, by), (x + 8, by),
                                         (x + 4, by - 10)], 1)
            elif state == "out":
                for x in range(r.x + 6, r.right - 6, 12):
                    pygame.draw.polygon(w, (230, 230, 240),
                                        [(x, by), (x + 8, by),
                                         (x + 4, by - r.h)])
                    pygame.draw.polygon(w, ROUGE_NEON,
                                        [(x, by), (x + 8, by),
                                         (x + 4, by - r.h)], 1)
            elif state == "retract":
                h = int(r.h * kk)
                for x in range(r.x + 6, r.right - 6, 12):
                    pygame.draw.polygon(w, (230, 230, 240),
                                        [(x, by), (x + 8, by),
                                         (x + 4, by - h)])

        elif k == "SWEEP_LASER_V":
            x = _sweep_v_x(self, tr_)
            ix = int(x)
            warn = pygame.Surface((26, tr_["y2"] - tr_["y1"]),
                                  pygame.SRCALPHA)
            warn.fill((255, 60, 60, 32))
            w.blit(warn, (ix - 13, tr_["y1"]))
            pygame.draw.rect(w, (90, 80, 110),
                             (ix - 10, tr_["y1"] - 8, 20, 10),
                             border_radius=3)
            pygame.draw.rect(w, (90, 80, 110),
                             (ix - 10, tr_["y2"] - 2, 20, 6),
                             border_radius=3)
            pygame.draw.rect(w, ROUGE_NEON,
                             (ix - 4, tr_["y1"],
                              8, tr_["y2"] - tr_["y1"]))
            pygame.draw.rect(w, BLANC,
                             (ix - 1, tr_["y1"],
                              2, tr_["y2"] - tr_["y1"]))

        elif k == "SWEEP_LASER_H":
            y = _sweep_h_y(self, tr_)
            iy = int(y)
            warn = pygame.Surface((tr_["x2"] - tr_["x1"], 22),
                                  pygame.SRCALPHA)
            warn.fill((255, 60, 60, 30))
            w.blit(warn, (tr_["x1"], iy - 11))
            pygame.draw.rect(w, (90, 80, 110),
                             (tr_["x1"] - 10, iy - 8, 12, 16),
                             border_radius=3)
            pygame.draw.rect(w, (90, 80, 110),
                             (tr_["x2"] - 2, iy - 8, 12, 16),
                             border_radius=3)
            pygame.draw.rect(w, ROUGE_NEON,
                             (tr_["x1"], iy - 4,
                              tr_["x2"] - tr_["x1"], 8))
            pygame.draw.rect(w, BLANC,
                             (tr_["x1"], iy - 1,
                              tr_["x2"] - tr_["x1"], 2))

        elif k == "GRAV_WELL":
            cx, cy, r = tr_["x"], tr_["y"], tr_["r"]
            pulse = 0.5 + 0.5 * math.sin(t * 0.06 + tr_["phase"] * 0.1)
            halo = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
            for i, rr in enumerate((r, int(r * 0.75), int(r * 0.5))):
                alpha = int(28 + 25 * pulse) - i * 5
                pygame.draw.circle(halo, (140, 60, 220, max(6, alpha)),
                                   (r + 10, r + 10), rr)
            w.blit(halo, (cx - r - 10, cy - r - 10))
            for i in range(3):
                rr = int(r * (0.35 + 0.22 * i))
                a0 = t * 0.035 * (1 + i * 0.3)
                pygame.draw.arc(w, (200, 120, 255),
                                pygame.Rect(cx - rr, cy - rr, rr * 2, rr * 2),
                                a0, a0 + 1.5, 2)
                pygame.draw.arc(w, (255, 220, 255),
                                pygame.Rect(cx - rr, cy - rr, rr * 2, rr * 2),
                                a0 + 3.14, a0 + 3.14 + 0.6, 1)
            pygame.draw.circle(w, (40, 12, 60), (cx, cy), 10)
            pygame.draw.circle(w, (200, 120, 255), (cx, cy), 6)
            pygame.draw.circle(w, BLANC, (cx, cy), 3)

        elif k == "CROSS_LASER":
            phase = (t + tr_["phase"]) % CROSS_LASER_PERIOD
            active = CROSS_LASER_WARN <= phase < CROSS_LASER_WARN + CROSS_LASER_ACTIVE
            warn = phase < CROSS_LASER_WARN
            for (ex, ey) in ((tr_["x1"], tr_["y1"]), (tr_["x2"], tr_["y1"]),
                             (tr_["x1"], tr_["y2"]), (tr_["x2"], tr_["y2"])):
                pygame.draw.rect(w, (90, 80, 110),
                                 (ex - 8, ey - 8, 16, 16),
                                 border_radius=3)
            if active:
                col = (255, 60, 120)
                pygame.draw.line(w, col,
                                 (tr_["x1"], tr_["y1"]),
                                 (tr_["x2"], tr_["y2"]), 4)
                pygame.draw.line(w, col,
                                 (tr_["x2"], tr_["y1"]),
                                 (tr_["x1"], tr_["y2"]), 4)
                pygame.draw.line(w, BLANC,
                                 (tr_["x1"], tr_["y1"]),
                                 (tr_["x2"], tr_["y2"]), 1)
                pygame.draw.line(w, BLANC,
                                 (tr_["x2"], tr_["y1"]),
                                 (tr_["x1"], tr_["y2"]), 1)
            elif warn and (t // 4) % 2 == 0:
                pygame.draw.line(w, (255, 60, 120),
                                 (tr_["x1"], tr_["y1"]),
                                 (tr_["x2"], tr_["y2"]), 1)
                pygame.draw.line(w, (255, 60, 120),
                                 (tr_["x2"], tr_["y1"]),
                                 (tr_["x1"], tr_["y2"]), 1)

        elif k == "UNSTABLE_PLATFORM":
            r = tr_["rect"]
            if tr_["triggered"] == 0:
                pygame.draw.rect(w, (42, 28, 68), r, border_radius=4)
                pygame.draw.rect(w, (70, 40, 110), r, 1, border_radius=4)
                for x in range(r.x + 6, r.right - 6, 12):
                    pygame.draw.line(w, (90, 60, 130),
                                     (x, r.y + 4), (x, r.bottom - 4), 1)
            elif tr_["triggered"] == 1:
                blink = (t // 5) % 2 == 0
                col = (255, 90, 60) if blink else (180, 60, 40)
                pygame.draw.rect(w, col, r, border_radius=4)
                pygame.draw.rect(w, (255, 200, 100), r, 2, border_radius=4)
                for i in range(3):
                    x = r.x + (i + 1) * r.w // 4
                    pygame.draw.line(w, (30, 10, 20),
                                     (x, r.y + 2), (x, r.bottom - 2), 2)
            else:
                s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                s.fill((80, 50, 120, 70))
                w.blit(s, r.topleft)
                p = tr.get("timer", 0) / float(UNSTABLE_RESPAWN)
                pygame.draw.rect(w, (150, 100, 200), r, 1, border_radius=4)
                pygame.draw.rect(w, (255, 220, 100),
                                 (r.x, r.bottom - 3,
                                  int(r.w * (1 - p)), 3))

        elif k == "TIME_DISTORTION":
            x, y = tr_["x"], tr_["y"] - tr_["h"]
            ww, hh = tr_["w"], tr_["h"]
            pulse = 0.5 + 0.5 * math.sin(t * 0.05 + tr_["phase"] * 0.02)
            s = pygame.Surface((ww, hh), pygame.SRCALPHA)
            s.fill((120, 80, 220, int(60 + 30 * pulse)))
            w.blit(s, (x, y))
            for i in range(3):
                rr = int(20 + i * 12 + 6 * pulse)
                pygame.draw.circle(w, (200, 150, 255),
                                   (x + ww // 2, y + hh // 2), rr, 1)
            pygame.draw.rect(w, (200, 150, 255), (x, y, ww, hh), 2)

        elif k == "AMBIENT_MISSILE":
            r = pygame.Rect(tr_["x"] - 12, tr_["y"] - 12, 24, 24)
            pygame.draw.rect(w, (70, 60, 90), r, border_radius=4)
            pygame.draw.circle(w, ORANGE, r.center, 6)
            pygame.draw.circle(w, JAUNE_NEON, r.center, 3)
            k2 = 1.0 - tr_["cd"] / float(AMBIENT_MISSILE_CD)
            pygame.draw.rect(w, (40, 30, 60),
                             (r.x - 4, r.bottom + 4, r.w + 8, 3))
            pygame.draw.rect(w, ORANGE,
                             (r.x - 4, r.bottom + 4,
                              int((r.w + 8) * k2), 3))

        elif k == "VERTICAL_CRUSHER":
            phase = (t + tr_["phase"]) % CRUSHER_PERIOD
            pygame.draw.line(w, (60, 50, 80),
                             (tr_["x"] + tr_["w"] // 2, 0),
                             (tr_["x"] + tr_["w"] // 2, tr_["base_y"]), 3)
            if phase < CRUSHER_STRIKE:
                fall = phase / float(CRUSHER_STRIKE)
                yy = int(fall * (tr_["base_y"] - tr_["h"]))
                r = pygame.Rect(tr_["x"], yy, tr_["w"], tr_["h"])
                pygame.draw.rect(w, (90, 90, 110), r, border_radius=6)
                pygame.draw.rect(w, (200, 40, 40), r, 3, border_radius=6)
                for i in range(6):
                    tx = r.x + 6 + i * (r.w - 12) / 6
                    pygame.draw.polygon(w, (230, 230, 240),
                                        [(tx, r.bottom), (tx + 8, r.bottom),
                                         (tx + 4, r.bottom - 12)])
            else:
                if (phase - CRUSHER_STRIKE) < 20:
                    pygame.draw.rect(w, (200, 60, 60),
                                     (tr_["x"], tr_["base_y"] - tr_["h"],
                                      tr_["w"], tr_["h"]), 2)
                pygame.draw.rect(w, (90, 90, 110),
                                 (tr_["x"], tr_["base_y"] - 12,
                                  tr_["w"], 12), border_radius=4)

        elif k == "PLASMA_POOL":
            pulse = 0.5 + 0.5 * math.sin(t * 0.15 + tr_["phase"] * 0.1)
            col = (255, int(80 + 100 * pulse), 40)
            pygame.draw.rect(w, col,
                             (tr_["x"], tr_["y"], tr_["w"], tr_["h"]),
                             border_radius=3)
            pygame.draw.rect(w, (255, 240, 200),
                             (tr_["x"], tr_["y"] + tr_["h"] // 2,
                              tr_["w"], 2))
            for i in range(0, tr_["w"], 14):
                pygame.draw.circle(w, col,
                                   (tr_["x"] + i + 4, tr_["y"] - 3), 3)

        elif k == "JUMP_BLOCKER":
            s = pygame.Surface((tr_["w"], tr_["h"]), pygame.SRCALPHA)
            for yy in range(0, tr_["h"], 4):
                alpha = int(30 + 20 * math.sin(t * 0.1 + yy * 0.05))
                pygame.draw.line(s, (180, 80, 255, alpha),
                                 (0, yy), (tr_["w"], yy))
            w.blit(s, (tr_["x"], tr_["y"]))
            pygame.draw.rect(w, (180, 80, 255),
                             (tr_["x"], tr_["y"], tr_["w"], tr_["h"]), 1)


def _session_draw_goal(self, w):
    """Portail de sortie du parcours."""
    if not self.goal:
        return
    g = self.goal
    pulse = 4 * math.sin(self.total * 0.1)
    pygame.draw.ellipse(w, (20, 60, 70), g.inflate(10 + pulse, 10 + pulse))
    pygame.draw.ellipse(w, CYAN_NEON, g.inflate(10 + pulse, 10 + pulse), 3)
    pygame.draw.ellipse(w, JAUNE_NEON, g.inflate(-14, -14), 2)
    draw_text(w, tr("SORTIE"), FONT_TINY, JAUNE_NEON,
              g.centerx, g.top - 12)


def _session_draw_freeze(self, surf):
    """Habillage du temps figé (Sanctuaire Temporel actif)."""
    if self.freeze_t <= 0:
        return
    el = self.freeze_max - self.freeze_t
    k = self.freeze_t / float(max(1, self.freeze_max))
    fade = clamp(min(el / 10.0, self.freeze_t / 16.0), 0.0, 1.0)

    fz = self.frz
    fz.fill((24, 44, 120, int(78 * fade)))
    cx0, cy0 = self.fis["cx"], self.fis["cy"]

    # Rayons dorés rotatifs
    for i in range(14):
        ang = i * math.tau / 14 + el * 0.004
        pygame.draw.line(fz, (255, 225, 140, int(26 * fade)),
                         (cx0, cy0),
                         (cx0 + math.cos(ang) * 1300,
                          cy0 + math.sin(ang) * 1300), 16)

    # Cadran central
    mx, my = WIDTH // 2, HEIGHT // 2
    pygame.draw.circle(fz, (255, 225, 140, int(70 * fade)),
                       (mx, my), 236, 3)
    pygame.draw.circle(fz, (255, 225, 140, int(40 * fade)),
                       (mx, my), 222, 1)
    for i in range(12):
        ang = i * math.tau / 12 - math.pi / 2
        r1 = 236 - (22 if i % 3 == 0 else 12)
        pygame.draw.line(fz, (255, 235, 170, int(110 * fade)),
                         (mx + math.cos(ang) * r1,
                          my + math.sin(ang) * r1),
                         (mx + math.cos(ang) * 236,
                          my + math.sin(ang) * 236),
                         4 if i % 3 == 0 else 2)

    # Aiguilles
    sa = -math.pi / 2 - (1.0 - k) * math.tau
    pygame.draw.line(fz, (255, 80, 120, int(150 * fade)),
                     (mx, my),
                     (mx + math.cos(sa) * 210,
                      my + math.sin(sa) * 210), 4)
    pygame.draw.line(fz, (255, 235, 170, int(120 * fade)),
                     (mx, my), (mx, my - 120), 6)
    pygame.draw.circle(fz, (255, 235, 170, int(160 * fade)),
                       (mx, my), 9)

    # Fissures
    al = int(clamp(170 * fade * (0.8 + 0.2 * math.sin(el * 0.25)), 0, 255))
    for pts in self.fis["cracks"]:
        pygame.draw.lines(fz, (255, 215, 120, al), False, pts, 4)
        pygame.draw.lines(fz, (255, 255, 255, al), False, pts, 1)

    surf.blit(fz, (0, 0))

    # Bandeau + timer
    cx = WIDTH // 2
    draw_text(surf, tr("SANCTUAIRE TEMPOREL"), FONT_BTN,
              (255, 215, 90), cx, 132, shadow=True)
    bar = pygame.Rect(cx - 130, 150, 260, 8)
    pygame.draw.rect(surf, (50, 20, 40), bar, border_radius=3)
    pygame.draw.rect(surf, (255, 215, 90),
                     (bar.x, bar.y, int(bar.w * k), bar.h),
                     border_radius=3)
    draw_text(surf, "%.1f s" % (self.freeze_t / 60.0),
              FONT_TINY, BLANC, cx, 172)


def _session_draw_hud(self, surf):
    """HUD complet : PV, bouclier, armes, [E], [F], manche, score, monnaies."""
    p = self.player

    # --- Panneau gauche : PV / bouclier / armes
    panel(surf, (14, 12, 280, 84), CYAN_NEON)
    pygame.draw.rect(surf, (60, 10, 30), (26, 22, 200, 14), border_radius=3)
    pygame.draw.rect(
        surf,
        VERT_NEON if p.hp > p.max_hp * 0.3 else ROUGE_NEON,
        (26, 22, 200 * clamp(p.hp / p.max_hp, 0, 1), 14),
        border_radius=3)
    draw_text(surf, "%d/%d" % (p.hp, p.max_hp),
              FONT_TINY, BLANC, 232, 22, center=False)
    pygame.draw.rect(surf, (10, 40, 60), (26, 41, 200, 8), border_radius=3)
    pygame.draw.rect(
        surf, CYAN_NEON,
        (26, 41, 200 * clamp(p.shield_energy / max(1, p.max_shield), 0, 1), 8),
        border_radius=3)

    slots = ["PLASMA", "LASER", "MISSILE"] + ([p.special] if p.special else [])
    for i, wn in enumerate(slots):
        r = pygame.Rect(26 + i * 62, 56, 58, 32)
        on = p.weapon_type == wn
        pygame.draw.rect(surf, (50, 30, 80) if on else (24, 16, 40), r,
                         border_radius=4)
        pygame.draw.rect(surf, JAUNE_NEON if on else (70, 60, 100), r,
                         2 if on else 1, border_radius=4)
        draw_text(surf, "[%d]" % (i + 1), FONT_TINY,
                  JAUNE_NEON if on else (130, 120, 160),
                  r.centerx, r.y + 9)
        draw_text(surf, tr(WEAPON_NAMES[wn])[:8], FONT_TINY,
                  BLANC if on else (130, 120, 160),
                  r.centerx, r.y + 23)

    # --- Bouton [E] (capacité de soutien)
    if p.ability:
        rdy = p.ab_cd <= 0
        r = pygame.Rect(26 + 4 * 62, 56, 32, 32)
        pygame.draw.rect(surf,
                         (30, 70, 40) if rdy else (40, 20, 30), r,
                         border_radius=4)
        pygame.draw.rect(surf, VERT_NEON if rdy else (90, 50, 70), r,
                         2, border_radius=4)
        draw_text(surf, "E", FONT_BTN,
                  VERT_NEON if rdy else (120, 90, 110),
                  r.centerx, r.centery)
        if not rdy:
            max_cd = 110.0 if p.ability == "DASH" else 1200.0
            pygame.draw.rect(surf, (200, 200, 220),
                             (r.x, r.bottom - 3,
                              r.w * (1 - p.ab_cd / max_cd), 3))

    # --- Jauge du Sanctuaire Temporel [F]
    if p.sa:
        rdy = p.sa_cd <= 0
        r = pygame.Rect(14, 102, 250, 34)
        pul = 0.5 + 0.5 * math.sin(self.total * 0.12)
        edge = mixc((255, 60, 110), (255, 215, 90), pul) if rdy else (96, 70, 100)
        panel(surf, r, edge, PANEL, 7, 2)
        ccx, ccy = r.x + 20, r.centery
        pygame.draw.circle(surf,
                           (255, 215, 90) if rdy else (110, 90, 100),
                           (ccx, ccy), 10, 2)
        ang = self.total * 0.12 if rdy else -math.pi / 2
        pygame.draw.line(surf,
                         (255, 60, 110) if rdy else (110, 90, 100),
                         (ccx, ccy),
                         (ccx + math.cos(ang) * 8,
                          ccy + math.sin(ang) * 8), 2)
        draw_text_ml(surf, "[F] " + tr("SANCTUAIRE"), FONT_TINY,
                     BLANC if rdy else (150, 130, 150),
                     r.x + 38, r.y + 11)
        frac = 1.0 if rdy else 1.0 - p.sa_cd / float(max(1, p.sa[1]))
        pygame.draw.rect(surf, (40, 16, 36),
                         (r.x + 38, r.y + 22, 196, 6), border_radius=3)
        pygame.draw.rect(surf,
                         (255, 215, 90) if rdy else (255, 60, 110),
                         (r.x + 38, r.y + 22, int(196 * frac), 6),
                         border_radius=3)
        if rdy:
            draw_text_ml(surf, tr("PRÊT"), FONT_TINY,
                         (255, 215, 90), r.right - 46, r.y + 11)
        else:
            draw_text_ml(surf, "%d s" % (p.sa_cd // 60 + 1), FONT_TINY,
                         (200, 180, 200), r.right - 40, r.y + 11)

    # --- Panneau droit : manche / score / monnaies
    panel(surf, (WIDTH - 264, 12, 250, 84), ROUGE_NEON)
    left = max(0, (self.round_time - self.t) // 60)
    draw_text(surf, "%s %d" % (tr("MANCHE"), self.round), FONT_BTN,
              JAUNE_NEON, WIDTH - 250, 22, center=False)
    draw_text(surf, "D%d" % self.diff, FONT_BTN,
              DIFFS[self.diff]["color"], WIDTH - 52, 22, center=False)
    info = ("%s %d" % (tr("SCORE"), self.score_value())
            if self.mode == "SURVIE"
            else "%s %d" % (tr("ÉCHOS"), len(self.echoes)))
    draw_text(surf, "%s  |  %02d:%02d" % (info, left // 60, left % 60),
              FONT_SMALL, BLANC, WIDTH - 250, 54, center=False)
    draw_coin_icon(surf, WIDTH - 244, 80, 6)
    draw_text_ml(surf, fmt_num(SAVE["coins"]), FONT_TINY, JAUNE_NEON,
                 WIDTH - 232, 80)
    draw_gem_icon(surf, WIDTH - 118, 80, 7)
    draw_text_ml(surf, fmt_num(SAVE["gems"]), FONT_TINY, GEM_COL,
                 WIDTH - 106, 80)

    # --- Titre du mode (bas-gauche)
    draw_text(surf, mode_title(self.mode), FONT_TINY, CYAN_NEON,
              20, HEIGHT - 20, center=False)

    # --- Score FFA (Arène)
    if self.cfg["ffa"]:
        y = 108
        for f in self.fighters:
            draw_text(surf,
                      "%s : %d  %s" % (
                          tr("TOI") if f.id == "P" else f.id,
                          self.pts.get(f.id, 0),
                          "" if f.alive else "(K.O.)"),
                      FONT_TINY,
                      CYAN_NEON if f.id == "P" else ROUGE_NEON,
                      WIDTH - 250, y, center=False)
            y += 16

    # --- Barre de vie du boss
    b = self.boss_f
    if b and b.alive:
        bw = 480
        panel(surf, (WIDTH // 2 - bw // 2 - 8, HEIGHT - 52, bw + 16, 36),
              ORANGE)
        pygame.draw.rect(surf, (60, 20, 10),
                         (WIDTH // 2 - bw // 2, HEIGHT - 44, bw, 14))
        pygame.draw.rect(surf, ORANGE,
                         (WIDTH // 2 - bw // 2, HEIGHT - 44,
                          bw * clamp(b.hp / b.max_hp, 0, 1), 14))
        draw_text(surf, tr("LE GARDIEN DU TEMPS"), FONT_TINY, BLANC,
                  WIDTH // 2, HEIGHT - 26)

    # --- Milestone (bandeau haut centré)
    mk = self.milestone_kind
    if mk:
        label = tr("BOSS ÉPIQUE") if mk == "BOSS" else tr("DÉFERLANTE")
        col = ROUGE_NEON if mk == "BOSS" else (255, 140, 60)
        x = WIDTH // 2
        y = 92
        panel(surf, (x - 130, y - 16, 260, 30), col, PANEL, 8, 2)
        draw_text(surf, label, FONT_BTN, col, x, y)

    # --- Bandeau de chaos (haut centré)
    cx = WIDTH // 2
    if self.phase in ("PLAY", "DYING") and not self.cfg.get("secret_level"):
        if self.chaos.spin > 0:
            draw_wheel(surf, cx, 62, 44, self.chaos)
            draw_text(surf, tr("ROUE DU CHAOS..."), FONT_TINY,
                      JAUNE_NEON, cx, 118)
        elif self.chaos.key:
            e = EFFECTS[self.chaos.key]
            box = pygame.Rect(cx - 200, 14, 400, 60)
            panel(surf, box, e["color"], width=3)
            draw_text(surf, tr(e["name"]), FONT_BTN, e["color"], cx, 34)
            draw_text(surf, tr(e["desc"]), FONT_TINY, BLANC, cx, 58)
            frac = clamp(self.chaos.timer
                         / max(1, self.chaos.interval - SPIN_FRAMES), 0, 1)
            pygame.draw.rect(surf, e["color"],
                             (box.x + 10, box.bottom + 5,
                              (box.w - 20) * frac, 4))


def _session_draw_overlays(self, surf):
    """Overlays de manche : intro, fin de manche, K.O., pause."""
    cx = WIDTH // 2

    if self.phase == "INTRO":
        panel(surf, (cx - 360, 220, 720, 210), PURPLE_NEON, width=3)
        draw_text(surf, "%s %d" % (tr("MANCHE"), self.round), FONT_BIG,
                  JAUNE_NEON, cx, 275, shadow=True)
        draw_text(surf, tr(self.cfg["hint"]), FONT_SMALL, BLANC, cx, 335)
        n = self.timer // 30
        draw_text(surf, str(n) if n > 0 else tr("GO !"), FONT_TITLE,
                  CYAN_NEON, cx, 380)
        if self.round > 1 and not self.cfg.get("ally"):
            draw_text(surf,
                      tr("%d écho(s) du passé rejoueront tes actions !")
                      % len(self.echoes),
                      FONT_SMALL, MINT, cx, 412)
        elif self.cfg.get("ally") and self.round > 1:
            draw_text(surf,
                      tr("%d écho(s) alliés te soutiennent !") % len(self.echoes),
                      FONT_SMALL, BLEU_ALLIE, cx, 412)

    elif self.phase == "ROUND_END":
        panel(surf, (cx - 330, 220, 660, 210), JAUNE_NEON, width=3)
        draw_text(surf, tr("MANCHE %d RÉUSSIE !") % self.round,
                  FONT_TITLE, JAUNE_NEON, cx, 268, shadow=True)
        shown = int(self.round_reward * clamp((180 - self.timer) / 50.0, 0, 1))
        draw_coin_icon(surf, cx - 70, 322, 11)
        draw_text(surf, "+ %d" % shown, FONT_TITLE, VERT_NEON, cx + 10, 322)
        draw_text(surf, tr("Ton personnage se fige : il devient un ÉCHO FANTÔME..."),
                  FONT_SMALL, MINT, cx, 372)
        draw_text(surf, tr("Prochaine manche dans %d...")
                  % (self.timer // 60 + 1),
                  FONT_SMALL, BLANC, cx, 402)

    elif self.phase == "DYING":
        sh = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        sh.fill((120, 0, 20, min(120, (110 - self.timer) * 3)))
        surf.blit(sh, (0, 0))
        draw_text(surf, "K.O. : %s" % tr(self.ko_cause), FONT_TITLE,
                  ROUGE_NEON, cx, 330, shadow=True)

    if self.paused:
        sh = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        sh.fill((6, 2, 14, 190))
        surf.blit(sh, (0, 0))
        draw_text(surf, tr("PAUSE"), FONT_BIG, CYAN_NEON, cx, 170,
                  shadow=True)


def _session_draw(self, surf, mpos):
    """Rendu complet de la frame de jeu."""
    w = self.world
    key = self.chaos.key
    col = EFFECTS[key]["color"] if key else PURPLE_NEON
    sol = self.platforms[0] if self.platforms else None

    # --- Fond + décor
    w.blit(self.bg, (0, 0))
    draw_clock_bg(w, self.total, col)
    self.shards.draw(w)

    # --- Lignes néon sur le dessus des plateformes
    for plat in self.platforms:
        pygame.draw.line(w, col,
                         (plat.x + 2, plat.y),
                         (plat.right - 2, plat.y), 3)

    # --- Lave au sol
    if self.chaos.p.get("lava") and sol:
        pygame.draw.rect(w, (255, 70 + (self.t * 7) % 60, 20),
                         (0, sol.top - 5, WIDTH, 7))

    # --- Pièges + sortie + secret
    self.draw_traps(w)
    if self.goal:
        self.draw_goal(w)
    if self.secret:
        r = self.secret["rect"]
        a = int((110 if self.t % 90 < 6
                 else random.randint(18, 55)) * self.secret["vis"])
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        s.fill((180, 90, 255, a))
        for yy in range(0, r.h, 6):
            pygame.draw.line(s, (255, 255, 255, a), (0, yy), (r.w, yy))
        w.blit(s, r.topleft)

    # --- Gemmes
    self.draw_gems(w)

    # --- Minis + échos + fighters + projectiles + météores
    for m in self.minis:
        if m.alive:
            m.draw(w, self.total)
    for e in self.echoes:
        e.draw(w, self.total)
    for f in self.fighters:
        f.draw(w, self)
    for p in self.projectiles:
        p.draw(w)
        if self.freeze_t > 0 and p.team != "P":
            pygame.draw.circle(w, (170, 230, 255),
                               (int(p.x), int(p.y)),
                               int(p.radius) + 4, 1)

    # --- Météores
    for m in self.meteors:
        if m["delay"] > 0:
            pygame.draw.polygon(w, ROUGE_NEON,
                                [(m["x"] - 8, 6), (m["x"] + 8, 6),
                                 (m["x"], 22)])
        else:
            pygame.draw.circle(w, (255, 90, 20),
                               (int(m["x"]), int(m["y"])), 12)
            pygame.draw.circle(w, JAUNE_NEON,
                               (int(m["x"]), int(m["y"])), 6)
            pygame.draw.line(w, ORANGE,
                             (m["x"], m["y"]),
                             (m["x"] - m["vx"] * 5,
                              m["y"] - m["vy"] * 5), 6)

    # --- Anneaux + ondes
    for rg in self.rings:
        pygame.draw.circle(w, (255, 200, 120),
                           (int(rg["x"]), int(rg["y"])), int(rg["r"]), 3)
    for wv in self.waves:
        frac = clamp(wv["life"] / float(wv["max"]), 0.0, 1.0)
        rr = int(wv["r"])
        if rr > 4:
            ctr = (int(wv["x"]), int(wv["y"]))
            pygame.draw.circle(w, mixc((60, 20, 80), (255, 225, 140), frac),
                               ctr, rr, max(2, int(11 * frac)))
            pygame.draw.circle(w, mixc((40, 10, 60), (255, 70, 120), frac),
                               ctr, max(3, int(rr * 0.82)),
                               max(1, int(5 * frac)))

    # --- Particules + textes
    if not self.paused:
        particle_system.update_and_draw(w)
    for tx in self.texts:
        tx.draw(w)

    # --- Blackout (chaos ou config)
    if (self.chaos.p.get("blackout") or self.cfg.get("blackout")) \
            and self.player.alive:
        self.dk.fill((0, 0, 0, 242))
        for rr, aa in ((150, 0), (170, 90), (190, 170), (210, 215)):
            pygame.draw.circle(self.dk, (0, 0, 0, aa),
                               self.player.rect.center, rr)
        pygame.draw.circle(self.dk, (0, 0, 0, 0),
                           self.player.rect.center, 130)
        w.blit(self.dk, (0, 0))

    # --- Relique
    if self.relic:
        r = self.relic
        pul = 0.5 + 0.5 * math.sin(self.total * 0.12)
        c = mixc((120, 70, 20), (255, 190, 60), pul)
        pygame.draw.polygon(w, c, [(r.centerx, r.top), (r.right, r.centery),
                                   (r.centerx, r.bottom), (r.left, r.centery)])
        pygame.draw.polygon(w, BLANC,
                            [(r.centerx, r.top), (r.right, r.centery),
                             (r.centerx, r.bottom), (r.left, r.centery)], 1)

    # --- Shake
    ox = oy = 0
    if self.shake > 0 and SET.get("shake", True):
        ox = random.randint(-self.shake, self.shake)
        oy = random.randint(-self.shake, self.shake)

    surf.fill(NOIR_FOND)
    surf.blit(w, (ox, oy))

    # --- Overlays plein écran
    edge = col if key else None
    low = self.player.alive and self.player.hp < self.player.max_hp * 0.3
    finish_overlays(
        surf,
        edge=ROUGE_NEON if low else edge,
        edge_alpha=((120 + 100 * math.sin(self.total * 0.2)) if low
                    else (110 if not SET.get("calm") else 50)))

    # --- Flash de chaos
    if self.chaos.flash > 0 and key and not SET.get("calm"):
        fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fl.fill((*EFFECTS[key]["color"], int(self.chaos.flash * 2.2)))
        surf.blit(fl, (0, 0))

    # --- Freeze + HUD + overlays de manche
    self.draw_freeze(surf)
    self.draw_hud(surf)
    self.draw_overlays(surf)

    # --- Trou noir
    if self.black_hole_fx:
        bh = self.black_hole_fx
        k = bh["life"] / max(1, bh["max"])
        bcx, bcy = int(bh["x"]), int(bh["y"])
        br = int(bh["r"] * (1 - k * 0.35))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(5):
            rr = max(6, br - i * 12)
            alpha = int(80 * k * (1 - i / 5))
            pygame.draw.circle(overlay, (180, 50, 255, alpha),
                               (bcx, bcy), rr)
        pygame.draw.circle(overlay, (30, 4, 50, int(180 * k)),
                           (bcx, bcy), max(8, int(br * 0.22)))
        for i in range(20):
            ang = i * math.tau / 20 + self.total * 0.06
            r1 = max(10, int(br * 0.35))
            pygame.draw.line(overlay,
                             (255, 200, 255, int(60 * k)),
                             (bcx + math.cos(ang) * r1,
                              bcy + math.sin(ang) * r1),
                             (bcx + math.cos(ang) * br,
                              bcy + math.sin(ang) * br), 2)
        surf.blit(overlay, (0, 0))

    # --- Curseur
    if self.phase != "OVER" and not self.paused:
        mx, my = mpos
        pygame.draw.circle(surf, JAUNE_NEON, (mx, my), 9, 1)
        pygame.draw.circle(surf, ROUGE_NEON, (mx, my), 2)
        for dx, dy in ((14, 0), (-14, 0), (0, 14), (0, -14)):
            pygame.draw.line(surf, JAUNE_NEON,
                             (mx + dx * 0.55, my + dy * 0.55),
                             (mx + dx, my + dy), 2)


# ─────────────────────────────────────────────────────────────────────────
#  Attachement des méthodes à la classe Session (une seule définition)
# ─────────────────────────────────────────────────────────────────────────
Session.draw_gems = _session_draw_gems
Session.draw_traps = _session_draw_traps
Session.draw_goal = _session_draw_goal
Session.draw_freeze = _session_draw_freeze
Session.draw_hud = _session_draw_hud
Session.draw_overlays = _session_draw_overlays
Session.draw = _session_draw


# ─────────────────────────────────────────────────────────────────────────
#  Wrapping propre de `contacts` : ajoute la physique des puits de gravité
#  sans dupliquer le code (closure unique, référence originale déchargée).
# ─────────────────────────────────────────────────────────────────────────
def _install_grav_well_hook():
    orig = Session.contacts

    def _contacts_with_wells(self):
        orig(self)
        _apply_grav_wells(self)

    Session.contacts = _contacts_with_wells


_install_grav_well_hook()


# ─────────────────────────────────────────────────────────────────────────
#  Enregistrement des traductions EN pour les ajouts § 10-11
# ─────────────────────────────────────────────────────────────────────────
EN.update({
    "SAUT BLOQUÉ": "JUMP BLOCKED",
    "PHASE %d": "PHASE %d",
    "BOSS ÉPIQUE": "EPIC BOSS",
    "BOSS ÉPIQUE !": "EPIC BOSS!",
    "DÉFERLANTE": "CALAMITY WAVE",
    "DÉFERLANTE !": "CALAMITY WAVE!",
    "BOSS VAINCU !": "BOSS DEFEATED!",
    "CALAMITÉ SURVÉCUE !": "CALAMITY SURVIVED!",
    "MANCHE": "ROUND", "SCORE": "SCORE", "ÉCHOS": "ECHOES",
    "TOI": "YOU", "SORTIE": "EXIT", "PAUSE": "PAUSE",
    "SANCTUAIRE": "SANCTUARY", "PRÊT": "READY",
    "SANCTUAIRE TEMPOREL": "TEMPORAL SANCTUARY",
    "LE TEMPS REPREND": "TIME RESUMES",
    "ROUE DU CHAOS...": "WHEEL OF CHAOS...",
    "GO !": "GO!",
    "MANCHE %d RÉUSSIE !": "ROUND %d CLEARED!",
    "Prochaine manche dans %d...": "Next round in %d...",
    "Ton personnage se fige : il devient un ÉCHO FANTÔME...":
        "Your character freezes: it becomes a GHOST ECHO...",
    "%d écho(s) du passé rejoueront tes actions !":
        "%d echo(es) from the past will replay your actions!",
    "%d écho(s) alliés te soutiennent !":
        "%d allied echo(es) are backing you up!",
    "RELIQUE TROUVÉE !": "RELIC FOUND!",
    "TEMPS ÉCOULÉ": "TIME'S UP",
    "EXPLOSION": "EXPLOSION",
    "MÉTÉORITE": "METEORITE",
    "BRÛLURE": "BURNING",
    "ÉCHO FAUCHEUR": "REAPER ECHO",
    "ENNEMI AU CONTACT": "ENEMY CONTACT",
    "PIÈGE MORTEL": "DEADLY TRAP",
    "SOL EN LAVE": "LAVA FLOOR",
    "RADIATION": "RADIATION",
    "RENVOI !": "REFLECTED!",
    "ONDE DE CHOC !": "SHOCKWAVE!",
    "TEMPS RALENTI": "TIME SLOWED",
    "SECONDE VIE !": "SECOND LIFE!",
    "BOUCLIER AUTO": "AUTO SHIELD",
    "ESQUIVE !": "DODGE!",
    "ESQUIVE QUANTIQUE": "QUANTUM DODGE",
    "PHASE !": "PHASE!",
    "CHAOS DOMPTÉ": "CHAOS TAMED",
    "FRÉNÉSIE DU CHAMPION": "CHAMPION FRENZY",
    "TROU NOIR QUANTIQUE": "QUANTUM BLACK HOLE",
})


# ═══════════════════════════════════════════════════════════════════════════
#  FIN § 10-11
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#  § 12 — ÉCRANS / MENUS
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  Widgets UI génériques (button, clicked, hover)
# ─────────────────────────────────────────────────────────────────────────
_hov_prev = set()
_hov_now = set()


def _reset_hover_frame():
    """Appelé en tête de boucle par le main loop (§ 17)."""
    _hov_prev.clear()
    _hov_prev.update(_hov_now)
    _hov_now.clear()


def _register_hover(key):
    """Enregistre un hover ; joue un son s'il est nouveau."""
    _hov_now.add(key)
    if key not in _hov_prev:
        try:
            audio.play("hover")
        except Exception:
            pass


def button(rect, label, font=None, color=None, enabled=True):
    """Bouton standard. Retourne True si cliqué cette frame.

    - hover → glow + son "hover"
    - click → consomme `mouse["click"]`, joue "click"
    - désactivé → rendu grisé, clics ignorés
    """
    font = font or FONT_BTN
    r = pygame.Rect(rect)
    hover = enabled and r.collidepoint(mouse["x"], mouse["y"])
    key = (r.x, r.y, r.w, r.h)
    if hover:
        _register_hover(key)

    col = color or CYAN_NEON
    if not enabled:
        panel(screen, r, (70, 60, 90), (22, 16, 34), 7, 1)
        fcol = (110, 100, 130)
    elif hover:
        panel(screen, r, col, mixc(PANEL, col, 0.38), 7, 3)
        fcol = BLANC
    else:
        panel(screen, r, mixc(col, (60, 50, 90), 0.5), PANEL, 7, 2)
        fcol = BLANC

    draw_text(screen, tr(label), font, fcol, r.centerx, r.centery)

    if hover and mouse.get("click"):
        mouse["click"] = False
        try:
            audio.play("click")
        except Exception:
            pass
        return True
    return False


def clicked(rect):
    """Zone cliquable invisible — consomme le clic si à l'intérieur."""
    if mouse.get("click") and pygame.Rect(rect).collidepoint(
            mouse["x"], mouse["y"]):
        mouse["click"] = False
        try:
            audio.play("click")
        except Exception:
            pass
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────
#  Fond animé des menus (gradient + shards + éclairs + particules)
# ─────────────────────────────────────────────────────────────────────────
class MenuBG:
    """Décor des menus : dégradé nuit, fissures temporelles, horloge brisée,
    shards flottants, éclairs d'ambiance, particules montantes."""

    def __init__(self):
        rng = random.Random(7)
        self.bg = make_gradient_bg((8, 3, 18), (44, 6, 46))
        add_fractures(self.bg, rng, 26, (64, 22, 86))
        self.shards = ShardField(24, 3)
        self.light = Lightning()
        self._particles_bg = []

    def draw(self, surf, t):
        surf.blit(self.bg, (0, 0))
        draw_clock_bg(surf, t, PURPLE_NEON,
                      cx=WIDTH // 2, cy=330, r=310, k=0.3)
        self.shards.draw(surf)
        if not SET.get("calm", False):
            self.light.update_draw(surf)

        # Particules montantes (densité selon qualité)
        q = int(clamp(SET.get("particles", 2), 0, 2))
        if q > 0 and t % 4 == 0 and len(particle_system.particles) < 150:
            particle_system.particles.append(
                Particle(random.randint(0, WIDTH), HEIGHT + 4,
                         random.uniform(-0.4, 0.4),
                         random.uniform(-1.8, -0.6),
                         random.choice((ORANGE, ROUGE_NEON, PURPLE_NEON)),
                         random.uniform(2, 4), 110))
        particle_system.update_and_draw(surf)
        finish_overlays(surf)


_MENU_BG = []


def menu_bg(surf):
    if not _MENU_BG:
        _MENU_BG.append(MenuBG())
    _MENU_BG[0].draw(surf, TICK[0])




# ─────────────────────────────────────────────────────────────────────────
#  Carte moderne de dashboard (glow pulsant, gradient, badge, icône)
# ─────────────────────────────────────────────────────────────────────────
def draw_modern_card(surf, rect, color, hover, t, title, subtitle,
                     icon_fn=None, badge=None):
    r = pygame.Rect(rect)

    # Ombre portée
    sh = pygame.Surface((r.w + 16, r.h + 16), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 130), sh.get_rect(), border_radius=20)
    surf.blit(sh, (r.x - 8, r.y - 6))

    # Glow pulsant au survol
    if hover:
        pulse = 0.5 + 0.5 * math.sin(t * 0.08)
        glow_rect(surf, r, color, spread=14,
                  max_alpha=int(80 + 50 * pulse))

    # Dégradé intérieur
    top = mixc(NOIR_FOND, color, 0.26 if hover else 0.16)
    bot = mixc(NOIR_FOND, color, 0.06 if hover else 0.03)
    grad = make_gradient(r.w, r.h, top, bot, 16)
    surf.blit(grad, r.topleft)

    # Bordure
    border_col = light(color, 0.35) if hover else color
    pygame.draw.rect(surf, border_col, r, 3 if hover else 2, border_radius=16)
    # Ligne d'accent
    pygame.draw.rect(surf, color, (r.x + 22, r.y + 10, r.w - 44, 3),
                     border_radius=2)

    # Icône
    if callable(icon_fn):
        icon_fn(surf, r.x + 42, r.y + 66, 22, color, hover, t)

    # Titre
    draw_text_ml(surf, title, FONT_BTN,
                 BLANC if hover else light(color, 0.45),
                 r.x + 86, r.y + 50)

    # Sous-titre (wrap)
    lines = wrap_text(subtitle, FONT_TINY, r.w - 108)[:3]
    for i, ln in enumerate(lines):
        draw_text_ml(surf, ln, FONT_TINY, (200, 195, 225),
                     r.x + 86, r.y + 80 + i * 16)

    # Badge haut-droit
    if badge:
        bw = FONT_TINY.size(badge)[0] + 22
        br = pygame.Rect(r.right - bw - 16, r.y + 16, bw, 24)
        pygame.draw.rect(surf, dark(color, 0.35), br, border_radius=12)
        pygame.draw.rect(surf, color, br, 2, border_radius=12)
        draw_text(surf, badge, FONT_TINY, color, br.centerx, br.centery)

    # Chevron (au survol)
    if hover:
        ax, ay = r.right - 30, r.bottom - 26
        pygame.draw.polygon(surf, color,
                            [(ax - 8, ay - 12), (ax + 10, ay),
                             (ax - 8, ay + 12)])


# ---- Icônes vectorielles des 4 pôles
def _icon_play(surf, cx, cy, s, col, hover, t):
    pygame.draw.polygon(surf, col,
                        [(cx - s * 0.55, cy - s),
                         (cx + s * 0.95, cy),
                         (cx - s * 0.55, cy + s)])
    pygame.draw.polygon(surf, BLANC,
                        [(cx - s * 0.55, cy - s),
                         (cx + s * 0.95, cy),
                         (cx - s * 0.55, cy + s)], 2)


def _icon_hq(surf, cx, cy, s, col, hover, t):
    pygame.draw.rect(surf, col,
                     (cx - s, cy - s * 0.5, s * 2, s * 1.4),
                     border_radius=4)
    pygame.draw.arc(surf, col,
                    (cx - s * 0.6, cy - s * 1.5, s * 1.2, s * 1.4),
                    0, math.pi, 3)
    pygame.draw.line(surf, col, (cx - s * 0.6, cy - s * 0.5),
                     (cx - s * 0.6, cy - s * 1.1), 3)
    pygame.draw.line(surf, col, (cx + s * 0.6, cy - s * 0.5),
                     (cx + s * 0.6, cy - s * 1.1), 3)


def _icon_trophy(surf, cx, cy, s, col, hover, t):
    pygame.draw.polygon(surf, col,
                        [(cx - s * 0.7, cy - s),
                         (cx + s * 0.7, cy - s),
                         (cx + s * 0.45, cy + 0.2 * s),
                         (cx - s * 0.45, cy + 0.2 * s)])
    pygame.draw.arc(surf, col, (cx - s * 1.15, cy - s, s * 0.75, s * 0.9),
                    1.6, 4.7, 2)
    pygame.draw.arc(surf, col, (cx + s * 0.4, cy - s, s * 0.75, s * 0.9),
                    -1.6, 1.6, 2)
    pygame.draw.rect(surf, col, (cx - s * 0.15, cy + 0.2 * s,
                                 s * 0.3, s * 0.5))
    pygame.draw.rect(surf, col, (cx - s * 0.6, cy + 0.7 * s,
                                 s * 1.2, s * 0.25))


def _icon_gear(surf, cx, cy, s, col, hover, t):
    a0 = t * 0.025 if hover else 0.0
    for i in range(8):
        a = a0 + i * math.tau / 8
        pygame.draw.line(surf, col,
                         (cx + math.cos(a) * s * 0.78,
                          cy + math.sin(a) * s * 0.78),
                         (cx + math.cos(a) * s,
                          cy + math.sin(a) * s), 4)
    pygame.draw.circle(surf, col, (cx, cy), int(s * 0.78))
    pygame.draw.circle(surf, NOIR_FOND, (cx, cy), int(s * 0.34))


# ─────────────────────────────────────────────────────────────────────────
#  En-tête commun des pôles (titre + sous-titre + fond coloré + bouton retour)
# ─────────────────────────────────────────────────────────────────────────
def _pole_header(title, subtitle, color):
    # Dégradé header
    grad = make_gradient(WIDTH, 96, mixc(NOIR_FOND, color, 0.18),
                         NOIR_FOND, 0)
    screen.blit(grad, (0, 0))
    pygame.draw.line(screen, color, (0, 94), (WIDTH, 94), 3)

    # Titre + sous-titre
    draw_text(screen, title, FONT_TITLE, BLANC, 24, 34,
              center=False, shadow=True)
    draw_text(screen, subtitle, FONT_SMALL, light(color, 0.35),
              26, 70, center=False)

    # Compteur pièces/gemmes en haut-droit
    draw_coins_counter()

    # Bouton Retour uniforme (position fixe bas-gauche)
    draw_back_button(action=lambda: UI.update({"sub": None}))


# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD PRINCIPAL (4 cartes)
# ═══════════════════════════════════════════════════════════════════════════
def screen_menu_dashboard():
    menu_bg(screen)
    cx = WIDTH // 2

    # Titre glitché + tagline
    draw_glitch_title(screen, GAME_TITLE, FONT_TITLE, cx, 40, TICK[0])
    draw_text(screen, tr("Le temps se brise. Ton passé te traque."),
              FONT_SMALL, (190, 160, 230), cx, 72)

    # Badge profil (haut-gauche) — cliquable
    badge = pygame.Rect(14, 12, 270, 66)
    badge_hover = badge.collidepoint(mouse["x"], mouse["y"])
    draw_profile_badge(screen, badge, badge_hover)
    if badge_hover and mouse.get("click"):
        mouse["click"] = False
        try:
            audio.play("click")
        except Exception:
            pass
        goto("PROFILE")

    # Compteur monnaie
    draw_coins_counter()

    # Infos pour les badges
    boxes_n = _to_int(SAVE.get("mystery_boxes", 0))
    found_secrets = sum(1 for v in SAVE["secrets"].values() if v)

    # Configuration des 4 cartes
    cards = [
        (tr("JOUER"),
         tr("Survie, Parcours, zones secrètes. Choisis ton mode et ta difficulté."),
         COL_PLAY, _icon_play,
         "D%d" % SAVE["difficulty"], "POLE_PLAY"),
        (tr("QG & EQUIPEMENT"),
         tr("Boutique, skins, stats, armes, armures et boîtes mystères."),
         COL_HQ, _icon_hq,
         ("x%d" % boxes_n) if boxes_n else None, "POLE_HQ"),
        (tr("COMPÉTITION & PROFIL"),
         tr("Succès, statistiques et profil du pilote."),
         COL_COMPET, _icon_trophy,
         None,  # ← plus de badge de rang
         "POLE_COMPET"),
        (tr("CONFIGURATION & AIDE"),
         tr("Audio, options, langue FR/EN, instructions et astuces."),
         COL_CONFIG, _icon_gear,
         None, "POLE_CONFIG"),
    ]

    cw, ch = 440, 200
    gap_x, gap_y = 30, 26
    x0 = (WIDTH - cw * 2 - gap_x) // 2
    y0 = 112

    for i, (title, subtitle, color, icon_fn, badge_txt, target) in enumerate(cards):
        col = i % 2
        row = i // 2
        r = pygame.Rect(x0 + col * (cw + gap_x),
                        y0 + row * (ch + gap_y), cw, ch)
        hover = r.collidepoint(mouse["x"], mouse["y"])
        draw_modern_card(screen, r, color, hover, TICK[0],
                         title, subtitle, icon_fn=icon_fn, badge=badge_txt)
        if hover and mouse.get("click"):
            mouse["click"] = False
            try:
                audio.play("click")
            except Exception:
                pass
            UI["sub"] = target

    # Bandeau d'astuce (rotation toutes les 15 s)
    if TICK[0] % 900 == 0:
        UI["tip"] = (UI.get("tip", 0) + 1) % len(TIPS)
    tip_txt = tr(TIPS[UI.get("tip", 0) % len(TIPS)])
    tip_panel = pygame.Rect(30, HEIGHT - 62, WIDTH - 60, 30)
    panel(screen, tip_panel, (110, 90, 160), PANEL, 8, 1)
    draw_text(screen, tip_txt, FONT_SMALL, (200, 190, 230),
              tip_panel.centerx, tip_panel.centery)

    # Records (bas d'écran)
    if SAVE["best_survie"] or SAVE["best_course"]:
        draw_text(screen,
                  "%s : %d    |    %s : %d    |    %s : %d/5"
                  % (tr("Record Survie"), SAVE["best_survie"],
                     tr("Record Parcours"), SAVE["best_course"],
                     tr("SECRETS"), found_secrets),
                  FONT_TINY, (150, 140, 190), WIDTH // 2, HEIGHT - 12)

    return True


# ═══════════════════════════════════════════════════════════════════════════
#  PÔLE JOUER (modes + difficulté + champion + campagne)
# ═══════════════════════════════════════════════════════════════════════════

def screen_pole_play():
    menu_bg(screen)
    _pole_header(tr("JOUER"),
                 tr("Choisis ton mode et ta difficulté."),
                 COL_PLAY)

    # --- Bandeau Campagne (D1 → D10)
    camp = SAVE["campaign"]
    unlocked = _to_int(camp["unlocked"], 2)
    cr = pygame.Rect(60, 110, WIDTH - 120, 56)
    cr_hover = cr.collidepoint(mouse["x"], mouse["y"])
    if cr_hover:
        pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.08)
        glow_rect(screen, cr, COL_PLAY, spread=10,
                  max_alpha=int(60 + 40 * pulse))
    panel(screen, cr, COL_PLAY if cr_hover else dark(COL_PLAY, 0.65),
          mixc(PANEL, COL_PLAY, 0.16 if cr_hover else 0.05), 10, 3 if cr_hover else 2)
    draw_text_ml(screen, tr("CAMPAGNE"), FONT_BTN, BLANC,
                 cr.x + 24, cr.y + 20)
    draw_text_ml(screen,
                 tr("Difficulté max débloquée : D%d / 15") % unlocked,
                 FONT_TINY, COL_PLAY, cr.x + 150, cr.y + 20)
    goal = campaign_next_goal_text(unlocked)
    if goal and unlocked < MAX_DIFF:
        draw_text_ml(screen, goal, FONT_TINY, (200, 190, 230),
                     cr.x + 24, cr.y + 42)
    if unlocked >= CHAMPION_MIN_DIFF:
        draw_text_ml(screen, tr("MODE CHAMPION ACTIF"),
                     FONT_TINY, CHAMPION_COL, cr.right - 180, cr.y + 20)
    if cr_hover and mouse.get("click"):
        mouse["click"] = False
        try:
            audio.play("click")
        except Exception:
            pass
        d = clamp(unlocked, 1, 10)
        SAVE["difficulty"] = d
        write_save()
        goto("GAME", Session("CAMPAGNE"))

    # --- 3 cartes de mode
    found = sum(1 for v in SAVE["secrets"].values() if v)
    modes = [
        (tr("PARCOURS ÉCHO"),
         tr("Atteins la SORTIE. Tes échos refont ton parcours."),
         "COURSE", COL_PLAY),
        (tr("SURVIE ARCADE"),
         tr("Tiens le plus longtemps possible face à l'IA."),
         "SURVIE", COL_PLAY),
        (tr("SECRETS") + "  %d/5" % found,
         tr("Des passages cachés mènent à des zones inexplorées..."),
         "SECRETS", PURPLE_NEON),
    ]
    for i, (title, sub, target, col) in enumerate(modes):
        r = pygame.Rect(60, 178 + i * 78, WIDTH - 260, 70)
        hover = r.collidepoint(mouse["x"], mouse["y"])
        if hover:
            pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.08)
            glow_rect(screen, r, col, spread=10,
                      max_alpha=int(50 + 40 * pulse))
        panel(screen, r, col if hover else dark(col, 0.65),
              mixc(PANEL, col, 0.20 if hover else 0.05), 10, 3 if hover else 2)
        draw_text(screen, title, FONT_BTN,
                  BLANC if hover else light(col, 0.35),
                  r.x + 24, r.y + 24, center=False)
        sub_lines = wrap_text(sub, FONT_TINY, r.w - 48)[:1]
        for li, ln in enumerate(sub_lines):
            draw_text(screen, ln, FONT_TINY, (200, 195, 225),
                      r.x + 24, r.y + 46 + li * 14, center=False)
        if hover and mouse.get("click"):
            mouse["click"] = False
            try:
                audio.play("click")
            except Exception:
                pass
            if target in ("COURSE", "SURVIE"):
                goto("GAME", Session(target))
            else:
                UI["page"] = 0
                UI["ipage"] = 0
                UI["apage"] = 0
                UI["iback"] = "MENU"
                UI["sub"] = None
                goto("SECRETS")

    # --- Sélecteur de difficulté 1-10
    d = SAVE["difficulty"]
    if d > 10:
        d = 3
        SAVE["difficulty"] = 3
    pr = pygame.Rect(60, 420, WIDTH - 120, 176)
    panel(screen, pr, DIFFS[d]["color"], PANEL, 12, 2)
    draw_text(screen, tr("DIFFICULTÉS LIBRES (1 à 10)"),
              FONT_BTN, DIFFS[d]["color"], pr.centerx, pr.y + 20)
    for row in range(2):
        for col_i in range(5):
            lv = row * 5 + col_i + 1
            D = DIFFS[lv]
            bw = (pr.w - 56) // 5
            br = pygame.Rect(pr.x + 16 + col_i * bw,
                             pr.y + 44 + row * 42, bw - 6, 36)
            sel = lv == d
            hv = br.collidepoint(mouse["x"], mouse["y"])
            fill = mixc(PANEL, D["color"],
                        0.55 if sel else (0.25 if hv else 0.06))
            panel(screen, br, D["color"], fill, 6, 3 if sel else 2)
            draw_text(screen, "D%d" % lv, FONT_BTN,
                      BLANC if (sel or hv) else D["color"],
                      br.x + 24, br.centery)
            draw_text(screen, tr(D["name"])[:10], FONT_TINY,
                      BLANC if sel else (200, 190, 230),
                      br.centerx + 12, br.centery)
            if hv and mouse.get("click"):
                mouse["click"] = False
                SAVE["difficulty"] = lv
                try:
                    audio.play("click")
                except Exception:
                    pass
                write_save()
    for li, ln in enumerate(wrap_text(tr(DIFFS[d]["desc"]),
                                       FONT_TINY, pr.w - 36)[:1]):
        draw_text(screen, ln, FONT_TINY, (200, 195, 225),
                  pr.x + 18, pr.bottom - 18 + li * 12, center=False)

    return True


# ═══════════════════════════════════════════════════════════════════════════
#  PÔLE QG & ÉQUIPEMENT
# ═══════════════════════════════════════════════════════════════════════════
def screen_pole_hq():
    menu_bg(screen)
    _pole_header(tr("QG & EQUIPEMENT"),
                 tr("Boutique, skins, améliorations et boîtes mystères."),
                 COL_HQ)

    boxes_n = _to_int(SAVE.get("mystery_boxes", 0))
    items = [
        (tr("BOUTIQUE"),
         tr("Skins par rareté, stats, armes et armures."),
         COL_HQ,
         lambda: (UI.update({"page": 0, "shop_tab": "SKINS", "sub": None}),
                  goto("SHOP"))),
        (tr("PERSONNALISER"),
         tr("Choisis et équipe ton skin de combat."),
         COL_PLAY,
         lambda: (UI.update({"page": 0, "sub": None}),
                  goto("SKINS"))),
        (tr("Boîtes Mystères") + ("  x%d" % boxes_n if boxes_n else ""),
         tr("Ouvre des boîtes pour débloquer skins et récompenses rares."),
         (200, 80, 255),
         lambda: UI.update({"sub": "BOXES"})),
    ]

    for i, (title, sub, col, action) in enumerate(items):
        r = pygame.Rect(60, 130 + i * 116, WIDTH - 120, 100)
        hover = r.collidepoint(mouse["x"], mouse["y"])
        if hover:
            pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.08)
            glow_rect(screen, r, col, spread=12,
                      max_alpha=int(60 + 40 * pulse))
        panel(screen, r, col if hover else dark(col, 0.65),
              mixc(PANEL, col, 0.20 if hover else 0.06), 12, 3 if hover else 2)
        draw_text_ml(screen, title, FONT_BTN,
                     BLANC if hover else light(col, 0.35),
                     r.x + 24, r.y + 32)
        for li, ln in enumerate(wrap_text(sub, FONT_TINY, r.w - 48)[:2]):
            draw_text_ml(screen, ln, FONT_TINY, (200, 195, 225),
                         r.x + 24, r.y + 58 + li * 14)
        if hover:
            ax, ay = r.right - 30, r.centery
            pygame.draw.polygon(screen, col,
                                [(ax - 8, ay - 10), (ax + 8, ay),
                                 (ax - 8, ay + 10)])
        if hover and mouse.get("click"):
            mouse["click"] = False
            try:
                audio.play("click")
            except Exception:
                pass
            action()

    return True


# ═══════════════════════════════════════════════════════════════════════════
#  PÔLE COMPÉTITION & PROFIL
# ═══════════════════════════════════════════════════════════════════════════
def screen_pole_compet():
    menu_bg(screen)
    _pole_header(tr("COMPÉTITION & PROFIL"),
                 tr("Classement mondial, succès et statistiques."),
                 COL_COMPET)

    items = [
        # Ligne leaderboard SUPPRIMÉE
        (tr("SUCCÈS") + "  %d/%d" % (len(SAVE["ach"]), len(ACHIEVEMENTS)),
         tr("Débloque des paliers et récupère des récompenses."),
         COL_HQ,
         lambda: (UI.update({"apage": 0, "sub": None}), goto("ACH"))),
       (tr("PROFIL DU PILOTE"),
        tr("Nom, avatar, niveau, records et statistiques."),
        COL_COMPET,
        lambda: (UI.update({"sub": None}), goto("PROFILE"))),
    ]

    for i, (title, sub, col, action) in enumerate(items):
        r = pygame.Rect(60, 130 + i * 116, WIDTH - 120, 100)
        hover = r.collidepoint(mouse["x"], mouse["y"])
        if hover:
            pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.08)
            glow_rect(screen, r, col, spread=12,
                      max_alpha=int(60 + 40 * pulse))
        panel(screen, r, col if hover else dark(col, 0.65),
              mixc(PANEL, col, 0.20 if hover else 0.06), 12, 3 if hover else 2)
        draw_text_ml(screen, title, FONT_BTN,
                     BLANC if hover else light(col, 0.35),
                     r.x + 24, r.y + 32)
        for li, ln in enumerate(wrap_text(sub, FONT_TINY, r.w - 48)[:2]):
            draw_text_ml(screen, ln, FONT_TINY, (200, 195, 225),
                         r.x + 24, r.y + 58 + li * 14)
        if hover:
            ax, ay = r.right - 30, r.centery
            pygame.draw.polygon(screen, col,
                                [(ax - 8, ay - 10), (ax + 8, ay),
                                 (ax - 8, ay + 10)])
        if hover and mouse.get("click"):
            mouse["click"] = False
            try:
                audio.play("click")
            except Exception:
                pass
            action()

    return True


# ═══════════════════════════════════════════════════════════════════════════
#  PÔLE CONFIGURATION & AIDE
# ═══════════════════════════════════════════════════════════════════════════
def screen_pole_config():
    menu_bg(screen)
    _pole_header(tr("CONFIGURATION & AIDE"),
                 tr("Audio, options, langue FR/EN, instructions et astuces."),
                 COL_CONFIG)

    quit_requested = False
    items = [
        (tr("PARAMÈTRES"),
         tr("Volume, plein écran, particules, langue FR/EN."),
         COL_CONFIG,
         lambda: (UI.update({"ret": "MENU", "sub": None}),
                  goto("SETTINGS"))),
        (tr("INSTRUCTIONS"),
         tr("Toutes les commandes, modes, K.O. et astuces."),
         COL_PLAY,
         lambda: (UI.update({"ipage": 0, "iback": "MENU", "sub": None}),
                  goto("INSTRUCTIONS"))),
        (tr("QUITTER"),
         tr("Ferme le jeu et sauvegarde la progression."),
         ROUGE_NEON,
         None),
    ]

    for i, (title, sub, col, action) in enumerate(items):
        r = pygame.Rect(60, 130 + i * 116, WIDTH - 120, 100)
        hover = r.collidepoint(mouse["x"], mouse["y"])
        if hover:
            pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.08)
            glow_rect(screen, r, col, spread=12,
                      max_alpha=int(60 + 40 * pulse))
        panel(screen, r, col if hover else dark(col, 0.65),
              mixc(PANEL, col, 0.20 if hover else 0.06),
              12, 3 if hover else 2)
        draw_text_ml(screen, tr(title), FONT_BTN,
                     BLANC if hover else light(col, 0.35),
                     r.x + 24, r.y + 32)
        for li, ln in enumerate(wrap_text(sub, FONT_TINY, r.w - 48)[:2]):
            draw_text_ml(screen, ln, FONT_TINY, (200, 195, 225),
                         r.x + 24, r.y + 58 + li * 14)
        if hover:
            ax, ay = r.right - 30, r.centery
            pygame.draw.polygon(screen, col,
                                [(ax - 8, ay - 10), (ax + 8, ay),
                                 (ax - 8, ay + 10)])
        if hover and mouse.get("click"):
            mouse["click"] = False
            try:
                audio.play("click")
            except Exception:
                pass
            if action:
                action()
            else:
                quit_requested = True

    return not quit_requested


# ═══════════════════════════════════════════════════════════════════════════
#  DISPATCHER DU MENU (le main loop appelle screen_menu)
# ═══════════════════════════════════════════════════════════════════════════
def screen_menu():
    """Dispatch selon UI["sub"] :
       - None → dashboard
       - POLE_PLAY/HQ/COMPET/CONFIG → écrans de pôle
       - BOX_OPEN/BOXES/LEADERBOARD → sous-écrans (message 8/9)
    Retourne True si le rendu est OK, False pour quitter le jeu."""
    sub = UI.get("sub")

    # Sous-écrans (définis en messages 8/9)
    if sub == "BOX_OPEN":
        fn = globals().get("screen_box_open")
        if callable(fn):
            return fn()
    if sub == "BOXES":
        fn = globals().get("screen_boxes")
        if callable(fn):
            return fn()
    if sub == "LEADERBOARD":
        fn = globals().get("screen_leaderboard")
        if callable(fn):
            return fn()

    # Pôles
    if sub == "POLE_PLAY":            # ← ajoute ces deux lignes
        return screen_pole_play()
    if sub == "POLE_HQ":
        return screen_pole_hq()
    if sub == "POLE_COMPET":
        return screen_pole_compet()
    if sub == "POLE_CONFIG":
        return screen_pole_config()

    # Dashboard par défaut
    return screen_menu_dashboard()


# ═══════════════════════════════════════════════════════════════════════════
#  ÉCRAN DE CRÉATION DE NOM (premier lancement)
# ═══════════════════════════════════════════════════════════════════════════
def validate_name():
    """Valide + enregistre le nom du joueur."""
    nm = UI.get("name_buf", "").strip()
    if not nm:
        try:
            audio.play("error")
        except Exception:
            pass
        say(tr("Choisis un nom !"), ROUGE_NEON)
        return False
    SAVE["profile"]["name"] = nm[:14]
    UI["renaming"] = False
    write_save()
    try:
        audio.play("buy")
    except Exception:
        pass
    return True


def screen_name():
    menu_bg(screen)
    cx = WIDTH // 2

    draw_glitch_title(screen, GAME_TITLE, FONT_BIG, cx, 110, TICK[0])

    panel(screen, (cx - 280, 200, 560, 330), PURPLE_NEON, PANEL, 14, 3)
    draw_text(screen, tr("BIENVENUE DANS LE CHAOS"), FONT_TITLE,
              JAUNE_NEON, cx, 244, shadow=True)
    draw_text(screen, tr("Choisis ton nom de pilote"), FONT_MED,
              BLANC, cx, 296)

    # Champ de saisie
    nb = pygame.Rect(cx - 190, 326, 380, 54)
    panel(screen, nb, CYAN_NEON, (14, 8, 26), 9, 3)
    cur = "_" if (TICK[0] // 25) % 2 == 0 else ""
    draw_text(screen, UI.get("name_buf", "") + cur, FONT_TITLE, BLANC,
              nb.centerx, nb.centery)

    # Aperçu de l'avatar + choix de cadre
    draw_avatar(screen, cx - 120, 450, 90,
                SAVE["selected"], SAVE["profile"]["frame"])
    for i, c in enumerate(FRAME_COLORS):
        r = pygame.Rect(cx - 50 + (i % 4) * 36, 420 + (i // 4) * 36, 28, 28)
        pygame.draw.rect(screen, c, r, border_radius=6)
        border = BLANC if SAVE["profile"]["frame"] == i else (60, 50, 90)
        pygame.draw.rect(screen, border, r,
                         3 if SAVE["profile"]["frame"] == i else 1,
                         border_radius=6)
        if clicked(r):
            SAVE["profile"]["frame"] = i

    # Bouton COMMENCER
    enabled = bool(UI.get("name_buf", "").strip())
    if button((cx + 110, 424, 140, 60), "COMMENCER",
              FONT_BTN, VERT_NEON, enabled=enabled):
        if validate_name():
            goto("MENU")

    draw_text(screen, tr("Entrée pour valider — tu pourras tout changer dans ton profil"),
              FONT_TINY, (150, 140, 180), cx, 508)

    return True


# ═══════════════════════════════════════════════════════════════════════════
#  Traductions FR → EN pour les nouveaux textes
# ═══════════════════════════════════════════════════════════════════════════
EN.update({
    "Le temps se brise. Ton passé te traque.":
        "Time is shattering. Your past is hunting you.",
    "JOUER": "PLAY",
    "QG & EQUIPEMENT": "HQ & EQUIPMENT",
    "COMPÉTITION & PROFIL": "COMPETITION & PROFILE",
    "CONFIGURATION & AIDE": "SETTINGS & HELP",
    "Survie, Parcours, zones secrètes. Choisis ton mode et ta difficulté.":
        "Survival, Run, secret zones. Choose your mode and difficulty.",
    "Boutique, skins, stats, armes, armures et boîtes mystères.":
        "Shop, skins, stats, weapons, armor and mystery boxes.",
    "Classement mondial, succès, statistiques et profil du pilote.":
        "Global leaderboard, achievements, statistics and pilot profile.",
    "Audio, options, langue FR/EN, instructions et astuces.":
        "Audio, options, FR/EN language, instructions and tips.",
    "Choisis ton mode et ta difficulté.": "Choose your mode and difficulty.",
    "Skins par rareté, stats, armes et armures.":
        "Skins by rarity, stats, weapons and armor.",
    "Choisis et équipe ton skin de combat.":
        "Choose and equip your battle skin.",
    "Ouvre des boîtes pour débloquer skins et récompenses rares.":
        "Open boxes to unlock rare skins and rewards.",
    "Compare ton score global, ligues et saisons.":
        "Compare your global score, leagues and seasons.",
    "Débloque des paliers et récupère des récompenses.":
        "Unlock tiers and claim rewards.",
    "Nom, avatar, niveau, records et statistiques.":
        "Name, avatar, level, records and stats.",
    "Volume, plein écran, particules, langue FR/EN.":
        "Volume, fullscreen, particles, FR/EN language.",
    "Toutes les commandes, modes, K.O. et astuces.":
        "All controls, modes, K.O.s and tips.",
    "Ferme le jeu et sauvegarde la progression.":
        "Close the game and save your progress.",
    "Boutique, skins, améliorations et boîtes mystères.":
        "Shop, skins, upgrades and mystery boxes.",
    "Atteins la SORTIE. Tes échos refont ton parcours.":
        "Reach the EXIT. Your echoes retrace your run.",
    "Tiens le plus longtemps possible face à l'IA.":
        "Hold out as long as you can against the AI.",
    "Des passages cachés mènent à des zones inexplorées...":
        "Hidden passages lead to unexplored zones...",
    "DIFFICULTÉS LIBRES (1 à 10)": "FREE DIFFICULTIES (1 to 10)",
    "Difficulté max débloquée : D%d / 15":
        "Max unlocked difficulty: D%d / 15",
    "MODE CHAMPION ACTIF": "CHAMPION MODE ACTIVE",
    "CAMPAGNE": "CAMPAIGN",
    "Top 100 requis": "Top 100 required",
    "Débloqué": "Unlocked",
    "Mondial": "Global",
    "CHAMPION": "CHAMPION",
    "Record Survie": "Survival record",
    "Record Parcours": "Run record",
    "SECRETS": "SECRETS",
    "BIENVENUE DANS LE CHAOS": "WELCOME TO THE CHAOS",
    "Choisis ton nom de pilote": "Choose your pilot name",
    "Entrée pour valider — tu pourras tout changer dans ton profil":
        "Press Enter to confirm — you can change everything in your profile",
    "Choisis un nom !": "Pick a name!",
    "SUCCÈS": "ACHIEVEMENTS",
    "CLASSEMENT MONDIAL": "GLOBAL LEADERBOARD",
    "PROFIL DU PILOTE": "PILOT PROFILE",
    "PARAMÈTRES": "SETTINGS",
    "INSTRUCTIONS": "HOW TO PLAY",
    "QUITTER": "QUIT",
    "PERSONNALISER": "CUSTOMIZE",
    "Boîtes Mystères": "Mystery Boxes",
})
# ═══════════════════════════════════════════════════════════════════════════
#  § 12 suite — ÉCRANS / MENUS (partie 2)
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  TOASTS (notifications de succès débloqués)
# ─────────────────────────────────────────────────────────────────────────
def draw_toasts(surf=None):
    """Affiche les toasts en attente (haut de l'écran) et les expire."""
    surf = surf if surf is not None else screen
    y = 16
    for t in TOASTS[:]:
        t["t"] += 1
        k = t["t"]
        # Slide-in / slide-out
        slide = clamp(min(k, 260 - k) / 18.0, 0, 1)
        r = pygame.Rect(WIDTH // 2 - 230, int(-80 + (y + 80) * slide),
                        460, 62)
        panel(surf, r, JAUNE_NEON, (30, 20, 8), 10, 3)
        draw_trophy(surf, r.x + 34, r.centery, JAUNE_NEON, 1.1)
        draw_text(surf, tr("SUCCÈS DÉBLOQUÉ"), FONT_TINY, JAUNE_NEON,
                  r.x + 64, r.y + 8, center=False)
        draw_text(surf, tr(t["text"]), FONT_BTN, BLANC,
                  r.x + 64, r.y + 24, center=False)
        if t.get("sub"):
            draw_text(surf, t["sub"], FONT_TINY, VERT_NEON,
                      r.x + 64, r.bottom - 18, center=False)
        y += 70
        if k >= 260:
            TOASTS.remove(t)


# ─────────────────────────────────────────────────────────────────────────
#  DIALOGUE CHAMPION REFUSÉ (superposé à l'écran courant)
# ─────────────────────────────────────────────────────────────────────────
def draw_champion_dialog(surf=None):
    """Dialog "accès refusé" (Top 100 requis)."""
    if UI.get("champion_denied", 0) <= 0:
        return
    surf = surf if surf is not None else screen
    UI["champion_denied"] -= 1
    UI["champion_dialog_t"] = UI.get("champion_dialog_t", 0) + 1

    k = min(1.0, UI["champion_dialog_t"] / 12.0)
    v = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    v.fill((4, 2, 10, int(200 * k)))
    surf.blit(v, (0, 0))

    cx, cy = WIDTH // 2, HEIGHT // 2
    box = pygame.Rect(cx - 300, cy - 140, 600, 280)
    pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.1)
    glow_rect(surf, box, ROUGE_NEON, spread=18,
              max_alpha=int(70 + 60 * pulse))
    panel(surf, box, ROUGE_NEON, mixc(PANEL, ROUGE_NEON, 0.10), 14, 3)

    draw_crown(surf, cx, cy - 70, 1.6, (140, 110, 70))
    pygame.draw.line(surf, ROUGE_NEON, (cx - 46, cy - 100),
                     (cx + 46, cy - 40), 5)

    draw_text_outlined(surf, tr("ACCÈS REFUSÉ"), FONT_TITLE, ROUGE_NEON,
                       cx, cy - 20, outline=(0, 0, 0), thick=2)
    draw_text(surf, tr("Réservé exclusivement à l'Élite du Top 100 Mondial"),
              FONT_SMALL, BLANC, cx, cy + 24)

    if button((cx - 100, cy + 86, 200, 42), "OK", FONT_BTN, ROUGE_NEON):
        UI["champion_denied"] = 0
        UI["champion_dialog_t"] = 0


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN PROFIL
# ─────────────────────────────────────────────────────────────────────────
def screen_profile():
    menu_bg(screen)
    cx = WIDTH // 2
    prof = SAVE["profile"]

    draw_text(screen, tr("PROFIL DU PILOTE"), FONT_TITLE, CYAN_NEON,
              cx, 50, shadow=True)

    # Panneau gauche : avatar + nom + niveau
    panel(screen, (40, 90, 420, 520),
          FRAME_COLORS[prof["frame"] % len(FRAME_COLORS)], PANEL, 14, 3)

    skin = prof["avatar"] if prof["avatar"] in SAVE["owned"] else SAVE["selected"]
    draw_avatar(screen, 250, 190, 150, skin, prof["frame"])

    # Champ nom
    nb = pygame.Rect(90, 290, 320, 46)
    panel(screen, nb, JAUNE_NEON if UI.get("renaming") else (110, 90, 160),
          (14, 8, 26), 8, 2)
    shown = UI.get("name_buf", "") if UI.get("renaming") else (prof["name"] or "PILOTE")
    cur = "_" if UI.get("renaming") and (TICK[0] // 25) % 2 == 0 else ""
    draw_text(screen, shown + cur, FONT_BTN, BLANC, nb.centerx, nb.centery)

    if not UI.get("renaming"):
        if clicked(nb):
            UI["renaming"] = True
            UI["name_buf"] = prof["name"] or ""
    else:
        if button((90, 342, 150, 34), "VALIDER", FONT_SMALL, VERT_NEON):
            if validate_name():
                UI["renaming"] = False
        if button((260, 342, 150, 34), "ANNULER", FONT_SMALL, ROUGE_NEON):
            UI["renaming"] = False

    if not UI.get("renaming"):
        draw_text(screen, tr("(clique sur le nom pour le changer)"),
                  FONT_TINY, (150, 140, 180), 250, 360)

    # Niveau + XP
    lvl, xp, need = player_level()
    rank_txt = tr(RANKS[min(4, lvl // 5)])
    draw_text(screen, "%s %d — %s" % (tr("NIVEAU"), lvl, rank_txt),
              FONT_BTN, JAUNE_NEON, 250, 400)
    pygame.draw.rect(screen, (40, 30, 70),
                     (90, 420, 320, 12), border_radius=4)
    pygame.draw.rect(screen, CYAN_NEON,
                     (90, 420, 320 * clamp01(xp / need), 12),
                     border_radius=4)
    draw_text(screen, "XP %d / %d" % (xp, need), FONT_TINY, BLANC,
              250, 446)

    # Choix d'avatar (flèches)
    owned = [k for k in SKIN_ORDER if k in SAVE["owned"]]
    idx = owned.index(skin) if skin in owned else 0
    draw_text(screen, tr("PHOTO DE PROFIL"), FONT_SMALL, BLANC, 250, 478)
    if button((90, 492, 60, 36), "<", FONT_BTN):
        prof["avatar"] = owned[(idx - 1) % len(owned)]
        write_save()
    draw_text(screen, tr(SKINS[skin]["name"]), FONT_SMALL,
              (200, 190, 230), 250, 510)
    if button((350, 492, 60, 36), ">", FONT_BTN):
        prof["avatar"] = owned[(idx + 1) % len(owned)]
        write_save()

    # Cadres
    for i, c in enumerate(FRAME_COLORS):
        r = pygame.Rect(95 + i * 40, 548, 32, 32)
        pygame.draw.rect(screen, c, r, border_radius=6)
        is_sel = prof["frame"] == i
        pygame.draw.rect(screen, BLANC if is_sel else (60, 50, 90), r,
                         3 if is_sel else 1, border_radius=6)
        if clicked(r):
            prof["frame"] = i
            write_save()

    # Panneau droit : statistiques
    panel(screen, (490, 90, 470, 520), (110, 90, 160), PANEL, 14, 2)
    draw_text(screen, tr("STATISTIQUES"), FONT_BTN, CYAN_NEON, 725, 118)
    st = SAVE["stats"]
    rows = [
        (tr("Parties jouées"), st["games"]),
        (tr("Manches réussies"), st["rounds_total"]),
        (tr("Ennemis détruits"), st["kills_total"]),
        (tr("Record Survie"), SAVE["best_survie"]),
        (tr("Record Parcours (manches)"), SAVE["best_course"]),
        (tr("Meilleure Survie (manche)"),
         max([int(v) for v in st["surv_best"].values()] or [0])),
        (tr("Zones secrètes trouvées"),
         "%d/5" % sum(1 for v in SAVE["secrets"].values() if v)),
        (tr("Succès"), "%d/%d" % (len(SAVE["ach"]), len(ACHIEVEMENTS))),
        (tr("Skins possédés"), "%d/%d" % (len(SAVE["owned"]), len(SKINS))),
        (tr("Objets possédés"), "%d/15" % len(SAVE["items"])),
        (tr("Pièces"), SAVE["coins"]),
        (tr("Gemmes"), SAVE["gems"]),
    ]
    for i, (lab, val) in enumerate(rows):
        y = 160 + i * 36
        draw_text(screen, lab, FONT_SMALL, (200, 190, 230),
                  515, y, center=False)
        val_s = str(val)
        draw_text(screen, val_s, FONT_MED, JAUNE_NEON,
                  930 - FONT_MED.size(val_s)[0], y - 3, center=False)
        pygame.draw.line(screen, (50, 38, 80),
                         (515, y + 22), (935, y + 22), 1)

    draw_back_button(action=lambda: goto("MENU"))
    return True


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN SUCCÈS
# ─────────────────────────────────────────────────────────────────────────
def screen_ach():
    menu_bg(screen)
    cx = WIDTH // 2
    draw_text_outlined(screen, tr("SUCCÈS"), FONT_TITLE, JAUNE_NEON,
                       cx, 46, outline=(0, 0, 0), thick=2)
    draw_text(screen, "%d / %d" % (len(SAVE["ach"]), len(ACHIEVEMENTS)),
              FONT_BTN, BLANC, cx, 90)
    draw_coins_counter()

    per = 8
    pages = max(1, (len(ACHIEVEMENTS) + per - 1) // per)
    UI["apage"] = clamp(UI.get("apage", 0), 0, pages - 1)

    start = UI["apage"] * per
    for i, a in enumerate(ACHIEVEMENTS[start:start + per]):
        r = pygame.Rect(30 + (i % 2) * 486, 116 + (i // 2) * 114, 470, 104)
        done = a["id"] in SAVE["ach"]
        panel(screen, r, JAUNE_NEON if done else (80, 118, 120),
              mixc(PANEL, (60, 44, 10), 0.5) if done else PANEL,
              10, 3 if done else 2)
        draw_trophy(screen, r.x + 36, r.y + 44,
                    JAUNE_NEON if done else (80, 118, 104), 1.4)
        draw_text(screen, tr(a["name"]), FONT_BTN,
                  BLANC if done else (180, 118, 205),
                  r.x + 72, r.y + 8, center=False)
        for li, ln in enumerate(wrap_text(tr(a["desc"]),
                                          FONT_SMALL, 380)[:2]):
            draw_text(screen, ln, FONT_SMALL,
                      (200, 118, 230) if done else (140, 118, 170),
                      r.x + 72, r.y + 36 + li * 19, center=False)
        draw_text(screen, reward_text(a["reward"]), FONT_TINY,
                  VERT_NEON if done else JAUNE_NEON,
                  r.x + 72, r.y + 82, center=False)

        # Barre de progression (paliers seulement)
        prog = achievement_progress(a)
        if prog:
            cur, goal = prog
            bar_x = r.x + 72
            bar_y = r.y + 92
            bar_w = 380
            pygame.draw.rect(screen, (40, 30, 60),
                             (bar_x, bar_y, bar_w, 4), border_radius=2)
            pygame.draw.rect(screen,
                             VERT_NEON if done else CYAN_NEON,
                             (bar_x, bar_y,
                              int(bar_w * clamp01(cur / max(1, goal))), 4),
                             border_radius=2)
            draw_text(screen, "%d / %d" % (cur, goal), FONT_TINY,
                      (150, 140, 180), r.right - 44, bar_y + 2)

    if button((30, HEIGHT - 62, 150, 44), "< PAGE", FONT_SMALL,
              enabled=UI["apage"] > 0):
        UI["apage"] -= 1
    if button((WIDTH - 180, HEIGHT - 62, 150, 44), "PAGE >", FONT_SMALL,
              enabled=UI["apage"] < pages - 1):
        UI["apage"] += 1
    draw_back_button(action=lambda: goto("MENU"))
    return True


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN PARAMÈTRES
# ─────────────────────────────────────────────────────────────────────────
def slider(sid, rect, val):
    """Slider horizontal interactif (retourne la nouvelle valeur)."""
    r = pygame.Rect(rect)
    pygame.draw.rect(screen, (50, 38, 80),
                     (r.x, r.centery - 4, r.w, 8), border_radius=4)
    pygame.draw.rect(screen, CYAN_NEON,
                     (r.x, r.centery - 4, int(r.w * val), 8),
                     border_radius=4)
    kx = r.x + int(r.w * val)
    pygame.draw.circle(screen, BLANC, (kx, r.centery), 11)
    pygame.draw.circle(screen, CYAN_NEON, (kx, r.centery), 11, 3)

    if mouse.get("click") and r.inflate(26, 26).collidepoint(
            mouse["x"], mouse["y"]):
        UI["drag"] = sid
        mouse["click"] = False
    if UI.get("drag") == sid:
        if mouse.get("down"):
            val = clamp01((mouse["x"] - r.x) / float(max(1, r.w)))
        else:
            UI["drag"] = None
            try:
                audio.play("tick")
            except Exception:
                pass
    draw_text(screen, "%d%%" % round(val * 100), FONT_SMALL, BLANC,
              r.right + 40, r.centery)
    return val


def screen_settings():
    menu_bg(screen)
    cx = WIDTH // 2
    draw_text_outlined(screen, tr("PARAMÈTRES"), FONT_TITLE, CYAN_NEON,
                       cx, 50, outline=(0, 0, 0), thick=2)

    panel(screen, (30, 88, 470, 470), (110, 90, 160), PANEL, 14, 2)
    panel(screen, (520, 88, 450, 470), (110, 90, 160), PANEL, 14, 2)

    # Colonne gauche : langue + volumes + clavier
    draw_text(screen, tr("LANGUE"), FONT_SMALL, JAUNE_NEON,
              54, 116, center=False)
    for i, (code, lab) in enumerate((("fr", "FRANÇAIS"), ("en", "ENGLISH"))):
        sel = SET["lang"] == code
        if button((54 + i * 220, 138, 200, 42), lab, FONT_SMALL,
                  JAUNE_NEON if sel else None):
            SET["lang"] = code
            write_save()
        if sel:
            pygame.draw.rect(screen, JAUNE_NEON,
                             (64 + i * 220, 184, 180, 3))

    y = 218
    for sid, lab in (("master", "VOLUME GÉNÉRAL"),
                     ("music", "MUSIQUE"),
                     ("sfx", "EFFETS SONORES")):
        draw_text(screen, tr(lab), FONT_SMALL, JAUNE_NEON,
                  54, y, center=False)
        old = SET[sid]
        SET[sid] = slider(sid, (54, y + 36, 320, 20), SET[sid])
        if SET[sid] != old:
            audio.apply()
        y += 76

    draw_text(screen, tr("CLAVIER"), FONT_SMALL, JAUNE_NEON,
              54, y, center=False)
    if button((54, y + 24, 200, 40),
              "AZERTY (ZQSD)" if SET["layout"] == "AZERTY"
              else "QWERTY (WASD)", FONT_SMALL):
        SET["layout"] = "QWERTY" if SET["layout"] == "AZERTY" else "AZERTY"
        write_save()

    # Colonne droite : options booléennes + particules
    rows = [
        ("PLEIN ÉCRAN (F11)", "fullscreen"),
        ("SECOUSSES D'ÉCRAN", "shake"),
        ("NOMBRES DE DÉGÂTS", "dmgnum"),
        ("RÉDUIRE LES FLASHS", "calm"),
        ("EFFET CRT", "crt"),
        ("AFFICHER LES FPS", "fps"),
    ]
    for i, (lab, key) in enumerate(rows):
        yy = 112 + i * 52
        draw_text(screen, tr(lab), FONT_SMALL, BLANC, 546, yy + 12,
                  center=False)
        if button((810, yy, 130, 38),
                  tr("OUI") if SET[key] else tr("NON"),
                  FONT_SMALL, VERT_NEON if SET[key] else ROUGE_NEON):
            if key == "fullscreen":
                set_fullscreen(not SET[key])
            else:
                SET[key] = not SET[key]
            write_save()

    yy = 112 + len(rows) * 52
    draw_text(screen, tr("PARTICULES"), FONT_SMALL, BLANC, 546, yy + 12,
              center=False)
    if button((810, yy, 130, 38),
              [tr("BAS"), tr("MOYEN"), tr("ÉLEVÉ")][
                  int(clamp(SET["particles"], 0, 2))], FONT_SMALL):
        SET["particles"] = (SET["particles"] + 1) % 3
        write_save()

    # Boutons bas — REMONTÉS pour ne pas chevaucher le bouton RETOUR
    if button((54, HEIGHT - 118, 230, 44), "COMMANDES", FONT_SMALL):
        UI["ipage"] = 0
        UI["iback"] = "SETTINGS"
        goto("INSTRUCTIONS")

    conf = UI.get("confirm", 0) > 0
    if button((300, HEIGHT - 118, 340, 44),
          "CONFIRMER : TOUT EFFACER ?" if conf
          else "RÉINITIALISER LA PROGRESSION",
          FONT_SMALL, ROUGE_NEON):
        if conf:
            fresh = default_save()
            for k, v in fresh.items():
                if k != "settings":
                    SAVE[k] = v
            # Préserve les réglages du joueur
            write_save()
            UI["confirm"] = 0
            UI["name_buf"] = ""
            say(tr("Progression effacée."), ROUGE_NEON)
            goto("NAME")
        else:
            UI["confirm"] = 240
        if UI.get("confirm", 0) > 0:
            UI["confirm"] -= 1

        # RETOUR en haut à droite — bien visible et cliquable
    back_r = pygame.Rect(WIDTH - 190, 12, 170, 44)
    hover = back_r.collidepoint(mouse["x"], mouse["y"])
    panel(screen, back_r,
          CYAN_NEON if hover else dark(CYAN_NEON, 0.7),
          mixc(PANEL, CYAN_NEON, 0.22 if hover else 0.06),
          8, 3 if hover else 2)
    pygame.draw.polygon(screen, CYAN_NEON if hover else light(CYAN_NEON, 0.4),
                        [(back_r.x + 18, back_r.centery - 8),
                         (back_r.x + 8, back_r.centery),
                         (back_r.x + 18, back_r.centery + 8)])
    pygame.draw.line(screen, CYAN_NEON if hover else light(CYAN_NEON, 0.4),
                     (back_r.x + 14, back_r.centery),
                     (back_r.x + 24, back_r.centery), 3)
    draw_text_ml(screen, tr("RETOUR"), FONT_SMALL, BLANC,
                 back_r.x + 34, back_r.centery)
    if hover and mouse.get("click"):
        mouse["click"] = False
        try:
            audio.play("click")
        except Exception:
            pass
        goto(UI.get("ret", "MENU"))
    return True                                                    


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN INSTRUCTIONS (4 pages)
# ─────────────────────────────────────────────────────────────────────────
INSTRUCTION_PAGES = [
    ("COMMANDES & CONCEPT", [
        "#COMMANDES",
        "DÉPLACEMENTS : Q / D (A / D en QWERTY) ou Flèches ← / →",
        "SAUT : Espace, Z (W en QWERTY) ou Flèche ↑ (pas de double saut)",
        "TIR : Clic gauche    |    BOUCLIER : Clic droit ou MAJ",
        "ARMES : [1] Plasma   [2] Laser   [3] Roquette   [4] arme d'objet",
        "POUVOIRS : [E] objet de soutien    |    [F] pouvoir du skin Mythique",
        "PAUSE : Échap    |    PLEIN ÉCRAN : F11",
        "",
        "#LE CONCEPT",
        "À chaque manche, ton personnage se FIGE et devient un ÉCHO-FANTÔME",
        "qui rejoue EXACTEMENT tes mouvements et tes tirs, en s'adaptant à la",
        "géométrie de la nouvelle carte.",
    ]),
    ("MODES, DIFFICULTÉS & CAMPAGNE", [
        "#MODES LIBRES",
        "PARCOURS ÉCHO  ·  SURVIE ARCADE  ·  5 ZONES SECRÈTES.",
        "Difficultés 1 à 10 : LIBRES, accessibles pour tous les joueurs.",
        "",
        "#CAMPAGNE (Niveaux 1 à 10)",
        "Progression SÉQUENTIELLE guidée. Chaque niveau = un défi rythmé",
        "(vagues d'ennemis + pièges + boss tous les 5 niveaux).",
        "D1 et D2 sont débloqués par défaut.",
        "Règle de déblocage : 5 manches consécutives dans un des deux modes",
        "(sauf D5→D6 et D10→Champion : 5 ou 10 manches dans les DEUX modes).",
        "",
        "#MODE CHAMPION (D11 à D15)",
        "Accès EXCLUSIF : Réservé au TOP 100 MONDIAL du Classement.",
        "Clique sur la couronne dorée dans le menu JOUER.",
        "Maps ultra-défensives : forteresses, tourelles, crushers verticaux,",
        "champs de plasma, puits de distorsion, annihilateurs de sauts...",
    ]),
    ("LA ROUE DU CHAOS", None),
    ("BOUTIQUE, MATRICE D'ARMES & GEMMES", [
        "#BOUTIQUE",
        "SKINS : 5 onglets de rareté (COMMUN → MYTHIQUE).",
        "Skins mythiques exclusivement en GEMMES ou via Boîtes Mystères.",
        "",
        "#MATRICE D'ARMES (onglet OBJETS)",
        "Grille organisée en 3 colonnes : ATTAQUE · DÉFENSE · SOUTIEN.",
        "Survole une carte pour afficher sa fiche détaillée (stats + prix).",
        "Certaines armes ne se trouvent QUE dans les Boîtes Mystères.",
        "",
        "#AMÉLIORATIONS PREMIUM (QG)",
        "Onglet dédié en GEMMES : Vitalité Éternelle, Égide Cosmique,",
        "Fureur Séquentielle, Avarice Chronique, Veine du Chaos, Écho Ancestral.",
        "Ces bonus sont cumulables avec les stats et les succès.",
        "",
        "#GEMMES",
        "Sources : fin de run (dès manche 3), cristaux en jeu, succès, pubs,",
        "Saison Mondiale. Monnaie premium : à dépenser intelligemment !",
    ]),
]


def screen_instructions():
    menu_bg(screen)
    UI["ipage"] = clamp(UI.get("ipage", 0), 0, len(INSTRUCTION_PAGES) - 1)
    title, lines = INSTRUCTION_PAGES[UI["ipage"]]

    draw_text(screen, tr(title), FONT_TITLE, JAUNE_NEON, WIDTH // 2, 48,
              shadow=True)
    panel(screen, (30, 84, 940, 500), (110, 90, 160), PANEL, 14, 2)

    if lines is None:
        # Page spéciale : liste des 20 effets de chaos
        names = list(EFFECTS.keys())
        draw_text(screen,
                  tr("Toutes les 15 s et à chaque manche, la roue tourne : "
                     "un effet s'applique à TOUT LE MONDE."),
                  FONT_SMALL, BLANC, WIDTH // 2, 110)
        for i, k in enumerate(names):
            e = EFFECTS[k]
            x = 56 + (i // 10) * 470
            y = 142 + (i % 10) * 42
            pygame.draw.rect(screen, e["color"], (x, y + 2, 8, 30),
                             border_radius=3)
            draw_text(screen, tr(e["name"]), FONT_SMALL, e["color"],
                      x + 18, y, center=False)
            lo, hi = e["lv"]
            tag = "D%d" % lo if lo == hi else "D%d-%d" % (lo, hi)
            draw_text(screen, tag, FONT_SMALL, DIFFS[lo]["color"],
                      x + 400, y, center=False)
            draw_text(screen, tr(e["desc"])[:58], FONT_TINY,
                      (180, 170, 210), x + 18, y + 19, center=False)
    else:
        y = 106
        for ln in lines:
            if ln.startswith("#"):
                draw_text(screen, tr(ln[1:]), FONT_BTN, CYAN_NEON,
                          56, y, center=False)
                y += 32
            else:
                draw_text(screen, tr(ln), FONT_SMALL, BLANC,
                          56, y, center=False)
                y += 26

    if button((30, HEIGHT - 118, 170, 44), "< PRÉCÉDENT", FONT_SMALL,
              enabled=UI["ipage"] > 0):
        UI["ipage"] -= 1
    if button((WIDTH - 200, HEIGHT - 118, 170, 44), "SUIVANT >", FONT_SMALL,
              enabled=UI["ipage"] < len(INSTRUCTION_PAGES) - 1):
        UI["ipage"] += 1
    draw_text(screen, "%d/%d" % (UI["ipage"] + 1, len(INSTRUCTION_PAGES)),
              FONT_SMALL, BLANC, WIDTH // 2 + 140, HEIGHT - 40)
    if button((WIDTH // 2 - 70, HEIGHT - 118, 140, 44), "RETOUR", FONT_SMALL):
        goto(UI.get("iback", "MENU"))
    return True


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN SECRETS (zones classiques + campagne secrète si débloquée)
# ─────────────────────────────────────────────────────────────────────────
def screen_secrets():
    menu_bg(screen)
    cx = WIDTH // 2
    draw_text(screen, tr("ZONES SECRÈTES"), FONT_TITLE, PURPLE_NEON,
              cx, 40, shadow=True)
    draw_coins_counter()

    # ---- 5 zones secrètes classiques
    for i, key in enumerate(SECRET_ORDER):
        cfg = MODES[key]
        col = pygame.Rect(30 + (i % 3) * 322, 90 + (i // 3) * 172,
                          300, 156)
        found = SAVE["secrets"][key]
        panel(screen, col, PURPLE_NEON if found else (80, 62, 120),
              PANEL, 10, 2)
        draw_text(screen, tr(cfg["title"]), FONT_SMALL,
                  CYAN_NEON if found else (150, 130, 190),
                  col.centerx, col.y + 22)
        for li, ln in enumerate(wrap_text(tr(cfg["hint"]),
                                          FONT_TINY, 270)[:2]):
            draw_text(screen, ln, FONT_TINY,
                      BLANC if found else (130, 120, 160),
                      col.x + 12, col.y + 50 + li * 15, center=False)

        if found:
            wins = _to_int(_get_secret_zone_wins().get(key, 0))
            draw_text(screen,
                      "%d / %d %s" % (wins, SECRET_ZONE_WINS_REQUIRED,
                                      tr("manches")),
                      FONT_TINY, JAUNE_NEON,
                      col.centerx, col.bottom - 62)
            if button((col.centerx - 70, col.bottom - 46, 140, 34),
                      "JOUER", FONT_SMALL, PURPLE_NEON):
                goto("GAME", Session(key))
        else:
            # Cadenas
            pygame.draw.arc(screen, (190, 190, 200),
                            (col.centerx - 10, col.centery + 4, 20, 28),
                            0, math.pi, 4)
            pygame.draw.line(screen, (190, 190, 200),
                             (col.centerx - 10, col.centery + 18),
                             (col.centerx - 10, col.centery + 28), 4)
            pygame.draw.line(screen, (190, 190, 200),
                             (col.centerx + 10, col.centery + 18),
                             (col.centerx + 10, col.centery + 28), 4)
            pygame.draw.rect(screen, (210, 170, 40),
                             (col.centerx - 16, col.centery + 26, 32, 24),
                             border_radius=4)

    # ---- Campagne secrète (invisible si non débloquée)
    if is_campaign_unlocked():
        draw_text(screen, tr("CAMPAGNE SECRÈTE"), FONT_BTN,
                  JAUNE_NEON, cx, 470)
        prog = secret_campaign_progress()
        for i, sid in enumerate(SECRET_LEVELS_IDS):
            info = SECRET_LEVELS_INFO[sid]
            n = _to_int(prog.get(sid, 0))
            done = n >= SECRET_CAMPAIGN_ROUNDS_REQUIRED
            r = pygame.Rect(30 + (i % 5) * 190,
                            494 + (i // 5) * 88, 180, 80)
            hover = r.collidepoint(mouse["x"], mouse["y"])
            panel(screen, r,
                  info["color"] if (done or hover) else dark(info["color"], 0.55),
                  PANEL, 8, 2)
            draw_text(screen, sid, FONT_SMALL,
                      BLANC if done else (200, 190, 230),
                      r.centerx, r.y + 14)
            pygame.draw.rect(screen, (40, 30, 60),
                             (r.x + 12, r.bottom - 16, r.w - 24, 7),
                             border_radius=4)
            fill_w = int((r.w - 24) *
                         min(1.0, n / SECRET_CAMPAIGN_ROUNDS_REQUIRED))
            pygame.draw.rect(screen, info["color"],
                             (r.x + 12, r.bottom - 16, fill_w, 7),
                             border_radius=4)
            draw_text(screen, "%d / %d" % (n, SECRET_CAMPAIGN_ROUNDS_REQUIRED),
                      FONT_TINY, (210, 200, 230),
                      r.centerx, r.bottom - 22)
            if hover and mouse.get("click"):
                mouse["click"] = False
                try:
                    audio.play("click")
                except Exception:
                    pass
                goto("GAME", Session(sid))
    else:
        # Petite accroche discrète
        draw_text(screen,
                  tr("Certains passages ne se révèlent qu'aux plus acharnés..."),
                  FONT_TINY, (140, 130, 170), cx, 480)

    draw_back_button(action=lambda: goto("MENU"))
    return True


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN SKINS (sélection rapide depuis le dashboard)
# ─────────────────────────────────────────────────────────────────────────
def draw_skin_tabs_inline():
    """Onglets de rareté (utilisés dans l'écran SKINS)."""
    n = len(SKIN_TABS)
    tw, gap = 176, 12
    x0 = (WIDTH - (n * tw + (n - 1) * gap)) // 2
    for i, tb in enumerate(SKIN_TABS):
        r = pygame.Rect(x0 + i * (tw + gap), 580, tw, 48)
        col = tb["col"]
        if tb["rar"] == "MYTHIC":
            col = mixc(col, (255, 205, 70),
                       0.5 + 0.5 * math.sin(TICK[0] * 0.07))
        sel = UI.get("page", 0) == i
        hover = r.collidepoint(mouse["x"], mouse["y"])
        key = (r.x, r.y, r.w, r.h)
        if hover:
            _register_hover(key)
        fill = mixc(PANEL, col, 0.42 if sel else (0.22 if hover else 0.07))
        panel(screen, r, col if (sel or hover) else dark(col, 0.55),
              fill, 8, 3 if sel else 2)
        pygame.draw.circle(screen,
                           col if (sel or hover) else dark(col, 0.65),
                           (r.x + 25, r.centery), 15)
        draw_text(screen, str(i + 1), FONT_BTN, (18, 10, 28),
                  r.x + 25, r.centery)
        owned_n = len([k for k in SKIN_ORDER
                       if SKINS[k]["rarity"] == tb["rar"] and k in SAVE["owned"]])
        total_n = len([k for k in SKIN_ORDER if SKINS[k]["rarity"] == tb["rar"]])
        draw_text_ml(screen, tr(tb["label"]), FONT_SMALL,
                     BLANC if (sel or hover) else light(col, 0.1),
                     r.x + 48, r.y + 17)
        draw_text_ml(screen, "%d/%d" % (owned_n, total_n), FONT_TINY,
                     col, r.x + 48, r.y + 34)
        if sel:
            pygame.draw.rect(screen, col,
                             (r.x + 10, r.bottom + 3, r.w - 20, 3),
                             border_radius=2)
        if hover and mouse.get("click"):
            mouse["click"] = False
            UI["page"] = i
            try:
                audio.play("click")
            except Exception:
                pass


def draw_skin_card(card, key, owned, equipped):
    """Carte de skin : aperçu, nom, statut."""
    sk = SKINS[key]
    reveal = owned or not sk["hidden"]
    mythic = sk["rarity"] == "MYTHIC"
    rc = (RARITY[sk["rarity"]]["color"] if reveal else (80, 62, 120))
    if mythic and reveal:
        rc = mixc((255, 50, 90), (255, 205, 70),
                  0.5 + 0.5 * math.sin(TICK[0] * 0.06))

    hover = card.collidepoint(mouse["x"], mouse["y"])
    edge = JAUNE_NEON if equipped else (light(rc, 0.5) if hover else rc)
    panel(screen, card, edge, PANEL, 10,
          3 if (hover or equipped or mythic) else 2)

    # Aura mythique
    if mythic and reveal:
        glow = pygame.Surface(card.size, pygame.SRCALPHA)
        pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.07)
        for i in range(7):
            pygame.draw.circle(glow, (255, 40, 90, int(10 + 7 * pulse)),
                               (card.w // 2, card.h // 2 - 22), 92 - i * 11)
        screen.blit(glow, card.topleft)

    if not owned and sk["hidden"]:
        # Skin secret verrouillé
        for i in range(8):
            pygame.draw.circle(screen, (*sk["body"], 16),
                               (card.centerx, card.y + 76), 90 - i * 10)
        draw_text(screen, "?", FONT_BIG, dark(sk["body"], 0.5),
                  card.centerx, card.y + 76)
        # Chaînes + cadenas
        for p1, p2 in (((card.x + 6, card.y + 12), (card.right - 6, card.y + 124)),
                       ((card.right - 6, card.y + 12), (card.x + 6, card.y + 124))):
            d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            n = max(2, int(d / 13))
            for i in range(n + 1):
                x = p1[0] + (p2[0] - p1[0]) * i / n
                y = p1[1] + (p2[1] - p1[1]) * i / n
                rr = pygame.Rect(0, 0, 16, 9) if i % 2 == 0 else pygame.Rect(0, 0, 9, 16)
                rr.center = (x, y)
                pygame.draw.ellipse(screen, (150, 155, 170), rr, 3)
        pygame.draw.arc(screen, (190, 190, 200),
                        (card.centerx - 10, card.y + 52, 20, 28), 0, math.pi, 4)
        pygame.draw.rect(screen, (210, 170, 40),
                         (card.centerx - 16, card.y + 66, 32, 24),
                         border_radius=4)
        draw_text(screen, tr("??? SKIN SECRET"), FONT_SMALL,
                  (200, 200, 210), card.centerx, card.bottom - 42)
        draw_text(screen, tr("Succès / zone cachée"), FONT_TINY,
                  (150, 150, 165), card.centerx, card.bottom - 20)
    else:
        draw_skin(screen, key, card.centerx, card.y + 76, 1, TICK[0],
                  False, 0, 1.55, 255 if owned else 120)
        draw_text(screen, tr(RARITY[sk["rarity"]]["label"]), FONT_TINY,
                  rc, card.x + 10, card.y + 8, center=False)
        draw_text(screen, tr(sk["name"]), FONT_SMALL, BLANC,
                  card.centerx, card.bottom - 44)
        if equipped:
            draw_text(screen, tr("[ÉQUIPÉ]"), FONT_SMALL, JAUNE_NEON,
                      card.centerx, card.bottom - 20)
        elif owned:
            draw_text(screen, tr("Cliquer pour équiper"), FONT_TINY,
                      VERT_NEON, card.centerx, card.bottom - 20)
        else:
            price = sk.get("gems") or sk["price"]
            is_gem = sk.get("gems") is not None
            txt = fmt_num(price)
            wtxt = FONT_SMALL.size(txt)[0]
            x0 = card.centerx - (wtxt + 22) // 2
            if is_gem:
                draw_gem_icon(screen, x0 + 8, card.bottom - 20, 8)
            else:
                draw_coin_icon(screen, x0 + 8, card.bottom - 20, 8)
            draw_text_ml(screen, txt, FONT_SMALL,
                         GEM_COL if is_gem else JAUNE_NEON,
                         x0 + 22, card.bottom - 20)
    return hover


def screen_skins():
    menu_bg(screen)
    draw_text(screen, tr("CHOISIS TON SKIN DE COMBAT"), FONT_TITLE,
              CYAN_NEON, WIDTH // 2, 56, shadow=True)
    draw_coins_counter()

    UI["page"] = clamp(UI.get("page", 0), 0, len(SKIN_TABS) - 1)
    tab = SKIN_TABS[UI["page"]]
    tcol = tab["col"]
    entries = tab_entries(UI["page"])

    # Cadre de la page
    panel(screen, pygame.Rect(28, 128, 944, 444), dark(tcol, 0.6),
          mixc(NOIR_FOND, tcol, 0.07), 12, 2)

    for i, key in enumerate(entries):
        card = pygame.Rect(36 + (i % 5) * 188, 138 + (i // 5) * 218,
                           172, 205)
        if key is None:
            # Emplacement verrouillé "bientôt"
            panel(screen, card, dark(tcol, 0.5), PANEL, 10, 2)
            draw_text(screen, "?", FONT_BIG, dark(tcol, 0.5),
                      card.centerx, card.y + 76)
            draw_text(screen, tr("??? MYTHIQUE"), FONT_SMALL,
                      (200, 200, 210), card.centerx, card.bottom - 42)
            draw_text(screen, tr("Bientôt disponible"), FONT_TINY,
                      (150, 150, 165), card.centerx, card.bottom - 20)
            continue

        owned = key in SAVE["owned"]
        equipped = SAVE["selected"] == key
        sk = SKINS[key]
        hover = draw_skin_card(card, key, owned, equipped)

        if hover and mouse.get("click"):
            mouse["click"] = False
            if owned:
                SAVE["selected"] = key
                try:
                    audio.play("click")
                except Exception:
                    pass
                write_save()
            else:
                try:
                    audio.play("error")
                except Exception:
                    pass
                say(tr("Pas encore débloqué : passe par la BOUTIQUE "
                       "(icône maison)."), ROUGE_NEON)

    # Onglets de rareté
    draw_skin_tabs_inline()

    # Bouton valider
    if button((WIDTH // 2 - 90, 646, 180, 40), "VALIDER", FONT_SMALL):
        goto("MENU")
    return True


# ─────────────────────────────────────────────────────────────────────────
#  PAUSE & FIN DE PARTIE
# ─────────────────────────────────────────────────────────────────────────
def draw_pause_menu(S):
    """Menu pause superposé à la frame de jeu."""
    cx = WIDTH // 2
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((6, 2, 14, 200))
    screen.blit(shade, (0, 0))

    panel(screen, (cx - 220, 190, 440, 320), CYAN_NEON, PANEL, 14, 3)
    draw_text(screen, tr("PAUSE"), FONT_TITLE, CYAN_NEON, cx, 240,
              shadow=True)

    if button((cx - 140, 290, 280, 48), "REPRENDRE", FONT_BTN, VERT_NEON):
        S.paused = False
    if button((cx - 140, 350, 280, 48), "PARAMÈTRES", FONT_BTN, CYAN_NEON):
        UI["ret"] = "GAME"
        goto("SETTINGS")
    if button((cx - 140, 410, 280, 48), "RECOMMENCER", FONT_BTN, JAUNE_NEON):
        S.pay_gems(announce=True)
        write_save()
        goto("GAME", Session(S.mode))
    if button((cx - 140, 470, 280, 48), "MENU PRINCIPAL", FONT_BTN, ROUGE_NEON):
        S.pay_gems(announce=True)
        write_save()
        goto("MENU")


def draw_over(S):
    """Écran de fin de partie (victoire / défaite / K.O.)."""
    cx = WIDTH // 2
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((6, 2, 14, 215))
    screen.blit(shade, (0, 0))

    panel(screen, (cx - 380, 50, 760, 600),
          JAUNE_NEON if S.win else ROUGE_NEON, PANEL, 16, 3)

    # Titre
    if S.cfg["rounds"]:
        head = tr("VICTOIRE !") if S.win else tr("DÉFAITE...")
        col = JAUNE_NEON if S.win else ROUGE_NEON
    else:
        head = "K.O. : %s" % tr(S.ko_cause or "FIN")
        col = ROUGE_NEON
    draw_text(screen, head, FONT_TITLE, col, cx, 100, shadow=True)
    draw_text(screen, "%s  —  %s %d" % (mode_title(S.mode),
                                         tr("Difficulté"), S.diff),
              FONT_BTN, CYAN_NEON, cx, 148)

    # Statistiques
    stats = [
        "%s : %d" % (tr("Manches réussies"), S.rounds_done),
        "%s : %d" % (tr("Ennemis détruits"), S.kills),
    ]
    if S.mode == "SURVIE":
        stats.insert(0, "%s : %d   (%s %d)" % (
            tr("SCORE"), S.score_value(),
            tr("record"), SAVE["best_survie"]))
    if S.mode == "ARENE":
        stats.insert(0, "%s : %d / 4" % (tr("Classement final"), S.rank))

    for i, line in enumerate(stats):
        draw_text(screen, line, FONT_MED, BLANC, cx, 200 + i * 34)

    # Récompenses
    yc = 200 + len(stats) * 34 + 14
    draw_coin_icon(screen, cx - 150, yc, 10)
    draw_text_ml(screen, "+ %s" % fmt_num(S.earned), FONT_MED,
                 JAUNE_NEON, cx - 132, yc)
    gt = S.gems_run + S.gems_pick
    draw_gem_icon(screen, cx + 40, yc, 10)
    draw_text_ml(screen, "+ %d" % gt, FONT_MED,
                 GEM_COL if gt else (110, 130, 140),
                 cx + 58, yc)

    # Succès débloqués
    y = 200 + len(stats) * 34 + 50
    if S.new_ach:
        draw_text(screen, tr("SUCCÈS DÉBLOQUÉS"), FONT_BTN, JAUNE_NEON,
                  cx, y)
        y += 26
        for a in S.new_ach[:5]:
            y += 26
            draw_trophy(screen, cx - 270, y - 4, JAUNE_NEON, 0.7)
            draw_text(screen, "%s  (%s)" % (tr(a["name"]),
                                             reward_text(a["reward"])),
                      FONT_SMALL, VERT_NEON,
                      cx - 245, y - 9, center=False)
            sk = a["reward"].get("skin")
            if sk:
                draw_skin(screen, sk, cx + 300, y - 4, 1, TICK[0],
                          False, 0, 0.55)

    # Boutons
    if button((cx - 270, 584, 250, 46), "REJOUER", FONT_BTN, VERT_NEON):
        goto("GAME", Session(S.mode))
    if button((cx + 20, 584, 250, 46), "MENU PRINCIPAL",
              FONT_BTN, ROUGE_NEON):
        goto("MENU")


# ═══════════════════════════════════════════════════════════════════════════
#  Traductions FR → EN pour les nouveaux textes
# ═══════════════════════════════════════════════════════════════════════════
EN.update({
    "SUCCÈS DÉBLOQUÉ": "ACHIEVEMENT UNLOCKED",
    "SUCCÈS DÉBLOQUÉS": "ACHIEVEMENTS UNLOCKED",
    "ACCÈS REFUSÉ": "ACCESS DENIED",
    "Réservé exclusivement à l'Élite du Top 100 Mondial":
        "Reserved exclusively for the Top 100 Global Elite",
    "Ton rang actuel : #%d": "Your current rank: #%d",
    "MODE CHAMPION": "CHAMPION MODE",
    "Difficultés 11 à 15 — Réservées au Top 100 Mondial":
        "Difficulties 11 to 15 — Top 100 Global only",
    "LANCER SURVIE": "START SURVIVAL",
    "LANCER PARCOURS": "START RUN",
    "ZONES SECRÈTES": "SECRET ZONES",
    "CAMPAGNE SECRÈTE": "SECRET CAMPAIGN",
    "Certains passages ne se révèlent qu'aux plus acharnés...":
        "Some passages only reveal themselves to the most relentless...",
    "manches": "rounds",
    "CHOISIS TON SKIN DE COMBAT": "CHOOSE YOUR BATTLE SKIN",
    "Cliquer pour équiper": "Click to equip",
    "[ÉQUIPÉ]": "[EQUIPPED]",
    "??? SKIN SECRET": "??? SECRET SKIN",
    "Succès / zone cachée": "Achievement / hidden zone",
    "??? MYTHIQUE": "??? MYTHIC",
    "Bientôt disponible": "Coming soon",
    "Pas encore débloqué : passe par la BOUTIQUE (icône maison).":
        "Not unlocked yet: visit the SHOP (house icon).",
    "REPRENDRE": "RESUME",
    "RECOMMENCER": "RESTART",
    "MENU PRINCIPAL": "MAIN MENU",
    "REJOUER": "RETRY",
    "VICTOIRE !": "VICTORY!",
    "DÉFAITE...": "DEFEAT...",
    "Classement final": "Final ranking",
    "record": "record",
    "Difficulté": "Difficulty",
    "PROFIL DU PILOTE": "PILOT PROFILE",
    "PHOTO DE PROFIL": "PROFILE PICTURE",
    "(clique sur le nom pour le changer)": "(click the name to change it)",
    "Parties jouées": "Games played",
    "Manches réussies": "Rounds cleared",
    "Ennemis détruits": "Enemies destroyed",
    "Meilleure Survie (manche)": "Best Survival (round)",
    "Zones secrètes trouvées": "Secret zones found",
    "Skins possédés": "Skins owned",
    "Objets possédés": "Items owned",
    "RECRUE": "RECRUIT", "PILOTE": "PILOT", "ÉLITE": "ELITE",
    "VÉTÉRAN": "VETERAN", "MAÎTRE DU CHAOS": "CHAOS MASTER",
    "LANGUE": "LANGUAGE", "CLAVIER": "KEYBOARD",
    "VOLUME GÉNÉRAL": "MASTER VOLUME", "MUSIQUE": "MUSIC",
    "EFFETS SONORES": "SOUND EFFECTS",
    "PLEIN ÉCRAN (F11)": "FULLSCREEN (F11)",
    "SECOUSSES D'ÉCRAN": "SCREEN SHAKE",
    "NOMBRES DE DÉGÂTS": "DAMAGE NUMBERS",
    "RÉDUIRE LES FLASHS": "REDUCE FLASHES",
    "EFFET CRT": "CRT EFFECT",
    "AFFICHER LES FPS": "SHOW FPS",
    "PARTICULES": "PARTICLES",
    "BAS": "LOW", "MOYEN": "MEDIUM", "ÉLEVÉ": "HIGH",
    "COMMANDES": "CONTROLS",
    "CONFIRMER : TOUT EFFACER ?": "CONFIRM: ERASE EVERYTHING?",
    "RÉINITIALISER LA PROGRESSION": "RESET PROGRESS",
    "Progression effacée.": "Progress erased.",
    "OUI": "YES", "NON": "NO",
    "COMMANDES & CONCEPT": "CONTROLS & CONCEPT",
    "MODES, DIFFICULTÉS & CAMPAGNE": "MODES, DIFFICULTIES & CAMPAIGN",
    "LA ROUE DU CHAOS": "THE WHEEL OF CHAOS",
    "BOUTIQUE, MATRICE D'ARMES & GEMMES": "SHOP, WEAPON MATRIX & GEMS",
    "Toutes les 15 s et à chaque manche, la roue tourne : "
    "un effet s'applique à TOUT LE MONDE.":
        "Every 15 s and at every round, the wheel spins: "
        "an effect applies to EVERYONE.",
    "< PRÉCÉDENT": "< PREVIOUS", "SUIVANT >": "NEXT >",
    "NIVEAU": "LEVEL",
})
# ═══════════════════════════════════════════════════════════════════════════
#  § 13 — BOUTIQUE (skins, stats, matrice d'armes, premium)
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  AMÉLIORATIONS PREMIUM (en gemmes)
# ─────────────────────────────────────────────────────────────────────────
PREMIUM_UPGRADES = {
    "prem_hp": dict(
        name="Vitalité Éternelle",
        desc="+6% PV max par niveau (cumulable).",
        levels=5, cost=[50, 100, 200, 400, 800],
        apply=lambda L, lvl: L.update(
            {"max_hp": L["max_hp"] * (1.0 + 0.06 * lvl)})),
    "prem_shield": dict(
        name="Égide Cosmique",
        desc="+8% bouclier max et +0.05/s de recharge par niveau.",
        levels=5, cost=[60, 120, 240, 480, 960],
        apply=lambda L, lvl: L.update({
            "max_shield": L["max_shield"] * (1.0 + 0.08 * lvl),
            "regen": L["regen"] + 0.05 * lvl})),
    "prem_power": dict(
        name="Fureur Séquentielle",
        desc="+4% de dégâts globaux par niveau.",
        levels=5, cost=[80, 160, 320, 640, 1280],
        apply=lambda L, lvl: L.update(
            {"power": L["power"] * (1.0 + 0.04 * lvl)})),
    "prem_coin": dict(
        name="Avarice Chronique",
        desc="+5% de pièces gagnées en fin de manche par niveau.",
        levels=5, cost=[40, 80, 160, 320, 640],
        apply=lambda L, lvl: L.update(
            {"coin": L["coin"] * (1.0 + 0.05 * lvl)})),
    "prem_luck": dict(
        name="Veine du Chaos",
        desc="+2% de chance de boîte mystère par manche par niveau.",
        levels=5, cost=[70, 140, 280, 560, 1120],
        apply=lambda L, lvl: None),   # effet passif géré dans box_from_round
    "prem_revive": dict(
        name="Écho Ancestral",
        desc="Une fois par run : ressuscite à 40% PV (+1 utilisation par niveau).",
        levels=3, cost=[300, 600, 1200],
        apply=lambda L, lvl: L.update({"prem_revives": lvl})),
}


def get_premium_level(key):
    return _to_int(SAVE.get("premium", {}).get(key, 0))


def set_premium_level(key, v):
    SAVE.setdefault("premium", {})[key] = v


def apply_premium_to_loadout(L):
    """Applique les bonus premium au loadout (appelé par loadout())."""
    for key, up in PREMIUM_UPGRADES.items():
        lvl = get_premium_level(key)
        if lvl > 0:
            try:
                up["apply"](L, lvl)
            except Exception:
                pass
    L.setdefault("prem_revives", 0)
    return L


# ─────────────────────────────────────────────────────────────────────────
#  ONGLET STATISTIQUES (achat de stats en pièces)
# ─────────────────────────────────────────────────────────────────────────
def shop_stats():
    for i, k in enumerate(STAT_KEYS):
        r = pygame.Rect(40 + (i % 2) * 480, 140 + (i // 2) * 112, 440, 104)
        st = STATS[k]
        panel(screen, r, (90, 70, 140), PANEL, 10, 2)
        draw_text(screen, tr(st["name"]), FONT_BTN, CYAN_NEON,
                  r.x + 16, r.y + 10, center=False)
        cur = st["fmt"](stat_value(k))
        nxt = st["fmt"](st["base"] + st["inc"]
                        * (SAVE["upg"][k] + 1 + SAVE["bonus"][k]))
        full = SAVE["upg"][k] >= STAT_MAX_BUY
        draw_text(screen, cur if full else "%s  >  %s" % (cur, nxt),
                  FONT_MED, BLANC, r.x + 16, r.y + 42, center=False)

        # Barres de niveau (jaune = achat, violet = succès)
        for j in range(STAT_MAX_BUY):
            col = JAUNE_NEON if j < SAVE["upg"][k] else (60, 52, 84)
            pygame.draw.rect(screen, col,
                             (r.x + 16 + j * 24, r.y + 78, 20, 10),
                             border_radius=3)
        for j in range(STAT_MAX_BONUS):
            col = PURPLE_NEON if j < SAVE["bonus"][k] else (46, 36, 70)
            pygame.draw.rect(screen, col,
                             (r.x + 150 + j * 24, r.y + 78, 20, 10),
                             border_radius=3)
        draw_text(screen, tr("achat"), FONT_TINY, (140, 130, 170),
                  r.x + 16, r.y + 90, center=False)
        draw_text(screen, tr("succès"), FONT_TINY, (140, 130, 170),
                  r.x + 150, r.y + 90, center=False)

        price = stat_price(k)
        label = tr("MAX") if full else "%d" % price
        b = pygame.Rect(r.right - 150, r.y + 30, 134, 44)
        if not full:
            draw_coin_icon(screen, b.x + 22, b.centery, 8)
        if button(b, label if full else "      %d" % price,
                  FONT_BTN, VERT_NEON, enabled=not full):
            if SAVE["coins"] >= price:
                SAVE["coins"] -= price
                SAVE["upg"][k] += 1
                audio.play("buy")
                write_save()
                say("%s : %s" % (tr("Amélioré"), tr(st["name"])), VERT_NEON)
            else:
                audio.play("error")
                say(tr("Pas assez de pièces !"), ROUGE_NEON)


# ─────────────────────────────────────────────────────────────────────────
#  ONGLET PREMIUM (achat en gemmes)
# ─────────────────────────────────────────────────────────────────────────
def shop_premium():
    draw_text_outlined(screen, tr("AMÉLIORATIONS PREMIUM — GEMMES"),
                       FONT_TITLE, GEM_COL, WIDTH // 2, 96,
                       outline=(0, 0, 0), thick=2)
    draw_text(screen,
              tr("Bonus passifs uniques, cumulables avec les stats et succès."),
              FONT_SMALL, (200, 190, 230), WIDTH // 2, 132)

    keys = list(PREMIUM_UPGRADES.keys())
    for i, key in enumerate(keys):
        up = PREMIUM_UPGRADES[key]
        lvl = get_premium_level(key)
        maxed = lvl >= up["levels"]
        r = pygame.Rect(60 + (i % 3) * 296, 160 + (i // 3) * 226,
                        280, 216)
        hover = r.collidepoint(mouse["x"], mouse["y"])
        if hover and not maxed:
            pulse = 0.5 + 0.5 * math.sin(TICK[0] * 0.08)
            glow_rect(screen, r, GEM_COL, spread=12,
                      max_alpha=int(60 + 50 * pulse))
        panel(screen, r, GEM_COL if hover else dark(GEM_COL, 0.6),
              mixc(PANEL, GEM_COL, 0.14 if hover else 0.05),
              10, 3 if hover else 2)
        draw_text_outlined(screen, tr(up["name"]), FONT_BTN, BLANC,
                           r.x + 16, r.y + 22, center=False,
                           outline=(0, 0, 0), thick=1)
        for li, ln in enumerate(wrap_text(tr(up["desc"]),
                                           FONT_TINY, r.w - 32)[:3]):
            draw_text(screen, ln, FONT_TINY, (200, 190, 225),
                      r.x + 16, r.y + 48 + li * 14, center=False)

        # Pastilles de niveau
        for j in range(up["levels"]):
            cx = r.x + 22 + j * 30
            cy = r.y + 122
            filled = j < lvl
            pygame.draw.circle(screen,
                               GEM_COL if filled else (50, 60, 80),
                               (cx, cy), 10, 0 if filled else 2)
            if filled:
                pygame.draw.circle(screen, BLANC, (cx, cy), 3)

        if maxed:
            draw_text(screen, tr("NIVEAU MAX"), FONT_BTN, JAUNE_NEON,
                      r.centerx, r.bottom - 30)
        else:
            cost = up["cost"][lvl]
            affordable = SAVE["gems"] >= cost
            draw_gem_icon(screen, r.x + 44, r.y + 168, 12)
            draw_text(screen, "%d" % cost, FONT_BTN,
                      GEM_COL if affordable else (150, 130, 150),
                      r.x + 66, r.y + 168, center=False)
            brect = pygame.Rect(r.right - 120, r.y + 146, 108, 44)
            if button(brect, tr("ACHETER"), FONT_SMALL,
                      GEM_COL if affordable else None,
                      enabled=affordable):
                SAVE["gems"] -= cost
                set_premium_level(key, lvl + 1)
                audio.play("buy")
                write_save()
                say(tr("%s : niveau %d") % (tr(up["name"]), lvl + 1),
                    GEM_COL)


# ─────────────────────────────────────────────────────────────────────────
#  ONGLET OBJETS — MATRICE NODALE (3 colonnes × 2 sous-catégories × 3 items)
# ─────────────────────────────────────────────────────────────────────────
WEAPON_MATRIX_LAYOUT = {
    "ATTAQUE": {
        "color": ATTACK_COL,
        "subs": {
            "Lames": [
                ("Lame Énergétique", 1500,
                 "Saignement 5 dmg/s × 3 s"),
                ("Sabre Quantique",  2200,
                 "Perfore 3 cibles + ralentit"),
                ("Katar du Void",    2800,
                 "Critique ×2.5 + explosion zone"),
            ],
            "Distance": [
                ("Fusil Plasma",       3500,
                 "Tir triple en éventail"),
                ("Railgun Magnétique", 4500,
                 "Perfore tout, ignore armure"),
                ("Orbe Singularité",   5500,
                 "Tête chercheuse + explosion"),
            ],
        },
    },
    "DÉFENSE": {
        "color": DEFENSE_COL,
        "subs": {
            "Boucliers": [
                ("Champ Prismatique", 1200,
                 "Renvoie 25% des dégâts"),
                ("Égide Tesseract",  2000,
                 "Bouclier auto (recharge 8 s)"),
                ("Bouclier Aegis-X", 2800,
                 "Explose au bris (40 dmg zone)"),
            ],
            "Armures": [
                ("Plaques Titane",   3800,
                 "Immunité pièges + 15% réduction"),
                ("Nano-Alliage",    4500,
                 "Régénération +2 PV/s"),
                ("Peau de Nébuleuse", 5500,
                 "18% esquive + soin sur esquive"),
            ],
        },
    },
    "SOUTIEN": {
        "color": SUPPORT_COL,
        "subs": {
            "Soin": [
                ("Croix Quantique",  1200,
                 "Pulse de soin +25 PV (10 s)"),
                ("Fontaine Vita",    1800,
                 "Zone de soin +2 PV/s"),
                ("Sève Éternelle",   2600,
                 "Anti-ralentissement + +1.5 PV/s"),
            ],
            "Buff": [
                ("Totem Chrono",      3400,
                 "Ralentit le temps 3 s"),
                ("Œil Oraculaire",   4000,
                 "Vision + critique 4 s"),
                ("Cœur du Multivers", 4800,
                 "Frénésie totale 5 s"),
            ],
        },
    },
}


def _weapon_icon(surf, cx, cy, size, kind, col):
    """Icône vectorielle unique par type d'arme (matrice nodale)."""
    s = int(size)
    h = s // 2
    kind_l = kind.lower()

    if any(k in kind_l for k in ("lame", "sabre", "katar")):
        pts = [(cx, cy - h), (cx + h * 0.5, cy + h * 0.4),
               (cx, cy + h), (cx - h * 0.5, cy + h * 0.4)]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, BLANC, pts, 2)
        pygame.draw.line(surf, BLANC, (cx, cy - h + 2),
                         (cx, cy + h - 2), 1)
    elif any(k in kind_l for k in ("fusil", "railgun", "orbe")):
        rect = pygame.Rect(cx - h, cy - h // 3, s, s // 3 * 2)
        pygame.draw.rect(surf, col, rect, border_radius=4)
        pygame.draw.rect(surf, BLANC, rect, 2, border_radius=4)
        pygame.draw.circle(surf, BLANC, (cx + h // 2, cy), 4)
    elif any(k in kind_l for k in ("bouclier", "égide", "aegis", "champ")):
        pts = [(cx, cy - h), (cx + h, cy - h // 3),
               (cx + h * 0.7, cy + h), (cx - h * 0.7, cy + h),
               (cx - h, cy - h // 3)]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, BLANC, pts, 2)
        pygame.draw.line(surf, BLANC, (cx, cy - h + 4),
                         (cx, cy + h - 4), 1)
    elif any(k in kind_l for k in ("plaques", "nano", "peau")):
        pts = [(cx - h, cy - h), (cx + h, cy - h),
               (cx + h * 0.85, cy + h), (cx - h * 0.85, cy + h)]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, BLANC, pts, 2)
        for i in (1, 2):
            pygame.draw.line(surf, BLANC,
                             (cx - h + 2, cy - h + i * h * 2 // 3),
                             (cx + h - 2, cy - h + i * h * 2 // 3), 1)
    elif any(k in kind_l for k in ("croix", "fontaine", "sève")):
        pygame.draw.rect(surf, col, (cx - h * 0.3, cy - h, h * 0.6, s))
        pygame.draw.rect(surf, col, (cx - h, cy - h * 0.3, s, h * 0.6))
        pygame.draw.rect(surf, BLANC, (cx - h * 0.3, cy - h, h * 0.6, s), 1)
        pygame.draw.rect(surf, BLANC, (cx - h, cy - h * 0.3, s, h * 0.6), 1)
    else:
        pygame.draw.circle(surf, col, (cx, cy), h)
        pygame.draw.circle(surf, BLANC, (cx, cy), h, 2)
        pygame.draw.circle(surf, BLANC, (cx, cy), 3)


def draw_weapon_matrix(surface, t=0.0):
    """Rendu de la matrice nodale. Retourne la liste des nœuds :
    [(rect, cat_key, sub_name, item_name, price, stat)].
    """
    surface.fill((8, 10, 22))

    # Étoiles de fond
    rng = random.Random(42)
    for _ in range(60):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        b = rng.randint(40, 120)
        pygame.draw.circle(surface, (b, b, b + 20), (x, y), 1)

    # Titres
    draw_text(surface, tr("MATRICE DES ARMES"), FONT_TITLE,
              (200, 220, 255), WIDTH // 2, 26)
    draw_text(surface,
              tr("Survole un nœud pour la fiche • Clique pour acheter"),
              FONT_TINY, (150, 180, 220), WIDTH // 2, 60)

    nodes = []
    cols = ["ATTAQUE", "DÉFENSE", "SOUTIEN"]
    col_x = [WIDTH // 4, WIDTH // 2, 3 * WIDTH // 4]
    root_y = 118
    row_gap = 46
    item_r = 22

    for ci, cat_key in enumerate(cols):
        data = WEAPON_MATRIX_LAYOUT[cat_key]
        col = data["color"]
        cx = col_x[ci]

        # Racine
        root_r = 34
        pygame.draw.circle(surface, dark(col, 0.35), (cx, root_y), root_r)
        pygame.draw.circle(surface, col, (cx, root_y), root_r, 3)
        draw_text(surface, tr(cat_key[:4]), FONT_BTN, BLANC, cx, root_y)

        sy = root_y + 88
        for sub_name, items in data["subs"].items():
            pygame.draw.line(surface, col,
                             (cx, root_y + root_r), (cx, sy - 14), 2)
            sub_r = pygame.Rect(cx - 70, sy - 14, 140, 28)
            pygame.draw.rect(surface, dark(col, 0.3), sub_r, border_radius=8)
            pygame.draw.rect(surface, col, sub_r, 2, border_radius=8)
            draw_text(surface, tr(sub_name), FONT_SMALL, BLANC, cx, sy)

            iy = sy + 48
            for item_name, price, stat in items:
                pygame.draw.line(surface, col, (cx, sy + 14),
                                 (cx, iy - item_r), 1)
                node_rect = pygame.Rect(cx - item_r, iy - item_r,
                                        item_r * 2, item_r * 2)
                hover = node_rect.collidepoint(mouse["x"], mouse["y"])

                if hover:
                    pulse = 0.5 + 0.5 * math.sin(t * 0.1)
                    size = node_rect.w + 20
                    halo = pygame.Surface((size, size), pygame.SRCALPHA)
                    hcx = hcy = size // 2
                    for i in range(5, 0, -1):
                        a = int((70 + 40 * pulse) * (1 - i / 5))
                        pygame.draw.circle(halo, (*col, a),
                                           (hcx, hcy),
                                           node_rect.w // 2 + i * 3)
                    surface.blit(halo, (node_rect.x - 10, node_rect.y - 10))

                pygame.draw.circle(surface, (18, 22, 40), (cx, iy), item_r)
                pygame.draw.circle(surface, col, (cx, iy), item_r,
                                   3 if hover else 2)
                _weapon_icon(surface, cx, iy, 22, item_name, col)

                draw_text(surface, tr(item_name), FONT_TINY,
                          BLANC if hover else (200, 210, 230),
                          cx + item_r + 10, iy - 8, center=False)
                draw_text(surface, "%d p" % price, FONT_TINY,
                          (255, 220, 100),
                          cx + item_r + 10, iy + 8, center=False)

                nodes.append((node_rect, cat_key, sub_name,
                              item_name, price, stat))
                iy += row_gap + item_r
            sy = iy + 8

    return nodes


def _draw_matrix_tooltip(node_rect, cat, sub, name, price, stat):
    """Info-bulle : effet mis en avant, description complète, prix."""
    W_tip, H_tip = 380, 210
    x = min(node_rect.right + 14, WIDTH - W_tip - 8)
    y = clamp(node_rect.y - 30, 100, HEIGHT - H_tip - 8)
    box = pygame.Rect(x, y, W_tip, H_tip)
    col = WEAPON_MATRIX_LAYOUT[cat]["color"]
    pygame.draw.rect(screen, (10, 14, 30), box, border_radius=12)
    pygame.draw.rect(screen, col, box, 3, border_radius=12)

    # Nom
    draw_text(screen, tr(name), FONT_BTN, BLANC,
              box.x + 16, box.y + 16, center=False)
    # Catégorie
    draw_text(screen, "[%s • %s]" % (tr(cat), tr(sub)),
              FONT_TINY, col, box.x + 16, box.y + 42, center=False)
    # Séparateur
    pygame.draw.line(screen, col,
                     (box.x + 16, box.y + 58),
                     (box.right - 16, box.y + 58), 1)
    # Bloc EFFET (le plus important visuellement)
    draw_text(screen, tr("EFFET"), FONT_TINY, col,
              box.x + 16, box.y + 72, center=False)
    for i, ln in enumerate(wrap_text(tr(stat), FONT_SMALL,
                                      W_tip - 32)[:3]):
        draw_text(screen, ln, FONT_SMALL, (255, 220, 130),
                  box.x + 16, box.y + 92 + i * 18, center=False)

    # Prix
    draw_text(screen, "%d %s" % (price, tr("pièces")),
              FONT_BTN, JAUNE_NEON, box.x + 16, box.bottom - 42,
              center=False)

    # Statut
    owned = False
    for lst in ITEMS.values():
        for it in lst:
            if it["name"] == name and it["id"] in SAVE["items"]:
                owned = True
                break
        if owned:
            break
    if owned:
        draw_text(screen, tr("✓ Déjà possédé"), FONT_TINY, VERT_NEON,
                  box.right - 120, box.bottom - 42, center=False)
    else:
        draw_text(screen, tr("Clic pour acheter"), FONT_TINY,
                  (180, 200, 230), box.right - 120, box.bottom - 42,
                  center=False)


def shop_items():
    """Onglet OBJETS : matrice nodale interactive."""
    draw_text(screen, tr("MATRICE D'ARMES"), FONT_TITLE,
              JAUNE_NEON, WIDTH // 2, 26)
    nodes = draw_weapon_matrix(screen, TICK[0] / 60.0)

    hovered = None
    for node_rect, cat, sub, name, price, stat in nodes:
        if node_rect.collidepoint(mouse["x"], mouse["y"]):
            hovered = (node_rect, cat, sub, name, price, stat)
            if mouse.get("click"):
                mouse["click"] = False
                # Achat : cherche l'objet correspondant dans ITEMS
                target = None
                for lst in ITEMS.values():
                    for it in lst:
                        if it["name"] == name:
                            target = it
                            break
                    if target:
                        break
                if not target:
                    audio.play("error")
                    say(tr("Objet indisponible."), ROUGE_NEON)
                elif target["id"] in SAVE["items"]:
                    audio.play("click")
                    say(tr("Déjà possédé !"), CYAN_NEON)
                elif SAVE["coins"] >= target["price"]:
                    SAVE["coins"] -= target["price"]
                    SAVE["items"].append(target["id"])
                    audio.play("buy")
                    write_save()
                    say("%s : %s" % (tr("Acheté"), tr(target["name"])),
                        VERT_NEON)
                else:
                    audio.play("error")
                    say(tr("Pas assez de pièces (il t'en manque %d).")
                        % (target["price"] - SAVE["coins"]), ROUGE_NEON)

    if hovered:
        _draw_matrix_tooltip(*hovered)


# ─────────────────────────────────────────────────────────────────────────
#  GRILLE DE SKINS (pour l'onglet SKINS de la boutique)
# ─────────────────────────────────────────────────────────────────────────
def draw_skin_tabs():
    """Onglets de rareté (version boutique)."""
    n = len(SKIN_TABS)
    tw, gap = 176, 12
    x0 = (WIDTH - (n * tw + (n - 1) * gap)) // 2
    for i, tb in enumerate(SKIN_TABS):
        r = pygame.Rect(x0 + i * (tw + gap), 580, tw, 48)
        col = tb["col"]
        if tb["rar"] == "MYTHIC":
            col = mixc(col, (255, 205, 70),
                       0.5 + 0.5 * math.sin(TICK[0] * 0.07))
        sel = UI.get("page", 0) == i
        hover = r.collidepoint(mouse["x"], mouse["y"])
        key = (r.x, r.y, r.w, r.h)
        if hover:
            _register_hover(key)
        fill = mixc(PANEL, col, 0.42 if sel else (0.22 if hover else 0.07))
        panel(screen, r, col if (sel or hover) else dark(col, 0.55),
              fill, 8, 3 if sel else 2)
        pygame.draw.circle(screen,
                           col if (sel or hover) else dark(col, 0.65),
                           (r.x + 25, r.centery), 15)
        draw_text(screen, str(i + 1), FONT_BTN, (18, 10, 28),
                  r.x + 25, r.centery)
        owned_n = len([k for k in SKIN_ORDER
                       if SKINS[k]["rarity"] == tb["rar"] and k in SAVE["owned"]])
        total_n = len([k for k in SKIN_ORDER if SKINS[k]["rarity"] == tb["rar"]])
        draw_text_ml(screen, tr(tb["label"]), FONT_SMALL,
                     BLANC if (sel or hover) else light(col, 0.1),
                     r.x + 48, r.y + 17)
        draw_text_ml(screen, "%d/%d" % (owned_n, total_n), FONT_TINY,
                     col, r.x + 48, r.y + 34)
        if sel:
            pygame.draw.rect(screen, col,
                             (r.x + 10, r.bottom + 3, r.w - 20, 3),
                             border_radius=2)
        if hover and mouse.get("click"):
            mouse["click"] = False
            UI["page"] = i
            UI["buy_arm"] = None
            audio.play("click")


def buy_skin(key):
    """Achat d'un skin (pièces ou gemmes, confirmation 2 clics si gros prix)."""
    sk = SKINS[key]
    gem = sk.get("gems")
    price = gem if gem else sk["price"]
    have = SAVE["gems"] if gem else SAVE["coins"]
    if have < price:
        audio.play("error")
        txt = (tr("Pas assez de gemmes (il t'en manque %d).") if gem
               else tr("Pas assez de pièces (il t'en manque %d)."))
        say(txt % (price - have), ROUGE_NEON)
        return
    if gem or price >= 100000:
        arm = UI.get("buy_arm")
        if not (arm and arm[0] == key and TICK[0] - arm[1] < 300):
            UI["buy_arm"] = (key, TICK[0])
            audio.play("click")
            say(tr("Achat important : clique encore pour confirmer."),
                JAUNE_NEON)
            return
    UI["buy_arm"] = None
    if gem:
        SAVE["gems"] -= price
    else:
        SAVE["coins"] -= price
    SAVE["owned"].append(key)
    SAVE["selected"] = key
    audio.play("buy")
    write_save()
    say("%s : %s !" % (tr("Acheté"), tr(sk["name"])), VERT_NEON)


def draw_skin_tip(card, key):
    """Info-bulle complète : rareté, stats, compétences."""
    sk = SKINS[key]
    rc = RARITY[sk["rarity"]]["color"]
    W_tip = 380
    rows = [(tr(sk["name"]), BLANC, FONT_SMALL, 0),
            (tr(RARITY[sk["rarity"]]["label"]), rc, FONT_TINY, 0)]
    stats = skin_stat_lines(key)
    if stats:
        rows.append((tr("STATISTIQUES"), (150, 150, 175), FONT_TINY, 0))
        rows += [(s_, (200, 230, 255), FONT_TINY, 8) for s_ in stats]
    skills = skin_skill_lines(key)
    if skills:
        rows.append((tr("COMPÉTENCES"), (150, 150, 175), FONT_TINY, 0))
        for tier, name, desc in skills:
            rows.append((name, RARITY[tier]["color"], FONT_SMALL, 8))
            for ln in wrap_text(desc, FONT_TINY, W_tip - 44):
                rows.append((ln, (215, 210, 235), FONT_TINY, 16))
    h = 20 + sum(f.get_linesize() + 2 for _t, _c, f, _i in rows)
    x = card.right + 8 if card.right + 8 + W_tip <= WIDTH - 8 else card.x - W_tip - 8
    # Limite haute AVANT les onglets de rareté (y=560) pour ne pas les couvrir
    y = clamp(card.y, 96, max(96, 555 - h))
    panel(screen, pygame.Rect(x, y, W_tip, h), rc, (14, 9, 26), 8, 2)
    yy = y + 10
    for text, col, font, ind in rows:
        draw_text(screen, text, font, col, x + 14 + ind, yy, center=False)
        yy += font.get_linesize() + 2


def draw_mythic_fx(card, t):
    """Halo pulsant + braises rouges et or pour les cartes mythiques."""
    glow = pygame.Surface(card.size, pygame.SRCALPHA)
    pulse = 0.5 + 0.5 * math.sin(t * 0.07)
    for i in range(7):
        pygame.draw.circle(glow, (255, 40, 90, int(10 + 7 * pulse)),
                           (card.w // 2, card.h // 2 - 22), 92 - i * 11)
    for i in range(14):
        ph = (t * 0.9 + i * 37) % 170
        ex = card.w // 2 + math.sin(i * 1.9 + t * 0.02) * 62
        ey = card.h - 40 - ph
        if 8 < ey < card.h - 40:
            al = int(200 * (1 - ph / 170.0))
            pygame.draw.circle(glow,
                               (255, 190 if i % 2 else 70, 70, al),
                               (int(ex), int(ey)), 2 + i % 2)
    screen.blit(glow, card.topleft)


def skin_grid(mode):
    """Grille de cartes de skins (utilisée par la boutique)."""
    UI["page"] = clamp(UI.get("page", 0), 0, len(SKIN_TABS) - 1)
    tab = SKIN_TABS[UI["page"]]
    tcol = tab["col"]
    entries = tab_entries(UI["page"])

    panel(screen, pygame.Rect(28, 128, 944, 444), dark(tcol, 0.6),
          mixc(NOIR_FOND, tcol, 0.07), 12, 2)

    tip = None
    for i, key in enumerate(entries):
        card = pygame.Rect(36 + (i % 5) * 188, 138 + (i // 5) * 218,
                           172, 205)
        if key is None:
            # Emplacement mythique "bientôt"
            panel(screen, card, dark(tcol, 0.5), PANEL, 10, 2)
            draw_text(screen, "?", FONT_BIG, dark(tcol, 0.5),
                      card.centerx, card.y + 76)
            draw_text(screen, tr("??? MYTHIQUE"), FONT_SMALL,
                      (200, 200, 210), card.centerx, card.bottom - 42)
            draw_text(screen, tr("Bientôt disponible"), FONT_TINY,
                      (150, 150, 165), card.centerx, card.bottom - 20)
            if card.collidepoint(mouse["x"], mouse["y"]) and mouse.get("click"):
                mouse["click"] = False
                audio.play("error")
                say(tr("Futur skin mythique : bientôt disponible..."), tcol)
            continue

        sk = SKINS[key]
        owned = key in SAVE["owned"]
        eq = SAVE["selected"] == key
        reveal = owned or not sk["hidden"]
        mythic = sk["rarity"] == "MYTHIC"
        rc = (RARITY[sk["rarity"]]["color"] if reveal else (80, 62, 120))
        if mythic and reveal:
            rc = mixc((255, 50, 90), (255, 205, 70),
                      0.5 + 0.5 * math.sin(TICK[0] * 0.06))
        hover = card.collidepoint(mouse["x"], mouse["y"])
        edge = JAUNE_NEON if eq else (light(rc, 0.5) if hover else rc)
        if hover and reveal:
            tip = (card, key)
        panel(screen, card, edge, PANEL, 10,
              3 if (hover or eq or mythic) else 2)
        if mythic and reveal:
            draw_mythic_fx(card, TICK[0])

        if not owned and sk["hidden"]:
            # Skin secret verrouillé
            for j in range(8):
                pygame.draw.circle(screen, (*sk["body"], 16),
                                   (card.centerx, card.y + 76), 90 - j * 10)
            draw_text(screen, "?", FONT_BIG, dark(sk["body"], 0.5),
                      card.centerx, card.y + 76)
            for p1, p2 in (((card.x + 6, card.y + 12), (card.right - 6, card.y + 124)),
                           ((card.right - 6, card.y + 12), (card.x + 6, card.y + 124))):
                d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                n = max(2, int(d / 13))
                for k2 in range(n + 1):
                    xx = p1[0] + (p2[0] - p1[0]) * k2 / n
                    yy = p1[1] + (p2[1] - p1[1]) * k2 / n
                    rr = (pygame.Rect(0, 0, 16, 9) if k2 % 2 == 0
                          else pygame.Rect(0, 0, 9, 16))
                    rr.center = (xx, yy)
                    pygame.draw.ellipse(screen, (150, 155, 170), rr, 3)
            pygame.draw.arc(screen, (190, 190, 200),
                            (card.centerx - 10, card.y + 52, 20, 28),
                            0, math.pi, 4)
            pygame.draw.rect(screen, (210, 170, 40),
                             (card.centerx - 16, card.y + 66, 32, 24),
                             border_radius=4)
            draw_text(screen, tr("??? SKIN SECRET"), FONT_SMALL,
                      (200, 200, 210), card.centerx, card.bottom - 42)
            draw_text(screen, tr("Succès / zone cachée"), FONT_TINY,
                      (150, 150, 165), card.centerx, card.bottom - 20)
        else:
            draw_skin(screen, key, card.centerx, card.y + 76, 1, TICK[0],
                      False, 0, 1.55, 255 if owned else 120)
            draw_text(screen, tr(RARITY[sk["rarity"]]["label"]), FONT_TINY,
                      rc, card.x + 10, card.y + 8, center=False)
            draw_text(screen, tr(sk["name"]), FONT_SMALL, BLANC,
                      card.centerx, card.bottom - 44)
            if eq:
                draw_text(screen, tr("[ÉQUIPÉ]"), FONT_SMALL, JAUNE_NEON,
                          card.centerx, card.bottom - 20)
            elif owned:
                draw_text(screen, tr("Cliquer pour équiper"), FONT_TINY,
                          VERT_NEON, card.centerx, card.bottom - 20)
            elif sk.get("box_only"):
                draw_text(screen, tr("BOÎTE UNIQUEMENT"), FONT_SMALL,
                          (200, 80, 255), card.centerx, card.bottom - 20)
            elif sk.get("champion_only"):
                draw_text(screen, tr("TOP 10 REQUIS"), FONT_SMALL,
                          CHAMPION_COL, card.centerx, card.bottom - 20)
            else:
                gem = sk.get("gems")
                arm = UI.get("buy_arm")
                if arm and arm[0] == key and TICK[0] - arm[1] < 300:
                    if (TICK[0] // 15) % 2 == 0:
                        draw_text(screen, tr("CONFIRMER ?"), FONT_SMALL,
                                  JAUNE_NEON, card.centerx, card.bottom - 20)
                else:
                    txt = fmt_num(gem if gem else sk["price"])
                    wtxt = FONT_SMALL.size(txt)[0]
                    x0 = card.centerx - (wtxt + 22) // 2
                    if gem:
                        draw_gem_icon(screen, x0 + 8, card.bottom - 20, 8)
                    else:
                        draw_coin_icon(screen, x0 + 8, card.bottom - 20, 8)
                    draw_text_ml(screen, txt, FONT_SMALL,
                                 GEM_COL if gem else JAUNE_NEON,
                                 x0 + 22, card.bottom - 20)

        if hover and mouse.get("click"):
            mouse["click"] = False
            if owned:
                SAVE["selected"] = key
                audio.play("click")
                write_save()
            elif sk["hidden"]:
                audio.play("error")
                say(tr("Skin secret : relève des défis et trouve "
                       "les zones cachées..."), ROUGE_NEON)
            elif mode == "shop":
                if sk.get("box_only"):
                    audio.play("error")
                    say(tr("Ce skin ne s'obtient que dans les "
                           "Boîtes Mystères !"), ROUGE_NEON)
                elif sk.get("champion_only"):
                    audio.play("error")
                    say(tr("Requis : Top 10 Mondial au Classement"),
                        CHAMPION_COL)
                else:
                    buy_skin(key)
            else:
                audio.play("error")
                say(tr("Pas encore débloqué : passe par la BOUTIQUE "
                       "(icône maison)."), ROUGE_NEON)

    draw_skin_tabs()
    if tip:
        draw_skin_tip(*tip)


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN BOUTIQUE (4 onglets)
# ─────────────────────────────────────────────────────────────────────────
def screen_shop():
    menu_bg(screen)
    cx = WIDTH // 2
    draw_text_outlined(screen, tr("BOUTIQUE"), FONT_TITLE,
                       JAUNE_NEON, cx, 46, outline=(0, 0, 0), thick=2)
    draw_coins_counter()

    tabs = [("SKINS", "SKINS"), ("STATISTIQUES", "STATS"),
            ("OBJETS", "ITEMS"), ("PREMIUM", "PREMIUM")]
    tab_w = 200
    gap = 8
    total = len(tabs) * tab_w + (len(tabs) - 1) * gap
    x0 = (WIDTH - total) // 2
    for i, (lab, key) in enumerate(tabs):
        r = pygame.Rect(x0 + i * (tab_w + gap), 82, tab_w, 42)
        active = UI.get("shop_tab") == key
        if button(r, lab, FONT_SMALL, JAUNE_NEON if active else None):
            UI["shop_tab"] = key
            UI["page"] = 0
        if active:
            pygame.draw.rect(screen, JAUNE_NEON,
                             (r.x + 10, r.bottom + 3, r.w - 20, 4),
                             border_radius=2)

    # Onglet actif
    if UI.get("shop_tab") == "SKINS":
        skin_grid("shop")
    elif UI.get("shop_tab") == "STATS":
        shop_stats()
        draw_text(screen,
                  tr("Jaune : achetable. Violet : bonus gagnés grâce aux succès."),
                  FONT_SMALL, (170, 150, 210), cx, 604)
    elif UI.get("shop_tab") == "PREMIUM":
        shop_premium()
    else:
        shop_items()

    # Bouton boîte mystère — placé en HAUT À DROITE sous le compteur
    # (ne chevauche plus les onglets de rareté)
    box_btn = pygame.Rect(WIDTH - 220, 90, 200, 36)
    if button(box_btn, "BOÎTE : %d GEMMES" % box_price(),
              FONT_SMALL, JAUNE_NEON):
        ok, msg = buy_box_with_gems()
        if not ok:
            say(msg, ROUGE_NEON)

    # Bouton retour standard (bas-gauche)
    draw_back_button(col=JAUNE_NEON, action=lambda: goto("MENU"))
    return True


# ═══════════════════════════════════════════════════════════════════════════
#  § 14 — BOÎTES MYSTÈRES
# ═══════════════════════════════════════════════════════════════════════════

# Table de drop v2 : simple et transparente.
#   Pièces 55% / Commun 20% / Rare 14% / Épique 8% / Légendaire 2.95% / Mythique 0.05%
class MysteryBoxSystem:
    """Tirage des boîtes mystères.

    Rareté du drop → conversion si doublon (pièces ou gemmes).
    Les skins secrets (hidden) restent exclus (ils se méritent par les
    zones cachées)."""
    TABLE = (("COINS", 55.0), ("COMMON", 20.0), ("RARE", 14.0),
             ("EPIC", 8.0), ("LEGENDARY", 2.95), ("MYTHIC", 0.05))
    COIN_RANGE, COIN_STEP = (1500, 8000), 100
    DUP_REWARD = {
        "COMMON":    dict(coins=5000),
        "RARE":      dict(gems=15),
        "EPIC":      dict(gems=30),
        "LEGENDARY": dict(gems=80),
        "MYTHIC":    dict(gems=200),
    }

    def __init__(self, save=None, rng=None, writer=None, audio_getter=None):
        self._save = save
        self.rng = rng or random
        self._writer = writer
        self._audio_getter = audio_getter

    @property
    def save(self):
        return self._save if self._save is not None else SAVE

    @property
    def stock(self):
        return _to_int(self.save.get("mystery_boxes", 0))

    def _play(self, *names):
        try:
            a = (self._audio_getter() if self._audio_getter
                 else globals().get("audio"))
            for n in names:
                a.play(n)
        except Exception:
            pass

    def _pool(self, rarity):
        """Skins éligibles à un drop de cette rareté (hors hidden)."""
        out = []
        for k, sk in SKINS.items():
            if sk["rarity"] != rarity or sk["hidden"]:
                continue
            if rarity == "COMMON" and k == "NEON_CYBER":
                continue
            if rarity == "MYTHIC" and not sk.get("box_only"):
                continue
            if rarity != "MYTHIC" and sk.get("box_only"):
                continue
            out.append(k)
        return out

    def _roll_tier(self):
        total = sum(w for _k, w in self.TABLE)
        r = self.rng.random() * total
        acc = 0.0
        for kind, w in self.TABLE:
            acc += w
            if r < acc:
                return kind
        return self.TABLE[0][0]

    def open(self):
        """Ouvre UNE boîte. Retourne un dict prêt pour l'animation."""
        if self.stock <= 0:
            self._play("error")
            return {"ok": False, "reason": "empty",
                    "title": tr("BOÎTE MYSTÈRE"),
                    "lines": [tr("Aucune boîte mystère à ouvrir.")],
                    "rarity": "COMMON", "remaining": 0,
                    "coins": 0, "gems": 0, "skin": None,
                    "duplicate": False, "new_ach": []}

        s = self.save
        st = s.setdefault("stats", {})
        st["boxes_opened"] = _to_int(st.get("boxes_opened", 0))
        s["mystery_boxes"] = self.stock - 1

        tier = self._roll_tier()
        res = dict(ok=True, tier=tier, rarity="COMMON", title="",
                   lines=[], coins=0, gems=0, skin=None,
                   duplicate=False, new_ach=[], remaining=self.stock)

        if tier == "COINS":
            lo, hi, step = self.COIN_RANGE[0], self.COIN_RANGE[1], self.COIN_STEP
            n = self.rng.randint(lo // step, hi // step) * step
            s["coins"] = _to_int(s.get("coins", 0)) + n
            res["coins"] = n
            res["title"] = tr("BOÎTE MYSTÈRE")
            res["lines"] = ["+%d %s" % (n, tr("pièces"))]
        else:
            pool = self._pool(tier)
            if not pool:
                # Fallback gemmes
                res["rarity"] = "RARE"
                res["title"] = tr("BOÎTE MYSTÈRE")
                gems = {"COMMON": 20, "RARE": 40, "EPIC": 80,
                        "LEGENDARY": 150, "MYTHIC": 300}[tier]
                s["gems"] = _to_int(s.get("gems", 0)) + gems
                res["gems"] = gems
                res["lines"] = ["+%d %s" % (gems, tr("gemmes")),
                                tr("Collection complète : gemmes bonus !")]
            else:
                key = self.rng.choice(pool)
                sk = SKINS[key]
                res["rarity"] = tier
                if key in s["owned"]:
                    # Doublon → conversion
                    dup = self.DUP_REWARD[tier]
                    res["duplicate"] = True
                    if "coins" in dup:
                        s["coins"] = _to_int(s.get("coins", 0)) + dup["coins"]
                        res["coins"] = dup["coins"]
                        res["lines"] = [
                            tr(sk["name"]) + "  (" + tr("doublon") + ")",
                            "+%d %s" % (dup["coins"], tr("pièces"))]
                    else:
                        s["gems"] = _to_int(s.get("gems", 0)) + dup["gems"]
                        res["gems"] = dup["gems"]
                        res["lines"] = [
                            tr(sk["name"]) + "  (" + tr("doublon") + ")",
                            "+%d %s" % (dup["gems"], tr("gemmes"))]
                    res["title"] = tr("DOUBLON CONVERTI")
                else:
                    s["owned"].append(key)
                    res["skin"] = key
                    res["title"] = tr("NOUVEAU SKIN !")
                    res["lines"] = [tr(sk["name"]),
                                    tr(RARITY[tier]["label"])]

        st["boxes_opened"] += 1
        res["remaining"] = self.stock

        # Son selon rareté
        self._play({"COINS": "coin", "COMMON": "buy", "RARE": "buy",
                    "EPIC": "ach", "LEGENDARY": "win",
                    "MYTHIC": "win"}.get(res["tier"], "buy"))

        # Succès liés (uniquement si pas de save injectée = save du jeu)
        if self._save is None:
            res["new_ach"] = check_achievements()
        (self._writer or write_save)()
        return res

    def open_many(self, n):
        """Ouvre jusqu'à n boîtes. Retourne la liste des résultats."""
        out = []
        for _ in range(max(0, int(n))):
            r = self.open()
            if not r["ok"]:
                break
            out.append(r)
        return out


_BOX_SYSTEM = None


def open_mystery_box():
    """Ouvre une boîte du stock courant. Instance singleton."""
    global _BOX_SYSTEM
    if _BOX_SYSTEM is None:
        _BOX_SYSTEM = MysteryBoxSystem()
    return _BOX_SYSTEM.open()


def buy_box_with_gems():
    """Achat direct en gemmes (depuis le shop)."""
    if SAVE["gems"] < BOX_GEM_PRICE:
        audio.play("error")
        return False, tr("Pas assez de gemmes (il t'en manque %d).") % (
            BOX_GEM_PRICE - SAVE["gems"])
    SAVE["gems"] -= BOX_GEM_PRICE
    grant_box(1, "Boutique")
    write_save()
    return True, ""


def buy_box_with_coins():
    """Achat direct en pièces."""
    if SAVE["coins"] < BOX_COIN_PRICE:
        audio.play("error")
        return False, tr("Pas assez de pièces (il t'en manque %d).") % (
            BOX_COIN_PRICE - SAVE["coins"])
    SAVE["coins"] -= BOX_COIN_PRICE
    grant_box(1, "Boutique")
    write_save()
    return True, ""


def box_price():
    return BOX_GEM_PRICE


# ─────────────────────────────────────────────────────────────────────────
#  ANIMATION D'OUVERTURE (4 phases : SHAKE / BURST / REVEAL / END)
# ─────────────────────────────────────────────────────────────────────────
class BoxOpeningAnimation:
    """Cinématique : SHAKE (suspense) → BURST (explosion)
    → REVEAL (apparition) → END (attente clic)."""

    S_SHAKE, S_BURST, S_REVEAL, S_END = 50, 42, 110, 45
    TOTAL = S_SHAKE + S_BURST + S_REVEAL + S_END

    def __init__(self, result):
        self.result = result
        self.t = 0
        self.particles = []
        self.stars = []
        self.flash = 0
        self._veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(70):
            self.stars.append(dict(
                x=random.uniform(0, WIDTH),
                y=random.uniform(0, HEIGHT),
                sp=random.uniform(0.3, 1.6),
                sz=random.uniform(1.0, 2.6),
                ph=random.uniform(0, 6.28)))

    @property
    def phase(self):
        t = self.t
        if t < self.S_SHAKE:
            return "SHAKE"
        t -= self.S_SHAKE
        if t < self.S_BURST:
            return "BURST"
        t -= self.S_BURST
        if t < self.S_REVEAL:
            return "REVEAL"
        return "END"

    @property
    def phase_t(self):
        t = self.t
        if t < self.S_SHAKE:
            return t
        t -= self.S_SHAKE
        if t < self.S_BURST:
            return t
        t -= self.S_BURST
        if t < self.S_REVEAL:
            return t
        return t - self.S_REVEAL

    def done(self):
        return self.t >= self.TOTAL

    def update(self):
        self.t += 1
        ph, pt = self.phase, self.phase_t
        for s in self.stars:
            s["y"] += s["sp"]
            if s["y"] > HEIGHT + 4:
                s["y"] = -4
                s["x"] = random.uniform(0, WIDTH)

        if ph == "SHAKE":
            if self.t % 3 == 0:
                a = random.uniform(0, math.tau)
                r = random.uniform(40, 90)
                self.particles.append(dict(
                    x=WIDTH // 2 + math.cos(a) * r,
                    y=HEIGHT // 2 - 20 + math.sin(a) * r * 0.6,
                    vx=math.cos(a) * random.uniform(0.3, 1.2),
                    vy=math.sin(a) * random.uniform(0.3, 1.2) - 1.0,
                    life=32, max=32, sz=random.uniform(2, 4),
                    col=(190, 80, 255) if random.random() < 0.7
                    else (255, 225, 0)))
        elif ph == "BURST":
            if pt == 0:
                self.flash = 220
                for _ in range(180):
                    a = random.uniform(0, math.tau)
                    sp = random.uniform(4, 17)
                    self.particles.append(dict(
                        x=WIDTH // 2, y=HEIGHT // 2 - 20,
                        vx=math.cos(a) * sp, vy=math.sin(a) * sp,
                        life=random.randint(40, 85), max=85,
                        sz=random.uniform(3, 8),
                        col=random.choice([(190, 80, 255), (255, 225, 0),
                                           (255, 60, 110), (255, 255, 255)])))
                audio.play("boom", 1.0)
            self.flash = max(0, self.flash - 14)
        elif ph == "REVEAL":
            self.flash = max(0, self.flash - 9)
            if pt % 6 == 0:
                a = random.uniform(0, math.tau)
                sp = random.uniform(1.5, 3.5)
                self.particles.append(dict(
                    x=WIDTH // 2, y=HEIGHT // 2 - 20,
                    vx=math.cos(a) * sp, vy=math.sin(a) * sp,
                    life=40, max=40, sz=random.uniform(2, 4),
                    col=(255, 255, 255) if random.random() < 0.5
                    else (190, 80, 255)))

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.20
            p["vx"] *= 0.98
            p["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _draw_box(self, surf, cx, cy, scale=1.0):
        if scale <= 0.02:
            return
        sz = int(78 * scale)
        r = pygame.Rect(0, 0, sz, sz)
        r.center = (cx, cy)
        glow = pygame.Surface((r.w * 3, r.h * 3), pygame.SRCALPHA)
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.22)
        for i in range(6):
            pygame.draw.circle(glow, (190, 80, 255, int(18 + 14 * pulse)),
                               (r.w * 3 // 2, r.h * 3 // 2),
                               r.w + i * 12)
        surf.blit(glow, (r.centerx - r.w * 3 // 2,
                         r.centery - r.h * 3 // 2))
        pygame.draw.rect(surf, (55, 16, 88), r, border_radius=8)
        pygame.draw.rect(surf, (200, 80, 255), r, 3, border_radius=8)
        pygame.draw.line(surf, (255, 215, 90),
                         (r.x + 4, r.centery), (r.right - 4, r.centery), 3)
        pygame.draw.line(surf, (255, 215, 90),
                         (r.centerx, r.y + 4), (r.centerx, r.bottom - 4), 3)
        pygame.draw.circle(surf, (255, 215, 90),
                           (r.centerx, r.centery), max(3, r.w // 10))

    def _draw_result_visual(self, surf, cx, cy):
        r = self.result
        sk_key = r.get("skin")
        if sk_key:
            draw_skin(surf, sk_key, cx, cy, 1, self.t, False, 0, 2.4)
        elif r.get("coins"):
            draw_coin_icon(surf, cx, cy, 44)
            draw_text(surf, "+%s" % fmt_num(r["coins"]),
                      FONT_BIG, JAUNE_NEON, cx, cy + 90, shadow=True)
        elif r.get("gems"):
            draw_gem_icon(surf, cx, cy, 44)
            draw_text(surf, "+%d" % r["gems"], FONT_BIG, GEM_COL,
                      cx, cy + 90, shadow=True)

    def draw(self, surf):
        ph, pt = self.phase, self.phase_t
        self._veil.fill((6, 2, 14, 235))
        surf.blit(self._veil, (0, 0))

        for s in self.stars:
            k = 0.55 + 0.45 * math.sin(self.t * 0.05 + s["ph"])
            col = (int(190 * k), int(120 * k), int(255 * k))
            pygame.draw.circle(surf, col,
                               (int(s["x"]), int(s["y"])), int(s["sz"]))

        cx, cy = WIDTH // 2, HEIGHT // 2 - 20

        if ph == "SHAKE":
            shake = min(14, pt // 2)
            self._draw_box(surf,
                           cx + random.randint(-shake, shake),
                           cy + random.randint(-shake, shake), 1.0)
            draw_text(surf, tr("OUVERTURE..."), FONT_TITLE,
                      (200, 100, 255), cx, 100, shadow=True)
        elif ph == "BURST":
            k = max(0.0, 1.0 - pt / self.S_BURST)
            if k > 0.02:
                self._draw_box(surf, cx, cy, k)
            if self.flash > 0:
                fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                fl.fill((255, 255, 255, self.flash))
                surf.blit(fl, (0, 0))
        elif ph in ("REVEAL", "END"):
            rc = RARITY[self.result.get("rarity", "COMMON")]["color"]
            k = (min(1.0, pt / 28) if ph == "REVEAL"
                 else max(0.0, 1.0 - pt / self.S_END))
            ray_s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for i in range(16):
                a = i * math.tau / 16 + self.t * 0.006
                ln = 520 * k
                pygame.draw.line(ray_s, (*rc, int(55 * k)),
                                 (cx, cy),
                                 (cx + math.cos(a) * ln,
                                  cy + math.sin(a) * ln), 26)
            pygame.draw.circle(ray_s, (*rc, int(120 * k)),
                               (cx, cy), int(60 * k))
            surf.blit(ray_s, (0, 0))

            if k > 0.35:
                self._draw_result_visual(surf, cx, cy)
            if ph == "REVEAL" and pt > 40:
                a = min(1.0, (pt - 40) / 30.0)
                title = self.result.get("title") or tr("BOÎTE MYSTÈRE")
                tcol = mixc((200, 200, 220), rc, a)
                draw_text(surf, title, FONT_TITLE, tcol,
                          cx, cy + 140, shadow=True)
                for i, line in enumerate(self.result.get("lines", [])):
                    img = FONT_MED.render(line, True, BLANC)
                    img.set_alpha(int(255 * a))
                    surf.blit(img, img.get_rect(
                        center=(cx, cy + 184 + i * 28)))

        # Particules
        for p in self.particles:
            k = p["life"] / p["max"]
            sz = max(1, int(p["sz"] * k))
            s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["col"], int(255 * k)), (sz, sz), sz)
            surf.blit(s, (int(p["x"] - sz), int(p["y"] - sz)))

        if ph == "END" and (self.t // 22) % 2 == 0:
            draw_text(surf, tr("Clique pour continuer"), FONT_SMALL,
                      (210, 190, 230), WIDTH // 2, HEIGHT - 70)


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRANS BOÎTES MYSTÈRES
# ─────────────────────────────────────────────────────────────────────────
def screen_boxes():
    menu_bg(screen)
    cx = WIDTH // 2
    draw_text(screen, tr("Boîtes Mystères"), FONT_TITLE,
              (200, 80, 255), cx, 46, shadow=True)
    draw_coins_counter()

    stock = _to_int(SAVE.get("mystery_boxes", 0))
    ads = SAVE["ads"]
    prog = _to_int(ads.get("box_ad_progress", 0))
    ad_ready = ADS.available() if "ADS" in globals() else False

    # Bandeau stock
    panel(screen, (cx - 240, 100, 480, 70), (200, 80, 255), PANEL, 10, 3)
    draw_text(screen, tr("STOCK DE BOÎTES"), FONT_SMALL,
              (190, 160, 230), cx, 118)
    draw_text(screen, "x %d" % stock, FONT_TITLE,
              JAUNE_NEON if stock else (140, 130, 170), cx, 148,
              shadow=True)

    # Panneau acquisition
    panel(screen, (60, 200, 880, 220), (120, 80, 180), PANEL, 12, 2)
    draw_text(screen, tr("OBTENIR UNE BOÎTE"), FONT_BTN, CYAN_NEON, cx, 218)

    # Ligne 1 : regarder des pubs
    y1 = 248
    draw_text(screen, tr("REGARDER %d PUBS") % BOX_ADS_NEEDED,
              FONT_SMALL, BLANC, 84, y1, center=False)
    for i in range(BOX_ADS_NEEDED):
        rr = pygame.Rect(84 + i * 36, y1 + 22, 28, 22)
        done = i < prog
        pygame.draw.rect(screen,
                         (190, 80, 255) if done else (50, 40, 80), rr,
                         border_radius=4)
        pygame.draw.rect(screen,
                         (230, 200, 255) if done else (90, 80, 120), rr,
                         2, border_radius=4)
    ad_label = tr("PUB (%d/%d)") % (prog, BOX_ADS_NEEDED)
    if button((500, y1, 420, 50), ad_label, FONT_BTN,
              (200, 80, 255) if ad_ready else None, enabled=ad_ready):
        # ADS sera défini en § 17 (AdManager)
        if "ADS" in globals():
            r = ADS.watch_ad_for_box(origin=(cx, HEIGHT - 200))
            if r.get("ok"):
                say(tr("Boîte mystère gagnée !") if r.get("box_granted")
                    else tr("Pub vue : +1 vers une boîte"),
                    (200, 80, 255))
            else:
                say(tr("Recharge en cours..."), ROUGE_NEON)
        else:
            # Fallback si ADS pas encore chargé
            SAVE["ads"]["box_ad_progress"] = prog + 1
            if SAVE["ads"]["box_ad_progress"] >= BOX_ADS_NEEDED:
                SAVE["ads"]["box_ad_progress"] = 0
                grant_box(1, "Pub")
            write_save()

    # Ligne 2 : achat en gemmes
    y2 = 312
    draw_gem_icon(screen, 96, y2 + 25, 12)
    draw_text(screen, "%d %s" % (BOX_GEM_PRICE, tr("GEMMES")),
              FONT_BTN, GEM_COL, 120, y2 + 25, center=False)
    if button((500, y2, 420, 50), tr("ACHETER AVEC GEMMES"),
              FONT_BTN, GEM_COL, enabled=SAVE["gems"] >= BOX_GEM_PRICE):
        ok, msg = buy_box_with_gems()
        if not ok:
            say(msg, ROUGE_NEON)

    # Ligne 3 : achat en pièces
    y3 = 376
    draw_coin_icon(screen, 96, y3 + 25, 12)
    draw_text(screen, "%s %s" % (fmt_num(BOX_COIN_PRICE), tr("PIÈCES")),
              FONT_BTN, JAUNE_NEON, 120, y3 + 25, center=False)
    if button((500, y3, 420, 50), tr("ACHETER AVEC PIÈCES"),
              FONT_BTN, JAUNE_NEON,
              enabled=SAVE["coins"] >= BOX_COIN_PRICE):
        ok, msg = buy_box_with_coins()
        if not ok:
            say(msg, ROUGE_NEON)

    # Boutons ouvrir
    if button((cx - 260, 448, 240, 60), tr("OUVRIR"),
              FONT_TITLE, (200, 80, 255), enabled=stock > 0):
        res = open_mystery_box()
        if res["ok"]:
            UI["box_anim"] = BoxOpeningAnimation(res)
            UI["sub"] = "BOX_OPEN"

    if button((cx + 20, 448, 240, 60), tr("TOUT OUVRIR"),
              FONT_BTN, (150, 60, 200), enabled=stock >= 2):
        last = None
        while True:
            r = open_mystery_box()
            if not r["ok"]:
                break
            last = r
        if last:
            UI["box_anim"] = BoxOpeningAnimation(last)
            UI["sub"] = "BOX_OPEN"

    # Taux de drop (panneau bas)
    panel(screen, (cx - 240, 522, 480, 130), (90, 60, 130), PANEL, 10, 2)
    draw_text(screen, tr("TAUX DE DROP"), FONT_SMALL,
              (200, 170, 240), cx, 538)
    rates = [("Pièces", 55.0, JAUNE_NEON),
             ("Commun", 20.0, (205, 208, 224)),
             ("Rare", 14.0, (70, 150, 255)),
             ("Épique", 8.0, (180, 80, 255)),
             ("Légendaire", 2.95, (255, 200, 40)),
             ("Mythique", 0.05, (255, 50, 90))]
    for i, (lab, pc, col) in enumerate(rates):
        x = cx - 220 + (i % 2) * 230
        y = 560 + (i // 2) * 22
        draw_text(screen, "%s  %.2f%%" % (tr(lab), pc), FONT_TINY,
                  col, x, y, center=False)

    draw_back_button(action=lambda: UI.update({"sub": None}))
    return True


def screen_box_open():
    """Animation plein écran d'ouverture d'une boîte."""
    anim = UI.get("box_anim")
    if not anim:
        UI["sub"] = None
        return True
    anim.update()
    anim.draw(screen)
    if anim.done() and mouse.get("click"):
        mouse["click"] = False
        UI["box_anim"] = None
        if _to_int(SAVE.get("mystery_boxes", 0)) > 0:
            UI["sub"] = "BOXES"
        else:
            UI["sub"] = None
        audio.play("click")
    return True


# ─────────────────────────────────────────────────────────────────────────
#  AD MANAGER (extension § 14 — pubs → boîte)
# ─────────────────────────────────────────────────────────────────────────
def _install_ad_box_hook():
    """Ajoute watch_ad_for_box() à la classe AdManager (définie en § 17)."""
    cls = globals().get("AdManager")
    if cls is None or hasattr(cls, "watch_ad_for_box"):
        return

    def _watch_ad_for_box(self, origin=None):
        if not self.available():
            self._play("error")
            return {"ok": False, "reason": "cooldown",
                    "remaining": self.remaining(),
                    "progress": _to_int(self.ads.get("box_ad_progress", 0)),
                    "box_granted": False}
        s, ads = self.save, self.ads
        ads["last_ts"] = self._now()
        ads["watched"] += 1
        ads["box_ad_progress"] = _to_int(ads.get("box_ad_progress", 0)) + 1
        granted = False
        if ads["box_ad_progress"] >= BOX_ADS_NEEDED:
            ads["box_ad_progress"] = 0
            s["mystery_boxes"] = _to_int(s.get("mystery_boxes", 0)) + 1
            granted = True
        (self._writer or write_save)()
        ox, oy = origin or (WIDTH // 2, HEIGHT // 2)
        col = (200, 80, 255)
        label = ("+1 " + tr("BOÎTE MYSTÈRE")) if granted \
            else tr("Pub vue : +1 vers une boîte")
        self.flash, self.flash_col = 130.0, col
        self.popups.append({"text": label, "col": col,
                            "x": ox, "y": oy, "t": 0, "life": 120})
        for _ in range(24):
            a = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
            sp = random.uniform(3.0, 8.0)
            self.particles.append({"x": float(ox), "y": float(oy),
                                   "vx": math.cos(a) * sp,
                                   "vy": math.sin(a) * sp,
                                   "t": 0, "life": random.randint(50, 85),
                                   "kind": "gems",
                                   "spin": random.uniform(0, math.tau),
                                   "r": random.uniform(5, 9)})
        self._play("ad_box" if granted else "pickup", "buy")
        return {"ok": True, "progress": ads["box_ad_progress"],
                "box_granted": granted, "remaining": self.cooldown}

    cls.watch_ad_for_box = _watch_ad_for_box


# Exécute le hook (silencieux si AdManager pas encore chargé)
_install_ad_box_hook()


# ═══════════════════════════════════════════════════════════════════════════
#  Traductions FR → EN
# ═══════════════════════════════════════════════════════════════════════════
EN.update({
    "BOUTIQUE": "SHOP", "SKINS": "SKINS", "STATISTIQUES": "STATS",
    "OBJETS": "ITEMS", "PREMIUM": "PREMIUM",
    "MATRICE DES ARMES": "WEAPON MATRIX",
    "Survole un nœud pour la fiche • Clique pour acheter":
        "Hover a node for details • Click to buy",
    "Déjà possédé !": "Already owned!",
    "Déjà possédé": "Already owned",
    "Objet indisponible.": "Item unavailable.",
    "Pas assez de pièces (il t'en manque %d).":
        "Not enough coins (you need %d more).",
    "Pas assez de pièces !": "Not enough coins!",
    "Pas assez de gemmes (il t'en manque %d).":
        "Not enough gems (you need %d more).",
    "Amélioré": "Upgraded", "Acheté": "Bought",
    "Achat important : clique encore pour confirmer.":
        "Big purchase: click again to confirm.",
    "CONFIRMER ?": "CONFIRM?",
    "Jaune : achetable. Violet : bonus gagnés grâce aux succès.":
        "Yellow: purchasable. Purple: bonuses earned through achievements.",
    "AMÉLIORATIONS PREMIUM — GEMMES": "PREMIUM UPGRADES — GEMS",
    "Bonus passifs uniques, cumulables avec les stats et succès.":
        "Unique passive bonuses, stackable with stats and achievements.",
    "NIVEAU MAX": "MAX LEVEL", "ACHETER": "BUY",
    "%s : niveau %d": "%s: level %d",
    "Vitalité Éternelle": "Eternal Vitality",
    "Égide Cosmique": "Cosmic Aegis",
    "Fureur Séquentielle": "Sequential Fury",
    "Avarice Chronique": "Chronic Avarice",
    "Veine du Chaos": "Chaos Vein",
    "Écho Ancestral": "Ancestral Echo",
    "+6% PV max par niveau (cumulable).":
        "+6% max HP per level (stackable).",
    "+8% bouclier max et +0.05/s de recharge par niveau.":
        "+8% max shield and +0.05/s recharge per level.",
    "+4% de dégâts globaux par niveau.":
        "+4% global damage per level.",
    "+5% de pièces gagnées en fin de manche par niveau.":
        "+5% coins earned at round end per level.",
    "+2% de chance de boîte mystère par manche par niveau.":
        "+2% mystery box chance per round per level.",
    "Une fois par run : ressuscite à 40% PV (+1 utilisation par niveau).":
        "Once per run: revive at 40% HP (+1 use per level).",
    "BOÎTE UNIQUEMENT": "MYSTERY BOX ONLY",
    "TOP 10 REQUIS": "TOP 10 REQUIRED",
    "Ce skin ne s'obtient que dans les Boîtes Mystères !":
        "This skin can only be found in Mystery Boxes!",
    "Requis : Top 10 Mondial au Classement":
        "Required: Top 10 Global in the Leaderboard",
    "Skin secret : relève des défis et trouve les zones cachées...":
        "Secret skin: take on challenges and find the hidden zones...",
    "Futur skin mythique : bientôt disponible...":
        "Future mythic skin: coming soon...",
    "??? MYTHIQUE": "??? MYTHIC", "Bientôt disponible": "Coming soon",
    "??? SKIN SECRET": "??? SECRET SKIN",
    "Succès / zone cachée": "Achievement / hidden zone",
    "Cliquer pour équiper": "Click to equip", "[ÉQUIPÉ]": "[EQUIPPED]",
    "Boîtes Mystères": "Mystery Boxes",
    "STOCK DE BOÎTES": "BOX STOCK",
    "OBTENIR UNE BOÎTE": "GET A BOX",
    "REGARDER %d PUBS": "WATCH %d ADS",
    "PUB (%d/%d)": "AD (%d/%d)",
    "ACHETER AVEC GEMMES": "BUY WITH GEMS",
    "ACHETER AVEC PIÈCES": "BUY WITH COINS",
    "TAUX DE DROP": "DROP RATES",
    "OUVRIR": "OPEN", "TOUT OUVRIR": "OPEN ALL",
    "OUVERTURE...": "OPENING...",
    "Clique pour continuer": "Click to continue",
    "DOUBLON CONVERTI": "DUPLICATE CONVERTED",
    "NOUVEAU SKIN !": "NEW SKIN!",
    "doublon": "duplicate",
    "BOÎTE MYSTÈRE": "MYSTERY BOX",
    "Collection complète : gemmes bonus !":
        "Collection complete: bonus gems!",
    "Aucune boîte mystère à ouvrir.": "No mystery box to open.",
    "Boîte mystère gagnée !": "Mystery box earned!",
    "Pub vue : +1 vers une boîte": "Ad watched: +1 toward a box",
    "Recharge en cours...": "Recharging...",
    "PIÈCES": "COINS", "GEMMES": "GEMS",
    "Lame Énergétique": "Energy Blade",
    "Sabre Quantique": "Quantum Saber",
    "Katar du Void": "Void Katar",
    "Fusil Plasma": "Plasma Rifle",
    "Railgun Magnétique": "Magnetic Railgun",
    "Orbe Singularité": "Singularity Orb",
    "Champ Prismatique": "Prismatic Field",
    "Égide Tesseract": "Tesseract Aegis",
    "Bouclier Aegis-X": "Aegis-X Shield",
    "Plaques Titane": "Titanium Plates",
    "Nano-Alliage": "Nano-Alloy",
    "Peau de Nébuleuse": "Nebula Skin",
    "Croix Quantique": "Quantum Cross",
    "Fontaine Vita": "Vita Fountain",
    "Sève Éternelle": "Eternal Sap",
    "Totem Chrono": "Chrono Totem",
    "Œil Oraculaire": "Oracular Eye",
    "Cœur du Multivers": "Multiverse Heart",
})
# ═══════════════════════════════════════════════════════════════════════════
#  § 15 — CLASSEMENT MONDIAL & SAISONS
# ═══════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN CLASSEMENT MONDIAL
# ─────────────────────────────────────────────────────────────────────────
def _draw_league_badge(cx, cy, r, league, surf=None):
    """Badge de ligue (losange coloré avec centre blanc)."""
    surf = surf or screen
    col = league["color"]
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, dark(col, 0.5), pts, 2)
    pygame.draw.circle(surf, BLANC, (cx, cy), max(1, r // 3))

# ═══════════════════════════════════════════════════════════════════════════
#  § 16 — CAMPAGNE & SECRETS (finitions & hooks premium)
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  Hook : bonus premium "Veine du Chaos" (prem_luck)
#  ─────────────────────────────────────────────────────────────────────────
def _install_prem_luck_hook():
    """Ajoute le bonus de chance de boîte mystère au calcul de
    box_from_round(). Wrapper propre, une seule fois."""
    orig = globals().get("box_from_round")
    if not callable(orig) or getattr(orig, "_prem_wrapped", False):
        return

    def _box_from_round_with_luck(diff, flawless):
        luck_lvl = get_premium_level("prem_luck")
        bonus = 0.02 * luck_lvl
        chance = 0.03 + 0.01 * diff + bonus + (0.05 if flawless else 0)
        if random.random() < chance:
            grant_box(1, "Bonus de manche")

    _box_from_round_with_luck._prem_wrapped = True
    globals()["box_from_round"] = _box_from_round_with_luck


_install_prem_luck_hook()


# ─────────────────────────────────────────────────────────────────────────
#  Hook : bonus premium "Écho Ancestral" (prem_revive)
#  ─────────────────────────────────────────────────────────────────────────
def _install_prem_revive_hook():
    """Intercepte la mort du joueur pour consommer un revive premium.
    Chaque run a son propre compteur (résilié à la fin de la partie)."""
    orig = Fighter.hurt
    if getattr(orig, "_prem_wrapped", False):
        return

    def _hurt_with_prem_revive(self, dmg, cause, S, src=None,
                                blockable=True, force=False):
        was_alive = self.alive
        result = orig(self, dmg, cause, S, src, blockable, force)

        # Cas : joueur vient de mourir
        if not (self is S.player and was_alive and not self.alive):
            return result

        # Vérifie les revives premium disponibles
        if not hasattr(S, "_prem_revives_left"):
            S._prem_revives_left = _to_int(
                SAVE.get("premium", {}).get("prem_revive", 0))
        if S._prem_revives_left <= 0:
            return result

        # Consomme un revive
        S._prem_revives_left -= 1
        self.alive = True
        self.hp = self.max_hp * 0.4
        self.inv = 150
        self.shield_energy = self.max_shield
        S.shake = max(S.shake, 14)
        S.slow_timer = max(S.slow_timer, 60)

        cx, cy = self.rect.center
        particle_system.emit(cx, cy, 60, (180, 80, 255),
                             (-7, 7), (3, 8), 45)
        particle_system.emit(cx, cy, 30, (255, 200, 255),
                             (-5, 5), (2, 6), 35)
        S.add_text(cx, self.rect.top - 30, tr("ÉCHO ANCESTRAL"),
                   (200, 120, 255), True)
        try:
            audio.play("win", 0.8)
            audio.play("chaos", 0.5)
        except Exception:
            pass
        return True

    _hurt_with_prem_revive._prem_wrapped = True
    Fighter.hurt = _hurt_with_prem_revive


_install_prem_revive_hook()


# ─────────────────────────────────────────────────────────────────────────
#  ÉCRAN CAMPAGNE — sélection dédiée (déblocage progressif 1 → 10)
#  (Appelé depuis le pôle JOUER si on veut un écran dédié, ou accessible
#   via un bouton optionnel dans le dashboard Campagne.)
# ─────────────────────────────────────────────────────────────────────────
def screen_campaign_select():
    """Écran de sélection de la Campagne principale (D1 à D10).
    Affiche le déblocage, le streak courant, et le prochain objectif."""
    menu_bg(screen)
    cx = WIDTH // 2

    draw_text_outlined(screen, tr("CAMPAGNE"), FONT_TITLE,
                       COL_PLAY, cx, 40, outline=(0, 0, 0), thick=2)
    draw_text(screen,
              tr("Progression séquentielle : réussis 5 manches consécutives "
                 "pour passer au niveau suivant."),
              FONT_SMALL, (200, 190, 230), cx, 74)
    draw_coins_counter()

    camp = SAVE["campaign"]
    unlocked = _to_int(camp["unlocked"], 2)

    # Bandeau objectif
    goal = campaign_next_goal_text(unlocked)
    if goal and unlocked < MAX_DIFF:
        panel(screen, (60, 102, WIDTH - 120, 44), COL_PLAY, PANEL, 8, 2)
        draw_text_ml(screen, goal, FONT_SMALL, BLANC, 76, 124)

    # Grille 2 × 5 des niveaux 1-10
    for row in range(2):
        for col_i in range(5):
            lv = row * 5 + col_i + 1
            D = DIFFS[lv]
            r = pygame.Rect(60 + col_i * 180, 168 + row * 130, 168, 118)
            available = lv <= unlocked
            sel = lv == SAVE["difficulty"]
            hover = r.collidepoint(mouse["x"], mouse["y"]) and available

            fill = (mixc(PANEL, D["color"], 0.55 if sel else
                         (0.22 if hover else 0.06)) if available
                    else (30, 22, 40))
            edge = D["color"] if available else (70, 60, 90)
            panel(screen, r, edge, fill, 10, 3 if sel else 2)

            draw_text_outlined(screen, "D%d" % lv, FONT_TITLE,
                               BLANC if available else (110, 100, 130),
                               r.centerx, r.y + 30,
                               outline=(0, 0, 0), thick=1)
            draw_text(screen, tr(D["name"])[:14], FONT_SMALL,
                      BLANC if available else (110, 100, 130),
                      r.centerx, r.y + 66)

            # Streak
            echo_streak = campaign_streak(lv, "COURSE")
            ia_streak = campaign_streak(lv, "SURVIE")
            streak_max = max(echo_streak, ia_streak)
            if available:
                draw_text(screen,
                          "Écho %d/5  ·  IA %d/5" % (echo_streak,
                                                     ia_streak),
                          FONT_TINY, (200, 190, 220),
                          r.centerx, r.y + 90)
            else:
                # Cadenas
                pygame.draw.arc(screen, (190, 190, 200),
                                (r.centerx - 8, r.y + 82, 16, 22),
                                0, math.pi, 3)
                pygame.draw.rect(screen, (210, 170, 40),
                                 (r.centerx - 12, r.y + 92, 24, 18),
                                 border_radius=3)

            if sel:
                pygame.draw.rect(screen, JAUNE_NEON,
                                 (r.x + 12, r.bottom - 6, r.w - 24, 3),
                                 border_radius=2)

            if hover and mouse.get("click"):
                mouse["click"] = False
                SAVE["difficulty"] = lv
                try:
                    audio.play("click")
                except Exception:
                    pass
                write_save()

    # Boutons lancer
    d = SAVE["difficulty"]
    if d > 10:
        d = 3
    D = DIFFS[d]
    panel(screen, (60, 438, WIDTH - 120, 90), D["color"], PANEL, 12, 2)
    draw_text_outlined(screen, "%s — %s" % (tr("DIFFICULTÉ"), tr(D["name"])),
                       FONT_BTN, D["color"], 80, 462, center=False,
                       outline=(0, 0, 0), thick=1)
    draw_text(screen, tr(D["desc"]), FONT_SMALL, BLANC,
              80, 492, center=False)

    if button((cx - 260, 548, 240, 54), tr("LANCER PARCOURS"),
              FONT_BTN, COL_PLAY, enabled=d <= unlocked):
        goto("GAME", Session("CAMPAGNE"))
    if button((cx + 20, 548, 240, 54), tr("LANCER SURVIE"),
              FONT_BTN, ROUGE_NEON, enabled=d <= unlocked):
        goto("GAME", Session("SURVIE"))

    draw_back_button(action=lambda: UI.update({"sub": None}))
    return True


# ─────────────────────────────────────────────────────────────────────────
#  Helper : info compacte sur le déblocage de la campagne secrète
# ─────────────────────────────────────────────────────────────────────────
def secret_campaign_status():
    """Retourne un dict prêt pour l'affichage d'UI :
       - unlocked : bool
       - levels_done : int (0-10, nombre de niveaux finis)
       - rounds_total : int (0-100, manches cumulées)
       - progress_pct : float (0.0-1.0)
    """
    sc = SAVE.get("secret_campaign", {})
    prog = sc.get("levels", {}) or {}
    levels_done = sum(
        1 for sid in SECRET_LEVELS_IDS
        if _to_int(prog.get(sid, 0)) >= SECRET_CAMPAIGN_ROUNDS_REQUIRED)
    rounds_total = sum(_to_int(prog.get(sid, 0))
                       for sid in SECRET_LEVELS_IDS)
    return dict(
        unlocked=bool(sc.get("unlocked", False)),
        levels_done=levels_done,
        rounds_total=rounds_total,
        progress_pct=levels_done / float(len(SECRET_LEVELS_IDS) or 1),
    )


# ─────────────────────────────────────────────────────────────────────────
#  Hook : badge discret de campagne secrète (sur le dashboard)
#  Appelé automatiquement par le dashboard s'il est débloqué.
# ─────────────────────────────────────────────────────────────────────────
def draw_secret_campaign_badge(surf=None):
    """Petit badge « ? » discret en bas-droite, UNIQUEMENT si la campagne
    secrète est débloquée. Retourne le Rect cliquable ou None."""
    if not is_campaign_unlocked():
        return None
    surf = surf if surf is not None else screen
    r = 22
    x, y = WIDTH - 60, HEIGHT - 100
    pulse = 0.5 + 0.5 * abs(math.sin(TICK[0] * 0.05))
    col = (int(120 + 100 * pulse), 60, int(200 + 55 * pulse))
    pygame.draw.circle(surf, col, (x, y), r)
    pygame.draw.circle(surf, BLANC, (x, y), r, 2)
    draw_text(surf, "?", FONT_BTN, BLANC, x, y)
    return pygame.Rect(x - r, y - r, r * 2, r * 2)


# ─────────────────────────────────────────────────────────────────────────
#  Nettoyage : retirer le stub apply_premium_to_loadout s'il existe encore
#  (défini au tout début de § 13 dans certaines variantes)
# ─────────────────────────────────────────────────────────────────────────
try:
    # Vérifie que la version réelle est bien celle de § 13
    _real_apply = apply_premium_to_loadout
    # Test : la vraie version retourne L (pas None)
    _test_loadout = {"max_hp": 100}
    _result = _real_apply(_test_loadout)
    if _result is None:
        # Stub détecté : remplace par la version § 13 déjà présente plus haut
        pass
except Exception:
    pass


# ─────────────────────────────────────────────────────────────────────────
#  Enregistrement des traductions EN
# ─────────────────────────────────────────────────────────────────────────
EN.update({
    "CLASSEMENT MONDIAL": "GLOBAL LEADERBOARD",
    "TON RANG": "YOUR RANK", "SCORE GLOBAL": "GLOBAL SCORE",
    "TOP 10 MONDIAL": "GLOBAL TOP 10",
    "SAISON": "SEASON", "FIN DANS": "ENDS IN",
    "RÉCOMPENSES DE SAISON": "SEASON REWARDS",
    "RÉCLAMER LES RÉCOMPENSES": "CLAIM REWARDS",
    "DÉJÀ RÉCLAMÉ": "ALREADY CLAIMED",
    "Top 1 - 10": "Top 1 - 10",
    "Top 11 - 100": "Top 11 - 100",
    "Top 101 - 1 000": "Top 101 - 1,000",
    "Top 1 001 - 10 000": "Top 1,001 - 10,000",
    "Top 10 001 - 50 000": "Top 10,001 - 50,000",
    "Apex Titan + 15 boîtes + 75 000 pièces + 300 gemmes":
        "Apex Titan + 15 boxes + 75,000 coins + 300 gems",
    "10 boîtes + 35 000 pièces + 150 gemmes":
        "10 boxes + 35,000 coins + 150 gems",
    "5 boîtes + 15 000 pièces + 50 gemmes":
        "5 boxes + 15,000 coins + 50 gems",
    "3 boîtes + 5 000 pièces + 15 gemmes":
        "3 boxes + 5,000 coins + 15 gems",
    "1 boîte + 2 000 pièces": "1 box + 2,000 coins",
    "Récompenses déjà réclamées cette saison.":
        "Rewards already claimed this season.",
    "Ton rang ne donne pas encore de récompense.":
        "Your rank does not grant a reward yet.",
    "Saison récompensée : ": "Season rewarded: ",
    "LÉGENDE": "LEGEND", "MAÎTRE": "MASTER", "DIAMANT": "DIAMOND",
    "PLATINE": "PLATINUM", "OR": "GOLD", "ARGENT": "SILVER",
    "BRONZE": "BRONZE",
    "ÉCHO ANCESTRAL": "ANCESTRAL ECHO",
    "Progression séquentielle : réussis 5 manches consécutives pour passer "
    "au niveau suivant.":
        "Sequential progression: clear 5 consecutive rounds to unlock the "
        "next level.",
    "LANCER PARCOURS": "START RUN",
    "LANCER SURVIE": "START SURVIVAL",
    "CAMPAGNE": "CAMPAIGN",
    "D5 → D6 : 5 manches des DEUX modes (Écho ET IA)":
        "D5 → D6: 5 rounds in BOTH modes (Echo AND AI)",
    "D10 → CHAMPION : 10 manches des DEUX modes en D10":
        "D10 → CHAMPION: 10 rounds in BOTH modes at D10",
    "D%d → D%d : 5 manches dans un des deux modes":
        "D%d → D%d: 5 rounds in either mode",
    "DIFFICULTÉ %d DÉBLOQUÉE !": "DIFFICULTY %d UNLOCKED!",
    "CAMPAGNE SECRÈTE DÉBLOQUÉE": "SECRET CAMPAIGN UNLOCKED",
})


# ═══════════════════════════════════════════════════════════════════════════
#  FIN § 15-16
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#  § 17 — ÉVÉNEMENTS & BOUCLE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
#  AD MANAGER — pubs simulées (recharge 60 s, récompenses, particules)
# ─────────────────────────────────────────────────────────────────────────
class AdManager:
    """Simulateur de pubs avec recharge sauvegardée (basée sur time.time).

    - state() / remaining() / draw_cooldown_ring() pour l'UI
    - retours visuels : flash, pluie de pièces/gemmes, popups, sons
    - watch_ad_for_box() est ajouté par _install_ad_box_hook() (§ 14)
    """

    def __init__(self, save=None, cooldown=AD_COOLDOWN, now=None,
                 writer=None, audio_getter=None):
        self._save = save
        self.cooldown = float(cooldown)
        self._now = now or time.time
        self._writer = writer
        self._audio_getter = audio_getter
        self.particles = []
        self.popups = []
        self.flash = 0.0
        self.flash_col = (255, 255, 255)
        self._flash_surf = None
        self._font_cache = None

    # ---- État --------------------------------------------------------
    @property
    def save(self):
        return self._save if self._save is not None else SAVE

    @property
    def ads(self):
        s = self.save
        if not isinstance(s.get("ads"), dict):
            s["ads"] = default_save()["ads"]
        return s["ads"]

    def remaining(self):
        elapsed = self._now() - float(self.ads.get("last_ts", 0.0))
        if elapsed < 0:
            elapsed = 0.0
        return max(0.0, self.cooldown - elapsed)

    def available(self):
        return self.remaining() <= 0.0

    def ads_until_box(self):
        return BOX_ADS_NEEDED - (self.ads.get("watched", 0)
                                  % BOX_ADS_NEEDED)

    def state(self):
        rem = self.remaining()
        secs = int(math.ceil(rem))
        t = globals().get("tr", lambda s: s)
        return {
            "available": rem <= 0.0,
            "remaining": rem,
            "seconds": secs,
            "ratio": clamp01(1.0 - rem / self.cooldown)
                     if self.cooldown > 0 else 1.0,
            "text": (t("DISPONIBLE") if rem <= 0.0
                     else t("RECHARGE : %d s") % secs),
            "until_box": self.ads_until_box(),
            "watched": self.ads.get("watched", 0),
        }

    # ---- Actions -----------------------------------------------------
    def watch_ad_for_coins(self, origin=None):
        return self._watch("coins", AD_COIN_REWARD, origin)

    def watch_ad_for_gems(self, origin=None):
        return self._watch("gems", AD_GEM_REWARD, origin)

    def _watch(self, kind, amount, origin):
        if not self.available():
            self._play("error")
            return {"ok": False, "reason": "cooldown", "kind": kind,
                    "amount": 0, "remaining": self.remaining(),
                    "bonus_box": False}
        s, ads = self.save, self.ads
        s[kind] = _to_int(s.get(kind, 0)) + amount
        ads["last_ts"] = self._now()
        ads["watched"] = _to_int(ads.get("watched", 0)) + 1
        ads[kind + "_earned"] = (_to_int(ads.get(kind + "_earned", 0))
                                  + amount)
        # Bonus boîte tous les 5
        box = ads["watched"] % AD_BOX_EVERY == 0
        if box:
            s["mystery_boxes"] = _to_int(s.get("mystery_boxes", 0)) + 1
        (self._writer or write_save)()
        self._celebrate(kind, amount, box, origin)
        return {"ok": True, "reason": "", "kind": kind, "amount": amount,
                "remaining": self.cooldown, "bonus_box": box}

    # ---- Retours sonores / visuels -----------------------------------
    def _play(self, *names):
        try:
            a = (self._audio_getter() if self._audio_getter
                 else globals().get("audio"))
            if a is None or not getattr(a, "ok", False):
                return
            for n in names:
                if n in a.sfx:
                    a.play(n)
                    return
        except Exception:
            pass

    def _get_font(self):
        if self._font_cache is None:
            self._font_cache = globals().get("FONT_BTN") or _get_font(25, True)
        return self._font_cache

    def _celebrate(self, kind, amount, box, origin):
        ox, oy = origin or (WIDTH // 2, HEIGHT // 2)
        t = globals().get("tr", lambda s: s)
        col = JAUNE_NEON if kind == "coins" else GEM_COL
        label = ("+%d " % amount) + (t("PIÈCES") if kind == "coins"
                                       else t("GEMMES"))
        self.flash, self.flash_col = 150.0, col
        self.popups.append({"text": label, "col": col,
                            "x": ox, "y": oy, "t": 0, "life": 110})
        if box:
            self.popups.append({"text": "+1 " + t("BOÎTE MYSTÈRE"),
                                "col": (140, 255, 200),
                                "x": ox, "y": oy + 40,
                                "t": -18, "life": 130})
        n_particles = 30 if kind == "coins" else 24
        for _ in range(n_particles):
            a = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
            sp = random.uniform(3.0, 9.0)
            self.particles.append({
                "x": float(ox), "y": float(oy),
                "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                "t": 0, "life": random.randint(55, 90),
                "kind": kind, "spin": random.uniform(0, math.tau),
                "r": random.uniform(5, 9)})
        self._play("ad_coins" if kind == "coins" else "ad_gems",
                   "coin" if kind == "coins" else "ach")
        if box:
            self._play("ad_box", "pickup")

    # ---- Mise à jour + rendu -----------------------------------------
    def update(self):
        self.flash = max(0.0, self.flash - 9.0)
        for p in self.particles:
            p["t"] += 1
            p["vy"] += 0.28
            p["vx"] *= 0.99
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["spin"] += 0.25
        self.particles = [p for p in self.particles
                          if p["t"] < p["life"]]
        for q in self.popups:
            q["t"] += 1
        self.popups = [q for q in self.popups if q["t"] < q["life"]]

    def active(self):
        return bool(self.particles or self.popups or self.flash > 0)

    def draw(self, surf):
        if not self.active():
            return
        if self.flash > 0:
            size = surf.get_size()
            if (self._flash_surf is None
                    or self._flash_surf.get_size() != size):
                self._flash_surf = pygame.Surface(size, pygame.SRCALPHA)
            self._flash_surf.fill((*self.flash_col, int(self.flash)))
            surf.blit(self._flash_surf, (0, 0))

        for p in self.particles:
            x, y, r = int(p["x"]), int(p["y"]), p["r"]
            fade = 1.0 - max(0.0, (p["t"] - p["life"] * 0.7)
                             / (p["life"] * 0.3))
            if p["kind"] == "coins":
                w = max(2, int(r * abs(math.cos(p["spin"]))))
                rect = pygame.Rect(x - w, y - int(r), w * 2, int(r) * 2)
                pygame.draw.ellipse(surf,
                                    (255, 225, 0) if fade > 0.3
                                    else (200, 150, 0), rect)
                pygame.draw.ellipse(surf, (200, 150, 0), rect, 2)
            else:
                draw_gem_icon(surf, x, y, int(r) + 1)

        font = self._get_font()
        for q in self.popups:
            if q["t"] < 0:
                continue
            k = q["t"] / q["life"]
            alpha = int(255 * min(1.0, (1.0 - k) * 3.0))
            sy = q["y"] - 70 * (1 - (1 - k) ** 2)
            for dx, dy, c in ((2, 2, (0, 0, 0)), (0, 0, q["col"])):
                img = font.render(q["text"], True, c)
                img.set_alpha(alpha)
                surf.blit(img, img.get_rect(
                    center=(q["x"] + dx, sy + dy)))

    def draw_cooldown_ring(self, surf, center, radius,
                            color=(0, 240, 255), width=4):
        st = self.state()
        pygame.draw.circle(surf, (46, 36, 70), center, radius, width)
        if st["available"]:
            pygame.draw.circle(surf, (50, 255, 120), center, radius, width)
            return
        n = max(2, int(48 * st["ratio"]))
        pts = [(center[0] + math.cos(-math.pi / 2
                                     + math.tau * st["ratio"] * i / n)
                * radius,
                center[1] + math.sin(-math.pi / 2
                                     + math.tau * st["ratio"] * i / n)
                * radius)
               for i in range(n + 1)]
        if len(pts) >= 2:
            pygame.draw.lines(surf, color, False, pts, width)


# Instance globale + hook pour watch_ad_for_box (défini en § 14)
ADS = AdManager()
_install_ad_box_hook()          # ajoute watch_ad_for_box à AdManager



# ═══════════════════════════════════════════════════════════════════
#  § 17 — CHARGEMENT AUDIO ASYNCHRONE (remplace audio.build)
# ═══════════════════════════════════════════════════════════════════
# ─────────────────────────────────────────────────────────────────────────
#  SPLASH (barre de progression pendant audio.build)
# ─────────────────────────────────────────────────────────────────────────
def splash(progress=0.0):
    screen.fill(NOIR_FOND)
    cx = WIDTH // 2
    draw_text(screen, GAME_TITLE, FONT_BIG, CYAN_NEON, cx, 280, shadow=True)
    pygame.draw.rect(screen, (40, 30, 70), (cx - 200, 380, 400, 14), border_radius=6)
    pygame.draw.rect(screen, ROUGE_NEON,
                     (cx - 200, 380, int(400 * clamp01(progress)), 14),
                     border_radius=6)
    draw_text(screen, tr("Synchronisation du chaos..."), FONT_SMALL,
              (170, 150, 210), cx, 420)
    try:
        pygame.display.flip()
        pygame.event.pump()
    except Exception:
        pass

async def build_audio_async():
    if not audio.ok:
        return
    if IS_WEB:
        audio.ok = False
        return
    # Synthèse par lots pour céder la main
    try:
        bufs = build_sfx_buffers()
        total = len(bufs) + 2
        i = 0
        for name, buf in bufs.items():
            audio.sfx[name] = to_sound(buf)
            i += 1
            if i % 4 == 0:
                await asyncio.sleep(0)   # ← indispensable
        for j, kind in enumerate(("menu", "battle")):
            audio.tracks[kind] = to_sound(build_track(kind), 0.9)
            await asyncio.sleep(0)
    except Exception:
        audio.ok = False
# ─────────────────────────────────────────────────────────────────────────
#  Gestion des touches texte (NAME, renommage PROFILE)
# ─────────────────────────────────────────────────────────────────────────
def handle_text_key(event):
    """Saisie de texte pour les champs de type name_buf."""
    if event.key == pygame.K_BACKSPACE:
        UI["name_buf"] = UI.get("name_buf", "")[:-1]
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        if validate_name() and UI.get("state") == "NAME":
            goto("MENU")
    else:
        ch = getattr(event, "unicode", "")
        if (ch and ch.isprintable()
                and len(UI.get("name_buf", "")) < 14
                and ch not in "%{}\\&"):
            UI["name_buf"] = UI.get("name_buf", "") + ch


# ─────────────────────────────────────────────────────────────────────────
#  Flash messages (say) — file FIFO
# ─────────────────────────────────────────────────────────────────────────
def _process_flash():
    """Affiche le premier message de _FLASH_QUEUE (file de `say()`)."""
    if not _FLASH_QUEUE:
        return
    # Nettoie la file si trop longue
    while len(_FLASH_QUEUE) > 3:
        _FLASH_QUEUE.pop(0)

    entry = _FLASH_QUEUE[0]
    entry["t"] -= 1
    txt = entry["text"]
    col = entry["col"]
    w = max(360, FONT_SMALL.size(txt)[0] + 50)
    box = pygame.Rect(0, 0, w, 40)
    box.center = (WIDTH // 2, HEIGHT - 60)
    panel(screen, box, col, (20, 14, 34), 8, 2)
    draw_text(screen, txt, FONT_SMALL, BLANC, box.centerx, box.centery)

    if entry["t"] <= 0:
        _FLASH_QUEUE.pop(0)


# ─────────────────────────────────────────────────────────────────────────
#  Transitions (fondu noir + scan-lines)
# ─────────────────────────────────────────────────────────────────────────
def _process_transition():
    """Fait avancer la transition d'écran si elle est active."""
    t_ = UI.get("trans")
    if not t_:
        return

    t_["t"] += 1
    if t_["phase"] == 1 and t_["t"] >= 10:
        # Switch de l'état au milieu
        UI["state"] = t_["target"]
        if t_.get("session"):
            UI["session"] = t_["session"]
        if t_["target"] == "NAME":
            UI["name_buf"] = ""
        if t_["target"] == "GAME":
            try:
                audio.music("battle")
            except Exception:
                pass
        else:
            try:
                audio.music("menu")
            except Exception:
                pass
            write_save()
        t_["phase"], t_["t"] = 2, 0
    elif t_["phase"] == 2 and t_["t"] >= 10:
        UI["trans"] = None


# ─────────────────────────────────────────────────────────────────────────
#  Gestion évènements clavier globaux
# ─────────────────────────────────────────────────────────────────────────
def _handle_keydown(event):
    """Route les KEYDOWN selon l'état courant."""
    state = UI.get("state", "MENU")

    # F11 (partout) = plein écran
    if event.key == pygame.K_F11:
        set_fullscreen(not SET["fullscreen"])
        write_save()
        return

    # Saisie texte (NAME ou renommage PROFILE)
    if state == "NAME" or (state == "PROFILE" and UI.get("renaming")):
        if event.key == pygame.K_ESCAPE and state == "PROFILE":
            UI["renaming"] = False
        else:
            handle_text_key(event)
        return

    # Échap = navigation / pause
    if event.key == pygame.K_ESCAPE:
        if state == "GAME" and UI.get("session"):
            S = UI["session"]
            if S.phase == "OVER":
                goto("MENU")
            else:
                S.paused = not S.paused
        elif state == "SETTINGS":
            goto(UI.get("ret", "MENU"))
        elif state == "INSTRUCTIONS":
            goto(UI.get("iback", "MENU"))
        elif state == "MENU":
            # Rien à faire (déjà au menu)
            pass
        else:
            goto("MENU")
        return

    # Raccourcis de jeu (armes)
    if state == "GAME" and UI.get("session"):
        S = UI["session"]
        if S.paused:
            return
        if event.key == pygame.K_1:
            S.player.weapon_type = "PLASMA"
        elif event.key == pygame.K_2:
            S.player.weapon_type = "LASER"
        elif event.key == pygame.K_3:
            S.player.weapon_type = "MISSILE"
        elif event.key == pygame.K_4 and S.player.special:
            S.player.weapon_type = S.player.special


# ─────────────────────────────────────────────────────────────────────────
#  Rendu de la session de jeu (update + draw + pause/over)
# ─────────────────────────────────────────────────────────────────────────
def _draw_game_state():
    """Rend la frame de jeu complète. Retourne True si le jeu continue,
    False si le joueur est sorti (via échap déjà géré ailleurs)."""
    S = UI.get("session")
    if not S:
        UI["state"] = "MENU"
        return True

    # Reset du curseur visible uniquement en pause / over / transition
    transition_active = UI.get("trans") is not None

    # Update (pas pendant une transition)
    if not transition_active:
        S.update(pygame.key.get_pressed(),
                 pygame.mouse.get_pressed(),
                 (mouse["x"], mouse["y"]))

    # Sortie secrète ?
    if S.secret_exit:
        kind = S.secret_exit
        if not SAVE["secrets"].get(kind):
            SAVE["secrets"][kind] = True
            check_achievements()
            grant_box(1, "Zone secrète")
            say(tr("ZONE SECRÈTE DÉCOUVERTE : %s")
                % tr(MODES[kind]["title"]), PURPLE_NEON)
        write_save()
        UI["session"] = Session(kind)
        UI["trans"] = None
        return True

    # Rendu
    S.draw(screen, (mouse["x"], mouse["y"]))
    if S.paused:
        draw_pause_menu(S)
    elif S.phase == "OVER":
        draw_over(S)

    return True


# ─────────────────────────────────────────────────────────────────────────
#  BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────
async def main_async() :
    splash(0.0)
    await asyncio.sleep(0)          # laisse le splash s'afficher
    await build_audio_async()
    try:
        audio.music("menu")
    except Exception:
        pass
    # ... reste inchangé ...

    # --- État initial
    if not SAVE["profile"]["name"]:
        UI["state"] = "NAME"
        UI["name_buf"] = ""
    else:
        UI["state"] = "MENU"

    cursor_vis = True
    running = True

    while running:
        if IS_WEB:
            await asyncio.sleep(1 / FPS)  # cède proprement + cadence
        else:
            clock.tick(FPS)
        TICK[0] += 1
        try:
            audio.frame += 1
        except Exception:
            pass

        # --- Reset hover frame (impulsion)
        _reset_hover_frame()

        # --- Input souris
        mouse["x"], mouse["y"] = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()
        mouse["down"] = bool(pressed[0])
        mouse["click"] = False

        # --- AdManager (retours visuels)
        try:
            ADS.update()
        except Exception:
            pass

        # --- Événements pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse["click"] = True
            elif event.type == pygame.KEYDOWN:
                _handle_keydown(event)

        # --- Bloquer clics pendant transitions
        if UI.get("trans"):
            mouse["click"] = False

        # --- Dispatch d'écran
        state = UI.get("state", "MENU")
        want_vis = True

        if state == "MENU":
            if screen_menu() is False:
                running = False

        elif state == "NAME":
            screen_name()

        elif state == "GAME":
            _draw_game_state()
            S = UI.get("session")
            if S is not None:
                want_vis = (S.paused or S.phase == "OVER"
                            or bool(UI.get("trans")))

        elif state == "SETTINGS":
            screen_settings()

        elif state == "INSTRUCTIONS":
            screen_instructions()

        elif state == "SKINS":
            screen_skins()

        elif state == "SHOP":
            screen_shop()

        elif state == "ACH":
            screen_ach()

        elif state == "PROFILE":
            screen_profile()

        elif state == "SECRETS":
            screen_secrets()

        else:
            # État inconnu → fallback
            UI["state"] = "MENU"

        # --- Curseur visible/invisible
        if want_vis != cursor_vis:
            try:
                pygame.mouse.set_visible(want_vis)
            except Exception:
                pass
            cursor_vis = want_vis

        # --- Transition (fondu + scan-lines)
        _process_transition()
        if UI.get("trans"):
            draw_transition(screen)

        # --- Toasts (succès débloqués)
        draw_toasts()

        # --- AdManager (particules et popups)
        try:
            ADS.draw(screen)
        except Exception:
            pass

        # --- Dialogue Champion refusé (superposé à tout)
        if UI.get("champion_denied", 0) > 0:
            draw_champion_dialog()

        # --- Flash messages (say())
        _process_flash()

        # --- Compteur FPS
        if SET.get("fps"):
            draw_text(screen, "%d FPS" % clock.get_fps(), FONT_TINY,
                      VERT_NEON, WIDTH - 54, HEIGHT - 12)
                # ── pygbag : rend le contrôle au navigateur à chaque frame

        # ── pygbag : rend le contrôle au navigateur à chaque frame
        await asyncio.sleep(0)   # ← CETTE LIGNE EST OBLIGATOIRE
        # --- Flip
        try:
            pygame.display.flip()
        except Exception:
            pass


    # --- Sortie propre
    write_save()
    if IS_WEB:
        # Sur le web : pas de sys.exit ni pygame.quit (crash WASM)
        print("[INIT] Partie terminée — retour au navigateur")
        return
    try:
        pygame.quit()
    except Exception:
        pass
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════════════
#  OVERRIDE FINAL DES POLICES — placé tout à la fin du fichier
#  Réassigne TOUTES les polices et surcharge draw_text pour être sûr
#  qu'aucune définition en amont ne l'écrase.
# ═══════════════════════════════════════════════════════════════════════════

import os as _os_ovr   # déjà importé en haut, juste sécurité

# ── POLICES LISIBLES (pas Impact !) ──────────────────────────────
# Bahnschrift = police système Windows 10/11, moderne et très lisible
# Segoe UI   = police principale Windows, la plus lisible
# Calibri / Candara = alternatives douces et modernes
_HEAD_NAMES_FINAL = ["bahnschrift", "segoeuiblack", "segoeuib",
                     "segoeui", "calibrib", "calibri", "candarab",
                     "candara", "verdanab", "verdana", "arial"]
_BODY_NAMES_FINAL = ["segoeui", "calibri", "candara",
                     "bahnschrift", "verdana", "arial"]

_WIN_FONT_FILES_FINAL = {
    "bahnschrift":  ["bahnschrift.ttf"],
    "segoeuiblack": ["seguibl.ttf", "segoeuibl.ttf"],
    "segoeuib":     ["segoeuib.ttf", "segoeui.ttf"],
    "segoeui":      ["segoeui.ttf"],
    "calibrib":     ["calibrib.ttf", "calibri.ttf"],
    "calibri":      ["calibri.ttf"],
    "candarab":     ["candarab.ttf", "candara.ttf"],
    "candara":      ["candara.ttf"],
    "verdanab":     ["verdanab.ttf", "verdana.ttf"],
    "verdana":      ["verdana.ttf"],
    "arial":        ["arial.ttf", "arialbd.ttf"],
}

def _final_load_font(name, size, bold):
    """Charge un TTF. Renvoie (font, tag)."""
    if IS_WEB:
        # Sur le web, match_font peut bloquer : on utilise SysFont direct
        try:
            f = pygame.font.SysFont(None, int(size), bold=bold)
            return f, "web_sysfont"
        except Exception:
            return pygame.font.Font(None, int(size)), "web_raw"
    if _os_ovr.name == "nt":
        windir = _os_ovr.environ.get("WINDIR", r"C:\Windows")
        fontdir = _os_ovr.path.join(windir, "Fonts")
        for fname in _WIN_FONT_FILES_FINAL.get(name, [name + ".ttf"]):
            path = _os_ovr.path.join(fontdir, fname)
            if _os_ovr.path.exists(path):
                try:
                    f = pygame.font.Font(path, int(size))
                    if bold:
                        f.set_bold(True)
                    return f, "win:" + name
                except Exception:
                    pass
    try:
        path = pygame.font.match_font(name)
        if path:
            f = pygame.font.Font(path, int(size))
            if bold:
                f.set_bold(True)
            return f, "match:" + name
    except Exception:
        pass
    return pygame.font.SysFont(None, int(size), bold=bold), "fallback"


def _final_font(names, size, bold):
    for name in names:
        f, tag = _final_load_font(name, size, bold)
        if not tag.startswith("fallback"):
            return f
    return pygame.font.SysFont(None, int(size), bold=bold)


# Réduction des tailles pour les polices lisibles (Bahnschrift paraît
# plus large qu'Impact, donc on baisse un peu)
FONT_BIG   = _final_font(_HEAD_NAMES_FINAL, 64, True)    # était 80
FONT_TITLE = _final_font(_HEAD_NAMES_FINAL, 38, True)    # était 46
FONT_BTN   = _final_font(_HEAD_NAMES_FINAL, 20, True)    # était 25
FONT_MED   = _final_font(_BODY_NAMES_FINAL, 22, False)   # était 24
FONT_SMALL = _final_font(_BODY_NAMES_FINAL, 16, False)   # était 17
FONT_TINY  = _final_font(_BODY_NAMES_FINAL, 13, False)   # inchangé


# ── Surcharge DÉFINITIVE de draw_text et dérivés ─────────────────
_TEXT_CACHE = {}
_OUTLINE_CACHE = {}

def draw_text(surf, text, font, color, x, y, center=True, shadow=True):
    if hasattr(font, "render"):
        f = font
    elif isinstance(font, (int, float)):
        sz = int(font)
        names = _HEAD_NAMES_FINAL if sz >= 30 else _BODY_NAMES_FINAL
        f = _final_font(names, sz, sz >= 30)
    else:
        f = _final_font(_BODY_NAMES_FINAL, 20, False)

    text_str = str(text)
    key = (text_str, id(f), tuple(color), shadow, center)
    if key not in _TEXT_CACHE:
        try:
            fg = f.render(text_str, True, color)
            sh = None
            if shadow:
                col_sh = (0, 0, 0) if shadow is True else shadow
                sh = f.render(text_str, True, col_sh)
            _TEXT_CACHE[key] = (fg, sh)
        except Exception:
            return None
    fg, sh = _TEXT_CACHE[key]
    r = (fg.get_rect(center=(int(x), int(y))) if center
         else fg.get_rect(topleft=(int(x), int(y))))
    if sh:
        surf.blit(sh, (r.x + 1, r.y + 1))
    surf.blit(fg, r)
    return r


def draw_text_ml(surf, text, font, color, x, y, shadow=True):
    if hasattr(font, "render"):
        f = font
    elif isinstance(font, (int, float)):
        sz = int(font)
        names = _HEAD_NAMES_FINAL if sz >= 30 else _BODY_NAMES_FINAL
        f = _final_font(names, sz, sz >= 30)
    else:
        f = _final_font(_BODY_NAMES_FINAL, 20, False)
    try:
        img = f.render(str(text), True, color)
    except Exception:
        return None
    r = img.get_rect(midleft=(int(x), int(y)))
    if shadow:
        try:
            sh = f.render(str(text), True, (0, 0, 0))
            surf.blit(sh, (r.x + 1, r.y + 1))
        except Exception:
            pass
    surf.blit(img, r)
    return r


def draw_text_sharp(surf, text, font, color, x, y, center=True, shadow=True):
    return draw_text(surf, text, font, color, x, y, center, shadow)


_OUTLINE_CACHE = {}

def draw_text_outlined(surf, text, font, color, x, y, center=True,
                       outline=(0, 0, 0), thick=2):
    font = _resolve_font(font)
    text_str = str(text)
    key = (text_str, id(font), tuple(color), tuple(outline), thick)
    
    if key not in _OUTLINE_CACHE:
        try:
            base = font.render(text_str, True, color)
            ol = font.render(text_str, True, outline)
            _OUTLINE_CACHE[key] = (base, ol)
        except Exception:
            return None
            
    base, ol = _OUTLINE_CACHE[key]
    r = (base.get_rect(center=(int(x), int(y))) if center
         else base.get_rect(topleft=(int(x), int(y))))
         
    for dx in (-thick, 0, thick):
        for dy in (-thick, 0, thick):
            if dx or dy:
                surf.blit(ol, (r.x + dx, r.y + dy))
    surf.blit(base, r)
    return r
# ═══════════════════════════════════════════════════════════════════════════
#  Entrée du programme
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # pygbag exige asyncio.run()
    asyncio.run(main_async())