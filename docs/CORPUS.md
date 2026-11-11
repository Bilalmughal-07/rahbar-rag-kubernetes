# Corpus

The corpus was fetched on 2026-11-09 with `python corpus/fetch.py` from official
FAST-NUCES pages and PDFs. The source configuration is in `corpus/sources.yaml`,
the downloaded files are intentionally gitignored under `corpus/raw/`, and the
fetcher-generated hashes are recorded in `corpus/MANIFEST.md` and
`corpus/raw/_index.json`.

**Verified inventory:** 11 documents (9 PDFs and 2 HTML pages), 400 PDF pages,
and 11/11 manifest hashes verified with `python corpus/fetch.py --verify`.

| # | Document | Source | Version | Pages / evidence |
| --- | --- | --- | --- | --- |
| 1 | Student Handbook | [FAST-NUCES PDF](https://nu.edu.pk/public/downloads/Student_Handbook_2026.pdf) | 2026-06 | 64 pages; 4 pages have no text layer |
| 2 | Faculty Handbook | [FAST-NUCES PDF](https://nu.edu.pk/public/downloads/Faculty_Handbook_2026.pdf) | 2026-06 | 60 pages; 4 pages have no text layer |
| 3 | Undergraduate Academic Rules Handbook | [FAST-NUCES PDF](https://nu.edu.pk/public/downloads/Academic_Rules_Handbook_2026.pdf) | 2026-06 | 58 pages; 4 pages have no text layer |
| 4 | Prospectus: Academic Rules and Regulations | [FAST-NUCES PDF](https://nu.edu.pk/Admissions/ProspectusUpload/Academic%20Rules%20and%20Regulations.pdf) | 2026 | 5 pages |
| 5 | Annual Report | [FAST-NUCES PDF](https://nu.edu.pk/public/downloads/AnnualReportForm/Annual%20Report%202022-23.pdf?261108=) | 2022-23; superseded | 36 pages |
| 6 | Annual Report | [FAST-NUCES PDF](https://nu.edu.pk/public/downloads/AnnualReportForm/Annual%20Report%202023-24.pdf?251014=) | 2023-24 | 85 pages |
| 7 | PhD Handbook | [FAST-NUCES PDF](https://nu.edu.pk/public/downloads/PhD_Handbook_2026_20261022.pdf) | 2026-08 | 58 pages |
| 8 | Faculty Entrepreneurship and Technical Start-ups Policy | [FAST-NUCES PDF](https://www.nu.edu.pk/OricResources/ResearchPolicies/27.pdf?20220530=) | 2022-05 | 8 pages; all 8 have no text layer |
| 9 | Fee Structure | [FAST-NUCES page](https://www.nu.edu.pk/Admissions/FeeStructure) | 2026-27 | HTML; 3 table tags |
| 10 | Grading | [FAST-NUCES page](https://www.nu.edu.pk/Student/Grading) | 2026 | HTML; 5 table tags |
| 11 | Undergraduate Academic Rules and Regulations (earlier official edition) | [FAST-NUCES PDF](https://nu.edu.pk/public/downloads/Academic-Rules-%20Undergrad-Programs.pdf) | 2023-08; superseded | 26 pages; 24 pages required OCR |

| Required property | Verified evidence | Status |
| --- | --- | --- |
| At least 6 authentic documents and 40 pages | 11 official documents and 400 PDF pages | Complete |
| Versioned documents | Official Annual Report 2022-23 and 2023-24; metadata marks 2022-23 superseded | Complete for document-version coverage |
| Same-policy version pair | Official Undergraduate Academic Rules and Regulations 2023-08 and Undergraduate Academic Rules Handbook 2026-06; metadata distinguishes the 2023 edition as superseded | Complete |
| Scanned, image-only PDF | Start-ups Policy: 8/8 pages had empty extracted text in `pypdf` | Verified; RapidOCR produced nonempty text for all 8 pages in the Kubernetes indexer run |
| Tables with real information | Fee Structure and Grading pages contain 3 and 5 HTML tables respectively | Verified; table structure is preserved in the indexed HTML extraction |
| Long definitions and exact terms | Student Handbook, Academic Rules Handbook, and Prospectus | Covered by the real golden/evaluation run |
| Deliberately absent topic | Hostel rules and transport facilities are not represented in the selected source list | Reserved for abstention evaluation |

The proposed Student Handbook 2024 and 2025 URLs were checked and returned HTTP
404, so they were not used. The earlier rules edition above is an accessible
official FAST-NUCES PDF and identifies itself internally as “ACADEMIC RULES AND
REGULATIONS 2023” and “Revised August 2023”. The 2026 counterpart identifies
itself as the 2026 Undergraduate Academic Rules and Regulations.

The official Downloads page lists the current handbooks and annual-report archive;
the configured URLs were taken from that source or official linked pages. No fake
documents, citations, page counts, or evaluation results were added.
