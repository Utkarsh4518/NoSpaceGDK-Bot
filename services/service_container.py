"""Dependency injection container for the NoSpaceFGK bot.

Provides lightweight service registration, singleton management, type-safe lookup,
and lazy instantiation without external libraries.
"""

from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")


class ServiceContainer:
    """Registry container storing and resolving application service dependencies."""

    def __init__(self) -> None:
        """Initialize the container registry."""
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}
        self._singletons: Dict[Type[Any], Any] = {}

    def register(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a service factory.

        Args:
            service_type: The class or type to register.
            factory: A callable that returns an instance of the service.
        """
        self._factories[service_type] = factory

    def get(self, service_type: Type[T]) -> T:
        """Retrieve a service instance (lazily initialized singleton).

        Args:
            service_type: The class/type to resolve.

        Returns:
            The resolved singleton instance.

        Raises:
            KeyError: If the service type is not registered.
        """
        if service_type in self._singletons:
            return self._singletons[service_type]

        if service_type not in self._factories:
            raise KeyError(f"Service '{service_type.__name__}' is not registered in the container.")

        factory = self._factories[service_type]
        instance = factory()
        self._singletons[service_type] = instance
        return instance
