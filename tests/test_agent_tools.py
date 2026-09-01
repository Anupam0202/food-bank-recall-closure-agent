import unittest

from app.agents.tools import (
    ALL_TOOLS,
    create_partner_tasks,
    evaluate_ambiguous_item,
    extract_recall_fields,
    get_incident_status,
    load_recall_source,
    propose_incident_actions,
    query_inventory,
    summarize_open_actions,
)


class AgentToolTests(unittest.TestCase):
    def test_exact_allowlist_has_eight_tools(self):
        self.assertEqual(len(ALL_TOOLS), 8)
        self.assertEqual({tool.__name__ for tool in ALL_TOOLS}, {
            "load_recall_source", "extract_recall_fields", "query_inventory",
            "evaluate_ambiguous_item", "propose_incident_actions",
            "create_partner_tasks", "get_incident_status", "summarize_open_actions",
        })

    def test_source_tool_excludes_raw_payload(self):
        result = load_recall_source("FDA", "https://example.test", "hash", "limit")
        self.assertNotIn("raw_payload", result)

    def test_extraction_tool_sanitizes_fields(self):
        result = extract_recall_fields({"recall_number": "R1", "secret": "no"})
        self.assertEqual(result, {"recall_number": "R1"})

    def test_inventory_query_can_scope_agency(self):
        result = query_inventory([{"id": "1", "agency_id": "a"}, {"id": "2", "agency_id": "b"}], "a")
        self.assertEqual(result["count"], 1)

    def test_ambiguous_tool_never_returns_exact(self):
        result = evaluate_ambiguous_item({"id": "i", "visible_identifiers": ["LOT1"]}, {"lots": ["LOT1"]})
        self.assertEqual(result["category"], "SEMANTIC_OR_VISUAL_REVIEW")
        self.assertTrue(result["requires_human_review"])

    def test_action_proposal_is_bounded(self):
        result = propose_incident_actions([{"inventory_item_id": "i", "category": "EXACT_MATCH"}])
        self.assertEqual(result["quarantine_holds"], ["i"])
        self.assertIn("dispose", result["prohibited_actions"])

    def test_task_tool_is_proposal_only(self):
        result = create_partner_tasks(["a"], ["i"], [])
        self.assertFalse(result["write_performed"])

    def test_status_and_open_action_tools(self):
        self.assertEqual(get_incident_status({"id": "x", "state": "MATCHED", "raw": "no"})["id"], "x")
        result = summarize_open_actions([{"id": "t", "status": "OPEN"}, {"id": "d", "status": "ACKNOWLEDGED"}])
        self.assertEqual(result["open_action_count"], 1)
