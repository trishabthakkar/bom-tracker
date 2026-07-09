from app.services.document_parser import extract_part_references, parse_document_text


def test_parse_document_text_splits_sections_and_detects_part_refs() -> None:
    parsed = parse_document_text(
        """
        Cooling Skid Service Manual
        1. Relief Valve Replacement
        Replace PN-1212 only after isolating the manifold.
        2. Commissioning Check
        Verify PN-2212 pressure setpoint after startup.
        """
    )

    assert parsed.title == "Cooling Skid Service Manual"
    assert len(parsed.sections) == 2
    assert parsed.sections[0].heading == "1. Relief Valve Replacement"
    assert parsed.sections[0].part_references == ["PN-1212"]
    assert parsed.part_references == ["PN-1212", "PN-2212"]


def test_extract_part_references_normalizes_values() -> None:
    assert extract_part_references("Use pn 1212 and valve_2200.") == ["PN-1212", "VALVE-2200"]
