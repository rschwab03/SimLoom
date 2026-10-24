import ctypes


class MessageBus:
    """Python view of the C++ MessageBus singleton, via the C API in message_bus.hpp."""

    def __init__(self, lib: ctypes.CDLL):
        self._lib = lib

        self._lib.bus_get.argtypes = [ctypes.c_char_p, ctypes.c_double]
        self._lib.bus_get.restype = ctypes.c_double
        self._lib.bus_has.argtypes = [ctypes.c_char_p]
        self._lib.bus_has.restype = ctypes.c_int
        self._lib.bus_publish.argtypes = [ctypes.c_char_p, ctypes.c_double]
        self._lib.bus_publish.restype = None
        self._lib.bus_keys.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self._lib.bus_keys.restype = ctypes.c_size_t

    def get(self, key: str, default: float = 0.0) -> float:
        return self._lib.bus_get(key.encode(), default)

    def has(self, key: str) -> bool:
        return bool(self._lib.bus_has(key.encode()))

    def publish(self, key: str, value: float) -> None:
        self._lib.bus_publish(key.encode(), value)

    def keys(self) -> list[str]:
        """All published keys, sorted."""
        size = self._lib.bus_keys(None, 0)
        buf = ctypes.create_string_buffer(size + 1)
        self._lib.bus_keys(buf, size + 1)
        text = buf.value.decode()
        return sorted(text.split("\n")) if text else []
