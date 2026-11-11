# Verified version pair

The same-policy version requirement is satisfied by two authentic official
FAST-NUCES undergraduate academic-rules editions:

| Edition | Official URL | Indexed filename | Internal edition evidence | SHA-256 |
| --- | --- | --- | --- | --- |
| 2023-08 | https://nu.edu.pk/public/downloads/Academic-Rules-%20Undergrad-Programs.pdf | `undergraduate-academic-rules-and-regulations-earlier-official-edition.pdf` | Cover: “ACADEMIC RULES AND REGULATIONS 2023”; page 2: “Revised August 2023” | `cddfe1f5e9770132e27d686abd1c2e6742ef4732f0c2f431ed514bc1691d2004` |
| 2026-06 | https://nu.edu.pk/public/downloads/Academic_Rules_Handbook_2026.pdf | `undergraduate-academic-rules-handbook-jun-2026.pdf` | Cover/title pages identify “Undergraduate Academic Rules and Regulations 2026” and June 2026 | `4cfee3e191b84aeb9168f17656c7642212ff52b90f2780d028b33c154aa74b62` |

The 2023 PDF has 26 pages and the 2026 PDF has 58 pages. Both were fetched by
`python corpus/fetch.py`, recorded in `corpus/MANIFEST.md`, copied to the
existing corpus PVC, and indexed without merging their source or version
metadata. The 2023 edition is marked `superseded: true`; the 2026 edition is
active.

## Verifiable differences

1. **Degree credit requirement:** the 2023 edition states in Rule 1.25 on
   page 8 that each Bachelor's degree program has a minimum of 130 credit
   hours, followed by the 2.00 graduation CGPA rule. In the 2026 edition,
   Rule 1.25 is on page 10 and states the minimum graduation CGPA of 2.00;
   the 130-credit-hour sentence is not present in that corresponding rule.

2. **Repeating courses:** the 2023 edition's Rule 5.8 on page 17 requires a
   student to repeat a course with an F whenever it is offered. The 2026
   edition's Rule 5.8 on page 25 covers any failed or missed course from the
   previous semester and makes registration mandatory in the subsequent
   semester when offered.

3. **Summer semester:** the 2023 edition's Rule 6.1 on page 20 describes an
   optional summer semester lasting 8 to 9 weeks and permits stated new-course
   exceptions. The 2026 edition's Rule 6.1 on page 28 defines an 8-week summer
   semester for four student categories, and Rules 6.2 and 6.7 restrict it to
   repeat courses and apply an 80% attendance rule.

The Student Handbook 2024 and 2025 candidate URLs were also checked and
returned HTTP 404; neither was substituted with an unofficial or fabricated
copy.
