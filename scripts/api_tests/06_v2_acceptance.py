import argparse
import tempfile
from pathlib import Path

from common import assert_status, client, print_json
from sample_data import SAMPLE_JOB


RESUME_ONE = """后端开发-陈晓明
电话：13800138001
邮箱：chen@example.com
城市：广州
本科，5 年工作经验
技能：Python FastAPI PostgreSQL Redis Docker React
项目经历：负责招聘系统 API、数据处理和自动化脚本。
"""

RESUME_TWO = """前端开发-李思雨
电话：13800138002
邮箱：li@example.com
城市：深圳
硕士，3 年工作经验
技能：TypeScript React Next.js Node SQL
项目经历：负责企业工作台、筛选列表和交互体验优化。
"""


def upload_file(http, job_id: str, path: Path, content_type: str = "text/plain") -> dict:
    with path.open("rb") as file_obj:
        response = http.post(
            f"/api/jobs/{job_id}/resumes/upload",
            files={"file": (path.name, file_obj, content_type)},
        )
    assert_status(response, 201)
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="V2 验收流程：工作台、上传队列、筛选、解释、时间线、人才库和岗位增强")
    parser.add_argument("--keep-files", action="store_true", help="保留临时 TXT/PDF 样例文件")
    args = parser.parse_args()

    temp_dir_ctx = None if args.keep_files else tempfile.TemporaryDirectory()
    temp_dir = Path(tempfile.mkdtemp()) if args.keep_files else Path(temp_dir_ctx.name)
    first_resume = temp_dir / "后端开发-陈晓明.txt"
    second_resume = temp_dir / "前端开发-李思雨.txt"
    broken_resume = temp_dir / "解析失败样例.pdf"
    first_resume.write_text(RESUME_ONE, encoding="utf-8")
    second_resume.write_text(RESUME_TWO, encoding="utf-8")
    broken_resume.write_bytes(b"not a real pdf")

    with client() as http:
        dashboard_before = http.get("/api/dashboard")
        assert_status(dashboard_before, 200)
        print_json("1 dashboard before", dashboard_before.json())

        create_response = http.post("/api/jobs", json=SAMPLE_JOB)
        assert_status(create_response, 201)
        job = create_response.json()
        job_id = job["id"]
        print_json("2 created job", job)

        first_upload = upload_file(http, job_id, first_resume)
        second_upload = upload_file(http, job_id, second_resume)
        failed_upload = upload_file(http, job_id, broken_resume, "application/pdf")
        print_json("3 first upload", first_upload)
        print_json("4 second upload", second_upload)
        print_json("5 failed upload task source", failed_upload)

        task_response = http.get(f"/api/jobs/{job_id}/upload-tasks")
        assert_status(task_response, 200)
        tasks = task_response.json()
        print_json("6 upload tasks", tasks)
        if not any(task["parse_status"] == "failed" for task in tasks):
            raise RuntimeError("expected at least one failed parse task")

        retry_response = http.post(f"/api/jobs/{job_id}/upload-tasks/retry-failed")
        assert_status(retry_response, 200)
        retry_payload = retry_response.json()
        print_json("7 retry failed tasks", retry_payload)
        for task in retry_payload:
            if task["parse_status"] == "success" and task["match_status"] != "success":
                raise RuntimeError("retry parsed a resume successfully but did not generate a match")

        candidates_response = http.get(f"/api/jobs/{job_id}/candidates?skill=React&min_score=1")
        assert_status(candidates_response, 200)
        candidates = candidates_response.json()
        print_json("8 filtered candidates", candidates)
        if len(candidates) < 2:
            raise RuntimeError("expected two parsed candidates")

        candidate_id = candidates[0]["candidate"]["id"]
        candidate_ids = [item["candidate"]["id"] for item in candidates]

        bulk_status_response = http.post(
            f"/api/jobs/{job_id}/candidates/bulk-status",
            json={"candidate_ids": [*candidate_ids, "missing-candidate"], "status": "pending_contact"},
        )
        assert_status(bulk_status_response, 200)
        bulk_status = bulk_status_response.json()
        print_json("9 bulk status partial result", bulk_status)
        if len(bulk_status) != len(candidate_ids):
            print(f"partial bulk notice: processed {len(bulk_status)} / {len(candidate_ids) + 1}")

        explanations_response = http.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/match/explanations")
        assert_status(explanations_response, 200)
        print_json("10 match explanations", explanations_response.json())

        note_response = http.post(
            f"/api/jobs/{job_id}/candidates/{candidate_id}/notes",
            json={"candidate_id": candidate_id, "job_id": job_id, "content": "V2 验收备注", "created_by": "acceptance"},
        )
        assert_status(note_response, 200)
        print_json("11 note", note_response.json())

        timeline_response = http.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/timeline")
        assert_status(timeline_response, 200)
        print_json("12 timeline", timeline_response.json())

        archive_response = http.post(f"/api/candidates/{candidate_id}/talent-pool", json={"job_id": job_id})
        assert_status(archive_response, 200)
        print_json("13 add to talent pool", archive_response.json())

        tag_response = http.post(f"/api/candidates/{candidate_id}/tags", json={"name": "V2验收"})
        assert_status(tag_response, 200)
        print_json("14 tag candidate", tag_response.json())

        talent_pool_response = http.get("/api/talent-pool/candidates?query=React")
        assert_status(talent_pool_response, 200)
        print_json("15 talent pool search", talent_pool_response.json())

        funnel_response = http.get(f"/api/jobs/{job_id}/funnel")
        quality_response = http.get(f"/api/jobs/{job_id}/jd-quality")
        assert_status(funnel_response, 200)
        assert_status(quality_response, 200)
        print_json("16 funnel", funnel_response.json())
        print_json("17 jd quality", quality_response.json())

        copy_response = http.post(f"/api/jobs/{job_id}/copy")
        pause_response = http.post(f"/api/jobs/{job_id}/pause")
        reopen_response = http.post(f"/api/jobs/{job_id}/reopen")
        close_response = http.post(f"/api/jobs/{job_id}/close")
        for response in (copy_response, pause_response, reopen_response, close_response):
            assert_status(response, (200, 201))
        print_json("18 copied job", copy_response.json())
        print_json("19 final closed job", close_response.json())

        print(f"\nV2_ACCEPTANCE_JOB_ID={job_id}")
        print(f"V2_ACCEPTANCE_CANDIDATE_ID={candidate_id}")

    if args.keep_files:
        print(f"sample files kept at: {temp_dir}")
    elif temp_dir_ctx:
        temp_dir_ctx.cleanup()


if __name__ == "__main__":
    main()
