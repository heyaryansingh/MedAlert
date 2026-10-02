from datetime import datetime

from backend.utils.side_effects_tracker import (
    EffectCategory,
    SeverityLevel,
    SideEffectsTracker,
)


def test_same_onset_effects_get_unique_ids_and_resolve_independently():
    t = SideEffectsTracker()
    onset = datetime(2024, 1, 1)
    a = t.report_side_effect("p1", "Metformin", "500mg", "nausea", EffectCategory.GASTROINTESTINAL, SeverityLevel.MILD, "", onset)
    b = t.report_side_effect("p1", "Metformin", "500mg", "rash", EffectCategory.DERMATOLOGICAL, SeverityLevel.MILD, "", onset)
    assert a.effect_id != b.effect_id
    t.resolve_side_effect(b.effect_id)
    assert not a.resolved and b.resolved
