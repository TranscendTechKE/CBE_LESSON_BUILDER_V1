# CBE Lesson Builder V1 — BUILD 09 Standardized Lesson Plan Patch

This is a **BUILD 09 patch** for the BUILD 08 application.

It is not a replacement for the whole project. Copy the files into the existing BUILD 08 project after creating the BUILD 08 Git checkpoint.

## Files

```text
CBE_BUILD09_STANDARDIZED/
├── app/
│   └── services/
│       └── lesson_plan_generator.py
├── tests/
│   └── test_build09_lesson_plan.py
├── BUILD_09_CHANGE_MAP.md
└── README.md
```

## Install/use

1. Make the BUILD 08 checkpoint first.
2. Back up the current `app/services/lesson_plan_generator.py`.
3. Replace it with the BUILD 09 version.
4. Keep the existing BUILD 08 curriculum upload, unit selection, dashboard and API routes unchanged initially.
5. Run the tests.

From Windows CMD:

```cmd
cd C:\Users\Loitah\Documents\Github\CBE_LESSON_BUILDER_V1
python -m pytest tests/test_build09_lesson_plan.py -q
```

Then run the application:

```cmd
python -m uvicorn app.main:app --reload
```

## Expected 40-minute output

```text
Introduction — 5 minutes
Lesson Development — 30 minutes
    Step 1 — 8 minutes
    Step 2 — 8 minutes
    Step 3 — 7 minutes
    Step 4 — 7 minutes
Conclusion — 5 minutes
```

The exact step distribution is data-driven; the important invariant is that the development steps add up to the development time.

## Important

The generic activity text is intentionally deterministic in BUILD 09. It is a stable foundation for the next planned layers:

1. DOCX generation
2. AI provider adapter for richer curriculum-grounded activities
3. Authentication and teacher accounts
4. Payment integration

AI should not be allowed to replace the verified curriculum fields extracted by BUILD 07.
