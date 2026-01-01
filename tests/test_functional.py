"""Functional tests."""

import astroid
from pylint.testutils import CheckerTestCase, MessageTest

import purelint


class TestRebindChecker(CheckerTestCase):
    """Test the RebindChecker"""

    CHECKER_CLASS = purelint.RebindChecker  # pylint: disable=rebind

    def test_reassignment(self):
        """Test reassignment"""
        module = astroid.parse("x = 1\nx = 2")
        node1 = module.body[0]
        node2 = module.body[1]

        self.checker.open()  # initialize scope

        # Visit first assignment to register 'x'
        self.checker.visit_assign(node1)

        # Second assignment should trigger a message
        with self.assertAddsMessages(
            MessageTest(
                msg_id="rebind",
                line=2,
                col_offset=0,
                end_line=2,
                end_col_offset=5,
                node=node2,
                args=("x",),
            )
        ):
            self.checker.visit_assign(node2)

    def test_assign_in_different_scopes(self):
        """Test assignment in different scopes."""
        node = astroid.parse("""
def get_db():
    conn = 1
    return conn

def toggle():
    conn = 2
    return conn
            """)

        for child in node.body:
            self.checker.visit_functiondef(child)
            for stmt in child.body:
                if hasattr(stmt, "targets"):
                    self.checker.visit_assign(stmt)
            self.checker.leave_functiondef(child)

        assert len(self.linter.release_messages()) == 0


class TestNoAugAssignChecker(CheckerTestCase):
    """Test NoAugAssignChecker."""

    CHECKER_CLASS = purelint.NoAugAssignChecker  # pylint: disable=rebind

    def test_augassign(self):
        """Test augmented assignment"""
        node = astroid.parse("x = 1\nx += 1")
        with self.assertAddsMessages(
            MessageTest(
                msg_id="augassign-used",
                line=2,
                node=node.body[1],
                args=("+=",),
                col_offset=0,
                end_line=2,
                end_col_offset=6,
            )
        ):
            self.checker.visit_augassign(node.body[1])


class TestNoSideEffectChecker(CheckerTestCase):
    """Test NoSideEffectChecker."""

    CHECKER_CLASS = purelint.NoSideEffectChecker  # pylint: disable=rebind

    def test_print_call(self):
        """Test print call."""
        node = astroid.parse("print('Hello')")
        call_node = node.body[0]
        with self.assertAddsMessages(
            MessageTest(
                msg_id="side-effect-used",
                line=1,
                node=call_node,
                args=("print",),
                col_offset=0,
                end_line=1,
                end_col_offset=14,
            )
        ):
            self.checker.visit_expr(call_node)

    def test_with_open(self):
        """Test with open."""
        node = astroid.parse("with open('file.txt', 'r') as f:\n    f.read()")
        node_with = node.body[0]
        with self.assertAddsMessages(
            MessageTest(
                msg_id="side-effect-used",
                line=1,
                node=node_with,
                args="open",
                col_offset=0,
                end_line=2,
                end_col_offset=12,
            )
        ):
            self.checker.visit_with(node_with)


class TestNoMutableLiteralChecker(CheckerTestCase):
    """Test NoMutableLiteralChecker."""

    CHECKER_CLASS = purelint.NoMutableLiteralChecker  # pylint: disable=rebind

    def test_list_literal(self):
        """Test list literal."""
        node = astroid.parse("lst = [1, 2, 3]")
        with self.assertAddsMessages(
            MessageTest(
                msg_id="mutable-literal",
                line=0,
                node=node,
                args=("list",),
                col_offset=0,
                end_line=None,
                end_col_offset=None,
            )
        ):
            self.checker.visit_list(node)

    def test_list_call(self):
        """Test list function."""
        node = astroid.parse("lst = list()")
        node_call = node.body[0].value
        with self.assertAddsMessages(
            MessageTest(
                msg_id="mutable-literal",
                line=1,
                node=node_call,
                args=("list",),
                col_offset=6,
                end_line=1,
                end_col_offset=12,
            )
        ):
            self.checker.visit_call(node_call)

    def test_dict_literal(self):
        """Test dict literal."""
        node = astroid.parse("d = {'a': 1}")
        with self.assertAddsMessages(
            MessageTest(
                msg_id="mutable-literal",
                line=0,
                node=node,
                args=("dict",),
                col_offset=0,
                end_line=None,
                end_col_offset=None,
            )
        ):
            self.checker.visit_dict(node)

    def test_dict_call(self):
        """Test dict function."""
        node = astroid.parse("d = dict()")
        node_call = node.body[0].value
        with self.assertAddsMessages(
            MessageTest(
                msg_id="mutable-literal",
                line=1,
                node=node_call,
                args=("dict",),
                col_offset=4,
                end_line=1,
                end_col_offset=10,
            )
        ):
            self.checker.visit_call(node_call)

    def test_set_literal(self):
        """Test set literal."""
        node = astroid.parse("s = {'a'}")
        with self.assertAddsMessages(
            MessageTest(
                msg_id="mutable-literal",
                line=0,
                node=node,
                args=("set",),
                col_offset=0,
                end_line=None,
                end_col_offset=None,
            )
        ):
            self.checker.visit_set(node)

    def test_set_call(self):
        """Test set function."""
        node = astroid.parse("s = set()")
        node_call = node.body[0].value
        with self.assertAddsMessages(
            MessageTest(
                msg_id="mutable-literal",
                line=1,
                node=node_call,
                args=("set",),
                col_offset=4,
                end_line=1,
                end_col_offset=9,
            )
        ):
            self.checker.visit_call(node_call)


class TestNoMutableMethodChecker(CheckerTestCase):
    """Test NoMutableMethodChecker."""

    CHECKER_CLASS = purelint.NoMutableMethodChecker  # pylint: disable=rebind

    def test_list_pop(self):
        """Test list popping."""
        node = astroid.parse("""
lst = [1, 2, 3]
lst.pop()
            """)
        call_node = node.body[-1].value

        with self.assertAddsMessages(
            MessageTest(
                msg_id="mutable-method-used",
                line=3,
                node=call_node,
                args=("pop",),
                col_offset=0,
                end_line=3,
                end_col_offset=9,
            )
        ):
            self.checker.visit_call(call_node)


class TestNoSubscriptAssignmentChecker(CheckerTestCase):
    """Test NoSubscriptAssignmentChecker."""

    CHECKER_CLASS = purelint.NoSubscriptAssignmentChecker  # pylint: disable=rebind

    def test_subscript(self):
        """Test subscripting."""
        node = astroid.parse("""
            import requests

            resp = requests.get("https://pokeapi.co/api/v2/pokemon/ditto", timeout=5)
            resp.raise_for_status()

            body = resp.json()
            print(body)

            body["abilities"] = None
            """)
        assign_node = node.body[-1]

        with self.assertAddsMessages(
            MessageTest(
                msg_id="subscript-assignment",
                line=10,
                node=assign_node,
                args=("body['abilities']",),
                col_offset=0,
                end_line=10,
                end_col_offset=24,
            )
        ):
            self.checker.visit_assign(assign_node)


class TestNoDeleteChecker(CheckerTestCase):
    """Test the NoDeleteChecker."""

    CHECKER_CLASS = purelint.NoDeleteChecker  # pylint: disable=rebind

    def test_del_variable(self):
        """Test deleting a variable."""
        node = astroid.parse("""
lst = [1, 2, 3]
del lst
            """)
        del_node = node.body[-1]

        with self.assertAddsMessages(
            MessageTest(
                msg_id="delete-used",
                line=3,
                node=del_node,
                args=("lst",),
                col_offset=0,
                end_line=3,
                end_col_offset=7,
            )
        ):
            self.checker.visit_delete(del_node)


class TestExhaustivenessChecker(CheckerTestCase):
    """Test the ExhaustivenessChecker."""

    CHECKER_CLASS = purelint.ExhaustiveMatchChecker  # pylint: disable=rebind

    def get_match_node(self, code: str):
        """Parse code and return the first Match node in the first function."""
        module = astroid.parse(code)
        # get the first function
        func = next(n for n in module.body if isinstance(n, astroid.nodes.FunctionDef))
        # find the first Match statement in function body
        match_node = next(n for n in func.body if isinstance(n, astroid.nodes.Match))
        return match_node

    def test_enum_exhaustive(self):
        """Test that all values in an enum are checked in a match."""
        code = """
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

def f(c: Color):
    match c:
        case Color.RED:
            pass
        case Color.GREEN:
            pass
            """
        match_node = self.get_match_node(code)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="match-not-exhaustive",
                line=10,
                node=match_node,
                args=(["BLUE"],),
                col_offset=4,
                end_line=14,
                end_col_offset=16,
            )
        ):
            self.checker.visit_match(match_node)

    def test_union_exhaustive(self):
        """Test that all values in a union are checked in a match"""
        code = """
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class Ok:
    value: int

@dataclasses(frozen=True)
class Err:
    msg: str

Result = Union[Ok, Err]

def handle(res: Result):
    match res:
        case Ok(value=v):
            return v
            """
        # 'Err' is missing -> should trigger message
        match_node = self.get_match_node(code)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="match-not-exhaustive",
                line=16,
                node=match_node,
                args=(["Union"],),
                col_offset=4,
                end_line=18,
                end_col_offset=20,
            )
        ):
            self.checker.visit_match(match_node)  # first match

    def test_union_and_enum_exhaustive(self):
        """Test that union and enum are exhaustive."""
        code = """
    from enum import Enum
    from dataclasses import dataclass
    from typing import Union

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    @dataclass(frozen=True)
    class Ok:
        value: int

    @dataclass(frozen=True)
    class Err:
        msg: str

    Result = Union[Ok, Err]

    def handle(res: Result | Color):
        match res:
            case Ok(value=v):
                return v
    """
        match_node = self.get_match_node(code)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="match-not-exhaustive",
                line=22,
                node=match_node,
                args=(["BLUE", "GREEN", "RED", "Union"],),
                col_offset=4,
                end_line=24,
                end_col_offset=20,
            )
        ):
            self.checker.visit_match(match_node)

    def test_union_and_enum_exhaustive2(self):
        """Test again."""
        code = """
from enum import Enum


class E(Enum):

    RED = auto()
    GREEN = auto()


def f_taker(f: E | None):
    match f:
        case E.RED:
            print("hi")
        case E.GREEN:
            print("hi")
        """
        match_node = self.get_match_node(code)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="match-not-exhaustive",
                line=12,
                node=match_node,
                args=([None],),
                col_offset=4,
                end_line=16,
                end_col_offset=23,
            )
        ):
            self.checker.visit_match(match_node)

    def test_bool(self):
        code = """
def f(b: bool):
    match b:
        case True:
            pass
        """
        match_node = self.get_match_node(code)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="match-not-exhaustive",
                line=3,
                node=match_node,
                args=([False, True],),
                col_offset=4,
                end_line=5,
                end_col_offset=16,
            )
        ):
            self.checker.visit_match(match_node)

    def test_bool_or_none(self):
        code = """
def f(b: bool | None):
    match b:
        case True:
            pass
        """
        match_node = self.get_match_node(code)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="match-not-exhaustive",
                line=3,
                node=match_node,
                args=([False, True, None],),
                col_offset=4,
                end_line=5,
                end_col_offset=16,
            )
        ):
            self.checker.visit_match(match_node)

    def test_bool_or_none_is_handled(self):
        code = """
def f(b: bool | None):
    match b:
        case True | False | None:
            pass
        """
        match_node = self.get_match_node(code)
        self.checker.visit_match(match_node)
        assert len(self.linter.release_messages()) == 0


class TestNoIfChecker(CheckerTestCase):
    """Test the NoIfChecker."""

    CHECKER_CLASS = purelint.NoIfChecker  # pylint: disable=rebind

    def test_no_if(self):
        """ "Test that no ifs are used."""
        node = astroid.parse("""if True:\n    pass""")
        with self.assertAddsMessages(
            MessageTest(
                msg_id="if-used",
                line=0,
                node=node,
                args=None,
                col_offset=0,
                end_line=None,
                end_col_offset=None,
            )
        ):
            self.checker.visit_if(node)
