import argparse

from common import assert_status, client, print_json
from sample_data import SAMPLE_JOB


def main() -> None:
    parser = argparse.ArgumentParser(description="测试岗位模块：JD 解析、创建、列表、详情")
    parser.add_argument("--close", action="store_true", help="创建后顺便关闭岗位")
    args = parser.parse_args()

    with client() as http:
        parse_response = http.post(
            "/api/jobs/parse-jd",
            json={
                "title": SAMPLE_JOB["title"],
                "jd": SAMPLE_JOB["jd"],
                "experience_required": SAMPLE_JOB["experience_required"],
                "education_required": SAMPLE_JOB["education_required"],
            },
        )
        assert_status(parse_response, 200)
        print_json("parse jd", parse_response.json())

        create_response = http.post("/api/jobs", json=SAMPLE_JOB)
        assert_status(create_response, 201)
        job = create_response.json()
        print_json("created job", job)

        list_response = http.get("/api/jobs")
        assert_status(list_response, 200)
        print_json("job list first 3", list_response.json()[:3])

        detail_response = http.get(f"/api/jobs/{job['id']}")
        assert_status(detail_response, 200)
        print_json("job detail", detail_response.json())

        if args.close:
            close_response = http.post(f"/api/jobs/{job['id']}/close")
            assert_status(close_response, 200)
            print_json("closed job", close_response.json())

        print(f"\nJOB_ID={job['id']}")


if __name__ == "__main__":
    main()
