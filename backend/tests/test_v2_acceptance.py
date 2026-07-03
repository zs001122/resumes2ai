from types import SimpleNamespace

import app.api.matches as matches_api
import app.api.resumes as resumes_api
import app.services.resume_parser as resume_parser
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
from app.services.resume_parser import parse_resume_text, parse_resume_text_with_ai
from app.services.resume_sections import extract_sections, normalized_lines


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


def upload_text_with_job_field(test_client: TestClient, job_id: str, filename: str, content: str):
    return test_client.post(
        "/api/resumes/upload",
        data={"job_id": job_id},
        files={"file": (filename, content.encode("utf-8"), "text/plain")},
    )


def create_job(test_client: TestClient, title: str = "软件开发实习生") -> str:
    payload = {**SAMPLE_JOB, "title": title}
    response = test_client.post("/api/jobs", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


def test_candidate_correction_log_records_vnext_source(client):
    job_id = create_job(client)
    upload_response = upload_text(client, job_id, "candidate.txt", RESUME_ONE)
    assert upload_response.status_code == 201
    candidate_id = upload_response.json()["candidate"]["id"]

    response = client.patch(
        f"/api/candidates/{candidate_id}",
        json={
            "name": "陈晓明",
            "city": "佛山",
            "correction_sources": {
                "name": {
                    "candidate_id": "field-candidate-1",
                    "extractor": "section:basics:rules",
                    "confidence": 0.91,
                    "source_text": "陈晓明",
                }
            },
        },
    )
    assert response.status_code == 200

    logs_response = client.get(f"/api/candidates/{candidate_id}/correction-logs")
    assert logs_response.status_code == 200
    logs = logs_response.json()
    name_log = next(log for log in logs if log["field_name"] == "name")
    city_log = next(log for log in logs if log["field_name"] == "city")
    assert name_log["new_value"] == "陈晓明"
    assert name_log["editor_id"] == "vnext:section:basics:rules@0.91"
    assert city_log["editor_id"] == "local"


def test_resume_parser_extracts_rich_structured_fields():
    parsed = parse_resume_text(
        "数据开发-王小明.txt",
        """姓名：王小明
电话：13800138009
邮箱：wang@example.com
城市：广州
本科，5 年工作经验
技能：Python SQL Docker React

教育经历
2016.09-2020.06 华南理工大学 软件工程 本科

工作经历
2021.07-至今 广州数智科技有限公司 数据开发工程师 负责数据平台建设

项目经历
项目名称：招聘数据平台
项目角色：后端开发
技术栈：Python FastAPI PostgreSQL Docker
负责简历解析、候选人筛选和报表服务

证书
PMP
系统集成项目管理工程师

语言能力
英语 CET-6

获奖经历
校级优秀毕业生

自我评价
熟悉数据平台和 AI 工具落地，沟通主动。
""",
    )

    candidate = parsed.candidate_data
    assert candidate["education"][0]["school"] == "华南理工大学"
    assert candidate["education"][0]["degree"] == "本科"
    assert candidate["work_experiences"][0]["company"] == "广州数智科技有限公司"
    assert candidate["work_experiences"][0]["title"] == "数据开发工程师"
    assert candidate["project_experiences"][0]["name"] == "招聘数据平台"
    assert "FastAPI" in candidate["project_experiences"][0]["technologies"]
    assert "PMP" in candidate["certifications"]
    assert "英语 CET-6" in candidate["languages"]
    assert "校级优秀毕业生" in candidate["awards"]
    assert "AI 工具落地" in candidate["self_evaluation"]
    assert "project_experiences" not in candidate["low_confidence_fields"]
    extracted_fields = {item["field_name"] for item in parsed.field_sources}
    assert {"certifications", "languages", "awards", "self_evaluation"} <= extracted_fields


def test_resume_sections_handles_spaced_and_inferred_sections():
    lines = normalized_lines(
        """李浩斌
教 育 经历
广州大学 2016 年 09 月 - 2020 年 07 月
网络工程 本科 计算机学院
项 目 经 历
HappyCommunity 社 交 网 站
后端开发 （2023 年 6 月~2023 年 8 月）
工 作 经 历
广州华资软件技术有限公司 2023 年 09 月~2023 年 11 月
java 开发实习生 政法行业事业部 广州
"""
    )
    sections = extract_sections(lines)

    assert sections["education"]
    assert sections["project"][0] == "HappyCommunity 社 交 网 站"
    assert sections["work"][0].startswith("广州华资软件技术有限公司")

    inferred_lines = normalized_lines(
        """杨晓飞
长城计算机软件与系统有限公司 etl数据处理工程师
2022.01-至今
市场监管数据综合治理平台项目 ETL数据处理工程师 2022.01-2023.11
项目概况：数据采集并整理开发。
"""
    )
    inferred = extract_sections(inferred_lines)

    assert inferred["work"][0].startswith("长城计算机软件与系统有限公司")
    assert inferred["project"][0].startswith("市场监管数据综合治理平台项目")


def test_resume_years_prefers_explicit_header_over_timeline():
    parsed = parse_resume_text(
        "数据开发-杨晓飞.txt",
        """杨晓飞
男 | 年龄：29岁 | 18126839220 | 1104314557@qq.com 7年工作经验 | 求职意向：数据开发 | 期望城市：广州
长城计算机软件与系统有限公司 etl数据处理工程师
2022.01-至今
广州源越通科技有限公司 数据分析师 2016.10-2018.04
教育经历
广西工业职业技术学院 专科 电子信息工程 2010-2013
""",
    )

    years_source = next(item for item in parsed.field_sources if item["field_name"] == "years_of_experience")
    assert parsed.candidate_data["years_of_experience"] == 7.0
    assert years_source["source_text"] == "7年"
    assert years_source["confidence"] == 0.85


def test_resume_years_prefers_role_specific_experience_over_generic_total():
    parsed = parse_resume_text(
        "数据开发-杨晓飞.txt",
        """杨晓飞
男 | 年龄：29岁 | 18126839220 | 1104314557@qq.com 7年工作经验 | 求职意向：数据开发 | 期望城市：广州
1.本人有5年数据开发经验，具有数据分析和数据清洗、转换、加载的项目实践经验；
工作经历
长城计算机软件与系统有限公司 etl数据处理工程师
2022.01-至今
广州弘诺电子科技有限公司 ETL工程师 2018.05-2021.12
广州源越通科技有限公司 数据分析师 2016.10-2018.04
""",
    )

    years_source = next(item for item in parsed.field_sources if item["field_name"] == "years_of_experience")
    assert parsed.candidate_data["years_of_experience"] == 5.0
    assert years_source["source_text"] == "5年"
    assert years_source["confidence"] == 0.88


def test_campus_project_role_does_not_create_work_experience():
    parsed = parse_resume_text(
        "嵌入式开发-翁鑫源.txt",
        """翁鑫源
应届生
项目经历
2022/03-2022/04 STM32 蓝牙智能小车项目 嵌入式开发
工作岗位：广州大学电子信息楼 软件设计实物仿真助理
负责工作：原理分析和系统框图、软件设计与 Proteus 仿真。
教育经历
广州大学 本科 电子信息工程 2020-2024
""",
    )

    candidate = parsed.candidate_data
    assert candidate["work_experiences"] == []
    assert candidate["project_experiences"]
    assert candidate["project_experiences"][0]["role"] == "广州大学电子信息楼 软件设计实物仿真助理"
    assert "work_experiences" in candidate["low_confidence_fields"]
    assert "project_experiences" not in candidate["low_confidence_fields"]


def test_campus_section_stops_work_experience_and_preserves_spaced_date_range():
    parsed = parse_resume_text(
        "24年应届生-李浩斌.pdf",
        """李浩斌
实习经历
广州华资软件技术有限公司 软件开发实习生
2023 年 09 月~2023 年 11 月
负责政务系统接口联调和问题修复。
校园 经历
2021 至 2022 学年担任学校计算机学院学生党建工作委员会副主席
2022 至 2023 学年担任班级干部
""",
    )

    candidate = parsed.candidate_data
    assert candidate["years_of_experience"] == 0.2
    assert len(candidate["work_experiences"]) == 1
    work = candidate["work_experiences"][0]
    assert work["company"] == "广州华资软件技术有限公司"
    assert work["time_range"] == "2023 年 09 月~2023 年 11 月"
    assert "校园" not in work["description"]


def test_project_heading_stops_work_section_overcapture():
    parsed = parse_resume_text(
        "后端开发-杨梓灼.pdf",
        """杨梓灼
工作经历
广州华源格林科技有限公司 | python 开发工程师
任职时间：2023 年 8 月至今
负责南方电网数字化转型相关业务系统的时序算法、LLM 模型、后端服务及全栈应用。
核心项目经历
1. 国内外学术期刊数据采集管理系统
项目背景：面向科研机构打造学术文献数据管理平台。
技术栈：FastAPI、Selenium、Playwright、Celery、MongoDB、Redis
核心技能
熟练使用 Python 进行业务服务开发。
""",
    )

    candidate = parsed.candidate_data
    assert len(candidate["work_experiences"]) == 1
    assert len(candidate["project_experiences"]) == 1
    work = candidate["work_experiences"][0]
    project = candidate["project_experiences"][0]
    assert "核心项目经历" not in (work["description"] or "")
    assert "国内外学术期刊" not in (work["description"] or "")
    assert project["name"] == "1. 国内外学术期刊数据采集管理系统"
    assert "FastAPI" in project["technologies"]


def test_self_evaluation_stops_before_work_header():
    parsed = parse_resume_text(
        "直聘简历-未命名.pdf",
        """候选人
个人优势
2 年智能化应用开发与企业项目落地经验，具备需求分析、方案设计、开发部署能力。
熟练掌握 Python，具备多技术栈协同开发与系统集成能力。
广州智算信息技术有限公司 算法工程师 2022.10-至今
负责智能体开发、企业知识库和自动化流程落地。
项目经历
项目描述：企业知识库问答系统
技术栈：Python Docker LangChain
""",
    )

    candidate = parsed.candidate_data
    assert candidate["self_evaluation"]
    assert "广州智算信息技术有限公司" not in candidate["self_evaluation"]
    assert len(candidate["work_experiences"]) == 1
    assert candidate["work_experiences"][0]["company"] == "广州智算信息技术有限公司"
    assert candidate["work_experiences"][0]["title"] == "算法工程师"


def test_unheaded_education_is_extracted_before_project_sections():
    parsed = parse_resume_text(
        "24年应届生-翁鑫源.docx",
        """翁鑫源
求职意向：后端开发
2017/09-2020/07 广州学院 专科 电子信息工程
主修课程：C 语言程序设计、数据结构与算法
2020/09-2024/07 广州大学 本科 电子信息工程
项目经历
2022/03-2022/04 STM32 蓝牙智能小车项目 嵌入式开发
工作岗位：广州大学电子信息楼 软件设计实物仿真助理
校内外实践活动
2023/05-2023/05 广州小蚁智控科技有限公司 实习员工
""",
    )

    education = parsed.candidate_data["education"]
    assert len(education) == 2
    assert education[0]["school"] == "广州学院"
    assert education[1]["school"] == "广州大学"
    assert parsed.candidate_data["highest_education"] == "本科"


@pytest.mark.anyio
async def test_resume_parser_ai_enriches_unstructured_fields(monkeypatch):
    class FakeProvider:
        async def chat_json(self, messages, schema_hint):
            return {
                "phone": "19999999999",
                "email": "wrong@example.com",
                "skills": ["精通 Python", "熟悉 React"],
                "work_experiences": [
                    {
                        "company": "北大",
                        "title": "数据开发工程师",
                        "time_range": "2021年3月至今",
                        "description": "负责数据平台接口、ETL 和稳定性建设",
                    }
                ],
                "project_experiences": [
                    {
                        "name": "智能招聘平台",
                        "role": "后端负责人",
                        "technologies": ["Python", "FastAPI"],
                        "description": "从自由文本中抽取项目职责和成果",
                    }
                ],
                "self_evaluation": "中英文混合项目经验丰富，能推动 AI 工具落地。",
            }

    monkeypatch.setattr(resume_parser.settings, "ai_resume_parse_enabled", True)
    monkeypatch.setattr(resume_parser, "get_ai_provider", lambda: FakeProvider())

    parsed = await parse_resume_text_with_ai(
        "后端开发-赵一.txt",
        "姓名：赵一\n电话：13800138010\n邮箱：zhao@example.com\n项目很多，Python/React 都做过。",
    )

    candidate = parsed.candidate_data
    assert candidate["phone"] == "13800138010"
    assert candidate["email"] == "zhao@example.com"
    assert "精通 Python" in candidate["skills"]
    assert candidate["work_experiences"][0]["company"] == "北京大学"
    assert candidate["project_experiences"][0]["role"] == "后端负责人"
    assert "AI 工具落地" in candidate["self_evaluation"]


def test_v2_acceptance_flow(client: TestClient):
    assert client.get("/api/dashboard").status_code == 200

    job_id = create_job(client)
    versions = client.get(f"/api/jobs/{job_id}/standard-versions")
    assert versions.status_code == 200
    assert versions.json()[0]["version"] == 1

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

    jobs_payload = client.get("/api/jobs").json()
    listed_job = next(item for item in jobs_payload if item["id"] == job_id)
    assert listed_job["candidate_count"] == 2
    assert listed_job["high_match_count"] == 2
    assert listed_job["pending_count"] == 2
    funnel_payload = client.get(f"/api/jobs/{job_id}/funnel").json()
    assert funnel_payload["high_match"] == 2
    assert funnel_payload["pending"] == 2

    bulk_response = client.post(
        f"/api/jobs/{job_id}/candidates/bulk-status",
        json={"candidate_ids": [*candidate_ids, "missing-candidate"], "status": "pending_contact"},
    )
    assert bulk_response.status_code == 200
    assert len(bulk_response.json()) == len(candidate_ids)

    explanations_response = client.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/match/explanations")
    assert explanations_response.status_code == 200
    assert explanations_response.json()
    latest_match = client.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/match").json()
    assert latest_match["job_standard_version_id"] == versions.json()[0]["id"]
    report_response = client.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/match/recommendation-report")
    assert report_response.status_code == 200
    report_content = report_response.json()["content"]
    assert "# 候选人推荐摘要" in report_content
    assert "匹配分" in report_content
    assert "13800138001" not in report_content
    assert "chen@example.com" not in report_content

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
    updated_job = client.patch(f"/api/jobs/{job_id}", json={"must_have": ["Python", "React", "SQL", "FastAPI"]})
    assert updated_job.status_code == 200
    updated_versions = client.get(f"/api/jobs/{job_id}/standard-versions").json()
    assert len(updated_versions) == 2
    assert updated_versions[0]["version"] == 2
    assert client.patch(f"/api/jobs/{job_id}", json={"location": "上海"}).status_code == 200
    non_standard_versions = client.get(f"/api/jobs/{job_id}/standard-versions").json()
    assert len(non_standard_versions) == 2
    rematch_response = client.post(f"/api/jobs/{job_id}/candidates/rematch", json={"candidate_ids": candidate_ids})
    assert rematch_response.status_code == 200
    rematch_payload = rematch_response.json()
    assert rematch_payload["succeeded"] == len(candidate_ids)
    assert rematch_payload["failed"] == 0
    assert rematch_payload["job_standard_version_id"] == updated_versions[0]["id"]
    rematched = client.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/match").json()
    assert rematched["job_standard_version_id"] == updated_versions[0]["id"]
    assert client.post(f"/api/jobs/{job_id}/reopen").json()["status"] == "open"
    assert client.post(f"/api/jobs/{job_id}/close").json()["status"] == "closed"
    assert client.patch(f"/api/jobs/{job_id}", json={"title": "关闭后修改"}).status_code == 400
    assert client.post(f"/api/jobs/{job_id}/reopen").status_code == 400

    candidate_payload = _candidate_payload(SimpleNamespace(**first_upload.json()["candidate"]))
    assert "phone" not in candidate_payload
    assert "email" not in candidate_payload


def test_job_candidate_boundaries(client: TestClient):
    job_a_id = create_job(client, "岗位 A")
    job_b_id = create_job(client, "岗位 B")

    upload_a = upload_text(client, job_a_id, "后端开发-陈晓明.txt", RESUME_ONE)
    upload_b = upload_text(client, job_b_id, "前端开发-李思雨.txt", RESUME_TWO)
    assert upload_a.status_code == 201
    assert upload_b.status_code == 201
    candidate_a_id = upload_a.json()["candidate"]["id"]
    candidate_b_id = upload_b.json()["candidate"]["id"]

    status_response = client.patch(
        f"/api/jobs/{job_a_id}/candidates/{candidate_b_id}/status",
        json={"status": "pending_contact"},
    )
    assert status_response.status_code == 404

    match_response = client.post(f"/api/jobs/{job_a_id}/candidates/{candidate_b_id}/match")
    assert match_response.status_code == 404

    note_response = client.post(
        f"/api/jobs/{job_a_id}/candidates/{candidate_b_id}/notes",
        json={
            "candidate_id": candidate_b_id,
            "job_id": job_b_id,
            "content": "不应写入",
            "created_by": "acceptance",
        },
    )
    assert note_response.status_code == 404

    timeline_response = client.get(f"/api/jobs/{job_a_id}/candidates/{candidate_b_id}/timeline")
    assert timeline_response.status_code == 404

    bulk_status = client.post(
        f"/api/jobs/{job_a_id}/candidates/bulk-status",
        json={"candidate_ids": [candidate_a_id, candidate_b_id], "status": "pending_contact"},
    )
    assert bulk_status.status_code == 200
    assert len(bulk_status.json()) == 1
    assert bulk_status.json()[0]["candidate_id"] == candidate_a_id

    bulk_match = client.post(
        f"/api/jobs/{job_a_id}/candidates/bulk-match",
        json={"candidate_ids": [candidate_a_id, candidate_b_id]},
    )
    assert bulk_match.status_code == 200
    assert len(bulk_match.json()) == 1
    assert bulk_match.json()[0]["candidate_id"] == candidate_a_id
    assert client.get(f"/api/jobs/{job_a_id}/funnel").json()["high_match"] == 1

    wrong_pool_response = client.post(
        f"/api/candidates/{candidate_b_id}/talent-pool",
        json={"job_id": job_a_id},
    )
    assert wrong_pool_response.status_code == 404

    right_pool_response = client.post(
        f"/api/candidates/{candidate_b_id}/talent-pool",
        json={"job_id": job_b_id},
    )
    assert right_pool_response.status_code == 200
    assert right_pool_response.json()["job_id"] == job_b_id


def test_unified_upload_detects_duplicate_candidates(client: TestClient):
    job_id = create_job(client)

    first_upload = upload_text(client, job_id, "后端开发-陈晓明.txt", RESUME_ONE)
    duplicate_upload = upload_text_with_job_field(client, job_id, "陈晓明-重复.txt", RESUME_ONE)

    assert first_upload.status_code == 201
    assert duplicate_upload.status_code == 201
    payload = duplicate_upload.json()
    assert payload["resume_file"]["job_id"] == job_id
    assert payload["duplicate_policy"] == "created_new"
    assert payload["duplicate_candidates"]
    assert payload["duplicate_candidates"][0]["match_reason"] == "手机号完全匹配"
    duplicate_check_id = payload["duplicate_candidates"][0]["id"]
    duplicate_candidate_id = payload["candidate"]["id"]

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["summary"]["pending_duplicate_reviews"] == 1
    duplicate_todo = next(item for item in dashboard["todos"] if item["key"] == "pending_duplicate_review")
    assert duplicate_todo["count"] == 1
    assert duplicate_candidate_id in duplicate_todo["href"]

    tasks = client.get(f"/api/jobs/{job_id}/upload-tasks").json()
    duplicate_tasks = [task for task in tasks if task["original_filename"] == "陈晓明-重复.txt"]
    assert duplicate_tasks
    assert duplicate_tasks[0]["has_duplicate_risk"] is True
    assert duplicate_tasks[0]["duplicate_count"] == 1
    assert duplicate_tasks[0]["pending_duplicate_review_count"] == 1

    review_response = client.patch(
        f"/api/jobs/{job_id}/candidates/{duplicate_candidate_id}/duplicate-checks/{duplicate_check_id}",
        json={"status": "confirmed_duplicate", "review_note": "确认是同一位候选人，本期不自动合并"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "confirmed_duplicate"
    detail_response = client.get(f"/api/jobs/{job_id}/candidates/{duplicate_candidate_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["duplicate_candidates"][0]["review_note"] == "确认是同一位候选人，本期不自动合并"
    timeline = client.get(f"/api/jobs/{job_id}/candidates/{duplicate_candidate_id}/timeline").json()
    assert any(item["action_type"] == "duplicate_reviewed" for item in timeline)

    tasks = client.get(f"/api/jobs/{job_id}/upload-tasks").json()
    duplicate_tasks = [task for task in tasks if task["original_filename"] == "陈晓明-重复.txt"]
    assert duplicate_tasks[0]["pending_duplicate_review_count"] == 0
    assert duplicate_tasks[0]["confirmed_duplicate_count"] == 1


def test_retry_failed_parse_runs_match_after_success(client: TestClient, monkeypatch):
    job_id = create_job(client)
    original_extract_text = resumes_api.ResumeTextExtractor.extract_text
    attempts = {"count": 0}

    def flaky_extract_text(self, path):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("临时解析失败")
        return original_extract_text(self, path)

    monkeypatch.setattr(resumes_api.ResumeTextExtractor, "extract_text", flaky_extract_text)

    failed_upload = upload_text(client, job_id, "临时解析失败-陈晓明.txt", RESUME_ONE)
    assert failed_upload.status_code == 201
    assert failed_upload.json()["resume_file"]["parse_status"] == "failed"
    assert failed_upload.json()["candidate"] is None

    retry_response = client.post(f"/api/jobs/{job_id}/upload-tasks/retry-failed")
    assert retry_response.status_code == 200
    retried_tasks = retry_response.json()
    assert len(retried_tasks) == 1
    assert retried_tasks[0]["parse_status"] == "success"
    assert retried_tasks[0]["match_status"] == "success"

    candidates = client.get(f"/api/jobs/{job_id}/candidates").json()
    assert len(candidates) == 1
    candidate_id = candidates[0]["candidate"]["id"]
    match_response = client.get(f"/api/jobs/{job_id}/candidates/{candidate_id}/match")
    assert match_response.status_code == 200


def test_rematch_reports_candidates_outside_job(client: TestClient):
    job_a_id = create_job(client, "重评岗位 A")
    job_b_id = create_job(client, "重评岗位 B")
    upload_a = upload_text(client, job_a_id, "后端开发-陈晓明.txt", RESUME_ONE)
    upload_b = upload_text(client, job_b_id, "前端开发-李思雨.txt", RESUME_TWO)
    candidate_a_id = upload_a.json()["candidate"]["id"]
    candidate_b_id = upload_b.json()["candidate"]["id"]

    response = client.post(
        f"/api/jobs/{job_a_id}/candidates/rematch",
        json={"candidate_ids": [candidate_a_id, candidate_b_id]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["succeeded"] == 1
    assert payload["failed"] == 1
    assert payload["failures"][0]["candidate_id"] == candidate_b_id

def test_upload_persists_vnext_parse_run(client: TestClient):
    job_id = create_job(client, "软件开发实习生")
    upload_response = upload_text(client, job_id, "后端开发-陈晓明.txt", RESUME_ONE)
    assert upload_response.status_code == 201
    resume_file_id = upload_response.json()["resume_file"]["id"]

    response = client.get(f"/api/resume-files/{resume_file_id}/parse-runs/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["resume_file_id"] == resume_file_id
    assert payload["candidate_id"] == upload_response.json()["candidate"]["id"]
    assert payload["parser_version"].startswith("resume-parser-vnext")
    assert payload["status"] == "success"
    assert isinstance(payload["quality_score"], float)
    assert payload["blocks"]
    assert any(item["field_name"] == "phone" and item["selected"] for item in payload["field_candidates"])
