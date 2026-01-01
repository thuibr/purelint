import astroid
from pylint.testutils import CheckerTestCase, MessageTest

import purelint


class TestRebindChecker(CheckerTestCase):
    CHECKER_CLASS = purelint.RebindChecker

    def test_assign(self):
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
    CHECKER_CLASS = purelint.NoAugAssignChecker

    def test_augassign(self):
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
    CHECKER_CLASS = purelint.NoSideEffectChecker

    def test_print_call(self):
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
    CHECKER_CLASS = purelint.NoMutableLiteralChecker

    def test_list_literal(self):
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
    CHECKER_CLASS = purelint.NoMutableMethodChecker

    def test_list_pop(self):
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
    CHECKER_CLASS = purelint.NoSubscriptAssignmentChecker

    def test_subscript(self):
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
    CHECKER_CLASS = purelint.NoDeleteChecker

    def test_del_variable(self):
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
