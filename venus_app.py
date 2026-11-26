import sys

from venus_backend import VenusTitaniumAPI, run_overlay_hud

MAIN_WINDOW = None


def get_window():
    return MAIN_WINDOW


HTML_UI = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>venUs SILVER</title>
<style>
  :root {
    --font: 'Segoe UI Variable Display', 'Segoe UI Variable', 'SF Pro Display', 'Inter', system-ui, sans-serif;
    --mono: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
    --card: linear-gradient(155deg, rgba(215, 220, 230, 0.08) 0%, rgba(16, 17, 20, 0.72) 100%);
    --card-hover: linear-gradient(155deg, rgba(235, 240, 248, 0.13) 0%, rgba(22, 24, 28, 0.82) 100%);
    --border: rgba(255, 255, 255, 0.09);
    --border-top: rgba(255, 255, 255, 0.26);
    --border-hover: rgba(255, 255, 255, 0.40);
    --text: #ffffff;
    --text-2: rgba(228, 231, 238, 0.62);
    --text-3: rgba(228, 231, 238, 0.36);
    --silver: linear-gradient(135deg, #ffffff 0%, #c8cdd6 100%);
    --ink: #040405;
    --ok: #34d399;
    --danger: #f87171;
    --radius: 20px;
    --shadow: 0 24px 56px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.18);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; -webkit-font-smoothing: antialiased; }

  /* FOND NOIR BRUT DÉGRADÉ SILVER */
  body {
    font-family: var(--font);
    color: var(--text);
    height: 100vh;
    overflow: hidden;
    background:
      radial-gradient(ellipse 75% 55% at 12% -5%, rgba(215, 220, 230, 0.24) 0%, rgba(120, 126, 138, 0.08) 38%, transparent 72%),
      radial-gradient(ellipse 65% 55% at 92% 108%, rgba(180, 186, 198, 0.16) 0%, transparent 64%),
      linear-gradient(150deg, #121316 0%, #050507 42%, #000000 100%);
  }

  #silver-sheen {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background: radial-gradient(560px circle at var(--gx, 50%) var(--gy, 20%), rgba(235, 240, 248, 0.065), transparent 62%);
  }

  .splash {
    position: fixed; inset: 0; z-index: 400;
    background: radial-gradient(circle at 50% 35%, #1d1f24 0%, #000000 72%);
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px;
    transition: opacity .5s cubic-bezier(.16,1,.3,1), transform .5s cubic-bezier(.16,1,.3,1); cursor: pointer;
  }
  .splash.hide { opacity: 0; transform: scale(1.03); pointer-events: none; }
  .splash-crest {
    width: 68px; height: 68px; border-radius: 20px; border: 1px solid rgba(255,255,255,.32);
    background: linear-gradient(155deg, rgba(255,255,255,.2), rgba(255,255,255,.03));
    box-shadow: 0 24px 60px rgba(0,0,0,.85), inset 0 1px 0 rgba(255,255,255,.45);
    display: grid; place-items: center;
  }
  .splash-word { font-size: 36px; font-weight: 600; letter-spacing: -.03em; }
  .splash-word span { font-weight: 300; color: #a1a1aa; margin-left: 8px; font-size: 14px; letter-spacing: .3em; text-transform: uppercase; }
  .splash-line { width: 170px; height: 1px; background: rgba(255,255,255,.14); position: relative; overflow: hidden; }
  .splash-line::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, #fff, transparent); animation: sweep 1.05s ease forwards; }
  @keyframes sweep { from { transform: translateX(-100%); } to { transform: translateX(100%); } }

  .app { position: relative; z-index: 2; height: 100vh; display: flex; flex-direction: column; border: 1px solid rgba(255,255,255,.1); }

  /* TITLEBAR */
  .titlebar {
    height: 54px; display: flex; align-items: center; justify-content: space-between;
    padding: 0 14px 0 20px; border-bottom: 1px solid var(--border);
    background: rgba(4, 4, 6, 0.72); backdrop-filter: blur(22px); flex-shrink: 0;
  }
  .tb-left { display: flex; align-items: center; gap: 12px; }
  .brand-trigger { display: flex; align-items: center; gap: 11px; cursor: pointer; }
  .brand-mark {
    width: 30px; height: 30px; border-radius: 9px; border: 1px solid var(--border-top);
    background: linear-gradient(155deg, rgba(255,255,255,.22), rgba(255,255,255,.04)); display: grid; place-items: center;
  }
  .brand-title { font-size: 15px; font-weight: 600; letter-spacing: -.02em; }
  .brand-title span { font-family: var(--mono); font-size: 10px; letter-spacing: .22em; color: var(--text-3); text-transform: uppercase; margin-left: 7px; }

  .search-pill {
    height: 32px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--border);
    background: rgba(255,255,255,.04); color: var(--text-2); font-size: 12px;
    display: inline-flex; align-items: center; gap: 10px; cursor: pointer; margin-left: 10px; transition: all .18s;
  }
  .search-pill:hover { background: rgba(255,255,255,.1); border-color: var(--border-hover); color: #fff; }
  .kbd { font-family: var(--mono); font-size: 10px; padding: 1px 6px; border-radius: 5px; background: rgba(255,255,255,.1); color: #fff; }

  .tb-drag { flex: 1; height: 100%; }
  .tb-right { display: flex; align-items: center; gap: 8px; }
  .pill-btn {
    height: 32px; padding: 0 13px; border-radius: 10px; border: 1px solid var(--border);
    background: rgba(255,255,255,.05); color: var(--text-2); font-family: var(--font); font-size: 12px; font-weight: 500;
    cursor: pointer; display: inline-flex; align-items: center; gap: 7px; transition: all .18s;
  }
  .pill-btn:hover { border-color: var(--border-hover); color: #fff; background: rgba(255,255,255,.1); }
  .pill-btn.on { border-color: rgba(52,211,153,.6); color: #6ee7b7; background: rgba(52,211,153,.14); }

  .icon-btn {
    width: 32px; height: 32px; border-radius: 9px; border: 1px solid transparent; background: transparent;
    color: var(--text-2); display: grid; place-items: center; cursor: pointer; transition: all .16s;
  }
  .icon-btn:hover { background: rgba(255,255,255,.1); border-color: var(--border); color: #fff; }
  .icon-btn.close:hover { background: rgba(239,68,68,.24); border-color: rgba(239,68,68,.5); color: #fecaca; }

  /* DOCK GAUCHE : LOGOS BLANCS */
  .workspace { flex: 1; display: grid; grid-template-columns: 88px 1fr; overflow: hidden; }
  .dock {
    border-right: 1px solid var(--border); background: rgba(3, 3, 5, 0.56); backdrop-filter: blur(22px);
    padding: 20px 12px; display: flex; flex-direction: column; align-items: center; gap: 10px;
  }
  .dock-btn {
    width: 62px; height: 58px; border-radius: 16px; border: 1px solid transparent; background: transparent;
    color: rgba(255,255,255,.52); cursor: pointer; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 5px; transition: all .2s cubic-bezier(.16,1,.3,1);
  }
  .dock-btn svg { width: 22px; height: 22px; stroke: currentColor; transition: transform .2s; }
  .dock-btn span { font-size: 9.5px; font-weight: 500; }
  .dock-btn:hover { background: rgba(255,255,255,.07); color: #fff; }
  .dock-btn:hover svg { transform: scale(1.08); }
  .dock-btn.active {
    background: linear-gradient(155deg, rgba(255,255,255,.20), rgba(255,255,255,.06));
    border-color: var(--border-top); color: #fff;
    box-shadow: 0 12px 26px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.35);
  }
  .dock-spacer { flex: 1; }
  .dock-clock { font-family: var(--mono); font-size: 11px; color: var(--text-3); }

  /* STAGE */
  .stage { position: relative; overflow: hidden; }
  .tab-view {
    position: absolute; inset: 0; padding: 34px 42px 38px; overflow-y: auto;
    display: flex; flex-direction: column; gap: 30px;
    transition: opacity .26s cubic-bezier(.16,1,.3,1), transform .26s cubic-bezier(.16,1,.3,1);
  }
  .tab-view.hidden { opacity: 0; transform: translateY(12px); pointer-events: none; }
  .tab-view::-webkit-scrollbar { width: 6px; }
  .tab-view::-webkit-scrollbar-thumb { background: rgba(255,255,255,.16); border-radius: 99px; }

  .head-row { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; flex-wrap: wrap; }
  .head-row h2 { font-size: 30px; font-weight: 600; letter-spacing: -.035em; line-height: 1.1; }
  .head-row p { font-size: 13.5px; color: var(--text-2); margin-top: 5px; }
  .sec-title { font-size: 12.5px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-2); display: flex; align-items: center; gap: 9px; margin-bottom: 14px; }
  .btn-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

  .btn-ghost {
    height: 38px; padding: 0 16px; border-radius: 12px; border: 1px solid var(--border); border-top-color: var(--border-top);
    background: rgba(255,255,255,.06); backdrop-filter: blur(14px); color: #fff; font-family: var(--font); font-size: 13px; font-weight: 500;
    display: inline-flex; align-items: center; gap: 8px; cursor: pointer; transition: all .18s;
  }
  .btn-ghost:hover { background: rgba(255,255,255,.14); border-color: var(--border-hover); transform: translateY(-1px); }

  .btn-primary {
    height: 38px; padding: 0 18px; border-radius: 12px; border: none; background: var(--silver); color: var(--ink);
    font-family: var(--font); font-size: 13px; font-weight: 700; display: inline-flex; align-items: center; gap: 8px;
    cursor: pointer; transition: all .18s; box-shadow: 0 10px 28px rgba(0,0,0,.55);
  }
  .btn-primary:hover { filter: brightness(1.06); transform: translateY(-1px); }
  .btn-primary:active { transform: scale(.97); }

  .btn-boost-max {
    height: 44px; padding: 0 24px; border-radius: 13px; border: 1px solid rgba(255,255,255,.6);
    background: linear-gradient(135deg, #ffffff 0%, #c6ccd6 100%); color: #050506;
    font-family: var(--font); font-size: 14px; font-weight: 700; letter-spacing: .02em;
    display: inline-flex; align-items: center; gap: 9px; cursor: pointer;
    box-shadow: 0 0 32px rgba(255,255,255,.22), 0 14px 32px rgba(0,0,0,.6); transition: all .2s;
  }
  .btn-boost-max:hover { transform: translateY(-2px) scale(1.02); box-shadow: 0 0 42px rgba(255,255,255,.35); }

  .card {
    position: relative; background: var(--card); backdrop-filter: blur(22px);
    border: 1px solid var(--border); border-top-color: var(--border-top); border-radius: var(--radius);
    padding: 24px; box-shadow: var(--shadow); overflow: hidden;
    transition: transform .22s cubic-bezier(.16,1,.3,1), border-color .2s, background .2s;
  }
  .card.clickable { cursor: pointer; }
  .card.clickable:hover { border-color: var(--border-hover); background: var(--card-hover); transform: translateY(-4px); }

  .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(265px, 1fr)); gap: 20px; }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 20px; }

  .status-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
  .stat-tile { padding: 18px 20px; display: flex; align-items: center; gap: 15px; }
  .stat-icon {
    width: 44px; height: 44px; border-radius: 13px; background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.18); display: grid; place-items: center; flex-shrink: 0; color: #fff;
  }
  .stat-num { font-size: 22px; font-weight: 600; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
  .stat-lbl { font-size: 12px; color: var(--text-2); margin-top: 2px; }

  .plat-card { height: 176px; display: flex; flex-direction: column; justify-content: space-between; }
  .plat-top { display: flex; justify-content: space-between; align-items: flex-start; }
  .plat-logo-box {
    width: 58px; height: 58px; border-radius: 16px;
    background: linear-gradient(155deg, rgba(255,255,255,.16), rgba(255,255,255,.04));
    border: 1px solid rgba(255,255,255,.24); display: grid; place-items: center; color: #fff;
    box-shadow: 0 10px 24px rgba(0,0,0,.45); transition: transform .24s;
  }
  .plat-card:hover .plat-logo-box { transform: scale(1.08); }
  .pill-mono { font-family: var(--mono); font-size: 11px; padding: 4px 10px; border-radius: 99px; background: rgba(255,255,255,.08); border: 1px solid var(--border); color: #fff; }
  .plat-card h3 { font-size: 20px; font-weight: 600; }
  .plat-card p { font-size: 12.5px; color: var(--text-2); margin-top: 3px; }

  /* ACCOUNT BANNER CARDS (BALISE <img> RÉELLE) */
  .acc-card { padding: 0; display: flex; flex-direction: column; }
  .banner-stage { height: 176px; position: relative; overflow: hidden; background: #0e1015; }
  .banner-img {
    position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block;
    transition: transform .55s cubic-bezier(.16,1,.3,1);
  }
  .banner-fallback {
    position: absolute; inset: 0;
    background: linear-gradient(145deg, #252830 0%, #111216 55%, #050507 100%);
  }
  .acc-card:hover .banner-img { transform: scale(1.06); }
  .banner-vignette { position: absolute; inset: 0; z-index: 1; background: linear-gradient(180deg, rgba(0,0,0,.15) 0%, rgba(0,0,0,.22) 45%, rgba(6,7,9,.96) 100%); }
  .banner-plat-badge {
    position: absolute; top: 14px; left: 14px; z-index: 3; width: 34px; height: 34px; border-radius: 10px;
    background: rgba(5,5,7,.72); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,.22);
    display: grid; place-items: center; color: #fff;
  }
  .banner-tools { position: absolute; top: 14px; right: 14px; z-index: 3; display: flex; gap: 6px; }
  .chip-tool {
    height: 30px; padding: 0 11px; border-radius: 9px; border: 1px solid rgba(255,255,255,.22);
    background: rgba(5,5,7,.72); backdrop-filter: blur(10px); color: #fff; font-size: 11.5px; font-weight: 500;
    cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: background .16s;
  }
  .chip-tool:hover { background: rgba(255,255,255,.24); }
  .chip-tool.fav { border-color: #fde047; color: #fde047; }
  .banner-footer { position: absolute; left: 18px; right: 18px; bottom: 14px; z-index: 2; display: flex; justify-content: space-between; align-items: flex-end; gap: 10px; }
  .banner-footer h3 { font-size: 21px; font-weight: 600; text-shadow: 0 2px 12px rgba(0,0,0,.9); }
  .acc-bar { padding: 14px 18px; display: flex; align-items: center; gap: 10px; }
  .btn-del {
    width: 38px; height: 38px; border-radius: 11px; border: 1px solid var(--border); background: rgba(255,255,255,.04);
    color: var(--text-2); display: grid; place-items: center; cursor: pointer;
  }
  .btn-del:hover { background: rgba(239,68,68,.2); border-color: rgba(239,68,68,.5); color: #fecaca; }

  /* BANNER PREVIEW IN EDIT MODAL */
  .modal-banner-preview {
    width: 100%; height: 112px; border-radius: 12px; border: 1px solid var(--border);
    background: linear-gradient(145deg, #20232a, #0a0b0e); overflow: hidden; margin-bottom: 12px;
    display: grid; place-items: center; position: relative;
  }
  .modal-banner-preview img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .modal-banner-preview span { font-size: 12px; color: var(--text-3); }

  /* STUDIO HUD */
  .hud-studio-grid { display: grid; grid-template-columns: 1.15fr 1fr; gap: 22px; }
  .hud-preview-stage {
    min-height: 330px; border-radius: var(--radius); border: 1px solid var(--border);
    background: radial-gradient(circle at 25% 25%, rgba(210,215,225,.14), transparent 60%), linear-gradient(155deg, #16181d, #030304);
    position: relative; padding: 22px; display: flex; overflow: hidden;
  }
  .hud-preview-stage.pos-top-left { align-items: flex-start; justify-content: flex-start; }
  .hud-preview-stage.pos-top-right { align-items: flex-start; justify-content: flex-end; }
  .hud-preview-stage.pos-bottom-left { align-items: flex-end; justify-content: flex-start; }
  .hud-preview-stage.pos-bottom-right { align-items: flex-end; justify-content: flex-end; }

  .hud-mock {
    background: #0a0b0e; border: 1px solid #424752; border-radius: 12px; padding: 10px 16px;
    display: flex; align-items: center; gap: 13px; font-family: var(--mono); font-size: 12px;
    color: #e5e7eb; box-shadow: 0 18px 42px rgba(0,0,0,.75); position: relative; z-index: 2;
  }
  .hud-mock.vertical { flex-direction: column; align-items: flex-start; gap: 8px; padding: 14px 16px; min-width: 165px; }
  .hud-free-preview {
    position: absolute; z-index: 3; border-radius: 10px; object-fit: contain;
    box-shadow: 0 12px 30px rgba(0,0,0,.6); border: 1px dashed rgba(255,255,255,.35);
  }

  .toggle-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 10px; }
  .toggle-card {
    padding: 10px 13px; border-radius: 11px; border: 1px solid var(--border); background: rgba(255,255,255,.04);
    color: var(--text-2); font-size: 12.2px; font-weight: 500; cursor: pointer;
    display: flex; justify-content: space-between; align-items: center; transition: all .16s;
  }
  .toggle-card.on { border-color: rgba(255,255,255,.38); background: rgba(255,255,255,.12); color: #fff; }
  .switch-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,.2); }
  .toggle-card.on .switch-dot { background: var(--ok); box-shadow: 0 0 8px var(--ok); }

  /* RAM */
  .ram-hero { display: flex; align-items: center; gap: 28px; }
  .gauge-wrap { position: relative; width: 120px; height: 120px; flex-shrink: 0; }
  .gauge-wrap svg { transform: rotate(-90deg); width: 120px; height: 120px; }
  .gauge-bg { fill: none; stroke: rgba(255,255,255,.09); stroke-width: 8; }
  .gauge-fg { fill: none; stroke: #ffffff; stroke-width: 8; stroke-linecap: round; transition: stroke-dashoffset .6s ease; }
  .gauge-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .proc-row { display: grid; grid-template-columns: 1fr 90px 160px; align-items: center; gap: 12px; padding: 11px 14px; border-radius: 12px; background: rgba(255,255,255,.04); border: 1px solid var(--border); font-size: 13px; }
  .proc-bar { height: 4px; background: rgba(255,255,255,.09); border-radius: 99px; margin-top: 6px; overflow: hidden; }
  .proc-fill { height: 100%; background: #ffffff; border-radius: 99px; }

  .sub-tabs { display: inline-flex; gap: 6px; padding: 4px; border-radius: 13px; background: rgba(255,255,255,.05); border: 1px solid var(--border); align-self: flex-start; }
  .sub-tab { height: 34px; padding: 0 16px; border-radius: 10px; border: none; background: transparent; color: var(--text-2); font-family: var(--font); font-size: 13px; font-weight: 500; cursor: pointer; }
  .sub-tab.active { background: #fff; color: var(--ink); font-weight: 600; }

  /* MODALS & PALETTE */
  .cmd-backdrop, .modal-backdrop { position: fixed; inset: 0; z-index: 220; background: rgba(0,0,0,.76); backdrop-filter: blur(14px); display: none; place-items: center; }
  .cmd-backdrop.open, .modal-backdrop.open { display: grid; }
  .cmd-box { width: 560px; max-width: 92vw; border-radius: 18px; background: #101114; border: 1px solid var(--border-hover); box-shadow: 0 36px 90px rgba(0,0,0,.85); overflow: hidden; }
  .cmd-in { display: flex; align-items: center; gap: 12px; padding: 16px 18px; border-bottom: 1px solid var(--border); }
  .cmd-in input { flex: 1; background: transparent; border: none; color: #fff; font-size: 15px; outline: none; }
  .cmd-list { max-height: 340px; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 3px; }
  .cmd-item { padding: 11px 14px; border-radius: 11px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; font-size: 13.5px; color: var(--text-2); }
  .cmd-item.selected, .cmd-item:hover { background: rgba(255,255,255,.1); color: #fff; }

  .modal { width: 490px; max-height: 86vh; overflow-y: auto; border-radius: 20px; background: #101114; border: 1px solid var(--border-hover); padding: 26px; box-shadow: 0 36px 90px rgba(0,0,0,.85); }
  .modal h3 { font-size: 19px; font-weight: 600; margin-bottom: 6px; }
  .modal p { font-size: 13px; color: var(--text-2); margin-bottom: 16px; line-height: 1.5; }
  .field { margin-bottom: 13px; }
  .field label { display: block; font-size: 12px; color: var(--text-2); margin-bottom: 6px; }
  .field input, .field select, .field textarea { width: 100%; padding: 10px 13px; border-radius: 10px; border: 1px solid var(--border); background: #060709; color: #fff; font-family: var(--font); font-size: 13px; outline: none; }
  .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .mono-box { font-family: var(--mono); font-size: 12px; padding: 11px 13px; border-radius: 10px; background: #060709; border: 1px solid var(--border); color: #e2e8f0; word-break: break-all; }
  .list-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 16px; border-radius: 13px; background: rgba(255,255,255,.04); border: 1px solid var(--border); }
  .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }

  .busy-overlay { position: fixed; inset: 0; z-index: 260; background: rgba(0,0,0,.76); backdrop-filter: blur(14px); display: none; place-items: center; }
  .busy-overlay.open { display: grid; }
  .busy-card { padding: 22px 34px; border-radius: 16px; background: #101114; border: 1px solid var(--border-hover); display: flex; align-items: center; gap: 14px; }
  .spinner { width: 20px; height: 20px; border-radius: 50%; border: 2px solid rgba(255,255,255,.18); border-top-color: #fff; animation: spin .75s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .toast-wrap { position: fixed; right: 24px; bottom: 24px; z-index: 300; display: flex; flex-direction: column; gap: 8px; }
  .toast { padding: 12px 16px; border-radius: 12px; background: #121418; border: 1px solid var(--border-hover); font-size: 13px; display: flex; align-items: center; gap: 10px; box-shadow: 0 16px 38px rgba(0,0,0,.7); }
  .toast.error { border-color: rgba(248,113,113,.6); color: #fecaca; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }
  .toast.error .dot { background: var(--danger); }
</style>
</head>
<body>
<div id="silver-sheen"></div>

<div class="splash" id="splash" onclick="dismissSplash()">
  <div class="splash-crest">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5l8 14L20 5"/><path d="M9.5 5L12 9.5L14.5 5" opacity=".4"/></svg>
  </div>
  <div class="splash-word">venUs<span>silver</span></div>
  <div class="splash-line"></div>
</div>

<div class="app">
  <header class="titlebar">
    <div class="tb-left">
      <div class="brand-trigger" onclick="switchTab('hub')">
        <div class="brand-mark"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.4"><path d="M4 5l8 14L20 5"/></svg></div>
        <div class="brand-title">venUs<span>silver</span></div>
      </div>
      <button class="search-pill" onclick="openCmd()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        Rechercher
        <span class="kbd">Ctrl K</span>
      </button>
    </div>

    <div class="tb-drag pywebview-drag-region" ondblclick="window.pywebview.api.win_toggle_maximize()"></div>

    <div class="tb-right">
      <button class="pill-btn" id="btn-gamemode" onclick="toggleGameMode()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        Game Mode
      </button>
      <button class="pill-btn" id="btn-overlay" onclick="toggleOverlay()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        HUD
      </button>
      <button class="icon-btn" id="sound-btn" onclick="toggleSound()" title="Audio"></button>
      <button class="icon-btn" onclick="window.pywebview.api.win_minimize()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/></svg></button>
      <button class="icon-btn" onclick="window.pywebview.api.win_toggle_maximize()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/></svg></button>
      <button class="icon-btn close" onclick="window.pywebview.api.win_close()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
    </div>
  </header>

  <div class="workspace">
    <!-- DOCK LOGOS BLANCS (SANS ONGLET CLIPS) -->
    <nav class="dock">
      <button class="dock-btn active" data-tab="hub" onclick="switchTab('hub')">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/></svg>
        <span>Hub</span>
      </button>
      <button class="dock-btn" data-tab="launchers" onclick="switchTab('launchers')">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="12" x2="10" y2="12"/><line x1="8" y1="10" x2="8" y2="14"/><line x1="15" y1="13" x2="15.01" y2="13"/><line x1="18" y1="11" x2="18.01" y2="11"/><rect x="2" y="6" width="20" height="12" rx="5"/></svg>
        <span>Comptes</span>
      </button>
      <button class="dock-btn" data-tab="ram" onclick="switchTab('ram')">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>
        <span>Boost</span>
      </button>
      <button class="dock-btn" data-tab="hud" onclick="switchTab('hud')">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M7 20h10"/><path d="M9 16v4"/><path d="M15 16v4"/><circle cx="8" cy="10" r="1.5" fill="currentColor" stroke="none"/><line x1="12" y1="10" x2="17" y2="10"/></svg>
        <span>HUD</span>
      </button>
      <button class="dock-btn" data-tab="configs" onclick="switchTab('configs')">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/></svg>
        <span>Configs</span>
      </button>
      <button class="dock-btn" data-tab="tools" onclick="switchTab('tools')">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>
        <span>Outils</span>
      </button>
      <div class="dock-spacer"></div>
      <div class="dock-clock" id="dock-clock">--:--</div>
    </nav>

    <main class="stage">
      <!-- 1. HUB -->
      <section class="tab-view" id="tab-hub">
        <div class="head-row">
          <div>
            <h2>venUs Hub</h2>
            <p>Accès direct à tes comptes, performances temps réel et launchers.</p>
          </div>
          <div class="btn-row">
            <button class="btn-ghost" onclick="switchTab('hud')">Studio HUD</button>
            <button class="btn-boost-max" onclick="runBoostMax(false)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              BOOST MAX (Safe)
            </button>
          </div>
        </div>

        <div class="status-strip">
          <div class="card stat-tile clickable" onclick="switchTab('ram')">
            <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg></div>
            <div><div class="stat-num" id="st-cpu">--%</div><div class="stat-lbl">Processeur</div></div>
          </div>
          <div class="card stat-tile clickable" onclick="switchTab('ram')">
            <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 19v-3M10 19v-3M14 19v-3M18 19v-3"/><rect x="3" y="5" width="18" height="11" rx="2"/></svg></div>
            <div><div class="stat-num" id="st-ram">--%</div><div class="stat-lbl" id="st-ram-sub">Mémoire RAM</div></div>
          </div>
          <div class="card stat-tile clickable" onclick="switchTab('hud')">
            <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
            <div><div class="stat-num" id="st-fps">-- FPS</div><div class="stat-lbl" id="st-gpu-sub">Affichage DWM</div></div>
          </div>
          <div class="card stat-tile clickable" onclick="runMacro('media_play')">
            <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></div>
            <div style="overflow:hidden;"><div class="stat-num" style="font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" id="st-track">En pause</div><div class="stat-lbl">Cliquer : Play / Pause</div></div>
          </div>
        </div>

        <div>
          <div class="sec-title">Accès rapide</div>
          <div class="grid-3" id="hub-quick-accounts"></div>
        </div>

        <div>
          <div class="sec-title">Plateformes</div>
          <div class="grid-3" id="hub-plats"></div>
        </div>
      </section>

      <!-- 2. COMPTES -->
      <section class="tab-view hidden" id="tab-launchers">
        <div id="launchers-hub">
          <div class="head-row" style="margin-bottom:24px;">
            <div><h2>Launchers &amp; Comptes</h2><p>Gère tes sessions, bannières et jeux lancés en un clic.</p></div>
            <div class="btn-row">
              <button class="btn-ghost" onclick="recoverAccounts()" id="btn-recover">Récupérer / Corbeille</button>
              <button class="btn-ghost" onclick="openPluginModal()">+ Plugin</button>
            </div>
          </div>
          <div class="grid-3" id="platform-grid"></div>
        </div>

        <div id="accounts-section" style="display:none;">
          <div class="head-row" style="margin-bottom:24px;">
            <div>
              <button class="btn-ghost" onclick="backToLaunchers()" style="margin-bottom:12px;">← Plateformes</button>
              <div style="display:flex;align-items:center;gap:14px;">
                <div class="plat-logo-box" id="plat-head-logo" style="width:46px;height:46px;border-radius:13px;"></div>
                <div><h2 id="plat-title">Epic Games</h2><p id="plat-sub"></p></div>
              </div>
            </div>
            <div class="btn-row">
              <button class="btn-ghost" onclick="recoverAccounts()">Récupérer</button>
              <button class="btn-ghost" onclick="configureExe()">Exécutable</button>
              <button class="btn-ghost" id="btn-other-acc" onclick="prepareNewAccount()">Autre compte</button>
              <button class="btn-primary" id="btn-add-acc" onclick="openAddAccountModal()">+ Capturer</button>
            </div>
          </div>
          <div class="grid-2" id="accounts-grid"></div>
        </div>
      </section>

      <!-- 3. RAM BOOST MAX -->
      <section class="tab-view hidden" id="tab-ram">
        <div class="head-row">
          <div><h2>RAM Boost Max</h2><p>Libère le maximum de mémoire vive sans fermer tes jeux ni tes applis ouvertes.</p></div>
          <div class="btn-row">
            <button class="btn-ghost" onclick="runBoostMax(true)">Boost + Fermer cibles</button>
            <button class="btn-boost-max" onclick="runBoostMax(false)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              BOOST MAX (Safe)
            </button>
          </div>
        </div>

        <div class="card ram-hero">
          <div class="gauge-wrap">
            <svg viewBox="0 0 100 100"><circle class="gauge-bg" cx="50" cy="50" r="42"/><circle class="gauge-fg" id="ram-ring" cx="50" cy="50" r="42" stroke-dasharray="263.9" stroke-dashoffset="263.9"/></svg>
            <div class="gauge-center"><span style="font-size:24px;font-weight:700;" id="ram-big-pct">--%</span><span style="font-family:var(--mono);font-size:10px;color:var(--text-3);">RAM</span></div>
          </div>
          <div style="flex:1;display:flex;flex-direction:column;gap:10px;">
            <div style="font-size:20px;font-weight:600;" id="ram-big-detail">-- / -- Go</div>
            <div style="font-family:var(--mono);font-size:12px;color:var(--ok);" id="ram-big-last">Double-pass Win32 EmptyWorkingSet + nettoyage %TEMP% + Performances élevées</div>
            <div class="btn-row" style="margin-top:4px;">
              <button class="pill-btn" id="opt-ram-auto" onclick="toggleRamSetting('ram_boost_enabled')">Auto au lancement</button>
              <button class="pill-btn" id="opt-ram-power" onclick="toggleRamSetting('ram_high_power')">Perf. Élevées</button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="sec-title">Processus les plus gourmands</div>
          <div id="ram-proc-list" style="display:flex;flex-direction:column;gap:8px;"></div>
        </div>
      </section>

      <!-- 4. STUDIO HUD -->
      <section class="tab-view hidden" id="tab-hud">
        <div class="head-row">
          <div><h2>Studio HUD</h2><p>Active les FPS, choisis le sens, et place ton image n'importe où avec la taille exacte.</p></div>
          <button class="btn-primary" id="btn-hud-launch" onclick="toggleOverlay()">Activer le HUD</button>
        </div>

        <div class="hud-studio-grid">
          <div style="display:flex;flex-direction:column;gap:14px;">
            <div class="sec-title" style="margin:0;">Aperçu en direct</div>
            <div class="hud-preview-stage pos-top-left" id="hud-preview-stage">
              <div class="hud-mock" id="hud-mock"></div>
              <img class="hud-free-preview" id="hud-free-preview" style="display:none;" />
            </div>

            <div class="card" style="display:flex;flex-direction:column;gap:14px;">
              <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
                <div>
                  <div style="font-size:14.5px;font-weight:600;">Image personnalisée du HUD</div>
                  <div style="font-size:12px;color:var(--text-2);margin-top:2px;">En mode « Image libre », déplace-la où tu veux sur ton écran à la souris.</div>
                </div>
                <div class="btn-row">
                  <button class="btn-primary" onclick="pickHudImage()">Importer</button>
                  <button class="btn-ghost" onclick="clearHudImage()">Retirer</button>
                </div>
              </div>

              <div class="row-2">
                <button class="toggle-card" id="hud-img-docked" onclick="setHudProp('img_free', false)"><span>Collée dans la barre</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-img-free" onclick="setHudProp('img_free', true)"><span>Image libre (où je veux)</span><span class="switch-dot"></span></button>
              </div>

              <div class="row-2">
                <div>
                  <div class="sec-title" style="margin-bottom:5px;font-size:11px;">Taille image (<span id="hud-sz-lbl">42</span> px)</div>
                  <input type="range" id="hud-img-size" min="24" max="320" value="42" style="width:100%;" oninput="previewHudSize(this.value)" onchange="setHudProp('img_size', Number(this.value))" />
                </div>
                <div>
                  <div class="sec-title" style="margin-bottom:5px;font-size:11px;">Opacité image (<span id="hud-iop-lbl">95</span>%)</div>
                  <input type="range" id="hud-img-op" min="20" max="100" value="95" style="width:100%;" oninput="previewHudImgOp(this.value)" onchange="setHudProp('img_opacity', Number(this.value)/100)" />
                </div>
              </div>
            </div>
          </div>

          <div class="card" style="display:flex;flex-direction:column;gap:18px;">
            <div>
              <div class="sec-title" style="margin-bottom:9px;">Sens de la barre HUD</div>
              <div class="row-2">
                <button class="toggle-card" id="hud-ori-h" onclick="setHudProp('orientation','horizontal')"><span>Horizontal</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-ori-v" onclick="setHudProp('orientation','vertical')"><span>Vertical</span><span class="switch-dot"></span></button>
              </div>
            </div>

            <div>
              <div class="sec-title" style="margin-bottom:9px;">Position de la barre</div>
              <div class="row-2">
                <button class="toggle-card" id="hud-pos-tl" onclick="setHudProp('position','top-left')"><span>Haut Gauche</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-pos-tr" onclick="setHudProp('position','top-right')"><span>Haut Droite</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-pos-bl" onclick="setHudProp('position','bottom-left')"><span>Bas Gauche</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-pos-br" onclick="setHudProp('position','bottom-right')"><span>Bas Droite</span><span class="switch-dot"></span></button>
              </div>
            </div>

            <div>
              <div class="sec-title" style="margin-bottom:5px;">Opacité barre (<span id="hud-op-lbl">92</span>%)</div>
              <input type="range" id="hud-opacity" min="35" max="100" value="92" style="width:100%;" oninput="previewHudOpacity(this.value)" onchange="setHudProp('opacity', Number(this.value)/100)" />
            </div>

            <div>
              <div class="sec-title" style="margin-bottom:4px;">Modules affichés</div>
              <div class="toggle-grid">
                <button class="toggle-card" id="hud-sh-fps" onclick="toggleHudBool('show_fps')"><span>FPS en direct</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-sh-image" onclick="toggleHudBool('show_image')"><span>Image / Logo</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-sh-clock" onclick="toggleHudBool('show_clock')"><span>Heure</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-sh-timer" onclick="toggleHudBool('show_timer')"><span>Chrono session</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-sh-cpu" onclick="toggleHudBool('show_cpu')"><span>CPU %</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-sh-ram" onclick="toggleHudBool('show_ram')"><span>RAM %</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-sh-gpu" onclick="toggleHudBool('show_gpu')"><span>GPU Temp</span><span class="switch-dot"></span></button>
                <button class="toggle-card" id="hud-sh-media" onclick="toggleHudBool('show_media')"><span>Média Spotify</span><span class="switch-dot"></span></button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 5. CONFIGS & STATS -->
      <section class="tab-view hidden" id="tab-configs">
        <div class="head-row">
          <div><h2>Configs &amp; Stats</h2><p>Réticules, snapshots .ini et temps de jeu cumulé.</p></div>
          <div class="btn-row">
            <button class="btn-ghost" onclick="openFileConfigModal()">+ Snapshot .ini</button>
            <button class="btn-primary" onclick="openCrosshairModal()">+ Profil réticule</button>
          </div>
        </div>
        <div class="sub-tabs">
          <button class="sub-tab active" id="st-tab-cfg" onclick="setCfgSub('cfg')">Configs &amp; Réticules</button>
          <button class="sub-tab" id="st-tab-stat" onclick="setCfgSub('stat')">Stats &amp; Temps de jeu</button>
        </div>
        <div id="sub-cfg" style="display:flex;flex-direction:column;gap:22px;">
          <div><div class="sec-title">Snapshots de fichiers</div><div class="grid-3" id="file-configs-grid"></div></div>
          <div><div class="sec-title">Réticules &amp; Sensibilités</div><div class="grid-2" id="crosshairs-grid"></div></div>
        </div>
        <div id="sub-stat" style="display:none;flex-direction:column;gap:20px;">
          <div class="grid-3" id="stats-kpi-grid"></div>
          <div style="display:flex;flex-direction:column;gap:10px;" id="stats-table"></div>
        </div>
      </section>

      <!-- 6. OUTILS -->
      <section class="tab-view hidden" id="tab-tools">
        <div class="head-row"><div><h2>Sécurité &amp; Outils</h2><p>Coffre-fort AES, Stream Deck Wi-Fi et mises à jour GitHub.</p></div></div>
        <div class="sub-tabs">
          <button class="sub-tab active" id="tl-tab-vault" onclick="setToolSub('vault')">venUs Vault</button>
          <button class="sub-tab" id="tl-tab-deck" onclick="setToolSub('deck')">Stream Deck Wi-Fi</button>
          <button class="sub-tab" id="tl-tab-sys" onclick="setToolSub('sys')">Plugins &amp; MAJ</button>
        </div>
        <div id="sub-vault" style="display:flex;flex-direction:column;gap:18px;">
          <div class="btn-row" id="vault-header-actions" style="display:none;"><button class="btn-primary" onclick="openVaultAddModal()">+ Entrée</button><button class="btn-ghost" onclick="vaultLock()">Verrouiller</button></div>
          <div id="vault-locked-box" class="card" style="max-width:440px;">
            <h3 id="vault-lock-title" style="margin-bottom:6px;">Déverrouiller</h3>
            <p id="vault-lock-desc" style="font-size:13px;color:var(--text-2);margin-bottom:16px;"></p>
            <div class="field"><label>Mot de passe maître</label><input type="password" id="inp-vault-pass" placeholder="••••••••" onkeydown="if(event.key==='Enter')vaultUnlock()" /></div>
            <button class="btn-primary" onclick="vaultUnlock()">Ouvrir</button>
          </div>
          <div id="vault-unlocked-box" style="display:none;"><div class="grid-2" id="vault-grid"></div></div>
        </div>
        <div id="sub-deck" style="display:none;flex-direction:column;gap:18px;">
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
              <div><h3>Serveur Stream Deck Wi-Fi</h3><p style="font-size:12.5px;color:var(--text-2);margin-top:2px;">Ouvre ce lien sur ton téléphone.</p></div>
              <button class="btn-primary" id="btn-deck-toggle" onclick="toggleDeck()">Activer</button>
            </div>
            <div style="display:flex;gap:10px;"><div class="mono-box" id="deck-url-box" style="flex:1;">Serveur arrêté</div><button class="btn-ghost" onclick="copyDeckUrl()">Copier</button></div>
          </div>
        </div>
        <div id="sub-sys" style="display:none;flex-direction:column;gap:18px;">
          <div class="card" style="display:flex;justify-content:space-between;align-items:center;">
            <div><h3>Plugins launchers</h3><p style="font-size:12.5px;color:var(--text-2);">Ajoute de nouvelles plateformes via JSON.</p></div>
            <div class="btn-row"><button class="btn-ghost" onclick="window.pywebview.api.open_plugins_folder()">Dossier plugins/</button><button class="btn-primary" onclick="openPluginModal()">+ Créer</button></div>
          </div>
          <div class="card">
            <h3 style="margin-bottom:6px;">Auto-Update GitHub</h3>
            <p style="font-size:12.5px;color:var(--text-2);margin-bottom:12px;">Format : <code>utilisateur/depot</code></p>
            <div style="display:flex;gap:10px;"><input id="inp-gh-repo" type="text" placeholder="monpseudo/venus" style="flex:1;padding:10px 13px;border-radius:10px;border:1px solid var(--border);background:#060709;color:#fff;outline:none;" /><button class="btn-primary" onclick="checkUpdates()">Vérifier</button></div>
            <div id="update-result" style="font-size:12.5px;color:var(--text-2);margin-top:10px;"></div>
          </div>
        </div>
      </section>
    </main>
  </div>
</div>

<!-- COMMAND PALETTE & MODALS -->
<div class="cmd-backdrop" id="cmd-backdrop" onclick="if(event.target===this)closeCmd()">
  <div class="cmd-box">
    <div class="cmd-in">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" style="opacity:.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input id="cmd-input" type="text" placeholder="Compte, BOOST MAX, Studio HUD..." oninput="renderCmdList()" onkeydown="cmdKeydown(event)" />
      <span class="kbd">ESC</span>
    </div>
    <div class="cmd-list" id="cmd-list"></div>
  </div>
</div>

<div class="modal-backdrop" id="account-modal"><div class="modal">
  <h3 id="am-title">Compte</h3><p id="am-desc"></p>
  <div class="row-2"><div class="field"><label>Nom du profil</label><input id="am-label" placeholder="Ex: RL Main" /></div><div class="field"><label>Rang actuel</label><input id="am-rank" placeholder="Ex: Champion II" /></div></div>
  <div class="field" id="am-steam-wrap" style="display:none;"><label>Identifiant Steam</label><input id="am-steam" /></div>
  <div class="field"><label>Jeu lancé directement (.exe ou URI)</label><div style="display:flex;gap:8px;"><input id="am-game-exe" placeholder="Optionnel" /><button class="btn-ghost" onclick="pickGameExe()">Parcourir</button></div></div>
  <div class="field"><label>Options de lancement</label><input id="am-args" placeholder="-high" /></div>
  <div id="am-banner-wrap" style="display:none;">
    <div class="modal-banner-preview" id="am-banner-preview"><span>Aucune bannière</span></div>
    <div class="row-2" style="margin-bottom:12px;">
      <button class="btn-primary" onclick="pickBannerPC()" style="justify-content:center;">Importer depuis le PC</button>
      <button class="btn-ghost" onclick="clearBanner()" style="justify-content:center;">Retirer bannière</button>
    </div>
    <div class="field"><label>Ou lien URL / chemin local d'image</label><input id="am-banner-url" placeholder="https://... ou C:\...\image.png" /></div>
  </div>
  <div class="modal-actions"><button class="btn-ghost" onclick="closeModals()">Annuler</button><button class="btn-primary" onclick="saveAccountModal()">Enregistrer</button></div>
</div></div>

<div class="modal-backdrop" id="crosshair-modal"><div class="modal">
  <h3>Profil réticule</h3>
  <div class="row-2"><div class="field"><label>Nom</label><input id="ch-name" /></div><div class="field"><label>Jeu</label><input id="ch-game" placeholder="Valorant" /></div></div>
  <div class="field"><label>Code réticule</label><input id="ch-code" /></div>
  <div class="row-2"><div class="field"><label>DPI</label><input id="ch-dpi" placeholder="800" /></div><div class="field"><label>Sensibilité</label><input id="ch-sens" placeholder="0.32" /></div></div>
  <div class="field"><label>Notes</label><input id="ch-notes" /></div>
  <div class="modal-actions"><button class="btn-ghost" onclick="closeModals()">Annuler</button><button class="btn-primary" onclick="submitCrosshair()">Sauvegarder</button></div>
</div></div>

<div class="modal-backdrop" id="filecfg-modal"><div class="modal">
  <h3>Snapshot .ini</h3><p>Sélectionne un fichier .ini ou .cfg à sauvegarder.</p>
  <div class="field"><label>Nom</label><input id="fc-name" placeholder="Fortnite Perf" /></div>
  <div class="field"><label>Jeu</label><input id="fc-game" placeholder="Fortnite" /></div>
  <div class="modal-actions"><button class="btn-ghost" onclick="closeModals()">Annuler</button><button class="btn-primary" onclick="submitFileConfig()">Choisir</button></div>
</div></div>

<div class="modal-backdrop" id="vault-modal"><div class="modal">
  <h3>Entrée chiffrée</h3>
  <div class="row-2"><div class="field"><label>Titre</label><input id="v-title" /></div><div class="field"><label>Catégorie</label><select id="v-cat"><option>Mot de passe</option><option>Code 2FA</option><option>Note</option></select></div></div>
  <div class="field"><label>Identifiant</label><input id="v-user" /></div>
  <div class="field"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="margin:0;">Secret</label><button class="chip-tool" onclick="genVaultPassword()">Générer</button></div><textarea id="v-secret" rows="3"></textarea></div>
  <div class="field"><label>Notes</label><input id="v-notes" /></div>
  <div class="modal-actions"><button class="btn-ghost" onclick="closeModals()">Annuler</button><button class="btn-primary" onclick="submitVaultEntry()">Chiffrer</button></div>
</div></div>

<div class="modal-backdrop" id="plugin-modal"><div class="modal">
  <h3>Créer un plugin</h3>
  <div class="row-2"><div class="field"><label>ID</label><input id="pl-id" placeholder="discord" /></div><div class="field"><label>Nom</label><input id="pl-name" placeholder="Discord" /></div></div>
  <div class="field"><label>Sous-titre</label><input id="pl-sub" /></div>
  <div class="field"><label>Processus (virgule)</label><input id="pl-procs" placeholder="Discord.exe" /></div>
  <div class="field"><label>Fichier/dossier session</label><input id="pl-sess" /></div>
  <div class="field"><label>.exe par défaut</label><input id="pl-exe" /></div>
  <div class="modal-actions"><button class="btn-ghost" onclick="closeModals()">Annuler</button><button class="btn-primary" onclick="submitPlugin()">Installer</button></div>
</div></div>

<div class="busy-overlay" id="busy"><div class="busy-card"><div class="spinner"></div><div id="busy-text">Traitement...</div></div></div>
<div class="toast-wrap" id="toasts"></div>

<script>
  let state = null, currentPlat = "epic", modalMode = "add", editingAccId = null;
  let vaultEntries = [], soundEnabled = true, cmdItems = [], cmdSel = 0;

  window.addEventListener("mousemove", e => {
    document.documentElement.style.setProperty("--gx", e.clientX + "px");
    document.documentElement.style.setProperty("--gy", e.clientY + "px");
  });

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  let actx = null, noiseBuf = null, reverbNode = null, lastHover = 0;
  function initAudio() {
    if (!actx) {
      actx = new AudioCtx();
      noiseBuf = actx.createBuffer(1, Math.floor(actx.sampleRate * 0.2), actx.sampleRate);
      const nd = noiseBuf.getChannelData(0); for (let i = 0; i < nd.length; i++) nd[i] = Math.random()*2-1;
      const irLen = Math.floor(actx.sampleRate * 0.3), ir = actx.createBuffer(2, irLen, actx.sampleRate);
      for (let ch = 0; ch < 2; ch++) { const d = ir.getChannelData(ch); for (let i = 0; i < irLen; i++) d[i] = (Math.random()*2-1)*Math.pow(1-i/irLen, 3.6); }
      reverbNode = actx.createConvolver(); reverbNode.buffer = ir;
      const wet = actx.createGain(); wet.gain.value = 0.22; reverbNode.connect(wet).connect(actx.destination);
    }
    if (actx.state === "suspended") actx.resume();
    return actx;
  }
  const SFX = {
    hover() {
      if (!soundEnabled || performance.now() - lastHover < 48) return; lastHover = performance.now();
      try { const c = initAudio(), t = c.currentTime, s = c.createBufferSource(); s.buffer = noiseBuf; const f = c.createBiquadFilter(); f.type = "bandpass"; f.frequency.value = 1850; f.Q.value = 3; const g = c.createGain(); g.gain.setValueAtTime(.0001, t); g.gain.linearRampToValueAtTime(.014, t + .002); g.gain.exponentialRampToValueAtTime(.0001, t + .014); s.connect(f).connect(g).connect(c.destination); s.start(t); s.stop(t + .016); } catch {}
    },
    click() {
      if (!soundEnabled) return;
      try { const c = initAudio(), t = c.currentTime, o = c.createOscillator(), g = c.createGain(); o.frequency.setValueAtTime(160, t); o.frequency.exponentialRampToValueAtTime(56, t + .04); g.gain.setValueAtTime(.075, t); g.gain.exponentialRampToValueAtTime(.0001, t + .046); o.connect(g).connect(c.destination); g.connect(reverbNode); o.start(t); o.stop(t + .05); } catch {}
    },
    launch() {
      if (!soundEnabled) return;
      try { const c = initAudio(), t = c.currentTime, lp = c.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.setValueAtTime(500, t); lp.frequency.exponentialRampToValueAtTime(2400, t + .28); lp.connect(c.destination); lp.connect(reverbNode); [261.6, 329.6, 392, 493.9].forEach((fr, i) => { const o = c.createOscillator(), g = c.createGain(); o.type = "triangle"; o.frequency.setValueAtTime(fr, t + i * .025); g.gain.setValueAtTime(.0001, t + i * .025); g.gain.linearRampToValueAtTime(.02, t + i * .025 + .04); g.gain.exponentialRampToValueAtTime(.0001, t + .6); o.connect(g).connect(lp); o.start(t + i * .025); o.stop(t + .64); }); } catch {}
    },
    ok() {
      if (!soundEnabled) return;
      try { const c = initAudio(), t = c.currentTime; [523.2, 659.2].forEach((f, i) => { const o = c.createOscillator(), g = c.createGain(); o.frequency.setValueAtTime(f, t + i * .06); g.gain.setValueAtTime(.026, t + i * .06); g.gain.exponentialRampToValueAtTime(.0001, t + i * .06 + .22); o.connect(g).connect(c.destination); g.connect(reverbNode); o.start(t + i * .06); o.stop(t + i * .06 + .25); }); } catch {}
    },
    err() {
      if (!soundEnabled) return;
      try { const c = initAudio(), t = c.currentTime, o = c.createOscillator(), g = c.createGain(); o.frequency.setValueAtTime(135, t); o.frequency.exponentialRampToValueAtTime(72, t + .1); g.gain.setValueAtTime(.07, t); g.gain.exponentialRampToValueAtTime(.0001, t + .11); o.connect(g).connect(c.destination); o.start(t); o.stop(t + .12); } catch {}
    }
  };
  document.addEventListener("pointerenter", e => { if (e.target.closest("button, .card.clickable")) SFX.hover(); }, true);

  function platWhiteLogo(pid, size = 28) {
    const s = `width="${size}" height="${size}" viewBox="0 0 24 24"`;
    if (pid === "epic") return `<svg ${s} fill="#ffffff"><path d="M4.5 2h15A1.5 1.5 0 0 1 21 3.5v13.8a2.2 2.2 0 0 1-1.08 1.9L12 23l-7.92-3.8A2.2 2.2 0 0 1 3 17.3V3.5A1.5 1.5 0 0 1 4.5 2zm2.8 4.4v10.2h9.4v-2.2H9.8v-2h5.9v-2H9.8V8.5h6.7V6.4H7.3z"/></svg>`;
    if (pid === "riot") return `<svg ${s} fill="#ffffff"><path d="M12.7 2.2L2 7.1l2.4 9.6 3.3.5-.9-6.6 1.2-.5 1.7 7.4 3.4.5-.8-8.2 1.2-.5 1.8 9 3.6.6L22 6.6 12.7 2.2zM5.2 18.7l1.1 3 11.5-1.4-.4-2.2-12.2.6z"/></svg>`;
    if (pid === "steam") return `<svg ${s} fill="#ffffff"><path d="M12 2a10 10 0 0 0-9.9 8.6l5.4 2.2a2.9 2.9 0 0 1 1.7-.5l2.4-3.5v-.1a3.8 3.8 0 1 1 3.8 3.8h-.1l-3.4 2.4a2.9 2.9 0 0 1-5.6 1.2L2.4 14.5A10 10 0 1 0 12 2zm3.4 4.3a2.4 2.4 0 1 0 0 4.8 2.4 2.4 0 0 0 0-4.8z"/></svg>`;
    if (pid === "battlenet") return `<svg ${s} fill="none" stroke="#ffffff" stroke-width="1.7"><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(30 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-30 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(90 12 12)"/><circle cx="12" cy="12" r="2.2" fill="#ffffff" stroke="none"/></svg>`;
    if (pid === "ubisoft") return `<svg ${s} fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round"><path d="M12 3a9 9 0 1 0 8.5 12A6.5 6.5 0 1 1 12 6.5a4 4 0 1 1-3.4 6.1"/></svg>`;
    if (pid === "ea") return `<svg ${s} fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h7M3 12h6M3 16h7M13 16l4-8 4 8M14.5 13h5"/></svg>`;
    if (pid === "minecraft") return `<svg ${s} fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><rect x="6.5" y="7" width="3.5" height="3.5" fill="#fff" stroke="none"/><rect x="14" y="7" width="3.5" height="3.5" fill="#fff" stroke="none"/><path d="M9.5 15v-2.5h5V15h1.5v3h-2v-1.5h-4V18H8v-3h1.5z" fill="#fff" stroke="none"/></svg>`;
    return `<svg ${s} fill="none" stroke="#ffffff" stroke-width="1.8"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><circle cx="12" cy="12" r="3"/></svg>`;
  }

  function dismissSplash() { document.getElementById("splash").classList.add("hide"); }
  setTimeout(dismissSplash, 1150);
  function esc(s) { return String(s ?? "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
  function fmtHours(sec) { const h = (sec || 0) / 3600; return h < 1 ? Math.round((sec || 0) / 60) + " min" : h.toFixed(1) + " h"; }
  function toast(msg, err = false) {
    const w = document.getElementById("toasts"), el = document.createElement("div");
    el.className = "toast" + (err ? " error" : "");
    el.innerHTML = `<span class="dot"></span><span>${esc(msg)}</span>`;
    w.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .25s"; setTimeout(() => el.remove(), 260); }, 3400);
  }
  function setBusy(on, text = "Traitement...") { document.getElementById("busy-text").textContent = text; document.getElementById("busy").classList.toggle("open", on); }
  function closeModals() { SFX.click(); document.querySelectorAll(".modal-backdrop").forEach(m => m.classList.remove("open")); }
  function copyText(txt) { navigator.clipboard.writeText(txt); SFX.ok(); toast("Copié."); }

  function switchTab(tab) {
    SFX.click();
    document.querySelectorAll(".dock-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
    document.querySelectorAll(".tab-view").forEach(v => v.classList.toggle("hidden", v.id !== "tab-" + tab));
    if (tab === "hud") renderHudStudio();
    if (tab === "configs") { renderConfigs(); renderStats(); }
  }
  function setCfgSub(mode) { SFX.click(); document.getElementById("st-tab-cfg").classList.toggle("active", mode==="cfg"); document.getElementById("st-tab-stat").classList.toggle("active", mode==="stat"); document.getElementById("sub-cfg").style.display = mode==="cfg"?"flex":"none"; document.getElementById("sub-stat").style.display = mode==="stat"?"flex":"none"; if (mode==="stat") renderStats(); }
  function setToolSub(mode) { SFX.click(); ["vault","deck","sys"].forEach(k => { document.getElementById("tl-tab-"+k).classList.toggle("active", mode===k); document.getElementById("sub-"+k).style.display = mode===k?"flex":"none"; }); }

  function renderAll() {
    if (!state) return;
    document.getElementById("btn-overlay").classList.toggle("on", !!state.overlay_running);
    document.getElementById("btn-gamemode").classList.toggle("on", !!state.game_mode);
    document.getElementById("btn-hud-launch").textContent = state.overlay_running ? "Désactiver le HUD" : "Activer le HUD";
    const trashCount = (state.trash || []).length;
    document.getElementById("btn-recover").textContent = trashCount ? `Récupérer (${trashCount})` : "Récupérer / Corbeille";
    renderHub();
    renderPlatforms();
    if (document.getElementById("accounts-section").style.display !== "none") renderAccounts();
    renderRamSettings();
    renderHudStudio();
    renderConfigs();
    renderStats();
    renderVault();
    renderDeck();
    document.getElementById("inp-gh-repo").value = state.settings.github_repo || "";
  }

  async function pollTelemetry() {
    if (!window.pywebview || !window.pywebview.api) return;
    try {
      const t = await window.pywebview.api.get_telemetry();
      document.getElementById("dock-clock").textContent = t.clock || "--:--";
      document.getElementById("st-cpu").textContent = t.cpu + "%";
      document.getElementById("st-ram").textContent = t.ram_pct + "%";
      document.getElementById("st-ram-sub").textContent = `${t.ram_used_gb} / ${t.ram_total_gb} Go`;
      document.getElementById("st-fps").textContent = t.fps > 0 ? `${t.fps} FPS` : "-- FPS";
      document.getElementById("st-gpu-sub").textContent = t.gpu_temp !== null ? `GPU ${t.gpu_temp}°C (${t.gpu_util}%)` : "Affichage DWM";
      document.getElementById("st-track").textContent = t.track || "En pause";
      document.getElementById("btn-overlay").classList.toggle("on", !!t.overlay_running);

      document.getElementById("ram-ring").style.strokeDashoffset = 263.9 * (1 - t.ram_pct / 100);
      document.getElementById("ram-big-pct").textContent = t.ram_pct + "%";
      document.getElementById("ram-big-detail").textContent = `${t.ram_used_gb} / ${t.ram_total_gb} Go (${t.ram_free_gb} Go libres)`;
      if (t.last_boost && t.last_boost.at) {
        const mb = t.last_boost.freed_mb;
        document.getElementById("ram-big-last").textContent = `Dernier BOOST MAX (${t.last_boost.at}) : ${mb >= 1024 ? (mb/1024).toFixed(2)+' Go' : mb+' Mo'} libérés (${t.last_boost.trimmed} processus optimisés)`;
      }
      renderRamProcesses(t.top_procs || []);
    } catch {}
  }

  function renderRamProcesses(procs) {
    const wrap = document.getElementById("ram-proc-list"); if (!wrap || !state) return;
    const killSet = new Set((state.settings.ram_kill_list || []).map(x => x.toLowerCase()));
    const maxMb = Math.max(500, ...(procs.map(p => p.mb)));
    wrap.innerHTML = procs.map(p => {
      const inList = killSet.has(p.name.toLowerCase());
      return `<div class="proc-row">
        <div><div style="font-weight:500;">${esc(p.name)}</div><div class="proc-bar"><div class="proc-fill" style="width:${Math.min(100, Math.round(p.mb/maxMb*100))}%"></div></div></div>
        <div style="font-family:var(--mono);text-align:right;">${p.mb} Mo</div>
        <div style="display:flex;gap:6px;justify-content:flex-end;">
          <button class="chip-tool ${inList ? 'fav' : ''}" onclick="toggleProcBoost('${esc(p.name).replace(/'/g,"\\'")}')">${inList ? 'Cible' : '+ Cible'}</button>
          <button class="chip-tool" onclick="killProc('${esc(p.name).replace(/'/g,"\\'")}')">Fermer</button>
        </div>
      </div>`;
    }).join("");
  }

  function renderHub() {
    const allAccs = [];
    state.platforms.forEach(p => (state.accounts[p.id] || []).forEach(a => allAccs.push({ plat: p, acc: a })));
    const favs = allAccs.filter(x => x.acc.favorite);
    const displayList = (favs.length ? favs : allAccs).slice(0, 3);
    document.getElementById("hub-quick-accounts").innerHTML = displayList.length
      ? displayList.map(({ plat, acc }) => accountCardHtml(plat.id, acc)).join("")
      : `<div class="card" style="grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;">
           <span style="color:var(--text-2);font-size:13.5px;">Aucun compte affiché.</span>
           <div class="btn-row"><button class="btn-ghost" onclick="recoverAccounts()">Récupérer mes comptes</button><button class="btn-primary" onclick="switchTab('launchers')">Ajouter</button></div>
         </div>`;
    document.getElementById("hub-plats").innerHTML = state.platforms.slice(0, 3).map(p => platCardHtml(p, true)).join("");
  }

  function platCardHtml(p, fromHub = false) {
    const n = (state.accounts[p.id] || []).length;
    return `<div class="card clickable plat-card" onclick="${fromHub ? `jumpToPlatform('${p.id}')` : `openPlatform('${p.id}')`}">
      <div class="plat-top"><div class="plat-logo-box">${platWhiteLogo(p.id, 28)}</div><span class="pill-mono">${n} ${n > 1 ? 'comptes' : 'compte'}</span></div>
      <div><h3>${esc(p.name)}</h3><p>${esc(p.subtitle || 'Plugin')}</p></div>
    </div>`;
  }

  function accountCardHtml(pid, a) {
    const mediaHtml = a.banner_src
      ? `<img class="banner-img" src="${esc(a.banner_src)}" alt="" onerror="this.style.display='none'" />`
      : `<div class="banner-fallback"></div>`;
    return `<div class="card acc-card">
      <div class="banner-stage">
        <div class="banner-fallback"></div>
        ${mediaHtml}
        <div class="banner-vignette"></div>
        <div class="banner-plat-badge">${platWhiteLogo(pid, 17)}</div>
        <div class="banner-tools">
          <button class="chip-tool ${a.favorite ? 'fav' : ''}" onclick="toggleFav('${pid}','${a.id}')">★</button>
          <button class="chip-tool" onclick="openEditAccountModal('${pid}','${a.id}')">Modifier</button>
        </div>
        <div class="banner-footer"><h3>${esc(a.label)}</h3>${a.rank ? `<span class="pill-mono">${esc(a.rank)}</span>` : ''}</div>
      </div>
      <div class="acc-bar">
        <button class="btn-primary" style="flex:1;justify-content:center;" onclick="launchAcc('${pid}','${a.id}','${esc(a.label).replace(/'/g,"\\'")}')">Lancer</button>
        <button class="btn-del" onclick="deleteAcc('${pid}','${a.id}')" title="Mettre à la corbeille">✕</button>
      </div>
    </div>`;
  }

  function renderHudStudio() {
    if (!state) return;
    const h = state.settings.hud;
    const stage = document.getElementById("hud-preview-stage");
    stage.className = "hud-preview-stage pos-" + (h.position || "top-left");

    const mock = document.getElementById("hud-mock");
    mock.className = "hud-mock" + (h.orientation === "vertical" ? " vertical" : "");
    mock.style.opacity = h.opacity ?? 0.92;

    const freePrev = document.getElementById("hud-free-preview");
    const sz = h.img_size || 42;
    const parts = [];

    if (h.show_image && h.img_free && state.hud_image_src) {
      freePrev.src = state.hud_image_src;
      freePrev.style.display = "block";
      freePrev.style.width = Math.min(180, sz) + "px";
      freePrev.style.height = "auto";
      freePrev.style.opacity = h.img_opacity ?? 0.95;
      freePrev.style.left = "50%";
      freePrev.style.top = "55%";
      freePrev.style.transform = "translate(-50%,-50%)";
    } else {
      freePrev.style.display = "none";
      if (h.show_image) {
        parts.push(state.hud_image_src
          ? `<img src="${esc(state.hud_image_src)}" style="width:${Math.min(72, sz)}px;height:${Math.min(72, sz)}px;border-radius:8px;object-fit:cover;" />`
          : `<div style="display:flex;align-items:center;gap:6px;font-weight:700;color:#fff;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4"><path d="M4 5l8 14L20 5"/></svg>venUs</div>`);
      }
    }

    if (h.show_fps) parts.push(`<span style="color:#34d399;font-weight:700;">144 FPS</span>`);
    if (h.show_clock) parts.push(`<span>21:30</span>`);
    if (h.show_timer) parts.push(`<span>01:12:04</span>`);
    if (h.show_cpu) parts.push(`<span>CPU 16%</span>`);
    if (h.show_ram) parts.push(`<span>RAM 48%</span>`);
    if (h.show_gpu) parts.push(`<span>GPU 59°C</span>`);
    if (h.show_media) parts.push(`<span>♪ Spotify</span>`);
    mock.innerHTML = parts.join("") || `<span style="color:var(--text-3);">Barre vide</span>`;

    document.getElementById("hud-img-docked").classList.toggle("on", !h.img_free);
    document.getElementById("hud-img-free").classList.toggle("on", !!h.img_free);
    document.getElementById("hud-img-size").value = sz;
    document.getElementById("hud-sz-lbl").textContent = sz;
    const iop = Math.round((h.img_opacity ?? 0.95) * 100);
    document.getElementById("hud-img-op").value = iop;
    document.getElementById("hud-iop-lbl").textContent = iop;

    document.getElementById("hud-ori-h").classList.toggle("on", h.orientation !== "vertical");
    document.getElementById("hud-ori-v").classList.toggle("on", h.orientation === "vertical");
    ["tl:top-left","tr:top-right","bl:bottom-left","br:bottom-right"].forEach(pair => {
      const [id, val] = pair.split(":"); document.getElementById("hud-pos-" + id).classList.toggle("on", h.position === val);
    });
    const opPct = Math.round((h.opacity ?? 0.92) * 100);
    document.getElementById("hud-opacity").value = opPct;
    document.getElementById("hud-op-lbl").textContent = opPct;
    ["fps","image","clock","timer","cpu","ram","gpu","media"].forEach(k => {
      document.getElementById("hud-sh-" + k).classList.toggle("on", !!h["show_" + k]);
    });
  }
  function previewHudOpacity(v) { document.getElementById("hud-op-lbl").textContent = v; document.getElementById("hud-mock").style.opacity = Number(v)/100; }
  function previewHudSize(v) { document.getElementById("hud-sz-lbl").textContent = v; const fp = document.getElementById("hud-free-preview"); if (fp.style.display !== "none") fp.style.width = Math.min(180, Number(v)) + "px"; }
  function previewHudImgOp(v) { document.getElementById("hud-iop-lbl").textContent = v; document.getElementById("hud-free-preview").style.opacity = Number(v)/100; }
  async function setHudProp(k, v) { SFX.click(); const r = await window.pywebview.api.save_hud_settings({ [k]: v }); if (r.ok) { state = r.state; renderHudStudio(); } }
  async function toggleHudBool(k) { SFX.click(); const r = await window.pywebview.api.save_hud_settings({ [k]: !state.settings.hud[k] }); if (r.ok) { state = r.state; renderHudStudio(); } }
  async function pickHudImage() { SFX.click(); const r = await window.pywebview.api.pick_hud_image(); if (r && r.ok) { state = r.state; renderHudStudio(); SFX.ok(); toast(r.message); } else if (r && !r.cancelled) { SFX.err(); toast(r.message || "Erreur image.", true); } }
  async function clearHudImage() { SFX.click(); const r = await window.pywebview.api.clear_hud_image(); if (r && r.ok) { state = r.state; renderHudStudio(); toast(r.message); } }

  function renderPlatforms() { document.getElementById("platform-grid").innerHTML = state.platforms.map(p => platCardHtml(p, false)).join(""); }
  function jumpToPlatform(pid) { switchTab("launchers"); openPlatform(pid); }
  function backToLaunchers() { SFX.click(); document.getElementById("accounts-section").style.display = "none"; document.getElementById("launchers-hub").style.display = "block"; }
  function openPlatform(pid) {
    SFX.click(); currentPlat = pid;
    const p = state.platforms.find(x => x.id === pid);
    document.getElementById("plat-head-logo").innerHTML = platWhiteLogo(pid, 24);
    document.getElementById("plat-title").textContent = p ? p.name : pid;
    document.getElementById("plat-sub").textContent = p ? (p.subtitle || "") : "";
    document.getElementById("btn-other-acc").style.display = pid === "steam" ? "none" : "inline-flex";
    document.getElementById("btn-add-acc").textContent = pid === "steam" ? "+ Ajouter" : "+ Capturer";
    document.getElementById("launchers-hub").style.display = "none";
    document.getElementById("accounts-section").style.display = "block";
    renderAccounts();
  }
  function renderAccounts() {
    const list = state.accounts[currentPlat] || [];
    document.getElementById("accounts-grid").innerHTML = list.length ? list.map(a => accountCardHtml(currentPlat, a)).join("") : `<div class="card" style="grid-column:1/-1;text-align:center;padding:56px;color:var(--text-2);">Aucun compte enregistré.</div>`;
  }
  async function recoverAccounts() {
    SFX.click();
    const r = await window.pywebview.api.recover_accounts();
    state = r.state; renderAll();
    r.ok ? (SFX.ok(), toast(r.message)) : (SFX.err(), toast(r.message, true));
  }
  async function toggleFav(pid, id) { SFX.click(); const r = await window.pywebview.api.toggle_favorite(pid, id); if (r.ok) { state = r.state; renderAll(); toast(r.message); } }
  function openAddAccountModal() {
    SFX.click(); modalMode = "add"; editingAccId = null;
    document.getElementById("am-title").textContent = "Nouveau compte";
    document.getElementById("am-desc").textContent = currentPlat === "steam" ? "Entre ton identifiant Steam." : "Le launcher se fermera 2s pour sauvegarder la session.";
    document.getElementById("am-steam-wrap").style.display = currentPlat === "steam" ? "block" : "none";
    document.getElementById("am-banner-wrap").style.display = "none";
    ["am-label","am-rank","am-steam","am-game-exe","am-args"].forEach(i => document.getElementById(i).value = "");
    document.getElementById("account-modal").classList.add("open");
  }
  function updateModalBannerPreview(src) {
    const box = document.getElementById("am-banner-preview");
    box.innerHTML = src ? `<img src="${esc(src)}" alt="" />` : `<span>Aucune bannière</span>`;
  }
  function openEditAccountModal(pid, id) {
    SFX.click(); currentPlat = pid; modalMode = "edit"; editingAccId = id;
    const a = (state.accounts[pid] || []).find(x => x.id === id); if (!a) return;
    document.getElementById("am-title").textContent = "Modifier — " + a.label;
    document.getElementById("am-desc").textContent = "Modifie la bannière, le rang ou le jeu lancé automatiquement.";
    document.getElementById("am-steam-wrap").style.display = "none";
    document.getElementById("am-banner-wrap").style.display = "block";
    document.getElementById("am-label").value = a.label || "";
    document.getElementById("am-rank").value = a.rank || "";
    document.getElementById("am-game-exe").value = a.game_exe || "";
    document.getElementById("am-args").value = a.launch_args || "";
    document.getElementById("am-banner-url").value = a.banner && a.banner.startsWith("http") ? a.banner : "";
    updateModalBannerPreview(a.banner_src || "");
    document.getElementById("account-modal").classList.add("open");
  }
  async function pickGameExe() { const r = await window.pywebview.api.pick_game_exe(); if (r.ok) document.getElementById("am-game-exe").value = r.path; }
  async function pickBannerPC() {
    SFX.click();
    const r = await window.pywebview.api.pick_banner_file(currentPlat, editingAccId);
    if (r && r.ok) {
      state = r.state; renderAll();
      const updated = (state.accounts[currentPlat] || []).find(x => x.id === editingAccId);
      updateModalBannerPreview(updated ? updated.banner_src : "");
      SFX.ok(); toast(r.message);
    } else if (r && !r.cancelled) {
      SFX.err(); toast(r.message || "Impossible de charger l'image.", true);
    }
  }
  async function clearBanner() {
    SFX.click();
    const r = await window.pywebview.api.clear_banner(currentPlat, editingAccId);
    if (r && r.ok) { state = r.state; renderAll(); updateModalBannerPreview(""); toast(r.message); }
  }
  async function saveAccountModal() {
    const label = document.getElementById("am-label").value.trim(), rank = document.getElementById("am-rank").value.trim();
    const gameExe = document.getElementById("am-game-exe").value.trim(), args = document.getElementById("am-args").value.trim();
    if (!label) { SFX.err(); toast("Nom requis.", true); return; }
    if (modalMode === "edit") {
      const r = await window.pywebview.api.update_account_meta(currentPlat, editingAccId, label, rank, gameExe, args, document.getElementById("am-banner-url").value.trim());
      if (r.ok) { state = r.state; closeModals(); renderAll(); SFX.ok(); toast(r.message); }
      return;
    }
    if (currentPlat === "steam") {
      const r = await window.pywebview.api.add_steam_account(label, document.getElementById("am-steam").value.trim(), rank, gameExe, args);
      if (r.ok) { state = r.state; closeModals(); renderAll(); SFX.ok(); toast(r.message); } else { SFX.err(); toast(r.message, true); }
      return;
    }
    closeModals(); setBusy(true, "Capture...");
    const r = await window.pywebview.api.capture_account(currentPlat, label, rank, gameExe, args);
    setBusy(false);
    if (r.ok) { state = r.state; renderAll(); SFX.ok(); toast(r.message); } else { SFX.err(); toast(r.message, true); }
  }
  async function launchAcc(pid, id, label) { SFX.launch(); setBusy(true, "Lancement — " + label + "..."); const r = await window.pywebview.api.launch_account(pid, id); setBusy(false); r.ok ? (SFX.ok(), toast(r.message)) : (SFX.err(), toast(r.message, true)); }
  async function deleteAcc(pid, id) { SFX.click(); const r = await window.pywebview.api.delete_account(pid, id); if (r.ok) { state = r.state; renderAll(); toast(r.message); } }
  async function configureExe() { const r = await window.pywebview.api.configure_exe_path(currentPlat); if (r && r.ok) { state = r.state; SFX.ok(); toast(r.message); } }
  async function prepareNewAccount() { setBusy(true, "Session vierge..."); const r = await window.pywebview.api.prepare_new_account(currentPlat); setBusy(false); r.ok ? (SFX.ok(), toast(r.message)) : (SFX.err(), toast(r.message, true)); }

  function renderRamSettings() {
    document.getElementById("opt-ram-auto").classList.toggle("on", !!state.settings.ram_boost_enabled);
    document.getElementById("opt-ram-power").classList.toggle("on", state.settings.ram_high_power !== false);
  }
  async function toggleRamSetting(k) { SFX.click(); const r = await window.pywebview.api.save_settings({ [k]: !state.settings[k] }); state = r.state; renderRamSettings(); }
  async function toggleProcBoost(n) { SFX.click(); const r = await window.pywebview.api.toggle_proc_in_boost_list(n); if (r.ok) { state = r.state; toast(r.message); pollTelemetry(); } }
  async function killProc(n) { SFX.click(); const r = await window.pywebview.api.kill_single_process(n); if (r.ok) { SFX.ok(); toast(r.message); pollTelemetry(); } }
  async function runBoostMax(closeTargets = false) {
    SFX.launch(); setBusy(true, closeTargets ? "BOOST MAX + fermeture cibles..." : "BOOST MAX (Safe) — Libération RAM...");
    const r = await window.pywebview.api.run_boost_max(closeTargets);
    setBusy(false);
    if (r.ok) { state = r.state; SFX.ok(); toast(r.message); pollTelemetry(); }
  }
  async function toggleOverlay() { SFX.click(); const r = await window.pywebview.api.toggle_overlay(); if (r.ok) { state = r.state; renderAll(); toast(r.message); } else { SFX.err(); toast(r.message, true); } }
  async function toggleGameMode() { SFX.launch(); setBusy(true, "Game Mode..."); const r = await window.pywebview.api.toggle_game_mode(); setBusy(false); if (r.ok) { state = r.state; renderAll(); SFX.ok(); toast(r.message); pollTelemetry(); } }
  async function runMacro(a) { SFX.click(); const r = await window.pywebview.api.run_macro(a, {}); toast(r.message || "OK", !r.ok); }

  function openCrosshairModal() { SFX.click(); document.getElementById("crosshair-modal").classList.add("open"); }
  function openFileConfigModal() { SFX.click(); document.getElementById("filecfg-modal").classList.add("open"); }
  async function submitCrosshair() { const r = await window.pywebview.api.add_config_profile(document.getElementById("ch-name").value, document.getElementById("ch-game").value, document.getElementById("ch-code").value, document.getElementById("ch-dpi").value, document.getElementById("ch-sens").value, document.getElementById("ch-notes").value); if (r.ok) { state = r.state; closeModals(); renderConfigs(); SFX.ok(); toast(r.message); } }
  async function submitFileConfig() { const n = document.getElementById("fc-name").value, g = document.getElementById("fc-game").value; closeModals(); const r = await window.pywebview.api.snapshot_game_config(n, g); if (r && r.ok) { state = r.state; renderConfigs(); SFX.ok(); toast(r.message); } }
  async function applyFileCfg(id) { const r = await window.pywebview.api.apply_game_config(id); r.ok ? (SFX.ok(), toast(r.message)) : (SFX.err(), toast(r.message, true)); }
  async function delFileCfg(id) { const r = await window.pywebview.api.delete_game_config(id); if (r.ok) { state = r.state; renderConfigs(); } }
  async function delCrosshair(id) { const r = await window.pywebview.api.delete_config_profile(id); if (r.ok) { state = r.state; renderConfigs(); } }
  function copyCrosshairById(id) { const c = (state.config_profiles || []).find(x => x.id === id); if (c) copyText(c.crosshair); }
  function renderConfigs() {
    const fc = state.file_configs || [];
    document.getElementById("file-configs-grid").innerHTML = fc.length ? fc.map(c => `<div class="card"><div style="display:flex;justify-content:space-between;margin-bottom:8px;"><h3>${esc(c.name)}</h3><span class="pill-mono">${esc(c.game)}</span></div><div style="font-size:11.5px;color:var(--text-3);margin-bottom:14px;word-break:break-all;font-family:var(--mono);">${esc(c.target_path)}</div><div class="btn-row"><button class="btn-primary" style="flex:1;justify-content:center;" onclick="applyFileCfg('${c.id}')">Appliquer</button><button class="btn-del" onclick="delFileCfg('${c.id}')">✕</button></div></div>`).join("") : `<div class="card" style="color:var(--text-2);">Aucun snapshot .ini.</div>`;
    const ch = state.config_profiles || [];
    document.getElementById("crosshairs-grid").innerHTML = ch.length ? ch.map(c => `<div class="card"><div style="display:flex;justify-content:space-between;margin-bottom:8px;"><h3>${esc(c.name)}</h3><span class="pill-mono">${esc(c.game)}</span></div><div style="font-size:12.5px;color:var(--text-2);margin-bottom:10px;">DPI <b>${esc(c.dpi||'-')}</b> &bull; Sens <b>${esc(c.sens||'-')}</b></div>${c.crosshair ? `<div class="mono-box" style="margin-bottom:12px;">${esc(c.crosshair)}</div>` : ''}<div class="btn-row">${c.crosshair ? `<button class="btn-primary" onclick="copyCrosshairById('${c.id}')">Copier</button>` : ''}<button class="btn-del" onclick="delCrosshair('${c.id}')">✕</button></div></div>`).join("") : `<div class="card" style="color:var(--text-2);">Aucun profil réticule.</div>`;
  }
  function renderStats() {
    let totalSec = 0, totalAcc = 0, rows = [];
    state.platforms.forEach(p => (state.accounts[p.id] || []).forEach(a => { totalAcc++; totalSec += (a.playtime_sec || 0); rows.push({ plat: p.name, pid: p.id, label: a.label, rank: a.rank || "—", sec: a.playtime_sec || 0 }); }));
    rows.sort((a, b) => b.sec - a.sec);
    document.getElementById("stats-kpi-grid").innerHTML = `<div class="card"><div class="stat-lbl">Temps cumulé</div><div class="stat-num" style="margin-top:6px;">${fmtHours(totalSec)}</div></div><div class="card"><div class="stat-lbl">Comptes actifs</div><div class="stat-num" style="margin-top:6px;">${totalAcc}</div></div><div class="card"><div class="stat-lbl">Plateformes</div><div class="stat-num" style="margin-top:6px;">${state.platforms.length}</div></div>`;
    document.getElementById("stats-table").innerHTML = rows.map(r => `<div class="list-row"><div style="display:flex;align-items:center;gap:12px;">${platWhiteLogo(r.pid, 18)}<b>${esc(r.label)}</b><span style="color:var(--text-2);font-size:12px;">${esc(r.plat)}</span></div><div style="display:flex;gap:12px;align-items:center;"><span class="pill-mono">${esc(r.rank)}</span><span style="font-family:var(--mono);font-size:12.5px;">${fmtHours(r.sec)}</span></div></div>`).join("");
  }

  function renderVault() {
    const u = !!state.vault_unlocked;
    document.getElementById("vault-locked-box").style.display = u ? "none" : "block";
    document.getElementById("vault-unlocked-box").style.display = u ? "block" : "none";
    document.getElementById("vault-header-actions").style.display = u ? "flex" : "none";
    document.getElementById("vault-lock-title").textContent = state.vault_exists ? "Déverrouiller le coffre" : "Créer vault.enc";
    document.getElementById("vault-lock-desc").textContent = state.vault_exists ? "Chiffrement local AES." : "Définis un mot de passe maître hors-ligne.";
    if (!u) return;
    document.getElementById("vault-grid").innerHTML = vaultEntries.length ? vaultEntries.map((e, i) => `<div class="card"><div style="display:flex;justify-content:space-between;margin-bottom:6px;"><h3>${esc(e.title)}</h3><span class="pill-mono">${esc(e.category)}</span></div>${e.username ? `<div style="font-size:12.5px;color:var(--text-2);margin-bottom:8px;">${esc(e.username)}</div>` : ''}<div class="mono-box" style="margin-bottom:12px;filter:blur(5px);cursor:pointer;" onclick="this.style.filter=this.style.filter?'':'blur(5px)'">${esc(e.secret)}</div><div class="btn-row"><button class="btn-primary" onclick="copyVaultIdx(${i})">Copier</button><button class="btn-del" onclick="vaultDelete('${e.id}')">✕</button></div></div>`).join("") : `<div class="card" style="color:var(--text-2);">Coffre vide.</div>`;
  }
  function copyVaultIdx(i) { if (vaultEntries[i]) copyText(vaultEntries[i].secret); }
  async function vaultUnlock() { const r = await window.pywebview.api.vault_unlock(document.getElementById("inp-vault-pass").value); if (r.ok) { state = r.state; vaultEntries = r.entries || []; document.getElementById("inp-vault-pass").value = ""; renderVault(); SFX.ok(); toast("Ouvert."); } else { SFX.err(); toast(r.message, true); } }
  async function vaultLock() { const r = await window.pywebview.api.vault_lock(); state = r.state; vaultEntries = []; renderVault(); toast("Verrouillé."); }
  function openVaultAddModal() { SFX.click(); ["v-title","v-user","v-secret","v-notes"].forEach(i => document.getElementById(i).value = ""); document.getElementById("vault-modal").classList.add("open"); }
  async function genVaultPassword() { SFX.click(); const r = await window.pywebview.api.generate_password(22); if (r.ok) document.getElementById("v-secret").value = r.password; }
  async function submitVaultEntry() { const r = await window.pywebview.api.vault_add(document.getElementById("v-title").value, document.getElementById("v-cat").value, document.getElementById("v-user").value, document.getElementById("v-secret").value, document.getElementById("v-notes").value); if (r.ok) { vaultEntries = r.entries; closeModals(); renderVault(); SFX.ok(); toast("Chiffré."); } }
  async function vaultDelete(id) { const r = await window.pywebview.api.vault_delete(id); if (r.ok) { vaultEntries = r.entries; renderVault(); } }

  function renderDeck() { document.getElementById("btn-deck-toggle").textContent = state.deck_running ? "Arrêter" : "Activer"; document.getElementById("deck-url-box").textContent = state.deck_running ? state.deck_url : "Serveur arrêté"; }
  function copyDeckUrl() { if (state.deck_running) copyText(state.deck_url); else toast("Serveur arrêté.", true); }
  async function toggleDeck() { SFX.click(); const r = await window.pywebview.api.toggle_deck(); if (r.ok) { state = r.state; renderDeck(); SFX.ok(); toast(r.running ? "Actif : " + r.url : "Arrêté."); } }
  function openPluginModal() { SFX.click(); document.getElementById("plugin-modal").classList.add("open"); }
  async function submitPlugin() { const r = await window.pywebview.api.create_plugin(document.getElementById("pl-id").value, document.getElementById("pl-name").value, document.getElementById("pl-sub").value, document.getElementById("pl-procs").value, document.getElementById("pl-sess").value, document.getElementById("pl-exe").value); if (r.ok) { state = r.state; closeModals(); renderAll(); SFX.ok(); toast(r.message); } else { SFX.err(); toast(r.message, true); } }
  async function checkUpdates() { setBusy(true, "GitHub..."); const r = await window.pywebview.api.check_updates(document.getElementById("inp-gh-repo").value.trim()); setBusy(false); const box = document.getElementById("update-result"); if (r.ok && r.has_update) { box.innerHTML = `${esc(r.message)} <button class="btn-primary" style="margin-left:8px;height:30px;" onclick="window.pywebview.api.open_url('${esc(r.url)}')">Télécharger</button>`; } else box.textContent = r.message; }

  function openCmd() { SFX.click(); document.getElementById("cmd-input").value = ""; document.getElementById("cmd-backdrop").classList.add("open"); cmdSel = 0; renderCmdList(); setTimeout(() => document.getElementById("cmd-input").focus(), 30); }
  function closeCmd() { document.getElementById("cmd-backdrop").classList.remove("open"); }
  function renderCmdList() {
    const q = document.getElementById("cmd-input").value.trim().toLowerCase(), all = [];
    if (state) state.platforms.forEach(p => (state.accounts[p.id] || []).forEach(a => all.push({ title: `Lancer ${a.label}`, tag: p.name, run: () => launchAcc(p.id, a.id, a.label) })));
    all.push(
      { title: "BOOST MAX (Safe RAM)", tag: "Mémoire", run: () => runBoostMax(false) },
      { title: "Studio HUD (FPS & Image)", tag: "HUD", run: () => switchTab("hud") },
      { title: "Activer / Désactiver Game Mode", tag: "Perf", run: () => toggleGameMode() },
      { title: "Récupérer des comptes", tag: "Corbeille", run: () => recoverAccounts() }
    );
    cmdItems = all.filter(it => !q || it.title.toLowerCase().includes(q) || it.tag.toLowerCase().includes(q)).slice(0, 9);
    if (cmdSel >= cmdItems.length) cmdSel = 0;
    document.getElementById("cmd-list").innerHTML = cmdItems.map((it, i) => `<div class="cmd-item ${i === cmdSel ? 'selected' : ''}" onclick="execCmd(${i})"><span>${esc(it.title)}</span><span class="pill-mono">${esc(it.tag)}</span></div>`).join("") || `<div class="cmd-item">Aucun résultat</div>`;
  }
  function execCmd(i) { closeCmd(); if (cmdItems[i]) cmdItems[i].run(); }
  function cmdKeydown(e) { if (e.key === "ArrowDown") { e.preventDefault(); cmdSel = (cmdSel + 1) % Math.max(1, cmdItems.length); renderCmdList(); } else if (e.key === "ArrowUp") { e.preventDefault(); cmdSel = (cmdSel - 1 + Math.max(1, cmdItems.length)) % Math.max(1, cmdItems.length); renderCmdList(); } else if (e.key === "Enter") { e.preventDefault(); execCmd(cmdSel); } }
  document.addEventListener("keydown", e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmd(); } else if (e.key === "Escape") { closeCmd(); closeModals(); } });

  const ICON_ON = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/></svg>`;
  const ICON_OFF = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>`;
  function toggleSound() { soundEnabled = !soundEnabled; document.getElementById("sound-btn").innerHTML = soundEnabled ? ICON_ON : ICON_OFF; if (soundEnabled) SFX.click(); if (window.pywebview) window.pywebview.api.save_settings({ sound: soundEnabled }); }

  let booted = false;
  async function boot() {
    if (booted) return; booted = true;
    state = await window.pywebview.api.get_state();
    soundEnabled = state.settings?.sound !== false;
    document.getElementById("sound-btn").innerHTML = soundEnabled ? ICON_ON : ICON_OFF;
    renderAll();
    pollTelemetry();
    setInterval(pollTelemetry, 1600);
  }
  window.addEventListener("pywebviewready", boot);
  if (window.pywebview && window.pywebview.api) boot();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    if "--overlay" in sys.argv:
        run_overlay_hud()
    else:
        import webview

        api = VenusTitaniumAPI(get_window)
        MAIN_WINDOW = webview.create_window(
            "venUs SILVER",
            html=HTML_UI,
            js_api=api,
            width=1280,
            height=800,
            min_size=(1060, 660),
            frameless=True,
            easy_drag=False,
            background_color="#000000",
        )
from pathlib import Path
ico = Path(__file__).parent / "venus.ico"
webview.start(icon=str(ico) if ico.exists() else None)