#!/usr/bin/env python3
"""CLI for Shock Index Calculator."""
import argparse
import json
import sys

from shock_index import calculate_shock_index, process_csv


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="shock-index-calculator",
        description="Shock Index (SI) & Modified Shock Index (MSI) Calculator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single calculation
    single = subparsers.add_parser("single", help="Single patient calculation")
    single.add_argument("--hr", type=float, required=True, help="Heart rate (bpm)")
    single.add_argument("--sbp", type=float, required=True, help="Systolic BP (mmHg)")
    single.add_argument("--dbp", type=float, default=None, help="Diastolic BP (mmHg)")
    single.add_argument("--age", type=float, default=None, help="Age (years)")
    single.add_argument("--sex", default=None, help="Sex (male/female)")

    # Batch processing
    batch = subparsers.add_parser("batch", help="Batch process CSV")
    batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    batch.add_argument("-o", "--output", default="results.csv", help="Output CSV path")

    # Audit command
    audit = subparsers.add_parser("audit", help="Run audit task")
    audit.add_argument("--task-id", required=True, help="Task identifier")

    # Chat command
    chat = subparsers.add_parser("chat", help="Supervisory chat")
    chat.add_argument("query", nargs="+", help="Query text")

    # Verify audit command
    subparsers.add_parser("verify-audit", help="Verify audit trail integrity")

    args = parser.parse_args(argv)

    if args.command == "single":
        result = calculate_shock_index(
            args.hr, args.sbp,
            dbp=args.dbp, age=args.age, sex=args.sex,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "batch":
        results = process_csv(args.input, args.output)
        print(f"Processed {len(results)} records -> {args.output}")
        return 0

    if args.command == "audit":
        from agents.supervisor import SystemSupervisor
        from agents.models import SystemTaskPayload
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier="CLI-AUDIT",
            primary_metric=10.0,
            secondary_metric=2.0,
            status_descriptor="NOMINAL",
        )
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))
        return 0

    if args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"response": response}, indent=2))
        return 0

    if args.command == "verify-audit":
        from agents.base import AuditLogger
        verified = AuditLogger.verify_integrity()
        trail = AuditLogger.get_trail()
        print(json.dumps({"verified": verified, "blocks": len(trail)}, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
