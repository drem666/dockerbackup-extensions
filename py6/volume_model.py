from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from utils import list_volumes


class TreeNode:
    def __init__(self, path, parent=None):
        self.path = path
        self.parent = parent
        self.children = []
        self.checked = False

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

    def rowCount(self, parent):
        node = parent.internalPointer() if parent.isValid() else self.root_node
        return node.child_count()

    def columnCount(self, parent):
        return 1

    def index(self, row, column, parent):
        parent_node = parent.internalPointer() if parent.isValid() else self.root_node
        child_node = parent_node.child(row)
        return self.createIndex(row, column, child_node)

    def parent(self, index):
        node = index.internalPointer()
        parent_node = node.parent
        if parent_node == self.root_node or not parent_node:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == Qt.DisplayRole:
            return node.path.split("/")[-1] or node.path

        if role == Qt.CheckStateRole:
            return Qt.Checked if node.checked else Qt.Unchecked

        return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def setData(self, index, value, role):
        if role == Qt.CheckStateRole:
            node = index.internalPointer()
            node.checked = value == Qt.Checked
            self._set_children_checked(node, node.checked)
            self.dataChanged.emit(index, index)
            return True
        return False

    def _set_children_checked(self, node, state):
        for child in node.children:
            child.checked = state
            self._set_children_checked(child, state)

    def get_selected_paths(self):
        selected = []

        def recurse(node):
            if node.checked:
                selected.append(node.path)
            for c in node.children:
                recurse(c)

        recurse(self.root_node)
        return selected