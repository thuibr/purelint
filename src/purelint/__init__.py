from functools import reduce
from typing import TYPE_CHECKING, Callable

from astroid import nodes
from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class RebindChecker(BaseChecker):
    """Check if variables are rebound."""

    name = "no-rebind"

    msgs = {
        "E9001": (
            "Rebinding name '%s' is not allowed",
            "rebind",
            "Used when a variable is rebound in the same scope",
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        self.scopes = []

    def open(self):
        # module-level scope
        self.scopes = [set()]

    def visit_functiondef(self, node: nodes.FunctionDef):
        self.scopes.append(set())

    def leave_functiondef(self, node: nodes.FunctionDef):
        self.scopes.pop()

    def visit_assign(self, node: nodes.Assign):
        scope = self.scopes[-1]
        for target in node.targets:
            if isinstance(target, nodes.AssignName):
                name = target.name
                if name in scope:
                    self.add_message("rebind", node=node, args=(name,))
                else:
                    scope.add(name)


class NoAugAssignChecker(BaseChecker):
    """Check if augmented assignment is used."""

    name = "no-augassign"
    msgs = {
        "E9002": (
            "Augmented assignment '%s' is not allowed",
            "augassign-used",
            "Disallows +=, -=, *= etc for functional style",
        )
    }

    def visit_augassign(self, node: nodes.AugAssign):
        op = node.op
        self.add_message("augassign-used", node=node, args=(op,))


class NoSideEffectChecker(BaseChecker):
    """Check if side-effects are used"""

    name = "no-side-effect"
    msgs = {
        "E9003": (
            "Side-effecting call '%s' is not allowed",
            "side-effect-used",
            "Disallows print, file writes, or OS commands in pure functions",
        )
    }

    SIDE_EFFECT_FUNCS = {"print", "open", "exec", "eval", "exit", "quit", "delattr"}

    def visit_expr(self, node: nodes.Call):
        func = node.value.func
        if isinstance(func, nodes.Name) and func.name in self.SIDE_EFFECT_FUNCS:
            self.add_message("side-effect-used", node=node, args=(func.name,))

    def visit_with(self, node: nodes.With):
        for item in node.items:
            expr = item[0]
            if (
                isinstance(expr, nodes.Call)
                and expr.func.name in self.SIDE_EFFECT_FUNCS
            ):
                self.add_message(
                    "side-effect-used", node=node, args=(expr.func.as_string())
                )


class NoMutableLiteralChecker(BaseChecker):
    """Check if mutable literals are used"""

    name = "no-mutable-literal-checker"
    msgs = {
        "E9004": (
            "Mutable literal '%s' is discouraged; use tuple/frozenset/frozen dataclass",
            "mutable-literal",
            "Disallow mutable literals in functional code",
        )
    }

    def visit_list(self, node: nodes.List):
        self.add_message("mutable-literal", node=node, args=("list",))

    def visit_dict(self, node: nodes.Dict):
        self.add_message("mutable-literal", node=node, args=("dict",))

    def visit_set(self, node: nodes.Set):
        self.add_message("mutable-literal", node=node, args=("set",))

    def visit_call(self, node: nodes.Call):
        func_name = node.func.as_string()
        if func_name in {"list", "dict", "set"}:
            self.add_message("mutable-literal", node=node, args=(func_name,))


class NoMutableMethodChecker(BaseChecker):
    """Check if mutable methods are used."""

    name = "no-mutable-method"

    msgs = {
        "E9005": (
            "Mutable method '%s' is not allowed; use functional alternatives",
            "mutable-method-used",
            "Disallow list/dict/set mutating methods like append, pop, remove, clear",
        )
    }

    MUTABLE_METHODS = {
        "append",
        "extend",
        "insert",
        "pop",
        "remove",
        "clear",
        "update",
        "setdefault",
    }

    def visit_call(self, node: nodes.Call):
        func = node.func

        if isinstance(func, nodes.Attribute):
            method_name = func.attrname
            if method_name in self.MUTABLE_METHODS:
                self.add_message("mutable-method-used", node=node, args=(method_name,))


class NoSubscriptAssignmentChecker(BaseChecker):
    """Check for assignment to subscripts."""

    name = "no-subscript-assign"

    msgs = {
        "E9006": (
            "Subscript assignment '%s' is not allowed; objects should be immutable",
            "subscript-assignment",
            "Disallows a[...] = ... assignments to enforce functional immutability",
        )
    }

    def visit_assign(self, node: nodes.Assign):
        for target in node.targets:
            if isinstance(target, nodes.Subscript):
                self.add_message(
                    "subscript-assignment", node=node, args=(target.as_string(),)
                )

    def visit_delete(self, node: nodes.Delete):
        for target in node.targets:
            if isinstance(target, nodes.Subscript) and not isinstance(
                target.parent, nodes.Delete
            ):
                # ignore if a del because NoDeleteChecker handles it
                self.add_message(
                    "subscript-assignment", node=node, args=(target.as_string(),)
                )


class NoDeleteChecker(BaseChecker):
    """Disallow 'del' statements to enforce immutability."""

    name = "no-delete"

    msgs = {
        "E9007": (
            "Deleting variable '%s' is not allowed; use functional alternatives",
            "delete-used",
            "Disallow 'del' to prevent mutation of variables",
        )
    }

    def visit_delete(self, node: nodes.Delete):
        for target in node.targets:
            if isinstance(target, nodes.DelName):
                # del obj
                self.add_message("delete-used", node=node, args=(target.name,))
            elif isinstance(target, nodes.DelAttr) or isinstance(
                target, nodes.Subscript
            ):
                # Catch del obj.attr
                self.add_message("delete-used", node=node, args=(target.as_string(),))


def register(linter: "PyLinter") -> None:
    linter.register_checker(RebindChecker(linter))
    linter.register_checker(NoAugAssignChecker(linter))
    linter.register_checker(NoSideEffectChecker(linter))
    linter.register_checker(NoMutableLiteralChecker(linter))
    linter.register_checker(NoMutableMethodChecker(linter))
    linter.register_checker(NoSubscriptAssignmentChecker(linter))
    linter.register_checker(NoDeleteChecker(linter))


def pipe(value, *funcs: Callable):
    """Pass value through a pipeline of functions."""
    return reduce(lambda acc, f: f(acc), funcs, value)
