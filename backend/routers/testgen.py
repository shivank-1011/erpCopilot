"""
routers/testgen.py — Test case generation endpoint.

POST /api/generate-tests
  Body:  { "chunk_text": str, "source": str }
  Returns: Structured test cases { feature_name, positive_tests, negative_tests, edge_cases }
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.testgen_service import generate_test_cases

router = APIRouter(prefix="/api", tags=["test-generation"])


class TestGenRequest(BaseModel):
    chunk_text: str = Field(
        ...,
        min_length=50,
        max_length=8000,
        description="The document section to generate test cases from.",
    )
    source: str = Field(
        default="Unknown source",
        description="Human-readable citation (filename + page), shown in the output.",
    )


class TestCase(BaseModel):
    test_id: str
    title: str
    preconditions: str = ""
    test_steps: list[str]
    test_data: str = ""
    expected_result: str


class TestGenResponse(BaseModel):
    feature_name: str
    feature_summary: str = ""
    positive_tests: list[TestCase]
    negative_tests: list[TestCase]
    edge_cases: list[TestCase]
    total_tests: int
    source: str


@router.post("/generate-tests", response_model=TestGenResponse)
def generate_tests(request: TestGenRequest):
    """
    Generate structured QA test cases from a selected document chunk.

    Uses Gemini 2.0 Flash with JSON mode to produce:
    - Positive tests (happy path)
    - Negative tests (invalid inputs, rule violations)
    - Edge cases (boundary conditions)
    """
    try:
        result = generate_test_cases(
            chunk_text=request.chunk_text,
            source=request.source,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Normalize test case fields (Gemini may use slightly different keys)
    def normalize(tc: dict, prefix: str, idx: int) -> dict:
        return {
            "test_id":       tc.get("test_id", f"{prefix}_{idx:03d}"),
            "title":         tc.get("title", "Untitled test"),
            "preconditions": tc.get("preconditions", ""),
            "test_steps":    tc.get("test_steps") or tc.get("steps") or [],
            "test_data":     tc.get("test_data", ""),
            "expected_result": tc.get("expected_result", ""),
        }

    positive = [normalize(tc, "TC_POS", i + 1) for i, tc in enumerate(result.get("positive_tests", []))]
    negative = [normalize(tc, "TC_NEG", i + 1) for i, tc in enumerate(result.get("negative_tests", []))]
    edges    = [normalize(tc, "TC_EDGE", i + 1) for i, tc in enumerate(result.get("edge_cases", []))]

    return TestGenResponse(
        feature_name=result.get("feature_name", "ERP Feature"),
        feature_summary=result.get("feature_summary", ""),
        positive_tests=positive,
        negative_tests=negative,
        edge_cases=edges,
        total_tests=len(positive) + len(negative) + len(edges),
        source=request.source,
    )
