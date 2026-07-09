from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOM = ROOT / "demo-files" / "demo-bom.csv"
DEFAULT_BOM_V2 = ROOT / "demo-files" / "demo-bom-v2.csv"
DEFAULT_ECO_TEXT = (
    "Replace old part PN-1212 with new part PN-2212. "
    "Reason: supplier obsolescence. Effective date: 2026-08-15."
)


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def get(self, path: str) -> dict:
        return self.request("GET", path)

    def post_json(self, path: str, payload: dict) -> dict:
        return self.request(
            "POST",
            path,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def patch_json(self, path: str, payload: dict) -> dict:
        return self.request(
            "PATCH",
            path,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def upload(self, path: str, file_path: Path, category: str) -> dict:
        boundary = f"----bomtracker{int(time.time() * 1000)}"
        file_bytes = file_path.read_bytes()
        body = b"".join(
            [
                _form_field(boundary, "upload_category", category),
                _form_field(boundary, "replace_existing", "false"),
                _file_field(boundary, "file", file_path.name, file_bytes),
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
        )
        return self.request(
            "POST",
            path,
            body=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    def request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict:
        request_headers = dict(headers or {})
        csrf = self._csrf_token()
        if csrf and method not in {"GET", "HEAD", "OPTIONS"}:
            request_headers["X-CSRF-Token"] = csrf

        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=request_headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                data = response.read()
                if not data:
                    return {}
                content_type = response.headers.get("Content-Type", "")
                if "application/json" not in content_type:
                    return {"bytes": len(data), "content_type": content_type}
                return json.loads(data.decode("utf-8"))
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path} failed: {error.code} {details}") from error

    def _csrf_token(self) -> str | None:
        for cookie in self.cookie_jar:
            if cookie.name == "csrf_token":
                return cookie.value
        return None


def _form_field(boundary: str, name: str, value: str) -> bytes:
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
        f"{value}\r\n"
    ).encode("utf-8")


def _file_field(boundary: str, name: str, filename: str, content: bytes) -> bytes:
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
        "Content-Type: text/csv\r\n\r\n"
    ).encode("utf-8") + content + b"\r\n"


def wait_for_job(client: ApiClient, job_id: int) -> dict:
    for _ in range(60):
        job = client.get(f"/api/v1/jobs/{job_id}")
        if job["status"] in {"completed", "failed"}:
            if job["status"] == "failed":
                raise RuntimeError(f"Job {job_id} failed: {job.get('error_message')}")
            return job
        time.sleep(1)
    raise RuntimeError(f"Job {job_id} did not finish within 60 seconds.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a live API smoke test against an already-running backend."
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("E2E_API_BASE_URL", "http://127.0.0.1:8000"),
    )
    parser.add_argument("--bom", type=Path, default=DEFAULT_BOM)
    parser.add_argument("--bom-v2", type=Path, default=DEFAULT_BOM_V2)
    parser.add_argument(
        "--email",
        default=f"qa-{int(time.time())}@example.com",
    )
    parser.add_argument("--password", default="Phase20-password-123")
    args = parser.parse_args()

    client = ApiClient(args.base_url)
    client.get("/api/v1/health")
    client.post_json(
        "/register",
        {
            "email": args.email,
            "password": args.password,
            "full_name": "Phase 20 API Smoke",
        },
    )
    me = client.get("/me")

    bom_upload = client.upload("/api/v1/uploads", args.bom, "bom")
    bom_v2_upload = client.upload("/api/v1/uploads", args.bom_v2, "bom")
    import_job = client.post_json(
        f"/api/v1/jobs/bom-imports/from-upload/{bom_upload['id']}",
        {},
    )
    import_result = wait_for_job(client, import_job["id"])["result_json"]
    import_v2 = client.post_json(
        f"/api/v1/bom-imports/from-upload/{bom_v2_upload['id']}",
        {},
    )
    graph_job = client.post_json(
        f"/api/v1/jobs/graph/build/{bom_upload['id']}",
        {},
    )
    graph_result = wait_for_job(client, graph_job["id"])["result_json"]
    diff = client.post_json(
        "/api/v1/bom-imports/diff",
        {
            "base_import_id": import_result["bom_import_id"],
            "target_import_id": import_v2["id"],
        },
    )
    eco = client.post_json(
        "/api/v1/eco-records/parse-text",
        {"text": DEFAULT_ECO_TEXT},
    )
    approved_eco = client.post_json(
        f"/api/v1/eco-records/{eco['id']}/approve",
        {"notes": "Approved by live Phase 20 smoke test."},
    )
    report_job = client.post_json(
        "/api/v1/jobs/reports/impact-report",
        {
            "bom_upload_id": bom_upload["id"],
            "eco_record_id": approved_eco["id"],
        },
    )
    report_result = wait_for_job(client, report_job["id"])["result_json"]
    report = client.get(f"/api/v1/reports/{report_result['report_id']}")
    comment = client.post_json(
        f"/api/v1/reports/{report['id']}/comments",
        {"body": "Live smoke test comment."},
    )
    signed = client.patch_json(
        f"/api/v1/reports/{report['id']}/review",
        {
            "review_status": "signed_off",
            "assigned_user_id": me["id"],
            "signoff_notes": "Signed off by API smoke test.",
        },
    )
    csv_export = client.get(f"/api/v1/reports/{report['id']}/export.csv")
    pdf_export = client.get(f"/api/v1/reports/{report['id']}/export.pdf")

    print("Phase 20 live API smoke complete")
    print(f"user={me['email']}")
    print(f"bom_upload_id={bom_upload['id']}")
    print(f"bom_import_id={import_result['bom_import_id']}")
    print(f"graph_nodes={graph_result['node_count']}")
    print(f"diff_replacements={diff['summary']['replacement_candidate_count']}")
    print(f"eco_status={approved_eco['workflow_status']}")
    print(f"report_id={report['id']}")
    print(f"risk={report['risk_level']} score={report['risk_score']}")
    print(f"comment_id={comment['id']}")
    print(f"review_status={signed['review_status']}")
    print(f"csv_bytes={csv_export['bytes']}")
    print(f"pdf_bytes={pdf_export['bytes']}")


if __name__ == "__main__":
    main()
