from dataclasses import dataclass


RESULT_TTL_HOURS = 24


@dataclass
class Job:
    job_id: int
    tenant: str
    request_key: str
    status: str = "queued"
    result: str = ""


class JobStore:
    def __init__(self):
        self.jobs = {}
        self.keys = {}

    def enqueue_once(self, tenant, request_key):
        key = (tenant, request_key)
        if key in self.keys:
            return self.jobs[self.keys[key]]
        job = Job(len(self.jobs) + 1, tenant, request_key)
        self.jobs[job.job_id] = job
        self.keys[key] = job.job_id
        return job

    def get_for_tenant(self, tenant, job_id):
        job = self.jobs.get(job_id)
        return job if job and job.tenant == tenant else None

    def complete(self, job_id, result):
        job = self.jobs[job_id]
        job.result = result
        job.status = "complete"


def render_report(rows):
    return "\n".join(",".join(str(value) for value in row) for row in rows)
