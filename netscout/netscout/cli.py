import argparse
import asyncio
import sys
from pathlib import Path

from netscout.discovery.oui_lookup import OUILookup
from netscout.discovery.ports import parse_port_spec
from netscout.scanner.scheduler import ScanScheduler
from netscout.utils.network import get_local_subnet, validate_subnet
from netscout.output.formatter import OutputFormatter
from netscout.output.json_exporter import export_json
from netscout.output.csv_exporter import export_csv
from netscout.utils.logging import setup_logging
from netscout.utils.errors import NetworkScoutError


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netscout",
        description="Network Scanner & Device Discovery Tool",
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Target subnet (e.g., 192.168.1.0/24) or IP range",
    )

    parser.add_argument(
        "-p",
        "--ports",
        default="common",
        help="Ports to scan: 'common', 'top100', or range (e.g., '1-1024')",
    )

    parser.add_argument(
        "--skip-arp",
        action="store_true",
        help="Skip ARP discovery, use only port scan",
    )

    parser.add_argument(
        "--skip-hostname",
        action="store_true",
        help="Skip hostname resolution",
    )

    parser.add_argument(
        "--skip-oui",
        action="store_true",
        help="Skip MAC vendor lookup",
    )

    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=100,
        help="Max concurrent port scans (default: 100)",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=2.0,
        help="Timeout for port checks in seconds (default: 2.0)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file (JSON or CSV based on extension)",
    )

    parser.add_argument(
        "--format",
        choices=["json", "csv", "table"],
        default="table",
        help="Output format",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv, -vvv)",
    )

    parser.add_argument(
        "--update-oui",
        action="store_true",
        help="Update OUI database before scanning",
    )

    return parser


async def update_oui() -> None:
    oui = OUILookup()
    oui.download()
    print("OUI database updated successfully")


async def run_scan(args) -> None:
    target = args.target

    if not target:
        target = get_local_subnet()
        if not target:
            print(
                "Error: Could not determine local subnet. Please specify target.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Using auto-detected subnet: {target}")

    if not validate_subnet(target):
        print(f"Error: Invalid subnet format: {target}", file=sys.stderr)
        sys.exit(1)

    ports = parse_port_spec(args.ports)

    scheduler = ScanScheduler(
        concurrency=args.concurrency,
        timeout=args.timeout,
        skip_hostname=args.skip_hostname,
        skip_oui=args.skip_oui,
        use_tcp_fallback=args.skip_arp,
    )

    formatter = OutputFormatter(verbose=args.verbose)

    devices = await scheduler.scan_all(target, ports)

    if args.format == "table":
        formatter.display_devices(devices)
        formatter.display_summary(devices)
    elif args.format == "json" and args.output:
        export_json(devices, args.output)
        print(f"Results exported to {args.output}")
    elif args.format == "csv" and args.output:
        export_csv(devices, args.output)
        print(f"Results exported to {args.output}")


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        if args.update_oui:
            asyncio.run(update_oui())
        else:
            asyncio.run(run_scan(args))
    except NetworkScoutError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nScan interrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
