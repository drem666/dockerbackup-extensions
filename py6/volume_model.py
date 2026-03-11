from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from utils import list_volumes


class TreeNode:
    def __init__(self, path, parent=None):
        self.path = path
        self.parent = parent
        self.children = []
        self.check_state = Qt.CheckState.Unchecked  # Use enum, not integer

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
            # FIXED: Convert integer value to Qt.CheckState enum for consistency
            if isinstance(value, int):
                node.check_state = Qt.CheckState(value)
            else:
                node.check_state = value
            
            # print(f"setData: node id={id(node)}, path={node.path}, state={node.check_state}")
            
            self._set_children_state(node, node.check_state)
            self._update_parent_state(node.parent)
            
            top_left = self.index(0, 0, QModelIndex())
            bottom_right = self.index(self.rowCount(QModelIndex())-1, 0, QModelIndex())
            self.dataChanged.emit(top_left, bottom_right, [Qt.CheckStateRole])
            return True
        return False

    def _set_children_state(self, node, state):
        for child in node.children:
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
            parent.check_state = Qt.CheckState.PartiallyChecked
        self._update_parent_state(parent.parent)

    # ---- Utility ----

    def get_selected_paths(self):
        selected = []
        # print("\n--- get_selected_paths called ---")
        
        # Uncomment for debugging (only prints checked/partial nodes + first 10)
        # counter = [0]
        
        def recurse(node, indent=""):
            # Debug output (uncomment if needed)
            # if node.check_state != Qt.CheckState.Unchecked or counter[0] < 10:
            #     print(f"{indent}Node: {node.path} | id={id(node)} | CheckState: {node.check_state} | Children: {len(node.children)}")
            #     counter[0] += 1
            
            # FIXED: Compare with Qt.CheckState.Checked enum, not integer
            if node.check_state == Qt.CheckState.Checked:
                parent = node.parent
                if parent is None or parent.check_state != Qt.CheckState.Checked:
                    selected.append(node.path)
            
            # Recurse to handle partially checked parents
            for child in node.children:
                recurse(child, indent + "  ")

        recurse(self.root_node)
        # print(f"Selected paths: {selected}\n")
        return selected

    def rebuild(self):
        """Completely rebuild the tree model from scratch."""
        self.beginResetModel()
        self.root_node = TreeNode("/")
        self._build_model()
        self.endResetModel()

    def find_node(self, path, node=None):
        """Find a tree node by its full path."""
        if node is None:
            node = self.root_node
        if node.path == path:
            return node
        for child in node.children:
            result = self.find_node(path, child)
            if result:
                return result
        return None

    def _set_subtree_state(self, node, state):
        """Set the check state of a node and all its descendants."""
        node.check_state = state
        for child in node.children:
            self._set_subtree_state(child, state)

    def _recompute_parent_states(self):
        """Update all parent nodes' check states based on their children."""
        def recurse(node):
            for child in node.children:
                recurse(child)
            if node.parent:
                states = {child.check_state for child in node.parent.children}
                if len(states) == 1:
                    node.parent.check_state = states.pop()
                else:
                    node.parent.check_state = Qt.CheckState.PartiallyChecked
        recurse(self.root_node)

    def restore_checked_states(self, paths):
        """
        Restore checked states from a list of previously selected paths.
        paths: list of full paths (strings) that were checked.
        """
        # First, reset everything to unchecked
        self._set_subtree_state(self.root_node, Qt.CheckState.Unchecked)

        # Then set each saved path and its descendants to checked
        for path in paths:
            node = self.find_node(path)
            if node:
                self._set_subtree_state(node, Qt.CheckState.Checked)

        # Update all parent states to reflect partial/checked correctly
        self._recompute_parent_states()

        # Notify the view that the whole model's check states changed
        top_left = self.index(0, 0, QModelIndex())
        bottom_right = self.index(self.rowCount(QModelIndex()) - 1, 0, QModelIndex())
        self.dataChanged.emit(top_left, bottom_right, [Qt.CheckStateRole])