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
                items_dict = json.loads(self.items_json)
                self.items = {
                    # Turn them into actual Item objects
                    list_name: [Item(**item) for item in items]
                    for list_name, items in items_dict.items()
                }
                return rx._x.toast.info("Locked and loaded from LocalStorage!")
            except ValueError:
                pass

    def save_items(self):
        self.items_json = json.dumps(self.get_value(self.items))

    def on_close(self, dismissed, toast):
        if dismissed:
            print(f"dismiss: {toast}")
        else:
            print(f"auto close: {toast}")

    def on_drag_end(self, result: DropResult):
        result = DropResult(**result)
        if result.destination is not None:
            try:
                item = self.items[result.source.droppableId].pop(result.source.index)
            except IndexError:
                return rx._x.toast.error("Invalid source index moving item")
            self._get_list_items(result.destination.droppableId).insert(
                result.destination.index, item
            )
            if result.source.droppableId != result.destination.droppableId:
                yield rx._x.toast.success(
                    f"Moved {item.text} to {result.destination.droppableId}",
                    action={
                        "label": "Undo",
                        "on_click": State.on_drag_end(
                            result.copy(
                                update=dict(source=result.destination, destination=result.source),
                            ),
                        ),
                    },
                    on_auto_close=State.on_close(False),
                    on_dismiss=State.on_close(True),
                )
            return State.save_items

    def add_item(self, form_data: dict[str, str]):
        item = Item(key=str(uuid.uuid4()), text=form_data["item"])
        self._get_list_items(form_data["list_name"]).append(item)
        yield rx._x.toast.success(
            f"Created {form_data['item']} in {form_data['list_name']}",
            action={
                "label": "Undo",
                "on_click": State.remove_item(item.key),
            },
            on_auto_close=State.on_close(False),
            on_dismiss=State.on_close(True),
        )
        return State.save_items

    def remove_item(self, key: str):
        for list_name, items in self.items.items():
            for item in items:
                if item.key == key:
                    self.items[list_name].remove(item)
                    yield rx._x.toast.warning(
                        f"Removed {item.text} from {list_name}",
                        action={
                            "label": "Undo",
                            "on_click": State.add_item(
                                {
                                    "list_name": list_name,
                                    "item": item.text,
                                }
                            )
                        },
                        on_auto_close=State.on_close(False),
                        on_dismiss=State.on_close(True),
                    )
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
        rx.color_mode.button(position="top-right"),
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
    ), rx._x.toast.provider(close_button=True)


# Add state and page to the app.
app = rx.App()
app.add_page(index, on_load=State.load_items)
