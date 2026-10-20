from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ImageCoverageUpdate:
    completed_epochs: int
    covered: int
    total: int


def get_repeat_weighted_source_paths(datasets) -> list[str]:
    coverage_groups = {}
    for dataset in datasets:
        for item in dataset.file_list:
            group_id = item.dataset_config.coverage_group_id
            if group_id is None:
                group_id = id(item.dataset_config)
            if group_id not in coverage_groups:
                coverage_groups[group_id] = (
                    set(),
                    max(1, item.dataset_config.num_repeats),
                )
            coverage_groups[group_id][0].add(item.path)

    return [
        path
        for paths, repeats in coverage_groups.values()
        for path in paths
        for _ in range(repeats)
    ]


class ImageCoverageTracker:
    def __init__(self, source_paths: Iterable[str]):
        source_paths = list(source_paths)
        self._source_paths = set(source_paths)
        self._total = len(source_paths)
        self._covered = 0
        self._pending = 0

    @property
    def total(self) -> int:
        return self._total

    @property
    def covered(self) -> int:
        return self._covered

    def stage(self, source_paths: Iterable[str]):
        self._pending += sum(path in self._source_paths for path in source_paths)

    def discard_pending(self):
        self._pending = 0

    def commit_pending(self) -> ImageCoverageUpdate:
        self._covered += self._pending
        self._pending = 0
        completed_epochs = 0
        if self.total > 0:
            completed_epochs, self._covered = divmod(self._covered, self.total)

        return ImageCoverageUpdate(
            completed_epochs=completed_epochs,
            covered=self.total if completed_epochs else self._covered,
            total=self.total,
        )

    def record(self, source_paths: Iterable[str]) -> ImageCoverageUpdate:
        self.stage(source_paths)
        return self.commit_pending()
