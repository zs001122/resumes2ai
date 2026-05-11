from types import SimpleNamespace

import app.api.matches as matches_api
import app.api.resumes as resumes_api
import app.models  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.schemas.match import CandidateMatchCreate
from app.services.matching import _candidate_payload


SAMPLE_JOB = {
    "title": "软件开发实习生",
    "department": "研发中心",
    "location": "广州",
    "salary_range": "150-250 元/天",
    "experience_required": "应届生或 1 年以内实习经验",
    "education_required": "本科及以上",
    "jd": "参与内部业务系统、数据平台和 AI 工具开发，负责接口、页面联调、数据处理和基础测试。",
    "responsibilities": ["参与系统开发", "完成接口联调", "整理技术文档"],
    "must_have": ["Python", "React", "SQL"],
    "nice_to_have": ["FastAPI", "Docker"],
    "deal_breakers": ["完全没有项目经验"],
    "scoring_dimensions": ["技术栈匹配", "项目经历", "沟通表达"],
}

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


@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)

    async def fake_match(job, candidate):
        return CandidateMatchCreate(
            score=88,
            level="强推荐",
            summary=f"{candidate.name or '候选人'} 与 {job.title} 技术栈匹配，建议复核项目深度。",
            matched_points=["命中 Python / React / SQL"],
            weak_points=["实习稳定性需要面试确认"],
            risks=["建议复核：项目职责边界需要进一步确认"],
            interview_questions=["请说明最复杂的一次接口或页面联调经历。"],
        )

    monkeypatch.setattr(resumes_api, "generate_candidate_match", fake_match)
    monkeypatch.setattr(matches_api, "generate_candidate_match", fake_match)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def upload_text(test_client: TestClient, job_id: str, filename: str, content: str):
    return test_client.post(
        f"/api/jobs/{job_id}/resumes/upload",
        files={"file": (filename, content.encode("utf-8"), "text/plain")},
    )


def test_v2_acceptance_flow(client: TestClient):
    assert client.get("/api/dashboard").status_code == 200

    job_response = client.post("/api/jobs", json=SAMPLE_JOB)
    assert job_response.status_code == 201
    job_id = job_response.json()["id"]

    first_upload = upload_text(client, job_id, "后端开发-陈晓明.txt", RESUME_ONE)
    second_upload = upload_text(client, job_id, "前端开发-李思雨.txt", RESUME_TWO)
    assert first_upload.status_code == 201
    assert second_upload.status_code == 201
    assert first_upload.json()["candidate"]
    assert second_upload.json()["candidate"]

    failed_upload = client.post(
        f"/api/jobs/{job_id}/resumes/upload",
        files={"file": ("解析失败样例.pdf", b"not a real pdf", "application/pdf")},
    )
    assert failed_upload.status_code == 201
    assert failed_upload.json()["resume_file"]["parse_status"] == "failed"

    tasks = client.get(f"/api/jobs/{job_id}/upload-tasks").json()
    assert len(tasks) == 3
    assert any(task["parse_status"] == "failed" for task in tasks)
    retry_response = client.post(f"/api/jobs/{job_id}/upload-tasks/retry-failed")
    assert retry_response.status_code == 200

    candidates_response = client.get(f"/api/jobs/{job_id}/candidates?skill=React&min_score=1")
    assert candidates_response.status_code == 200
    candidates = candidates_response.json()
    assert len(candidates) == 2
    candidate_id = candidates[0]["candidate"]["id"]
    candidate_ids = [item["candidate"]["id"] for item in candidates]

    bulk_response = client.post(
        f"/api/jobs/{job_id}/candidates/bulk-status",
        json={"candidate_ids": [*candidate_ids, "missing-candidate"], "status": "pending_contact"},
    )
    assert bulk_response.status_code == 200
    assert len(bulk_response.json()) == len(candidate_ids)

    explanations_response = client.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/match/explanations")
    assert explanations_response.status_code == 200
    assert explanations_response.json()

    note_response = client.post(
        f"/api/jobs/{job_id}/candidates/{candidate_id}/notes",
        json={
            "candidate_id": candidate_id,
            "job_id": job_id,
            "content": "V2 验收备注",
            "created_by": "acceptance",
        },
    )
    assert note_response.status_code == 200
    timeline = client.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/timeline").json()
    assert any(item["action_type"] == "note_created" for item in timeline)

    archive_response = client.post(f"/api/candidates/{candidate_id}/talent-pool", json={"job_id": job_id})
    assert archive_response.status_code == 200
    assert client.post(f"/api/candidates/{candidate_id}/tags", json={"name": "V2验收"}).status_code == 200
    talent_pool = client.get("/api/talent-pool/candidates?query=React").json()
    assert any(item["candidate"]["id"] == candidate_id for item in talent_pool)

    assert client.get(f"/api/jobs/{job_id}/funnel").status_code == 200
    assert client.get(f"/api/jobs/{job_id}/jd-quality").status_code == 200
    assert client.post(f"/api/jobs/{job_id}/copy").status_code == 201
    assert client.post(f"/api/jobs/{job_id}/pause").json()["status"] == "paused"
    assert client.post(f"/api/jobs/{job_id}/reopen").json()["status"] == "open"
    assert client.post(f"/api/jobs/{job_id}/close").json()["status"] == "closed"

    candidate_payload = _candidate_payload(SimpleNamespace(**first_upload.json()["candidate"]))
    assert "phone" not in candidate_payload
    assert "email" not in candidate_payload
