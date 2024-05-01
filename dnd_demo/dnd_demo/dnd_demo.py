import json
import uuid

import reflex as rx

from reflex_dnd import drag_drop_context, droppable, draggable, DropResult


class Item(rx.Base):
    key: str
    text: str


class State(rx.State):
    """The app state."""

    lists: list[str] = ["To Do", "Doing", "Done"]
    items: dict[str, list[Item]] = {}
    items_json: str = rx.LocalStorage()

    def _get_list_items(self, list_name: str) -> list[Item]:
        return self.items.setdefault(list_name, [])

    def load_items(self):
        if self.items_json:
            try:
                self.items = json.loads(self.items_json)
            except ValueError:
                pass

    def save_items(self):
        self.items_json = json.dumps(self.get_value(self.items))

    def on_drag_end(self, result: DropResult):
        result = DropResult(**result)
        if result.destination is not None:
            item = self.items[result.source.droppableId].pop(result.source.index)
            self._get_list_items(result.destination.droppableId).insert(
                result.destination.index, item
            )
            return State.save_items

    def add_item(self, form_data: dict[str, str]):
        self._get_list_items(form_data["list_name"]).append(
            Item(key=str(uuid.uuid4()), text=form_data["item"]),
        )
        return State.save_items

    def remove_item(self, key: str):
        for list_name, items in self.items.items():
            for item in items:
                if item.key == key:
                    self.items[list_name].remove(item)
                    return State.save_items


def item_view(item: Item, index: int) -> rx.Component:
    return draggable(
        rx.card(
            rx.hstack(
                item.text,
                rx.spacer(),
                rx.icon_button(
                    rx.icon("trash", size=16),
                    on_click=State.remove_item(item.key),
                    variant="ghost",
                    color_scheme="gray",
                ),
                align="center",
            ),
            width="100%",
        ),
        draggable_id=f"draggable-{item.key}",
        index=index,
        key=item.key,
        width="100%",
    )


def drop_list(name: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(name),
            rx.spacer(),
            rx.cond(
                State.items[name],
                State.items[name].length(),
                "0",
            ),
            width="100%",
            align="center",
        ),
        rx.divider(),
        droppable(
            rx.vstack(
                rx.cond(
                    State.items[name],
                    rx.foreach(
                        State.items[name],
                        item_view,
                    ),
                ),
            ),
            droppable_id=name,
            height="50vh",
            width="100%",
            overflow_y="auto",
        ),
        rx.divider(),
        rx.form(
            rx.hstack(
                rx.input(placeholder="Add New Item", name="item", width="100%"),
                rx.icon_button(rx.icon("plus")),
                width="100%",
            ),
            rx.el.input(type="hidden", name="list_name", value=name),
            reset_on_submit=True,
            on_submit=State.add_item,
            width="100%",
        ),
        min_width="250px",
        width="25vw",
        border_radius="8px",
        border=f"1px solid {rx.color('gray', 5)}",
        padding="15px",
    )


def index() -> rx.Component:
    return rx.vstack(
        rx.heading("Reflex Kanban", size="8"),
        drag_drop_context(
            rx.hstack(
                rx.foreach(State.lists, drop_list),
            ),
            on_drag_end=State.on_drag_end,
        ),
        rx.logo(),
        padding_top="2em",
        align_items=["start", "start", "center"],
        padding_x="10px",
        height="100vh",
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index, on_load=State.load_items)
