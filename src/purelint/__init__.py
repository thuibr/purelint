"""Module implementing mutability and exhaustiveness checking."""

from functools import reduce
from typing import TYPE_CHECKING, Callable

from astroid import nodes
from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from typing import NoReturn

    from pylint.lint import PyLinter


def assert_never(value: "NoReturn") -> "NoReturn":
    """This should never be called."""
    assert False, f"Unknown value: {value}"


def pipe(value, *funcs: Callable):
    """Pass value through a pipeline of functions."""
    return reduce(lambda acc, f: f(acc), funcs, value)


class RebindChecker(BaseChecker):
    """Check if variables are rebound."""

    # pylint: disable=rebind
    name = "no-rebind"
    msgs = {
        "E9001": (
            "Rebinding name '%s' is not allowed",
            "rebind",
            "Used when a variable is rebound in the same scope",
        ),
    }
    # pylint: enable=rebind

    def __init__(self, linter=None):
        super().__init__(linter)
        self.scopes = []

    def open(self):
        # module-level scope
        self.scopes = [set()]

    def visit_functiondef(self, _: nodes.FunctionDef):
        """Init when visiting a function def."""
        self.scopes.append(set())  # pylint: disable=mutable-method-used

    def leave_functiondef(self, _: nodes.FunctionDef):
        """Cleanup after leaving a function def."""
        self.scopes.pop()  # pylint: disable=mutable-method-used

    def visit_assign(self, node: nodes.Assign):
        """Visit assignment in the AST."""
        scope = self.scopes[-1]

        # Collect all variable names that would be rebinding
        rebind_names = {
            target.name
            for target in node.targets
            if isinstance(target, nodes.AssignName) and target.name in scope
        }

        for name in rebind_names:
            self.add_message("rebind", node=node, args=(name,))

        # Update scope with all assigned names
        new_names = {
            target.name
            for target in node.targets
            if isinstance(target, nodes.AssignName)
        }
        scope.update(new_names)  # pylint: disable=mutable-method-used


class NoAugAssignChecker(BaseChecker):
    """Check if augmented assignment is used."""

    # pylint: disable=rebind
    name = "no-augassign"
    msgs = {
        "E9002": (
            "Augmented assignment '%s' is not allowed",
            "augassign-used",
            "Disallows +=, -=, *= etc for functional style",
        )
    }
    # pylint: enable=rebind

    def visit_augassign(self, node: nodes.AugAssign):
        """Visit augmented assignment in the AST."""
        op = node.op
        self.add_message("augassign-used", node=node, args=(op,))


class NoSideEffectChecker(BaseChecker):
    """Check if side-effects are used"""

    # pylint: disable=rebind
    name = "no-side-effect"
    msgs = {
        "E9003": (
            "Side-effecting call '%s' is not allowed",
            "side-effect-used",
            "Disallows print, file writes, or OS commands in pure functions",
        )
    }
    # pylint: enable=rebind

    SIDE_EFFECT_FUNCS = {"print", "open", "exec", "eval", "exit", "quit", "delattr"}

    def visit_expr(self, node: nodes.Call):
        """Visit expressions in the AST."""
        func = node.value.func
        if isinstance(func, nodes.Name) and func.name in self.SIDE_EFFECT_FUNCS:
            self.add_message("side-effect-used", node=node, args=(func.name,))

    def _get_func_name(self, func_node) -> str | None:
        match func_node:
            case nodes.Name(name=name):
                return name
            case nodes.Attribute(attrname=attrname):
                return attrname
            case _:
                return None

    def visit_with(self, node: nodes.With):
        """Visit with calls in the AST."""
        for item in node.items:
            expr = item[0]
            if isinstance(expr, nodes.Call):
                func_name = self._get_func_name(expr.func)
                if func_name in self.SIDE_EFFECT_FUNCS:
                    self.add_message(
                        "side-effect-used", node=node, args=(expr.func.as_string())
                    )


class NoMutableLiteralChecker(BaseChecker):
    """Check if mutable literals are used"""

    # pylint: disable=rebind
    name = "no-mutable-literal-checker"
    msgs = {
        "E9004": (
            "Mutable literal '%s' is discouraged; use tuple/frozenset/frozen dataclass",
            "mutable-literal",
            "Disallow mutable literals in functional code",
        )
    }
    # pylint: enable=rebind

    def visit_list(self, node: nodes.List):
        """Visit lists in the AST."""
        self.add_message("mutable-literal", node=node, args=("list",))

    def visit_dict(self, node: nodes.Dict):
        """Visit dicts in the AST."""
        self.add_message("mutable-literal", node=node, args=("dict",))

    def visit_set(self, node: nodes.Set):
        """Visit sets in the AST."""
        self.add_message("mutable-literal", node=node, args=("set",))

    def visit_call(self, node: nodes.Call):
        "Visit function calls in the AST."
        func_name = node.func.as_string()
        if func_name in {"list", "dict", "set"}:
            self.add_message("mutable-literal", node=node, args=(func_name,))


class NoMutableMethodChecker(BaseChecker):
    """Check if mutable methods are used."""

    # pylint: disable=rebind
    name = "no-mutable-method"
    msgs = {
        "E9005": (
            "Mutable method '%s' is not allowed; use functional alternatives",
            "mutable-method-used",
            "Disallow list/dict/set mutating methods like append, pop, remove, clear",
        )
    }
    # pylint: enable=rebind

    MUTABLE_METHODS = {
        "add",
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
        """Visit function calls in the AST."""
        func = node.func

        if isinstance(func, nodes.Attribute):
            method_name = func.attrname
            if method_name in self.MUTABLE_METHODS:
                self.add_message("mutable-method-used", node=node, args=(method_name,))


class NoSubscriptAssignmentChecker(BaseChecker):
    """Check for assignment to subscripts."""

    # pylint: disable=rebind
    name = "no-subscript-assign"
    msgs = {
        "E9006": (
            "Subscript assignment '%s' is not allowed; objects should be immutable",
            "subscript-assignment",
            "Disallows a[...] = ... assignments to enforce functional immutability",
        )
    }
    # pylint: enable=rebind

    def visit_assign(self, node: nodes.Assign):
        """Visit assign calls in the AST."""
        for target in node.targets:
            if isinstance(target, nodes.Subscript):
                self.add_message(
                    "subscript-assignment", node=node, args=(target.as_string(),)
                )

    def visit_delete(self, node: nodes.Delete):
        """Visit delete calls in the AST."""
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

    # pylint: disable=rebind
    name = "no-delete"
    msgs = {
        "E9007": (
            "Deleting variable '%s' is not allowed; use functional alternatives",
            "delete-used",
            "Disallow 'del' to prevent mutation of variables",
        )
    }
    # pylint: enable=rebind

    def visit_delete(self, node: nodes.Delete):
        """Visit delete calls in the AST."""
        for target in node.targets:
            if isinstance(target, nodes.DelName):
                # del obj
                self.add_message("delete-used", node=node, args=(target.name,))
            elif isinstance(target, (nodes.DelAttr, nodes.Subscript)):
                # Catch del obj.attr
                self.add_message("delete-used", node=node, args=(target.as_string(),))


AnyMatch = (
    nodes.MatchSingleton
    | nodes.MatchAs
    | nodes.MatchClass
    | nodes.MatchValue
    | nodes.MatchOr
    | nodes.Match
)


class ExhaustiveMatchChecker(BaseChecker):
    """All possible types must be checked in a 'match' statement."""

    # pylint: disable=rebind
    name = "exhaustiveness"
    msgs = {
        "E9008": (
            "Not all values are handled: %s",
            "match-not-exhaustive",
            "Raised when a match statement doesn't handle all branches",
        ),
    }
    # pylint: enable=rebind

    def visit_match(self, node: nodes.Match):
        """Visit a match in the AST."""
        has_default = any(
            isinstance(case.pattern, nodes.MatchAs) and case.pattern.name is None
            for case in node.cases
        )

        if not has_default:
            self.add_message("match-not-exhaustive", node=node, args=("_",))


class NoIfChecker(BaseChecker):
    """Forbid using 'if' statements."""

    # pylint: disable=rebind
    name = "no-if"
    msgs = {
        "E9009": (
            "Usage of 'if' statements is not allowed",
            "if-used",
            "Disallows 'if' statements for pure functional style",
        )
    }
    # pylint: enable=rebind

    def visit_if(self, node: nodes.If):
        """Called for each If node in the AST."""
        self.add_message("if-used", node=node)


def register(linter: "PyLinter") -> None:
    """Register the linters with PyLint."""
    for lint in [
        RebindChecker,
        NoAugAssignChecker,
        # NoSideEffectChecker,
        # NoMutableLiteralChecker,
        NoMutableMethodChecker,
        NoSubscriptAssignmentChecker,
        NoDeleteChecker,
        ExhaustiveMatchChecker,
        # NoIfChecker,
    ]:
        linter.register_checker(lint(linter))
