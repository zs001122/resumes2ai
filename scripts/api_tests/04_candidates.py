import argparse

from common import assert_status, client, print_json


def main() -> None:
    parser = argparse.ArgumentParser(description="测试候选人列表、详情、修正、评分和状态流转")
    parser.add_argument("--job-id", required=True, help="岗位 ID")
    parser.add_argument("--candidate-id", help="候选人 ID；不传则使用该岗位列表第一个候选人")
    parser.add_argument("--status", default="pending_contact", help="要更新的候选人状态")
    args = parser.parse_args()

    with client() as http:
        list_response = http.get(f"/api/jobs/{args.job_id}/candidates")
        assert_status(list_response, 200)
        candidates = list_response.json()
        print_json("candidate list", candidates)

        candidate_id = args.candidate_id
        if not candidate_id:
            if not candidates:
                raise RuntimeError("该岗位暂无候选人，请先运行 03_upload_resume.py")
            candidate_id = candidates[0]["candidate"]["id"]

        detail_response = http.get(f"/api/jobs/{args.job_id}/candidates/{candidate_id}")
        assert_status(detail_response, 200)
        print_json("candidate detail", detail_response.json())

        review_response = http.get(f"/api/jobs/{args.job_id}/candidates/{candidate_id}/review")
        assert_status(review_response, 200)
        review = review_response.json()
        print_json("candidate review", {
            "candidate": review["candidate"],
            "resume_file": review["resume_file"],
            "field_extractions_count": len(review["field_extractions"]),
            "correction_logs_count": len(review["correction_logs"]),
        })

        update_response = http.patch(
            f"/api/candidates/{candidate_id}",
            json={
                "city": review["candidate"].get("city") or "广州",
                "skills": sorted(set((review["candidate"].get("skills") or []) + ["Python", "SQL"])),
            },
        )
        assert_status(update_response, 200)
        print_json("updated candidate", update_response.json())

        match_response = http.post(f"/api/jobs/{args.job_id}/candidates/{candidate_id}/match")
        assert_status(match_response, 200)
        print_json("candidate match", match_response.json())

        status_response = http.patch(
            f"/api/jobs/{args.job_id}/candidates/{candidate_id}/status",
            json={"status": args.status},
        )
        assert_status(status_response, 200)
        print_json("updated status", status_response.json())


if __name__ == "__main__":
    main()
