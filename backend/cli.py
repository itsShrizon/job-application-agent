import sys
import argparse
import logging

from app.core.config import settings


def setup_logging():
    log_dir = settings.logs_path
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "agent.log"),
            logging.StreamHandler(),
        ],
    )


def handle_jobfind(args):
    from app.services import job_service

    # Route special sub-commands
    if args.deadline == "continue":
        # python cli.py jobfind continue prev <new_limit>
        # positionals: deadline=continue, location=prev, role=<new_limit>
        try:
            new_limit = int(args.role or args.limit)
        except (TypeError, ValueError):
            new_limit = int(args.limit) if args.limit else 1000
        result = job_service.continue_scrape(new_limit)
        print(f"Continue scrape complete: {result['new_count']} new, "
              f"{result['duplicate_count']} duplicates, {result['total_count']} total")
        return

    if args.deadline == "deadline_review":
        result = job_service.deadline_review()
        print(f"Deadline review: {result['expired_count']} expired, {result['active_count']} active")
        return

    if args.deadline not in ("24h", "7d", "30d", "anytime"):
        print(f"ERROR: invalid deadline '{args.deadline}'. Choose from: 24h, 7d, 30d, anytime",
              file=sys.stderr)
        sys.exit(1)

    result = job_service.scrape_jobs(
        deadline=args.deadline,
        location=args.location,
        role=args.role,
        work_type=args.work_type,
        limit=args.limit,
    )
    print(f"Scrape complete: {result['new_count']} new, "
          f"{result['duplicate_count']} duplicates, {result['total_count']} total")


def handle_jobsort(args):
    from app.services import scoring_service
    result = scoring_service.score_all_unscored()
    print(f"Scored {result['scored_count']} jobs")
    if result["top_5"]:
        print("\nTop 5 jobs:")
        for i, job in enumerate(result["top_5"], 1):
            score = job.get("relevance_score", "N/A")
            print(f"  {i}. [{job.get('job_id', '')}] {job.get('title', '')} "
                  f"at {job.get('company_name', '')} — Score: {score}")


def handle_gitref(args):
    from app.services import github_service
    result = github_service.refresh_github()
    print(f"Fetched {result['repo_count']} repos → {result['file_path']}")


def handle_mkcv(args):
    from app.services import cv_service

    job_ref = args.job_ref
    template = args.template

    # Accept bare IDs (4CD6CA), prefixed IDs (jobid-4CD6CA), or .md files
    if job_ref.endswith(".md"):
        result = cv_service.generate_cv_from_file(file_path=job_ref, template=template)
    else:
        job_id = job_ref.replace("jobid-", "")
        result = cv_service.generate_cv(job_id=job_id, template=template)

    print(f"CV generated: {result['pdf_path']}")


def handle_mkcover(args):
    from app.services import cover_service

    job_ref = args.job_ref

    # Accept bare IDs (4CD6CA), prefixed IDs (jobid-4CD6CA), or .md files
    if job_ref.endswith(".md"):
        result = cover_service.generate_cover_from_file(file_path=job_ref)
    else:
        job_id = job_ref.replace("jobid-", "")
        result = cover_service.generate_cover(job_id=job_id)

    print(f"Cover letter generated: {result['pdf_path']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cli.py", description="Job Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # jobfind — flat positional args (avoid subparser conflict with '24h')
    # Usage:
    #   python cli.py jobfind <deadline> <location> [role] [work_type] [limit]
    #   python cli.py jobfind continue prev <new_limit>
    #   python cli.py jobfind deadline_review
    jf = subparsers.add_parser("jobfind", help="Scrape LinkedIn jobs")
    jf.add_argument("deadline", help="24h | 7d | 30d | anytime | continue | deadline_review")
    jf.add_argument("location", nargs="?", default=None, help="Location filter (e.g. Bangladesh)")
    jf.add_argument("role", nargs="?", default=None, help="Job title / keyword (optional)")
    jf.add_argument("work_type", nargs="?", default=None, help="onsite | hybrid | remote (optional)")
    jf.add_argument("limit", nargs="?", type=int, default=500, help="Max jobs to scrape")

    # jobsort
    subparsers.add_parser("jobsort", help="Score jobs by relevance")

    # gitref
    subparsers.add_parser("gitref", help="Fetch GitHub projects")

    # mkcv
    mk = subparsers.add_parser("mkcv", help="Generate CV")
    mk.add_argument("job_ref", help="jobid-XXXXXX or filename.md")
    mk.add_argument("template", choices=["t1", "t2", "t3"])

    # mkcover
    mc = subparsers.add_parser("mkcover", help="Generate cover letter")
    mc.add_argument("job_ref", help="jobid-XXXXXX or filename.md")

    return parser


def main():
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    try:
        handlers = {
            "jobfind": handle_jobfind,
            "jobsort": handle_jobsort,
            "gitref": handle_gitref,
            "mkcv": handle_mkcv,
            "mkcover": handle_mkcover,
        }
        handlers[args.command](args)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
