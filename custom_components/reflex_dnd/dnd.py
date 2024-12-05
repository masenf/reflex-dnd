"""Reflex wrapper for @hello-pangea/dnd"""
from typing import Optional

import reflex as rx


class DraggableLocation(rx.Base):
    droppableId: str
    index: int


class DraggableRubric(rx.Base):
    draggableId: str
    type: str
    source: DraggableLocation


class DragStart(DraggableRubric):
    mode: str


def _on_drag_start_signature(start: DragStart) -> list[DragStart]:
    return [start]


class Combine(rx.Base):
    draggableId: str
    droppableId: str


class DragUpdate(DragStart):
    destination: Optional[DraggableLocation]
    combine: Optional[Combine]


def _on_drag_update_signature(update: DragUpdate) -> list[DragUpdate]:
    return [update]


class DropResult(DragUpdate):
    reason: str


def _on_drag_end(result: DropResult) -> list[DropResult]:
    return [result]


class DndBase(rx.Component):
    """Dnd component."""

    # The React library to wrap.
    library = "@hello-pangea/dnd"


class DragDropContext(DndBase):

    # The React component tag.
    tag = "DragDropContext"

    # Optional: called before an item is picked up.
    on_before_capture: rx.EventHandler[lambda draggable_id, mode: [draggable_id, mode]]
    on_before_drag_start: rx.EventHandler[_on_drag_start_signature]

    # Optional: called when an item is first picked up.
    on_drag_start: rx.EventHandler[_on_drag_start_signature]

    # Optional: called when an item is dragged over a new potential target.
    on_drag_update: rx.EventHandler[_on_drag_update_signature]

    # Required: called when an item has been dropped.
    on_drag_end: rx.EventHandler[_on_drag_end]


class Droppable(DndBase):
    tag = "Droppable"

    droppable_id: rx.Var[str]
    mode: rx.Var[str]
    type: rx.Var[str]
    is_drop_disabled: rx.Var[bool]
    is_combine_enabled: rx.Var[bool]
    direction: rx.Var[str]
    ignore_container_clipping: rx.Var[bool]

    def _render(self):
        rtag = super()._render()
        passed_css = rtag.props.pop("css", None)
        if passed_css is not None:
            css = f"css={{{passed_css}}}"
        else:
            css = ""
        rtag.contents = rx.Var(
            f"{{(provided, snapshot) => <div ref={{provided.innerRef}} {{...provided.droppableProps}} {css}>{self.children[0]}{{provided.placeholder}}</div>}}"
        )
        return rtag

    def render(self):
        rdict = super().render()
        rdict["children"] = [{}]
        return rdict


class Draggable(DndBase):
    tag = "Draggable"

    draggable_id: rx.Var[str]
    index: rx.Var[int]
    is_drag_disabled: rx.Var[bool]
    disable_interactive_element_blocking: rx.Var[bool]
    should_respect_force_press: rx.Var[bool]

    def _render(self):
        rtag = super()._render()
        passed_css = rtag.props.pop("css", None)
        if passed_css is not None:
            css = f"css={{{passed_css}}}"
        else:
            css = ""
        contents = rx.Var(
            f"{{(provided, snapshot) => <div ref={{provided.innerRef}} {{...provided.draggableProps}} {{...provided.dragHandleProps}} {css}>{self.children[0]}</div>}}"
        )
        rtag.contents = contents
        return rtag

    def render(self):
        rdict = super().render()
        rdict["children"] = [{}]
        return rdict


drag_drop_context = DragDropContext.create
droppable = Droppable.create
draggable = Draggable.create
