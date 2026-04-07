# gui/dashboard/tabs/phrases_tab.py
import flet as ft
import os
from gui.dashboard.tabs.base_tab import BaseTab
from gui.styles import AppColors
from gui.services.phrase_service import PhraseService
from core.database import db


class PhrasesTab(BaseTab):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.phrase_service = PhraseService()
        self.current_file = None
        self.current_category = None
        self.is_chat_commands_mode = False

        self.file_list = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
        self.category_button_text = ft.Text("Selecciona un archivo primero", color="white70")
        self.category_options_column = ft.Column(spacing=0)
        self.phrases_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

        self.category_menu = ft.ExpansionTile(
            title=self.category_button_text,
            subtitle=ft.Text("Categoría seleccionada", size=10, color="white50"),
            collapsed_bgcolor=ft.Colors.BLACK,
            bgcolor=ft.Colors.BLACK,
            maintain_state=True,
            controls=[
                ft.Container(
                    content=self.category_options_column,
                    padding=10,
                    bgcolor=ft.Colors.BLACK
                )
            ],
            shape=ft.RoundedRectangleBorder(radius=8),
        )

    def _create_phrase_card(self, text=""):
        txt_input = ft.TextField(
            value=text, text_size=13, color="white",
            bgcolor=ft.Colors.TRANSPARENT, border=ft.InputBorder.NONE,
            expand=True, multiline=True, min_lines=1, max_lines=10,
            cursor_color=AppColors.ACCENT, cursor_height=16,
            content_padding=ft.padding.only(top=0, bottom=10),
            selection_color=ft.Colors.with_opacity(0.3, AppColors.ACCENT),
        )
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color=AppColors.ACCENT, size=16),
                        margin=ft.margin.only(top=5),
                    ),
                    ft.Container(content=txt_input, expand=True, margin=ft.margin.only(top=-15)),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE, icon_color="white24", icon_size=18,
                            padding=0,
                            on_click=lambda e: self._delete_phrase_card(e.control.parent.parent.parent)
                        ),
                        margin=ft.margin.only(top=0),
                    )
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
            ),
            padding=ft.padding.only(top=8, bottom=5, left=20, right=15),
            bgcolor="#0d0d0d", border_radius=10,
            border=ft.border.all(1, "white05"),
            on_hover=self._on_card_hover,
        )

    def _on_card_hover(self, e):
        e.control.bgcolor = "#1a1a1a" if e.data == "true" else "#0d0d0d"
        e.control.border = ft.border.all(1, "white10") if e.data == "true" else ft.border.all(1, "white05")
        e.control.update()

    def _delete_phrase_card(self, card_control):
        self.phrases_list.controls.remove(card_control)
        self.page.update()

    def _add_phrase_card(self, e):
        if not self.current_category and not self.is_chat_commands_mode:
            return
        self.phrases_list.controls.insert(0, self._create_phrase_card(""))
        self.page.update()

    def build(self) -> ft.Tab:
        self._load_file_list()
        return ft.Tab(
            text="FRASES",
            icon=ft.Icons.TEXT_FIELDS,
            content=ft.Container(
                padding=20,
                bgcolor=ft.Colors.BLACK,
                content=ft.Row([
                    ft.Container(
                        width=280,
                        content=ft.Column([
                            ft.Row([
                                ft.Text("EXPLORADOR", size=12, weight="bold", color=AppColors.ACCENT),
                                ft.IconButton(ft.Icons.REFRESH, icon_size=16, on_click=lambda _: self._load_file_list())
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(
                                content=self.file_list, expand=True,
                                bgcolor=ft.Colors.BLACK,
                                border=ft.border.all(1, "white10"),
                                border_radius=10, padding=10
                            )
                        ], spacing=10, expand=True),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Column([
                            ft.Row([
                                ft.Text("EDITOR DE FRASES / COMANDOS", size=12, weight="bold", color=AppColors.ACCENT),
                                ft.TextButton("Añadir", icon=ft.Icons.ADD, on_click=self._add_phrase_card)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(
                                content=self.category_menu, width=450,
                                border=ft.border.all(1, "white10"), border_radius=8,
                                visible=not self.is_chat_commands_mode
                            ),
                            ft.Container(content=self.phrases_list, expand=True, padding=ft.padding.only(right=10)),
                            ft.Row([
                                ft.ElevatedButton(
                                    "GUARDAR CAMBIOS", icon=ft.Icons.SAVE_ROUNDED,
                                    on_click=self._save_phrases,
                                    bgcolor=AppColors.ACCENT, color="white", height=45,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ], spacing=15, expand=True)
                    )
                ], spacing=30, expand=True)
            )
        )

    def _load_file_list(self):
        self.file_list.controls.clear()

        self.file_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.BOLT, size=16, color=ft.Colors.AMBER_400),
                    ft.Text("COMANDOS DEL CHAT (!)", size=13, weight="bold", color=ft.Colors.AMBER_400)
                ], spacing=10),
                padding=ft.padding.symmetric(vertical=10, horizontal=12),
                border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.AMBER),
                on_click=self._select_chat_commands,
                ink=True
            )
        )
        self.file_list.controls.append(ft.Container(height=10))

        base_dir = os.path.abspath(os.getcwd())
        phrases_dir = os.path.join(base_dir, "phrases")
        if not os.path.exists(phrases_dir):
            return

        for folder in sorted(os.listdir(phrases_dir)):
            if folder == "__pycache__":
                continue
            folder_path = os.path.join(phrases_dir, folder)
            if os.path.isdir(folder_path):
                self.file_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(folder.upper(), size=10, weight="bold", color="white30"),
                            ft.Divider(height=1, color="white10")
                        ], spacing=5),
                        margin=ft.margin.only(top=15, bottom=5)
                    )
                )
                for file in os.listdir(folder_path):
                    if file.endswith(".py") and file != "__init__.py":
                        path = os.path.join(folder_path, file)
                        self.file_list.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.CODE_ROUNDED, size=16, color=ft.Colors.BLUE_GREY_400),
                                    ft.Text(file.replace(".py", ""), size=13, color="white70")
                                ], spacing=10),
                                padding=ft.padding.symmetric(vertical=8, horizontal=12),
                                border_radius=8,
                                on_click=lambda e, p=path: self._select_file(e, p),
                                data=path, ink=True,
                                on_hover=self._on_file_hover
                            )
                        )
        if self.page:
            self.page.update()

    def _select_chat_commands(self, e):
        self.is_chat_commands_mode = True
        self.current_file = None
        self.current_category = "Chat Commands"

        for ctrl in self.file_list.controls:
            if isinstance(ctrl, ft.Container):
                ctrl.bgcolor = None
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.AMBER)

        self.phrases_list.controls.clear()
        comandos = db.get_all_commands()
        for cmd in comandos:
            self.phrases_list.controls.append(
                self._create_phrase_card(f"{cmd['comando']}: {cmd['respuesta']}")
            )
        self.page.update()

    def _select_file(self, e, path):
        self.is_chat_commands_mode = False
        self.file_list.controls[0].bgcolor = None

        for ctrl in self.file_list.controls:
            if isinstance(ctrl, ft.Container) and ctrl.data:
                ctrl.bgcolor = None
                ctrl.content.controls[1].color = "white70"
        e.control.bgcolor = ft.Colors.with_opacity(0.1, AppColors.ACCENT)
        e.control.content.controls[1].color = AppColors.ACCENT
        self.current_file = path
        categories = self.phrase_service.get_categories(path)
        self._update_category_options(categories)
        if categories:
            self._select_category(categories[0])
        self.page.update()

    def _save_phrases(self, e):
        if not self.current_category:
            return

        updated_items = []
        for card in self.phrases_list.controls:
            try:
                txt_field = card.content.controls[1].content
                txt_val = txt_field.value.strip()
                if txt_val:
                    updated_items.append(txt_val)
            except:
                pass

        if self.is_chat_commands_mode:
            for item in updated_items:
                if ":" in item:
                    parts = item.split(":", 1)
                    comando = parts[0].strip().lower()
                    respuesta = parts[1].strip()
                    db.save_command(comando, respuesta)
            self._show_success_snack("Comandos del chat actualizados")
        else:
            if self.phrase_service.save_phrases(self.current_file, self.current_category, updated_items):
                self._show_success_snack("¡Archivo actualizado!")

    def _show_success_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=AppColors.ACCENT)
        self.page.snack_bar.open = True
        self.page.update()

    def _on_file_hover(self, e):
        if e.control.bgcolor != ft.Colors.with_opacity(0.1, AppColors.ACCENT):
            e.control.bgcolor = "white10" if e.data == "true" else None
            e.control.update()

    def _update_category_options(self, categories):
        self.category_options_column.controls.clear()
        for cat in categories:
            self.category_options_column.controls.append(
                ft.ListTile(
                    title=ft.Text(cat, size=13, color="white"),
                    on_click=lambda e, c=cat: self._select_category(c),
                    dense=True, hover_color="white10",
                    shape=ft.RoundedRectangleBorder(radius=6)
                )
            )
        if self.page:
            self.page.update()

    def _select_category(self, category_name):
        self.current_category = category_name
        self.category_button_text.value = category_name
        self.category_button_text.color = "white"
        self.category_menu.initially_expanded = False
        self._load_phrases()
        if self.page:
            self.page.update()

    def _load_phrases(self):
        if self.current_file and self.current_category:
            phrases = self.phrase_service.load_phrases(self.current_file, self.current_category)
            self.phrases_list.controls.clear()
            for p in phrases:
                if p:
                    self.phrases_list.controls.append(self._create_phrase_card(str(p).strip()))
            if self.page:
                self.page.update()