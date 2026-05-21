"""DNS-over-HTTPS (RFC 8484) proxy/forwarder."""

import base64
import logging
from dnslib import DNSRecord, RCODE
import httpx

logger = logging.getLogger(__name__)


class DoHResolver:
    """DNS-over-HTTPS proxy/forwarder.

    Supports RFC 8484:
    - POST: Binary DNS message in body
    - GET: base64url-encoded in ?dns= parameter
    """

    def __init__(self, upstream_url="https://cloudflare-dns.com/dns-query", timeout=10.0):
        self.upstream_url = upstream_url
        self.timeout = timeout
        self.client = httpx.Client(
            http2=True, timeout=timeout, headers={"Accept": "application/dns-message"}
        )

    def resolve(self, request, client_addr=None):
        """Forward DNS query via DoH."""
        wire = request.pack()

        response = self._do_post(wire)
        if response:
            return DNSRecord.parse(response)

        response = self._do_get(request)
        if response:
            return DNSRecord.parse(response)

        return self._servfail(request)

    def _do_post(self, wire):
        """POST method with binary DNS message."""
        try:
            resp = self.client.post(
                self.upstream_url, content=wire, headers={"Content-Type": "application/dns-message"}
            )
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            logger.debug(f"DoH POST failed: {e}")
        return None

    def _do_get(self, request):
        """GET method with base64url encoding."""
        try:
            wire = request.pack()
            b64 = base64.urlsafe_b64encode(wire).decode().rstrip("=")
            resp = self.client.get(self.upstream_url, params={"dns": b64})
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            logger.debug(f"DoH GET failed: {e}")
        return None

    def _servfail(self, request):
        """Return SERVFAIL response."""
        reply = request.reply()
        reply.header.rcode = RCODE.SERVFAIL
        return reply

    def close(self):
        """Close HTTP client."""
        self.client.close()
