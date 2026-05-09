import argparse
from pathlib import Path

from common import DEFAULT_RESUME_PATH, assert_status, client, print_json
from sample_data import SAMPLE_JOB


def main() -> None:
    parser = argparse.ArgumentParser(description="端到端测试：创建岗位 -> 上传简历 -> 修正 -> 评分 -> 状态流转")
    parser.add_argument("--file", default=str(DEFAULT_RESUME_PATH), help="简历文件路径")
    parser.add_argument("--status", default="pending_contact", help="最终候选人状态")
    args = parser.parse_args()

    resume_path = Path(args.file)
    if not resume_path.exists():
      raise FileNotFoundError(f"Resume file not found: {resume_path}")

    with client() as http:
        create_response = http.post("/api/jobs", json=SAMPLE_JOB)
        assert_status(create_response, 201)
        job = create_response.json()
        print_json("1 created job", job)

        with resume_path.open("rb") as file_obj:
            upload_response = http.post(
                f"/api/jobs/{job['id']}/resumes/upload",
                files={"file": (resume_path.name, file_obj, "application/octet-stream")},
            )
        assert_status(upload_response, 201)
        upload_result = upload_response.json()
        print_json("2 upload result", upload_result)

        if not upload_result.get("candidate"):
            raise RuntimeError(f"解析失败，无法继续端到端流程：{upload_result['resume_file'].get('parse_error')}")

        candidate = upload_result["candidate"]
        candidate_id = candidate["id"]

        update_response = http.patch(
            f"/api/candidates/{candidate_id}",
            json={
                "name": candidate.get("name") or "测试候选人",
                "city": candidate.get("city") or "广州",
                "skills": sorted(set((candidate.get("skills") or []) + ["Python", "SQL", "FastAPI"])),
            },
        )
        assert_status(update_response, 200)
        print_json("3 updated candidate", update_response.json())

        match_response = http.post(f"/api/jobs/{job['id']}/candidates/{candidate_id}/match")
        assert_status(match_response, 200)
        print_json("4 match", match_response.json())

        status_response = http.patch(
            f"/api/jobs/{job['id']}/candidates/{candidate_id}/status",
            json={"status": args.status},
        )
        assert_status(status_response, 200)
        print_json("5 status", status_response.json())

        list_response = http.get(f"/api/jobs/{job['id']}/candidates")
        assert_status(list_response, 200)
        print_json("6 candidates", list_response.json())

        print(f"\nJOB_ID={job['id']}")
        print(f"CANDIDATE_ID={candidate_id}")


if __name__ == "__main__":
    main()
