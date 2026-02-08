from pathlib import Path
from . import Handler


def get_filesize(file: Path) -> int:
    """Return size of a file."""
    return file.stat()[6]


class RotatingFileHandler(Handler):
    """A rotating file handler like RotatingFileHandler.

    Compatible with CPythons `logging.handlers.RotatingFileHandler` class.
    """

    def __init__(self, filename: Path, max_bytes: int= 0, backup_count: int = 0):
        super().__init__()
        self.file: Path = filename
        self.max_bytes: int = max_bytes
        self.backup_count: int = backup_count

        try:
            self._counter = get_filesize(self.file)
        except OSError:
            self._counter = 0

    def emit(self, record):
        """Write to file."""
        msg = self.formatter.format(record)
        s_len = len(msg)

        if self.max_bytes and self.backup_count and self._counter + s_len > self.max_bytes:
            # remove the last backup file if it is there
            Path(f"{self.file}.{self.backup_count}").unlink()

            for i in range(self.backup_count - 1, 0, -1):
                if i < self.backup_count:
                    Path(f"{self.file}.{i}").rename(target=f"{self.file}.{i + 1}")
            try:
                self.file.rename(f"{self.file}.1")
            except OSError:
                pass
            self._counter = 0

        with open(self.file, "a") as f:
            f.write(msg + "\n")

        self._counter += s_len
