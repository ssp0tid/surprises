"""Tests for capture module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from packetsniffer.capture import capture_packets, start_capture


class TestCapturePackets:
    @patch("packetsniffer.capture.sniff")
    def test_capture_packets_default(self, mock_sniff):
        mock_packets = [Mock(), Mock()]
        mock_sniff.return_value = mock_packets

        result = capture_packets()

        mock_sniff.assert_called_once()
        call_kwargs = mock_sniff.call_args.kwargs
        assert call_kwargs["iface"] is None
        assert call_kwargs["filter"] is None
        assert call_kwargs["count"] is None
        assert call_kwargs["store"] is False
        assert result == mock_packets

    @patch("packetsniffer.capture.sniff")
    def test_capture_packets_with_args(self, mock_sniff):
        mock_packets = [Mock()]
        mock_sniff.return_value = mock_packets

        result = capture_packets(
            iface="eth0",
            bpf_filter="tcp port 80",
            count=100,
            store=True,
        )

        call_kwargs = mock_sniff.call_args.kwargs
        assert call_kwargs["iface"] == "eth0"
        assert call_kwargs["filter"] == "tcp port 80"
        assert call_kwargs["count"] == 100
        assert call_kwargs["store"] is True


class TestStartCapture:
    @patch("packetsniffer.capture.sniff")
    def test_start_capture(self, mock_sniff):
        mock_sniff.return_value = None
        stop_event = Mock()
        stop_event.is_set.return_value = False
        packet_handler = Mock()

        start_capture("eth0", "tcp", packet_handler, stop_event)

        mock_sniff.assert_called_once()
        call_kwargs = mock_sniff.call_args.kwargs
        assert call_kwargs["iface"] == "eth0"
        assert call_kwargs["filter"] == "tcp"
        assert call_kwargs["prn"] == packet_handler
