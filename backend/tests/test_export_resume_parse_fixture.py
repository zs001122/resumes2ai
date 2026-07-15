from scripts.export_resume_parse_fixture import _redact_file_name, _redact_resume_text


def test_redact_resume_text_replaces_detected_contact_values():
    text = "王小明\n电话：13912345678\n邮箱：real@example.com\n项目经历"

    redacted = _redact_resume_text(
        text,
        {"name": "王小明", "phone": "13912345678", "email": "real@example.com"},
        name_alias="张三",
        phone_alias="13800000000",
        email_alias="candidate@example.com",
    )

    assert "王小明" not in redacted
    assert "13912345678" not in redacted
    assert "real@example.com" not in redacted
    assert "张三" in redacted
    assert "13800000000" in redacted
    assert "candidate@example.com" in redacted


def test_redact_resume_text_masks_unparsed_contact_patterns():
    text = "联系方式 +86 139-1234-5678 / backup@example.cn"

    redacted = _redact_resume_text(
        text,
        {},
        name_alias="张三",
        phone_alias="13800000000",
        email_alias="candidate@example.com",
    )

    assert "139-1234-5678" not in redacted
    assert "backup@example.cn" not in redacted
    assert "13800000000" in redacted
    assert "candidate@example.com" in redacted


def test_redact_file_name_replaces_detected_contact_values():
    assert (
        _redact_file_name(
            "王小明-13912345678-real@example.com.pdf",
            {"name": "王小明", "phone": "13912345678", "email": "real@example.com"},
            name_alias="张三",
            phone_alias="13800000000",
            email_alias="candidate@example.com",
        )
        == "张三-13800000000-candidate@example.com.pdf"
    )
