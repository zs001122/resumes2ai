# Resume Parse vNext 0.2 E2E Check - 2026-07-02

Scope: Upload two local real resume PDFs from `test_data/` through the normal upload API, verify `resume-parser-vnext-0.2` parse runs, check candidate detail/review page reachability, and record parser defects. Raw resume files are not committed.

## Test Job

- Job ID: `25eb00dc-aa93-45a6-b433-fff2b54238f6`
- Job title: `vNext 0.2 简历解析验收岗`
- Frontend base: `http://192.168.2.137:3010`
- Backend base: `http://192.168.2.137:8010`

## Upload Results

| Case | Resume file ID | Candidate ID | Parse status | Parser version | Quality | Low confidence fields |
| --- | --- | --- | --- | --- | ---: | --- |
| A | `7be10d90-bfc2-4b2f-8cfd-7eb6ea7566ae` | `e9da9e77-4fd2-4bfa-a8ac-83c995bce6a6` | success | `resume-parser-vnext-0.2` | 92 | `certifications` |
| B | `dce26e77-b511-403f-8e1c-de52925585b0` | `f7ada41b-d831-438c-8de1-6cad77753532` | success | `resume-parser-vnext-0.2` | 68 | `name`, `education`, `certifications` |

## Page Checks

| Case | Candidate detail | Candidate review | Result |
| --- | --- | --- | --- |
| A | `/jobs/25eb00dc-aa93-45a6-b433-fff2b54238f6/candidates/e9da9e77-4fd2-4bfa-a8ac-83c995bce6a6` | `/jobs/25eb00dc-aa93-45a6-b433-fff2b54238f6/candidates/e9da9e77-4fd2-4bfa-a8ac-83c995bce6a6/review` | both returned 200 |
| B | `/jobs/25eb00dc-aa93-45a6-b433-fff2b54238f6/candidates/f7ada41b-d831-438c-8de1-6cad77753532` | `/jobs/25eb00dc-aa93-45a6-b433-fff2b54238f6/candidates/f7ada41b-d831-438c-8de1-6cad77753532/review` | both returned 200 |

No browser automation dependency is installed in the frontend project, so click-level behavior was not automated. The review page was verified by route/API checks and implementation inspection: vNext candidates are grouped by editable field, low-confidence fields are ordered first, candidate values and the apply button both fill the form field, and source text is passed to preview highlighting.

## vNext Evidence Coverage

### Case A

- Blocks: `education`, `work`, `project`, `intention`
- Extractors present: `rules_ai_compat`, `section:basics:rules`, `section:education:rules`, `section:work:rules`, `section:projects:rules`, `section:skills:rules`, `section:unknown:rules`
- Selected section fields include: `name`, `phone`, `email`, `city`, `years_of_experience`, `highest_education`, `current_company`, `current_title`, `skills`, `education`, `work_experiences`, `project_experiences`
- Selected candidates all had `source_text`.
- Work/project source text exists but is too long and includes large narrative spans.

### Case B

- Blocks: `work`, `project`, `self_evaluation`
- Extractors present: `rules_ai_compat`, `section:basics:rules`, `section:education:rules`, `section:work:rules`, `section:projects:rules`, `section:skills:rules`, `section:unknown:rules`
- Selected section fields include: `phone`, `email`, `city`, `years_of_experience`, `highest_education`, `current_title`, `skills`, `work_experiences`, `project_experiences`
- Missing low-confidence candidates exist for `name`, `education`, and `certifications` with `missing_required_field`-style behavior.
- Project source text exists but is too long and spans too much of the project section.

## Parser Defects

1. Case A: work block over-captures project content.
   - The `work` block includes the `核心项目经历` section and part of project details.
   - Impact: `work_experiences.description` becomes noisy, and work evidence is too broad for review.
   - Likely cause: section boundary detection does not stop work when encountering project-like headings such as `核心项目经历`.

2. Case A: project source text is too long.
   - `project_experiences` source text contains multiple project narratives in one large span.
   - Impact: review page can highlight evidence, but HR still has to search inside a long block.
   - Next improvement: split projects by numbered headings and store one candidate/source per project item.

3. Case B: name extraction failed.
   - `name` is low-confidence/missing even though other basics were extracted.
   - Impact: candidate identity needs manual correction.
   - Next improvement: support resume exports where candidate name is not in filename and not labeled as `姓名`.

4. Case B: education extraction failed while highest education was inferred.
   - `highest_education` was extracted, but `education` list is empty.
   - Impact: the UI shows highest degree but cannot show school/major/time evidence.
   - Next improvement: add unheaded education recovery around degree/school/time patterns in PDF-export resumes.

5. Case B: self-evaluation block over-captures later work history.
   - The `self_evaluation` block includes later company/work-history text.
   - Impact: self evaluation evidence is polluted and may hide actual work entries from `work` parsing.
   - Next improvement: stop self-evaluation on company/date-range headers and job-title patterns.

6. Case B: current title is noisy.
   - `current_title` appears to be derived from the generic exported filename/title rather than the actual latest role.
   - Impact: candidate list title can be misleading.
   - Next improvement: prefer latest work experience title over generic filename-derived title when filename is an export placeholder.

7. Low-confidence treatment is mostly useful but too generic for missing optional fields.
   - `certifications` is flagged low-confidence in both cases when no certificate is present.
   - Impact: HR may see false work if the role does not require certificates.
   - Next improvement: distinguish required core fields from optional enrichment fields in quality scoring and review ordering.

## Suggested Next Parser Work

1. Improve section boundary detection for project and self-evaluation headings.
2. Split work/project blocks into item-level evidence candidates.
3. Add basics extraction fallback for unlabeled names in PDF export formats.
4. Add unheaded education recovery for exported resume layouts.
5. Adjust low-confidence policy so optional fields like certifications do not always reduce quality.
