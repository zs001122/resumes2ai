import argparse
from pathlib import Path

from common import DEFAULT_RESUME_PATH, assert_status, client, print_json


def main() -> None:
    parser = argparse.ArgumentParser(description="测试简历上传与解析模块")
    parser.add_argument("--job-id", required=True, help="岗位 ID")
    parser.add_argument("--file", default=str(DEFAULT_RESUME_PATH), help="简历文件路径，默认使用简历数据样例")
    args = parser.parse_args()

    resume_path = Path(args.file)
    if not resume_path.exists():
      raise FileNotFoundError(f"Resume file not found: {resume_path}")

    with client() as http:
        with resume_path.open("rb") as file_obj:
            response = http.post(
                f"/api/jobs/{args.job_id}/resumes/upload",
                files={"file": (resume_path.name, file_obj, "application/octet-stream")},
            )
        assert_status(response, 201)
        result = response.json()
        print_json("upload result", result)

        resume_file_id = result["resume_file"]["id"]
        preview_response = http.get(f"/api/resume-files/{resume_file_id}/preview")
        assert_status(preview_response, 200)
        preview = preview_response.json()
        preview["content"] = preview["content"][:800]
        print_json("resume preview first 800 chars", preview)

        if result["resume_file"]["parse_status"] != "success":
            retry_response = http.post(f"/api/resume-files/{resume_file_id}/parse")
            assert_status(retry_response, 200)
            print_json("retry parse result", retry_response.json())

        if result.get("candidate"):
            print(f"\nCANDIDATE_ID={result['candidate']['id']}")


if __name__ == "__main__":
    main()
