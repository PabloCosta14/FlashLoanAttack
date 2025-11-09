from copy import deepcopy
from typing import Iterable, Callable, Optional
import traceback

class TransactionError(Exception):
    pass

class Transaction:
    def __init__(
        self,
        objects: Iterable[object],
        name: Optional[str] = None,
        pre_check: Optional[Callable[[], bool]] = None,
        post_check: Optional[Callable[[], bool]] = None,
        on_commit: Optional[Callable[[dict, dict], None]] = None,
        logger: Optional[Callable[[str], None]] = None,
    ):
        self.objects = list(objects)
        self.name = name or "tx"
        self.pre_check = pre_check
        self.post_check = post_check
        self.on_commit = on_commit
        # logger is kept for compatibility but not used for lifecycle messages to avoid noisy output
        self.logger = logger
        self._snapshots = {}

    def __enter__(self):
        # take snapshots of __dict__ for each object
        self._snapshots = {id(obj): deepcopy(obj.__dict__) for obj in self.objects}
        # no lifecycle prints to keep output clean
        if self.pre_check and not self.pre_check():
            self._rollback()
            raise TransactionError(f"Pre-check failed for transaction {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            # exception inside tx: rollback and propagate exception
            self._rollback()
            # do not print stack here to keep output minimal; propagate
            return False  # re-raise exception
        # run post_check if provided
        if self.post_check and not self.post_check():
            self._rollback()
            raise TransactionError(f"Post-check failed for transaction {self.name}")
        # commit: compute deltas for summary if requested
        if self.on_commit:
            try:
                before = {id(obj): deepcopy(self._snapshots.get(id(obj), {})) for obj in self.objects}
                after = {id(obj): deepcopy(obj.__dict__) for obj in self.objects}
                # call the on_commit callback with (before, after)
                self.on_commit(before, after)
            except Exception:
                # ignore on_commit errors to avoid breaking the simulation
                pass
        return False  # normal exit

    def _rollback(self):
        # restore snapshots
        for obj in self.objects:
            snap = self._snapshots.get(id(obj))
            if snap is not None:
                obj.__dict__.clear()
                obj.__dict__.update(deepcopy(snap))
