#!/usr/bin/env python3
"""CertCheck - SSL Certificate Checker CLI."""
import ssl
import socket
import json
import datetime
import argparse
import sys
import os
from typing import Dict, Any

def check_cert(domain: str, port: int = 443, timeout: int = 10) -> Dict[str, Any]:
    """Check SSL certificate for a domain."""
    try:
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
        not_after = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        days_remaining = (not_after - datetime.datetime.now()).days
        issuer = dict(x[0] for x in cert.get('issuer', []))
        subject = dict(x[0] for x in cert.get('subject', []))
        
        return {
            'domain': domain,
            'port': port,
            'valid': True,
            'issuer': issuer.get('organizationName', 'Unknown'),
            'subject': subject.get('commonName', domain),
            'not_before': cert.get('notBefore'),
            'not_after': cert.get('notAfter'),
            'days_remaining': days_remaining,
            'serial_number': cert.get('serialNumber'),
        }
    except socket.timeout:
        return {'domain': domain, 'port': port, 'valid': False, 'error': 'Connection timeout'}
    except socket.gaierror as e:
        return {'domain': domain, 'port': port, 'valid': False, 'error': 'DNS error'}
    except ConnectionRefusedError:
        return {'domain': domain, 'port': port, 'valid': False, 'error': 'Connection refused'}
    except ssl.SSLError as e:
        return {'domain': domain, 'port': port, 'valid': False, 'error': 'SSL error'}
    except Exception as e:
        return {'domain': domain, 'port': port, 'valid': False, 'error': str(e)}

def get_color(days: int) -> str:
    """Get color code based on days remaining."""
    if days < 0:
        return "\033[91m"  # Red - expired
    elif days < 30:
        return "\033[93m"  # Yellow - expiring soon
    return "\033[92m"  # Green - valid

RESET = "\033[0m"

def format_result(result: Dict[str, Any]) -> str:
    """Format a single certificate check result."""
    if not result['valid']:
        return "X " + result['domain'] + ":" + str(result['port']) + " - " + result.get('error', 'Unknown error')
    
    days = result['days_remaining']
    color = get_color(days)
    
    if days < 0:
        status = color + "! EXPIRED " + str(abs(days)) + " days ago" + RESET
    elif days < 30:
        status = color + "Expires in " + str(days) + " days" + RESET
    else:
        status = color + str(days) + " days remaining" + RESET
    
    out = "V " + result['domain'] + ":" + str(result['port']) + "\n"
    out += "  Issuer: " + result['issuer'] + "\n"
    out += "  Subject: " + result['subject'] + "\n"
    out += "  Valid: " + result['not_before'] + " to " + result['not_after'] + "\n"
    out += "  " + status
    return out

def main():
    parser = argparse.ArgumentParser(description='CertCheck - SSL Certificate Checker')
    parser.add_argument('domains', nargs='*', help='Domains to check')
    parser.add_argument('-p', '--port', type=int, default=443, help='Port to check (default: 443)')
    parser.add_argument('-w', '--warn-days', type=int, default=30, help='Warn if expiring within N days (default: 30)')
    parser.add_argument('-o', '--output', help='Export to JSON file')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    
    args = parser.parse_args()
    
    if not args.domains:
        parser.print_help()
        sys.exit(1)
    
    results = []
    for domain in args.domains:
        result = check_cert(domain, args.port)
        results.append(result)
        print(format_result(result))
        print()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print("Results exported to " + args.output)
    
    # Check for warnings
    warnings = [r for r in results if r.get('valid') and r['days_remaining'] < args.warn_days]
    if warnings:
        print("\n! " + str(len(warnings)) + " certificate(s) expiring within " + str(args.warn_days) + " days!")

if __name__ == '__main__':
    main()
