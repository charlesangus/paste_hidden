# Deferred Items — Phase 05

## Pre-existing Test Failures (out of scope for 05-03)

### test_dot_anchor_name_sync.py — 6 failing tests

These tests were written by plan 05-02 for Dot anchor name-sync features
(`rename_anchor_to()`, `mark_dot_as_anchor()` with name-setting) that are not
yet implemented in `anchor.py`. The `StubNode` used in the test suite lacks a
`setName()` method, and the anchor.py logic for setting the node name is
incomplete.

Failing tests:
- TestMarkDotAsAnchorNameSync::test_mark_dot_as_anchor_with_labelled_dot_sets_node_name_to_anchor_prefix_plus_sanitized_label
- TestRenameAnchorToDotPath::test_rename_anchor_to_dot_updates_label
- TestRenameAnchorToDotPath::test_rename_anchor_to_dot_updates_link_node_knob_name_from_old_fqnn_to_new_fqnn
- TestRenameAnchorToDotPath::test_rename_anchor_to_dot_updates_link_node_label_to_new_name
- TestRenameAnchorToDotPath::test_rename_anchor_to_dot_updates_node_name_to_anchor_prefix_plus_sanitized
- TestRenameAnchorToDotPath::test_rename_anchor_to_dot_with_name_that_sanitizes_to_empty_raises_value_error

These were present before plan 05-03 changes and are not caused by 05-03.
They should be resolved by a follow-up plan that implements the full
`rename_anchor_to()` Dot-anchor path and adds `setName()` to StubNode.
