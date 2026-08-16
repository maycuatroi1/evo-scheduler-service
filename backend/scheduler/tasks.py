from celery import shared_task

from scheduler.models import Schedule, SolveJob
from scheduler.solver.engine import DEFAULT_MAX_TIME_SECONDS, DEFAULT_SEED

PHASE_BUILDING_MODEL = SolveJob.Phase.BUILDING_MODEL
PHASE_SOLVING = SolveJob.Phase.SOLVING
PHASE_POST_PROCESSING = SolveJob.Phase.POST_PROCESSING


def _save_job(job, **fields):
    for key, value in fields.items():
        setattr(job, key, value)
    job.save(update_fields=list(fields.keys()) + ["updated_at"])


def _metrics(result) -> dict:
    return {
        "tier_mode": result.tier_mode,
        "conflicts": len(result.violations),
        "violations": [str(v) for v in result.violations],
        "diagnostics": list(getattr(result, "diagnostics", []) or []),
        "num_assignments": len(result.assignments),
        "tier_results": [
            {
                "tier": tr.tier,
                "status": tr.status,
                "objective_value": tr.objective_value,
                "num_sessions": tr.num_sessions,
                "num_assignments": len(tr.assignments),
            }
            for tr in result.tier_results
        ],
    }


@shared_task(bind=True, name="scheduler.solve_schedule")
def solve_schedule(self, schedule_id, config=None):
    config = dict(config or {})
    job = None
    job_id = config.get("solve_job_id")
    if job_id:
        job = SolveJob.objects.filter(id=job_id).first()

    schedule = Schedule.objects.select_related("tenant").filter(
        id=schedule_id
    ).first()
    if schedule is None:
        if job is not None:
            _save_job(
                job,
                status=SolveJob.Status.FAILED,
                phase=None,
                progress=100,
                error="schedule not found",
            )
        return {"status": "failed", "error": "schedule not found"}
    if job is None:
        job = SolveJob.objects.create(
            tenant=schedule.tenant, schedule=schedule
        )

    try:
        _save_job(
            job,
            status=SolveJob.Status.SOLVING,
            phase=PHASE_BUILDING_MODEL,
            progress=10,
            error="",
        )
        schedule.status = Schedule.Status.SOLVING
        schedule.objective_value = None
        schedule.save(update_fields=["status", "objective_value"])

        _save_job(job, phase=PHASE_SOLVING, progress=50)

        from scheduler.solver.orchestrator import orchestrate

        result = orchestrate(
            schedule,
            max_time_seconds=float(
                config.get("max_time_seconds") or DEFAULT_MAX_TIME_SECONDS
            ),
            seed=int(config.get("seed") or DEFAULT_SEED),
            verbose=bool(config.get("verbose", False)),
        )

        _save_job(job, phase=PHASE_POST_PROCESSING, progress=85)
        metrics = _metrics(result)

        if result.status == Schedule.Status.SOLVED:
            _save_job(
                job,
                status=SolveJob.Status.SOLVED,
                phase=None,
                progress=100,
                objective_value=float(result.objective_value or 0.0),
                metrics_json=metrics,
                error="",
            )
        else:
            message = (
                "; ".join(str(v) for v in result.violations[:5])
                or "solve failed"
            )
            _save_job(
                job,
                status=SolveJob.Status.FAILED,
                phase=None,
                progress=100,
                objective_value=None,
                metrics_json=metrics,
                error=message,
            )
    except Exception as exc:
        _save_job(
            job,
            status=SolveJob.Status.FAILED,
            phase=None,
            progress=100,
            error=str(exc),
        )
        return {
            "solve_job_id": str(job.id),
            "status": job.status,
            "error": str(exc),
        }

    return {
        "solve_job_id": str(job.id),
        "schedule_id": schedule.id,
        "status": job.status,
        "objective_value": job.objective_value,
    }
