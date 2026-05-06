from app.recommendations.quality_spec import quality_spec_reference


def test_quality_spec_reference_points_to_project_spec():
    ref = quality_spec_reference()

    assert ref.exists is True
    assert ref.sha256
    assert ref.title == "Recommendation Quality Spec"
    assert ref.path.endswith("docs\\recommendation_quality_spec.md") or ref.path.endswith(
        "docs/recommendation_quality_spec.md"
    )
