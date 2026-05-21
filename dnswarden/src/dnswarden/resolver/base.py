"""Base resolver interface."""

from abc import ABC, abstractmethod
from dnslib import DNSRecord


class BaseResolver(ABC):
    """Abstract base resolver.

    All resolvers implement this interface.
    The resolver pipeline chains multiple resolvers.
    """

    @abstractmethod
    def resolve(self, request, client_addr):
        """Resolve DNS query and return response.

        Args:
            request: DNSRecord containing the query
            client_addr: Tuple (ip, port) of client

        Returns:
            DNSRecord: Response to send back
        """
        pass

    def can_resolve(self, request):
        """Check if this resolver can handle the query.

        Override to implement conditional resolution.

        Args:
            request: DNSRecord containing the query

        Returns:
            bool: True if this resolver can answer
        """
        return True


class ChainedResolver(BaseResolver):
    """Chain multiple resolvers together."""

    def __init__(self, *resolvers):
        self.resolvers = list(resolvers)

    def resolve(self, request, client_addr):
        """Resolve by chaining through resolvers."""
        for resolver in self.resolvers:
            if resolver.can_resolve(request):
                response = resolver.resolve(request, client_addr)
                if response:
                    return response
        return None

    def add(self, resolver):
        """Add resolver to chain."""
        self.resolvers.append(resolver)
