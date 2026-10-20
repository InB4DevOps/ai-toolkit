import unittest
from collections import Counter
from types import SimpleNamespace

from toolkit.image_coverage import ImageCoverageTracker, get_repeat_weighted_source_paths


class TestImageCoverageTracker(unittest.TestCase):
    def test_epoch_size_adds_dataset_entries_but_collapses_internal_variants(self):
        first_config = SimpleNamespace(coverage_group_id=0, num_repeats=2)
        resolution_copy = SimpleNamespace(coverage_group_id=0, num_repeats=2)
        duplicate_entry = SimpleNamespace(coverage_group_id=1, num_repeats=3)
        datasets = [
            SimpleNamespace(file_list=[
                SimpleNamespace(path="shared.png", dataset_config=first_config),
                SimpleNamespace(path="shared.png", dataset_config=first_config),
            ]),
            SimpleNamespace(file_list=[
                SimpleNamespace(path="shared.png", dataset_config=resolution_copy),
            ]),
            SimpleNamespace(file_list=[
                SimpleNamespace(path="shared.png", dataset_config=duplicate_entry),
            ]),
        ]

        source_paths = get_repeat_weighted_source_paths(datasets)

        self.assertEqual(Counter(source_paths), Counter({"shared.png": 5}))

    def test_repeated_sources_define_epoch_size_and_each_batch_use_counts(self):
        tracker = ImageCoverageTracker(["a.png", "a.png", "b.png"])

        update = tracker.record(["a.png", "a.png"])

        self.assertEqual(update.total, 3)
        self.assertEqual(update.covered, 2)
        self.assertEqual(update.completed_epochs, 0)

    def test_completes_after_repeat_weighted_number_of_uses(self):
        tracker = ImageCoverageTracker(["a.png", "a.png", "b.png"])

        update = tracker.record(["a.png", "a.png", "a.png"])

        self.assertEqual(update.total, 3)
        self.assertEqual(update.completed_epochs, 1)

    def test_source_distribution_does_not_delay_completion(self):
        tracker = ImageCoverageTracker(["a.png", "a.png", "b.png"])
        tracker.record(["a.png"])

        update = tracker.record(["a.png", "a.png"])

        self.assertEqual(update.completed_epochs, 1)
        self.assertEqual(update.covered, 3)

    def test_151_use_epoch_completes_on_the_151st_successful_use(self):
        tracker = ImageCoverageTracker(["a.png"] * 151)

        partial = tracker.record(["a.png"] * 150)
        complete = tracker.record(["a.png"])

        self.assertEqual(partial.covered, 150)
        self.assertEqual(partial.completed_epochs, 0)
        self.assertEqual(complete.covered, 151)
        self.assertEqual(complete.completed_epochs, 1)

    def test_additive_dataset_entries_increase_the_source_quota(self):
        tracker = ImageCoverageTracker(["shared.png", "shared.png", "shared.png"])

        partial = tracker.record(["shared.png", "shared.png"])
        complete = tracker.record(["shared.png"])

        self.assertEqual(partial.covered, 2)
        self.assertEqual(partial.completed_epochs, 0)
        self.assertEqual(complete.completed_epochs, 1)

    def test_completes_when_epoch_size_is_reached_across_sources(self):
        tracker = ImageCoverageTracker(["a.png", "b.png"])
        tracker.record(["a.png"])

        update = tracker.record(["b.png"])

        self.assertEqual(update.completed_epochs, 1)
        self.assertEqual(update.covered, 2)

    def test_preserves_excess_uses_for_the_next_epoch(self):
        tracker = ImageCoverageTracker(["a.png", "b.png"])

        first_epoch = tracker.record(["a.png", "a.png", "b.png"])

        self.assertEqual(first_epoch.completed_epochs, 1)
        self.assertEqual(tracker.covered, 1)

        second_epoch = tracker.record(["b.png"])
        self.assertEqual(second_epoch.completed_epochs, 1)
        self.assertEqual(second_epoch.covered, 2)

    def test_preserves_excess_uses_with_repeat_weighted_total(self):
        tracker = ImageCoverageTracker(["a.png", "a.png", "b.png"])

        first_epoch = tracker.record(["a.png", "a.png", "a.png", "b.png"])

        self.assertEqual(first_epoch.completed_epochs, 1)
        self.assertEqual(tracker.covered, 1)
        second_epoch = tracker.record(["a.png", "a.png"])
        self.assertEqual(second_epoch.completed_epochs, 1)
        self.assertEqual(second_epoch.covered, 3)

    def test_ignores_unknown_paths(self):
        tracker = ImageCoverageTracker(["a.png"])

        update = tracker.record(["regularization.png"])

        self.assertEqual(update.covered, 0)
        self.assertEqual(update.completed_epochs, 0)

    def test_empty_update_does_not_advance_coverage(self):
        tracker = ImageCoverageTracker(["a.png"])

        update = tracker.record([])

        self.assertEqual(update.covered, 0)
        self.assertEqual(update.completed_epochs, 0)

    def test_staged_uses_only_count_after_commit(self):
        tracker = ImageCoverageTracker(["a.png"])

        tracker.stage(["a.png"])

        self.assertEqual(tracker.covered, 0)
        update = tracker.commit_pending()
        self.assertEqual(update.completed_epochs, 1)

    def test_discard_removes_the_whole_accumulation_window(self):
        tracker = ImageCoverageTracker(["a.png", "b.png"])
        tracker.stage(["a.png"])

        tracker.discard_pending()
        update = tracker.record(["b.png"])

        self.assertEqual(update.covered, 1)
        self.assertEqual(update.completed_epochs, 0)

    def test_preserves_repeated_uses_across_staged_steps(self):
        tracker = ImageCoverageTracker(["a.png", "b.png"])
        tracker.stage(["a.png"])
        tracker.stage(["a.png"])
        tracker.stage(["b.png"])

        first_epoch = tracker.commit_pending()

        self.assertEqual(first_epoch.completed_epochs, 1)
        self.assertEqual(tracker.covered, 1)


if __name__ == "__main__":
    unittest.main()
