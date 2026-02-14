from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from utils import list_volumes


class TreeNode:
    def __init__(self, path, parent=None):
        self.path = path
        self.parent = parent
        self.children = []
        self.check_state = Qt.Unchecked

    def child(self, row):
        return self.children[row]

    def child_count(self):
        return len(self.children)

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class VolumeTreeModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root_node = TreeNode("/")
        self._build_model()

    def _build_model(self):
        volumes = list_volumes()
        self._add_children(self.root_node, volumes)

    def _add_children(self, parent_node, children_data):
        for child in children_data:
            node = TreeNode(child["path"], parent_node)
            parent_node.children.append(node)
            self._add_children(node, child.get("children", []))

    # ---- Required Model Methods ----

    def rowCount(self, parent):
        node = parent.internalPointer() if parent.isValid() else self.root_node
        return node.child_count()

    def columnCount(self, parent):
        return 1

    def index(self, row, column, parent):
        parent_node = parent.internalPointer() if parent.isValid() else self.root_node
        if row < 0 or row >= parent_node.child_count():
            return QModelIndex()

        child_node = parent_node.child(row)
        return self.createIndex(row, column, child_node)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        node = index.internalPointer()
        parent_node = node.parent

        if parent_node is None or parent_node == self.root_node:
            return QModelIndex()

        return self.createIndex(parent_node.row(), 0, parent_node)

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == Qt.DisplayRole:
            return node.path.split("/")[-1] or node.path

        if role == Qt.CheckStateRole:
            return node.check_state

        return None

    def flags(self, index):
        return (
            Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
            | Qt.ItemIsUserCheckable
        )

    # ---- Checkbox Logic ----

    def setData(self, index, value, role):
        if role == Qt.CheckStateRole:
            node = index.internalPointer()
            # print(f"\n>>> setData: {node.path} set to {value}")
            node.check_state = value
            self._set_children_state(node, value)
            self._update_parent_state(node.parent)
            # self.layoutChanged.emit()
            top_left = self.index(0, 0, QModelIndex())
            bottom_right = self.index(self.rowCount(QModelIndex())-1, 0, QModelIndex())
            self.dataChanged.emit(top_left, bottom_right, [Qt.CheckStateRole])
            return True
        return False

    def _set_children_state(self, node, state):
        for child in node.children:
            # print(f"    child {child.path} set to {state}")
            child.check_state = state
            self._set_children_state(child, state)

    def _update_parent_state(self, parent):
        if parent is None:
            return
        states = {child.check_state for child in parent.children}
        old_state = parent.check_state
        if len(states) == 1:
            parent.check_state = states.pop()
        else:
            parent.check_state = Qt.PartiallyChecked
        if parent.check_state != old_state:
            # print(f"    parent {parent.path} changed from {old_state} to {parent.check_state}")
            pass
        self._update_parent_state(parent.parent)

    # ---- Utility ----

    def get_selected_paths(self):
        # print(f"get_selected_paths: root_node id = {id(self.root_node)}")
        # print(f"get_selected_paths: model id = {id(self)}")
        selected = []
        # print("\n--- get_selected_paths called ---")

        def recurse(node, indent=""):
            # print(f"{indent}Node: {node.path} (id={id(node)}) state={node.check_state}")
            # print(f"{indent}Node: {node.path} | CheckState: {node.check_state} | Children: {len(node.children)}")
            # If node is checked and its parent is not fully checked, add it
            if node.check_state == Qt.Checked:
                parent = node.parent
                if parent is None or parent.check_state != Qt.Checked:
                    # print(f"{indent}  --> ADDING: {node.path}")
                    selected.append(node.path)
            # Recurse to handle partially checked parents
            for child in node.children:
                recurse(child, indent + "  ")

        recurse(self.root_node)
        # print(f"Selected paths: {selected}\n")
        return selected


