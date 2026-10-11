import unittest

from service import JobStore, render_report


class ServiceTests(unittest.TestCase):
    def test_repeated_request_returns_same_job(self):
        store = JobStore()
        self.assertIs(store.enqueue_once("a", "r1"), store.enqueue_once("a", "r1"))

    def test_request_keys_are_tenant_scoped(self):
        store = JobStore()
        a = store.enqueue_once("a", "r1")
        b = store.enqueue_once("b", "r1")
        self.assertNotEqual(a.job_id, b.job_id)
        self.assertIsNone(store.get_for_tenant("b", a.job_id))

    def test_simple_report(self):
        self.assertEqual(render_report([["name", "total"], ["Ada", 4]]), "name,total\nAda,4")


if __name__ == "__main__":
    unittest.main()
