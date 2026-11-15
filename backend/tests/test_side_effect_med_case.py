from backend.utils.side_effects_tracker import SideEffectsTracker, EffectCategory, SeverityLevel


def test_same_medication_different_case_grouped_in_alert():
    t = SideEffectsTracker()
    for name, eff in [("Metformin", "nausea"), ("metformin", "rash"), ("METFORMIN ", "dizzy")]:
        t.report_side_effect("p1", name, "500mg", eff, EffectCategory.OTHER, SeverityLevel.MILD, "d")
    assert any("3 active side effects" in a for a in t.check_for_alerts("p1"))
