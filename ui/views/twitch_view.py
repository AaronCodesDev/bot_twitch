# ui/views/twitch_view.py
# Vista Twitch Bot — FanTan Hub

import flet as ft
import sqlite3
import os
import sys
import threading
import asyncio
import datetime
from ui.colors import *
from ui.components import *


BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TWITCH_DB = os.path.join(BASE, "bot_twitch", "data", "database.db")
BOT_BASE  = os.path.join(BASE, "bot_twitch")


def _q(query: str, default=None):
    try:
        if not os.path.exists(TWITCH_DB):
            return default
        conn = sqlite3.connect(TWITCH_DB)
        conn.row_factory = sqlite3.Row
        r = conn.cursor().execute(query).fetchone()
        conn.close()
        return r[0] if r and r[0] is not None else default
    except Exception:
        return default


def _qa(query: str):
    try:
        if not os.path.exists(TWITCH_DB):
            return []
        conn = sqlite3.connect(TWITCH_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.cursor().execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


class TwitchView:
    def __init__(self, state: dict, page: ft.Page):
        self.state = state
        self.page = page
        self._log_list = ft.ListView(
            expand=True, spacing=3, auto_scroll=True,
            padding=ft.padding.all(8),
        )
        self._chat_list = ft.ListView(
            expand=True, spacing=3, auto_scroll=True,
            padding=ft.padding.all(8),
        )
        self._tabs_ref = ft.Ref[ft.Tabs]()

    # ─── Datos ────────────────────────────────────────────────────────────────
    def _get_stats(self):
        total_subs    = _q("SELECT COUNT(*) FROM subscribers", 0)
        tier3_subs    = _q("SELECT COUNT(*) FROM subscribers WHERE tier=3", 0)
        tier2_subs    = _q("SELECT COUNT(*) FROM subscribers WHERE tier=2", 0)
        tier1_subs    = _q("SELECT COUNT(*) FROM subscribers WHERE tier=1", 0)
        total_users   = _q("SELECT COUNT(*) FROM users", 0)
        total_cmds    = _q("SELECT COUNT(*) FROM custom_commands", 0)
        return {
            "total": total_subs or 0,
            "tier3": tier3_subs or 0,
            "tier2": tier2_subs or 0,
            "tier1": tier1_subs or 0,
            "users": total_users or 0,
            "cmds": total_cmds or 0,
        }

# ─── Build ────────────────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        stats      = self._get_stats()
        is_running = self.state.get("bot_running", False)

        # Definición del nuevo componente de estadística (estilo Dashboard)
        def _cs(icon, label, value, accent):
            return ft.Container(
                content=ft.Row([
                    ft.Text(icon, size=14),
                    ft.Column([
                        ft.Text(value, size=14, weight=ft.FontWeight.W_800, color=TEXT),
                        ft.Text(label, size=9, color=MUTED),
                    ], spacing=0, expand=True),
                ], spacing=7),
                bgcolor=with_alpha(accent, 0.06), 
                border_radius=9,
                border=ft.border.only(left=ft.BorderSide(2, accent)), 
                padding=ft.padding.symmetric(horizontal=11, vertical=7),
                expand=True,
            )

        # Re-construimos el HERO para que use el stats_row que creaste
        hero = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Dashboard Twitch", size=18, weight="bold", color=TEXT),
                    self._build_bot_toggle(is_running),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Row([
                    _cs("👥", "Total Subs", str(stats["total"]), PURPLE),
                    _cs("💜", "Tier 3",     str(stats["tier3"]), PURPLE),
                    _cs("💙", "Tier 2",     str(stats["tier2"]), INFO),
                    _cs("💚", "Tier 1",     str(stats["tier1"]), GREEN),
                ], spacing=8, expand=True),
            ]),
            padding=20,
            bgcolor=SURFACE,
            border_radius=16,
            border=ft.border.all(1, BORDER2)
        )

        # ─── Tabs ─────────────────────────────────────────────────────────────
        tabs = ft.Tabs(
            ref=self._tabs_ref,
            selected_index=0,
            animation_duration=250,
            tab_alignment=ft.TabAlignment.START,
            indicator_color=PURPLE,
            label_color=PURPLE,
            unselected_label_color=MUTED,
            tabs=[
                ft.Tab(text="Monitor", icon=ft.Icons.MONITOR_HEART_OUTLINED,
                       content=self._build_monitor_tab()),
                ft.Tab(text="Suscriptores", icon=ft.Icons.PEOPLE_OUTLINED,
                       content=self._build_subs_tab(stats)),
                ft.Tab(text="Comandos", icon=ft.Icons.TERMINAL_OUTLINED,
                       content=self._build_commands_tab()),
                ft.Tab(text="Usuarios", icon=ft.Icons.MANAGE_ACCOUNTS_OUTLINED,
                       content=self._build_users_tab()),
            ],
            expand=True,
        )

        return ft.Column([
            hero,
            ft.Container(height=10),
            ft.Container(content=tabs, expand=True),
        ], spacing=0, expand=True)

        return ft.Column([
            hero,
            ft.Container(height=10),
            ft.Container(content=tabs, expand=True),
        ], spacing=0, expand=True)

    # ─── Bot toggle ───────────────────────────────────────────────────────────
    def _build_bot_toggle(self, is_running: bool) -> ft.Control:
        label_ref = ft.Ref[ft.Text]()
        dot_ref   = ft.Ref[ft.Container]()

        def toggle(e):
            running = self.state.get("bot_running", False)
            if running:
                self._stop_bot()
                label_ref.current.value = "Bot Offline"
                dot_ref.current.bgcolor = DANGER
                self.state["bot_running"] = False
                self._add_log("Bot detenido", "warning")
            else:
                self._start_bot()
                label_ref.current.value = "Bot Online"
                dot_ref.current.bgcolor = SUCCESS
                self.state["bot_running"] = True
                self._add_log("Bot iniciado", "success")
            e.control.bgcolor = DANGER if self.state.get("bot_running") else SUCCESS
            self.page.update()

        btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Container(
                    ref=dot_ref,
                    width=8, height=8,
                    bgcolor=SUCCESS if is_running else DANGER,
                    border_radius=4,
                ),
                ft.Text(
                    ref=label_ref,
                    value="Bot Online" if is_running else "Bot Offline",
                    size=12, color="white", weight=ft.FontWeight.W_600,
                ),
            ], spacing=8, tight=True),
            bgcolor=DANGER if is_running else SUCCESS,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=0,
            ),
            on_click=toggle,
        )
        return btn

    # ─── Monitor tab ──────────────────────────────────────────────────────────
    def _build_monitor_tab(self) -> ft.Container:
        self._add_log("Sistema listo — esperando actividad", "info")

        def _panel(title, accent, list_ctrl, on_clear):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(title, size=11, color=accent,
                                            weight=ft.FontWeight.W_600),
                            border=ft.border.only(left=ft.BorderSide(2, accent)),
                            padding=ft.padding.only(left=8),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                            icon_color=MUTED, icon_size=16,
                            tooltip="Limpiar",
                            on_click=on_clear,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(
                        content=list_ctrl,
                        bgcolor=BG,
                        border_radius=10,
                        border=ft.border.all(1, BORDER2),
                        expand=True,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                ], spacing=6, expand=True),
                expand=True,
            )

        def clear_console(e):
            self._log_list.controls.clear()
            self.page.update()

        def clear_chat(e):
            self._chat_list.controls.clear()
            self.page.update()

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                ft.Row([
                    _panel("🖥️  Consola", CYAN,   self._log_list,  clear_console),
                    ft.Container(width=10),
                    _panel("💬  Chat Twitch", PURPLE, self._chat_list, clear_chat),
                ], spacing=0, expand=True),
            ], spacing=0, expand=True),
            padding=ft.padding.only(top=4),
            expand=True,
        )

    # ─── Subs tab ─────────────────────────────────────────────────────────────
    def _build_subs_tab(self, stats: dict) -> ft.Container:
        subs = _qa("SELECT username, tier, meses, fecha FROM subscribers ORDER BY tier DESC, meses DESC LIMIT 50")

        tier_colors = {3: PURPLE, 2: INFO, 1: GREEN}
        tier_labels = {3: "T3 👑", 2: "T2 ⭐", 1: "T1"}

        rows = []
        for s in subs:
            tier = s.get("tier", 1)
            fecha = s.get("fecha", "")[:10] if s.get("fecha") else "---"
            rows.append([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(tier_labels.get(tier, "T1"), size=10,
                                            color=tier_colors.get(tier, GREEN),
                                            weight=ft.FontWeight.W_700),
                            bgcolor=with_alpha(tier_colors.get(tier, GREEN), 0.12),
                            border_radius=6,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        ),
                    ]),
                    expand=True,
                ),
                s.get("username", ""),
                f"{s.get('meses', 0)} meses",
                fecha,
            ])

        # Tier distribution bar
        total = max(stats["total"], 1)
        dist_bar = ft.Column([
            ft.Text("Distribución de tiers", size=11, color=MUTED, weight=ft.FontWeight.W_500),
            ft.Container(height=6),
            ft.Row([
                ft.Container(
                    width=(stats["tier3"] / total) * 300,
                    height=8,
                    bgcolor=PURPLE,
                    border_radius=ft.border_radius.only(top_left=4, bottom_left=4),
                ),
                ft.Container(
                    width=(stats["tier2"] / total) * 300,
                    height=8,
                    bgcolor=INFO,
                ),
                ft.Container(
                    width=(stats["tier1"] / total) * 300,
                    height=8,
                    bgcolor=GREEN,
                    border_radius=ft.border_radius.only(top_right=4, bottom_right=4),
                ),
            ], spacing=2),
            ft.Row([
                ft.Row([ft.Container(width=8, height=8, bgcolor=PURPLE, border_radius=4),
                        ft.Text(f"T3: {stats['tier3']}", size=10, color=MUTED)], spacing=4),
                ft.Row([ft.Container(width=8, height=8, bgcolor=INFO, border_radius=4),
                        ft.Text(f"T2: {stats['tier2']}", size=10, color=MUTED)], spacing=4),
                ft.Row([ft.Container(width=8, height=8, bgcolor=GREEN, border_radius=4),
                        ft.Text(f"T1: {stats['tier1']}", size=10, color=MUTED)], spacing=4),
            ], spacing=16),
        ], spacing=4)

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                ft.Container(
                    content=dist_bar,
                    bgcolor=SURFACE2,
                    border_radius=12,
                    padding=16,
                    border=ft.border.all(1, BORDER),
                ),
                ft.Container(height=12),
                section_title(f"Suscriptores ({len(subs)})", accent=PURPLE),
                ft.Container(height=8),
                ft.Container(
                    content=simple_table(
                        ["Tier", "Usuario", "Meses", "Fecha"],
                        rows if rows else [["—", "Sin subs", "—", "—"]],
                        accent=PURPLE,
                    ),
                    expand=True,
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    # ─── Commands tab ─────────────────────────────────────────────────────────
    def _build_commands_tab(self) -> ft.Container:
        import ast as _ast

        PHRASES_BASE = os.path.join(BOT_BASE, "phrases")

        # ── Helpers: leer / escribir frases de archivos .py ───────────────────
        def get_list_vars(filepath):
            """Devuelve lista de (var_name, [values]) para todas las listas del archivo."""
            try:
                with open(filepath, encoding="utf-8") as f:
                    src = f.read()
                tree = _ast.parse(src)
                result = []
                for node in tree.body:
                    if isinstance(node, _ast.Assign):
                        for t in node.targets:
                            if isinstance(t, _ast.Name) and isinstance(node.value, _ast.List):
                                values = []
                                for el in node.value.elts:
                                    try:
                                        v = _ast.literal_eval(el)
                                        if isinstance(v, str):
                                            values.append(v)
                                    except Exception:
                                        pass
                                if values:
                                    result.append((t.id, values))
                return result
            except Exception:
                return []

        def read_phrases(rel_path, var_name):
            full = os.path.join(PHRASES_BASE, rel_path)
            for vn, vals in get_list_vars(full):
                if vn == var_name:
                    return vals
            return []

        def save_phrases(rel_path, var_name, phrases):
            full = os.path.join(PHRASES_BASE, rel_path)
            try:
                # Preserve other variables in the file
                try:
                    with open(full, encoding="utf-8") as f:
                        src = f.read()
                    tree = _ast.parse(src)
                    # Replace only the target variable
                    new_lines = src.splitlines(keepends=True)
                    for node in tree.body:
                        if isinstance(node, _ast.Assign):
                            for t in node.targets:
                                if isinstance(t, _ast.Name) and t.id == var_name:
                                    start = node.lineno - 1
                                    end   = node.end_lineno
                                    replacement = [f"{var_name} = [\n"]
                                    for p in phrases:
                                        safe = p.replace("\\", "\\\\").replace('"', '\\"')
                                        replacement.append(f'    "{safe}",\n')
                                    replacement.append("]\n")
                                    new_lines[start:end] = replacement
                    with open(full, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    return True
                except Exception:
                    # Fallback: rewrite whole file
                    lines = [f"{var_name} = [\n"]
                    for p in phrases:
                        safe = p.replace("\\", "\\\\").replace('"', '\\"')
                        lines.append(f'    "{safe}",\n')
                    lines.append("]\n")
                    with open(full, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    return True
            except Exception:
                return False

        def save_chat_command(comando, respuesta):
            try:
                conn = sqlite3.connect(TWITCH_DB)
                conn.execute(
                    "INSERT OR REPLACE INTO custom_commands (comando, respuesta, creado_by) "
                    "VALUES (?, ?, ?)",
                    (comando.lower().lstrip("!"), respuesta, "dashboard")
                )
                conn.commit()
                conn.close()
                return True
            except Exception:
                return False

        # ── Escaneo dinámico de TODOS los archivos de frases ──────────────────
        def scan_structure():
            """Devuelve {SECTION: [(basename, rel_path, [var_name, ...]), ...]}"""
            result = {}
            if not os.path.exists(PHRASES_BASE):
                return result
            for folder in sorted(os.listdir(PHRASES_BASE)):
                if folder in ("__pycache__", "__init__.py"):
                    continue
                folder_path = os.path.join(PHRASES_BASE, folder)
                if not os.path.isdir(folder_path):
                    continue
                entries = []
                for filename in sorted(os.listdir(folder_path)):
                    if not filename.endswith(".py") or filename in ("__init__.py",):
                        continue
                    rel  = f"{folder}/{filename}"
                    full = os.path.join(folder_path, filename)
                    var_names = [vn for vn, _ in get_list_vars(full)]
                    if not var_names:
                        continue
                    entries.append((filename.replace(".py", ""), rel, var_names))
                if entries:
                    result[folder.upper()] = entries
            return result

        STRUCTURE = scan_structure()

        # ── Estado mutable ────────────────────────────────────────────────────
        _first_section = next(iter(STRUCTURE)) if STRUCTURE else None
        _first_file    = STRUCTURE[_first_section][0] if _first_section else None
        _first_var     = _first_file[2][0] if _first_file else ""

        sel = {
            "section": _first_section or "",
            "name":    _first_file[0] if _first_file else "",
            "path":    _first_file[1] if _first_file else "",
            "var":     _first_var,
            "mode":    "file",
        }
        sidebar_refs   = {}    # key=(rel_path, var_name) → Container
        chat_cmd_item  = None
        expanded_files = {}    # key=(section, basename) → bool

        # ── Widgets del editor ────────────────────────────────────────────────
        phrase_col = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        cat_label  = ft.Text(sel["var"], size=13, color=TEXT, weight=ft.FontWeight.W_500)
        cat_sub    = ft.Text("Categoría seleccionada", size=10, color=MUTED)
        cat_box_ref = ft.Ref[ft.Container]()
        status_txt = ft.Text("", size=11, color=MUTED)

        def _get_tf_value(row):
            """Extrae el valor del TextField de una fila de frase."""
            try:
                return row.controls[1].value or ""
            except Exception:
                return ""

        def make_phrase_card(text: str = "") -> ft.Container:
            tf = ft.TextField(
                value=text,
                border=ft.InputBorder.NONE,
                bgcolor=ft.colors.TRANSPARENT,
                text_size=13,
                color=TEXT,
                expand=True,
                multiline=True,
                min_lines=1,
                max_lines=5,
                cursor_color=PURPLE,
                content_padding=ft.padding.only(top=0, bottom=6),
                selection_color=with_alpha(PURPLE, 0.25),
            )
            row = ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
            card = ft.Container(
                padding=ft.padding.only(top=8, bottom=5, left=16, right=10),
                bgcolor=SURFACE2,
                border_radius=10,
                border=ft.border.all(1, BORDER),
            )

            def on_delete(e):
                phrase_col.controls.remove(card)
                self.page.update()

            def on_hover(e):
                card.bgcolor   = SURFACE3 if e.data == "true" else SURFACE2
                card.border    = ft.border.all(1, BORDER2 if e.data == "true" else BORDER)
                card.update()

            row.controls = [
                ft.Container(
                    content=ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color=PURPLE, size=15),
                    margin=ft.margin.only(top=4),
                ),
                ft.Container(content=tf, expand=True, margin=ft.margin.only(top=-14)),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=MUTED2,
                    icon_size=17,
                    tooltip="Eliminar",
                    padding=ft.padding.all(0),
                    on_click=on_delete,
                    style=ft.ButtonStyle(
                        overlay_color=with_alpha(DANGER, 0.10),
                        shape=ft.RoundedRectangleBorder(radius=6),
                    ),
                ),
            ]
            card.content  = row
            card.on_hover = on_hover
            return card

        def load_file_phrases(rel_path, var_name):
            phrase_col.controls.clear()
            for p in read_phrases(rel_path, var_name):
                phrase_col.controls.append(make_phrase_card(p))
            try:
                self.page.update()
            except Exception:
                pass

        def load_chat_commands():
            phrase_col.controls.clear()
            cmds = _qa("SELECT comando, respuesta FROM custom_commands ORDER BY comando")
            for c in cmds:
                phrase_col.controls.append(
                    make_phrase_card(f"!{c.get('comando','')}: {c.get('respuesta','')}")
                )
            try:
                self.page.update()
            except Exception:
                pass

        def on_add(e):
            phrase_col.controls.insert(0, make_phrase_card(""))
            self.page.update()

        def on_save(e):
            texts = []
            for card in phrase_col.controls:
                try:
                    v = card.content.controls[1].content.value.strip()
                    if v:
                        texts.append(v)
                except Exception:
                    pass

            if sel["mode"] == "commands":
                ok = True
                for item in texts:
                    if ":" in item:
                        parts = item.split(":", 1)
                        ok = ok and save_chat_command(parts[0].strip(), parts[1].strip())
                status_txt.value = "✓ Comandos guardados" if ok else "✗ Error"
            else:
                ok = save_phrases(sel["path"], sel["var"], texts)
                status_txt.value = "✓ Guardado" if ok else "✗ Error al guardar"

            status_txt.color = SUCCESS if ok else DANGER
            self.page.update()

        def _deselect_all():
            for ref in sidebar_refs.values():
                ref.bgcolor = "transparent"
            nonlocal chat_cmd_item
            if chat_cmd_item:
                chat_cmd_item.bgcolor = with_alpha(WARNING, 0.05)

        def on_select_file(section, name, rel_path, var_name):
            _deselect_all()
            ref = sidebar_refs.get((rel_path, var_name))
            if ref:
                ref.bgcolor = with_alpha(PURPLE, 0.12)
            sel.update({"section": section, "name": name,
                        "path": rel_path, "var": var_name, "mode": "file"})
            cat_label.value  = var_name
            cat_sub.value    = "Categoría seleccionada"
            status_txt.value = ""
            load_file_phrases(rel_path, var_name)

        def on_select_chat_commands(e):
            _deselect_all()
            if chat_cmd_item:
                chat_cmd_item.bgcolor = with_alpha(WARNING, 0.15)
            sel["mode"] = "commands"
            cat_label.value = "custom_commands"
            cat_sub.value   = "Base de datos · !addcomando"
            status_txt.value = ""
            load_chat_commands()

        # ── Sidebar ────────────────────────────────────────────────────────────
        chat_entry = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT, color=WARNING, size=13),
                ft.Text("COMANDOS DEL CHAT (!)", size=11,
                        color=WARNING, weight=ft.FontWeight.W_700),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=6,
            bgcolor=with_alpha(WARNING, 0.05),
            on_click=on_select_chat_commands,
        )
        chat_cmd_item = chat_entry

        sidebar_items = [
            ft.Container(height=8),
            chat_entry,
            ft.Container(height=6),
            ft.Divider(height=1, color=BORDER2),
        ]

        for section, files in STRUCTURE.items():
            sidebar_items.append(ft.Container(
                content=ft.Text(section, size=9, color=MUTED, weight=ft.FontWeight.W_700),
                padding=ft.padding.only(left=10, top=10, bottom=2),
            ))
            for basename, rel_path, var_names in files:
                if len(var_names) == 1:
                    # ── Un solo grupo: item plano ───────────────────────────
                    vn     = var_names[0]
                    is_sel = (sel["path"] == rel_path and sel["var"] == vn)
                    item   = ft.Container(
                        content=ft.Row([
                            ft.Text("<>", size=9, color=PURPLE, opacity=0.7),
                            ft.Text(basename, size=12, color=TEXT,
                                    overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=8),
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        border_radius=6,
                        bgcolor=with_alpha(PURPLE, 0.12) if is_sel else "transparent",
                        on_click=lambda e, s=section, n=basename, p=rel_path, v=vn:
                            on_select_file(s, n, p, v),
                    )
                    sidebar_refs[(rel_path, vn)] = item
                    sidebar_items.append(item)
                else:
                    # ── Varias listas: parent colapsable + hijos ────────────
                    expanded_files[(section, basename)] = False
                    arrow_txt    = ft.Text("▶", size=9, color=MUTED2)
                    children_col = ft.Column(spacing=0, visible=False)

                    child_list = []
                    for vn in var_names:
                        is_sel = (sel["path"] == rel_path and sel["var"] == vn)
                        child  = ft.Container(
                            content=ft.Row([
                                ft.Container(width=14),
                                ft.Text("·", size=13, color=PURPLE_L),
                                ft.Text(vn, size=11, color=TEXT,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                            ], spacing=5),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border_radius=6,
                            bgcolor=with_alpha(PURPLE, 0.12) if is_sel else "transparent",
                            on_click=lambda e, s=section, n=basename, p=rel_path, v=vn:
                                on_select_file(s, n, p, v),
                        )
                        sidebar_refs[(rel_path, vn)] = child
                        child_list.append(child)
                    children_col.controls = child_list

                    def toggle_expand(e,
                                      at=arrow_txt, cc=children_col,
                                      key=(section, basename)):
                        is_exp = not expanded_files.get(key, False)
                        expanded_files[key] = is_exp
                        cc.visible = is_exp
                        at.value   = "▼" if is_exp else "▶"
                        at.color   = TEXT if is_exp else MUTED2
                        self.page.update()

                    parent = ft.Container(
                        content=ft.Row([
                            arrow_txt,
                            ft.Text("<>", size=9, color=PURPLE, opacity=0.7),
                            ft.Text(basename, size=12, color=TEXT,
                                    overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ], spacing=6),
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        border_radius=6,
                        bgcolor="transparent",
                        on_click=toggle_expand,
                    )
                    sidebar_items.append(parent)
                    sidebar_items.append(children_col)

        sidebar_items.append(ft.Container(height=8))

        sidebar = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row([
                            ft.Text("EXPLORADOR", size=10, color=PURPLE,
                                    weight=ft.FontWeight.W_700),
                        ]),
                        padding=ft.padding.only(left=10, top=8, bottom=4),
                    ),
                    ft.Divider(height=1, color=BORDER2),
                    ft.Container(
                        content=ft.Column(sidebar_items, spacing=0),
                        padding=ft.padding.symmetric(horizontal=4),
                        expand=True,
                    ),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            bgcolor=SURFACE,
            border=ft.border.all(1, BORDER2),
            border_radius=12,
            width=200,
        )

        # ── Editor panel ───────────────────────────────────────────────────────
        editor_panel = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text("EDITOR DE FRASES / COMANDOS", size=10,
                            color=MUTED, weight=ft.FontWeight.W_600),
                    ft.Row([], expand=True),
                    ft.TextButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ADD, size=14, color=PURPLE),
                            ft.Text("Añadir", size=12, color=PURPLE,
                                    weight=ft.FontWeight.W_500),
                        ], spacing=4, tight=True),
                        on_click=on_add,
                        style=ft.ButtonStyle(
                            overlay_color=with_alpha(PURPLE, 0.08),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                # Category pill
                ft.Container(
                    ref=cat_box_ref,
                    content=ft.Row([
                        ft.Column([cat_label, cat_sub], spacing=1, expand=True),
                        ft.Icon(ft.Icons.UNFOLD_MORE_OUTLINED, color=MUTED2, size=16),
                    ]),
                    bgcolor=SURFACE2,
                    border=ft.border.all(1, BORDER2),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                ),
                ft.Container(height=8),
                # Phrase list
                ft.Container(content=phrase_col, expand=True),
                ft.Container(height=6),
                # Footer
                ft.Row([
                    status_txt,
                    ft.Row([], expand=True),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SAVE_ROUNDED, size=14, color="white"),
                            ft.Text("GUARDAR CAMBIOS", size=11, color="white",
                                    weight=ft.FontWeight.W_600),
                        ], spacing=6, tight=True),
                        bgcolor=PURPLE,
                        on_click=on_save,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            elevation=0,
                            overlay_color=with_alpha("#ffffff", 0.1),
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=0, expand=True),
            expand=True,
            padding=ft.padding.only(left=14, top=2),
        )

        # Carga inicial
        if _first_file and _first_var:
            load_file_phrases(_first_file[1], _first_var)

        return ft.Container(
            content=ft.Column([
                ft.Container(height=10),
                ft.Row([
                    sidebar,
                    editor_panel,
                ], spacing=0, expand=True,
                   vertical_alignment=ft.CrossAxisAlignment.START),
            ], spacing=0, expand=True),
            expand=True,
        )

    # ─── Users tab ────────────────────────────────────────────────────────────
    def _build_users_tab(self) -> ft.Container:
        users = _qa("SELECT username, full_name, tier, ref_code FROM users ORDER BY tier DESC LIMIT 50")

        tier_labels = {3: "🔴 Admin", 2: "🟡 Mod", 1: "⚪ User"}
        tier_colors = {3: DANGER, 2: WARNING, 1: MUTED}

        rows = []
        for u in users:
            tier = u.get("tier", 1)
            rows.append([
                u.get("username", ""),
                u.get("full_name", "—") or "—",
                ft.Container(
                    content=ft.Text(tier_labels.get(tier, "User"), size=10,
                                    color=tier_colors.get(tier, MUTED)),
                    bgcolor=with_alpha(tier_colors.get(tier, MUTED), 0.08),
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    expand=True,
                ),
                u.get("ref_code", "—") or "—",
            ])

        return ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                section_title(f"Usuarios registrados ({len(users)})", accent=PURPLE),
                ft.Container(height=8),
                ft.Container(
                    content=simple_table(
                        ["Usuario", "Nombre", "Rol", "Código ref."],
                        rows if rows else [["—", "Sin usuarios", "—", "—"]],
                        accent=PURPLE,
                    ),
                    expand=True,
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    # ─── Bot control ──────────────────────────────────────────────────────────
    def _start_bot(self):
        import subprocess
        bot_script = os.path.join(BOT_BASE, "app.py")

        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            proc = subprocess.Popen(
                [sys.executable, "-u", bot_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=BOT_BASE,
                env=env,
                encoding="utf-8",
            )
            self.state["_bot_process"] = proc
            self._add_log("🚀 Conectando a Twitch...", "info")

            def read_output():
                for line in iter(proc.stdout.readline, ""):
                    line = line.strip()
                    if not line:
                        continue
                    is_chat = any(x in line for x in ["[CHAT]", "[COMANDO]", "-> @"])
                    if is_chat:
                        self._add_chat(line)
                    else:
                        level = "error" if any(x in line.lower() for x in ["error", "traceback", "exception"]) else "info"
                        self._add_log(line, level)

            t = threading.Thread(target=read_output, daemon=True)
            t.start()
            self.state["_bot_thread"] = t

        except Exception as ex:
            self._add_log(f"❌ Error al iniciar el bot: {ex}", "error")

    def _stop_bot(self):
        try:
            proc = self.state.get("_bot_process")
            if proc:
                proc.terminate()
                self.state["_bot_process"] = None
        except Exception:
            pass

    def _add_log(self, message: str, level: str = "info"):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_list.controls.append(log_item(now, message, level))
        try:
            self.page.update()
        except Exception:
            pass

    def _add_chat(self, raw_line: str):
        """Renderiza una línea de chat coloreando comandos y @menciones."""
        now = datetime.datetime.now().strftime("%H:%M:%S")

        # Detectar tipo y parsear formato
        # [CHAT] @user: mensaje
        # [COMANDO] @user usó: !comando
        is_command = "[COMANDO]" in raw_line
        line = raw_line.replace("[CHAT]", "").replace("[COMANDO]", "").strip()

        if ":" in line:
            username, _, message = line.partition(":")
            username = username.replace("usó", "").strip().lstrip("@")
            message  = message.strip()
        else:
            username = ""
            message  = line
        has_mention = "@" in message

        # Color del mensaje
        if is_command:
            msg_color  = WARNING
            msg_weight = ft.FontWeight.W_600
        elif has_mention:
            msg_color  = CYAN
            msg_weight = ft.FontWeight.W_500
        else:
            msg_color  = TEXT
            msg_weight = ft.FontWeight.W_400

        item = ft.Container(
            content=ft.Row([
                ft.Text(f"[{now}]", size=10, color=MUTED, width=55),
                ft.Text(
                    f"{username}:" if username else "",
                    size=11, color=PURPLE,
                    weight=ft.FontWeight.W_700,
                    width=90 if username else 0,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    message, size=11,
                    color=msg_color,
                    weight=msg_weight,
                    expand=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ], spacing=6),
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=6,
            bgcolor=with_alpha(WARNING, 0.04) if is_command else (
                with_alpha(CYAN, 0.04) if has_mention else None
            ),
        )

        self._chat_list.controls.append(item)
        try:
            self.page.update()
        except Exception:
            pass
